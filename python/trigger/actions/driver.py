"""creates driven connections between given attributes. It uses remap or direct connect according to the values"""

import fnmatch
from maya import cmds
from trigger.library import attribute
from trigger.core import filelog
from trigger.core.action import ActionCore

from trigger.ui import custom_widgets
from trigger.ui.Qt import QtWidgets, QtGui  # for progressbar

log = filelog.Filelog(logname=__name__, filename="trigger_log")


ACTION_DATA = {"mapping_data": []}

"""Example Mapping Data:
[
    ["mouthArea_cont.L_upperlipRaiser", "0", "100", "morph_hook.LupperlipRaiser", "0", "1"],
    ["mouthArea_cont.R_upperlipRaiser", "0", "100", "morph_hook.RupperlipRaiser", "0", "1"],
    ["L_cheekArea_cont.cheekRaiser", "0", "100", "morph_hook.LcheekRaiser", "0", "1"],
]
"""


class Driver(ActionCore):
    action_data = ACTION_DATA

    def __init__(self, *args, **kwargs):
        super(Driver, self).__init__(*args, **kwargs)
        self.mappingData = []

    def feed(self, action_data, *args, **kwargs):
        self.mappingData = self._validate(action_data.get("mapping_data"))

    def action(self):
        for data in self.mappingData:
            # ls the driven attribute to make sure it exists

            splits = data[3].split(".")
            node = splits[0]
            wild_attr = ".".join(splits[1:])
            nodes_list = cmds.ls(node)
            found_attrs = []
            for n in nodes_list:
                # get all attributes of the node
                all_attrs = cmds.listAttr(n)
                wild_attrs = fnmatch.filter(all_attrs, wild_attr)
                found_attrs.extend(["{0}.{1}".format(n, w) for w in wild_attrs])
            if not found_attrs:
                log.error("No attributes found for %s" % data[3])
                return
            attribute.drive_attrs(
                data[0],
                found_attrs,
                driver_range=[data[1], data[2]],
                driven_range=[data[4], data[5]],
                optimize=False,
            )

    def save_action(self):
        pass

    def ui(self, ctrl, layout, handler, *args, **kwargs):
        mappings_lbl = QtWidgets.QLabel(text="Mappings:")
        mappings_tablebox = custom_widgets.TableBoxLayout(
            buttonsPosition="top",
            buttonDown=True,
            buttonUp=True,
            buttonAdd=False,
            buttonRename=False,
            buttonGet=False,
        )
        mappings_tablebox.viewWidget.setMinimumHeight(400)
        layout.addRow(mappings_lbl, mappings_tablebox)

        ctrl.connect(mappings_tablebox, "mapping_data", list)
        ctrl.update_ui()

        ## SIGNALS ##
        mappings_tablebox.viewWidget.cellChanged.connect(
            lambda x=0: ctrl.update_model()
        )
        mappings_tablebox.buttonRemove.clicked.connect(lambda x=0: ctrl.update_model())
        mappings_tablebox.buttonUp.clicked.connect(lambda x=0: ctrl.update_model())
        mappings_tablebox.buttonDown.clicked.connect(lambda x=0: ctrl.update_model())
        mappings_tablebox.buttonClear.clicked.connect(lambda x=0: ctrl.update_model())

    @staticmethod
    def _validate(data_matrix):
        validated_data = []
        for row in data_matrix:
            try:
                validated_data.append(
                    [
                        str(row[0]),
                        float(row[1]),
                        float(row[2]),
                        str(row[3]),
                        float(row[4]),
                        float(row[5]),
                    ]
                )
            except ValueError:
                log.error("Range values must be digits => %s" % row)
        return validated_data
