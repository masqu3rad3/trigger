import os
from trigger.ui.Qt import QtWidgets


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
                new_path, selected_extension = dlg
            else:
                new_path, selected_extension = None, None
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
