#!/usr/bin/env python3

from sys import argv
import fontforge

def linear(a: float, b: float, p: float):
    try:
        from math import fma  # 3.13 or later
        return fma(b - a, p, a)
    except ImportError:
        return (b - a) * p + a

font1 = fontforge.open(argv[2])
interpolation = float(argv[4])
font = font1.interpolateFonts(interpolation, argv[3])
font.encoding = "UnicodeBmp"

attrs = [
    "fontname",
    "familyname",
    "fullname",
    "version",
    "copyright",
    "upos",
    "uwidth",
    "italicangle",
] + [a for a in dir(font) if a.startswith('os2_') or a.startswith('hhea_')]

for attr in attrs:
    setattr(font, attr, getattr(font1, attr))

font.importLookups(font1, font1.gsub_lookups)
for lookup in (  # workaround for multiple lookup tag
    lu for lu in font.gsub_lookups if
    lu in font1.gsub_lookups and font.getLookupInfo(lu) != font1.getLookupInfo(lu)
):
    font.lookupSetFeatureList(lookup, font1.getLookupInfo(lookup)[2])

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
                        anchor1 = [a for a in anchor1 if a[1] == 'ligature' and a[4] == anchor[4]]
                        anchor2 = [a for a in anchor2 if a[1] == 'ligature' and a[4] == anchor[4]]
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
