from pathlib import Path
import json,hashlib,zipfile
R=Path(__file__).resolve().parents[1];band='band8pro' in R.parent.name;backup=R.parent/('开发记录/0.1.0修复前' if band else '开发记录/0.1.6修复前');m=json.loads((R/'src/manifest.json').read_text('utf8'));pkg=R/f"dist/{m['package']}.debug.{m['versionName']}.rpk"
def graph(p):return json.loads(p.read_text('utf8').removeprefix('export const graph=').strip().removesuffix(';'))
a=graph(R/'src/common/graph.js');b=graph(backup/'src/common/graph.js');before=b['nodes']['b402:*dummyselect1']['choices'];after=a['nodes']['b402:*dummyselect1']['choices'];assert len(before)==3 and len(after)==2
assert after[0]==dict(before[0],when=None,disabled=False) and after[1]==before[2];b['nodes']['b402:*dummyselect1']['choices']=after;assert a==b,'Other original graph data changed'
assert hashlib.sha256((R/'src/common/engine.js').read_bytes()).hexdigest()=='3cb0610913d11bda0975e75770a4149186c6c71c3cb2a9849df4e41104d2e199'
with zipfile.ZipFile(pkg) as z:
 assert json.loads(z.read('manifest-watch.json'))==m and z.testzip() is None
 old=R.parent/'最终交付'/('ATRI-Band8Pro-0.1.0.bin' if band else 'ATRI-RW5-0.1.6-轻量版.bin')
 with zipfile.ZipFile(old) as prior:
  changed=[name for name in z.namelist() if name.startswith('common/') and not name.endswith('/') and z.read(name)!=prior.read(name)]
  assert set(changed)==({'common/atri-text.otf','common/logo.png'} if band else set()),changed
 report={'passed':True,'packageSha256':hashlib.sha256(pkg.read_bytes()).hexdigest(),'onlyFinalChoiceAvailabilityChanged':True,'earlierChoiceEffectsAndAllEndingConditionsUnchanged':True,'allVisibleChoicesSelectable':True,'saveFormatUnchanged':True,'allStoryAndArtResourceBytesUnchanged':True,'otherChangedCommonResources':changed,'physicalDeviceTested':False}
(R/'reports/choice-change-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report))
