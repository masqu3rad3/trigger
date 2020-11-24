import os
from trigger.ui.Qt import QtWidgets
from trigger.core import foolproof
from PySide2 import QtWidgets

class BrowserButton(QtWidgets.QPushButton):
    def __init__(self, text="Browse", update_widget=None, mode="openFile", filterExtensions=None, title=None, overwrite_check=True, *args, **kwargs):
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
        self._overwriteCheck=overwrite_check

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
        if self._mode == "openFile":
            dlg = QtWidgets.QFileDialog.getOpenFileName(self, self._title, self._selectedPath, self._filterExtensions)
            if dlg: new_path, selected_extension = dlg
            else: new_path, selected_extension = None, None
            # new_path = dlg[0] if dlg else None
        elif self._mode == "saveFile":
            if not self._overwriteCheck:
                dlg = QtWidgets.QFileDialog.getSaveFileName(self, self._title, self._selectedPath, self._filterExtensions, options=(QtWidgets.QFileDialog.DontConfirmOverwrite))
            else:
                dlg = QtWidgets.QFileDialog.getSaveFileName(self, self._title, self._selectedPath, self._filterExtensions)
            # new_path = dlg[0] if dlg else None
            if dlg: new_path, selected_extension = dlg
            else: new_path, selected_extension = None, None
        elif self._mode == "directory":
            dlg = QtWidgets.QFileDialog.getExistingDirectory(self, self._title, self._selectedPath, options=(QtWidgets.QFileDialog.ShowDirsOnly))
            # new_path = dlg if dlg else None
            if dlg: new_path, selected_extension = dlg
            else: new_path, selected_extension = None, None
        else:
            new_path = None
            selected_extension = None

        if new_path:
            if selected_extension:
                ext = selected_extension.split('(*', 1)[1].split(')')[0]
                if not new_path.endswith(ext):
                    new_path = "%s%s" %(new_path, ext)
            self._selectedPath = os.path.normpath(new_path)
            if self._updateWidget:
                self._updateWidget.setText(self._selectedPath)
            self.click()

        return new_path

    def mouseReleaseEvent(self, *args, **kwargs):
        self.browserEvent()
        super(BrowserButton, self).mouseReleaseEvent(*args, **kwargs)

class ValidatedLineEdit(QtWidgets.QLineEdit):
    def __init__(self, connected_widgets=None, allowSpaces=False, allowDirectory=False, *args, **kwargs):
        super(ValidatedLineEdit, self).__init__(*args, **kwargs)
        self.allowSpaces = allowSpaces
        self.allowDirectory = allowDirectory
        self.connected_widgets = connected_widgets
        self.default_stylesheet = self.styleSheet()
        if connected_widgets:
            if type(connected_widgets) != list:
                self._connected_widgets = [connected_widgets]
        else:
            self._connected_widgets = []

    def setConnectedWidgets(self, widgets):
        if type(widgets) != list:
            self._connected_widgets = [widgets]
        else:
            self._connected_widgets = widgets

    def connectedWidgets(self):
        return self._connected_widgets

    # @property
    # def connected_widgets(self):
    #     return self._connected_widgets

    # @connected_widgets.setter
    # def connected_widgets(self, widgets):
    #     if type(widgets) != list:
    #         self._connected_widgets = [widgets]
    #     else:
    #         self._connected_widgets = widgets

    def keyPressEvent(self, *args, **kwargs):
        super(ValidatedLineEdit, self).keyPressEvent(*args, **kwargs)
        current_text = self.text()
        if not foolproof.text(current_text, allowSpaces=self.allowSpaces, directory=self.allowDirectory):
            self.setStyleSheet("background-color: rgb(40,40,40); color: red")
            if self.connected_widgets:
                for wid in self.connected_widgets:
                    wid.setEnabled(False)
        else:
            # self.setStyleSheet("background-color: rgb(40,40,40); color: white")
            self.setStyleSheet(self.default_stylesheet)
            if self.connected_widgets:
                for wid in self.connected_widgets:
                    wid.setEnabled(True)