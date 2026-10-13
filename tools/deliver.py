"""Copy only a size-compliant package whose exact hash passed native validation."""
from pathlib import Path
import json,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parents[1]/'outputs';OUT.mkdir(exist_ok=True)
audit=json.loads((ROOT/'reports/package-audit.json').read_text('utf8'))
native=json.loads((ROOT/'native-test-results/v011/report.json').read_text('utf8'))
package=ROOT/'dist/com.codex.atri.rw5.debug.0.1.1.rpk';raw=package.read_bytes();sha=hashlib.sha256(raw).hexdigest()
delta=json.loads((ROOT/'reports/final-title-revision.json').read_text('utf8'))
smoke=json.loads((ROOT/'native-test-results/v011/final-title-report.json').read_text('utf8'))
assert len(raw)<=15000000 and sha==audit['sha256']==delta['packageSha256']==smoke['packageSha256']
assert delta['passed'] and delta['runtimeAndAllGameplayResourcesByteIdentical'] and smoke['passed']
assert delta['baselinePackageSha256']==native['packageSha256']==smoke['baselinePackageSha256']
assert native['result']=='passed' and native['coldBoot30Slots'] and native['trueEndingReached']
visual=json.loads((ROOT/'native-test-results/v011/visual-report.json').read_text('utf8'))
presentation=json.loads((ROOT/'reports/presentation-audit.json').read_text('utf8'))
assert visual['passed'] and visual['packageSha256']==delta['baselinePackageSha256'] and len(visual['pixelComparison'])==5 and presentation['passed']
name='ATRI-RW5-0.1.1'
for suffix in ('.bin','.rpk'):(OUT/(name+suffix)).write_bytes(raw)
(OUT/(name+'-安装说明.md')).write_text((ROOT/'README.md').read_text('utf8'),encoding='utf8')
(OUT/(name+'-SHA256.txt')).write_text(''.join(sha+'  '+name+suffix+'\n' for suffix in ('.bin','.rpk')),encoding='utf8')
report={'game':'ATRI','author':'xuanyide','implementation':'Codex','version':'0.1.1','maximumPackageBytes':15000000,'status':'官方Vela模拟器验证通过；等待REDMI Watch 5实机确认','physicalDeviceTested':False,'package':audit,'native':native,'nativeVisual':visual,'sourceCorrespondence':presentation,'presentation':json.loads((ROOT/'reports/watch-assets.json').read_text('utf8')),'portraitOptimization':json.loads((ROOT/'reports/portrait-size-optimization.json').read_text('utf8'))}
report.update({'finalTitleRevision':delta,'finalTitleVerification':smoke,'verificationNote':'完整原生剧情/30旧存档/5个CG验证报告保留原测试包摘要。最终修订仅移除标题logo，正文脚本和全部游戏资源字节一致；最终准确包另做冷安装、标题、开始和退出验证。'})
(OUT/(name+'-检查报告.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
# Generated watch source is sufficient to rebuild. Do not bundle the original
# archives, research DLLs, SDK, signing keys, external tools or emulator disks.
archive=OUT/(name+'-源码.zip')
files=[]
for p in ROOT.rglob('*'):
    if not p.is_file():continue
    rel=p.relative_to(ROOT)
    if rel.parts[0] not in ('src','tools','runtime','licenses','reports','converted') and rel.name not in ('README.md','LICENSE','package.json','WORK_PROGRESS.md'):continue
    if rel.parts[0]=='converted' and rel.as_posix()!='converted/graph.json':continue
    if rel.parts[0]=='reports' and 'visual-inspect' in rel.parts:continue
    if '__pycache__' in rel.parts or p.suffix in ('.pem','.pyc','.log'):continue
    files.append((p,rel.as_posix()))
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p,rel in sorted(files,key=lambda x:x[1]):z.write(p,'atri-rw5/'+rel)
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
assert archive.stat().st_size<=15000000,'Generated source archive exceeds 15 MB'
print(json.dumps({'binBytes':len(raw),'sha256':sha,'sourceZipBytes':archive.stat().st_size,'files':len(files),'physicalDeviceTested':False},ensure_ascii=False))
