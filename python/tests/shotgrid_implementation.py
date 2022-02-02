from importlib import reload

from trigger.version_control import rbl_shotgrid

reload(rbl_shotgrid)

shot_trigger = rbl_shotgrid.ShotTrigger()
a = shot_trigger.task




shot_trigger.request_new_session_path("hedehot")

shot_trigger.request_new_version_path()

shot_trigger.get_sessions("charCube", "RIG", "AvA")

shot_trigger.sg

tk = shot_trigger._sg_template.tk  # get tk instance from sg_template, or elsewhere if you already have an instance
temp = tk.templates.get("asset_trigger_sessionfile")
fields = {"Asset": "charSoldier", "Step": "RIG",
          "variant_name": "AvA"}  # assemble all of the fields you know
paths = tk.paths_from_template(temp, fields, ["version"],
                               skip_missing_optional_keys=True)  # the third arg is a list of all the fields you don't know, and you need to use the "skip_missing_optional_keys=True" option
for path in paths:
    f=temp.get_fields(path)
    print(f)
    print(f.get("version"))
print(self._sg_template.fields_from_path(paths[0]))


test = {}
test["asdf"] = [2]
test.update({"asdf":[32]})


shot_trigger._sg_template

shot_trigger.task
shot_trigger.get_latest_path("asset_trigger_guide", part_name="weights1")

shot_trigger.get_steps(shot_trigger.asset)

shot_trigger.get_tasks(shot_trigger.asset, shot_trigger.step)


##

# try to get the asset_type, asset, step and task values. Order:
    # 1. (DISCARDED) Trigger session file
    # 2. solve it with with work file
    # 3. None (pick the first of each column)

# Get the asset_types and feed the combo box
# set the

from PySide2 import QtWidgets
from trigger.ui.vcs_widgets import session_selection
reload(asset_selection)
# from trigger.ui.custom_widgets import ListBoxLayout
d = QtWidgets.QDialog()
r = asset_selection.SessionSelection()
r.new_session_signal.connect(lambda x: print("hede_%s" %x))
d.setLayout(r)

d.show()