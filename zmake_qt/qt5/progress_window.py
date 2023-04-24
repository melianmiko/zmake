# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'progress_window.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_ProgressWindow(object):
    def setupUi(self, ProgressWindow):
        if not ProgressWindow.objectName():
            ProgressWindow.setObjectName(u"ProgressWindow")
        ProgressWindow.resize(500, 600)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ProgressWindow.sizePolicy().hasHeightForWidth())
        ProgressWindow.setSizePolicy(sizePolicy)
        ProgressWindow.setMinimumSize(QSize(500, 600))
        ProgressWindow.setMaximumSize(QSize(500, 600))
        self.centralwidget = QWidget(ProgressWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.progressBar = QProgressBar(self.centralwidget)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setMaximum(0)
        self.progressBar.setValue(0)
        self.progressBar.setInvertedAppearance(False)

        self.verticalLayout.addWidget(self.progressBar)

        self.log_view = QTextBrowser(self.centralwidget)
        self.log_view.setObjectName(u"log_view")

        self.verticalLayout.addWidget(self.log_view)

        ProgressWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(ProgressWindow)

        QMetaObject.connectSlotsByName(ProgressWindow)
    # setupUi

    def retranslateUi(self, ProgressWindow):
        ProgressWindow.setWindowTitle(QCoreApplication.translate("ProgressWindow", u"ZMake: Processing...", None))
        self.progressBar.setFormat("")
    # retranslateUi

