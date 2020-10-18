import os
from trigger.ui.Qt import QtWidgets

class BrowserButton(QtWidgets.QPushButton):
    def __init__(self, text="Browse", update_widget=None, mode="openFile", filterExtensions=None, title=None, overwrite_check=True):
        super(BrowserButton, self).__init__()
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
            new_path = dlg[0] if dlg else None
        elif self._mode == "saveFile":
            if not self._overwriteCheck:
                dlg = QtWidgets.QFileDialog.getSaveFileName(self, self._title, self._selectedPath, self._filterExtensions, options=(QtWidgets.QFileDialog.DontConfirmOverwrite))
            else:
                dlg = QtWidgets.QFileDialog.getSaveFileName(self, self._title, self._selectedPath, self._filterExtensions)
            new_path = dlg[0] if dlg else None
        elif self._mode == "directory":
            dlg = QtWidgets.QFileDialog.getExistingDirectory(self, self._title, self._selectedPath, options=(QtWidgets.QFileDialog.ShowDirsOnly))
            new_path = dlg if dlg else None
        else:
            new_path = None

        if new_path:
            self._selectedPath = os.path.normpath(new_path)
            if self._updateWidget:
                self._updateWidget.setText(self._selectedPath)
            self.click()

        return new_path

    def mouseReleaseEvent(self, *args, **kwargs):
        super(BrowserButton, self).mouseReleaseEvent(*args, **kwargs)
        self.browserEvent()

class Pops(object):
    def __init__(self):
        super(Pops, self).__init__()

    def infoPop(self, textTitle="info", textHeader="", textInfo="", type="I"):
        msg = QtWidgets.QMessageBox(parent=self)
        if type == "I":
            msg.setIcon(QtWidgets.QMessageBox.Information)
        if type == "C":
            msg.setIcon(QtWidgets.QMessageBox.Critical)

        msg.setText(textHeader)
        msg.setInformativeText(textInfo)
        msg.setWindowTitle(textTitle)
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.button(QtWidgets.QMessageBox.Ok).setFixedHeight(30)
        msg.button(QtWidgets.QMessageBox.Ok).setFixedWidth(100)
        msg.show()

    def queryPop(self, type, textTitle="Question", textHeader="", textInfo=""):
        """
        Pops a query window

        Args:
            type: (String) Valid types are: 'yesNoCancel', 'okCancel', 'yesNo'
            textTitle: (String) Title of the text
            textHeader: (String) Message header
            textInfo: (String) Message details

        Returns: (String) 'yes', 'no', 'ok' or 'cancel' depending on the type

        """

        if type == "yesNoCancel":

            q = QtWidgets.QMessageBox(parent=self)
            q.setIcon(QtWidgets.QMessageBox.Question)
            q.setText(textHeader)
            q.setInformativeText(textInfo)
            q.setWindowTitle(textTitle)
            q.setStandardButtons(
                QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Cancel)

            q.button(QtWidgets.QMessageBox.Save).setFixedHeight(30)
            q.button(QtWidgets.QMessageBox.Save).setFixedWidth(100)
            q.button(QtWidgets.QMessageBox.No).setFixedHeight(30)
            q.button(QtWidgets.QMessageBox.No).setFixedWidth(100)
            q.button(QtWidgets.QMessageBox.Cancel).setFixedHeight(30)
            q.button(QtWidgets.QMessageBox.Cancel).setFixedWidth(100)
            ret = q.exec_()
            if ret == QtWidgets.QMessageBox.Save:
                return "yes"
            elif ret == QtWidgets.QMessageBox.No:
                return "no"
            elif ret == QtWidgets.QMessageBox.Cancel:
                return "cancel"

        if type == "okCancel":
            q = QtWidgets.QMessageBox(parent=self)
            q.setIcon(QtWidgets.QMessageBox.Question)
            q.setText(textHeader)
            q.setInformativeText(textInfo)
            q.setWindowTitle(textTitle)
            q.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
            q.button(QtWidgets.QMessageBox.Ok).setFixedHeight(30)
            q.button(QtWidgets.QMessageBox.Ok).setFixedWidth(100)
            q.button(QtWidgets.QMessageBox.Cancel).setFixedHeight(30)
            q.button(QtWidgets.QMessageBox.Cancel).setFixedWidth(100)
            ret = q.exec_()
            if ret == QtWidgets.QMessageBox.Ok:
                return "ok"
            elif ret == QtWidgets.QMessageBox.Cancel:
                return "cancel"

        if type == "yesNo":
            q = QtWidgets.QMessageBox(parent=self)
            q.setIcon(QtWidgets.QMessageBox.Question)
            q.setText(textHeader)
            q.setInformativeText(textInfo)
            q.setWindowTitle(textTitle)
            q.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            q.button(QtWidgets.QMessageBox.Yes).setFixedHeight(30)
            q.button(QtWidgets.QMessageBox.Yes).setFixedWidth(100)
            q.button(QtWidgets.QMessageBox.No).setFixedHeight(30)
            q.button(QtWidgets.QMessageBox.No).setFixedWidth(100)
            ret = q.exec_()
            if ret == QtWidgets.QMessageBox.Yes:
                return "yes"
            elif ret == QtWidgets.QMessageBox.No:
                return "no"
