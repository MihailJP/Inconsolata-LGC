#!/usr/bin/env fontforge

import fontforge, re
from sys import argv
from pathlib import Path
import fontforge_refsel

fontforge.hooks = {}  # disable hooks for this script

font = fontforge.open(argv[2])
if 'Hinted' in argv[1]:
	fontforge_refsel.selectGlyphsWithDistortedRefs(font)
	font.unlinkReferences()
fontforge_refsel.decomposeNestedRefs(font, True)
gsubtags = sorted(set(font.getLookupInfo(lu)[2][0][0] for lu in font.gsub_lookups if font.getLookupInfo(lu)[2]))
if argv[1].endswith(".ufo"):
	for glyph in font.glyphs():
		glyph.unlinkRmOvrlpSave = False
else:
	font.buildOrReplaceAALTFeatures()

for glyph in sorted(fontforge_refsel.unusedGlyphs(font)):
	font.removeGlyph(glyph)

if argv[1].endswith(".otf"):
	font.em = 1000

if argv[1].endswith(".sfd"):
	font.save(argv[1])
else:
	font.generate(argv[1], flags=('no-mac-names','opentype','no-FFTM-table'))

font.close()

if argv[1].endswith(".ufo"): # workaround
	# Read
	with open(Path(argv[1], "fontinfo.plist")) as font:
		fontInfo = font.read()
	with open(Path(argv[1], "features.fea")) as font:
		fontFeature = font.read()

	# Workaround for postscriptIsFixedPitch
	if "<key>postscriptIsFixedPitch</key>" in fontInfo:
		fontInfo = re.sub(r"(?<=<key>postscriptIsFixedPitch</key>)(\s*)<false\s*/>", r"\1<true/>", fontInfo)
	else:
		fontInfo = re.sub(r"\n(?=\s*</dict>\s*</plist>)", "\n    <key>postscriptIsFixedPitch</key>\n    <true />\n", fontInfo)

	# Workaround for styleMapFamilyName
	if fontInfo.find("<key>styleMapFamilyName</key>") >= 0:
		fontInfo = re.sub(r"(?<=<key>styleMapFamilyName</key>)(\s*<string>.*?)( Bold)?( Italic)?</string>", r"\1</string>", fontInfo)

	# Add `aalt` feature
	if gsubtags:
		featureInstructions = ""
		for feature in gsubtags:
			featureInstructions += "  feature {0};\n".format(feature)
		fontFeature = re.sub(r"\bfeature\b", "feature aalt {{\n{0}}} aalt;\n\nfeature".format(featureInstructions), fontFeature, count=1)

	# Write
	with open(Path(argv[1], "fontinfo.plist"), "w") as font:
		font.write(fontInfo)
	with open(Path(argv[1], "features.fea"), "w") as font:
		font.write(fontFeature)
