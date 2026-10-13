"""Check actual emulator portrait pixels and the opaque dialogue boundary."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
version=json.loads((ROOT/'src/manifest.json').read_text('utf8'))['versionName'];out=ROOT/('native-test-results/v'+version.replace('.',''))
report=json.loads((out/'portrait-alignment-report.json').read_text('utf8'))
sha=hashlib.sha256((ROOT/f'dist/com.codex.atri.rw5.debug.{version}.rpk').read_bytes()).hexdigest();assert report['packageSha256']==sha and report['passed']
results=[]
for index in (21,28,155):
    assert f'b102:*start/{index}' in report['capturedScenes']
    frame=json.loads((ROOT/f'src/common/story/b102/start-{index//48:03}.txt').read_text('utf8'))[index%48]
    assert len(frame['art']['sprites'])==1
    screenshot=Image.open(out/f'portrait-b102-{index}.png').convert('RGB');actual=np.array(screenshot.crop((0,0,432,286))).astype(float)
    errors=[];contact_errors=[];counts=[]
    for bg_y in (21,22):
        expected=Image.new('RGBA',(432,286),'black');mask=Image.new('L',(432,286),0)
        bg=Image.open(ROOT/'src'/frame['art']['background'].lstrip('/')).convert('RGBA').resize((432,243),Image.Resampling.BILINEAR);expected.paste(bg,(0,bg_y))
        for sprite in frame['art']['sprites']:
            assert sprite['opacity']==1
            image=Image.open(ROOT/'src'/sprite['src'].lstrip('/')).convert('RGBA')
            scale=min(sprite['width']/image.width,sprite['height']/image.height)
            image=image.resize((round(image.width*scale),round(image.height*scale)),Image.Resampling.BILINEAR)
            pos=(sprite['left']+round((sprite['width']-image.width)/2),sprite['top']+round((sprite['height']-image.height)/2))
            expected.alpha_composite(image,pos);mask.paste(image.getchannel('A'),pos)
        delta=np.abs(actual-np.array(expected.convert('RGB')).astype(float));contact=np.array(mask)[285]>200
        assert contact.sum()>10
        errors.append(float(delta.mean()));contact_errors.append(float(delta[285,contact,:].mean()));counts.append(int(contact.sum()))
    assert min(errors)<10,(index,'Different displayed scene/portrait geometry',errors)
    assert min(contact_errors)<20,(index,'Portrait does not reach dialogue',contact_errors)
    backdrop=Image.open(ROOT/'src/common/dialogue_bg.jpg').convert('RGB')
    boundary_error=float(np.abs(np.array(screenshot.crop((0,286,432,296))).astype(float)-np.array(backdrop.crop((0,0,432,10))).astype(float)).mean())
    assert boundary_error<10,(index,'Portrait leaked into text panel',boundary_error)
    results.append({'scene':f'b102:*start/{index}','meanChannelError':round(min(errors),3),'dialogueEdgeForegroundPixels':min(counts),'dialogueEdgeForegroundError':round(min(contact_errors),3),'dialogueBackdropError':round(boundary_error,3)})
report['pixelComparison']=results;report['visualAlignmentVerified']=True;report['noPortraitLeakIntoDialogue']=True
(out/'portrait-alignment-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False))
