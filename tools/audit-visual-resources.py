"""Inventory exact image references before selecting or compressing watch art."""
from pathlib import Path
import json,collections
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT.parent/'atri-probe/extracted'
index=collections.defaultdict(list)
for p in SOURCE.rglob('*'):
    if p.suffix.lower() in ('.png','.jpg','.tlg','.pimg'):index[p.stem].append(p)
snaps=json.loads((ROOT/'converted/visual-snapshots.json').read_text('utf8'));refs=collections.defaultdict(set)
for snapshot in snaps.values():
    for name,kind,state in snapshot:
        image=state.get('redraw',{}).get('imageFile')
        if image and kind not in ('bu','character') and state.get('showmode') in (1,3):refs[image['file']].add(kind)
resolved=[];missing=[];ambiguous=[]
for name,kinds in sorted(refs.items()):
    matches=index[name]
    item={'name':name,'classes':sorted(kinds)}
    if not matches:missing.append(item);continue
    item['files']=[str(p.relative_to(SOURCE)).replace('\\','/') for p in matches]
    if len(matches)!=1:ambiguous.append(item);continue
    p=matches[0]
    if p.suffix.lower() in ('.jpg','.png'):
        with Image.open(p) as image:item.update(size=image.size,mode=image.mode)
    resolved.append(item)
report={'uniqueReferences':len(refs),'resolved':resolved,'unresolved':missing,'ambiguous':ambiguous,'note':'Exact stem match only. Unresolved names may be procedural/animated effects and require original config evidence before omission.'}
(ROOT/'reports/visual-resource-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'unique':len(refs),'resolved':len(resolved),'unresolved':len(missing),'ambiguous':len(ambiguous)},ensure_ascii=False))
print('Unresolved:',', '.join(x['name'] for x in missing))
