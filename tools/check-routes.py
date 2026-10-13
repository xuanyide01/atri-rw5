"""Exhaust reachable choices against the original SCN flag conditions."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
g=json.loads((ROOT/'converted/graph.json').read_text('utf8'))
def matches(test,flag):return test is None or ((flag==test[1]) if test[0]=='==' else (flag!=test[1]))
def walk(key,flag=0,path=(),complete=(),seen=()):
    assert len(seen)<150,'Loop in story graph'
    if key=='@title':return [{'choices':path,'flag':flag,'completed':complete,'nodes':len(seen)}]
    node=g['nodes'][key];complete=complete+tuple(node['complete'])
    if node['choices']:
        options=[o for o in node['choices'] if matches(o['when'],flag) and not o['disabled']]
        assert options,'No enabled choices'
        result=[]
        for o in options:
            e=o['effect'];new=flag if not e else e[1] if e[0]=='set' else flag+e[1]
            result+=walk(o['to'],new,path+(o['text'],),complete,seen+(key,))
        return result
    targets=[t for t in node['next'] if matches(t['when'],flag)]
    assert targets,'Unexpected dead end '+key
    return walk(targets[0]['to'],flag,path,complete,seen+(key,))
routes=walk(g['initial'])
assert len(routes)==5,len(routes)
happy=[r for r in routes if 'b501' in r['completed']]
bad=[r for r in routes if 'b601' in r['completed']]
assert len(happy)==1 and len(bad)==4
assert happy[0]['choices']==('亚托莉先放在我这','吻她','捡起鞋子')
assert all(r['flag']!=11 for r in bad)
true=walk(g['trueEnding']);assert len(true)==1 and 'b701' in true[0]['completed']
assert g['trueRequires']==['b501','b601']
for done in [[],['b501'],['b601'],['b501','b601']]:assert all(x in done for x in g['trueRequires'])==(len(done)==2)
report={'reachablePlaythroughs':len(routes),'happy':len(happy),'bad':len(bad),'true':len(true),'routes':routes,'note':'Graph and converted conditions verified. Device runtime and chapter-skip tests pending.'}
(ROOT/'reports/route-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print('PASS: five reachable normal-play choice paths (1 happy, 4 bad), true-ending graph, unlock condition, no missing targets or unexpected dead ends.')
