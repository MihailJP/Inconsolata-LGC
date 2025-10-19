#!/usr/bin/env python3

from sys import argv
from fontTools import ufoLib
import re

class FontInfo:
    def __init__(self):
        for key in ufoLib.fontInfoAttributesVersion2:
            self.__dict__[key] = None

(_, ufoPath, sfdPath) = argv

with open(sfdPath, 'r') as file:
    sfd = file.read()
ufo = ufoLib.UFOReaderWriter(ufoPath)

# Workaround for fontinfo.plist

m = re.search(r"^Version:\s*(.*?)$", sfd, re.M)
versionStr = None
if m:
    versionStr = m.group(1)

fontInfo = FontInfo()
ufo.readInfo(fontInfo)
if versionStr and not fontInfo.openTypeNameVersion:
    fontInfo.openTypeNameVersion = "Version " + versionStr
fontInfo.postscriptIsFixedPitch = True
ufo.writeInfo(fontInfo)
