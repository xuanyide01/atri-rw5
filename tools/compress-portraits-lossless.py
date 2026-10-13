"""Try PNG scanline/DEFLATE encodings; never alter palette, alpha or pixels."""
from pathlib import Path
import argparse,concurrent.futures,hashlib,io,json,struct,zlib,zipfile
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]

def chunk(kind,data):
    return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)

def replace_idat(original,compressed):
    out=bytearray(original[:8]);at=8;inserted=False
    while at<len(original):
        size=struct.unpack('>I',original[at:at+4])[0];kind=original[at+4:at+8]
        if kind==b'IDAT':
            if not inserted:out.extend(chunk(kind,compressed));inserted=True
        else:out.extend(original[at:at+12+size])
        at+=12+size
    assert at==len(original) and inserted
    return bytes(out)

def optimize(item):
    name,raw=item
    image=Image.open(io.BytesIO(raw));image.load()
    if image.mode!='P' or raw[24:26]!=bytes([8,3]) or raw[28]!=0:return name,raw,{'before':len(raw),'after':len(raw),'method':'unchanged non-P8 PNG'}
    a=np.frombuffer(image.tobytes(),dtype=np.uint8).reshape(image.height,image.width).astype(np.int16)
    left=np.zeros_like(a);left[:,1:]=a[:,:-1]
    above=np.zeros_like(a);above[1:]=a[:-1]
    corner=np.zeros_like(a);corner[1:,1:]=a[:-1,:-1]
    p=left+above-corner;pa=np.abs(p-left);pb=np.abs(p-above);pc=np.abs(p-corner)
    predictors=(np.zeros_like(a),left,above,(left+above)//2,np.where((pa<=pb)&(pa<=pc),left,np.where(pb<=pc,above,corner)))
    filtered=[((a-pred)&255).astype(np.uint8) for pred in predictors]
    scores=np.array([np.minimum(x.astype(np.int16),256-x.astype(np.int16)).sum(axis=1) for x in filtered])
    adaptive=scores.argmin(axis=0)
    candidates=[('filter'+str(f),b''.join(bytes([f])+row.tobytes() for row in filtered[f])) for f in range(5)]
    candidates.append(('adaptive',b''.join(bytes([int(f)])+filtered[int(f)][y].tobytes() for y,f in enumerate(adaptive))))
    best=raw;method='original'
    for label,data in candidates:
        for strategy in (zlib.Z_DEFAULT_STRATEGY,zlib.Z_FILTERED):
            co=zlib.compressobj(9,zlib.DEFLATED,15,9,strategy);packed=co.compress(data)+co.flush()
            encoded=replace_idat(raw,packed)
            if len(encoded)<len(best):best=encoded;method=label+('/filtered' if strategy else '/default')
    result=Image.open(io.BytesIO(best));result.load()
    assert result.size==image.size and result.convert('RGBA').tobytes()==image.convert('RGBA').tobytes(),name
    assert result.getpalette()==image.getpalette() and result.info.get('transparency')==image.info.get('transparency'),name
    return name,best,{'before':len(raw),'after':len(best),'saved':len(raw)-len(best),'method':method,'pixelPaletteAlphaExact':True}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--sample',type=int,default=0);args=parser.parse_args()
    baseline=ROOT.parents[1]/'outputs/ATRI-RW5-0.1.3.bin'
    with zipfile.ZipFile(baseline) as z:
        names=[n for n in z.namelist() if n.startswith('common/images/') and n.endswith('.png')]
        if args.sample:names=names[::max(1,len(names)//args.sample)][:args.sample]
        items=[(n,z.read(n)) for n in names]
    folder=ROOT/'compression/v014';folder.mkdir(parents=True,exist_ok=True)
    entries={}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for n,raw,result in pool.map(optimize,items):
            if not args.sample:
                p=folder/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
            entries[n]=result
    before=sum(e['before'] for e in entries.values());after=sum(e['after'] for e in entries.values())
    report={'baselineSha256':hashlib.sha256(baseline.read_bytes()).hexdigest(),'sampleOnly':bool(args.sample),'count':len(entries),'before':before,'after':after,'saved':before-after,'rgbaPaletteAndAlphaUnchanged':True,'entries':entries}
    (folder/('sample.json' if args.sample else 'lossless-png.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='entries'},ensure_ascii=False))

if __name__=='__main__':main()
