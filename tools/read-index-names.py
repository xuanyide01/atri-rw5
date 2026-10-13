from pathlib import Path
import struct,zlib,json,collections,hashlib
from xp3 import chunks,index
root=Path('G:/SteamLibrary/steamapps/common/ATRI -My Dear Moments-')
out=Path(__file__).resolve().parents[2]/'atri-probe'
for name in ['data','bgimage','fgimage','vol1']:
 p=root/(name+'.xp3')
 with p.open('rb') as f:
  f.seek(11);offset=struct.unpack('<Q',f.read(8))[0];parts=[]
  for _ in range(16):
   f.seek(offset);flag=f.read(1)[0];size=struct.unpack('<Q',f.read(8))[0]
   if flag&1:f.read(8)
   part=f.read(size)
   if flag&1:part=zlib.decompress(part)
   parts.append(part)
   if not flag&128:break
   offset=struct.unpack('<Q',f.read(8))[0]
  data=b''.join(parts)
 (out/(name+'.index.raw')).write_bytes(data)
 counts=collections.Counter();samples=[];names=[]
 for tag,b in chunks(data):
  counts[tag]+=1
  if tag!='File':
   if len(samples)<5:samples.append({'tag':tag,'length':len(b),'prefix':b[:80].hex()})
   if len(b)>=6:
    h,n=struct.unpack_from('<IH',b)
    if n>0 and 6+2*n<=len(b):
     s=b[6:6+2*n].decode('utf-16-le',errors='replace');names.append({'hash':h,'name':s})
 (out/(name+'.names.json')).write_text(json.dumps(names,ensure_ascii=False,indent=2),encoding='utf8')
 print(name,dict(counts),'names',len(names),'sample',str(names[:3]),'other',samples)
