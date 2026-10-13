"""Deliver 0.1.2 with separate current font/install and inherited story checks."""
from pathlib import Path
import json,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parents[1]/'outputs';OUT.mkdir(exist_ok=True)
read=lambda p:json.loads((ROOT/p).read_text('utf8'))
version=read('src/manifest.json')['versionName'];assert version=='0.1.2'
current='native-test-results/v'+version.replace('.','')
audit=read('reports/package-audit.json');delta=read('reports/installation-revision.json');font=read('reports/install-font-audit.json')
native=read(current+'/installation-report.json');extra=read(current+'/extra-report.json');fresh=read(current+'/fresh-install.json');installed=read('reports/installed-script-check.json')
baseline=read('native-test-results/v011/report.json');visual=read('native-test-results/v011/visual-report.json');presentation=read('reports/presentation-audit.json')
raw=(ROOT/f'dist/com.codex.atri.rw5.debug.{version}.rpk').read_bytes();sha=hashlib.sha256(raw).hexdigest()
assert len(raw)<=15000000
assert all(r['packageSha256']==sha for r in (delta,native,extra,installed)) and audit['sha256']==sha
assert all(audit[k] for k in ('zipCRCValid','outerSignatureValid','innerSignatureValid','allFileDigestsValid','fontCoverageValid'))
assert delta['passed'] and delta['mainPageAllImagesTextsChoicesAndSaveKeysByteIdenticalToFailedPackage'] and delta['allNonFontGameplayResourcesByteIdenticalToCompleteNativeBaseline']
assert font['passed'] and font['allMappedOutlinesAndHorizontalMetricsIdentical'] and font['codepoints']==2779
assert native['passed'] and native['coldBootSlot30Restored'] and extra['passed'] and installed['installedScriptMatchesPackage']
assert fresh['freshInstallation'] and fresh['oldPackageAbsentBeforeInstall'] and 'success 0' in fresh['result']
assert baseline['result']=='passed' and baseline['coldBoot30Slots'] and baseline['trueEndingReached'] and len(baseline['routes'])==5
assert baseline['packageSha256']==visual['packageSha256']==delta['completeNativeBaselineSha256']
assert visual['passed'] and len(visual['pixelComparison'])==5 and presentation['passed']
name='ATRI-RW5-'+version
for suffix in ('.bin','.rpk'):
    target=OUT/(name+suffix)
    assert not target.exists() or target.read_bytes()==raw,('Existing delivery differs',target)
    target.write_bytes(raw)
(OUT/(name+'-安装说明.md')).write_text((ROOT/'README.md').read_text('utf8'),encoding='utf8')
(OUT/(name+'-SHA256.txt')).write_text(''.join(sha+'  '+name+suffix+'\n' for suffix in ('.bin','.rpk')),encoding='utf8')
report={'game':'ATRI','author':'xuanyide','implementation':'Codex','version':version,'maximumPackageBytes':15000000,'status':'0.1.1实机全新安装失败；0.1.2官方Vela模拟器全新安装、冷启动和字体验证通过，实机修复待确认','physicalFailureOfPreviousVersionReported':True,'physicalDeviceTestedForThisVersion':False,'physicalFixConfirmed':False,'rootCauseConfirmed':False,'package':audit,'fontOptimization':font,'fontOnlyRevisionProof':delta,'freshEmulatorInstallation':fresh,'installedScriptVerification':installed,'currentNative':native,'currentNativeTextAndScroll':extra,'inheritedNativeBaseline':baseline,'inheritedNativeVisualBaseline':visual,'sourceCorrespondence':presentation,'physicalFailureInvestigation':read('reports/installation-issue-v011.json'),'verificationNote':'完整30栏位/5路线/真结局及5处CG像素检查保留基线摘要，没有声称全部在0.1.2重跑。本版重测全新安装、冷启动、第30栏位分页保存读取、点击对白、CG差分、长对白滚动和大字号，全部字符轮廓和横向字宽逐字一致。实机安装失败原因仍不确定。'}
(OUT/(name+'-检查报告.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
archive=OUT/(name+'-源码.zip');files=[]
for p in ROOT.rglob('*'):
    if not p.is_file():continue
    rel=p.relative_to(ROOT)
    if rel.parts[0] not in ('src','tools','runtime','licenses','reports','converted') and rel.name not in ('README.md','LICENSE','package.json','WORK_PROGRESS.md'):continue
    if rel.parts[0]=='converted' and rel.as_posix()!='converted/graph.json':continue
    if rel.parts[0]=='reports' and 'visual-inspect' in rel.parts:continue
    if 'node_modules' in rel.parts or '__pycache__' in rel.parts or p.suffix in ('.pem','.pyc','.log'):continue
    files.append((p,rel.as_posix()))
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p,rel in sorted(files,key=lambda x:x[1]):z.write(p,'atri-rw5/'+rel)
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
assert archive.stat().st_size<=15000000,'Source ZIP exceeds 15 MB'
print(json.dumps({'binBytes':len(raw),'sha256':sha,'sourceZipBytes':archive.stat().st_size,'files':len(files),'physicalFixConfirmed':False},ensure_ascii=False))
