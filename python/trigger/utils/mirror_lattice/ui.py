import os
import logging
from tabnanny import check

# from Qt import QtWidgets, QtCore
from trigger.ui.Qt import QtWidgets, QtCore

# from dnmayalib.interface import main_window
from trigger.ui.qtmaya import getMayaMainWindow as main_window

from .mirror_lattice import MirrorLattice

LOG = logging.getLogger(__name__)

WINDOWNAME = "Anatomy Transfer Tools v0.0.1"


class MainUI(QtWidgets.QDialog):
    def __init__(self):
        for entry in QtWidgets.QApplication.allWidgets():
            try:
                if entry.objectName() == WINDOWNAME:
                    entry.close()
            except (AttributeError, TypeError):
                pass
        parent = main_window()
        super(MainUI, self).__init__(parent=parent)

        self.setWindowTitle(WINDOWNAME)
        self.setObjectName(WINDOWNAME)

        self.size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.size_policy.setHorizontalStretch(1)
        self.size_policy.setVerticalStretch(0)

        self.build_ui()
        # self.setMinimumSize(600, 70)

        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setFocus()

    def build_ui(self):
        master_vlay = QtWidgets.QVBoxLayout()
        self.setLayout(master_vlay)

        mirror_lattice_group = QtWidgets.QGroupBox(title="Mirror Lattice")
        master_vlay.addWidget(mirror_lattice_group)
        mirror_lattice_formlayout = QtWidgets.QFormLayout(mirror_lattice_group)
        # set the alignment of the form layout to center
        mirror_lattice_formlayout.setAlignment(QtCore.Qt.AlignCenter)

        ml_divisions_lbl = QtWidgets.QLabel(text="Divisions: ")
        self.ml_division_box = DivisionBoxLayout()
        self.ml_division_box.spinners[2].setValue(2)
        self.ml_division_box.spinners[0].setValue(2)
        self.ml_division_box.spinners[1].setValue(5)
        mirror_lattice_formlayout.addRow(ml_divisions_lbl, self.ml_division_box)

        ml_local_divisions_lbl = QtWidgets.QLabel(text="Local divisions: ")
        self.ml_local_divisions_box = DivisionBoxLayout()
        self.ml_local_divisions_box.spinners[0].setValue(2)
        self.ml_local_divisions_box.spinners[1].setValue(2)
        self.ml_local_divisions_box.spinners[2].setValue(2)
        mirror_lattice_formlayout.addRow(ml_local_divisions_lbl, self.ml_local_divisions_box)

        ml_axis_lbl = QtWidgets.QLabel(text="Mirror axis: ")
        self.ml_axis_box = AxisBoxLayout()
        mirror_lattice_formlayout.addRow(ml_axis_lbl, self.ml_axis_box)

        _ = QtWidgets.QLabel(text="")
        ml_create_btn = QtWidgets.QPushButton(text="Create Mirror Lattice")
        ml_create_btn.setSizePolicy(self.size_policy)
        mirror_lattice_formlayout.addRow(_, ml_create_btn)

        ml_create_btn.clicked.connect(self.on_create_mirror_lattice)

    def on_create_mirror_lattice(self):
        """Create a mirror lattice from selection"""
        # selection = cmds.ls(sl=True)
        mirror_lattice = MirrorLattice(set_from_selection=True)
        mirror_lattice.divisions = [self.ml_division_box.spinners[0].value(),
                                    self.ml_division_box.spinners[1].value(),
                                    self.ml_division_box.spinners[2].value()]
        mirror_lattice.local_divisions = [self.ml_local_divisions_box.spinners[0].value(),
                                          self.ml_local_divisions_box.spinners[1].value(),
                                          self.ml_local_divisions_box.spinners[2].value()]
        mirror_lattice.mirror_axis = self.ml_axis_box.get_axis()
        mirror_lattice.create()

