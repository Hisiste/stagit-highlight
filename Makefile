PREFIX = /usr/local
target = stagit-highlight

all:

.PHONY: install
install:
	cp ${target}.py ${DESTDIR}${PREFIX}/bin/${target}
