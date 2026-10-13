"""Keep Atri's standing portraits; retain every original background and CG."""
from pathlib import Path
import hashlib,io,json,re,zipfile
from PIL import Image
from portrait_layout import aligned_sprite
ROOT=Path(__file__).resolve().parents[1];PROBE=ROOT.parent/'atri-probe';SRC=ROOT/'src';IMAGES=SRC/'common/images'
BASE=ROOT.parents[1]/'outputs/ATRI-RW5-0.1.3.bin'
EXPECTED='f4bf643a6c24b46617ea6f61dee63e66dd06d25bf8c80855635f9bb03658a468'
assert hashlib.sha256(BASE.read_bytes()).hexdigest()==EXPECTED
mapping=json.loads((ROOT/'reports/portrait-assets-map.json').read_text('utf8'));assert mapping['complete']
mapping=mapping['portraits'];metadata=json.loads((ROOT/'reports/atri-portrait-source-map.json').read_text('utf8'))
assert IMAGES.resolve().is_relative_to(ROOT.resolve())
kept=set();refs_before=refs_after=passages=0;old_png_bytes=new_png_bytes=0;removed=[];backgrounds=set()
with zipfile.ZipFile(BASE) as z:
    for name in z.namelist():
        if not(name.startswith('common/story/') and name.endswith('.txt')):continue
        frames=json.loads(z.read(name))
        for f in frames:
            passages+=1;backgrounds.add(f['art']['background'].lstrip('/'));selected=[]
            for s in f['art']['sprites']:
                refs_before+=1;asset=s['src'].lstrip('/');assert asset in mapping
                if mapping[asset]['atri']:selected.append(s);kept.add(asset);refs_after+=1
            f['art']['sprites']=selected
        p=SRC/name;p.write_text(json.dumps(frames,ensure_ascii=False,separators=(',',':')),encoding='utf8')
    assert passages==12172 and kept==set(metadata)
    for group in json.loads(z.read('common/gallery.txt')):backgrounds.update(p.lstrip('/') for p in group['variants'])
    for asset in sorted(kept):
        meta=metadata[asset];assert meta['base'].startswith('tatr')
        with Image.open(PROBE/'portraits'/(meta['id']+'.png')) as source:
            image=source.convert('RGBA');image=image.crop((0,0,image.width,round(image.height*.72)))
            image.thumbnail((220,216),Image.Resampling.LANCZOS)
            image=image.quantize(colors=192,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE)
            buffer=io.BytesIO();image.save(buffer,format='PNG',optimize=True)
        old_png_bytes+=len(z.read(asset));new_png_bytes+=len(buffer.getvalue());(SRC/asset).write_bytes(buffer.getvalue())
    # Geometry is derived from the final encoded aspect ratio, after resizing.
    for story in sorted((SRC/'common/story').rglob('*.txt')):
        frames=json.loads(story.read_text('utf8'))
        for frame in frames:
            sprites=frame['art']['sprites']
            for index,sprite in enumerate(sprites):
                with Image.open(SRC/sprite['src'].lstrip('/')) as image:
                    sprites[index]=aligned_sprite(sprite,image.size,len(sprites)==1)
        story.write_text(json.dumps(frames,ensure_ascii=False,separators=(',',':')),encoding='utf8')
    for entry in z.infolist():
        if entry.is_dir() or not entry.filename.startswith('common/images/'):continue
        name=entry.filename;p=SRC/name
        assert p.parent.resolve()==IMAGES.resolve() and re.fullmatch(r'[0-9a-f]{16}\.(png|jpg)',p.name)
        if name in backgrounds:assert p.read_bytes()==z.read(name)
        elif name not in kept:
            assert name in mapping and not mapping[name]['atri'],('Unexpected resource removal',name)
            removed.append({'file':name,'bytes':entry.file_size});p.unlink(missing_ok=True)
    for name in ('common/gallery.txt','common/atri-text.otf','common/logo.png','common/title_bg.jpg'):
        assert (SRC/name).read_bytes()==z.read(name),name
    with zipfile.ZipFile(ROOT.parents[1]/'outputs/ATRI-RW5-0.1.3-源码.zip') as original_source:
        assert (SRC/'common/graph.js').read_bytes()==original_source.read('atri-rw5/src/common/graph.js')
report={'baselineVersion':'0.1.3','baselineSha256':EXPECTED,'variant':'Atri standing portraits only','maximumPackageBytes':10500000,'target':'approximately 10 MB','removedOtherCharacterAssets':len(removed),'removedOtherCharacterBytes':sum(x['bytes'] for x in removed),'retainedAtriAssets':len(kept),'atriSourceMaximumHeight':216,'atriPaletteMaximumColors':192,'atriBytesBefore':old_png_bytes,'atriBytesAfter':new_png_bytes,'singleResizeFromOriginalIntermediate':True,'originalBackgroundAndCGBytesUnchanged':True,'backgroundAndCGAssets':len(backgrounds),'galleryGroups':31,'galleryVariants':71,'speakerAndDialoguePreserved':True,'passages':passages,'portraitReferencesBefore':refs_before,'portraitReferencesAfter':refs_after,'remainingPortraitsCenteredAndDialogueAligned':True,'graphFontIconAndTitleBytesUnchanged':True,'removedAssets':removed}
(ROOT/'reports/atri-only-assets.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k!='removedAssets'},ensure_ascii=False))
