DESTDIR=

all:
	echo "Nothing to do"

make_qt:
	pyside6-uic -o zmake_qt/_guide_window.py zmake_qt/_guide_window.ui
	pyside6-uic -o zmake_qt/_progress_window.py zmake_qt/_progress_window.ui

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