class AxisBoxLayout(QtWidgets.QHBoxLayout):
    def __init__(self, parent=None):
        super(AxisBoxLayout, self).__init__(parent=parent)
        self.x = QtWidgets.QRadioButton("X")
        self.y = QtWidgets.QRadioButton("Y")
        self.z = QtWidgets.QRadioButton("Z")
        ml_axis_group = QtWidgets.QButtonGroup()
        ml_axis_group.addButton(self.x)
        ml_axis_group.addButton(self.y)
        ml_axis_group.addButton(self.z)
        self.addWidget(self.x)
        self.addWidget(self.y)
        self.addWidget(self.z)
        self.x.setChecked(True)

    def get_axis(self):
        if self.x.isChecked():
            return "x"
        elif self.y.isChecked():
            return "y"
        elif self.z.isChecked():
            return "z"
        else:
            raise ValueError("No axis selected")

class DivisionBoxLayout(QtWidgets.QHBoxLayout):
    """Custom layout for the division spinners"""

    def __init__(self, parent=None, spinner_count=3, is_integer=True):
        super(DivisionBoxLayout, self).__init__(parent=parent)
        # self.setSpacing(10)
        self.setContentsMargins(0, 0, 0, 0)
        self.is_integer = is_integer
        self.spinner_count = spinner_count
        self.spinners = []

        # align the layout to the right
        self.setAlignment(QtCore.Qt.AlignRight)

        self.initilaize()

    def initilaize(self):
        # clear all existing widgets
        for i in reversed(range(self.count())):
            self.itemAt(i).widget().setParent(None)

        for nmb in range(self.spinner_count):
            # create a spinner widget
            if self.is_integer:
                spinner_widget = QtWidgets.QSpinBox()
            else:
                spinner_widget = QtWidgets.QDoubleSpinBox()
            # set the spinner widget properties
            spinner_widget.setRange(1, 100)
            spinner_widget.setFixedWidth(100)
            spinner_widget.setMinimumHeight(30)
            spinner_widget.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
            spinner_widget.setFrame(False)
            spinner_widget.setAlignment(QtCore.Qt.AlignCenter)

            self.spinners.append(spinner_widget)
            # add it to the layout
            self.addWidget(spinner_widget)


class FileLineEdit(QtWidgets.QLineEdit):
    """Custom Line Edit Widget specific for file and folder paths with version increment and sanity checks"""

    def __init__(self, connected_widgets=None, *args, **kwargs):
        super(FileLineEdit, self).__init__(*args, **kwargs)
        self.default_stylesheet = self.styleSheet()
        if connected_widgets:
            if not isinstance(connected_widgets, list):
                self._connected_widgets = [connected_widgets]
        else:
            self._connected_widgets = []

        self.textChanged.connect(self.validate)

    def setConnectedWidgets(self, widgets):
        if not isinstance(widgets, list):
            self._connected_widgets = [widgets]
        else:
            self._connected_widgets = widgets

    def validate(self):
        text = os.path.normpath(str(self.text()))
        if text == ".":
            for wid in self._connected_widgets:
                wid.setEnabled(False)
            return
        if os.path.isdir(text):
            self.setStyleSheet(self.default_stylesheet)
            for wid in self._connected_widgets:
                wid.setEnabled(True)
        else:
            self.setStyleSheet("background-color: rgb(40,40,40); color: red")
            for wid in self._connected_widgets:
                wid.setEnabled(False)

    def moveEvent(self, *args, **kwargs):
        super(FileLineEdit, self).moveEvent(*args, **kwargs)
        self.validate()

    def leaveEvent(self, *args, **kwargs):
        super(FileLineEdit, self).leaveEvent(*args, **kwargs)
        self.validate()


