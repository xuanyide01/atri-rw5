"""Download public tool artifacts into the workspace, with hashes for provenance."""
from pathlib import Path
import urllib.request,hashlib,json,concurrent.futures,zipfile
ROOT=Path(__file__).resolve().parents[2]/'atri-tools';ROOT.mkdir(exist_ok=True)
items={
 'GARbro.rar':'https://github.com/morkt/GARbro/releases/download/v1.5.44/GARbro-v1.5.44.2904.rar',
 'GARbro-Mod.zip':'https://codeload.github.com/nanami5270/GARbro-Mod/zip/refs/heads/master',
 'FreeMote.zip':'https://github.com/UlyssesWu/FreeMote/releases/download/v4.8.0/Ulysses-FreeMoteToolkit-v4.8.0.zip'}
def get(item):
    name,url=item;p=ROOT/name
    if not p.exists():
        with urllib.request.urlopen(url,timeout=90) as r,p.open('wb') as f:
            while b:=r.read(1024*1024):f.write(b)
    row={'name':name,'url':url,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    print(json.dumps(row),flush=True)
    if p.suffix=='.zip':
        out=ROOT/p.stem
        with zipfile.ZipFile(p) as z:
            assert z.testzip() is None
            assert all((out/n).resolve().is_relative_to(out.resolve()) for n in z.namelist())
            z.extractall(out)
    return row
with concurrent.futures.ThreadPoolExecutor(3) as ex:rows=list(ex.map(get,items.items()))
(ROOT/'downloads.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8')
