"""creates driven connections between given attributes. It uses remap or direct connect according to the values"""

from trigger.library import attribute
from trigger.ui.Qt import QtWidgets, QtGui # for progressbar


ACTION_DATA = {
    "mapping_data": []
}

"""Example Mapping Data:
[
    ["mouthArea_cont.L_upperlipRaiser", [0, 100], "morph_hook.LupperlipRaiser", [0, 1]],
    ["mouthArea_cont.R_upperlipRaiser", [0, 100], "morph_hook.RupperlipRaiser", [0, 1]],
    ["L_cheekArea_cont.cheekRaiser", [0, 100], "morph_hook.LcheekRaiser", [0, 1]],
    ["R_cheekArea_cont.cheekRaiser", [0, 100], "morph_hook.RcheekRaiser", [0, 1]],
]
"""

class Driver(object):
    def __init__(self, *args, **kwargs):
        super(Driver, self).__init__(*args, **kwargs)
        self.mappingData = []

    def feed(self, action_data, *args, **kwargs):
        self.mappingData = action_data.get("mapping_data")

    def action(self):
        for con in self.mappingData:
            attribute.drive_attrs(con[0], con[2], driver_range=con[1], driven_range=con[3])

    def save_action(self):
        pass

    def ui(self, ctrl, layout, handler, *args, **kwargs):
        pass