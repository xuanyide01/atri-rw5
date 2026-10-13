"""Original title art/buttons with a compact sea-themed watch menu area."""
from PIL import Image,ImageDraw

def build_title(source,probe,out):
    title=Image.new('RGB',(432,514));draw=ImageDraw.Draw(title)
    for y in range(243,514):
        t=(y-243)/271;draw.line((0,y,431,y),fill=tuple(round(a+(b-a)*t) for a,b in zip((236,247,253),(213,234,247))))
    # Quiet sea contours behind a thin translucent-looking menu panel.
    for offset in range(4):draw.arc((250-offset*22,324-offset*12,572+offset*18,601+offset*16),170,320,fill='#bad9eb',width=1)
    draw.rounded_rectangle((18,253,413,494),radius=15,fill='#f2f9fd',outline='#bed9e9',width=1)
    draw.line((32,278,32,475),fill='#92bdd6',width=2)
    draw.line((48,492,390,492),fill='#d6e9f4',width=1)
    # Lower-right menu area deliberately remains blank.
    with Image.open(source/'data/image/title_base2.png') as image:title.paste(image.convert('RGB').resize((432,243),Image.Resampling.LANCZOS),(0,0))
    title.save(out/'title_bg.jpg',quality=87,optimize=True)
    with Image.open(source/'data/image/title_logo_cn.png') as image:
        logo=image.crop(image.getbbox());logo.thumbnail((190,84),Image.Resampling.LANCZOS);logo.save(out/'title_logo.png',optimize=True)
    for name,index in [('true_end',1122),('start',1124),('load',1125),('gallery',1127),('exit',1129)]:
        with Image.open(probe/'title-ui/title'/(str(index)+'.png')) as image:image.save(out/('title_'+name+'.png'),optimize=True)
    dialogue=Image.new('RGB',(432,228));d=ImageDraw.Draw(dialogue)
    for y in range(228):
        t=y/227;d.line((0,y,431,y),fill=tuple(round(x+(z-x)*t) for x,z in zip((225,231,236),(194,205,216))))
    dialogue.save(out/'dialogue_bg.jpg',quality=86,optimize=True)
    unused=out/'title_true_end_locked.png'
    if unused.exists():unused.unlink()
    unused=out/'title_chapter.png'
    if unused.exists():unused.unlink()
