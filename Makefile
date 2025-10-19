.PHONY: all build check
check= || (e=$$?; rm -rf testdir; exit $$e)
all: build check

venv:
	python3 -m venv venv ${check}
	(source venv/bin/activate && pip3 install -r requirements.txt) ${check}
	(source venv/bin/activate && pip3 install fontbakery shaperglot glyphsets) ${check}

build: venv
	source venv/bin/activate; cd sources; ./build.sh

check: build
	source venv/bin/activate; \
		fontbakery check-universal \
		-x opentype/STAT/ital_axis \
		-x smart_dropout \
		fonts/ttf/*.ttf
