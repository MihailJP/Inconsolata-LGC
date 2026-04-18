# Makefile for Inconsolata font

FONTS=Inconsolata-LGC.ttf \
      Inconsolata-LGC-Bold.ttf \
      Inconsolata-LGC-Italic.ttf \
      Inconsolata-LGC-BoldItalic.ttf
EXTRAPOLATES=Inconsolata-LGC-Minimum.sfd \
             Inconsolata-LGC-Maximum.sfd \
             Inconsolata-LGC-MinimumItalic.sfd \
             Inconsolata-LGC-MaximumItalic.sfd
EXFONTS=Inconsolata-EX.ttf \
        Inconsolata-EX-Bold.ttf \
        Inconsolata-EX-Italic.ttf \
        Inconsolata-EX-BoldItalic.ttf
EXEXTRAPOLATES=Inconsolata-EX-Minimum.sfd \
             Inconsolata-EX-Maximum.sfd \
             Inconsolata-EX-MinimumItalic.sfd \
             Inconsolata-EX-MaximumItalic.sfd
CSS=Inconsolata-LGC.css
EXCSS=Inconsolata-EX.css
HINTEDTTFONTS=${FONTS:.ttf=-Hinted.ttf}
OTFONTS=${FONTS:.ttf=.otf}
TTCFONTS=${FONTS:.ttf=.ttc}
WOFFFONTS=${FONTS:.ttf=.woff}
WOFF2FONTS=${FONTS:.ttf=.woff2}
HINTEDEXTTFONTS=${EXFONTS:.ttf=-Hinted.ttf}
EXOTFONTS=${EXFONTS:.ttf=.otf}
EXWOFFFONTS=${EXFONTS:.ttf=.woff}
EXWOFF2FONTS=${EXFONTS:.ttf=.woff2}
UFOS=${FONTS:.ttf=.ufo} ${EXTRAPOLATES:.sfd=.ufo}
EXUFOS=${EXFONTS:.ttf=.ufo} ${EXEXTRAPOLATES:.sfd=.ufo}
DESIGNSPACES=Inconsolata-LGC.designspace Inconsolata-LGC-Italic.designspace
EXDESIGNSPACES=Inconsolata-EX.designspace Inconsolata-EX-Italic.designspace
DOC_ASSET_DIR=doc
DOCUMENTS=README.md ChangeLog OFL.txt $(wildcard ${DOC_ASSET_DIR}/*.png)
PKGS=InconsolataLGC.tar.xz InconsolataLGC-Hinted.tar.xz InconsolataLGC-OT.tar.xz \
     InconsolataLGC-WOFF2.tar.xz InconsolataLGC-TTC.tar.xz InconsolataLGC-Variable.tar.xz \
	 InconsolataEX.tar.xz InconsolataEX-Hinted.tar.xz InconsolataEX-OT.tar.xz \
	 InconsolataEX-WOFF2.tar.xz InconsolataEX-Variable.tar.xz
VARFONTS=Inconsolata-LGC-Variable.ttf \
         Inconsolata-LGC-Variable-Italic.ttf
EXVARFONTS=Inconsolata-EX-Variable.ttf \
           Inconsolata-EX-Variable-Italic.ttf
TTFPKGCMD=rm -rf $*; mkdir $*; rsync -R ${FONTS} ${DOCUMENTS} $*
HINTEDTTFPKGCMD=rm -rf $*; mkdir $*; rsync -R ${HINTEDTTFONTS} ${DOCUMENTS} $*
OTFPKGCMD=rm -rf $*; mkdir $*; rsync -R ${OTFONTS} ${DOCUMENTS} $*
WOFF2PKGCMD=rm -rf $*; mkdir $*; rsync -R ${WOFF2FONTS} ${CSS} ${DOCUMENTS} $*
TTCPKGCMD=rm -rf $*; mkdir $*; rsync -R ${TTCFONTS} ${DOCUMENTS} $*
VTTFPKGCMD=rm -rf $*; mkdir $*; rsync -R ${VARFONTS} ${DOCUMENTS} $*

EXTTFPKGCMD=rm -rf $*; mkdir $*; rsync -R ${EXFONTS} ${DOCUMENTS} $*
HINTEDEXTTFPKGCMD=rm -rf $*; mkdir $*; rsync -R ${HINTEDEXTTFONTS} ${DOCUMENTS} $*
EXOTFPKGCMD=rm -rf $*; mkdir $*; rsync -R ${EXOTFONTS} ${DOCUMENTS} $*
EXWOFF2PKGCMD=rm -rf $*; mkdir $*; rsync -R ${EXWOFF2FONTS} ${EXCSS} ${DOCUMENTS} $*
EXVTTFPKGCMD=rm -rf $*; mkdir $*; rsync -R ${EXVARFONTS} ${DOCUMENTS} $*

.PHONY: all
all: ttf hintedttf otf ttc woff2 variable exttf hintedexttf exotf exwoff2 exvariable

.SUFFIXES: .sfd .ttf .otf .woff .woff2 .ufo

include Inconsolata-LGC.mk
include Inconsolata-LGC-Bold.mk
include Inconsolata-LGC-Italic.mk
include Inconsolata-LGC-BoldItalic.mk

Inconsolata-LGC-Bold.mk: Inconsolata-LGC.mk
	sed -E -e 's/\.(sfd|ttc)/-Bold.\1/g' $< > $@
Inconsolata-LGC-Italic.mk: Inconsolata-LGC.mk
	sed -E -e 's/\.(sfd|ttc)/-Italic.\1/g' $< > $@
Inconsolata-LGC-BoldItalic.mk: Inconsolata-LGC.mk
	sed -E -e 's/\.(sfd|ttc)/-BoldItalic.\1/g' $< > $@

.sfd.ttf .sfd.otf .sfd.woff .sfd.woff2 .sfd.ufo:
	for i in $?; do ./makefont.py $@ $$i; done

%-Hinted-raw.ttf: %.sfd
	./makefont.py $@ $<
%-Hinted.ttf: %-Hinted-raw.ttf Inconsolata-LGC.ttf
	ttfautohint -R Inconsolata-LGC.ttf $< $@

.PHONY: ttf otf ttc woff woff2 variable hintedttf
ttf: ${FONTS}
hintedttf: ${HINTEDTTFONTS}
otf: ${OTFONTS}
ttc: ${TTCFONTS}
woff: ${WOFFFONTS}
woff2: ${WOFF2FONTS}
variable: ${VARFONTS}

.PHONY: exttf exotf exwoff exwoff2 exvariable hintedexttf
exttf: ${EXFONTS}
hintedexttf: ${HINTEDEXTTFONTS}
exotf: ${EXOTFONTS}
exwoff: ${EXWOFFFONTS} ${EXCSS}
exwoff2: ${EXWOFF2FONTS} ${EXCSS}
exvariable: ${EXVARFONTS}

.SUFFIXES: .tar.xz .tar.gz .tar.bz2 .zip
.PHONY: dist
dist: ${PKGS}

Inconsolata-EX.sfd: Inconsolata-LGC.sfd Inconsolata-Arabic.sfd
	./makeexsfd.py $@ $^
Inconsolata-EX-Italic.sfd: Inconsolata-LGC-Italic.sfd Inconsolata-Arabic.sfd
	./makeexsfd.py $@ $^
Inconsolata-EX-Bold.sfd: Inconsolata-LGC-Bold.sfd Inconsolata-Arabic-Bold.sfd
	./makeexsfd.py $@ $^
Inconsolata-EX-BoldItalic.sfd: Inconsolata-LGC-BoldItalic.sfd Inconsolata-Arabic-Bold.sfd
	./makeexsfd.py $@ $^

.INTERMEDIATE: ${VARFONTS:.ttf=.raw.ttf} ${EXVARFONTS:.ttf=.raw.ttf}
include Inconsolata-LGC-Variable.mk
include Inconsolata-EX-Variable.mk

Inconsolata-EX-Variable.mk: Inconsolata-LGC-Variable.mk
	sed -E -e 's/-LGC/-EX/g' $< > $@

.INTERMEDIATE: prep.ttx
prep.ttx: Inconsolata-LGC.ttf
	ttx -o $@ -tprep $<

${VARFONTS} ${EXVARFONTS}: %.ttf: %.raw.ttf prep.ttx
	ttx -o $@ -m $^

Inconsolata-EX.css: Inconsolata-LGC.css
	sed 's/LGC/EX/' $< > $@

.PHONY: check
check: check-static check-hinted check-variable

CHECKCMD=if command -v fontspector; then \
	fontspector --configuration $^; \
	else \
	fontbakery check-universal --configuration $^; \
	fi
.PHONY: check-static
check-static: fontspector_static.toml ${FONTS}
	${CHECKCMD}
.PHONY: check-hinted
check-hinted: fontspector_static.toml ${HINTEDTTFONTS}
	${CHECKCMD}
.PHONY: check-variable
check-variable: fontspector_variable.toml ${VARFONTS}
	${CHECKCMD}

.PHONY: check-ex-static
check-ex-static: fontspector_static.toml ${EXFONTS}
	${CHECKCMD}
.PHONY: check-ex-hinted
check-ex-hinted: fontspector_static.toml ${HINTEDEXTTFONTS}
	${CHECKCMD}
.PHONY: check-ex-variable
check-ex-variable: fontspector_variable.toml ${EXVARFONTS}
	${CHECKCMD}

InconsolataLGC.tar.xz: ${FONTS} ${DOCUMENTS}
	${TTFPKGCMD}; tar cfvJ $@ $*
InconsolataLGC.tar.gz: ${FONTS} ${DOCUMENTS}
	${TTFPKGCMD}; tar cfvz $@ $*
InconsolataLGC.tar.bz2: ${FONTS} ${DOCUMENTS}
	${TTFPKGCMD}; tar cfvj $@ $*
InconsolataLGC.zip: ${FONTS} ${DOCUMENTS}
	${TTFPKGCMD}; zip -9r $@ $*

InconsolataLGC-Hinted.tar.xz: ${HINTEDTTFONTS} ${DOCUMENTS}
	${HINTEDTTFPKGCMD}; tar cfvJ $@ $*
InconsolataLGC-Hinted.tar.gz: ${HINTEDTTFONTS} ${DOCUMENTS}
	${HINTEDTTFPKGCMD}; tar cfvz $@ $*
InconsolataLGC-Hinted.tar.bz2: ${HINTEDTTFONTS} ${DOCUMENTS}
	${HINTEDTTFPKGCMD}; tar cfvj $@ $*
InconsolataLGC-Hinted.zip: ${HINTEDTTFONTS} ${DOCUMENTS}
	${HINTEDTTFPKGCMD}; zip -9r $@ $*

InconsolataLGC-OT.tar.xz: ${OTFONTS} ${DOCUMENTS}
	${OTFPKGCMD}; tar cfvJ $@ $*
InconsolataLGC-OT.tar.gz: ${OTFONTS} ${DOCUMENTS}
	${OTFPKGCMD}; tar cfvz $@ $*
InconsolataLGC-OT.tar.bz2: ${OTFONTS} ${DOCUMENTS}
	${OTFPKGCMD}; tar cfvj $@ $*
InconsolataLGC-OT.zip: ${OTFONTS} ${DOCUMENTS}
	${OTFPKGCMD}; zip -9r $@ $*

InconsolataLGC-WOFF2.tar.xz: ${WOFF2FONTS} ${CSS} ${DOCUMENTS}
	${WOFF2PKGCMD}; tar cfvJ $@ $*
InconsolataLGC-WOFF2.tar.gz: ${WOFF2FONTS} ${CSS} ${DOCUMENTS}
	${WOFF2PKGCMD}; tar cfvz $@ $*
InconsolataLGC-WOFF2.tar.bz2: ${WOFF2FONTS} ${CSS} ${DOCUMENTS}
	${WOFF2PKGCMD}; tar cfvj $@ $*
InconsolataLGC-WOFF2.zip: ${WOFF2FONTS} ${CSS} ${DOCUMENTS}
	${WOFF2PKGCMD}; zip -9r $@ $*

InconsolataLGC-TTC.tar.xz: ${TTCFONTS} ${DOCUMENTS}
	${TTCPKGCMD}; tar cfvJ $@ $*
InconsolataLGC-TTC.tar.gz: ${TTCFONTS} ${DOCUMENTS}
	${TTCPKGCMD}; tar cfvz $@ $*
InconsolataLGC-TTC.tar.bz2: ${TTCFONTS} ${DOCUMENTS}
	${TTCPKGCMD}; tar cfvj $@ $*
InconsolataLGC-TTC.zip: ${TTCFONTS} ${DOCUMENTS}
	${TTCPKGCMD}; zip -9r $@ $*

InconsolataLGC-Variable.tar.xz: ${VARFONTS} ${DOCUMENTS}
	${VTTFPKGCMD}; tar cfvJ $@ $*
InconsolataLGC-Variable.tar.gz: ${VARFONTS} ${DOCUMENTS}
	${VTTFPKGCMD}; tar cfvz $@ $*
InconsolataLGC-Variable.tar.bz2: ${VARFONTS} ${DOCUMENTS}
	${VTTFPKGCMD}; tar cfvj $@ $*
InconsolataLGC-Variable.zip: ${VARFONTS} ${DOCUMENTS}
	${VTTFPKGCMD}; zip -9r $@ $*

InconsolataEX.tar.xz: ${EXFONTS} ${DOCUMENTS}
	${EXTTFPKGCMD}; tar cfvJ $@ $*
InconsolataEX.tar.gz: ${EXFONTS} ${DOCUMENTS}
	${EXTTFPKGCMD}; tar cfvz $@ $*
InconsolataEX.tar.bz2: ${EXFONTS} ${DOCUMENTS}
	${EXTTFPKGCMD}; tar cfvj $@ $*
InconsolataEX.zip: ${EXFONTS} ${DOCUMENTS}
	${EXTTFPKGCMD}; zip -9r $@ $*

InconsolataEX-Hinted.tar.xz: ${HINTEDEXTTFONTS} ${DOCUMENTS}
	${HINTEDEXTTFPKGCMD}; tar cfvJ $@ $*
InconsolataEX-Hinted.tar.gz: ${HINTEDEXTTFONTS} ${DOCUMENTS}
	${HINTEDEXTTFPKGCMD}; tar cfvz $@ $*
InconsolataEX-Hinted.tar.bz2: ${HINTEDEXTTFONTS} ${DOCUMENTS}
	${HINTEDEXTTFPKGCMD}; tar cfvj $@ $*
InconsolataEX-Hinted.zip: ${HINTEDEXTTFONTS} ${DOCUMENTS}
	${HINTEDEXTTFPKGCMD}; zip -9r $@ $*

InconsolataEX-OT.tar.xz: ${EXOTFONTS} ${DOCUMENTS}
	${EXOTFPKGCMD}; tar cfvJ $@ $*
InconsolataEX-OT.tar.gz: ${EXOTFONTS} ${DOCUMENTS}
	${EXOTFPKGCMD}; tar cfvz $@ $*
InconsolataEX-OT.tar.bz2: ${EXOTFONTS} ${DOCUMENTS}
	${EXOTFPKGCMD}; tar cfvj $@ $*
InconsolataEX-OT.zip: ${EXOTFONTS} ${DOCUMENTS}
	${EXOTFPKGCMD}; zip -9r $@ $*

InconsolataEX-WOFF2.tar.xz: ${EXWOFF2FONTS} ${EXCSS} ${DOCUMENTS}
	${EXWOFF2PKGCMD}; tar cfvJ $@ $*
InconsolataEX-WOFF2.tar.gz: ${EXWOFF2FONTS} ${EXCSS} ${DOCUMENTS}
	${EXWOFF2PKGCMD}; tar cfvz $@ $*
InconsolataEX-WOFF2.tar.bz2: ${EXWOFF2FONTS} ${EXCSS} ${DOCUMENTS}
	${EXWOFF2PKGCMD}; tar cfvj $@ $*
InconsolataEX-WOFF2.zip: ${EXWOFF2FONTS} ${EXCSS} ${DOCUMENTS}
	${EXWOFF2PKGCMD}; zip -9r $@ $*

InconsolataEX-Variable.tar.xz: ${EXVARFONTS} ${DOCUMENTS}
	${EXVTTFPKGCMD}; tar cfvJ $@ $*
InconsolataEX-Variable.tar.gz: ${EXVARFONTS} ${DOCUMENTS}
	${EXVTTFPKGCMD}; tar cfvz $@ $*
InconsolataEX-Variable.tar.bz2: ${EXVARFONTS} ${DOCUMENTS}
	${EXVTTFPKGCMD}; tar cfvj $@ $*
InconsolataEX-Variable.zip: ${EXVARFONTS} ${DOCUMENTS}
	${EXVTTFPKGCMD}; zip -9r $@ $*

ChangeLog: .git # GIT
	./mkchglog.rb > $@ # GIT

.PHONY: clean
clean:
	-rm -f ${FONTS} ${HINTEDTTFONTS} ${OTFONTS} ${TTCFONTS} ${WOFFFONTS} ${WOFF2FONTS} ${VARFONTS} ChangeLog
	-rm -f ${VARFONTS:.ttf=.raw.ttf} ${TTCFONTS:.ttc=.raw.ttc}
	-rm -f ${EXFONTS:.ttf=.sfd} ${EXFONTS} ${HINTEDEXTTFONTS} ${EXOTFONTS} ${EXWOFFFONTS} ${EXWOFF2FONTS} ${EXVARFONTS} ${EXCSS}
	-rm -f ${FONTS:.ttf=-Intermediate.sfd}
	-rm -f ${FONTS:.ttf=-Romanian.sfd} ${FONTS:.ttf=-Polish.sfd} ${FONTS:.ttf=-Bulgarian.sfd} ${FONTS:.ttf=-Yugoslav.sfd}
	-rm -f ${FONTS:.ttf=-Livonian.sfd} ${FONTS:.ttf=-Sami.sfd} ${FONTS:.ttf=-Pinyin.sfd} ${FONTS:.ttf=-African.sfd}
	-rm -f ${FONTS:.ttf=-Chuvash.sfd}
	-rm -f Inconsolata-LGC-Bold.mk Inconsolata-LGC-Italic.mk Inconsolata-LGC-BoldItalic.mk
	-rm -f Inconsolata-EX-Variable.mk
	-rm -f prep.ttx
	-rm -rf ${UFOS} ${EXTRAPOLATES} ${DESIGNSPACES}
	-rm -rf ${EXUFOS} ${EXEXTRAPOLATES} ${EXDESIGNSPACES}
	-rm -rf ${PKGS} ${PKGS:.tar.xz=} ${PKGS:.tar.xz=.tar.bz2} \
	${PKGS:.tar.xz=.tar.gz} ${PKGS:.tar.xz=.zip}
