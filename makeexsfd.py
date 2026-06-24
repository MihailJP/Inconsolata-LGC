#!/usr/bin/env python3

import fontforge
from psMat import skew, translate, scale
from math import radians, tan
from sys import argv
from typing import Optional, Union, Iterable
from copy import deepcopy
import re

type LangTuple = tuple[tuple[str, tuple[str, ...]], ...]
type LangDict = dict[str, set[str]]

def langDictToLangTuple(langdict: LangDict) -> LangTuple:
    return tuple((scr, tuple(sorted(lang)))for scr, lang in langdict.items())

def langTupleToLangDict(langtuple: LangTuple) -> LangDict:
    langdict: LangDict = {}
    for script, languages in langtuple:
        langdict.setdefault(script, set())
        langdict[script] |= set(languages)
    return langdict

def mergeLangDict(langdict1: LangDict, langdict2: LangDict) -> LangDict:
    langdict: LangDict = {}
    for script in sorted(set(list(langdict1.keys()) + list(langdict2.keys()))):
        langdict[script] = langdict1.get(script, set()) | langdict2.get(script, set())
    return langdict

def getLangDict(font: fontforge.font, lookup: Union[str, Iterable[str], None] = None) -> LangDict:
    if isinstance(lookup, str):
        lookups = [lookup]
    elif lookup is None:
        lookups = (font.gsub_lookups + font.gpos_lookups)
    else:
        lookups = lookup
    scripts = sum([list(font.getLookupInfo(lu)[2][0][1]) for lu in lookups if font.getLookupInfo(lu)[2]], [])
    return langTupleToLangDict(tuple(scripts))

def allAnchors(font: fontforge.font) -> tuple[list[str], list[str]]:
    subtables = sum([list(font.getLookupSubtables(a)) for a in font.gpos_lookups], [])
    anchors = sum([list(font.getLookupSubtableAnchorClasses(s)) for s in subtables], [])
    return (anchors, subtables)

def removeUnusedAnchorClass(font: fontforge.font):
    anchors, subtables = allAnchors(font)
    for anchor in anchors:
        mark = any(len([a for a in glyph.anchorPoints if a[0] == anchor and a[1] == 'mark' and glyph.unicode >= 0 and glyph.width == 0]) for glyph in font.glyphs())
        base = any(len([a for a in glyph.anchorPoints if a[0] == anchor and a[1] != 'mark' and glyph.unicode >= 0]) for glyph in font.glyphs())
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
    from unicodedata import decomposition as unidecomp
    if glyph.user_decomp:
        return [ord(c) for c in glyph.user_decomp]
    elif glyph.unicode < 0:
        return []
    else:
        decomp = [toDec(c) for c in unidecomp(chr(glyph.unicode)).split() if toDec(c) is not None]
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

    font.createChar(-1, 'invalidbase')
    font['invalidbase'].width = 613
    font['invalidbase'].addReference('dottedcircle')

dotlessforms: list[tuple[str, str, str]] = [
    ('i', 'dotlessi', 'i'),
    ('j', 'dotlessj', 'j'),
    ('icyril', 'dotlessi', 'i'),
    ('je', 'dotlessj', 'j'),
    ('iogonek', 'iogonek.dotless', 'i'),
    ('ibar', 'ibar.dotless', 'i'),
    ('itildebelow', 'itildebelow.dotless', 'i'),
    ('idotbelow', 'idotbelow.dotless', 'i'),
    ('uni0249', 'jdotlessbar', 'j'),
]

def add_dotlessforms(font: fontforge.font):
    font.addLookup('Dotless forms', 'gsub_single', None, ())
    font.addLookupSubtable('Dotless forms', 'Dotless forms-1')
    for dotted, dotless, _ in dotlessforms:
        font[dotted].addPosSub('Dotless forms-1', dotless)
        font[dotted].glyphclass = 'baseglyph'
    font.addLookup('Remove the dot above i', 'gsub_contextchain', None, (('ccmp', langDictToLangTuple(getLangDict(font))),))
    diacritics = [m.glyphname for m in font.glyphs() if m.width == 0 and 'LGC-accent-above' in [a[0] for a in m.anchorPoints]]
    diacritics += [g for g in font.glyphs() if 'cmb_' in g.glyphname or 'comb_' in g.glyphname]  # combined diacritics
    font.addContextualSubtable(
        'Remove the dot above i',
        'Remove the dot above i-1',
        'class',
        '| 1 @<Dotless forms> | 1',
        mclasses=((), tuple([d[0] for d in dotlessforms])),  # pyright: ignore[reportArgumentType]
        fclasses=((), tuple(diacritics)),  # pyright: ignore[reportArgumentType]
    )

def anchorCoord(font: fontforge.font, x: float, y: float) -> tuple[float, float]:
    return (x - y * tan(radians(font.italicangle)), y)

