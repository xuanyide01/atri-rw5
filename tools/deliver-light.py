"""Deliver the exact emulator-checked Atri-only package, retaining full 0.1.3."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parents[1]/'outputs';OUT.mkdir(exist_ok=True)
read=lambda p:json.loads((ROOT/p).read_text('utf-8-sig'))
version=read('src/manifest.json')['versionName'];assert version=='0.1.5'
current='native-test-results/v015'
audit=read('reports/package-audit.json');diff=read('reports/portrait-alignment-audit.json');assets=read('reports/atri-only-assets.json')
native=read(current+'/installation-report.json');portrait=read(current+'/portrait-alignment-report.json');fresh=read(current+'/fresh-install.json');installed=read('reports/installed-script-check.json');logic=read('reports/runtime-check.json')
extra=read('native-test-results/v014/extra-report.json');visual=read('native-test-results/v014/visual-report.json');previous=read('reports/atri-only-audit.json')
raw=(ROOT/f'dist/com.codex.atri.rw5.debug.{version}.rpk').read_bytes();sha=hashlib.sha256(raw).hexdigest()
assert len(raw)<=10500000 and sha==audit['sha256']
assert all(r['packageSha256']==sha for r in (diff,native,portrait,installed))
assert all(r['packageSha256']==diff['baselineSha256'] for r in (extra,visual,previous))
assert all(audit[k] for k in ('zipCRCValid','outerSignatureValid','innerSignatureValid','allFileDigestsValid','fontCoverageValid','circularIcon'))
assert diff['passed'] and diff['allOriginalBackgroundAndCGBytesIdentical'] and diff['allTextSpeakersAndBranchesIdentical'] and diff['runtimePageAndSaveEngineByteIdentical']
assert native['passed'] and native['coldBootSlot30Restored'] and native['legacySlot1Restored'] and extra['passed']
assert portrait['passed'] and portrait['visualAlignmentVerified'] and len(portrait['pixelComparison'])==3
assert visual['passed'] and len(visual['pixelComparison'])==5
assert fresh['freshInstallation'] and fresh['oldPackageAbsentBeforeInstall'] and 'success 0' in fresh['result']
assert installed['installedScriptMatchesPackage'] and installed['installedManifestAndChangedAssetsMatch'] and logic['passed']
name='ATRI-RW5-'+version+'-轻量版'
for suffix in ('.bin','.rpk'):
    p=OUT/(name+suffix);assert not p.exists() or p.read_bytes()==raw,('Existing delivery differs',p);p.write_bytes(raw)
(OUT/(name+'-安装说明.md')).write_text((ROOT/'README.md').read_text('utf8'),encoding='utf8')
(OUT/(name+'-SHA256.txt')).write_text(''.join(sha+'  '+name+s+'\n' for s in ('.bin','.rpk')),encoding='utf8')
report={'game':'ATRI','author':'xuanyide','implementation':'Codex','version':version,'variant':'仅保留亚托莉独立立绘的轻量版','target':'approximately 10 MB','maximumPackageBytes':10500000,'physicalDeviceTested':False,'status':'立绘放大贴合修复；新版模拟器全新安装/冷启动/旧存档及三种立绘显示验证通过，实机待确认','package':audit,'assetChangesFromFullVersion':assets,'independentComparison':diff,'nativeInstallation':native,'nativePortraitAlignment':portrait,'freshInstallation':fresh,'actualInstalledResources':installed,'inheritedBaselineValidation':{'packageSha256':diff['baselineSha256'],'comparison':previous,'logic':logic,'nativeTextAndScroll':extra,'nativeVisual':visual,'note':'滚动/大字号与五处CG像素核对沿用0.1.4记录；0.1.5仅显示矩形和版本元数据改变，并未重跑所有剧情。'},'physicalBaseline':read('reports/physical-test-v013.json'),'verificationNote':'12,172条文本、分支与存档引擎和全部图片字节保留。新准确包的报告保留本次摘要，继承验证保留0.1.4摘要。0.1.3实机通过记录仅为基线，不宣称0.1.5已实机测试，也不宣称本轮重新读取了所有30栏位。'}
(OUT/(name+'-检查报告.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
files=[]
for p in ROOT.rglob('*'):
    if not p.is_file():continue
    rel=p.relative_to(ROOT)
    if rel.parts[0] not in ('src','tools','runtime','licenses','reports','converted') and rel.name not in ('README.md','LICENSE','package.json','WORK_PROGRESS.md'):continue
    if rel.parts[0]=='converted' and rel.as_posix()!='converted/graph.json':continue
    if rel.parts[0]=='reports' and 'visual-inspect' in rel.parts:continue
    if 'node_modules' in rel.parts or '__pycache__' in rel.parts or p.suffix in ('.pem','.pyc','.log'):continue
    files.append((p,rel.as_posix()))
archive=OUT/(name+'-源码.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p,rel in sorted(files,key=lambda x:x[1]):z.write(p,'atri-rw5/'+rel)
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
assert archive.stat().st_size<=15000000
preview=ROOT/(current+'/portrait-b102-155.png');assert preview.is_file();(OUT/(name+'-立绘预览.png')).write_bytes(preview.read_bytes())
print(json.dumps({'version':version,'variant':'Atri-only','binBytes':len(raw),'sha256':sha,'sourceZipBytes':archive.stat().st_size,'physicalDeviceTested':False},ensure_ascii=False))
