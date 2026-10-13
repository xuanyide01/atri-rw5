"""Audit exact signed bytes, bounded resources, original text and font coverage."""
from pathlib import Path
import json,zipfile,io,hashlib
from PIL import Image
from fontTools.ttLib import TTFont
from rpk_signature import audit
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'src/manifest.json').read_text('utf8'))
package=ROOT/('dist/'+manifest['package']+'.debug.'+manifest['versionName']+'.rpk');report=audit(package)
assert report['bytes']<=15000000
manifest=json.loads((ROOT/'src/manifest.json').read_text('utf8'))
font=TTFont(ROOT/'src/common/atri-text.otf').getBestCmap()
images=0;maxdecode=0;maxplaydecode=0;passages=0;maxchunk=0;original_reference=True
with zipfile.ZipFile(package) as z:
    assert z.testzip() is None
    packaged=json.loads(z.read('manifest.json'))
    assert all(packaged[k]==manifest[k] for k in ('package','name','versionName','versionCode','icon','features','router'))
    assert packaged['config']['designWidth']==432
    assert json.loads(z.read('manifest-watch.json'))==manifest
    for name in z.namelist():
        if name.endswith('/'):continue
        data=z.read(name)
        if name.startswith('common/'):
            source=ROOT/'src'/name;assert source.exists() and data==source.read_bytes(),name
        if name.endswith(('.png','.jpg')):
            image=Image.open(io.BytesIO(data));image.load();images+=1
            maxdecode=max(maxdecode,image.width*image.height*4)
            if '/images/' in name:
                assert image.width<=320 and image.height<=256,name
                maxplaydecode=max(maxplaydecode,image.width*image.height*4)
        if name.startswith('common/story/') and name.endswith('.txt'):
            frames=json.loads(data);maxchunk=max(maxchunk,len(data));assert len(frames)<=48
            reference_path=(ROOT/'converted/story'/name.removeprefix('common/story/')).with_suffix('.json')
            original=json.loads(reference_path.read_text('utf8')) if reference_path.exists() else None
            if original is None:original_reference=False
            else:assert len(frames)==len(original)
            for index,frame in enumerate(frames):
                if original is not None:assert frame['text']==original[index]['text'] and frame['speaker']==original[index]['speaker']
                for ch in frame['text']+frame['speaker']:assert ch.isspace() or ord(ch)<32 or ord(ch) in font,repr(ch)
                assert frame['art']['background'].lstrip('/') in z.namelist()
                for sprite in frame['art']['sprites']:
                    assert sprite['src'].lstrip('/') in z.namelist()
                    assert sprite['top']+sprite['height']==286
            passages+=len(frames)
    logo=Image.open(io.BytesIO(z.read('common/logo.png')))
    assert logo.size==(192,192) and logo.mode=='RGBA'
    assert all(logo.getpixel(p)[3]==0 for p in [(0,0),(191,0),(0,191),(191,191)])
    gallery=json.loads(z.read('common/gallery.txt'))
    for group in gallery:
        assert group['variants']
        for path in group['variants']:assert path.lstrip('/') in z.namelist()
assert passages==12172 and maxchunk<24000
report.update({'decodedImages':images,'maxSingleImageRGBABytes':maxdecode,'maxGameplayImageRGBABytes':maxplaydecode,'passages':passages,'maxStoryChunkBytes':maxchunk,'sourceTextAndNamesPreserved':True if original_reference else None,'originalIntermediateReferenceAvailable':original_reference,'fontCoverageValid':True,'circularIcon':True,'galleryGroups':len(gallery),'galleryVariants':sum(len(g['variants']) for g in gallery),'saveSlots':30,'physicalDeviceTested':False})
(ROOT/'reports/package-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False))
