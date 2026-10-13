"""Validate every horizontal glyph against the failed physical-install package."""
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
import io,json,zipfile,hashlib
ROOT=Path(__file__).resolve().parents[1];oldpath=ROOT.parents[1]/'outputs/ATRI-RW5-0.1.1.bin'
with zipfile.ZipFile(oldpath) as z:old=TTFont(io.BytesIO(z.read('common/atri-text.otf')))
new=TTFont(ROOT/'src/common/atri-text.otf');a,b=old.getBestCmap(),new.getBestCmap()
assert set(a)==set(b);ga,gb=old.getGlyphSet(),new.getGlyphSet()
for cp in sorted(a):
    pa=DecomposingRecordingPen(ga);pb=DecomposingRecordingPen(gb)
    ga[a[cp]].draw(pa);gb[b[cp]].draw(pb)
    assert pa.value==pb.value,(hex(cp),'glyph outline changed')
    assert old['hmtx'][a[cp]]==new['hmtx'][b[cp]],(hex(cp),'horizontal advance changed')
assert old['head'].unitsPerEm==new['head'].unitsPerEm
report={'passed':True,'originalFontBytes':len(old.reader.file.getvalue()),'newFontBytes':(ROOT/'src/common/atri-text.otf').stat().st_size,'originalGlyphs':len(old.getGlyphOrder()),'newGlyphs':len(new.getGlyphOrder()),'codepoints':len(a),'allMappedOutlinesAndHorizontalMetricsIdentical':True,'physicalFailureCauseConfirmed':False,'hypothesis':'Large single compressed font entry/installer memory burden. Removing unused shaping and vertical glyphs lowers resource peak; no physical installer logs yet.'}
(ROOT/'reports/install-font-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
