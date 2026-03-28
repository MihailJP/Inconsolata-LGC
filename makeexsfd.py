#!/usr/bin/env fontforge

import fontforge
from psMat import skew, translate, scale
from math import radians
from sys import argv
from typing import Optional

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
    for lookup in (lu for lu in font.gpos_lookups if not font.getLookupSubtables(lu)):
        font.removeLookup(lookup)

def decomposition(glyph: fontforge.glyph) -> list:
    def toDec(hexText: str) -> Optional[int]:
        try:
            return int(hexText, 16)
        except ValueError:
            return None
    from unicodedata import decomposition
    if glyph.user_decomp:
        return [ord(c) for c in glyph.user_decomp]
    elif glyph.unicode < 0:
        return []
    else:
        decomp = [toDec(c) for c in decomposition(chr(glyph.unicode)).split() if toDec(c) is not None]
        if len(decomp) >= 2:
            return decomp
        else:
            return []

def add_dottedcircle(font: fontforge.font):
    from math import radians, sin, cos
    top, bottom = 554, -14
    centerX = 613 / 2
    centerY = (top + bottom) / 2
    dotRadius = 40 if 'Bold' in font.weight else 30
    radius = top - centerY - dotRadius
    font.createChar(0x25cc, 'dottedcircle')
    font['dottedcircle'].width = 613
    circle = fontforge.unitShape(0).transform(scale(dotRadius))
    for deg in range(0, 360, 30):
        font['dottedcircle'].layers[1] += circle.dup().transform(translate(radius * cos(radians(deg)) + centerX, radius * sin(radians(deg)) + centerY))
    font['dottedcircle'].round()

def diacritics(font: fontforge.font):
    add_dottedcircle(font)
    diacriticdata = [
        ('gravemodifier', 'grave.cap', 0x300, 'gravecomb'),
        ('acute', 'acute.cap', 0x301, 'acutecomb'),
        ('circumflex', 'circumflex.cap', 0x302, 'circumflexcomb'),
        ('tilde', None, 0x303, 'tildecomb'),
        ('macronmodifier', None, 0x304, 'macroncomb'),
        ('breve', None, 0x306, 'brevecomb'),
        ('dotaccent', None, 0x307, 'dotaccentcmb'),
        ('dieresis', None, 0x308, 'dieresiscmb'),
        ('hookabove', 'hookabove.cap', 0x309, 'hookabovecomb'),
        ('ring', None, 0x30a, 'ringcmb'),
        ('hungarumlaut', 'hungarumlaut.cap', 0x30b, 'hungarumlautcmb'),
        ('caron', 'caron.cap', 0x30c, 'caroncomb'),
        ('verticallinemod', None, 0x30d, 'verticallineabovecmb'),
        ('dblgrave', 'dblgrave.cap', 0x30f, 'dblgravecmb'),
        ('invertedbreve', None, 0x311, 'breveinvertedcmb'),
        ('dotsub', None, 0x323, 'dotbelowcomb'),
        ('uni02F3', None, 0x325, 'ringbelowcmb'),
        ('commaaccent', None, 0x326, 'commasubnosp'),
        ('cedilla', None, 0x327, 'cedillacmb'),
        ('ogonek', None, 0x328, 'ogonekcmb'),
        ('verticallinelowmod', None, 0x329, 'verticallinebelowcmb'),
        ('uniA788', None, 0x32d, 'circumflexbelowcmb'),
        ('uni02F7', None, 0x330, 'tildebelowcmb'),
        ('macronsub', None, 0x331, 'macronbelowcmb'),
        ('uni02BF', None, 0x351, 'uni0351'),
        ('uni02BE', None, 0x357, 'uni0357'),
    ]
    for sourcename, capsourcename, targetuni, targetname in diacriticdata:
        font.createChar(targetuni, targetname)
        font[targetname].width = 0
        font[targetname].addReference(sourcename, translate(-613, 0))
        font[targetname].glyphclass = 'mark'
        if capsourcename:
            font.createChar(-1, targetname + '.cap')
            font[targetname + '.cap'].width = 0
            font[targetname + '.cap'].addReference(capsourcename, translate(-613, 0))
            font[targetname + '.cap'].glyphclass = 'mark'

    # Precomposed forms
    customDecomp = {
        # Vietnamese tone mark
        'Acircumflexdotbelow': ('Acircumflex', 'dotbelowcomb'),
        'acircumflexdotbelow': ('acircumflex', 'dotbelowcomb'),
        'Abrevedotbelow': ('Abreve', 'dotbelowcomb'),
        'abrevedotbelow': ('abreve', 'dotbelowcomb'),
        'Ecircumflexdotbelow': ('Ecircumflex', 'dotbelowcomb'),
        'ecircumflexdotbelow': ('ecircumflex', 'dotbelowcomb'),
        'Ocircumflexdotbelow': ('Ocircumflex', 'dotbelowcomb'),
        'ocircumflexdotbelow': ('ocircumflex', 'dotbelowcomb'),
    }
    proscribedDecomp = {
        # Duplicate
        'tonos': [('space', 'acutecomb')],
    }
    all_lang = font.getLookupInfo('Variants of zero')[2][0][1]
    font.addLookup('Precomposed forms', 'gsub_ligature', None, (('ccmp', all_lang),))
    font.addLookupSubtable('Precomposed forms', 'Precomposed forms-1')
    for glyph in font.glyphs():
        if (decomp := decomposition(glyph)) and all([font.findEncodingSlot(c) >= 0 for c in decomp]):
            if len(decomp) == 2 and decomp[1] in (c[2] for c in diacriticdata):
                components = tuple(font[font.findEncodingSlot(c)].glyphname for c in decomp)
                if glyph.glyphname not in proscribedDecomp or all([components != p for p in proscribedDecomp[glyph.glyphname]]):
                    glyph.addPosSub('Precomposed forms-1', components)
                    glyph.glyphclass = 'baseglyph'
    for glyph in customDecomp:
        font[glyph].addPosSub('Precomposed forms-1', customDecomp[glyph])
        font[glyph].glyphclass = 'baseglyph'

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
diacritics(font)
font.mergeFonts(argv[3])
font.encoding = 'UnicodeFull'
font.save(argv[1])
