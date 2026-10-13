"""Compile decoded original SCN into bounded text chunks and a strict branch graph.

This is an intermediate representation, not yet the watch runtime format.
Graphics snapshots are retained separately for offline compositing; no rendering
or sound commands are executed by this converter. Unknown expressions fail closed.
"""
from pathlib import Path
import json,re,hashlib
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT.parent/'atri-probe/scenarios'
OUT=ROOT/'converted'

def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf8')

def condition(expr):
    if not expr:return None
    m=re.fullmatch(r'\s*f\.sen_flag\s*(==|!=)\s*(\d+)\s*',expr)
    if not m:raise ValueError('Unrecognized condition: '+expr)
    return [m[1],int(m[2])]

def effect(expr):
    if not expr:return None
    m=re.fullmatch(r'\s*f\.sen_flag\s*=\s*(?:(f\.sen_flag)\s*\+\s*)?(\d+)\s*',expr)
    if not m:raise ValueError('Unrecognized effect: '+expr)
    return ['add' if m[1] else 'set',int(m[2])]

def destination(item,current):
    storage=item.get('storage',current)
    if storage=='start.ks' and item.get('target')=='*gameend_title':return '@title'
    return storage.removesuffix('.ks')+':'+(item.get('target') or '*start')

def clean_text(value):
    # Decode the known SCN newline control only, preserving other literal escapes.
    return str(value or '').replace('\\n','\n').replace('\r\n','\n').replace('\r','\n').strip(' \t\n\u3000')

def main():
    nodes={};visuals={};chapters=[];passages=0;nulls=0
    for path in sorted(SOURCE.glob('b*.ks.json')):
        source=json.loads(path.read_text('utf8'));chapter=source['name'].removesuffix('.ks')
        chapters.append({'id':chapter,'title':source['scenes'][0]['title'][2]})
        for scene in source['scenes']:
            key=chapter+':'+scene['label'];frames=[]
            for index,text in enumerate(scene.get('texts',[])):
                if text[2] is None:nulls+=1;continue
                translated=text[2][2]
                if translated is None:raise ValueError(f'Missing Chinese: {key}/{index}')
                snapshot=[e for e in text[-1].get('data',[]) if e[1] in ('bu','stage','event','character','noevent','layer')]
                raw=json.dumps(snapshot,ensure_ascii=False,sort_keys=True,separators=(',',':'))
                visual=hashlib.sha256(raw.encode()).hexdigest()[:20]
                if visual in visuals:assert visuals[visual]==snapshot
                visuals[visual]=snapshot
                frames.append({'speaker':clean_text(translated[0]),'text':clean_text(translated[1]),'visual':visual,'sourceIndex':index})
            chunks=[]
            # Hard bound both passage count and serialized UTF-8 bytes per load.
            batch=[]
            for frame in frames:
                if batch and (len(batch)>=48 or len(json.dumps(batch+[frame],ensure_ascii=False).encode('utf8'))>24000):
                    name=f'{chapter}/{scene["label"].lstrip("*")}-{len(chunks):03}.json'
                    write(OUT/'story'/name,batch);chunks.append({'file':name,'count':len(batch)});batch=[]
                batch.append(frame)
            if batch:
                name=f'{chapter}/{scene["label"].lstrip("*")}-{len(chunks):03}.json'
                write(OUT/'story'/name,batch);chunks.append({'file':name,'count':len(batch)})
            node={'chapter':chapter,'title':scene['title'][2],'count':len(frames),'chunks':chunks,'next':[],'choices':[],'complete':[]}
            for expr in scene.get('postevals',[]):
                m=re.fullmatch(r'kag.errorCmd\("実績:(b\d+)クリア"\)',expr)
                if m:node['complete'].append(m[1])
                elif expr.replace(' ','')=='sf.allcflag=1':node['allClear']=True
                else:raise ValueError('Unrecognized posteval: '+expr)
            for item in scene.get('selects',[]):
                disabled=item.get('disabled')=='true'
                node['choices'].append({'text':item['language'][2]['text'],'when':condition(item.get('eval')),'effect':effect(item.get('exp')),'disabled':disabled,'to':None if disabled else destination(item,source['name'])})
            # Choices take precedence over the SCN fallback successor.
            if not node['choices']:
                for item in scene.get('nexts',[]):node['next'].append({'when':condition(item.get('eval')),'to':destination(item,source['name'])})
            assert key not in nodes;nodes[key]=node;passages+=len(frames)
    for key,node in nodes.items():
        for item in node['choices']+node['next']:
            assert item['to'] in (None,'@title') or item['to'] in nodes,(key,item)
    graph={'format':1,'initial':'b999:*start','trueEnding':'b701:*start','trueRequires':['b501','b601'],'chapters':chapters,'nodes':nodes}
    write(OUT/'graph.json',graph);write(OUT/'visual-snapshots.json',visuals)
    report={'chapters':len(chapters),'nodes':len(nodes),'passages':passages,'nullTextRecords':nulls,'uniqueVisualSnapshots':len(visuals),'choiceNodes':sum(bool(n['choices']) for n in nodes.values()),'chunks':sum(len(n['chunks']) for n in nodes.values()),'maxChunkBytes':max(p.stat().st_size for p in (OUT/'story').rglob('*.json')),'status':'intermediate; watch UI and visual mapping pending'}
    write(ROOT/'reports/story-conversion.json',report);print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
