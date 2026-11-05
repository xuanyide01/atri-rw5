"""Idempotently remove character-window frames after lightweight conversion.
Preconverted clean targets are already supplied. --original-images can rebuild
missing targets from the user's verified original bgimage resource directory.
"""
from pathlib import Path
import argparse,json,hashlib,zlib,io,re
from PIL import Image
R=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser();p.add_argument('--original-images');a=p.parse_args();policy=json.loads((R/'tools/atri-portrait-policy.json').read_text('utf8'));mapping=policy['backgroundReplacements']
needed={dst for dst in mapping.values() if not (R/'src'/dst.lstrip('/')).exists()}
if needed:
 if not a.original_images:raise SystemExit('Clean targets missing: supply --original-images with the verified original bgimage directory')
 source=Path(a.original_images)
 for name,meta in policy['originalInputs'].items():
  raw=(source/name).read_bytes();assert hashlib.sha256(raw).hexdigest()==meta['sha256'] and zlib.adler32(raw)&0xffffffff==meta['adler32']
 for case in policy['sourceSnapshotCorrections']:
  if case['new'] not in needed:continue
  primary=case['primary'];filename='LL/bg005bell.jpg' if primary=='bg005bell' else 'bg003a.png';assert primary in ['bg005bell','bg003a']
  with Image.open(source/filename) as im:im=im.convert('RGBA');im.thumbnail((320,180),Image.Resampling.LANCZOS);canvas=Image.new('RGBA',(320,180),'black');canvas.alpha_composite(im,((320-im.width)//2,(180-im.height)//2))
  for name,actions in case['preservedOverlays']:
   assert name=='item059b'
   with Image.open(source/'item/item059b.png') as im:im=im.convert('RGBA')
   im=im.resize((max(1,round(im.width*actions.get('zoomx',100)/400)),max(1,round(im.height*actions.get('zoomy',100)/400))),Image.Resampling.LANCZOS)
   if actions.get('opacity',255)!=255:im.putalpha(im.getchannel('A').point(lambda p:p*actions['opacity']//255))
   if actions.get('rotate',0):im=im.rotate(-actions['rotate'],resample=Image.Resampling.BICUBIC,expand=True)
   canvas.alpha_composite(im,(round(160+actions.get('xpos',0)/4-im.width/2),round(90+actions.get('ypos',0)/4-im.height/2)))
  buf=io.BytesIO();canvas.convert('RGB').save(buf,format='JPEG',quality=70,optimize=True,subsampling=2);raw=buf.getvalue();assert case['new']=='/common/images/'+hashlib.sha256(raw).hexdigest()[:16]+'.jpg'
  if 'band8pro' in R.parent.name:
   im=Image.open(io.BytesIO(raw)).convert('RGB');im.thumbnail((288,216),Image.Resampling.LANCZOS);buf=io.BytesIO();im.save(buf,format='JPEG',quality=74,optimize=True,progressive=False)
   if len(buf.getvalue())<len(raw):raw=buf.getvalue()
  (R/'src'/case['new'].lstrip('/')).write_bytes(raw);needed.remove(case['new'])
 assert not needed
changed=0;active=set()
for path in (R/'src/common/story').rglob('*.txt'):
 frames=json.loads(path.read_text('utf8'));dirty=False
 for frame in frames:
  for sprite in frame['art']['sprites']:assert sprite['src'].lstrip('/') in policy['atriPortraitWhitelist']
  before=frame['art']['background'];after=mapping.get(before,before);active.add(after)
  if before!=after:frame['art']['background']=after;dirty=True;changed+=1
 if dirty:path.write_text(json.dumps(frames,ensure_ascii=False,separators=(',',':')),encoding='utf8')
for group in json.loads((R/'src/common/gallery.txt').read_text('utf8')):active.update(group['variants'])
for before,after in mapping.items():
 if before==after:continue
 assert before not in active;target=(R/'src'/before.lstrip('/')).resolve();assert target.parent==(R/'src/common/images').resolve() and re.fullmatch('[0-9a-f]{16}[.]jpg',target.name)
 target.unlink(missing_ok=True)
print('CHARACTER_WINDOWS_REMOVED',changed)