lgcRange = [
    range(0x0041, 0x005b),  # Basic uppercase letters
    range(0x0061, 0x007b),  # Basic lowercase letters
    range(0x00c0, 0x0530),  # LGC letters
    range(0x1c80, 0x1c90),  # Cyrillic Extended-C
    range(0x1d00, 0x1dc0),  # Phonetic Extensions
    range(0x1e00, 0x1f00),  # Latin Extended Additional
    range(0x2c60, 0x2c80),  # Latin Extended-C
    range(0xa720, 0xa800),  # Latin Extended-D
    range(0xab30, 0xab70),  # Latin Extended-E
    range(0x10780, 0x107c0),  # Latin Extended-F
]

def lgcBaseAnchors(font: fontforge.font):
    def trunkGlyph(glyph: fontforge.glyph) -> Optional[fontforge.glyph]:
        trunkname = re.sub(r'\.(serif|bg|mkd|ewe|nav|kbc|cat|var\d?|pinyin|alt|dotless)+$', '', glyph.glyphname)
        if trunkname == 'fscript':
            trunkname = 'florin'
        if trunkname not in glyph.font or trunkname == glyph.glyphname:
            trunkname = None
        if trunkname:
            return font[trunkname]
        else:
            return None
    type ComposedDict = dict[str, list[tuple[str, list[str]]]]  # pyright: ignore[reportGeneralTypeIssues]
    composed: ComposedDict = {}
    def addComposedVariant(composed: ComposedDict, glyph: fontforge.glyph):
        if '.' in glyph.glyphname:
            suffix, stem = tuple(n[::-1] for n in glyph.glyphname[::-1].split('.', 1))
            if stem in composed:
                composed[glyph.glyphname] = [(d[0] + '.' + suffix, d[1]) for d in composed[stem] if d[0] + '.' + suffix in glyph.font]
    for glyph in font.glyphs():
        if decomp := decomposition(glyph):
            decomp = [(font[font.findEncodingSlot(uni)].glyphname if font.findEncodingSlot(uni) >= 0 else None) for uni in decomp]
            if decomp[0]:
                marks = [g for g in decomp[1:] if g and font[g].width == 0]
                if marks:
                    composed.setdefault(decomp[0], [])
                    composed[decomp[0]].append((glyph.glyphname, marks))
    addComposedVariant(composed, font['r.serif'])
    if 'ii.bg' in font:
        addComposedVariant(composed, font['ii.bg'])
    positions: dict[str, list[list[tuple[float, float]]]] = {}
    excludeBase = [
        'ydotbelow',
        'dieresis', 'psili', 'dasia',
        'uni2373', 'uni2375', 'uni2377', 'uni2378', 'uni237A',
        'Acircumflex', 'Ecircumflex', 'Ocircumflex',
        'acircumflex', 'ecircumflex', 'ocircumflex',
    ]
    excludeComposed = [
        'gcommaaccent', 'ydotbelow',
        'dcaron', 'Lcaron', 'lcaron', 'tcaron',
        'Hcedilla', 'hcedilla',
        'Alphatonos', 'Epsilontonos', 'Etatonos', 'Iotatonos',
        'Omicrontonos', 'Upsilontonos', 'Omegatonos',
        'Alphalenis', 'Epsilonlenis', 'Etalenis', 'Iotalenis',
        'Omicronlenis', 'Omegalenis',
        'Alphaasper', 'Epsilonasper', 'Etaasper', 'Iotaasper',
        'Omicronasper', 'Rhoasper', 'Upsilonasper', 'Omegaasper',
        'Alphagrave', 'Epsilongrave', 'Etagrave', 'Iotagrave',
        'Omicrongrave', 'Upsilongrave', 'Omegagrave',
        'Alphaacute', 'Epsilonacute', 'Etaacute', 'Iotaacute',
        'Omicronacute', 'Upsilonacute', 'Omegaacute',
    ]
    for glyph, composedGlyphs in composed.items():  # base glyphs
        abovePos = []
        belowPos = []
        for composedGlyph, _ in composedGlyphs:
            accentType = ''
            if glyph in excludeBase or composedGlyph in excludeComposed:
                pass
            elif font[composedGlyph].boundingBox()[3] > font[glyph].boundingBox()[3]:  # above
                accentType = 'above'
            elif font[composedGlyph].boundingBox()[1] < font[glyph].boundingBox()[1]:  # below
                accentType = 'below'
            glyphnames = [glyph]
            if glyph in [g[0] for g in dotlessforms]:
                glyphnames += [g[1] for g in dotlessforms if g[0] == glyph]
            if accentType and [r for r in font[composedGlyph].references if r[0] in glyphnames] and len(font[composedGlyph].references) == 2:
                mark, mat, _ = [r for r in font[composedGlyph].references if r[0] not in glyphnames][0]
                if mat[:4] == (1, 0, 0, 1):
                    if accentType == 'above':
                        abovePos.append(tuple(mat[4:]))
                    elif accentType == 'below' and mark != 'ogonek':
                        belowPos.append(tuple(mat[4:]))
        if abovePos or belowPos:
            positions.setdefault(glyph, [[], []])
            if glyph in [g[0] for g in dotlessforms]:
                for dotlessglyph in [g[1] for g in dotlessforms if g[0] == glyph]:
                    positions.setdefault(dotlessglyph, [[], []])
                    positions[dotlessglyph][0] += abovePos
                    positions[dotlessglyph][1] += belowPos
            else:
                positions[glyph][0] += abovePos
            positions[glyph][1] += belowPos
    for glyph in font.glyphs():
        from unicodedata import category
        trunk = trunkGlyph(glyph) or glyph
        if (any(glyph.unicode in r for r in lgcRange) or any(trunk and (trunk.unicode in r) for r in lgcRange)) and glyph.glyphname not in excludeComposed:
            if ((not (len(glyph.references) == 1 and glyph.references[0][1] == (1, 0, 0, 1, 0, 0)))) or (trunk is not glyph):
                decomp = decomposition(trunk)
                cat = category(chr(trunk.unicode))
                if cat in ['Lu', 'Ll'] and not decomp:
                    positions.setdefault(glyph.glyphname, [[], []])
                    if (not positions[glyph.glyphname][0]) and all(g[0] != glyph.glyphname for g in dotlessforms):
                        if (glyph.yBoundsAtX(306) or (0, 0))[1] >= 766:
                            positions[glyph.glyphname][0].append((0, 193))
                        elif glyph.boundingBox()[3] >= 700:
                            positions[glyph.glyphname][0].append((0, 151))
                        elif glyph.boundingBox()[3] >= 600:
                            positions[glyph.glyphname][0].append((0, 110))
                        else:
                            positions[glyph.glyphname][0].append((0, 0))
                    if (not positions[glyph.glyphname][1]):
                        if glyph.boundingBox()[1] <= -100:
                            positions[glyph.glyphname][1].append((0, -195))
                        else:
                            positions[glyph.glyphname][1].append((0, 0))
    while True:  # alias
        added = False
        for glyph in font.glyphs():
            if glyph.foreground.isEmpty() and len(glyph.references) == 1 and glyph.glyphname not in positions and glyph.references[0][0] in positions and glyph.references[0][1] == (1, 0, 0, 1, 0, 0) and any((glyph.unicode in r) for r in lgcRange):
                positions[glyph.glyphname] = positions[glyph.references[0][0]]
                added = True
        if not added:
            break
    while True:  # pre-composed
        added = False
        for glyph, composedGlyphs in composed.items():
            if glyph in positions and glyph not in excludeBase and any((trunk.unicode in r) for r in (lgcRange + [range(-1, 0)])):
                for composedGlyph, _ in composedGlyphs:
                    if composedGlyph not in positions and composedGlyph not in excludeComposed:
                        above = bool(font[composedGlyph].boundingBox()[3] > font[glyph].boundingBox()[3])
                        below = bool(font[composedGlyph].boundingBox()[1] < font[glyph].boundingBox()[1])
                        positions[composedGlyph] = [[] if above else positions[glyph][0], [] if below else positions[glyph][1]]
                        added = True
        if not added:
            break
    for dotted, dotless, base in dotlessforms:
        if dotless.endswith('.dotless'):
            assert base == 'i' or base == 'j'
            positions.setdefault(dotless, [[], []])
            if not positions[dotless][0]:
                positions[dotless][0] = positions['dotless' + base][0]
            if not positions[dotless][1]:
                positions[dotless][1] = positions[dotted][1]
    for glyph in (g.glyphname.removesuffix('.nav') for g in font.glyphs() if g.glyphname.endswith('.nav')):
        positions[glyph + '.nav'] = positions[glyph]
    for glyph, pos in positions.items():  # add anchors
        abovePos, belowPos = [((sum([p[0] for p in q]) / len(q), sum([p[1] for p in q]) / len(q)) if len(q) else None) for q in pos]
        if abovePos:
            x, y = anchorCoord(font, 306, 554)
            xx, yy = abovePos
            font[glyph].addAnchorPoint('LGC-accent-above', 'base', x + xx, y + yy)
        if belowPos:
            x, y = anchorCoord(font, 306, 0)
            xx, yy = belowPos
            font[glyph].addAnchorPoint('LGC-accent-below', 'base', x + xx, y + yy)
 
