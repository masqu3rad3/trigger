import os
from trigger.ui.Qt import QtWidgets, QtCore
from trigger.ui import feedback
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

class ListBoxLayout(QtWidgets.QVBoxLayout):
    """Easy to manage listwidget with preset buttons"""
    def __init__(self, buttonsPosition="right",
                 alignment=None,
                 buttonAdd=False,
                 buttonNew=True,
                 buttonRename=True,
                 buttonGet=True,
                 buttonUp=False,
                 buttonDown=False,
                 buttonRemove=True,
                 buttonClear=True,
                 multiSelect=True,
                 *args, **kwargs):
        super(ListBoxLayout, self).__init__(*args, **kwargs)
        self.buttonsPosition = buttonsPosition
        self.alignment = alignment
        self.isButtonAdd = buttonAdd
        self.isButtonNew = buttonNew
        self.isButtonRename = buttonRename
        self.isButtonGet = buttonGet
        self.isButtonUp = buttonUp
        self.isButtonDown = buttonDown
        self.isButtonRemove = buttonRemove
        self.isButtonClear = buttonClear
        self.isMultiSelect = multiSelect
        self.init_widget()
        self.init_properties()
        self.build()

    def init_widget(self):
        self.viewWidget = QtWidgets.QListWidget()

    def init_properties(self):
        pass

    def build(self):
        if self.buttonsPosition == "right" or self.buttonsPosition == "left":
            self.masterLayout = QtWidgets.QHBoxLayout()
            self.buttonsStretchLay = QtWidgets.QVBoxLayout()
            self.buttonslayout = QtWidgets.QVBoxLayout()
        elif self.buttonsPosition == "top" or self.buttonsPosition == "bottom":
            self.masterLayout = QtWidgets.QVBoxLayout()
            self.buttonsStretchLay = QtWidgets.QHBoxLayout()
            self.buttonslayout = QtWidgets.QHBoxLayout()
        else:
            raise Exception ("invalid value for buttonsPosition. Valid values are 'top', 'bottom', 'left', 'right'")
        self.addLayout(self.masterLayout)
        if self.alignment == "start":
            spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
            self.buttonsStretchLay.addLayout(self.buttonslayout)
            self.buttonsStretchLay.addItem(spacer)
        elif self.alignment == "end":
            spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
            self.buttonsStretchLay.addItem(spacer)
            self.buttonsStretchLay.addLayout(self.buttonslayout)
        else:
            self.buttonsStretchLay.addLayout(self.buttonslayout)

        # self.listwidget = QtWidgets.QListWidget()

        if self.isMultiSelect:
            self.viewWidget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        if self.isButtonAdd:
            self.buttonAdd = QtWidgets.QPushButton(text="Add")
            self.buttonslayout.addWidget(self.buttonAdd)
        if self.isButtonNew:
            self.buttonNew = QtWidgets.QPushButton(text="New")
            self.buttonslayout.addWidget(self.buttonNew)
            self.buttonNew.clicked.connect(self._on_new)
        if self.isButtonRename:
            self.buttonRename = QtWidgets.QPushButton(text="Rename")
            self.buttonslayout.addWidget(self.buttonRename)
            self.buttonRename.clicked.connect(self._on_rename)
        if self.isButtonGet:
            self.buttonGet = QtWidgets.QPushButton(text="Get")
            self.buttonslayout.addWidget(self.buttonGet)
        if self.isButtonUp:
            self.buttonUp = QtWidgets.QPushButton(text="Move Up")
            self.buttonslayout.addWidget(self.buttonUp)
            self.buttonUp.clicked.connect(self._on_move_up)
        if self.isButtonDown:
            self.buttonDown = QtWidgets.QPushButton(text="Move Down")
            self.buttonslayout.addWidget(self.buttonDown)
            self.buttonDown.clicked.connect(self._on_move_down)
        if self.isButtonRemove:
            self.buttonRemove = QtWidgets.QPushButton(text="Remove")
            self.buttonslayout.addWidget(self.buttonRemove)
            self.buttonRemove.clicked.connect(self._on_remove)
        if self.isButtonClear:
            self.buttonClear = QtWidgets.QPushButton(text="Clear")
            self.buttonslayout.addWidget(self.buttonClear)
            self.buttonClear.clicked.connect(self._on_clear)

        if self.buttonsPosition == "top" or self.buttonsPosition == "left":
            self.masterLayout.addLayout(self.buttonsStretchLay)
            self.masterLayout.addWidget(self.viewWidget)
        else:
            self.masterLayout.addWidget(self.viewWidget)
            self.masterLayout.addLayout(self.buttonsStretchLay)

    def _on_clear(self):
        self.viewWidget.clear()

    def _on_new(self):
        w = QtWidgets.QWidget()
        newitem, ok = QtWidgets.QInputDialog.getText(w, "New Item", "Enter new item name:")
        if ok:
            self.viewWidget.addItem(str(newitem))

    def _on_rename(self):
        all_selected_rows = [self.viewWidget.row(item) for item in self.viewWidget.selectedItems()]
        if not all_selected_rows:
            return
        w = QtWidgets.QWidget()
        newname, ok = QtWidgets.QInputDialog.getText(w, "Rename Item", "Enter new name:")
        if ok:
            for row in all_selected_rows:
                self.viewWidget.item(row).setText(newname)

    def _on_move_up(self):
        row = self.viewWidget.currentRow()
        if row == -1:
            return
        if not row == 0:
            current_list = self.listItemNames()
            current_list.insert(row-1, current_list.pop(row))
            self.viewWidget.clear()
            self.viewWidget.addItems(current_list)
            self.viewWidget.setCurrentRow(row - 1)

    def _on_move_down(self):
        row = self.viewWidget.currentRow()
        if row == -1:
            return
        current_list = self.listItemNames()
        if not row == len(current_list)-1:
            current_list.insert(row+1, current_list.pop(row))
            self.viewWidget.clear()
            self.viewWidget.addItems(current_list)
            self.viewWidget.setCurrentRow(row + 1)
        else:
            self.viewWidget.setCurrentRow(row)

    def _on_remove(self):
        all_selected_rows = [self.viewWidget.row(item) for item in self.viewWidget.selectedItems()]

        for row in reversed(all_selected_rows):
            self.viewWidget.takeItem(row)

    def addNewButton(self, buttonwidget):
        self.buttonslayout.addWidget(buttonwidget)

    def removeButton(self, buttonwidget):
        buttonwidget.setEnabled(False)
        buttonwidget.deleteLater()

    def listItems(self):
        return [self.viewWidget.item(index) for index in range(self.viewWidget.count())]

    def listItemNames(self):
        return [self.viewWidget.item(index).text() for index in range(self.viewWidget.count())]

