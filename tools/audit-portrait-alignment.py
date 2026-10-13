"""Prove 0.1.5 changes only displayed portrait rectangles and version metadata."""
from pathlib import Path
import hashlib,io,json,math,re,zipfile
from PIL import Image
from portrait_layout import aligned_sprite,visible_bottom,SCENE_HEIGHT,PORTRAIT_HEIGHT

ROOT=Path(__file__).resolve().parents[1]
version=json.loads((ROOT/'src/manifest.json').read_text('utf8'))['versionName']
package=ROOT/f'dist/com.codex.atri.rw5.debug.{version}.rpk'
base=ROOT.parents[1]/'outputs/ATRI-RW5-0.1.4-轻量版.bin'
assert hashlib.sha256(base.read_bytes()).hexdigest()=='3b971542bb25e78be2d9c0c7fa1b1a88d2ef8074ec3ea210cf2fad813c51252d'
passages=refs=0;portraits=set();changed=[];min_bottom=999;min_contact=999
with zipfile.ZipFile(base) as a,zipfile.ZipFile(package) as b:
    assert set(a.namelist())==set(b.namelist()),'Resource addition/removal'
    assert a.read('pages/index/index.js')==b.read('pages/index/index.js'),'UI/save/choice logic changed'
    backdrop=Image.open(io.BytesIO(b.read('common/dialogue_bg.jpg')))
    assert backdrop.size==(432,228) and backdrop.mode=='RGB','Dialogue must occlude lower portrait pixels'
    for name in a.namelist():
        if name.endswith('/'):continue
        if name.startswith('common/story/') and name.endswith('.txt'):
            before=json.loads(a.read(name));after=json.loads(b.read(name));assert len(before)==len(after)
            if a.read(name)!=b.read(name):changed.append(name)
            for x,y in zip(before,after):
                passages+=1
                assert {k:v for k,v in x.items() if k!='art'}=={k:v for k,v in y.items() if k!='art'}
                assert x['art']['background']==y['art']['background']
                assert len(x['art']['sprites'])==len(y['art']['sprites'])
                for old,new in zip(x['art']['sprites'],y['art']['sprites']):
                    refs+=1;path=new['src'].lstrip('/');portraits.add(path)
                    image=Image.open(io.BytesIO(b.read(path))).convert('RGBA');alpha=image.getchannel('A');bbox=alpha.getbbox();assert bbox
                    assert new==aligned_sprite(old,image.size,len(y['art']['sprites'])==1)
                    bottom=visible_bottom(new,image.size,bbox);min_bottom=min(min_bottom,bottom)
                    assert bottom>=SCENE_HEIGHT+16
                    scale=min(new['width']/image.width,new['height']/image.height)
                    row=math.floor((SCENE_HEIGHT-.5-new['top']-(new['height']-image.height*scale)/2)/scale)
                    contact=sum(alpha.getpixel((x,row))>=128 for x in range(image.width))
                    assert contact>=1,(path,'Transparent silhouette at dialogue edge')
                    min_contact=min(min_contact,contact)
                    assert new['top']==0,'Keep face and hair top; clip lower body only'
        elif name.startswith('common/') or name.startswith('pages/'):
            assert a.read(name)==b.read(name),('Non-layout resource changed',name)
    for name in ('manifest.json','manifest-watch.json'):
        old_manifest=json.loads(a.read(name));new_manifest=json.loads(b.read(name))
        if 'packageInfo' in old_manifest:
            old_manifest['packageInfo']['timeStamp']=new_manifest['packageInfo']['timeStamp']
        assert {k:v for k,v in old_manifest.items() if k not in ('versionName','versionCode')}=={k:v for k,v in new_manifest.items() if k not in ('versionName','versionCode')}
    app_before=a.read('app.js').replace(b'"versionName":"0.1.4","versionCode":10',b'"versionName":"0.1.5","versionCode":11')
    assert app_before==b.read('app.js'),'Application change beyond embedded version metadata'
    assert re.sub(rb'timeStamp=[^\r\n]+',b'timeStamp=',a.read('META-INF/build.txt'))==re.sub(rb'timeStamp=[^\r\n]+',b'timeStamp=',b.read('META-INF/build.txt'))
    allowed={'manifest.json','manifest-watch.json','rpk.config.json','app.js','META-INF/CERT','META-INF/CERT.SF','META-INF/CERT.RSA','META-INF/MANIFEST.MF','META-INF/build.txt'}
    # Compiler/signature files vary with the new version; all other entries must
    # be identical unless they are a verified geometry-only story block.
    unexplained=[n for n in a.namelist() if a.read(n)!=b.read(n) and n not in allowed and n not in changed]
    assert not unexplained,unexplained
assert passages==12172 and refs==5065 and len(portraits)==418
report={'passed':True,'version':version,'packageSha256':hashlib.sha256(package.read_bytes()).hexdigest(),'baselineVersion':'0.1.4','baselineSha256':hashlib.sha256(base.read_bytes()).hexdigest(),'passages':passages,'portraitReferences':refs,'portraitAssets':len(portraits),'changedStoryChunks':len(changed),'geometryOnly':True,'imageBytesUnchanged':True,'allTextSpeakersAndBranchesIdentical':True,'runtimePageAndSaveEngineByteIdentical':True,'allOriginalBackgroundAndCGBytesIdentical':True,'encodedImageMemoryUnchanged':True,'displayHeightBefore':286,'displayHeightAfter':PORTRAIT_HEIGHT,'enlargementPercent':round((PORTRAIT_HEIGHT/286-1)*100,2),'minimumVisibleBottomBeforeClipping':min_bottom,'sceneClippedAt':SCENE_HEIGHT,'minimumOpaqueSourcePixelsAtDialogueEdge':min_contact,'facesNotCroppedAtTop':True,'physicalDeviceTested':False}
(ROOT/'reports/portrait-alignment-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False))
