# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file '_guide_window.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


class Ui_GuideWindow(object):
    def setupUi(self, GuideWindow):
        if not GuideWindow.objectName():
            GuideWindow.setObjectName(u"GuideWindow")
        GuideWindow.resize(600, 214)
        sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(GuideWindow.sizePolicy().hasHeightForWidth())
        GuideWindow.setSizePolicy(sizePolicy)
        self.centralwidget = QWidget(GuideWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.guide_label = QLabel(self.centralwidget)
        self.guide_label.setObjectName(u"guide_label")
        sizePolicy1 = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.guide_label.sizePolicy().hasHeightForWidth())
        self.guide_label.setSizePolicy(sizePolicy1)
        self.guide_label.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)

        self.horizontalLayout.addWidget(self.guide_label)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.btn_config = QPushButton(self.centralwidget)
        self.btn_config.setObjectName(u"btn_config")

        self.verticalLayout.addWidget(self.btn_config)

        self.btn_backup = QPushButton(self.centralwidget)
        self.btn_backup.setObjectName(u"btn_backup")

        self.verticalLayout.addWidget(self.btn_backup)

        self.btn_website = QPushButton(self.centralwidget)
        self.btn_website.setObjectName(u"btn_website")

        self.verticalLayout.addWidget(self.btn_website)

        self.btn_donate = QPushButton(self.centralwidget)
        self.btn_donate.setObjectName(u"btn_donate")

        self.verticalLayout.addWidget(self.btn_donate)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.horizontalLayout.addLayout(self.verticalLayout)

        GuideWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(GuideWindow)

        QMetaObject.connectSlotsByName(GuideWindow)
    # setupUi

    def retranslateUi(self, GuideWindow):
        GuideWindow.setWindowTitle(QCoreApplication.translate("GuideWindow", u"ZMake", None))
        self.guide_label.setText(QCoreApplication.translate("GuideWindow", u"Hello\n"
"123123", None))
        self.btn_config.setText(QCoreApplication.translate("GuideWindow", u"Open config directory", None))
        self.btn_backup.setText(QCoreApplication.translate("GuideWindow", u"Open backup directory", None))
        self.btn_website.setText(QCoreApplication.translate("GuideWindow", u"Website...", None))
        self.btn_donate.setText(QCoreApplication.translate("GuideWindow", u"Donate...", None))
    # retranslateUi

