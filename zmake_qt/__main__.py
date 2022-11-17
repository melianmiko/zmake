import logging
import sys
import threading
import time
from pathlib import Path

from PySide2.QtCore import QThread, Signal

import zmake
from zmake import ZMakeContext
from zmake_qt.qt_window import Ui_MainWindow
from PySide2.QtWidgets import QApplication, QMessageBox, QInputDialog

logging.basicConfig(level=logging.INFO)


class QtLogHandler(logging.StreamHandler):
    def __init__(self, signal):
        super().__init__()
        self.signal = signal

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        self.signal.emit(msg)


class ZMakeQtContext(ZMakeContext):
    def __init__(self, path, logHandler):
        super().__init__(path)
        self.logger.addHandler()


# noinspection PyUnresolvedReferences
class ZMakeThread(QThread):
    on_data = Signal(str)
    on_dialog = Signal(list)
    ev_dialog_closed = threading.Event()
    dialog_response = "none"

    def __init__(self, parent_window: Ui_MainWindow, path: str):
        super().__init__()
        self.parent_window = parent_window
        self.path = path

        self.log_handler = QtLogHandler(self.on_data)
        self.on_data.connect(self.write_log)
        self.on_dialog.connect(self.open_dialog)

    def write_log(self, msg):
        self.parent_window.log_view.append(msg)

    def open_dialog(self, data):
        msg, options = data
        item, ok = QInputDialog.getItem(self.parent_window,
                                        "Question",
                                        msg,
                                        options, 0, False)

        if not ok:
            self.parent_window.close()
            return

        self.dialog_response = item
        self.ev_dialog_closed.set()

    def ask_question(self, msg, options):
        self.ev_dialog_closed.clear()

        self.on_dialog.emit([msg, options])
        print("Waiting for resp")
        self.ev_dialog_closed.wait()
        return self.dialog_response

    def run(self):
        path = Path(self.path).resolve()

        context = ZMakeContext(path)
        context.logger.addHandler(self.log_handler)
        context.ask_question = self.ask_question

        # noinspection PyBroadException
        try:
            context.perform_auto()
            time.sleep(0.5)
            self.parent_window.close()
        except Exception:
            time.sleep(0.5)
            self.parent_window.log_view.append("Build failed")


def main():
    app = QApplication(sys.argv)

    if len(sys.argv) < 1:
        # noinspection PyTypeChecker
        QMessageBox.information(None, "ZMake", zmake.GUIDE)
        return

    window = Ui_MainWindow()
    window.setupUi(window)
    window.show()

    build_thread = ZMakeThread(window, sys.argv[1])
    build_thread.start()

    app.exec_()


main()
