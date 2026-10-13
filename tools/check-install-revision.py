"""Prove a font/metadata-only delta against the actual failed installation package."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1]
version=json.loads((ROOT/'src/manifest.json').read_text('utf8'))['versionName']
old=ROOT.parents[1]/'outputs/ATRI-RW5-0.1.1.bin'
new=ROOT/f'dist/com.codex.atri.rw5.debug.{version}.rpk'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
previous=json.loads((ROOT/'reports/final-title-revision.json').read_text('utf8'))
assert previous['passed'] and previous['packageSha256']==sha(old)
baseline=ROOT/'native-test-results/v011/tested-with-logos.rpk'
assert sha(baseline)==previous['baselinePackageSha256']
with zipfile.ZipFile(old) as a,zipfile.ZipFile(new) as b:
    assert set(a.namelist())==set(b.namelist())
    changed=[n for n in a.namelist() if a.read(n)!=b.read(n)]
    for name in changed:
        if name in ('manifest.json','manifest-watch.json'):
            x=json.loads(a.read(name));y=json.loads(b.read(name))
            assert y['versionCode']>x['versionCode']
            for m in (x,y):
                m.pop('versionCode');m.pop('versionName')
                if 'packageInfo' in m:m['packageInfo'].pop('timeStamp')
            assert x==y
        elif name=='app.js':
            x=json.loads(a.read('manifest-watch.json'));y=json.loads(b.read('manifest-watch.json'))
            normalized=a.read(name).replace(('"versionCode":'+str(x['versionCode'])).encode(),('"versionCode":'+str(y['versionCode'])).encode())
            normalized=normalized.replace(('"versionName":"'+x['versionName']+'"').encode(),('"versionName":"'+y['versionName']+'"').encode())
            assert normalized==b.read(name)
        else:assert name=='common/atri-text.otf' or name.startswith('META-INF/'),('Unexpected change',name)
    assert a.read('pages/index/index.js')==b.read('pages/index/index.js')
    assert a.read('common/title_bg.jpg')==b.read('common/title_bg.jpg')
    with zipfile.ZipFile(baseline) as c:
        assert set(c.namelist())==set(b.namelist())
        # Verify the complete native baseline directly rather than trusting prose.
        for n in b.namelist():
            if n in ('common/title_bg.jpg','common/atri-text.otf','manifest.json','manifest-watch.json','app.js') or n.startswith('META-INF/'):continue
            assert c.read(n)==b.read(n),('Gameplay changed relative to tested baseline',n)
font=json.loads((ROOT/'reports/install-font-audit.json').read_text('utf8'))
assert font['passed'] and font['allMappedOutlinesAndHorizontalMetricsIdentical']
report={'passed':True,'version':version,'packageSha256':sha(new),'failedPhysicalPackageSha256':sha(old),'completeNativeBaselineSha256':sha(baseline),'changedEntries':changed,'mainPageAllImagesTextsChoicesAndSaveKeysByteIdenticalToFailedPackage':True,'allNonFontGameplayResourcesByteIdenticalToCompleteNativeBaseline':True,'titleByteIdenticalToFailedPackage':True,'bootstrapOnlyVersionUpdated':True,'fontMappedOutlinesAndMetricsIdentical':True,'physicalFixConfirmed':False}
(ROOT/'reports/installation-revision.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False))
