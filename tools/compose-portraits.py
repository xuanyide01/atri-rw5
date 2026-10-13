"""Resolve original .stand/.sinfo/PBD rules and precompose transparent portraits.

Uses extracted game layers, not inferred faces. Unresolved layers are reported
and block completeness; never silently substitute an unrelated character.
"""
from pathlib import Path
import json,re,unicodedata,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];PROBE=ROOT.parent/'atri-probe'
FG=PROBE/'extracted/fgimage';LAYERS=PROBE/'layers';OUT=PROBE/'portraits'
norm=lambda s:unicodedata.normalize('NFKC',s)

def rules(base):
    result={'dress':{},'names':{},'aliases':{}}
    for line in (FG/(base+'.sinfo.utf8.txt')).read_text('utf8').splitlines():
        a=line.split()
        if not a:continue
        if a[0]=='dress':result['dress'][(a[1],a[2],a[3] if a[2]=='diff' else '')]=norm(a[-1])
        elif a[0]=='fgname':result['names'][norm(a[1])]=norm(a[2])
        elif a[0]=='fgalias':result['aliases'][norm(a[1])]=[norm(x) for x in a[2:]]
    return result

RULES={p.name.split('.')[0]:rules(p.name.split('.')[0]) for p in FG.glob('*.sinfo.utf8.txt')}
STANDS={p.name.removesuffix('.utf8.txt'):re.findall(r'"filename"=>"([^"]+)"',p.read_text('utf8')) for p in FG.glob('*.stand.utf8.txt')}
PBD={p.name.removesuffix('_s.pbd.json'):p for p in FG.rglob('*_s.pbd.json')}

def compose(filename,options):
    dress=options.get('dress','d1');pose=options.get('pose','p1');face=norm(options.get('face',''))
    candidates=[b for b in STANDS[filename] if (dress,'diff',pose) in RULES[b]['dress']]
    if len(candidates)!=1:raise ValueError(f'Pose not unique: {filename}/{dress}/{pose}: {candidates}')
    base=candidates[0];rule=RULES[base];pbd=PBD[base];records=json.loads(pbd.read_text('utf8'));byid={r['layer_id']:r for r in records[1:]}
    def fullname(r):
        group=byid.get(r.get('group_layer_id'))
        return (fullname(group)+'/' if group else '')+norm(r['name'])
    layers={fullname(r):r for r in records[1:] if r['layer_type']==0}
    wanted=[rule['dress'][(dress,'diff',pose)]]
    if (dress,'base','') in rule['dress']:wanted.append(rule['dress'][(dress,'base','')])
    tokens=face.split(':') if face else []
    expanded=[]
    for token in tokens:expanded.extend(rule['aliases'].get(token,[token]))
    for token in expanded:
        # The p3 source pose has no cheek group at any size. Preserve its defined
        # expression layers; this unsupported decorative request adds no layer.
        if base=='tatr02' and token=='頬1' and not any('頬' in x for x in layers):continue
        if token not in rule['names']:raise ValueError(f'Face token missing {base}: {token}')
        target=rule['names'][token]
        if target!='dummy':wanted.append(target)
    missing=[n for n in wanted if n not in layers]
    if missing:raise ValueError(f'Missing layer paths {base}: {missing}')
    selected={layers[n]['layer_id'] for n in wanted}
    canvas=Image.new('RGBA',(records[0]['width'],records[0]['height']))
    for r in reversed(records[1:]):
        if r.get('layer_id') not in selected:continue
        image=LAYERS/pbd.parent.relative_to(FG)/(base+'_s_'+str(r['layer_id'])+'.png')
        with Image.open(image) as original:
            layer=original.convert('RGBA')
            assert layer.size==(r['width'],r['height']),(image,layer.size,r)
            if r['opacity']!=255:layer.putalpha(layer.getchannel('A').point(lambda p:p*r['opacity']//255))
            canvas.alpha_composite(layer,(r['left'],r['top']))
    box=canvas.getbbox()
    if not box:raise ValueError('Empty portrait '+base)
    cropped=canvas.crop(box);scale=min(1,400/cropped.height)
    resized=cropped.resize((max(1,round(cropped.width*scale)),max(1,round(cropped.height*scale))),Image.Resampling.LANCZOS)
    return resized,{'base':base,'canvas':canvas.size,'crop':box,'selectedLayers':sorted(selected),'size':resized.size}

def main():
    snapshots=json.loads((ROOT/'converted/visual-snapshots.json').read_text('utf8'))
    requests={}
    for snapshot in snapshots.values():
        for name,kind,state in snapshot:
            if kind not in ('bu','character') or state.get('showmode') not in (1,3):continue
            image=state.get('redraw',{}).get('imageFile',{})
            if not image:continue
            key=json.dumps([image['file'],image.get('options',{})],ensure_ascii=False,sort_keys=True)
            requests[key]=(image['file'],image.get('options',{}))
    OUT.mkdir(parents=True,exist_ok=True);index={};errors=[]
    for key,(name,options) in requests.items():
        identifier=hashlib.sha256(key.encode()).hexdigest()[:16]
        try:
            image,meta=compose(name,options);image.save(OUT/(identifier+'.png'),optimize=True)
            index[key]={'id':identifier,**meta}
        except (KeyError,ValueError,AssertionError,FileNotFoundError) as exc:errors.append({'request':json.loads(key),'error':str(exc)})
    (OUT/'index.json').write_text(json.dumps(index,ensure_ascii=False),encoding='utf8')
    report={'requests':len(requests),'composed':len(index),'errors':errors,'note':'Intermediate 400px transparent PNGs. Device compression and visual QA pending.'}
    (ROOT/'reports/portrait-composition.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'requests':len(requests),'composed':len(index),'errors':len(errors)},ensure_ascii=False))
    for error in errors[:8]:print(json.dumps(error,ensure_ascii=False))

if __name__=='__main__':main()
