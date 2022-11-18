from PySide2.QtWidgets import QMainWindow

from zmake_qt._progress_window import Ui_ProgressWindow


class ProgressWindow(QMainWindow, Ui_ProgressWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

    def write_log(self, msg):
        self.log_view.append(msg)