diacriticdata: list[tuple[str, Optional[str], int, str, int]] = [
    ('gravemodifier', 'grave.cap', 0x300, 'gravecomb', 0),
    ('acute', 'acute.cap', 0x301, 'acutecomb', 0),
    ('acute.pinyin', 'acute.cap.pinyin', -1, 'acutecomb.pinyin', 0),
    ('circumflex', 'circumflex.cap', 0x302, 'circumflexcomb', 0),
    ('tilde', None, 0x303, 'tildecomb', 0),
    ('macronmodifier', None, 0x304, 'macroncomb', 0),
    ('breve', None, 0x306, 'brevecomb', 0),
    ('dotaccent', None, 0x307, 'dotaccentcmb', 0),
    ('dieresis', None, 0x308, 'dieresiscmb', 0),
    ('hookabove', 'hookabove.cap', 0x309, 'hookabovecomb', 0),
    ('ring', None, 0x30a, 'ringcmb', 0),
    ('hungarumlaut', 'hungarumlaut.cap', 0x30b, 'hungarumlautcmb', 0),
    ('caron', 'caron.cap', 0x30c, 'caroncomb', 0),
    ('verticallinemod', 'verticallinemod.cap', 0x30d, 'verticallineabovecmb', 0),
    ('dblgrave', 'dblgrave.cap', 0x30f, 'dblgravecmb', 0),
    ('candrabindumod', None, 0x310, 'candrabinducmb', 0),
    ('invertedbreve', None, 0x311, 'breveinvertedcmb', 0),
    ('commaturnedabove', None, 0x312, 'commaturnedabovecmb', 0),
    ('commaabove', None, 0x313, 'commaabovecmb', 0),
    ('psili', None, -1, 'commaabovecmb.grek', 0),
    ('commareversedabove', None, 0x314, 'commareversedabovecmb', 0),
    ('dasia', None, -1, 'commareversedabovecmb.grek', 0),
    ('commaaboveright', None, 0x315, 'commaaboverightcmb', 0),
    ('gravesub', None, 0x316, 'gravesubnosp', 0),
    ('acutesub', None, 0x317, 'acutesubnosp', 0),
    ('horn', None, 0x31b, 'horncmb', 0),
    ('dotsub', None, 0x323, 'dotbelowcomb', 0),
    ('dieresisbelow', None, 0x324, 'dieresisbelowcmb', 0),
    ('uni02F3', None, 0x325, 'ringbelowcmb', 0),
    ('commaaccent', None, 0x326, 'commasubnosp', 10),
    ('cedilla', None, 0x327, 'cedillacmb', -40),
    ('ogonek', None, 0x328, 'ogonekcmb', -160),
    ('verticallinelowmod', None, 0x329, 'verticallinebelowcmb', 0),
    ('uni02EC', None, 0x32c, 'caronbelowcmb', 0),
    ('uniA788', None, 0x32d, 'circumflexbelowcmb', 0),
    ('brevebelow', None, 0x32e, 'brevebelowcmb', 0),
    ('breveinvertedbelow', None, 0x32f, 'breveinvertedbelowcmb', 0),
    ('uni02F7', None, 0x330, 'tildebelowcmb', 0),
    ('macronsub', None, 0x331, 'macronbelowcmb', 0),
    ('strokeshortoverlay', None, 0x335, 'strokeshortoverlaycmb', 0),
    ('invertedbreve', None, 0x342, 'perispomenigreekcmb', 0),
    ('tilde', None, -1, 'perispomenigreekcmb.alt', 0),
    ('uni02BF', None, 0x351, 'uni0351', 0),
    ('uni02BE', None, 0x357, 'uni0357', 0),
    ('hokkiendot', None, 0x358, 'uni0358', 0),
    ('doublemacronbelow', None, 0x35f, 'uni035F', 0),
]