class BrowserButton(QtWidgets.QPushButton):
    def __init__(self, text="Browse", update_widget=None, mode="openFile", filterExtensions=None, title=None,
                 overwrite_check=True, *args, **kwargs):
        """
        Customized Pushbutton opens the file browser by default

        Args:
            text: (string) Button label
            update_widget: (QLineEdit) The line edit widget which will be updated with selected path (optional)
            mode: (string) Sets the file browser mode. Valid modes are 'openFile', 'saveFile', 'directory'
            filterExtensions: (list) if defined, only the extensions defined here will be shown in the file browser
            title: (string) Title of the browser window
            overwrite_check: (bool) If set True and if the defined file exists, it will pop up a confirmation box.
                                    works only with 'openFile' mode
            *args:
            **kwargs:
        """
        super(BrowserButton, self).__init__(*args, **kwargs)
        self._updateWidget = update_widget
        if text:
            self.setText(text)
        self._validModes = ["openFile", "saveFile", "directory"]
        if mode in self._validModes:
            self._mode = mode
        else:
            raise Exception("Mode is not valid. Valid modes are %s" % (", ".join(self._validModes)))
        self._filterExtensions = self._listToFilter(filterExtensions) if filterExtensions else ""
        self._title = title if title else ""
        self._selectedPath = ""
        self._overwriteCheck = overwrite_check
        self._cancelFlag = False

    def isCancelled(self):
        return self._cancelFlag

    def setUpdateWidget(self, widget):
        self._updateWidget = widget

    def updateWidget(self):
        return self._updateWidget

    def setMode(self, mode):
        if mode not in self._validModes:
            raise Exception("Mode is not valid. Valid modes are %s" % (", ".join(self._validModes)))
        self._mode = mode

    def mode(self):
        return self._mode

    def setFilterExtensions(self, extensionlist):
        self._filterExtensions = self._listToFilter(extensionlist)

    def selectedPath(self):
        return self._selectedPath

    def setSelectedPath(self, new_path):
        self._selectedPath = new_path

    def setTitle(self, title):
        self._title = title

    def title(self):
        return self._title

    def _listToFilter(self, filter_list):
        return ";;".join(filter_list)

    def browserEvent(self):
        self._cancelFlag = False
        if self._updateWidget:
            default_path = str(self._updateWidget.text())
        else:
            default_path = self._selectedPath
        if self._mode == "openFile":
            dlg = QtWidgets.QFileDialog.getOpenFileName(self, self._title, default_path, self._filterExtensions)
            if dlg:
                new_path, selected_extension = dlg
            else:
                new_path, selected_extension = None, None
        elif self._mode == "saveFile":
            if not self._overwriteCheck:
                dlg = QtWidgets.QFileDialog.getSaveFileName(self, self._title, default_path, self._filterExtensions,
                                                            options=(QtWidgets.QFileDialog.DontConfirmOverwrite))
            else:
                dlg = QtWidgets.QFileDialog.getSaveFileName(self, self._title, default_path, self._filterExtensions)
            if dlg:
                new_path, selected_extension = dlg
            else:
                new_path, selected_extension = None, None
        elif self._mode == "directory":
            dlg = QtWidgets.QFileDialog.getExistingDirectory(self, self._title, default_path,
                                                             options=(QtWidgets.QFileDialog.ShowDirsOnly))
            if dlg:
                new_path = dlg
            else:
                new_path = None
        else:
            new_path = None
            selected_extension = None

        if new_path:
            if self._mode == "saveFile" and selected_extension:
                ext = selected_extension.split('(*', 1)[1].split(')')[0]
                if not new_path.endswith(ext):
                    new_path = "%s%s" % (new_path, ext)
            self._selectedPath = os.path.normpath(new_path)
            if self._updateWidget:
                self._updateWidget.setText(self._selectedPath)
            self.click()
        else:
            self._cancelFlag = True

        return new_path

    def mouseReleaseEvent(self, *args, **kwargs):
        self.browserEvent()
        super(BrowserButton, self).mouseReleaseEvent(*args, **kwargs)
