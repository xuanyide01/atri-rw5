"""Reposition lightweight portraits from immutable 0.1.4; no image recompression."""
from pathlib import Path
import hashlib,json,zipfile
from PIL import Image
from portrait_layout import aligned_sprite

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT.parents[1]/'outputs/ATRI-RW5-0.1.4-轻量版.bin'
assert hashlib.sha256(BASE.read_bytes()).hexdigest()=='3b971542bb25e78be2d9c0c7fa1b1a88d2ef8074ec3ea210cf2fad813c51252d'
count=0
with zipfile.ZipFile(BASE) as z:
    for name in z.namelist():
        if not(name.startswith('common/story/') and name.endswith('.txt')):continue
        frames=json.loads(z.read(name))
        for frame in frames:
            sprites=frame['art']['sprites']
            for index,sprite in enumerate(sprites):
                with Image.open(ROOT/'src'/sprite['src'].lstrip('/')) as image:
                    sprites[index]=aligned_sprite(sprite,image.size,len(sprites)==1)
                count+=1
        (ROOT/'src'/name).write_text(json.dumps(frames,ensure_ascii=False,separators=(',',':')),encoding='utf8')
assert count==5065
print('Aligned',count,'portrait references without changing images, dialogue or branches.')
