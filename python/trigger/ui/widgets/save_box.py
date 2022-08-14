
from trigger.ui.Qt import QtWidgets, QtCore
from trigger.ui.widgets.browser_button import BrowserButton
from trigger.library import naming
from trigger.ui import feedback

class SaveBoxLayout(QtWidgets.QVBoxLayout):
    saved = QtCore.Signal(str)

    def __init__(self, alignment=None, update_widget=None, filter_extensions=None, overwrite_check=False, control_model=None, *args, **kwargs):
        super(SaveBoxLayout, self).__init__(*args, **kwargs)
        self.saveButton = None
        self.saveAsButton = None
        self.incrementButton = None
        self.storeButton = None
        self.classic_mode_checkbox = None
        self.alignment = alignment or "horizontal"
        self.updateWidget = update_widget
        self.filterExtensions = filter_extensions
        self.overwriteCheck = overwrite_check
        self.controlModel = control_model
        self.feedback = feedback.Feedback()


        self.build()

    def build(self):
        if self.alignment == "horizontal":
            self.masterLayout = QtWidgets.QHBoxLayout()
        elif self.alignment == "vertical":
            self.masterLayout = QtWidgets.QVBoxLayout()
        else:
            raise Exception("alignment argument is not valid. Valid arguments are 'horizontal' and 'vertical'")

        self.addLayout(self.masterLayout)
        self.classic_mode_checkbox = QtWidgets.QCheckBox(text="Use classic save options")
        self.classic_mode_checkbox.setChecked(False)
        self.saveButton = QtWidgets.QPushButton(text="Save")
        self.saveAsButton = BrowserButton(text="Save As", mode="saveFile", update_widget=self.updateWidget, filterExtensions=self.filterExtensions, overwrite_check=self.overwriteCheck)
        self.storeButton = QtWidgets.QPushButton(text="Store")
        self.storeButton.setToolTip("Saves the file in the correct folder under the trigger file")
        self.incrementButton = QtWidgets.QPushButton(text="Increment")
        self.masterLayout.addWidget(self.saveButton)
        self.masterLayout.addWidget(self.storeButton)
        self.masterLayout.addWidget(self.saveAsButton)
        self.masterLayout.addWidget(self.incrementButton)
        self.masterLayout.addWidget(self.classic_mode_checkbox)

        # SIGNALS
        self.saveButton.clicked.connect(self.save)
        self.saveAsButton.clicked.connect(self.saveAs)
        self.incrementButton.clicked.connect(self.increment)

    def save(self):
        if self.controlModel:
            self.controlModel.update_model()
        if self.updateWidget:
            file_path = str(self.updateWidget.text())
            if not file_path:
                self.saveAsButton.browserEvent()
                return
            self.controlModel.update_model()
            self.saveEvent(file_path)

    def saveAs(self):
        if self.controlModel:
            self.controlModel.update_model()
        if self.saveAsButton.isCancelled():
            return
        if self.updateWidget:
            file_path = str(self.updateWidget.text())
            if not file_path:
                return
            self.controlModel.update_model()
            self.saveEvent(file_path)
        pass

    def increment(self):

        if self.controlModel:
            self.controlModel.update_model()
        if self.updateWidget:
            file_path = str(self.updateWidget.text())
            if not file_path:
                self.feedback.pop_info(title="Cannot Proceed", text="No path defined to increment", critical=True)
                return
            incremented_file_path = naming.increment(file_path)
            self.saveEvent(incremented_file_path)
            self.updateWidget.setText(incremented_file_path)

    def saveEvent(self, file_path):
        self.saved.emit(file_path)