from pathlib import Path
import json,hashlib,zipfile,subprocess
ROOT=Path(__file__).resolve().parents[1]
adb=ROOT.parent/'starry-rw5/node_modules/@miwt/adb/bin/win/adb.exe'
manifest=json.loads((ROOT/'src/manifest.json').read_text('utf8'))
version=manifest['versionName']
destination=ROOT/('native-test-results/v'+version.replace('.','')+'/installed-index.js')
destination.parent.mkdir(parents=True,exist_ok=True)
subprocess.run([str(adb),'-s','emulator-5558','pull','/data/app/com.codex.atri.rw5/pages/index/index.js',str(destination)],check=True,timeout=30)
package=ROOT/('dist/'+manifest['package']+'.debug.'+version+'.rpk')
with zipfile.ZipFile(package) as z:
    expected=z.read('pages/index/index.js')
    samples=['manifest-watch.json']
    old=ROOT.parents[1]/'outputs/ATRI-RW5-0.1.3.bin'
    if old.exists():
        with zipfile.ZipFile(old) as baseline:
            for prefix,suffix in [('common/story/','.txt'),('common/images/','.png')]:
                names=[n for n in z.namelist() if n.startswith(prefix) and n.endswith(suffix)]
                changed=[n for n in names if n in baseline.namelist() and z.read(n)!=baseline.read(n)]
                if changed:samples.append(changed[0])
    verified=[]
    for name in samples:
        local=destination.parent/'installed-assets'/name;local.parent.mkdir(parents=True,exist_ok=True)
        subprocess.run([str(adb),'-s','emulator-5558','pull','/data/app/com.codex.atri.rw5/'+name,str(local)],check=True,timeout=30)
        assert local.read_bytes()==z.read(name),('Simulator asset/manifest is stale',name)
        verified.append(name)
actual=destination.read_bytes()
report={'installedScriptMatchesPackage':actual==expected,'installedManifestAndChangedAssetsMatch':True,'verifiedManifestAndAssets':verified,'packageSha256':hashlib.sha256(package.read_bytes()).hexdigest(),'expectedSHA256':hashlib.sha256(expected).hexdigest(),'actualSHA256':hashlib.sha256(actual).hexdigest()}
(ROOT/'reports/installed-script-check.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(report)
assert actual==expected,'Simulator is running an older package; do not accept its tests.'
