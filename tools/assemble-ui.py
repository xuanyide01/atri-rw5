from pathlib import Path
root=Path(__file__).resolve().parents[1]
template=(root/'tools/ui-template.txt').read_text('utf8')
# Original b999 prologue comes first in the chapter picker, matching normal play.
graph_path=root/'src/common/graph.js'
import json
text=graph_path.read_text('utf8');graph=json.loads(text.removeprefix('export const graph=').strip().removesuffix(';'))
graph['chapters'].sort(key=lambda x:(x['id']!='b999',x['id']))
graph_path.write_text('export const graph='+json.dumps(graph,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf8')
style=(root/'tools/ui-style.txt').read_text('utf8')
from PIL import Image
import re
# Original OFF sprites have different widths but the same 21px cap box. Use
# their real aspect ratios so each label is 30px tall (the previous START size),
# without extra centering inside a wider image box shifting the left edge.
for css,name in [('true','true_end'),('start','start'),('load','load'),('gallery','gallery'),('exit','exit')]:
    with Image.open(root/'src/common'/('title_'+name+'.png')) as image:
        width=round(image.width*30/image.height)
    style=re.sub(r'\.title-'+css+r'\{[^}]+\}',f'.title-{css}{{width:{width}px;height:30px;object-fit:contain;}}',style)
(root/'src/pages/index/index.ux').write_text(template+(root/'tools/ui-script.txt').read_text('utf8')+'\n<style>'+style+'</style>\n',encoding='utf8')
