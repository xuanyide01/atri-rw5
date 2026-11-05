"""Convert the tested RW5 source to a 336x480 Band 8 Pro package."""
from pathlib import Path
import json,math,re,io
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parents[1]/'atri-rw5/源码';SRC=ROOT/'src'
count=0
for p in (BASE/'src/common/story').rglob('*.txt'):
    frames=json.loads(p.read_text('utf8'))
    for f in frames:
        for s in f['art']['sprites']:
            with Image.open(SRC/s['src'].lstrip('/')) as im:w=math.ceil(im.width*243/im.height)
            center=(s['left']+s['width']/2)*336/432;s.update(width=w,height=243,top=0,left=round(center-w/2));count+=1
    (SRC/'common/story'/p.relative_to(BASE/'src/common/story')).write_text(json.dumps(frames,ensure_ascii=False,separators=(',',':')),encoding='utf8')
before=after=0;images=0
for p in (BASE/'src/common/images').glob('*.jpg'):
    before+=p.stat().st_size
    with Image.open(p) as im:
        im=im.convert('RGB');im.thumbnail((288,216),Image.Resampling.LANCZOS);buffer=io.BytesIO();im.save(buffer,format='JPEG',quality=74,optimize=True,progressive=False)
        data=buffer.getvalue();(SRC/'common/images'/p.name).write_bytes(data if len(data)<p.stat().st_size else p.read_bytes())
    after+=(SRC/'common/images'/p.name).stat().st_size;images+=1
with Image.open(BASE/'src/common/logo.png') as im:im.resize((96,96),Image.Resampling.LANCZOS).save(SRC/'common/logo.png',optimize=True)
title=Image.new('RGB',(336,480));d=ImageDraw.Draw(title)
for y in range(189,480):
    t=(y-189)/291;d.line((0,y,335,y),fill=tuple(round(a+(b-a)*t) for a,b in zip((236,247,253),(213,234,247))))
with Image.open(BASE/'src/common/title_bg.jpg') as im:title.paste(im.crop((0,0,432,243)).resize((336,189),Image.Resampling.LANCZOS),(0,0))
for i in range(4):d.arc((200-i*18,320-i*10,450+i*14,560+i*13),170,320,fill='#bad9eb',width=1)
d.rounded_rectangle((14,204,321,464),radius=13,fill='#f2f9fd',outline='#bed9e9',width=1);d.line((24,224,24,447),fill='#92bdd6',width=2)
title.save(SRC/'common/title_bg.jpg',quality=88,optimize=True)
dialogue=Image.new('RGB',(336,256));d=ImageDraw.Draw(dialogue)
for y in range(256):
    t=y/255;d.line((0,y,335,y),fill=tuple(round(a+(b-a)*t) for a,b in zip((225,231,236),(194,205,216))))
dialogue.save(SRC/'common/dialogue_bg.jpg',quality=86,optimize=True)
strings=[]
def collect(v):
    if isinstance(v,str):strings.append(v)
    elif isinstance(v,list):
        for x in v:collect(x)
    elif isinstance(v,dict):
        for x in v.values():collect(x)
for p in (SRC/'common/story').rglob('*.txt'):collect(json.loads(p.read_text('utf8')))
collect(json.loads((SRC/'common/gallery.txt').read_text('utf8')))
triggers=[]
for ch in sorted(set(''.join(strings))):
    if ch.isspace() or ord(ch)<128:continue
    try:ch.encode('gb2312')
    except UnicodeEncodeError:triggers.append(ch)
    else:
        if ch=='・':triggers.append(ch)
(SRC/'common/text-font.js').write_text('const extra='+json.dumps(''.join(triggers),ensure_ascii=False)+";\nexport function textFont(text){const value=String(text||'');for(let i=0;i<extra.length;i++)if(value.indexOf(extra[i])>=0)return 'atrifont';return '';}\n",encoding='utf8')
# The authoritative Band UI lives in tools/ui-*.txt; retain manual layout fixes.
report={'sourceVersion':'RW5 '+json.loads((BASE/'src/manifest.json').read_text('utf8'))['versionName'],'viewport':[336,480],'portraitReferences':count,'portraitImageBytesUnchanged':True,'fullCGCount':images,'jpegBytesBefore':before,'jpegBytesAfter':after,'fontPolicy':'System default without explicit family; supplemental font for missing SDK glyphs','extraFontTriggers':triggers}
(ROOT/'reports/band-conversion.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k!='extraFontTriggers'},ensure_ascii=False))


# Apply the current firmware font policy and static custom-font classes.
import subprocess,sys
subprocess.run([sys.executable,str(ROOT/'tools/fix-band-font.py')],check=True)
subprocess.run([sys.executable,str(ROOT/'tools/apply-font-classes.py')],check=True)