def addLgcAnchorClasses(font: fontforge.font):
    allLGC = dict((scr, lng) for scr, lng in getLangDict(font).items() if scr in ['latn', 'grek', 'cyrl'])
    font.addLookup('Accent above', 'gpos_mark2base', None, (('mark', langDictToLangTuple(allLGC)),))
    font.addLookupSubtable('Accent above', 'Accent above-1')
    font.addAnchorClass('Accent above-1', 'LGC-accent-above')
    font.addLookup('Accent below', 'gpos_mark2base', None, (('mark', langDictToLangTuple(allLGC)),))
    font.addLookupSubtable('Accent below', 'Accent below-1')
    font.addAnchorClass('Accent below-1', 'LGC-accent-below')
    font.addLookup('Overlay', 'gpos_mark2base', None, (('mark', langDictToLangTuple(allLGC)),))
    font.addLookupSubtable('Overlay', 'Overlay-1')
    font.addAnchorClass('Overlay-1', 'LGC-overlay')

def lgcMarkAnchors(font: fontforge.font):
    def yTranslate(font: fontforge.font, sourcename: str) -> int:
        bbox = font[sourcename].boundingBox()
        if bbox[1] >= 700:
            return -123
        elif 10 < bbox[3] < 100:
            return -55
        else:
            return 0

    def addChar(font: fontforge.font, sourcename: str, targetuni: int, targetname: str, xoffset:int):
        font.createChar(targetuni, targetname)
        font[targetname].width = 0
        font[targetname].addReference(sourcename, translate(*anchorCoord(font, xoffset - 306, yTranslate(font, sourcename))))
        font[targetname].glyphclass = 'mark'
        left, _, _, top = font[sourcename].boundingBox()
        if left > 400:
            return
        elif top < 100:
            anchor = 'LGC-accent-below'
            y = 0
        elif top < 500:
            anchor = 'LGC-overlay'
            y = 294
        else:
            anchor = 'LGC-accent-above'
            y = 554
        font[targetname].addAnchorPoint(anchor, 'mark', *anchorCoord(font, 0, y))

    font.addLookup(
        'Combining Greek breathing marks',
        'gsub_single',
        None,
        (('locl', (('grek', ('dflt',)),)),),
        font.gsub_lookups[font.gsub_lookups.index('Old style numerals') - 1],
    )
    font.addLookupSubtable('Combining Greek breathing marks', 'Combining Greek breathing marks-1')
    for sourcename, capsourcename, targetuni, targetname, xoffset in diacriticdata:
        addChar(font, sourcename, targetuni, targetname, xoffset)
        if capsourcename:
            addChar(font, capsourcename, -1, targetname + '.cap', xoffset)
        if targetname.endswith('.pinyin'):
            font[targetname.removesuffix('.pinyin')].addPosSub('Pinyin variant forms-1', targetname)
        if targetname.endswith('.grek'):
            font[targetname.removesuffix('.grek')].addPosSub('Combining Greek breathing marks-1', targetname)
        if targetname == 'perispomenigreekcmb.alt':
            font[targetname.removesuffix('.alt')].addPosSub('Polytonic Greek alternative circumflex-1', targetname)

