"""Read-only inventory of the supplied Steam archives; no original files written."""
from pathlib import Path
import json,hashlib,collections,zlib
from xp3 import index,payload

ROOT=Path('G:/SteamLibrary/steamapps/common/ATRI -My Dear Moments-')
PROJECT=Path(__file__).resolve().parents[1];OUT=PROJECT.parent/'atri-probe'
OUT.mkdir(exist_ok=True)
rows=[]
for path in sorted(ROOT.glob('*.xp3')):
    entries=index(path)
    (OUT/(path.name+'.index.json')).write_text(json.dumps(entries,ensure_ascii=False,indent=2),encoding='utf8')
    samples=[]
    for item in entries[1:5]:
        try:
            raw=payload(path,item)
            samples.append({'name':item['name'],'flags':item['flags'],'bytes':len(raw),'prefix':raw[:24].hex(),'adlerMatches':zlib.adler32(raw)&0xffffffff==item.get('adler')})
            if path.stem in ['data','bgimage','fgimage']:(OUT/(path.stem+'-'+item['name']+'.raw')).write_bytes(raw)
        except Exception as e:samples.append({'name':item['name'],'error':str(e)})
    row={'archive':path.name,'bytes':path.stat().st_size,'entries':len(entries),'extensions':dict(collections.Counter(Path(e['name']).suffix for e in entries)),'samples':samples}
    rows.append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
modules=[]
for p in ROOT.rglob('*'):
    if p.suffix.lower() not in ['.exe','.dll','.tpm']:continue
    modules.append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
report={'source':'User supplied Steam ATRI -My Dear Moments-','originalReadOnly':True,'archives':rows,'modules':modules}
(PROJECT/'reports/source-inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('INVENTORY_COMPLETE',len(rows),'archives',len(modules),'modules')
