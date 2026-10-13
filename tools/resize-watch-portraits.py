"""Reduce decoded portrait dimensions while retaining the same on-screen box."""
from pathlib import Path
from PIL import Image
import hashlib,json,io,re
ROOT=Path(__file__).resolve().parents[1];IMAGES=ROOT/'src/common/images';mapping={};created=set()
manifest=json.loads((ROOT/'src/manifest.json').read_text('utf8'))
if manifest['versionCode']>=2:raise SystemExit('0.1.1+ portraits are already optimized once. Rebuild with prepare-watch-assets.py only.')
assert IMAGES.resolve().is_relative_to(ROOT.resolve())
for p in list(IMAGES.glob('*.png')):
    with Image.open(p) as source:
        image=source.convert('RGBA');image.thumbnail((200,224),Image.Resampling.LANCZOS)
        palette=image.quantize(colors=160,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE)
        buffer=io.BytesIO();palette.save(buffer,format='PNG',optimize=True)
        raw=buffer.getvalue();name=hashlib.sha256(raw).hexdigest()[:16]+'.png';(IMAGES/name).write_bytes(raw);created.add(name)
        mapping['/common/images/'+p.name]={'src':'/common/images/'+name,'width':round(image.width*286/image.height),'height':286,'top':0}
for p in (ROOT/'src/common/story').rglob('*.txt'):
    frames=json.loads(p.read_text('utf8'))
    for frame in frames:
        for sprite in frame['art']['sprites']:
            old_width=sprite['width'];center=sprite['left']+old_width/2;sprite.update(mapping[sprite['src']]);sprite['left']=round(center-sprite['width']/2)
    p.write_text(json.dumps(frames,ensure_ascii=False,separators=(',',':')),encoding='utf8')
for old in mapping:
    p=IMAGES/old.rsplit('/',1)[1]
    if p.name not in created:p.unlink()
report={'portraitResourceMaxHeight':224,'displayHeight':286,'imageBytes':sum(p.stat().st_size for p in IMAGES.iterdir()),'note':'Optimization of generated sprites. Rebuilding from originals runs prepare-watch-assets then this script once.'}
(ROOT/'reports/portrait-size-optimization.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(report)
