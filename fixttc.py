#!/usr/bin/env python3
from sys import argv
from fontTools.ttLib import TTCollection

with TTCollection(argv[2]) as ttc:
    for ttf in ttc.fonts:
        if 'FFTM' in ttf:
            del ttf['FFTM']
        if 'PfEd' in ttf:
            del ttf['PfEd']
    ttc.save(argv[1])