def precomposedForms(font: fontforge.font):
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
        'koronis': [('space', 'commaabovecmb')],
        'psili': [('space', 'commaabovecmb')],
        'dasia': [('space', 'commareversedabovecmb')],
        # Caron
        'dcaron': [('d', 'caroncomb')],
        'Lcaron': [('L', 'caroncomb')],
        'lcaron': [('l', 'caroncomb')],
        'tcaron': [('t', 'caroncomb')],
        # Comma accent
        'Gcommaaccent': [('G', 'cedillacmb')],
        'Kcommaaccent': [('K', 'cedillacmb')],
        'Lcommaaccent': [('L', 'cedillacmb')],
        'Ncommaaccent': [('N', 'cedillacmb')],
        'Rcommaaccent': [('R', 'cedillacmb')],
        'gcommaaccent': [('g', 'cedillacmb')],
        'kcommaaccent': [('k', 'cedillacmb')],
        'lcommaaccent': [('l', 'cedillacmb')],
        'ncommaaccent': [('n', 'cedillacmb')],
        'rcommaaccent': [('r', 'cedillacmb')],
        'Dcedilla': [('D', 'cedillacmb')],
        'dcedilla': [('d', 'cedillacmb')],
        # Vietnamese
        'Acircumflexacute': [('Acircumflex', 'acutecomb')],
        'Acircumflexgrave': [('Acircumflex', 'gravecomb')],
        'Acircumflexhookabove': [('Acircumflex', 'hookabovecomb')],
        'Ecircumflexacute': [('Ecircumflex', 'acutecomb')],
        'Ecircumflexgrave': [('Ecircumflex', 'gravecomb')],
        'Ecircumflexhookabove': [('Ecircumflex', 'hookabovecomb')],
        'Ocircumflexacute': [('Ocircumflex', 'acutecomb')],
        'Ocircumflexgrave': [('Ocircumflex', 'gravecomb')],
        'Ocircumflexhookabove': [('Ocircumflex', 'hookabovecomb')],
        'acircumflexacute': [('acircumflex', 'acutecomb')],
        'acircumflexgrave': [('acircumflex', 'gravecomb')],
        'acircumflexhookabove': [('acircumflex', 'hookabovecomb')],
        'ecircumflexacute': [('ecircumflex', 'acutecomb')],
        'ecircumflexgrave': [('ecircumflex', 'gravecomb')],
        'ecircumflexhookabove': [('ecircumflex', 'hookabovecomb')],
        'ocircumflexacute': [('ocircumflex', 'acutecomb')],
        'ocircumflexgrave': [('ocircumflex', 'gravecomb')],
        'ocircumflexhookabove': [('ocircumflex', 'hookabovecomb')],
        'ydotbelow': [('y', 'dotbelowcomb')],
    }
    all_lang = font.getLookupInfo('Variants of zero')[2][0][1]
    font.addLookup('Precomposed forms', 'gsub_ligature', None, (('ccmp', all_lang),))
    font.addLookupSubtable('Precomposed forms', 'Precomposed forms-1')
    for glyph in font.glyphs():
        if (decomp := decomposition(glyph)) and all([font.findEncodingSlot(c) >= 0 for c in decomp]):
            if len(decomp) >= 2 and all((d in (c[2] for c in diacriticdata)) for d in decomp[1:]):
                components = tuple(font[font.findEncodingSlot(c)].glyphname for c in decomp)
                if glyph.glyphname not in proscribedDecomp or all([components != p for p in proscribedDecomp[glyph.glyphname]]):
                    glyph.addPosSub('Precomposed forms-1', components)
                    glyph.glyphclass = 'baseglyph'
    for glyph in customDecomp:
        font[glyph].addPosSub('Precomposed forms-1', customDecomp[glyph])
        font[glyph].glyphclass = 'baseglyph'

