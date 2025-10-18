#!/usr/bin/env fontforge
from sys import argv
font = fontforge.open(argv[2])
fonts = [fontforge.open(filename) for filename in argv[3:len(argv)]]
font.generateTtc(argv[1], fonts, layer=1)
