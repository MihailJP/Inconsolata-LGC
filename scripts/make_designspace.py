#!/usr/bin/env python3

import os, re
from sys import argv
from fontTools.designspaceLib import DesignSpaceDocument, AxisDescriptor, DiscreteAxisDescriptor, SourceDescriptor, InstanceDescriptor, AxisLabelDescriptor

root = os.getcwd()
doc = DesignSpaceDocument()

familyName = "Inconsolata LGC"
isItalic = bool(re.search('Italic', argv[1]))
italicValue = 1 if isItalic else 0

weightList = [
	(100, "Thin"),
	(200, "Extra Light"),
	(300, "Light"),
	(400, None),
	(500, "Medium"),
	(600, "DemiBold"),
	(700, "Bold"),
	(800, "Extra Bold"),
	(900, "Black"),
]

#------
# axes
#------

a1 = AxisDescriptor()
a1.maximum = 1000
a1.minimum = 0
a1.default = 400
a1.name = "Weight"
a1.tag = "wght"
a1.axisOrdering = 1
a1.axisLabels = []

for weight in weightList:
	l1 = AxisLabelDescriptor(
		name = "Regular" if weight[1] is None else weight[1],
		userValue = weight[0],
	)
	if weight[0] == 400:
		l1.elidable = isItalic
		l1.linkedUserValue = 700
	a1.axisLabels = a1.axisLabels + [l1]

a2 = DiscreteAxisDescriptor()
a2.values = [italicValue]
a2.default = italicValue
a2.name = "Italic"
a2.tag = "ital"
a2.axisOrdering = 2
if isItalic:
	a2.axisLabels = [
		AxisLabelDescriptor(name = "Italic", userValue = 1, elidable = False)
	]
else:
	a2.axisLabels = [
		AxisLabelDescriptor(name = "Roman", userValue = 0, elidable = True)
	]

doc.addAxis(a1)
doc.addAxis(a2)

#---------
# masters
#---------

sourceList = [
	("Regular", argv[2],  400),
	("Minimum", argv[4],    0),
	("Bold",    argv[3],  700),
	("Maximum", argv[5], 1000),
]

for source in sourceList:
	s0 = SourceDescriptor()
	s0.path = source[1]
	s0.name = familyName + " " + source[0]
	s0.familyName = familyName
	s0.styleName = source[0] + (" Italic" if isItalic else "")
	if s0.styleName == "Regular Italic":
		s0.styleName = "Italic"
	s0.location = dict(Weight=source[2], Italic=italicValue)
	if source[2] == a1.default:
		s0.copyLib = True
		s0.copyInfo = True
		s0.copyGroups = True
		s0.copyFeatures = True
	doc.addSource(s0)

#----------
# instances
#----------

for weight in weightList:
	i1 = InstanceDescriptor()
	styleNameList = [i for i in [weight[1], "Italic" if isItalic else None] if i is not None]
	i1.familyName = familyName
	i1.styleName = " ".join(styleNameList)
	if i1.styleName == "":
		i1.styleName = "Regular"
	i1.name = i1.familyName + " " + i1.styleName
	i1.postscriptFontName = (i1.familyName + "-" + i1.styleName).replace(" ", "")
	i1.styleMapFamilyName = i1.familyName
	if weight[0] == 400:
		i1.styleMapStyleName = "italic" if isItalic else "regular"
	elif weight[0] == 700:
		i1.styleMapStyleName = "bold italic" if isItalic else "bold"
	else:
		i1.styleMapStyleName = None
	i1.path = i1.postscriptFontName + ".ufo"
	i1.designLocation = dict(Weight=weight[0], Italic=italicValue)
	doc.addInstance(i1)


#--------
# saving
#--------

path = os.path.join(root, argv[1])
doc.write(path)
