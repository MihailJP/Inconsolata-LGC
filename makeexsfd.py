#!/usr/bin/env fontforge

import fontforge
from psMat import skew
from math import radians
from sys import argv

def removeUnusedAnchorClass(font: fontforge.font):
    subtables = sum([list(font.getLookupSubtables(a)) for a in font.gpos_lookups], [])
    anchors = sum([list(font.getLookupSubtableAnchorClasses(s)) for s in subtables], [])
    for anchor in anchors:
        mark = any(len([a for a in glyph.anchorPoints if a[0] == anchor and a[1] == 'mark' and glyph.width == 0]) for glyph in font.glyphs())
        base = any(len([a for a in glyph.anchorPoints if a[0] == anchor and a[1] != 'mark']) for glyph in font.glyphs())
        print([anchor, mark, base])
        if not all([mark, base]):
            font.removeAnchorClass(anchor)
    for subtable in (s for s in subtables if not font.getLookupSubtableAnchorClasses(s)):
        print(subtable)
        font.removeLookupSubtable(subtable)
    for lookup in font.gpos_lookups:
        font.removeLookup(lookup)

font = fontforge.open(argv[2])
font2 = fontforge.open(argv[3])
font.encoding = 'Original'
font2.encoding = 'Original'
font.fontname = font.fontname.replace('LGC', 'EX')
font.familyname = font.familyname.replace('LGC', 'EX')
font.fullname = font.fullname.replace('LGC', 'EX')
font.copyright += '\n\nArabic glyphs are derived from public domain part of DejaVu Sans Mono.'
font.os2_winascent = 1255
font.os2_windescent = 290
if font.italicangle != 0:
    font2.selection.all()
    font2.transform(skew(radians(-font.italicangle)), ('noWidth', 'round', 'simplePos'))
removeUnusedAnchorClass(font2)
font.mergeFonts(argv[3])
font.encoding = 'UnicodeFull'
font.save(argv[1])
