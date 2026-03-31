#!/usr/bin/env fontforge

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
    return langTupleToLangDict(scripts)

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

dotlessforms: list[tuple[str, str]] = [
    ('i', 'dotlessi'),
    ('j', 'dotlessj'),
    ('icyril', 'dotlessi'),
    ('je', 'dotlessj'),
]

def add_dotlessforms(font: fontforge.font):
    font.addLookup('Dotless forms', 'gsub_ligature', None, ())
    font.addLookupSubtable('Dotless forms', 'Dotless forms-1')
    for dotted, dotless in dotlessforms:
        font[dotted].addPosSub('Dotless forms-1', dotless)
        font[dotted].glyphclass = 'baseglyph'

def anchorCoord(font: fontforge.font, x: float, y: float) -> tuple[float, float]:
    return (x - y * tan(radians(font.italicangle)), y)

lgcRange = [
    range(0x0041, 0x005b),
    range(0x0061, 0x007b),
    range(0x00c0, 0x0530),
    range(0x1c80, 0x1c90),
    range(0x1e00, 0x1f00),
]

def lgcBaseAnchors(font: fontforge.font):
    def trunkGlyph(glyph: fontforge.glyph) -> Optional[fontforge.glyph]:
        trunkname = re.sub(r'\.(serif|bg|mkd|ewe|var\d?|pinyin|alt)+$', '', glyph.glyphname)
        if trunkname == 'fscript':
            trunkname = 'florin'
        if trunkname not in glyph.font or trunkname == glyph.glyphname:
            trunkname = None
        if trunkname:
            return font[trunkname]
        else:
            return None
    type ComposedDict = dict[str, list[tuple[str, list[str]]]]
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
    ]
    excludeComposed = [
        'gcommaaccent', 'ydotbelow',
        'dcaron', 'Lcaron', 'lcaron', 'tcaron',
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
                        if glyph.boundingBox()[3] >= 700:
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
 
diacriticdata: list[tuple[str, Optional[str], int, str]] = [
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

def addLgcAnchorClasses(font: fontforge.font):
    allLGC = dict((scr, lng) for scr, lng in getLangDict(font).items() if scr in ['latn', 'grec', 'cyrl'])
    font.addLookup('Accent above', 'gpos_mark2base', None, (('mark', langDictToLangTuple(allLGC)),))
    font.addLookupSubtable('Accent above', 'Accent above-1')
    font.addAnchorClass('Accent above-1', 'LGC-accent-above')
    font.addLookup('Accent below', 'gpos_mark2base', None, (('mark', langDictToLangTuple(allLGC)),))
    font.addLookupSubtable('Accent below', 'Accent below-1')
    font.addAnchorClass('Accent below-1', 'LGC-accent-below')

def lgcMarkAnchors(font: fontforge.font):
    def addChar(font: fontforge.font, sourcename: str, targetuni: int, targetname: str):
        font.createChar(targetuni, targetname)
        font[targetname].width = 0
        font[targetname].addReference(sourcename, translate(*anchorCoord(font, -613, -123 if font[sourcename].boundingBox()[1] >= 700 else 0)))
        font[targetname].glyphclass = 'mark'
        _, _, _, top = font[sourcename].boundingBox()
        if top < 100:
            anchor = 'LGC-accent-below'
            y = 0
        else:
            anchor = 'LGC-accent-above'
            y = 554
        font[targetname].addAnchorPoint(anchor, 'mark', *anchorCoord(font, -307, y))

    for sourcename, capsourcename, targetuni, targetname in diacriticdata:
        addChar(font, sourcename, targetuni, targetname)
        if capsourcename:
            addChar(font, capsourcename, -1, targetname + '.cap')

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
        # Comma accent
        'Gcommaaccent': ('G', 'commasubnosp'),
        'Kcommaaccent': ('K', 'commasubnosp'),
        'Lcommaaccent': ('L', 'commasubnosp'),
        'Ncommaaccent': ('N', 'commasubnosp'),
        'Rcommaaccent': ('R', 'commasubnosp'),
        'kcommaaccent': ('k', 'commasubnosp'),
        'lcommaaccent': ('l', 'commasubnosp'),
        'ncommaaccent': ('n', 'commasubnosp'),
        'rcommaaccent': ('r', 'commasubnosp'),
    }
    proscribedDecomp = {
        # Duplicate
        'tonos': [('space', 'acutecomb')],
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

def uppercaseForms(font: fontforge.font):
    mark = sum([[glyph.glyphname for a in glyph.anchorPoints if a[0] == 'LGC-accent-above' and a[1] == 'mark' and glyph.width == 0] for glyph in font.glyphs() if (glyph.glyphname + '.cap') in font], [])
    base = sum([[glyph.glyphname for a in glyph.anchorPoints if a[0] == 'LGC-accent-above' and a[1] != 'mark' and glyph.boundingBox()[3] >= 660] for glyph in font.glyphs()], [])
    font.addLookup('Forms for tall base glyphs', 'gsub_single', None, (), font.gsub_lookups[-1])
    font.addLookupSubtable('Forms for tall base glyphs', 'Forms for tall base glyphs-1')
    font.addLookup('Accents for tall base glyphs', 'gsub_contextchain', None, (('calt', langDictToLangTuple(getLangDict(font))),), font.gsub_lookups[-1])
    font.addContextualSubtable(
        'Accents for tall base glyphs',
        'Accents for tall base glyphs-1',
        'class',
        '1 | 1 @<Forms for tall base glyphs> |',
        bclasses=((), tuple(base)),
        mclasses=((), tuple(mark)),
    )
    for glyph in mark:
        font[glyph].addPosSub('Forms for tall base glyphs-1', glyph + '.cap')

def diacritics(font: fontforge.font):
    add_dottedcircle(font)
    add_dotlessforms(font)
    addLgcAnchorClasses(font)
    lgcMarkAnchors(font)
    lgcBaseAnchors(font)
    precomposedForms(font)
    uppercaseForms(font)

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
        font.addContextualSubtable(
            lookupName,
            lookupName + '-1',
            'class',
            '1 | 1 @<Remove dotted circle> 2 |',
            bclasses=((), tuple(sorted(set(base + additionalBase)))),
            mclasses=((), 'invalidbase', tuple(sorted(set(mark + additionalMark)))),
        )
        lookupOrder = lookupName

        if font.getLookupInfo(lookup)[0] == 'gpos_mark2base':
            markCoordinates = sum([[(a[2] + (613 if (lambda bb: abs(bb[0]) > abs(bb[2]))(font[g].boundingBox()) else 0), a[3]) for a in font[g].anchorPoints if a[0] == anchor] for g in mark], [])
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
oldAllLang = getLangDict(font)
font.mergeFonts(argv[3])
font.save(argv[1])
font.close()  # workaround
font = fontforge.open(argv[1])
font.encoding = 'UnicodeFull'
newAllLang = getLangDict(font)
fixAllLang(font, oldAllLang, newAllLang)
mark_dottedcircle(font)
font.save(argv[1])
