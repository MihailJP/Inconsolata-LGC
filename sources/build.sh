#!/bin/sh

startdir="$PWD"
rm -rf ../build
for j in ../fonts/*; do
	for i in $j/*; do
		rm -rf $i
	done
done
mkdir ../build

for i in *.sfd; do
        fontforge -lang=py -script <<EOS || exit $?
import fontforge
font = fontforge.open("$i")
font.generate("../build/${i%sfd}ufo")
font.buildOrReplaceAALTFeatures()
font.generate("../fonts/ttf/${i%sfd}ttf")
font.generate("../fonts/otf/${i%sfd}otf")
font.generate("../fonts/webfonts/${i%sfd}woff2")
font.close()
EOS
done

../scripts/interpolate.py ../build/Inconsolata-LGC-Minimum.sfd Inconsolata-LGC.sfd Inconsolata-LGC-Bold.sfd -1.6 || exit $?
../scripts/interpolate.py ../build/Inconsolata-LGC-MinimumItalic.sfd Inconsolata-LGC-Italic.sfd Inconsolata-LGC-BoldItalic.sfd -1.6 || exit $?
../scripts/interpolate.py ../build/Inconsolata-LGC-Maximum.sfd Inconsolata-LGC.sfd Inconsolata-LGC-Bold.sfd 2.5 || exit $?
../scripts/interpolate.py ../build/Inconsolata-LGC-MaximumItalic.sfd Inconsolata-LGC-Italic.sfd Inconsolata-LGC-BoldItalic.sfd 2.5 || exit $?

cd ../build

for i in *.sfd; do
        fontforge -lang=py -script <<EOS || exit $?
import fontforge
font = fontforge.open("$i")
font.generate("../build/${i%sfd}ufo")
font.close()
EOS
done

for i in *.ufo; do
	srcdir=.
	stat ${i%ufo}sfd > /dev/null || srcdir=../sources
	../scripts/ufo-workaround.py $i $srcdir/${i%ufo}sfd || exit $?
done

../scripts/make_designspace.py Inconsolata-LGC.designspace Inconsolata-LGC.ufo Inconsolata-LGC-Bold.ufo Inconsolata-LGC-Minimum.ufo Inconsolata-LGC-Maximum.ufo || exit $?
../scripts/make_designspace.py Inconsolata-LGC-Italic.designspace Inconsolata-LGC-Italic.ufo Inconsolata-LGC-BoldItalic.ufo Inconsolata-LGC-MinimumItalic.ufo Inconsolata-LGC-MaximumItalic.ufo || exit $?

fontmake -m Inconsolata-LGC.designspace -o variable --output-path ../fonts/variable/Inconsolata-LGC\[wght\].ttf || exit $?
fontmake -m Inconsolata-LGC-Italic.designspace -o variable --output-path ../fonts/variable/Inconsolata-LGC-Italic\[wght\].ttf || exit $?

for i in ../sources/*.sfd; do
	for j in ro pl bg mkd liv smi zhp ewe cv; do
		../scripts/regional.rb $j < $i > $(basename $i .sfd)-$j.sfd || exit $?
	done

	../scripts/makettc.py ../fonts/ttc/$(basename $i .sfd).ttc $i \
		$(basename $i .sfd)-ro.sfd \
		$(basename $i .sfd)-pl.sfd \
		$(basename $i .sfd)-bg.sfd \
		$(basename $i .sfd)-mkd.sfd \
		$(basename $i .sfd)-liv.sfd \
		$(basename $i .sfd)-smi.sfd \
		$(basename $i .sfd)-zhp.sfd \
		$(basename $i .sfd)-ewe.sfd \
		$(basename $i .sfd)-cv.sfd \
		|| exit $?
done

cd "$startdir"
rm -rf ../build
