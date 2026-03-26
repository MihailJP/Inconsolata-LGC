Inconsolata-LGC-Minimum.sfd: Inconsolata-LGC.sfd Inconsolata-LGC-Bold.sfd
	./interpolate.py $@ $^ -1.6
Inconsolata-LGC-MinimumItalic.sfd: Inconsolata-LGC-Italic.sfd Inconsolata-LGC-BoldItalic.sfd
	./interpolate.py $@ $^ -1.6
Inconsolata-LGC-Maximum.sfd: Inconsolata-LGC.sfd Inconsolata-LGC-Bold.sfd
	./interpolate.py $@ $^ 2.5
Inconsolata-LGC-MaximumItalic.sfd: Inconsolata-LGC-Italic.sfd Inconsolata-LGC-BoldItalic.sfd
	./interpolate.py $@ $^ 2.5

Inconsolata-LGC.designspace: Inconsolata-LGC.ufo Inconsolata-LGC-Bold.ufo Inconsolata-LGC-Minimum.ufo Inconsolata-LGC-Maximum.ufo
	./make_designspace.py $@ $^
Inconsolata-LGC-Italic.designspace: Inconsolata-LGC-Italic.ufo Inconsolata-LGC-BoldItalic.ufo Inconsolata-LGC-MinimumItalic.ufo Inconsolata-LGC-MaximumItalic.ufo
	./make_designspace.py $@ $^

Inconsolata-LGC-Variable.raw.ttf: Inconsolata-LGC.designspace
	fontmake -m $< -o variable --output-path $@
Inconsolata-LGC-Variable-Italic.raw.ttf: Inconsolata-LGC-Italic.designspace
	fontmake -m $< -o variable --output-path $@
