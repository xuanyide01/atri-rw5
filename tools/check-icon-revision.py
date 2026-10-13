"""Confirm the only asset change is the launcher icon, using the tested 0.1.2."""
from pathlib import Path
import json,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[1]
version=json.loads((ROOT/'src/manifest.json').read_text('utf8'))['versionName']
old=ROOT.parents[1]/'outputs/ATRI-RW5-0.1.2.bin';new=ROOT/f'dist/com.codex.atri.rw5.debug.{version}.rpk'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
physical=json.loads((ROOT/'reports/physical-test-v012.json').read_text('utf8'))
assert physical['installationSucceeded'] and physical['packageSha256']==sha(old)
with zipfile.ZipFile(old) as a,zipfile.ZipFile(new) as b:
    assert set(a.namelist())==set(b.namelist())
    changed=[n for n in a.namelist() if a.read(n)!=b.read(n)]
    assert 'common/logo.png' in changed
    for n in changed:
        if n in ('manifest.json','manifest-watch.json'):
            x=json.loads(a.read(n));y=json.loads(b.read(n));assert y['versionCode']>x['versionCode']
            for m in (x,y):
                m.pop('versionCode');m.pop('versionName')
                if 'packageInfo' in m:m['packageInfo'].pop('timeStamp')
            assert x==y
        elif n=='app.js':
            x=json.loads(a.read('manifest-watch.json'));y=json.loads(b.read('manifest-watch.json'))
            s=a.read(n).replace(('"versionCode":'+str(x['versionCode'])).encode(),('"versionCode":'+str(y['versionCode'])).encode())
            s=s.replace(('"versionName":"'+x['versionName']+'"').encode(),('"versionName":"'+y['versionName']+'"').encode());assert s==b.read(n)
        else:assert n=='common/logo.png' or n.startswith('META-INF/'),('Unexpected change',n)
report={'passed':True,'version':version,'packageSha256':sha(new),'physicalTestedBaselineSha256':sha(old),'changedEntries':changed,'allNonIconResourcesAndMainPageByteIdentical':True,'fontAndStorageKeysUnchanged':True,'physicalDeviceTestedForNewVersion':False,'physicalBaselineReport':physical}
(ROOT/'reports/icon-revision.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