def precomposedDiacritics(font: fontforge.font):
    all_lang = font.getLookupInfo('Variants of zero')[2][0][1]
    font.addLookup('Precomposed diacritics', 'gsub_ligature', None, (('ccmp', all_lang),))
    font.addLookupSubtable('Precomposed diacritics', 'Precomposed diacritics-1')
    composedDiacritics = [g for g in font.glyphs() if 'cmb_' in g.glyphname or 'comb_' in g.glyphname]
    for glyph in composedDiacritics:
        assert glyph.boundingBox()[3] > 100 and glyph.boundingBox()[0] < 400
        glyph.transform(translate(-306, 0))
        glyph.width = 0
        glyph.addAnchorPoint('LGC-accent-above', 'mark', *anchorCoord(font, 0, 554))
        glyph.glyphclass = 'mark'
        if '.' not in glyph.glyphname:
            glyph.addPosSub('Precomposed diacritics-1', tuple(glyph.glyphname.split('_')))
        elif glyph.glyphname.endswith('.pinyin'):
            font[glyph.glyphname.removesuffix('.pinyin')].addPosSub('Pinyin variant forms-1', glyph.glyphname)
    font.addLookup('Accent decomposition', 'gsub_multiple', None, ())
    font.addLookupSubtable('Accent decomposition', 'Accent decomposition-1')
    for glyph in [g for g in font.glyphs() if g.getPosSub('Precomposed forms-1')]:
        decomp = [
            d[2:] for d in glyph.getPosSub('Precomposed forms-1') if
            len(d) == 4 and
            d[2] != 'space' and
            (not font[d[2]].getPosSub('Precomposed forms-1')) and
            d[3] in [m.glyphname.split('_')[0] for m in composedDiacritics]
        ]
        if decomp:
            glyph.addPosSub('Accent decomposition-1', decomp[0])
    font.addLookup('Decompose precomposed for recompose', 'gsub_contextchain', None, (('ccmp', all_lang),))
    for mark1, mark2, *_ in [g.glyphname.split('_') for g in composedDiacritics if '.' not in g.glyphname]:
        glyphs = [
            g.glyphname for g in font.glyphs() if
            g.getPosSub('Accent decomposition-1') and
            g.getPosSub('Accent decomposition-1')[0][3] == mark1 and  # pyright: ignore[reportGeneralTypeIssues]
            not [
                h.getPosSub('Precomposed forms-1') for h in font.glyphs() if
                h.getPosSub('Precomposed forms-1') and
                [i for i in h.getPosSub('Precomposed forms-1') if i[2:4] == (g.glyphname, mark1)]
            ]
        ]
        font.addContextualSubtable(
            'Decompose precomposed for recompose',
            'Decompose {} before {}'.format(mark1, mark2),
            'class',
            '| 1 @<Accent decomposition> | 1',
            mclasses=((), tuple(glyphs)),  # pyright: ignore[reportArgumentType]
            fclasses=((), (mark2,)),  # pyright: ignore[reportArgumentType]
        )

def uppercaseForms(font: fontforge.font):
    mark = sum([[glyph.glyphname for a in glyph.anchorPoints if a[0] == 'LGC-accent-above' and a[1] == 'mark' and glyph.width == 0] for glyph in font.glyphs() if (glyph.glyphname + '.cap') in font], [])
    base = sum([[glyph.glyphname for a in glyph.anchorPoints if a[0] == 'LGC-accent-above' and a[1] != 'mark' and glyph.boundingBox()[3] >= 660] for glyph in font.glyphs()], [])
    font.addLookup('Forms for tall base glyphs', 'gsub_single', None, (), font.gsub_lookups[-1])
    font.addLookupSubtable('Forms for tall base glyphs', 'Forms for tall base glyphs-1')
    font.addLookup('Accents for tall base glyphs', 'gsub_contextchain', None, (('ccmp', langDictToLangTuple(getLangDict(font))),), font.gsub_lookups[-1])
    font.addContextualSubtable(
        'Accents for tall base glyphs',
        'Accents for tall base glyphs-1',
        'class',
        '1 | 1 @<Forms for tall base glyphs> |',
        bclasses=((), tuple(base)),  # pyright: ignore[reportArgumentType]
        mclasses=((), tuple(mark)),  # pyright: ignore[reportArgumentType]
    )
    for glyph in mark:
        font[glyph].addPosSub('Forms for tall base glyphs-1', glyph + '.cap')

def overlayDiacritics(font: fontforge.font):
    def overlayRequired(g: fontforge.glyph) -> bool:
        return (
            (g.width > 0) and
            ('bar' not in g.glyphname) and
            ('slash' not in g.glyphname) and
            ('stroke' not in g.glyphname) and
            (g.glyphname not in [
                'Eth',
                'Dcroat',
                'dcroat',
                'Dafrican',
                'uni023A',
                'uni023B',
                'uni023C',
                'uni023D',
                'uni023E',
                'uni0243',
                'uni0246',
                'uni0247',
                'uni0248',
                'uni0249',
                'uni024C',
                'uni024D',
                'uni024E',
                'uni024F',
                'lmiddletilde',
                'lbelt',
                'uni04FA',
                'uni04FB',
                'uni04FA.var',
                'uni04FB.var',
                'uni04FE',
                'uni04FF',
                'uni1D7D',
                'uni2C60',
                'uni2C61',
                'uni2C62',
                'uni2C63',
                'uni2C65',
                'uni2C66',
                'uniA740',
                'uniA741',
                'uniA748',
                'uniA749',
                'uniA7A8',
                'uniA7A9',
                'uniA7AD',
                'uniA7B8',
                'uniA7B9',
                'uniA7C7',
                'uniA7C8',
                'uniA7CC',
                'uniA7CD',
                'uniA7DC',
            ]) and
            bool([a[0] for a in g.anchorPoints if 'LGC-' in a[0]])
        )

    for glyph in (g for g in font.glyphs() if overlayRequired(g)):
        baseglyph = glyph
        while True:
            if (baselist := baseglyph.getPosSub('Precomposed forms-1')):
                baseglyph = font[baselist[0][2]]
            else:
                break
        if (
            baseglyph.boundingBox()[3] < 720 or
            any(a[3] < 600 for a in baseglyph.anchorPoints if 'LGC-accent-above' in a[0]) or
            (baseglyph.glyphname in (g[0] for g in dotlessforms))
        ):
            glyph.addAnchorPoint('LGC-overlay', 'base', 306, 315)
            # glyph.color = 0xff00ff
        else:
            glyph.addAnchorPoint('LGC-overlay', 'base', 306, 421)
            # glyph.color = 0xff80ff

