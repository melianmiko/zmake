DESTDIR=

all:
	echo "Nothing to do"

install:
	rm -rf ${DESTDIR}/opt/zmake
	mkdir -p ${DESTDIR}/opt
	cp -r zmake/ ${DESTDIR}/opt/zmake
	mkdir -p ${DESTDIR}/usr/bin
	cp docs/linux_entrypoint.py ${DESTDIR}/usr/bin/zmake
	rm -rf ${DESTDIR}/opt/zmake/backups

uninstall:
	rm -rf ${DESTDIR}/opt/zmake
	rm -f ${DESTDIR}/usr/bin/zmake
