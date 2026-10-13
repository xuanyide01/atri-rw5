"""Reuse completed runtime checks only if the last change is title art alone."""
from pathlib import Path
import json,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[1]
old=ROOT/'native-test-results/v011/tested-with-logos.rpk';new=ROOT/'dist/com.codex.atri.rw5.debug.0.1.1.rpk'
native=json.loads((ROOT/'native-test-results/v011/report.json').read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert native['result']=='passed' and native['packageSha256']==sha(old)
with zipfile.ZipFile(old) as a,zipfile.ZipFile(new) as b:
    assert set(a.namelist())==set(b.namelist());changed=[n for n in a.namelist() if a.read(n)!=b.read(n)]
    assert 'common/title_bg.jpg' in changed
    for name in changed:
        if name in ('manifest.json','manifest-watch.json'):
            x=json.loads(a.read(name));y=json.loads(b.read(name));assert y['versionCode']>x['versionCode'];x.pop('versionCode');y.pop('versionCode')
            if 'packageInfo' in x:x['packageInfo'].pop('timeStamp');y['packageInfo'].pop('timeStamp')
            assert x==y
        elif name=='app.js':
            oldcode=json.loads(a.read('manifest-watch.json'))['versionCode'];newcode=json.loads(b.read('manifest-watch.json'))['versionCode']
            assert a.read(name).replace(('"versionCode":'+str(oldcode)).encode(),('"versionCode":'+str(newcode)).encode())==b.read(name)
        else:assert name=='common/title_bg.jpg' or name.startswith('META-INF/'),('Unexpected runtime/resource change',name)
    assert a.read('pages/index/index.js')==b.read('pages/index/index.js')
report={'passed':True,'packageSha256':sha(new),'baselinePackageSha256':sha(old),'changedEntries':changed,'runtimeAndAllGameplayResourcesByteIdentical':True,'bootstrapOnlyVersionCodeUpdated':True,'method':'Only title art, version/build metadata and signatures differ. Main page logic and all gameplay resources are byte-identical. Complete baseline emulator tests retain their original hash; final title and exit are tested separately.'}
(ROOT/'reports/final-title-revision.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
