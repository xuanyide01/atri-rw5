"""Audit source SCN correspondence, reported visual regressions and old saves."""
from pathlib import Path
from PIL import Image,ImageOps
import hashlib,json,zipfile,io,importlib.util
ROOT=Path(__file__).resolve().parents[1];PROBE=ROOT.parent/'atri-probe'
spec=importlib.util.spec_from_file_location('compile_story',ROOT/'tools/compile-story.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
mapping=json.loads((ROOT/'converted/visual-map.json').read_text('utf8'))
graph=json.loads((ROOT/'converted/graph.json').read_text('utf8'));checks=[];count=0;breaks=0;verified=set()
regressions={('b701:*start',1):'ev018a',('b701:*start',13):'ev020al',('b701:*start',16):'bg004ll',('b123:*start',0):'bg015l',('b123:*start',1):'bg005ll'}
for path in sorted((PROBE/'scenarios').glob('b*.ks.json')):
    original=json.loads(path.read_text('utf8'));chapter=original['name'].removesuffix('.ks')
    for scene in original['scenes']:
        node=chapter+':'+scene['label'];frames=[]
        for chunk in graph['nodes'][node]['chunks']:
            frames.extend(json.loads((ROOT/'src/common/story'/chunk['file']).with_suffix('.txt').read_text('utf8')))
        source=[t for t in scene.get('texts',[]) if t[2] is not None];assert len(source)==len(frames)
        for index,(t,f) in enumerate(zip(source,frames)):
            assert t[-1]['env']=={'name':'env'},'Unexpected global camera'
            assert f['speaker']==module.clean_text(t[2][2][0]) and f['text']==module.clean_text(t[2][2][1]),(node,index)
            assert '\\n' not in f['text'];breaks+=str(t[2][2][1]).count('\\n')
            snapshot=[e for e in t[-1]['data'] if e[1] in ('bu','stage','event','character','noevent','layer')]
            identifier=hashlib.sha256(json.dumps(snapshot,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()[:20]
            entry=mapping[identifier];assert entry['background']==f['art']['background']
            visible={s.get('redraw',{}).get('imageFile',{}).get('file') for _,_,s in snapshot if s.get('showmode') in (1,3)}
            assert entry['primary'] is None or entry['primary'] in visible
            assert set(entry['overlays'])<=visible
            assert not any(x.startswith(('clip_','mask_','str2_','str3_')) for x in entry['overlays'])
            primary=entry['primaryLayer'];expected_people=[]
            rank=(-primary['actions'].get('zpos',233 if primary['kind']=='stage' else -60),primary['actions'].get('order',0),primary['index']) if primary else None
            for order,(_,kind,state) in enumerate(snapshot):
                if kind not in ('bu','character') or state.get('showmode') not in (1,3) or not state.get('redraw',{}).get('imageFile'):continue
                a=dict((x[0],x[1]) for x in state.get('action',[]) if x and len(x)>=2)
                if a.get('opacity',255)<=0 or (rank is not None and (-a.get('zpos',0),a.get('order',0),order)<rank):continue
                expected_people.append((a.get('xpos',0),order,a.get('opacity',255)/255))
            assert [x[2] for x in sorted(expected_people)[:3]]==[s['opacity'] for s in f['art']['sprites']],(node,index,'portrait depth/opacity mismatch')
            count+=1;verified.add(identifier)
            if (node,index) in regressions:
                expected=regressions[(node,index)];assert entry['primary']==expected,(node,index,entry)
                assert not entry['overlays'],entry
                name=entry['background'].rsplit('/',1)[1]
                target=ROOT/'reports/visual-inspect'/(node.split(':')[0]+'-'+str(index)+'-fixed.jpg')
                target.write_bytes((ROOT/'src/common/images'/name).read_bytes())
                checks.append({'node':node,'index':index,'originalResource':expected,'generatedResource':name,'text':f['text'],'overlappingSceneLayers':False})
assert count==12172 and len(verified)==4799 and len(checks)==5
old=ROOT.parents[1]/'outputs/ATRI-RW5-0.1.0-源码.zip'
with zipfile.ZipFile(old) as z:
    text=z.read('atri-rw5/src/common/graph.js').decode('utf8');previous=json.loads(text.removeprefix('export const graph=').strip().removesuffix(';'))
new=json.loads((ROOT/'src/common/graph.js').read_text('utf8').removeprefix('export const graph=').strip().removesuffix(';'))
assert new==previous,'Story graph changes could invalidate old save cursors'
report={'passed':True,'sourceSCNFramesChecked':count,'sourceSnapshotsChecked':len(verified),'sourceCharacterDepthAndOpacityChecked':True,'literalNewlineControlsDecoded':breaks,'reportedCGRegressions':checks,'graphMatchesV010':True,'saveStoragePrefixUnchanged':'atri_rw5_','presentationLimit':'Whole original scene/CG stills with source-registered transparent illustrations; camera movement and masks omitted, not a pixel-identical replay of PC cinematics.'}
(ROOT/'reports/presentation-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False))
