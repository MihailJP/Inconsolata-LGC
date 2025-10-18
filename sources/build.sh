#!/bin/sh

rm -rf ../build/*
for i in *.sfd; do
        python3 <<EOS
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

../scripts/interpolate.py ../build/Inconsolata-LGC-Minimum.sfd Inconsolata-LGC.sfd Inconsolata-LGC-Bold.sfd -1.6
../scripts/interpolate.py ../build/Inconsolata-LGC-MinimumItalic.sfd Inconsolata-LGC-Italic.sfd Inconsolata-LGC-BoldItalic.sfd -1.6
../scripts/interpolate.py ../build/Inconsolata-LGC-Maximum.sfd Inconsolata-LGC.sfd Inconsolata-LGC-Bold.sfd 2.5
../scripts/interpolate.py ../build/Inconsolata-LGC-MaximumItalic.sfd Inconsolata-LGC-Italic.sfd Inconsolata-LGC-BoldItalic.sfd 2.5

pushd ../build

for i in *.sfd; do
        python3 <<EOS
import fontforge
font = fontforge.open("$i")
font.generate("../build/${i%sfd}ufo")
font.close()
EOS
done

for i in *.ufo; do
srcdir=.
stat ${i%ufo}sfd > /dev/null || srcdir=../sources
sed -i~ -f - <<EOS $i/fontinfo.plist
/<key>openTypeNameVersion<\/key>/ {
n
s/<string>.*<\/string>/\<string>$(grep "^Version: " $srcdir/${i%ufo}sfd | sed -e "s/^Version: //")<\/string>\n\
    <key>postscriptIsFixedPitch<\/key>\n\
    <true\/>/
}
EOS
done

../scripts/make_designspace.py Inconsolata-LGC.designspace Inconsolata-LGC.ufo Inconsolata-LGC-Bold.ufo Inconsolata-LGC-Minimum.ufo Inconsolata-LGC-Maximum.ufo
../scripts/make_designspace.py Inconsolata-LGC-Italic.designspace Inconsolata-LGC-Italic.ufo Inconsolata-LGC-BoldItalic.ufo Inconsolata-LGC-MinimumItalic.ufo Inconsolata-LGC-MaximumItalic.ufo

fontmake -m Inconsolata-LGC.designspace -o variable --output-path ../fonts/variable/Inconsolata-LGC\[wght\].ttf
fontmake -m Inconsolata-LGC-Italic.designspace -o variable --output-path ../fonts/variable/Inconsolata-LGC-Italic\[wght\].ttf

for i in ../sources/*.sfd; do
	for j in ro pl bg mkd liv smi zhp ewe cv; do
		../scripts/regional.rb $j < $i > $(basename $i .sfd)-$j.sfd
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
		$(basename $i .sfd)-cv.sfd
done

popd
