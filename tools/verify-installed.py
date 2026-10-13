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
with zipfile.ZipFile(package) as z:expected=z.read('pages/index/index.js')
actual=destination.read_bytes()
report={'installedScriptMatchesPackage':actual==expected,'packageSha256':hashlib.sha256(package.read_bytes()).hexdigest(),'expectedSHA256':hashlib.sha256(expected).hexdigest(),'actualSHA256':hashlib.sha256(actual).hexdigest()}
(ROOT/'reports/installed-script-check.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(report)
assert actual==expected,'Simulator is running an older package; do not accept its tests.'
