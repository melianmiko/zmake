DESTDIR=

all:
	echo "Nothing to do"

make_qt5:
	pyside2-uic -o zmake_qt/qt5/guide_window.py zmake_qt/qt_src/guide_window.ui
	pyside2-uic -o zmake_qt/qt5/progress_window.py zmake_qt/qt_src/progress_window.ui

make_qt6:
	pyside6-uic -o zmake_qt/qt6/guide_window.py zmake_qt/qt_src/guide_window.ui
	pyside6-uic -o zmake_qt/qt6/progress_window.py zmake_qt/qt_src/progress_window.ui

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
