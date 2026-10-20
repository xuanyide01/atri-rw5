"""Deliver the exact auto-reading build after focused integration checks."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parents[1]/'outputs'
read=lambda p:json.loads((ROOT/p).read_text('utf-8-sig'))
version=read('src/manifest.json')['versionName'];assert version=='0.1.6'
native_dir='native-test-results/v016'
raw=(ROOT/f'dist/com.codex.atri.rw5.debug.{version}.rpk').read_bytes();sha=hashlib.sha256(raw).hexdigest()
package=read('reports/package-audit.json');diff=read('reports/auto-reader-revision.json');unit=read('reports/auto-reader-unit.json')
native=read(native_dir+'/auto-reader-report.json');scroll=read(native_dir+'/auto-scroll-report.json');extra=read(native_dir+'/extra-report.json');installed=read('reports/installed-script-check.json');logic=read('reports/runtime-check.json')
assert len(raw)<=10500000 and package['sha256']==sha
assert all(r['packageSha256']==sha for r in (diff,native,scroll,extra,installed))
assert all(r['passed'] for r in (diff,unit,native,scroll,extra,logic))
assert all(package[k] for k in ('zipCRCValid','outerSignatureValid','innerSignatureValid','allFileDigestsValid','fontCoverageValid'))
assert diff['allStoryAndArtBytesUnchanged'] and diff['originalSaveAndBranchEngineUnchanged']
assert native['legacySlot1Restored'] and native['choiceNeverAutoSelected'] and native['resumesAfterManualChoice'] and native['autoOffAfterRestart'] and native['speedPersistsAfterRestart']
assert scroll['automaticReadingResumesAfterActualScroll'] and extra['dialogueDragDoesNotAdvance'] and extra['largeFontChecked']
assert installed['installedScriptMatchesPackage'] and installed['installedManifestAndChangedAssetsMatch']
name='ATRI-RW5-'+version+'-轻量版'
for ext in ('.bin','.rpk'):
    target=OUT/(name+ext);assert not target.exists() or target.read_bytes()==raw;target.write_bytes(raw)
(OUT/(name+'-安装说明.md')).write_text((ROOT/'README.md').read_text('utf8'),encoding='utf8')
(OUT/(name+'-SHA256.txt')).write_text(''.join(sha+'  '+name+ext+'\n' for ext in ('.bin','.rpk')),encoding='utf8')
report={'game':'ATRI','author':'xuanyide','implementation':'Codex','version':version,'variant':'仅亚托莉独立立绘轻量版','physicalDeviceTested':False,'status':'自动播放/三档速度新增；准确新版官方模拟器和逻辑检查通过，实机待确认','package':package,'independentRevision':diff,'timerAndPageUnitTests':unit,'nativeAutoReading':native,'nativeScrollWithAutoReading':scroll,'nativeTextAndScrollRegression':extra,'actualInstalledResources':installed,'storyLogic':logic,'physicalBaseline':read('reports/physical-test-v015.json'),'verificationNote':'0.1.5实机通过仅作为旧版基线；本版重新验证自动播放、旧存档读取、滑动和大字号，不声称重新读取所有30栏位或穷举实机剧情。全部剧情与图片字节不变，未测量本版实机内存/帧率。'}
(OUT/(name+'-检查报告.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
for filename in ('auto-reader-report.json','auto-scroll-report.json','extra-report.json'):
    (ROOT/'reports'/('native-v016-'+filename)).write_bytes((ROOT/native_dir/filename).read_bytes())
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
(OUT/(name+'-自动播放菜单.png')).write_bytes((ROOT/native_dir/'auto-menu-enabled.png').read_bytes())
print(json.dumps({'version':version,'packageBytes':len(raw),'sha256':sha,'sourceZipBytes':archive.stat().st_size,'physicalDeviceTested':False},ensure_ascii=False))
