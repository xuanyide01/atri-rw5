"""User-selected accessibility policy: every choice can be selected.
Only remove the final shoe choice's availability gate. Earlier state changes and
all successor/end conditions remain exactly as converted from the original.
"""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
changed=[]
for name in ['converted/graph.json','src/common/graph.js']:
 p=R/name;text=p.read_text('utf8');is_js=name.endswith('.js');g=json.loads(text.removeprefix('export const graph=').strip().removesuffix(';'))
 n=g['nodes']['b402:*dummyselect1'];shoe=next(x.copy() for x in n['choices'] if x['text']=='捡起鞋子' and x['to']=='b402:*402_a');bad=next(x.copy() for x in n['choices'] if x['text']=='放着不管')
 assert shoe['effect'] is None and bad['effect']==['set',0]
 shoe.update(when=None,disabled=False);n['choices']=[shoe,bad]
 assert all(not x['disabled'] and x['to'] for n in g['nodes'].values() for x in n['choices'])
 p.write_text(('export const graph=' if is_js else '')+json.dumps(g,ensure_ascii=False,separators=(',',':'))+(';' if is_js else '')+'\n',encoding='utf8');changed.append(name)
(R/'reports/choice-policy.json').write_text(json.dumps({'policy':'all choices selectable; original prior-choice state and ending conditions preserved','modifiedNode':'b402:*dummyselect1','newAvailability':'unconditional','shoeEffect':None,'shoeDestination':'b402:*402_a','badEffect':['set',0],'saveFormat':1,'noBadEndingPrerequisite':True,'note':'This deliberately differs from the original greyed-out shoe option, as explicitly requested by the user.'},ensure_ascii=False,indent=2),encoding='utf8')
print('CHOICE_POLICY',str(R),changed)
