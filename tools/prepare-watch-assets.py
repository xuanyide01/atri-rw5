"""Offline still-frame adaptation: whole art, bounded decoded sizes, deduplication.

Original camera motion, particles, audio and video are deliberately omitted.
Story and branches are handled by compile-story.py, never by image heuristics.
"""
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
import json,hashlib,csv,re,io
ROOT=Path(__file__).resolve().parents[1];PROBE=ROOT.parent/'atri-probe';SOURCE=PROBE/'extracted'
OUT=ROOT/'src/common';IMAGES=OUT/'images';IMAGES.mkdir(parents=True,exist_ok=True)
lookup={p.stem.lower():p for p in SOURCE.rglob('*') if p.suffix.lower() in ('.png','.jpg')}
portraits=json.loads((PROBE/'portraits/index.json').read_text('utf8'))
snapshots=json.loads((ROOT/'converted/visual-snapshots.json').read_text('utf8'))
aliases={'lay_white':'#ffffff','lay_black':'#000000'}
ignored=set();cached={};stored={};portrait_assets={};meta={};provenance={}
presentation=re.compile(r'^(?:clip_|mask_|str\d|bgi_|bge|color,|ノイズ|煙|雨|smoke)',re.I)

def store(image,transparent=False,colors=160):
    buffer=io.BytesIO()
    if transparent:
        image=image.convert('RGBA').quantize(colors=colors,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE)
        image.save(buffer,format='PNG',optimize=True)
    else:image.convert('RGB').save(buffer,format='JPEG',quality=70,optimize=True,subsampling=2)
    raw=buffer.getvalue();key=hashlib.sha256(raw).hexdigest()[:16];name=key+('.png' if transparent else '.jpg')
    (IMAGES/name).write_bytes(raw);stored[name]={'size':image.size,'bytes':len(raw),'transparent':transparent}
    return '/common/images/'+name

