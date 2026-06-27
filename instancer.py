#!/usr/bin/env python3

from sys import argv
from fontTools.ttLib.ttFont import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

font = TTFont(argv[2])
if '-Light' in argv[1]:
    static = instantiateVariableFont(font, {'wght': 300}, static=True)
    bold = False
    subfamilyName = ribbiFamily = 'Light'
elif '-Medium' in argv[1]:
    static = instantiateVariableFont(font, {'wght': 500}, static=True)
    bold = False
    subfamilyName = ribbiFamily = 'Medium'
elif '-DemiBold' in argv[1]:
    static = instantiateVariableFont(font, {'wght': 600}, static=True)
    bold = True
    ribbiFamily = 'Light'
    subfamilyName = 'DemiBold'
elif '-ExtraBold' in argv[1]:
    static = instantiateVariableFont(font, {'wght': 800}, static=True)
    bold = True
    ribbiFamily = 'Medium'
    subfamilyName = 'ExtraBold'
else:
    raise ValueError('unknown weight: {}'.format(argv[1]))
italic = ('Italic' in argv[1])

if not isinstance(static, TTFont):
    raise TypeError('instantiateVariableFont did not return TTFont')

ribbiName = ('Bold Italic' if italic else 'Bold') if bold else ('Italic' if italic else 'Regular')
familyName = str(static['name'].getName(1, 3, 1))
if italic:
    subfamilyName = subfamilyName + ' Italic'

static['name'].setName(familyName, 16, 3, 1, 0x409)
static['name'].setName(subfamilyName, 17, 3, 1, 0x409)
static['name'].setName(familyName + ' ' + subfamilyName, 4, 3, 1, 0x409)
static['name'].setName((familyName + '-' + subfamilyName).replace(' ', ''), 6, 3, 1, 0x409)
static['name'].setName(familyName + ' ' + ribbiFamily, 1, 3, 1, 0x409)
static['name'].setName(ribbiName, 2, 3, 1, 0x409)
static['OS/2'].fsSelection &= ~(0x7f)  # pyright: ignore[reportAttributeAccessIssue]
static['OS/2'].fsSelection |= (33 if italic else 32) if bold else (1 if italic else 64)  # pyright: ignore[reportAttributeAccessIssue]
static['OS/2'].fsSelection |= 128  # pyright: ignore[reportAttributeAccessIssue]
static['head'].macStyle = (3 if italic else 1) if bold else (2 if italic else 0)  # pyright: ignore[reportAttributeAccessIssue]

static.save(argv[1])
