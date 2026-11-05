"""Rebuild a small conditional font using the tested Paper Band strategy.

Default text deliberately has no font-family. Only actual missing glyphs route to
an embedded font; punctuation such as the middle dot must not switch a whole UI
label away from the firmware font. No SDK font data is redistributed.
"""
from pathlib import Path
import argparse,json,hashlib,re
from fontTools import subset
from fontTools.ttLib import TTFont
R=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--source',default=str(R.parents[1]/'shinuyakata-rw5/研究/NotoSansCJKsc-Regular.otf'));parser.add_argument('--default-font',default=str(R.parent/'开发记录/模拟器环境/sdk/qa/font/MiSansW_Normal.ttf'));a=parser.parse_args()
source=Path(a.source);default=Path(a.default_font);cm=TTFont(default).getBestCmap();strings=[];story=[]
for p in (R/'src/common/story').rglob('*.txt'):
 for f in json.loads(p.read_text('utf8')):
  strings.extend([f['text'],f['speaker']]);story.extend([f['text'],f['speaker']])
gallery=json.loads((R/'src/common/gallery.txt').read_text('utf8'))
for group in gallery:
 strings.append(group['label'])
 for i in range(len(group['variants'])):strings.append(group['label']+' · '+str(i+1)+' / '+str(len(group['variants']))+' · 点击切换')
ui=(R/'tools/ui-template.txt').read_text('utf8')+(R/'tools/ui-script.txt').read_text('utf8')
# Include static UI characters if a rare-glyph label combines them with story text.
ui_chars=set(re.findall(r'[^\x00-\x7f]',ui));triggers=sorted({c for s in strings for c in s if not c.isspace() and ord(c)>=32 and ord(c) not in cm})
affected=[s for s in strings if set(triggers).intersection(s)]
chars=set(chr(c) for c in range(32,127))|ui_chars|set(''.join(affected))
font=TTFont(source);original=font.getBestCmap();coverage={ord(c) for c in chars if ord(c) in original}
assert not [c for c in chars if not c.isspace() and ord(c)>=32 and ord(c) not in original]
# Retain the source's font metadata and layout tables, as Paper 0.1.1 does.
options=subset.Options();options.name_IDs=['*'];options.name_languages=['*']
subsetter=subset.Subsetter(options=options);subsetter.populate(unicodes=coverage);subsetter.subset(font)
for name in font['name'].names:
 if name.nameID in (1,3,4,6,16):name.string='AtriBandExtra'.encode(name.getEncoding(),errors='replace')
if 'CFF ' in font:font['CFF '].cff.fontNames=['AtriBandExtra']
output=R/'src/common/atri-text.otf';font.save(output);actual=TTFont(output).getBestCmap();assert coverage==set(actual)
assert output.stat().st_size<655856
js='const extra='+json.dumps(''.join(triggers),ensure_ascii=False)+";\nexport function textFont(text){const value=String(text||'');for(let i=0;i<extra.length;i++)if(value.indexOf(extra[i])>=0)return 'atrifont';return '';}\n"
(R/'src/common/text-font.js').write_text(js,encoding='utf8')
for s in strings:
 fontmap=actual if set(triggers).intersection(s) else cm
 assert all(c.isspace() or ord(c)<32 or ord(c) in fontmap for c in s),repr(s)
assert '·' not in triggers
report={'passed':True,'strategy':'Paper Band 0.1.1: no explicit default family, small conditional supplementary font, preserved source metadata/layout','referenceFont':'official SDK MiSansW_Normal.ttf','referenceFontSha256':hashlib.sha256(default.read_bytes()).hexdigest(),'sourceFontFamily':TTFont(source)['name'].getDebugName(1),'sourceFontSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'fontBytes':output.stat().st_size,'embeddedCodepoints':len(actual),'affectedStrings':len(affected),'embeddedFallbackTriggers':triggers,'defaultCGCaptions':True,'allRenderedStringsCovered':True,'allDefaultBranchStoryCharactersCoveredBySDKFont':True,'physicalFirmwareCoverageClaimed':False,'previousPhysicalFeedback':'0.1.0 CG labels displayed tofu around separators and 点击切换','note':'SDK字形检查不等于实机固件；0.1.1实机待复测。'}
(R/'reports/font-compatibility.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False))