def diacritics(font: fontforge.font):
    add_dottedcircle(font)
    addLgcAnchorClasses(font)
    lgcMarkAnchors(font)
    lgcBaseAnchors(font)
    add_dotlessforms(font)
    precomposedForms(font)
    precomposedDiacritics(font)
    uppercaseForms(font)
    overlayDiacritics(font)

def mark_dottedcircle(font: fontforge.font):
    font.addLookup('Append dotted circle', 'gsub_multiple', None, (('ccmp', langDictToLangTuple(getLangDict(font))),), font.gsub_lookups[-1])
    font.addLookupSubtable('Append dotted circle', 'Append dotted circle-1')
    font.addLookup('Remove dotted circle', 'gsub_ligature', None, (), 'Append dotted circle')
    font.addLookupSubtable('Remove dotted circle', 'Remove dotted circle-1')
    for glyph in [g for g in font.glyphs() if g.width == 0]:
        glyph.addPosSub('Append dotted circle-1', ('invalidbase', glyph.glyphname))
        glyph.addPosSub('Remove dotted circle-1', ('invalidbase', glyph.glyphname))
    anchors, _ = allAnchors(font)

    lookupOrder = 'Append dotted circle'
    for anchor in anchors:
        lookup = font.getLookupOfSubtable(font.getSubtableOfAnchor(anchor))
        lang = getLangDict(font, lookup)
        font.addLookup('Activate anchor ' + anchor, 'gsub_contextchain', font.getLookupInfo(lookup)[1], (('ccmp', langDictToLangTuple(getLangDict(font))),), lookupOrder)
        mark = sum([[glyph.glyphname for a in glyph.anchorPoints if a[0] == anchor and a[1] == 'mark' and glyph.width == 0] for glyph in font.glyphs()], [])
        base = sum([[glyph.glyphname for a in glyph.anchorPoints if a[0] == anchor and a[1] != 'mark'] for glyph in font.glyphs()], [])
        additionalMark = []
        additionalBase = ['space', 'nonbreakingspace', 'dottedcircle']
        if 'arab' in lang:
            additionalBase.append('tatweelarabic')
        additionalBase = [g for g in additionalBase if g in font]
        lookupName = 'Activate anchor ' + anchor
        baseList = sorted(set(base + additionalBase))
        markList = sorted(set(mark + additionalMark))
        if 'above' in anchor:
            aboveBelowMark = sum([[glyph.glyphname for a in glyph.anchorPoints if a[0] == anchor.replace('above', 'below') and a[1] == 'mark' and glyph.width == 0] for glyph in font.glyphs()], [])
        elif 'below' in anchor:
            aboveBelowMark = sum([[glyph.glyphname for a in glyph.anchorPoints if a[0] == anchor.replace('below', 'above') and a[1] == 'mark' and glyph.width == 0] for glyph in font.glyphs()], [])
        else:
            aboveBelowMark = []
        overlayMark = sum([[glyph.glyphname for a in glyph.anchorPoints if a[0] == 'LGC-overlay' and a[1] == 'mark' and glyph.width == 0] for glyph in font.glyphs()], [])
        font.addContextualSubtable(
            lookupName,
            lookupName + '-1',
            'class',
            '1 | 1 @<Remove dotted circle> 2 |',
            bclasses=((), tuple(baseList)),  # pyright: ignore[reportArgumentType]
            mclasses=((), 'invalidbase', tuple(markList)),  # pyright: ignore[reportArgumentType]
        )
        if aboveBelowMark:
            marks = [
                tuple(sorted(set(aboveBelowMark))),
                'invalidbase',
                tuple(sorted(set(overlayMark))),
            ]
            backtracks = [
                [0],
                [1, 0],
            ]
            for i, v in enumerate(backtracks, start=2):
                font.addContextualSubtable(
                    lookupName,
                    lookupName + '-' + str(i),
                    'class',
                    '1 ' + (' '.join(str(gc + 2) for gc in v)) + ' | 1 @<Remove dotted circle> 2 |',
                    afterSubtable=lookupName + '-' + str(i - 1),
                    bclasses=((), tuple(baseList)) + tuple(marks),  # pyright: ignore[reportArgumentType]
                    mclasses=((), 'invalidbase', tuple(markList)),  # pyright: ignore[reportArgumentType]
                )
        lookupOrder = lookupName

        if font.getLookupInfo(lookup)[0] == 'gpos_mark2base':
            markCoordinates = sum([[(a[2] + (306 if (lambda bb: (bb[0] * bb[2]) < 0)(font[g].boundingBox()) else 0), a[3]) for a in font[g].anchorPoints if a[0] == anchor] for g in mark], [])
            averagex = sum([p[0] for p in markCoordinates], 0.0) / len(markCoordinates)
            averagey = sum([p[1] for p in markCoordinates], 0.0) / len(markCoordinates)
            for g in ['dottedcircle', 'invalidbase']:
                font[g].addAnchorPoint(anchor, 'base', averagex, averagey)
                font[g].round()

