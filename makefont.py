#!/usr/bin/env python3

import fontforge, re
from sys import argv, stderr
from pathlib import Path
from tempfile import TemporaryDirectory
from subprocess import run
import fontforge_refsel

fontforge.hooks = {}  # disable hooks for this script

font = fontforge.open(argv[2])

try:
	font.style_set_names = font.style_set_names
except ValueError:  # 20251009 or earlier versions
	stderr.write('Names of character variations are not supported in this version.\n')
	stderr.write('Such entries have been removed.\n')
	font.style_set_names = tuple(n for n in font.style_set_names if n[1].startswith('ss'))

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

glyphnames = [n for n in font]
widthCount = len(set(glyph.width for glyph in font.glyphs()))

assert not argv[1].endswith(".ttc")

def genfont(font: fontforge.font, filename: str):
	try:
		font.generate(filename, flags=(  # pyright: ignore[reportArgumentType]
			'no-mac-names',
			'opentype',
			'no-FFTM-table',
			'no-special-null-cr',
		))
	except ValueError:
		stderr.write("This version of Fontforge does not support 'no-special-null-cr' flag.\n")
		stderr.write("Dangling glyphs '.null' and 'nonmarkingreturn' will be present.\n")
		font.generate(filename, flags=('no-mac-names','opentype','no-FFTM-table'))

if argv[1].endswith(".sfd"):
	font.save(argv[1])
elif argv[1].endswith(".ufo") or widthCount == 1:
	genfont(font, argv[1])
else:
	with TemporaryDirectory() as tmpdir:
		tmpFont = Path(tmpdir, 'tmp.' + argv[1].split('.')[-1])
		ttxFile = Path(tmpdir, 'tmp.ttx')
		genfont(font, str(tmpFont))
		run(['ttx', '-o', str(ttxFile), '-t', 'post', str(tmpFont)], check=True)
		with open(ttxFile) as ttx:
			ttxData = ttx.read()
		ttxData = re.sub(r'(?<=<isFixedPitch value=")0(?=")', r"1", ttxData)
		with open(ttxFile, "w") as ttx:
			ttx.write(ttxData)
		run(['ttx', '-o', argv[1], '-m', str(tmpFont), str(ttxFile)], check=True)

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

	# Workaround for openTypeOS2Selection
	if "<key>openTypeOS2Selection</key>" in fontInfo:
		fontInfo = re.sub(r"(?<=<key>openTypeOS2Selection</key>)(\s*)<array>.*?</array>", (
			r"\1<array>" "\n"
			"    <array>\n"
			"      <integer>7</integer>\n"
			"      <integer>8</integer>\n"
			"    </array>\n"
		), fontInfo)
	else:
		fontInfo = re.sub(r"\n(?=\s*</dict>\s*</plist>)", (
			"\n"
			"    <key>openTypeOS2Selection</key>\n"
			"    <array>\n"
			"      <integer>7</integer>\n"
			"      <integer>8</integer>\n"
			"    </array>\n"
		), fontInfo)

	# Add `aalt` feature
	if gsubtags:
		featureInstructions = ""
		for feature in gsubtags:
			featureInstructions += "  feature {0};\n".format(feature)
		fontFeature = re.sub(r"\bfeature\b", "feature aalt {{\n{0}}} aalt;\n\nfeature".format(featureInstructions), fontFeature, count=1)

	# Check nonexistent glyphs
	nonexistentGlyphs = set(m[0] for m in re.finditer(r'\\[^\W\d][\w\.]*\b', re.sub(r'".*?"', '', fontFeature))) - set('\\' + g for g in glyphnames)
	for glyph in sorted(nonexistentGlyphs):
		fontFeature = re.sub(glyph.replace("\\", "\\\\") + r'\b(?!\.)', '', fontFeature)

	# Write
	with open(Path(argv[1], "fontinfo.plist"), "w") as font:
		font.write(fontInfo)
	with open(Path(argv[1], "features.fea"), "w") as font:
		font.write(fontFeature)
