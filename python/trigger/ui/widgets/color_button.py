from trigger.ui.Qt import QtWidgets, QtCore, QtGui


class ColorButton(QtWidgets.QPushButton):
    def __init__(self, *args, **kwargs):
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
        super(ColorButton, self).__init__(*args, **kwargs)
        self.default_stylesheet = self.styleSheet()
        self._color = QtGui.QColor()
        # self._updateWidget = update_widget
        # if text:
        #     self.setText(text)
        # self._validModes = ["openFile", "saveFile", "directory"]
        # if mode in self._validModes:
        #     self._mode = mode
        # else:
        #     raise Exception("Mode is not valid. Valid modes are %s" % (", ".join(self._validModes)))
        # self._filterExtensions = self._listToFilter(filterExtensions) if filterExtensions else ""
        # self._title = title if title else ""
        # self._selectedPath = ""
        # self._overwriteCheck = overwrite_check
        # self._cancelFlag = False

    # def isCancelled(self):
    #     return self._cancelFlag
    #
    # def setUpdateWidget(self, widget):
    #     self._updateWidget = widget
    #
    # def updateWidget(self):
    #     return self._updateWidget
    #
    # def setMode(self, mode):
    #     if mode not in self._validModes:
    #         raise Exception("Mode is not valid. Valid modes are %s" % (", ".join(self._validModes)))
    #     self._mode = mode
    #
    # def mode(self):
    #     return self._mode
    #
    # def setFilterExtensions(self, extensionlist):
    #     self._filterExtensions = self._listToFilter(extensionlist)
    #
    # def selectedPath(self):
    #     return self._selectedPath
    #
    # def setSelectedPath(self, new_path):
    #     self._selectedPath = new_path
    #
    # def setTitle(self, title):
    #     self._title = title
    #
    # def title(self):
    #     return self._title
    #
    # def _listToFilter(self, filter_list):
    #     return ";;".join(filter_list)

    def setDisabled(self, state):
        super(ColorButton, self).setDisabled(state)
        if state:
            print(self.default_stylesheet)
            self.setStyleSheet(self.default_stylesheet)
        else:
            self._update_button_color()

    def setEnabled(self, state):
        super(ColorButton, self).setEnabled(state)
        if not state:
            self.setStyleSheet(self.default_stylesheet)
        else:
            self._update_button_color()



    def setColor(self, rgb=None, normalized_rgb=None, hex=None, QColor=None):
        if QColor:
            self._color = QColor
            self._update_button_color()
            return
        if rgb:
            pass
        elif normalized_rgb:
            rgb = tuple(int(x*255) for x in normalized_rgb)
        elif hex:
            _hex = hex.lstrip("#")
            rgb = tuple(int(_hex[i:i+2], 16) for i in (0, 2, 4))
        print("-"*30)
        print("-"*30)
        print("-"*30)
        print(rgb)
        print("-"*30)
        print("-"*30)
        print("-"*30)
        self._color.setRgb(*rgb)
        self._update_button_color()

    def getRgb(self):
        return self._color.getRgb()

    def getNormalized(self):
        _rgb = self._color.getRgb()
        return tuple(x/255 for x in _rgb)

    def _update_button_color(self):
        self.setStyleSheet("background-color:rgb{0}".format(self._color.getRgb()))

    def colorpickEvent(self):
        _color = QtWidgets.QColorDialog.getColor()
        if _color.isValid():
            self.setColor(QColor=_color)
            # self._update_button_color()

    def mouseReleaseEvent(self, *args, **kwargs):
        self.colorpickEvent()
        super(ColorButton, self).mouseReleaseEvent(*args, **kwargs)

    # @staticmethod
    # def _f2b(float_index_color):
    #     byte_list = [int(f*255.999) for f in float_index_color]
    #     return tuple(byte_list)