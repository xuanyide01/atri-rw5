"""ATRI TJS/4s0 reader. Format reference: xmoezzz/xp3-brute (MIT),
src/decoder/pbd.rs. This reader validates type-check bytes and full consumption.
Only the crypt=1, empty-IV variant observed in the supplied assets is accepted.
"""
from pathlib import Path
import struct,hashlib,json
import lz4.block
MASK=0xffffffff
def rol(x,n):return ((x<<n)|(x>>(32-n)))&MASK
def chacha(key,counter,nlo,nhi):
 s=list(struct.unpack('<4I',b'expand 32-byte k'))+list(struct.unpack('<8I',key))+[counter&MASK,counter>>32,nlo,nhi];origin=s[:]
 def q(a,b,c,d):
  s[a]=(s[a]+s[b])&MASK;s[d]=rol(s[d]^s[a],16);s[c]=(s[c]+s[d])&MASK;s[b]=rol(s[b]^s[c],12)
  s[a]=(s[a]+s[b])&MASK;s[d]=rol(s[d]^s[a],8);s[c]=(s[c]+s[d])&MASK;s[b]=rol(s[b]^s[c],7)
 for _ in range(4):
  for v in [(0,4,8,12),(1,5,9,13),(2,6,10,14),(3,7,11,15),(0,5,10,15),(1,6,11,12),(2,7,8,13),(3,4,9,14)]:q(*v)
 return [(a+b)&MASK for a,b in zip(s,origin)]
def decode(data):
 assert data[:8]==b'TJS/4s0\0'
 seed,crypt,ivlen=struct.unpack_from('<IHH',data,8);assert crypt==1 and ivlen==0,(crypt,ivlen)
 h=(seed+374761393)&MASK;h^=h>>15;h=(h*2246822519)&MASK;h^=h>>13;h=(h*3266489917)&MASK;h^=h>>16
 fallback=(seed^h) or seed or MASK;key=hashlib.blake2s(b'',key=struct.pack('<I',seed)).digest();framed=bytearray(data[16:])
 for offset in range(0,len(framed),1024):
  words=chacha(key,offset//1024,h,seed)
  for i in range(240):
   x=words[i];x^=(x<<13)&MASK;x^=x>>17;x^=(x<<5)&MASK;words.append(x or fallback)
  stream=struct.pack('<256I',*words)
  for j in range(min(1024,len(framed)-offset)):framed[offset+j]^=stream[j]
 pos=0;plain=bytearray()
 while pos<len(framed):
  size=struct.unpack_from('<H',framed,pos)[0];pos+=2
  if not size:assert not any(framed[pos:]);break
  assert pos+size<=len(framed)
  plain.extend(lz4.block.decompress(bytes(framed[pos:pos+size]),uncompressed_size=65536,dict=bytes(plain[-65536:])))
  pos+=size
 pos=0;state=[((seed>>24)^seed)&255,(seed>>8)&255,(seed>>16)&255]
 def read(fmt):
  nonlocal pos
  v=struct.unpack_from('<'+fmt,plain,pos)[0];pos+=struct.calcsize('<'+fmt);return v
 def string():
  nonlocal pos
  n=read('I');assert n<1000000 and pos+2*n<=len(plain);v=plain[pos:pos+2*n].decode('utf-16-le');pos+=n*2;return v
 def value(depth=0):
  assert depth<128
  t=read('B');c=read('B')
  if t:
   z=(state[0]^(state[0]<<1))&255;state[:]=[state[1],state[2],(state[2]^(state[2]>>3)^z^(z>>5))&255]
  assert c==state[2],('type check',pos,t,c,state)
  if t==0:return None
  if t==2:return string()
  if t==4:return read('q')
  if t==5:return read('d')
  n=read('I');assert n<1000000
  if t==0x81:return [value(depth+1) for _ in range(n)]
  if t==0xc1:
   result={}
   for _ in range(n):
    k=string();assert k not in result;result[k]=value(depth+1)
   return result
  raise ValueError(('Unsupported PBD type',t))
 root=value();trailer=read('I');assert pos==len(plain),(pos,len(plain))
 return root
if __name__=='__main__':
 root=Path(__file__).resolve().parents[2]/'atri-probe/extracted/fgimage';count=0
 for p in root.rglob('*.pbd'):
  result=decode(p.read_bytes());p.with_suffix('.pbd.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');count+=1
 print('PBD_DECODED',count,'all type checks and full consumption passed')
