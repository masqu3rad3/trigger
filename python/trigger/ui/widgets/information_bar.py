"""Custom widget to display information to the user."""

from trigger.ui.Qt import QtWidgets, QtCore


class InformationBar(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(InformationBar, self).__init__(parent=parent)

        self._border_color = '#FF8D1C'
        self._text_color = "#FF8D1C"
        self._background_color = "#3c3c3c"

        self._label = QtWidgets.QLabel()
        self._label.setWordWrap(True)

        # center the text
        self._label.setAlignment(QtCore.Qt.AlignCenter)

        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label)
        self.setLayout(layout)


        # make the widget bordered and slightly different color
        # self.setStyleSheet(
        #     "QWidget { border: 2px solid #FF8D1C; }"
        # )
        self._update_color_style()

    def set_text(self, text):
        self._label.setText(text)

    def set_text_color(self, color):
        self._text_color = color
        self._label.setStyleSheet(f"color: {color};")

    def set_border_color(self, color):
        self._border_color = color
        self._update_color_style()


    def set_background_color(self, color):
        self._background_color = color
        self._update_color_style()

    def _update_color_style(self):
        color_style = f"""
        QWidget
        {{
        border: 2px solid {self._border_color};
        background-color: {self._background_color};
        }}
        """

        self.setStyleSheet(color_style)
        self.style().polish(self)

    def clear(self):
        self._label.clear()


# test the widget
if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = InformationBar()
    window.set_text("This is a test")
    window.set_text_color("red")
    window.set_text_color("green")
    window.set_border_color("red")
    window.set_background_color("blue")
    window.show()
    sys.exit(app.exec_())