"""Read XP3 metadata and script samples; never execute original game code."""
from pathlib import Path
import struct, zlib, json, collections, re

ROOT=Path(r'G:\SteamLibrary\steamapps\common\ATRI -My Dear Moments-')
OUT=Path(__file__).resolve().parents[1]/'reports/xp3'
OUT.mkdir(exist_ok=True)
MAGIC=b'XP3\r\n \n\x1a\x8bg\x01'

def chunks(data):
    pos=0
    while pos+12<=len(data):
        tag=data[pos:pos+4].decode('ascii',errors='replace')
        size=struct.unpack_from('<Q',data,pos+4)[0]
        if size>len(data)-pos-12: raise ValueError('invalid chunk size')
        yield tag,data[pos+12:pos+12+size]
        pos+=12+size

def index(path):
    entries=[]
    with path.open('rb') as f:
        header=f.read(19)
        if header[:11]!=MAGIC: raise ValueError('not standard XP3')
        offset=struct.unpack_from('<Q',header,11)[0]
        for _ in range(16):
            f.seek(offset);flag=f.read(1)[0]
            packed=struct.unpack('<Q',f.read(8))[0]
            raw=struct.unpack('<Q',f.read(8))[0] if flag&1 else packed
            if max(raw,packed)>64*1024*1024:raise ValueError('index too big')
            data=f.read(packed)
            if flag&1:data=zlib.decompress(data)
            assert len(data)==raw
            for tag,chunk in chunks(data):
                if tag!='File':continue
                item={}
                for sub,d in chunks(chunk):
                    if sub=='info':
                        flags,original,size,n=struct.unpack_from('<IQQH',d)
                        item.update(name=d[22:22+n*2].decode('utf-16-le'),flags=flags,original=original,packed=size)
                    elif sub=='segm':item['segments']=[struct.unpack_from('<IQQQ',d,i) for i in range(0,len(d),28)]
                    elif sub=='adlr':item['adler']=struct.unpack_from('<I',d)[0]
                entries.append(item)
            if not flag&128:break
            offset=struct.unpack('<Q',f.read(8))[0]
    return entries

def payload(path,item):
    if item['original']>64*1024*1024:raise ValueError('sample too big')
    blocks=[]
    with path.open('rb') as f:
        for flags,offset,original,packed in item['segments']:
            f.seek(offset);data=f.read(packed)
            if flags&1:data=zlib.decompress(data)
            assert len(data)==original
            blocks.append(data)
    data=b''.join(blocks);assert len(data)==item['original']
    return data

def decode_text(data):
    if data.startswith(b'\xff\xfe'):return data[2:].decode('utf-16-le'), 'utf-16-le'
    if data.startswith(b'\xef\xbb\xbf'):return data[3:].decode('utf-8'),'utf-8-sig'
    if data.startswith(b'\xfe\xfe'):return None,'kirikiri encoded text'
    for encoding in ['utf-8','cp932','gb18030']:
        try:
            text=data.decode(encoding)
            if '\x00' in text: continue
            return text,encoding
        except UnicodeError:pass
    return None,'unknown/binary'

def main():
    reports=[];samples=[]
    for path in sorted([ROOT/'data.xp3',*(ROOT/'arc').glob('*.xp3')]):
        try:entries=index(path)
        except Exception as error:
            reports.append({'archive':path.name,'error':str(error)});continue
        (OUT/(path.name+'.index.json')).write_text(json.dumps(entries,ensure_ascii=False,indent=2),encoding='utf-8')
        extensions=collections.Counter(Path(x['name']).suffix.lower() for x in entries)
        report={'archive':path.name,'archiveBytes':path.stat().st_size,'entries':len(entries),'uncompressedBytes':sum(x['original'] for x in entries),'extensions':dict(extensions),'entryFlags':dict(collections.Counter(str(x['flags']) for x in entries)),'examples':[x['name'] for x in entries[:6]]}
        reports.append(report)
        print(json.dumps(report,ensure_ascii=False),flush=True)
        text_entries=[x for x in entries if Path(x['name']).suffix.lower() in ['.ks','.tjs','.csv','.txt','.ini']]
        # Inspect all scenario files for tag structure, storing only local research copies.
        text_stats=[]
        for item in text_entries:
            data=payload(path,item)
            text,encoding=decode_text(data)
            row={'name':item['name'],'bytes':len(data),'encoding':encoding,'headerHex':data[:16].hex(),'adlerMatches':(zlib.adler32(data)&0xffffffff)==item.get('adler')}
            if text is not None:
                row['cjkCharacters']=len(re.findall(r'[\u3400-\u9fff]',text))
                row['tags']=dict(collections.Counter(re.findall(r'(?:\[|^@)([A-Za-z_][\w]*)',text,re.M)))
                if Path(item['name']).suffix.lower()=='.ks':
                    target=OUT/'scenarios'/path.stem/(Path(item['name']).name)
                    target.parent.mkdir(parents=True,exist_ok=True)
                    target.write_text(text,encoding='utf-8')
                if len(samples)<8 and Path(item['name']).suffix.lower()=='.ks':
                    samples.append({'archive':path.name,**row,'preview':text[:900]})
            text_stats.append(row)
        if text_stats:
            (OUT/(path.name+'.text.json')).write_text(json.dumps(text_stats,ensure_ascii=False,indent=2),encoding='utf-8')
            print(json.dumps({'archive':path.name,'textEntries':len(text_stats),'decodable':sum(x['encoding'] not in ['unknown/binary','kirikiri encoded text'] for x in text_stats),'encodings':dict(collections.Counter(x['encoding'] for x in text_stats)),'textExamples':text_stats[:4]},ensure_ascii=False),flush=True)
        for item in [x for x in entries if Path(x['name']).suffix.lower() in ['.png','.jpg','.tlg','.psb']][:2]:
            try:data=payload(path,item)
            except ValueError:continue
            print(json.dumps({'imageSample':item['name'],'archive':path.name,'headerHex':data[:16].hex(),'adlerMatches':(zlib.adler32(data)&0xffffffff)==item.get('adler')},ensure_ascii=False),flush=True)
    (OUT/'archive-report.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'script-samples.json').write_text(json.dumps(samples,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'scriptSamples':samples},ensure_ascii=False),flush=True)

if __name__=='__main__':main()

