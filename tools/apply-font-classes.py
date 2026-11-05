from pathlib import Path
import re
r=Path(__file__).resolve().parents[1];p=r/'tools/ui-template.txt';t=p.read_text('utf8')
def extra(m):
 s=m.group().replace('font-family:atrifont;','')
 s=re.sub(r'class="([^"]+)"',lambda n:'class="'+n.group(1)+' embedded-text"',s)
 return s.replace(' style=""','')
t=re.sub(r'<text\b[^>]*font-family:atrifont;[^>]*>',extra,t).replace(' style=""','');p.write_text(t,encoding='utf8')
