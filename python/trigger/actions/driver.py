"""creates driven connections between given attributes. It uses remap or direct connect according to the values"""

from trigger.library import attribute
from trigger.ui import custom_widgets
from trigger.ui.Qt import QtWidgets, QtGui # for progressbar
from trigger.core import logger

log = logger.Logger()


ACTION_DATA = {
    "mapping_data": []
}

"""Example Mapping Data:
[
    ["mouthArea_cont.L_upperlipRaiser", "0", "100", "morph_hook.LupperlipRaiser", "0", "1"],
    ["mouthArea_cont.R_upperlipRaiser", "0", "100", "morph_hook.RupperlipRaiser", "0", "1"],
    ["L_cheekArea_cont.cheekRaiser", "0", "100", "morph_hook.LcheekRaiser", "0", "1"],
]
"""

class Driver(object):
    def __init__(self, *args, **kwargs):
        super(Driver, self).__init__(*args, **kwargs)
        self.mappingData = []

    def feed(self, action_data, *args, **kwargs):
        self.mappingData = self._validate(action_data.get("mapping_data"))

    def action(self):
        for data in self.mappingData:
            attribute.drive_attrs(data[0], data[3], driver_range=[data[1], data[2]], driven_range=[data[4], data[5]])

    def save_action(self):
        pass

    def ui(self, ctrl, layout, handler, *args, **kwargs):
        mappings_lbl = QtWidgets.QLabel(text="Mappings:")
        mappings_tablebox = custom_widgets.TableBoxLayout(buttonsPosition="top",
                                                          buttonDown=True, buttonUp=True,
                                                          buttonAdd=False, buttonRename=False, buttonGet=False)
        mappings_tablebox.viewWidget.setMinimumHeight(400)
        layout.addRow(mappings_lbl, mappings_tablebox)

        ctrl.connect(mappings_tablebox, "mapping_data", list)
        ctrl.update_ui()

        ## SIGNALS ##
        mappings_tablebox.viewWidget.cellChanged.connect(lambda x=0: ctrl.update_model())

    @staticmethod
    def _validate(data_matrix):
        validated_data = []
        for row in data_matrix:
            try:
                validated_data.append([str(row[0]), float(row[1]), float(row[2]), str(row[3]), float(row[4]), float(row[5])])
            except ValueError:
                log.throw_error("Range values must be digits => %s" %row)
        return validated_data