"""creates driven connections between given attributes. It uses remap or direct connect according to the values"""

import fnmatch
from maya import cmds
from trigger.library import attribute
from trigger.library import selection

from trigger.ui import feedback

from trigger.core import filelog
from trigger.core.action import ActionCore

from trigger.ui import custom_widgets
from trigger.ui.Qt import QtWidgets, QtGui  # for progressbar

LOG = filelog.Filelog(logname=__name__, filename="trigger_log")


ACTION_DATA = {"mapping_data": [], "proxy_controller": ""}

"""Example Mapping Data:
[
    ["mouthArea_cont.L_upperlipRaiser", "0", "100", "morph_hook.LupperlipRaiser", "0", "1", ""],
    ["mouthArea_cont.R_upperlipRaiser", "0", "100", "morph_hook.RupperlipRaiser", "0", "1", ""],
    ["L_cheekArea_cont.cheekRaiser", "0", "100", "morph_hook.LcheekRaiser", "0", "1", "proxyCheekRaiser"],
]
"""


class Driver(ActionCore):
    action_data = ACTION_DATA

    def __init__(self, **kwargs):
        super(Driver, self).__init__(kwargs)
        self.mapping_data = []
        self.proxy_controller = None

    def feed(self, action_data, *args, **kwargs):
        self.mapping_data = self._validate(action_data.get("mapping_data"))
        self.proxy_controller = action_data.get("proxy_controller")

    def action(self):
        for data in self.mapping_data:
            # Check if this is a separator.
            if len(data[0].split(".")) == 1:
                if self.proxy_controller:
                    attribute.separator(self.proxy_controller, data[0])
                else:
                    LOG.warning("Proxy controller not defined. Separator %s will not be created.", data[0])
                continue

            splits = data[3].split(".")
            node = splits[0]
            wild_attr = ".".join(splits[1:])
            # ls the driven attribute to make sure it exists
            nodes_list = cmds.ls(node)
            found_attrs = []
            for n in nodes_list:
                # get all attributes of the node
                all_attrs = cmds.listAttr(n)
                wild_attrs = fnmatch.filter(all_attrs, wild_attr)
                found_attrs.extend(["{0}.{1}".format(n, w) for w in wild_attrs])
            if not found_attrs:
                LOG.error("No attributes found for %s" % data[3])
                return

            print(data)
            if data[6] and self.proxy_controller:
                proxy_attr = "{0}.{1}".format(self.proxy_controller, data[6])
            else:
                proxy_attr = None

            attribute.drive_attrs(
                data[0],
                found_attrs,
                driver_range=[data[1], data[2]],
                driven_range=[data[4], data[5]],
                optimize=False,
                proxy_driver_attr=proxy_attr
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

        def get_selected_controller(widget):
            sel, msg = selection.validate(
                minimum=1, maximum=1, meshes_only=False, transforms=True
            )
            if sel:
                widget.setText(sel[0])
                ctrl.update_model()
                return
            else:
                feedback.Feedback().pop_info(
                    title="Selection Error", text=msg, critical=True
                )
                return

        controller_lbl = QtWidgets.QLabel(text="Controller For Proxies:")
        controller_le_box = custom_widgets.LineEditBoxLayout(buttonsPosition="right")
        controller_le_box.viewWidget.setPlaceholderText("If defined, proxy attributes will be created on controller.")
        controller_le_box.buttonGet.setText("<")
        controller_le_box.buttonGet.setMaximumWidth(30)
        controller_le_box.buttonGet.setToolTip("Gets the selected object as controller")
        layout.addRow(controller_lbl, controller_le_box)


        ctrl.connect(mappings_tablebox, "mapping_data", list)
        ctrl.connect(controller_le_box.viewWidget, "proxy_controller", str)
        ctrl.update_ui()



        ## SIGNALS ##
        mappings_tablebox.viewWidget.cellChanged.connect(
            lambda x=0: ctrl.update_model()
        )
        mappings_tablebox.buttonRemove.clicked.connect(lambda x=0: ctrl.update_model())
        mappings_tablebox.buttonUp.clicked.connect(lambda x=0: ctrl.update_model())
        mappings_tablebox.buttonDown.clicked.connect(lambda x=0: ctrl.update_model())
        mappings_tablebox.buttonClear.clicked.connect(lambda x=0: ctrl.update_model())

        controller_le_box.buttonGet.pressed.connect(
            lambda: get_selected_controller(controller_le_box.viewWidget)
        )

        controller_le_box.viewWidget.textChanged.connect(lambda: ctrl.update_model())

    @staticmethod
    def _validate(data_matrix):
        validated_data = []
        for row in data_matrix:
            try:
                row_data = [
                        str(row[0]),
                        float(row[1]),
                        float(row[2]),
                        str(row[3]),
                        float(row[4]),
                        float(row[5]),
                    ]
                # for backwards compatibility
                if len(row) == 7:
                    row_data.append(str(row[6]))
                else:
                    row_data.append("")
                validated_data.append(row_data)
            except ValueError:
                LOG.error("Range values must be digits => %s" % row)
        return validated_data
