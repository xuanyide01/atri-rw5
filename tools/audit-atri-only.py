"""Compare release structure independently against the tested full portrait build."""
from pathlib import Path
import io,json,hashlib,zipfile
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
old=ROOT.parents[1]/'outputs/ATRI-RW5-0.1.3.bin';new=ROOT/'dist/com.codex.atri.rw5.debug.0.1.4.rpk'
mapping=json.loads((ROOT/'reports/portrait-assets-map.json').read_text('utf8'))['portraits']
passages=frames_changed=0;kept=set()
with zipfile.ZipFile(old) as a,zipfile.ZipFile(new) as b:
    assert a.read('pages/index/index.js')==b.read('pages/index/index.js'),'Runtime page changed'
    for n in a.namelist():
        if n.startswith('common/story/') and n.endswith('.txt'):
            before=json.loads(a.read(n));after=json.loads(b.read(n));assert len(before)==len(after)
            for x,y in zip(before,after):
                passages+=1;assert {k:v for k,v in x.items() if k!='art'}=={k:v for k,v in y.items() if k!='art'}
                assert x['art']['background']==y['art']['background']
                want=[s for s in x['art']['sprites'] if mapping[s['src'].lstrip('/')]['atri']]
                assert len(want)==len(y['art']['sprites'])
                for s,t in zip(want,y['art']['sprites']):
                    assert {k:v for k,v in s.items() if k!='left'}=={k:v for k,v in t.items() if k!='left'}
                    if len(want)==1:assert abs(t['left']+t['width']/2-216)<=.5
                    else:assert s['left']==t['left']
                    assert t['top']+t['height']==286;kept.add(t['src'].lstrip('/'))
                if x!=y:frames_changed+=1
        elif n.startswith('common/images/') and n.endswith('.jpg'):assert a.read(n)==b.read(n),n
    for n in b.namelist():
        if n.startswith('common/images/') and n.endswith('.png'):
            assert n in kept and mapping[n]['atri'];im=Image.open(io.BytesIO(b.read(n)));im.load()
            assert im.height<=224 and im.width<=220 and len(im.getcolors(im.width*im.height))<=192
    for n in ('common/gallery.txt','common/atri-text.otf','common/logo.png','common/title_bg.jpg','common/title_logo.png','common/dialogue_bg.jpg'):
        assert a.read(n)==b.read(n),n
    with zipfile.ZipFile(ROOT.parents[1]/'outputs/ATRI-RW5-0.1.3-源码.zip') as source:
        assert (ROOT/'src/common/graph.js').read_bytes()==source.read('atri-rw5/src/common/graph.js')
        assert (ROOT/'runtime/story-engine.cjs').read_bytes()==source.read('atri-rw5/runtime/story-engine.cjs')
assert passages==12172 and len(kept)==418
report={'passed':True,'version':'0.1.4','packageSha256':hashlib.sha256(new.read_bytes()).hexdigest(),'baselineSha256':hashlib.sha256(old.read_bytes()).hexdigest(),'passages':passages,'framesWithPortraitChanges':frames_changed,'retainedAtriPortraits':len(kept),'allOriginalBackgroundAndCGBytesIdentical':True,'allTextSpeakersAndBranchesIdentical':True,'runtimePageAndSaveEngineByteIdentical':True,'singleAtriCenteredMultiAtriPositionsPreserved':True,'noOtherCharacterPortraitsOrMissingReferences':True,'physicalDeviceTested':False}
(ROOT/'reports/atri-only-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
