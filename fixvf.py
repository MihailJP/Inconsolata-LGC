#!/usr/bin/env python3

from sys import argv
from fontTools.ttLib.ttFont import TTFont

srcfont = TTFont(argv[3])
font = TTFont(argv[2])
font['prep'] = srcfont['prep']
font['OS/2'].fsSelection |= 128  # pyright: ignore[reportAttributeAccessIssue]
font.save(argv[1])