def fixAllLang(font: fontforge.font, oldAllLang: LangDict, newAllLang: LangDict):
    for lookup in (font.gsub_lookups + font.gpos_lookups):
        newTags = []
        _, _, tags = font.getLookupInfo(lookup)
        for tag, lang in tags:
            langDict = langTupleToLangDict(lang)
            newLangDict = deepcopy(langDict)
            if tag != 'locl':
                for scr, lng in langDict.items():
                    if scr in oldAllLang and scr in newAllLang and lng == oldAllLang[scr]:
                        print([lookup, tag, scr])
                        newLangDict[scr] = deepcopy(newAllLang[scr])
            newTags.append((tag, langDictToLangTuple(newLangDict)))
        font.lookupSetFeatureList(lookup, tuple(newTags))

def addLdotL(font: fontforge.font):
    lastLoclLookup = font.gsub_lookups[font.gsub_lookups.index('Old style numerals') - 1]
    font.addLookup('Catalan punt volat precomposed', 'gsub_single', None, (), lastLoclLookup)
    font.addLookupSubtable('Catalan punt volat precomposed', 'Catalan punt volat precomposed-1')
    font.addLookup('Catalan punt volat ligature', 'gsub_ligature', None, (), lastLoclLookup)
    font.addLookupSubtable('Catalan punt volat ligature', 'Catalan punt volat ligature-1')
    dot_bb = font['periodcentered'].boundingBox()
    for ligature in ['L_periodcentered.cat', 'l_periodcentered.cat']:
        base = ligature[0]
        font.createChar(-1, ligature)
        font.selection.select(base)
        font.copyReference()
        font.selection.select(ligature)
        font.paste()
        font[ligature].useRefsMetrics(base)
        stem = font[ligature].xBoundsAtY(dot_bb[1], dot_bb[3])
        assert stem is not None
        stemX = (stem[0] + stem[1]) / 2
        dotX = (dot_bb[0] + dot_bb[2]) / 2
        targetX = stemX + font[ligature].width / 2
        font[ligature].addReference('periodcentered', translate(targetX - dotX, 0))
        font[ligature].addPosSub('Catalan punt volat ligature-1', (base, 'periodcentered'))
        font[ligature].lcarets = (306,)
    for ligature in ['Ldot.cat', 'ldot.cat']:
        font.createChar(-1, ligature)
        font.selection.select(ligature[0] + '_periodcentered.cat')
        font.copy()
        font.selection.select(ligature)
        font.paste()
        font[ligature.removesuffix('.cat')].addPosSub('Catalan punt volat precomposed-1', ligature)
    font.addLookup('Catalan L-L', 'gsub_contextchain', None, (('locl', (('latn', ('CAT ',)),)),), lastLoclLookup)
    for ligprec in [('precomposed', 'dot', ''), ('ligature', '', ' periodcentered')]:
        for ell in ['l', 'L']:
            font.addContextualSubtable(
                'Catalan L-L',
                'Catalan {0:}-{0:} {1:}'.format(ell, ligprec[0]),
                'glyph',
                '| {0:}{2:} @<Catalan punt volat {1:}>{3:} | {0:}'.format(ell, *ligprec),
            )

font = fontforge.open(argv[2])
font2 = fontforge.open(argv[3])
font.encoding = 'Original'
font2.encoding = 'Original'
assert font.copyright
font.fontname = font.fontname.replace('LGC', 'EX')
font.familyname = font.familyname.replace('LGC', 'EX')
font.fullname = font.fullname.replace('LGC', 'EX')
font.copyright += '\n\nArabic glyphs are derived from public domain part of DejaVu Sans Mono.'
font.os2_winascent = 1255
font.os2_windescent = 631
if font.italicangle != 0:
    font2.selection.all()
    font2.transform(skew(radians(-font.italicangle)), ('noWidth', 'round', 'simplePos'))
removeUnusedAnchorClass(font2)
diacritics(font)
oldAllLang = getLangDict(font)
addLdotL(font)
font.mergeFonts(argv[3])
font.save(argv[1])
font.close()  # workaround
font = fontforge.open(argv[1])
font.encoding = 'UnicodeFull'
newAllLang = getLangDict(font)
fixAllLang(font, oldAllLang, newAllLang)
mark_dottedcircle(font)
font.save(argv[1])
