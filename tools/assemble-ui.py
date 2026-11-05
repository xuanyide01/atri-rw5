from pathlib import Path
from PIL import Image
root=Path(__file__).resolve().parents[1]
style=(root/'tools/ui-style.txt').read_text('utf-8-sig')
for css,name in [('true','true_end'),('start','start'),('load','load'),('gallery','gallery'),('exit','exit')]:
    with Image.open(root/'src/common'/('title_'+name+'.png')) as im:w=round(im.width*25/im.height)
    style+='\n.title-'+css+'{width:'+str(w)+'px;height:25px;object-fit:contain;}'
(root/'src/pages/index/index.ux').write_text((root/'tools/ui-template.txt').read_text('utf8')+(root/'tools/ui-script.txt').read_text('utf8')+'\n<style>'+style+'</style>\n',encoding='utf8')

