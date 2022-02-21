"""Controller module for Model/View"""
from trigger.core import filelog
from trigger.ui.Qt import QtWidgets

log = filelog.Filelog(logname=__name__, filename="trigger_log")

class Controller(object):

    def __init__(self):
        super(Controller, self).__init__()
        self.model = None
        self.action_name = None
        self.connections = []


    def connect(self, widget, property, property_type):
        connection_item = {
            "action_name": self.action_name,
            "property": property,
            "widget": widget,
            "type": property_type
        }
        self.connections.append(connection_item)
        
    def _widget_val(self, widget, property_type, value=None, get=None, set=None):
        """Returns the required widget method if the widget is supported"""
        widget_class = widget.__class__.__name__
        if set and value == None:
            log.error("Set mode needs a value")
            raise
        if set == None and get == None:
            log.error("Either set or get needs to be flagged")
            raise
        if set and get:
            log.error("Both set and get cannot be defined")
            raise
        if widget_class == "QLineEdit" or widget_class == "FileLineEdit":
            if get:
                if property_type == list:
                    get_value = self.text_to_list(widget.text())
                else:
                    get_value = property_type(widget.text())
                return get_value
            else:
                set_value = self.list_to_text(value) if property_type == list else property_type(value)
                widget.setText(set_value)
        elif widget_class == "QCheckBox":
            if get:
                return property_type(widget.isChecked())
            else:
                widget.setChecked(bool(value))
        elif widget_class == "QComboBox":
            if get:
                return property_type(widget.currentIndex())
            else:
                widget.setCurrentIndex(int(value))
        elif widget_class == "QSpinBox":
            if get:
                return property_type(widget.value())
            else:
                widget.setValue(int(value))
        elif widget_class == "QDoubleSpinBox":
            if get:
                return property_type(widget.value())
            else:
                widget.setValue(float(value))
        elif widget_class == "QListWidget":
            if get:
                items = [widget.item(index).text() for index in range(widget.count())]
                return property_type(items)
            else:
                widget.addItems(list(value))
        elif widget_class == "QTreeWidget":
            if get:
                return_dict = {}
                root = widget.invisibleRootItem()
                top_items = [root.child(i) for i in range(root.childCount())]
                for item in top_items:
                    children = [item.child(i) for i in range(item.childCount())]
                    return_dict[item.text(0)] = [data.text(0) for data in children]
                return return_dict
            else:
                for key, value_list in value.items():
                    topLevel = QtWidgets.QTreeWidgetItem([key])
                    widget.addTopLevelItem(topLevel)
                    children = [QtWidgets.QTreeWidgetItem([value]) for value in value_list]
                    topLevel.addChildren(children)
        elif widget_class == "TableBoxLayout":
            if get:
                return widget.get_data()
            else:
                widget.set_data(list(value))

        elif widget_class == "ColorButton":
            if get:
                return property_type(widget.getNormalized())
            else:
                widget.setColor(normalized_rgb=tuple(value))

        else:
            log.error("UNSUPPORTED WIDGET CLASS ==> %s" % widget_class)
            raise


    def update_model(self):
        for item in self.connections:
            ui_property_value = self._widget_val(item["widget"], item["type"], get=True)
            self.model.edit_action(item["action_name"], item["property"], ui_property_value)

    def update_ui(self):
        for item in self.connections:
            model_property_value = self.model.query_action(self.action_name, item["property"])
            self._widget_val(item["widget"], item["type"], model_property_value, set=True)

    @staticmethod
    def list_to_text(list_item):
        return "; ".join(list_item)

    @staticmethod
    def text_to_list(text_item):
        if text_item:
            return str(text_item).split("; ")
        else:
            return []



