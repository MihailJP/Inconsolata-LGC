#!/usr/bin/env fontforge

import fontforge, psMat, re
from sys import argv
from pathlib import Path

def decomposeNestedRefs(font):
	while True:
		nestedRefsFound = False
		for glyph in font.glyphs():
			decomposedRef = []
			for ref in glyph.references:
				(srcglyph, matrix, _) = ref
				if len(font[srcglyph].references) > 0:
					print("Glyph " + glyph.glyphname + " has a nested reference to " + srcglyph)
					for srcref in font[srcglyph].references:
						decomposedRef += [(srcref[0], psMat.compose(srcref[1], matrix), False)]
					nestedRefsFound = True
				else:
					decomposedRef += [ref]
			glyph.references = tuple(decomposedRef)
		if not nestedRefsFound:
			break

font = fontforge.open(argv[2])
decomposeNestedRefs(font)
if not argv[1].endswith(".ufo"):
	font.buildOrReplaceAALTFeatures()

if argv[1].endswith(".sfd"):
	font.save(argv[1])
else:
	font.generate(argv[1], flags=('no-mac-names','opentype'))

font.close()

if argv[1].endswith(".ufo"): # workaround
	# Read
	with open(Path(argv[1], "fontinfo.plist")) as font:
		fontInfo = font.read()

	# Workaround for postscriptIsFixedPitch
	if fontInfo.find("<key>postscriptIsFixedPitch</key>") >= 0:
		fontInfo = re.sub(r"(?<=<key>postscriptIsFixedPitch</key>)(\s*)<false\s*/>", r"\1<true/>", fontInfo)
	else:
		fontInfo = re.sub(r"\n(?=\s*</dict>\s*</plist>)", "\n    <key>postscriptIsFixedPitch</key>\n    <true />\n", fontInfo)

	# Workaround for styleMapFamilyName
	if fontInfo.find("<key>styleMapFamilyName</key>") >= 0:
		fontInfo = re.sub(r"(?<=<key>styleMapFamilyName</key>)(\s*<string>.*?)( Bold)?( Italic)?</string>", r"\1</string>", fontInfo)

	# Write
	with open(Path(argv[1], "fontinfo.plist"), "w") as font:
		font.write(fontInfo)
