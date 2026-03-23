#!/usr/bin/env fontforge

from sys import argv
import fontforge
from math import fma

def linear(a: float, b: float, p: float):
    return fma(b - a, p, a)

font1 = fontforge.open(argv[2])
interpolation = float(argv[4])
font = font1.interpolateFonts(interpolation, argv[3])
font.encoding = "UnicodeBmp"

font.upos = font1.upos
font.uwidth = font1.uwidth
font.os2_winascent_add = font1.os2_winascent_add
font.os2_windescent_add = font1.os2_windescent_add
font.os2_winascent = font1.os2_winascent
font.os2_windescent = font1.os2_windescent
font.os2_typoascent_add = font1.os2_typoascent_add
font.os2_typodescent_add = font1.os2_typodescent_add
font.os2_typoascent = font1.os2_typoascent
font.os2_typodescent = font1.os2_typodescent
font.os2_typolinegap = font1.os2_typolinegap
font.hhea_ascent_add = font1.hhea_ascent_add
font.hhea_descent_add = font1.hhea_descent_add
font.hhea_ascent = font1.hhea_ascent
font.hhea_descent = font1.hhea_descent
font.hhea_linegap = font1.hhea_linegap
font.os2_family_class = font1.os2_family_class
font.os2_stylemap = font1.os2_stylemap
font.os2_panose = font1.os2_panose
font.os2_version = font1.os2_version
font.os2_strikeypos = font1.os2_strikeypos
font.os2_strikeysize = font1.os2_strikeysize
font.os2_subxoff = font1.os2_subxoff
font.os2_subxsize = font1.os2_subxsize
font.os2_subyoff = font1.os2_subyoff
font.os2_subysize = font1.os2_subysize
font.os2_supxoff = font1.os2_supxoff
font.os2_supxsize = font1.os2_supxsize
font.os2_supyoff = font1.os2_supyoff
font.os2_supysize = font1.os2_supysize

font.importLookups(font1, font1.gsub_lookups)

if font1.gpos_lookups:
    font2 = fontforge.open(argv[3])
    font.importLookups(font1, font1.gpos_lookups)
    for glyph in font.glyphs():
        newAnchors = []
        if glyph.glyphname in font1 and glyph.glyphname in font2:
            anchors1 = font1[glyph.glyphname].anchorPoints
            anchors2 = font2[glyph.glyphname].anchorPoints
            for anchor in glyph.anchorPoints:
                anchor1 = [a for a in anchors1 if a[0:2] == anchor[0:2]]
                anchor2 = [a for a in anchors2 if a[0:2] == anchor[0:2]]
                if anchor[1] in ['base', 'basemark', 'mark']:
                    if anchor1 and anchor2:
                        anchor1 = anchor1[0]
                        anchor2 = anchor2[0]
                        newAnchors.append((
                            anchor[0],
                            anchor[1],
                            linear(anchor1[2], anchor2[2], interpolation),
                            linear(anchor1[3], anchor2[3], interpolation),
                        ))
                elif anchor[1] == 'ligature':
                    if anchor1 and anchor2:
                        anchor1 = [a for a in anchor1 if a[4] == anchor[4]]
                        anchor2 = [a for a in anchor2 if a[4] == anchor[4]]
                        if anchor1 and anchor2:
                            anchor1 = anchor1[0]
                            anchor2 = anchor2[0]
                            newAnchors.append((
                                anchor[0],
                                anchor[1],
                                linear(anchor1[2], anchor2[2], interpolation),
                                linear(anchor1[3], anchor2[3], interpolation),
                                anchor[4],
                            ))
        glyph.anchorPoints = tuple(newAnchors)

font.save(argv[1])
