# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'modules_part_only.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(537, 256)
        self.module_create_splitter = QtWidgets.QSplitter(Dialog)
        self.module_create_splitter.setGeometry(QtCore.QRect(30, 30, 473, 192))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.module_create_splitter.sizePolicy().hasHeightForWidth())
        self.module_create_splitter.setSizePolicy(sizePolicy)
        self.module_create_splitter.setOrientation(QtCore.Qt.Horizontal)

        self.verticalLayoutWidget_2 = QtWidgets.QWidget(self.module_create_splitter)

        self.guides_create_vLay = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_2)
        self.guides_create_vLay.setContentsMargins(0, 0, 0, 0)

        self.guides_sides_hLay = QtWidgets.QHBoxLayout()

        self.guides_sides_L_rb = QtWidgets.QRadioButton(self.verticalLayoutWidget_2)
        self.guides_sides_L_rb.setText("L")
        self.guides_sides_hLay.addWidget(self.guides_sides_L_rb)

        self.guides_sides_R_rb = QtWidgets.QRadioButton(self.verticalLayoutWidget_2)
        self.guides_sides_R_rb.setText("R")

        self.guides_sides_hLay.addWidget(self.guides_sides_R_rb)

        self.guides_sides_Both_rb = QtWidgets.QRadioButton(self.verticalLayoutWidget_2)
        self.guides_sides_Both_rb.setText("Both")

        self.guides_sides_hLay.addWidget(self.guides_sides_Both_rb)

        self.guides_sides_Auto_rb = QtWidgets.QRadioButton(self.verticalLayoutWidget_2)
        self.guides_sides_Auto_rb.setText("Auto")

        self.guides_sides_hLay.addWidget(self.guides_sides_Auto_rb)

        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.guides_sides_hLay.addItem(spacerItem)

        self.guides_create_vLay.addLayout(self.guides_sides_hLay)
        self.guide_buttons_vLay = QtWidgets.QVBoxLayout()

        self.guide_button_sample_hLay1 = QtWidgets.QHBoxLayout()
        self.guide_button_sample_hLay1.setSpacing(2)
        self.guide_button_sample_pb1 = QtWidgets.QPushButton(self.verticalLayoutWidget_2)
        self.guide_button_sample_pb1.setText("Arm")
        self.guide_button_sample_hLay1.addWidget(self.guide_button_sample_pb1)
        self.segments_sample_sp1 = QtWidgets.QSpinBox(self.verticalLayoutWidget_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.segments_sample_sp1.sizePolicy().hasHeightForWidth())
        self.segments_sample_sp1.setSizePolicy(sizePolicy)
        self.guide_button_sample_hLay1.addWidget(self.segments_sample_sp1)
        self.guide_buttons_vLay.addLayout(self.guide_button_sample_hLay1)
        self.guide_button_sample_hLay1_2 = QtWidgets.QHBoxLayout()
        self.guide_button_sample_hLay1_2.setSpacing(2)
        self.guide_button_sample_pb1_2 = QtWidgets.QPushButton(self.verticalLayoutWidget_2)
        self.guide_button_sample_pb1_2.setText("Arm")
        self.guide_button_sample_hLay1_2.addWidget(self.guide_button_sample_pb1_2)
        self.segments_sample_sp1_2 = QtWidgets.QSpinBox(self.verticalLayoutWidget_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.segments_sample_sp1_2.sizePolicy().hasHeightForWidth())
        self.segments_sample_sp1_2.setSizePolicy(sizePolicy)
        self.guide_button_sample_hLay1_2.addWidget(self.segments_sample_sp1_2)
        self.guide_buttons_vLay.addLayout(self.guide_button_sample_hLay1_2)
        self.guide_button_sample_hLay1_3 = QtWidgets.QHBoxLayout()
        self.guide_button_sample_hLay1_3.setSpacing(2)
        self.guide_button_sample_pb1_3 = QtWidgets.QPushButton(self.verticalLayoutWidget_2)
        self.guide_button_sample_pb1_3.setText("Arm")
        self.guide_button_sample_hLay1_3.addWidget(self.guide_button_sample_pb1_3)
        self.segments_sample_sp1_3 = QtWidgets.QSpinBox(self.verticalLayoutWidget_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.segments_sample_sp1_3.sizePolicy().hasHeightForWidth())
        self.segments_sample_sp1_3.setSizePolicy(sizePolicy)
        self.guide_button_sample_hLay1_3.addWidget(self.segments_sample_sp1_3)
        self.guide_buttons_vLay.addLayout(self.guide_button_sample_hLay1_3)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.guide_buttons_vLay.addItem(spacerItem1)
        self.guides_create_vLay.addLayout(self.guide_buttons_vLay)

        self.guides_list_listWidget = QtWidgets.QListWidget(self.module_create_splitter)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(False)
        font.setWeight(50)
        font.setStrikeOut(False)
        self.guides_list_listWidget.setFont(font)
        self.guides_list_listWidget.setMouseTracking(False)
        self.guides_list_listWidget.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.guides_list_listWidget.setViewMode(QtWidgets.QListView.ListMode)

        item = QtWidgets.QListWidgetItem()
        item.setText("Arm")
        item.setTextAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignVCenter)
        self.guides_list_listWidget.addItem(item)
        item = QtWidgets.QListWidgetItem()
        item.setText("Leg")
        item.setTextAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignVCenter)
        self.guides_list_listWidget.addItem(item)
        item = QtWidgets.QListWidgetItem()
        item.setText("Tentacle")
        item.setTextAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignVCenter)
        self.guides_list_listWidget.addItem(item)




        self.retranslateUi(Dialog)
        self.guides_list_listWidget.setCurrentRow(-1)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        __sortingEnabled = self.guides_list_listWidget.isSortingEnabled()
        self.guides_list_listWidget.setSortingEnabled(False)
        self.guides_list_listWidget.setSortingEnabled(__sortingEnabled)