class TreeBoxLayout(ListBoxLayout):
    def __init__(self, *args, **kwargs):
        super(TreeBoxLayout, self).__init__(*args, **kwargs)
        self.key_name = "Name"
        self.value_name = "Value List"
        self.value_database = []

    def init_widget(self):
        # override the widget with tree widget
        self.viewWidget = QtWidgets.QTreeWidget()

    def _on_new(self):
        dialog = QtWidgets.QDialog()
        dialog.setModal(True)
        master_layout = QtWidgets.QVBoxLayout()
        dialog.setLayout(master_layout)
        form_layout = QtWidgets.QFormLayout()
        master_layout.addLayout(form_layout)

        key_lbl = QtWidgets.QLabel(text=self.key_name)
        key_le = QtWidgets.QLineEdit()
        form_layout.addRow(key_lbl, key_le)

        value_lbl = QtWidgets.QLabel(text=self.value_name)
        value_listbox = ListBoxLayout(buttonGet=False)
        # if not self.override_listbox:
        #     value_listbox = ListBoxLayout(buttonGet=False)
        # else:
        #     value_listbox = self.override_listbox
        form_layout.addRow(value_lbl, value_listbox)

        button_box = QtWidgets.QDialogButtonBox(dialog)
        button_box.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        master_layout.addWidget(button_box)

        # Signals
        button_box.accepted.connect(lambda x=0: self._add_tree_item(key_le.text(), value_listbox.listItemNames()))
        button_box.accepted.connect(dialog.close)
        button_box.rejected.connect(dialog.close)

        dialog.exec_()

    def _add_tree_item(self, key, value_list):
        topLevel = QtWidgets.QTreeWidgetItem([key])
        self.viewWidget.addTopLevelItem(topLevel)
        children = [QtWidgets.QTreeWidgetItem([value]) for value in value_list]
        topLevel.addChildren(children)

    def _on_rename(self):
        all_selected_items = self.viewWidget.selectedItems()
        if not all_selected_items:
            return
        w = QtWidgets.QWidget()
        newname, ok = QtWidgets.QInputDialog.getText(w, "Rename Item", "Enter new name:")
        if ok:
            for x in self.viewWidget.selectedItems():
                x.setText(0, newname)

    @staticmethod
    def get_children(root):
        return [root.child(i) for i in range(root.childCount())]

    def get_dictionary(self):
        return_dict = {}
        top_items = self.get_children(self.viewWidget.invisibleRootItem())
        for item in top_items:
            return_dict[item.text(0)] = [data.text(0) for data in self.get_children(item)]

