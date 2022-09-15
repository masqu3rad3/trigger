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
