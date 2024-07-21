"""
DISCLAIMER
Credit to Jung Gyu Yoon for the original code.

https://github.com/yjg30737/pyqt-loading-progressbar/blob/main/LICENSE
MIT License

Copyright (c) 2022 Jung Gyu Yoon

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from trigger.ui.Qt import QtWidgets, QtCore

class LoadingProgressBar(QtWidgets.QProgressBar):
    def __init__(self):
        super().__init__()
        self.__initUi()

    def __initUi(self):
        self.setValue(0)
        self.setTextVisible(False)
        self.__animation = QtCore.QPropertyAnimation(self, b'loading')
        self.__animation.setStartValue(self.minimum())
        self.__animation.setEndValue(self.maximum())
        self.__animation.valueChanged.connect(self.__loading)
        self.__animation.setDuration(1000)
        self.__animation.setEasingCurve(QtCore.QEasingCurve.InOutQuad)
    def start(self):
        self.__animation.start()

    def stop(self):
        self.__animation.stop()
        self.setValue(0)

    def __loading(self, v):
        self.setValue(v)
        if self.__animation.currentValue() == self.__animation.endValue():
            self.__animation.setDirection(QtCore.QAbstractAnimation.Backward)
            self.setInvertedAppearance(True)
            self.__animation.start()
        elif self.__animation.currentValue() == self.__animation.startValue():
            self.__animation.setDirection(QtCore.QAbstractAnimation.Forward)
            self.setInvertedAppearance(False)
            self.__animation.start()

    def setAnimationType(self, type: str):
        if type == 'fade':
            self.setStyleSheet('''
                QProgressBar::chunk {
                    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 transparent, stop: 0.5 #FF8D1C, stop: 0.6 #FF8D1C, stop:1 transparent);
                }
            ''')
            self.__animation.setEasingCurve(QtCore.QEasingCurve.Linear)
            self.__animation.setDuration(500)
        elif type == 'dynamic':
            self.setStyleSheet('')

            self.__animation.setEasingCurve(QtCore.QEasingCurve.InOutQuad)
            self.__animation.setDuration(1000)