class TableBoxLayout(ListBoxLayout):
    def __init__(self, labels=["Driver", "Start", "End", "Driven", "Start", "End"], *args, **kwargs):
        self.labels = labels

        super(TableBoxLayout, self).__init__(*args, **kwargs)


    def init_widget(self):
        self.viewWidget = QtWidgets.QTableWidget()

    def init_properties(self):
        self.viewWidget.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.viewWidget.setAutoFillBackground(True)
        self.viewWidget.setRowCount(0)
        self.viewWidget.setColumnCount(6)
        self.viewWidget.setHorizontalHeaderLabels(self.labels)

        self.viewWidget.horizontalHeader().setMinimumSectionSize(60)
        self.viewWidget.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.viewWidget.horizontalHeader().resizeSection(1, 50)
        self.viewWidget.horizontalHeader().resizeSection(2, 50)
        self.viewWidget.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)
        self.viewWidget.horizontalHeader().resizeSection(4, 50)
        self.viewWidget.horizontalHeader().resizeSection(5, 50)

        self.viewWidget.verticalHeader().setVisible(False)

    def _on_new(self):
        next_row = self.viewWidget.rowCount()
        self.viewWidget.insertRow(next_row)

    def _on_clear(self):
        row_count = self.viewWidget.rowCount()
        if row_count:
            feedback_h = feedback.Feedback()
            q = feedback_h.pop_question(title="Are you sure?", text="Are you sure you want to clear all items?\n There is no undo for this action.", buttons=["yes", "cancel"])
            if q == "yes":
                for x in reversed(range(self.viewWidget.rowCount())):
                    self.viewWidget.removeRow(x)
        else:
            return

    def _on_remove(self):
        all_selected_rows = [idx.row() for idx in self.viewWidget.selectedIndexes()]
        for row in reversed(all_selected_rows):
            self.viewWidget.removeRow(row)

    def _on_move_down(self):
        row = self.viewWidget.currentRow()
        column = self.viewWidget.currentColumn();
        if row < self.viewWidget.rowCount()-1:
            self.viewWidget.insertRow(row+2)
            for i in range(self.viewWidget.columnCount()):
               self.viewWidget.setItem(row+2,i,self.viewWidget.takeItem(row,i))
               self.viewWidget.setCurrentCell(row+2,column)
            self.viewWidget.removeRow(row)

    def _on_move_up(self):
        row = self.viewWidget.currentRow()
        column = self.viewWidget.currentColumn();
        if row > 0:
            self.viewWidget.insertRow(row-1)
            for i in range(self.viewWidget.columnCount()):
               self.viewWidget.setItem(row-1,i,self.viewWidget.takeItem(row+1,i))
               self.viewWidget.setCurrentCell(row-1,column)
            self.viewWidget.removeRow(row+1)

    def set_data(self, data_list):
        self._on_clear()
        for row, mapping_data in enumerate(data_list):
            self.viewWidget.insertRow(row)
            for column, cell_data in enumerate(mapping_data):
                self.viewWidget.setItem(row, column, QtWidgets.QTableWidgetItem(str(cell_data)))

