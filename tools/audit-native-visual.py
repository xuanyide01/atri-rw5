"""Compare actual emulator image area to the independently identified CG assets."""
from pathlib import Path
from PIL import Image
import numpy as np,json
ROOT=Path(__file__).resolve().parents[1]
version=json.loads((ROOT/'src/manifest.json').read_text('utf8'))['versionName']
OUT=ROOT/('native-test-results/v'+version.replace('.',''))
source=json.loads((ROOT/'reports/presentation-audit.json').read_text('utf8'));native=json.loads((OUT/'visual-report.json').read_text('utf8'));audit=json.loads((ROOT/'reports/package-audit.json').read_text('utf8'))
assert native['passed'] and native['packageSha256']==audit['sha256']
results=[]
for entry in source['reportedCGRegressions']:
    name=entry['node'].split(':')[0]+'-'+str(entry['index']);actual=Image.open(OUT/(name+'.png')).convert('RGB').crop((0,0,432,286))
    art=Image.open(ROOT/'src/common/images'/entry['generatedResource']).convert('RGB').resize((432,243),Image.Resampling.BILINEAR)
    errors=[]
    for y in (21,22):
        expected=Image.new('RGB',(432,286),'black');expected.paste(art,(0,y))
        errors.append(float(np.mean(np.abs(np.array(actual).astype(float)-np.array(expected).astype(float)))))
    error=min(errors);assert error<10,(name,error,'Actual emulator did not show expected source CG')
    results.append({'scene':name,'meanChannelError':round(error,3),'matchedOriginalResource':entry['originalResource']})
native['pixelComparison']=results;native['passed']=True
(OUT/'visual-report.json').write_text(json.dumps(native,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(native,ensure_ascii=False))
