"""Browser and File related widgets"""

import os
from trigger.ui.Qt import QtWidgets
from trigger.library import naming


class BrowserButton(QtWidgets.QPushButton):
    def __init__(
        self,
        text=None,
        update_widget=None,
        mode="openFile",
        filterExtensions=None,
        title=None,
        overwrite_check=True,
        *args,
        **kwargs
    ):
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
        else:
            icon = QtWidgets.QApplication.style().standardIcon(QtWidgets.QStyle.SP_DirOpenIcon)
            self.setIcon(icon)
        self._validModes = ["openFile", "saveFile", "directory"]
        if mode in self._validModes:
            self._mode = mode
        else:
            raise Exception(
                "Mode is not valid. Valid modes are %s" % (", ".join(self._validModes))
            )
        self._filterExtensions = (
            self._listToFilter(filterExtensions) if filterExtensions else ""
        )
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
            raise Exception(
                "Mode is not valid. Valid modes are %s" % (", ".join(self._validModes))
            )
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
            dlg = QtWidgets.QFileDialog.getOpenFileName(
                self, self._title, default_path, self._filterExtensions
            )
            if dlg:
                new_path, selected_extension = dlg
            else:
                new_path, selected_extension = None, None
        elif self._mode == "saveFile":
            if not self._overwriteCheck:
                dlg = QtWidgets.QFileDialog.getSaveFileName(
                    self,
                    self._title,
                    default_path,
                    self._filterExtensions,
                    options=(QtWidgets.QFileDialog.DontConfirmOverwrite),
                )
            else:
                dlg = QtWidgets.QFileDialog.getSaveFileName(
                    self, self._title, default_path, self._filterExtensions
                )
            if dlg:
                new_path, selected_extension = dlg
            else:
                new_path, selected_extension = None, None
        elif self._mode == "directory":
            dlg = QtWidgets.QFileDialog.getExistingDirectory(
                self,
                self._title,
                default_path,
                options=(QtWidgets.QFileDialog.ShowDirsOnly),
            )
            new_path = dlg
            selected_extension = None
        else:
            new_path = None
            selected_extension = None

        if new_path:
            if self._mode == "saveFile" and selected_extension:
                ext = selected_extension.split("(*", 1)[1].split(")")[0]
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


class FileLineEdit(QtWidgets.QLineEdit):
    """Custom Line Edit Widget specific for file and folder paths with version increment and sanity checks"""

    def __init__(self, directory=False, *args, **kwargs):
        super(FileLineEdit, self).__init__(*args, **kwargs)
        self.directory = directory
        self.default_stylesheet = self.styleSheet()

    def validate(self):
        text = os.path.normpath(str(self.text()))
        if not text:
            return
        if self.directory:
            if not os.path.isdir(text):
                self.setStyleSheet("background-color: rgb(40,40,40); color: red")
            else:
                self.setStyleSheet(self.default_stylesheet)
        else:
            if not os.path.isfile(text):
                self.setStyleSheet("background-color: rgb(40,40,40); color: red")
            else:
                self.setStyleSheet(self.default_stylesheet)
            if naming.is_latest_version(text):
                self.setStyleSheet(
                    "background-color: rgb(40,40,40); color: rgb(0,255,0)"
                )
            else:
                self.setStyleSheet("background-color: rgb(40,40,40); color: yellow")

    def moveEvent(self, *args, **kwargs):
        super(FileLineEdit, self).moveEvent(*args, **kwargs)
        self.validate()

    def leaveEvent(self, *args, **kwargs):
        super(FileLineEdit, self).leaveEvent(*args, **kwargs)
        self.validate()

    def keyPressEvent(self, e):
        super(FileLineEdit, self).keyPressEvent(e)
        self.validate()
        if e.key() == 16777235:  # CTRL + UP arrow
            self.version_up()

        if e.key() == 16777237:  # CTRL + DOWN arrow
            self.version_down()

    def version_up(self):
        self.setText(naming.get_next_version(str(self.text())))
        self.validate()

    def version_down(self):
        self.setText(naming.get_previous_version(str(self.text())))
        self.validate()

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        menu.addSeparator()

        next_version_action = QtWidgets.QAction(self, text="Next Version")
        previous_version_action = QtWidgets.QAction(self, text="Previous Version")
        menu.addAction(next_version_action)
        menu.addAction(previous_version_action)
        next_version_action.triggered.connect(self.version_up)
        previous_version_action.triggered.connect(self.version_down)

        menu.exec_(event.globalPos())


class FileBrowserBoxLayout(QtWidgets.QHBoxLayout):
    """Custom Layout for File and Folder Browsers"""

    def __init__(self, directory=False, *args, **kwargs):
        super(FileBrowserBoxLayout, self).__init__(*args, **kwargs)
        self.directory = directory
        self.line_edit = FileLineEdit(directory=self.directory)
        self.browser_button = BrowserButton(update_widget=self.line_edit)

        self.addWidget(self.line_edit)
        self.addWidget(self.browser_button)

class FolderBrowserBoxLayout(QtWidgets.QHBoxLayout):
    """Custom Layout for File and Folder Browsers"""

    def __init__(self, directory=False, *args, **kwargs):
        super(FolderBrowserBoxLayout, self).__init__(*args, **kwargs)
        self.directory = directory
        self.line_edit = FileLineEdit(directory=self.directory)
        self.browser_button = BrowserButton(update_widget=self.line_edit,  mode="directory")

        self.addWidget(self.line_edit)
        self.addWidget(self.browser_button)
