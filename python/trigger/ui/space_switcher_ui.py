from trigger.ui.Qt import QtWidgets, QtCore, QtGui
from trigger.ui.qtmaya import get_main_maya_window
from trigger.ui import feedback
from trigger.library.selection import validate

windowName = "AnchorMaker"

from trigger.utils import space_switcher


def launch():
    _ = MainUI().show()


class MainUI(QtWidgets.QDialog):
    def __init__(self):
        for entry in QtWidgets.QApplication.allWidgets():
            try:
                if entry.objectName() == windowName:
                    entry.close()
            except:
                pass
        parent = get_main_maya_window()
        super(MainUI, self).__init__(parent=parent)

        self.feed = feedback.Feedback()
        self.setWindowTitle(windowName)
        self.setObjectName(windowName)
        self.build_ui()
        self.anchorObject = None
        self.anchorLocations = []

    def build_ui(self):
        self.setObjectName(("anchormaker_Dialog"))
        self.resize(288, 197)
        self.setWindowTitle(("Anchor Maker"))

        self.anchortype_comboBox = QtWidgets.QComboBox(self)
        self.anchortype_comboBox.setGeometry(QtCore.QRect(110, 20, 101, 22))
        self.anchortype_comboBox.setObjectName(("anchortype_comboBox"))
        self.anchortype_comboBox.addItem((""))
        self.anchortype_comboBox.setItemText(0, ("parent"))
        self.anchortype_comboBox.addItem((""))
        self.anchortype_comboBox.setItemText(1, ("point"))
        self.anchortype_comboBox.addItem((""))
        self.anchortype_comboBox.setItemText(2, ("orient"))

        self.anchortype_label = QtWidgets.QLabel(self)
        self.anchortype_label.setGeometry(QtCore.QRect(20, 20, 81, 21))
        self.anchortype_label.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.anchortype_label.setText(("Anchor Type:"))
        self.anchortype_label.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter
        )
        self.anchortype_label.setObjectName(("anchortype_label"))

        self.anchorobject_lineEdit = QtWidgets.QLineEdit(self)
        self.anchorobject_lineEdit.setGeometry(QtCore.QRect(110, 50, 101, 21))
        self.anchorobject_lineEdit.setToolTip(
            ("This is the object that will be anchored to different locations")
        )
        self.anchorobject_lineEdit.setPlaceholderText(("select and hit 'get'"))
        self.anchorobject_lineEdit.setObjectName(("anchorobject_lineEdit"))
        self.anchorobject_lineEdit.setReadOnly(True)

        self.anchorobject_label = QtWidgets.QLabel(self)
        self.anchorobject_label.setGeometry(QtCore.QRect(20, 50, 81, 21))
        self.anchorobject_label.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.anchorobject_label.setText(("Anchor Object:"))
        self.anchorobject_label.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter
        )
        self.anchorobject_label.setObjectName(("anchorobject_label"))

        self.locationobjects_lineEdit = QtWidgets.QLineEdit(self)
        self.locationobjects_lineEdit.setGeometry(QtCore.QRect(110, 80, 101, 21))
        self.locationobjects_lineEdit.setToolTip(
            ("This is the object that will be anchored to different locations")
        )
        self.locationobjects_lineEdit.setPlaceholderText(("select and hit 'get'"))
        self.locationobjects_lineEdit.setObjectName(("locationobjects_lineEdit"))
        self.locationobjects_lineEdit.setReadOnly(True)

        self.locationobjects_label = QtWidgets.QLabel(self)
        self.locationobjects_label.setGeometry(QtCore.QRect(10, 80, 91, 21))
        self.locationobjects_label.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.locationobjects_label.setText(("Anchor Locations:"))
        self.locationobjects_label.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter
        )
        self.locationobjects_label.setObjectName(("locationobjects_label"))

        self.getanchor_pushButton = QtWidgets.QPushButton(self)
        self.getanchor_pushButton.setGeometry(QtCore.QRect(220, 50, 51, 21))
        self.getanchor_pushButton.setText(("<- Get"))
        self.getanchor_pushButton.setObjectName(("getanchor_pushButton"))

        self.getlocations_pushButton = QtWidgets.QPushButton(self)
        self.getlocations_pushButton.setGeometry(QtCore.QRect(220, 80, 51, 21))
        self.getlocations_pushButton.setText(("<- Get"))
        self.getlocations_pushButton.setObjectName(("getlocations_pushButton"))

        self.deleteanchor_pushButton = QtWidgets.QPushButton(self)
        self.deleteanchor_pushButton.setGeometry(QtCore.QRect(20, 120, 71, 61))
        self.deleteanchor_pushButton.setText(("Delete\nAnchors"))
        self.deleteanchor_pushButton.setObjectName(("deleteanchor_pushButton"))

        self.createanchor_pushButton = QtWidgets.QPushButton(self)
        self.createanchor_pushButton.setGeometry(QtCore.QRect(120, 120, 151, 61))
        self.createanchor_pushButton.setText(("Create\nAnchor"))
        self.createanchor_pushButton.setObjectName(("createanchor_pushButton"))
        self.createanchor_pushButton.setEnabled(False)

        self.getanchor_pushButton.clicked.connect(self.onGetAnchor)
        self.getlocations_pushButton.clicked.connect(self.onGetAnchorLocations)
        self.createanchor_pushButton.clicked.connect(
            lambda: space_switcher.create_space_switch(
                self.anchorObject,
                self.anchorLocations,
                mode=self.anchortype_comboBox.currentText(),
            )
        )
        self.deleteanchor_pushButton.clicked.connect(self.onDeleteAnchor)

    def onGetAnchor(self):
        selection, msg = validate(minimum=1, maximum=1, transforms=True)
        if not selection:
            self.feed.pop_info(title="Selection Error", text=msg, critical=True)
            return
        self.anchorobject_lineEdit.setText(selection[0])
        self.anchorobject_lineEdit.setStyleSheet(
            "background-color: yellow; color: black"
        )
        self.anchorObject = selection[0]
        if not self.anchorLocations == []:
            self.createanchor_pushButton.setEnabled(True)
            self.createanchor_pushButton.setStyleSheet(
                "background-color: green; color: black"
            )

    def onGetAnchorLocations(self):
        selection, msg = validate(minimum=1, maximum=None, transforms=True)
        if not selection:
            self.feed.pop_info(title="Selection Error", text=msg, critical=True)
            return
        self.locationobjects_lineEdit.setText("%s items" % len(selection))
        self.locationobjects_lineEdit.setStyleSheet(
            "background-color: yellow; color: black"
        )
        self.anchorLocations = selection
        if self.anchorObject:
            self.createanchor_pushButton.setEnabled(True)
            self.createanchor_pushButton.setStyleSheet(
                "background-color: green; color: black"
            )

    def onDeleteAnchor(self):
        selection, msg = validate(minimum=1, maximum=None, transforms=True)
        if selection:
            for i in selection:
                space_switcher.remove_space_switch(i)
