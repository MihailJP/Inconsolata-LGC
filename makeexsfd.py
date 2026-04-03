#!/usr/bin/env fontforge

import fontforge
from psMat import skew, translate, scale
from math import radians
from sys import argv
from typing import Union, Iterable
from copy import deepcopy

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
            markCoordinates = sum([[a[2:4] for a in font[g].anchorPoints if a[0] == anchor] for g in mark], [])
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
font.os2_windescent = 295
if font.italicangle != 0:
    font2.selection.all()
    font2.transform(skew(radians(-font.italicangle)), ('noWidth', 'round', 'simplePos'))
removeUnusedAnchorClass(font2)
add_dottedcircle(font)
add_dottedcircle(font2)
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
