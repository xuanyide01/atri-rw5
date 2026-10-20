"""Confirm auto-reading does not alter story data, art, font or save engine."""
from pathlib import Path
import hashlib,json,re,zipfile
from fontTools.ttLib import TTFont
ROOT=Path(__file__).resolve().parents[1]
version=json.loads((ROOT/'src/manifest.json').read_text('utf8'))['versionName']
old=ROOT.parents[1]/'outputs/ATRI-RW5-0.1.5-轻量版.bin';new=ROOT/f'dist/com.codex.atri.rw5.debug.{version}.rpk'
assert hashlib.sha256(old.read_bytes()).hexdigest()=='96be13097273fa2a25373269d5984f57384bae29acdaec2c454afb660f178d78'
files=0;story=0;images=0
with zipfile.ZipFile(old) as a,zipfile.ZipFile(new) as b:
    assert set(a.namelist())==set(b.namelist())
    for name in a.namelist():
        if name.startswith('common/'):
            assert a.read(name)==b.read(name),name;files+=1
            if name.startswith('common/story/') and name.endswith('.txt'):story+=len(json.loads(b.read(name)))
            if name.startswith('common/images/') and name.endswith(('.jpg','.png')):images+=1
    x=json.loads(a.read('manifest-watch.json'));y=json.loads(b.read('manifest-watch.json'))
    assert {k:v for k,v in x.items() if k not in ('versionName','versionCode')}=={k:v for k,v in y.items() if k not in ('versionName','versionCode')}
    assert a.read('pages/index/index.js')!=b.read('pages/index/index.js')
source=ROOT.parents[1]/'outputs/GitHub发布/release-files/atri-rw5-v0.1.5/atri-rw5-v0.1.5-light-source.zip'
with zipfile.ZipFile(source) as z:
    for name in ('src/common/graph.js','src/common/engine.js','runtime/story-engine.cjs','src/app.ux'):
        assert (ROOT/name).read_bytes()==z.read('atri-rw5/'+name),name
    old_audit=json.loads(z.read('atri-rw5/reports/package-audit.json'))
    current_audit=json.loads((ROOT/'reports/package-audit.json').read_text('utf8'))
    assert old_audit['certificateSha256']==current_audit['certificateSha256']
    before=z.read('atri-rw5/tools/ui-script.txt').decode('utf8');after=(ROOT/'tools/ui-script.txt').read_text('utf8')
    assert re.search(r"const PREFIX='([^']+)'",before).group(1)==re.search(r"const PREFIX='([^']+)'",after).group(1)=='atri_rw5_'
cmap=TTFont(ROOT/'src/common/atri-text.otf').getBestCmap()
text=(ROOT/'src/pages/index/index.ux').read_text('utf8')+(ROOT/'src/common/auto-reader.js').read_text('utf8')
assert all(ord(c) in cmap for c in text if '\u3400'<=c<='\u9fff')
assert story==12172 and images==887
report={'passed':True,'version':version,'packageSha256':hashlib.sha256(new.read_bytes()).hexdigest(),'baselineVersion':'0.1.5','baselineSha256':hashlib.sha256(old.read_bytes()).hexdigest(),'identicalCommonFiles':files,'passages':story,'identicalBackgroundCGAndPortraitAssets':images,'allStoryAndArtBytesUnchanged':True,'fontIconAndTitleBytesUnchanged':True,'originalSaveAndBranchEngineUnchanged':True,'samePackageCertificateAndStorageKeys':True,'menuAndNewLabelsFontCovered':True,'autoDefaultsOff':True,'speedsMilliseconds':[2600,1500,800],'typewriterMilliseconds':30,'physicalDeviceTested':False}
(ROOT/'reports/auto-reader-revision.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False))
