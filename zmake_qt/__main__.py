import logging
import sys
import threading
import time
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QApplication, QInputDialog

from zmake import ZMakeContext
from zmake_qt.main import ProgressWindow, GuideWindow

logging.basicConfig(level=logging.INFO)


class QtLogHandler(logging.StreamHandler):
    def __init__(self, signal):
        super().__init__()
        self.signal = signal

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        self.signal.emit(msg)


# noinspection PyUnresolvedReferences
class ZMakeThread(QThread):
    on_data = Signal(str)
    on_dialog = Signal(list)
    on_finish = Signal(bool)
    ev_dialog_closed = threading.Event()
    dialog_response = "none"

    def __init__(self, parent_window: ProgressWindow, path: str):
        super().__init__()
        self.parent_window = parent_window
        self.path = path

        self.log_handler = QtLogHandler(self.on_data)
        self.on_finish.connect(self.parent_window.close)
        self.on_data.connect(self.parent_window.write_log)
        self.on_dialog.connect(self.open_dialog)

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
            self.parent_window.remove_progress()
        except Exception:
            time.sleep(0.5)
            self.parent_window.log_view.append("Build failed")
            return

        time.sleep(0.5)
        self.on_finish.emit(True)


def main():
    app = QApplication(sys.argv)

    if len(sys.argv) < 2:
        window = GuideWindow()
        window.show()
    else:
        window = ProgressWindow()
        window.show()

        build_thread = ZMakeThread(window, sys.argv[1])
        build_thread.start()

    app.exec()


main()