def image_for(name):
    if name in aliases:return Image.new('RGBA',(320,180),aliases[name])
    if name.startswith('color,'):
        match=re.search(r'color,0x([0-9a-fA-F]+)',name)
        # Original bars are layout effects; omit to keep the full frame visible.
        ignored.add(name);return None
    path=lookup.get(name.lower())
    if not path:ignored.add(name);return None
    with Image.open(path) as source:
        image=source.convert('RGBA')
        if re.match(r'^bg015',name,re.I):image=ImageOps.fit(image,(320,180),method=Image.Resampling.LANCZOS)
        else:image.thumbnail((320,180),Image.Resampling.LANCZOS)
    result=Image.new('RGBA',(320,180));result.alpha_composite(image,((320-image.width)//2,(180-image.height)//2));return result

def background(names,overlays=None):
    key=json.dumps([names,overlays or []],ensure_ascii=False,sort_keys=True)
    if key in cached:return cached[key]
    canvas=Image.new('RGBA',(320,180),'black')
    for name in names:
        image=image_for(name)
        if image is not None:canvas.alpha_composite(image)
    # One shared 1280x720 coordinate space for transparent illustrations.
    # Independently fitting each piece would misregister it with the scene.
    for name,actions in overlays or []:
        with Image.open(lookup[name.lower()]) as original:image=original.convert('RGBA')
        image=image.resize((max(1,round(image.width*actions.get('zoomx',100)/400)),max(1,round(image.height*actions.get('zoomy',100)/400))),Image.Resampling.LANCZOS)
        if actions.get('opacity',255)!=255:image.putalpha(image.getchannel('A').point(lambda p:p*actions['opacity']//255))
        if actions.get('rotate',0):image=image.rotate(-actions['rotate'],resample=Image.Resampling.BICUBIC,expand=True)
        canvas.alpha_composite(image,(round(160+actions.get('xpos',0)/4-image.width/2),round(90+actions.get('ypos',0)/4-image.height/2)))
    cached[key]=store(canvas);return cached[key]

def metadata(name):
    if name not in meta:
        if name in aliases:meta[name]={'size':(1280,720),'solid':True}
        elif name.lower() in lookup:
            with Image.open(lookup[name.lower()]) as image:
                meta[name]={'size':image.size,'solid':image.convert('RGBA').getchannel('A').getextrema()[0]>=200}
        else:meta[name]=None
    return meta[name]

def visible_area(layer):
    a=layer['actions'];w,h=metadata(layer['file'])['size']
    w*=a.get('zoomx',100)/100;h*=a.get('zoomy',100)/100
    x=640+a.get('xpos',0)-w/2;y=360+a.get('ypos',0)-h/2
    return max(0,min(1280,x+w)-max(0,x))*max(0,min(720,y+h)-max(0,y))/(1280*720)

def resolve_scene(layers):
    layers.sort(key=lambda x:(-x['actions'].get('zpos',233 if x['kind']=='stage' else -60),x['actions'].get('order',0),x['index']))
    # The original text snapshots all have a reset global camera. Resolve the
    # active scene by depth/order and actual viewport intersection. Whole CGs
    # replace other opaque scenes; they must not be fitted and stacked together.
    candidates=[x for x in layers if re.match(r'^(bg\d|ev\d)',x['file'],re.I) and metadata(x['file'])['solid'] and x['actions'].get('opacity',255)>=200 and visible_area(x)>.01]
    if not candidates:candidates=[x for x in layers if x['kind']=='stage' and metadata(x['file'])['solid']]
    primary=candidates[-1] if candidates else None
    # Only foreground pieces after the chosen primary can cover it.
    remaining=layers[layers.index(primary)+1:] if primary else layers
    overlays=[(x['file'],x['actions']) for x in remaining if (not metadata(x['file'])['solid'] or not re.match(r'^(bg\d|ev\d|lay_)',x['file'],re.I)) and visible_area(x)>.01]
    return background([primary['file']] if primary else [],overlays),primary,overlays

def portrait(key,meta):
    if meta['id'] in portrait_assets:return portrait_assets[meta['id']]
    with Image.open(PROBE/'portraits'/(meta['id']+'.png')) as source:
        image=source.convert('RGBA')
        # Show head and torso clearly, ending at the dialogue edge instead of
        # shrinking the whole standing figure until facial details disappear.
        image=image.crop((0,0,image.width,round(image.height*.72)))
        atri=meta['base'].startswith('tatr')
        image.thumbnail((220,256) if atri else (200,224),Image.Resampling.LANCZOS)
    asset={'src':store(image,True,256 if atri else 160),'width':round(image.width*286/image.height),'height':286}
    portrait_assets[meta['id']]=asset;return asset

visuals={}
for identifier,snapshot in snapshots.items():
    art=[];people=[];excluded=[]
    for order,(name,kind,state) in enumerate(snapshot):
        if state.get('showmode') not in (1,3):continue
        image=state.get('redraw',{}).get('imageFile',{})
        if not image:continue
        actions=dict((a[0],a[1]) for a in state.get('action',[]) if len(a)>=2)
        if kind in ('bu','character'):
            key=json.dumps([image['file'],image.get('options',{})],ensure_ascii=False,sort_keys=True)
            assert key in portraits,(identifier,key)
            people.append((float(actions.get('xpos',0)),order,actions,key))
        elif presentation.match(image['file']) or metadata(image['file']) is None:
            ignored.add(image['file']);excluded.append(image['file'])
        else:art.append({'name':name,'kind':kind,'file':image['file'],'actions':actions,'index':order})
    bg,primary,overlays=resolve_scene(art)
    provenance[identifier]={'primary':primary['file'] if primary else None,'primaryLayer':primary,'overlays':[x[0] for x in overlays],'omittedPresentation':excluded,'sourceLayers':art,'background':bg}
    visible_people=[]
    for x,order,actions,key in people:
        opacity=actions.get('opacity',255)
        if opacity<=0:continue
        # Opaque CG event layers cover character layers behind their source
        # depth/order. A stage CG can still have characters in front of it.
        rank=(-actions.get('zpos',0),actions.get('order',0),order)
        primary_rank=(-primary['actions'].get('zpos',233 if primary['kind']=='stage' else -60),primary['actions'].get('order',0),primary['index']) if primary else None
        if primary_rank is not None and rank<primary_rank:continue
        asset={**portrait(key,portraits[key]),'opacity':opacity/255}
        visible_people.append((x,order,asset))
    people=sorted(visible_people,key=lambda x:(x[0],x[1]));sprites=[]
    # Keep the lower body touching the top edge of the dialogue panel.
    for i,(x,order,asset) in enumerate(people[:3]):
        center=216 if len(people)==1 else (108+216*i if len(people)==2 else 72+144*i)
        sprites.append({**asset,'left':round(center-asset['width']/2),'top':286-asset['height']})
    visuals[identifier]={'background':bg,'sprites':sprites}

# Build original CG groups, including layered SD art and source-defined variants.
gallery=[]
for row in csv.reader((SOURCE/'vol1/cglist_10.csv.utf8.txt').read_text('utf8').splitlines()):
    if not row or row[0].startswith('#') or row[1]=='movie.ks':continue
    variants=[]
    for cell in row[2:]:
        if not cell:continue
        parts=cell.split('|')
        if len(parts)>1:names=[x for x in parts[1:] if x]
        else:names=[cell.split('?')[0]]
        if not all(n.lower() in lookup or n in aliases for n in names):
            ignored.update(n for n in names if n.lower() not in lookup and n not in aliases)
            continue
        # Gallery SD entries explicitly declare a common 1280x720 canvas.
        variants.append(background(names[:1],[(n,{}) for n in names[1:]]))
    if variants:gallery.append({'label':'CG '+row[0].removeprefix('thum_').upper(),'variants':variants})
for path in (ROOT/'converted/story').rglob('*.json'):
    frames=json.loads(path.read_text('utf8'))
    for frame in frames:frame['art']=visuals[frame.pop('visual')];frame.pop('sourceIndex',None)
    destination=OUT/'story'/path.relative_to(ROOT/'converted/story');destination.parent.mkdir(parents=True,exist_ok=True)
    destination.with_suffix('.txt').write_text(json.dumps(frames,ensure_ascii=False,separators=(',',':')),encoding='utf8')
(OUT/'gallery.txt').write_text(json.dumps(gallery,ensure_ascii=False,separators=(',',':')),encoding='utf8')
(ROOT/'converted/visual-map.json').write_text(json.dumps(provenance,ensure_ascii=False,separators=(',',':')),encoding='utf8')
graph=json.loads((ROOT/'converted/graph.json').read_text('utf8'))
for node in graph['nodes'].values():
    for chunk in node['chunks']:chunk['file']=str(Path(chunk['file']).with_suffix('.txt')).replace('\\','/')
(OUT/'graph.js').write_text('export const graph='+json.dumps(graph,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf8')
# Remove only obsolete generated image hashes inside this project's images folder.
assert IMAGES.resolve().is_relative_to(ROOT.resolve())
for old in IMAGES.iterdir():
    if old.is_file() and re.fullmatch(r'[0-9a-f]{16}\.(png|jpg)',old.name) and old.name not in stored:old.unlink()
from title_assets import build_title
build_title(SOURCE,PROBE,OUT)
# Keep the selected original-title crop when rebuilding all game assets.
icon_asset=ROOT/'tools/assets/atri-title-icon.png'
assert icon_asset.exists(),'Run node tools/build-title-icon.cjs before preparing assets'
(OUT/'logo.png').write_bytes(icon_asset.read_bytes())
report={'backgroundCombinations':len(cached),'portraitCombinations':len(portrait_assets),'deduplicatedImages':len(stored),'imageBytes':sum(x['bytes'] for x in stored.values()),'maxImageBytes':max(x['bytes'] for x in stored.values()),'maxDecodedRGBABytes':max(x['size'][0]*x['size'][1]*4 for x in stored.values()),'galleryGroups':len(gallery),'galleryVariants':sum(len(x['variants']) for x in gallery),'omittedPresentationReferences':sorted(ignored),'note':'Primary source scene resolved by depth/order and viewport intersection; opaque replacements are not fitted and stacked. Whole CG plus registered transparent illustrations; transition masks/camera/particles/audio/video omitted. Title uses original post-clear title_base2 and original PIMG off-button sprites.'}
(ROOT/'reports/portrait-size-optimization.json').write_text(json.dumps({'atriMaxHeight':256,'atriPalette':256,'otherPortraitMaxHeight':224,'otherPalette':160,'displayHeight':286,'imageBytes':report['imageBytes'],'note':'One resize and quantization from original intermediate layers. Do not run the legacy second-pass resize script.'},ensure_ascii=False,indent=2),encoding='utf8')
(ROOT/'reports/watch-assets.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
