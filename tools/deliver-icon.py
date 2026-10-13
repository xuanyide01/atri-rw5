"""Deliver an icon-only revision without relabelling older runtime tests."""
from pathlib import Path
import json,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parents[1]/'outputs';OUT.mkdir(exist_ok=True)
read=lambda p:json.loads((ROOT/p).read_text('utf8'))
version=read('src/manifest.json')['versionName'];assert version=='0.1.3'
audit=read('reports/package-audit.json');delta=read('reports/icon-revision.json');cover=read('reports/title-icon.json');physical=read('reports/physical-test-v012.json')
raw=(ROOT/f'dist/com.codex.atri.rw5.debug.{version}.rpk').read_bytes();sha=hashlib.sha256(raw).hexdigest()
assert len(raw)<=15000000 and sha==audit['sha256']==delta['packageSha256']
assert delta['passed'] and delta['allNonIconResourcesAndMainPageByteIdentical'] and delta['fontAndStorageKeysUnchanged']
assert physical['installationSucceeded'] and physical['packageSha256']==delta['physicalTestedBaselineSha256']
assert all(audit[k] for k in ('zipCRCValid','outerSignatureValid','innerSignatureValid','allFileDigestsValid','fontCoverageValid','circularIcon'))
icon=(ROOT/'src/common/logo.png').read_bytes();assert hashlib.sha256(icon).hexdigest()==cover['iconSha256']
with zipfile.ZipFile(ROOT/f'dist/com.codex.atri.rw5.debug.{version}.rpk') as z:assert z.read('common/logo.png')==icon
name='ATRI-RW5-'+version
for suffix in ('.bin','.rpk'):
    p=OUT/(name+suffix);assert not p.exists() or p.read_bytes()==raw,('Existing delivery differs',p);p.write_bytes(raw)
(OUT/(name+'-封面.png')).write_bytes(icon)
(OUT/(name+'-安装说明.md')).write_text((ROOT/'README.md').read_text('utf8'),encoding='utf8')
(OUT/(name+'-SHA256.txt')).write_text(''.join(sha+'  '+name+s+'\n' for s in ('.bin','.rpk')),encoding='utf8')
report={'game':'ATRI','author':'xuanyide','implementation':'Codex','version':version,'maximumPackageBytes':15000000,'physicalDeviceTestedForThisVersion':False,'status':'0.1.2由用户确认REDMI Watch 5实机安装运行正常；0.1.3只更换圆形标题背景图标及版本签名元数据，静态校验与字节差异检查通过','package':audit,'iconRevision':delta,'coverSource':cover,'physicalBaseline':physical,'inheritedEmulatorInstallation':read('native-test-results/v012/installation-report.json'),'inheritedEmulatorTextChecks':read('native-test-results/v012/extra-report.json'),'verificationNote':'继承测试保留0.1.2原摘要；没有声称0.1.3重新执行了实机或所有剧情检查。'}
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
print(json.dumps({'version':version,'binBytes':len(raw),'sha256':sha,'sourceZipBytes':archive.stat().st_size,'files':len(files),'onlyIconAndMetadataChanged':True},ensure_ascii=False))
