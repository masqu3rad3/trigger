"""Shotgrid toolkit"""
from maya import cmds
from rbl_pipe_sg import template, load, publish
from trigger.core import filelog

log = filelog.Filelog(logname=__name__, filename="trigger_log")

sg_script = "rbl_pipe_maya"
sg_key = "nn5lcvmojkfqgbzUkhbwdh%nc"

# templates
#
# Trigger
#

work_area_t = "asset_work_area_trigger"
# definition: '@asset_root/work/trigger'

guide_t = "asset_trigger_guide"
# definition: '@asset_work_area_trigger/guides/{Asset}_{variant_name}_{part_name}_v{version}.trg'

session_t = "asset_trigger_sessionfile"
# definition: '@asset_work_area_trigger/{Asset}_{variant_name}_v{version}.tr'

lookfile_t = "asset_trigger_lookfile"
# definition: '@asset_work_area_trigger/look/{Asset}_{variant_name}_{action_name}_v{version}.trl'

presetsfile_t = "asset_trigger_presetsfile"
# definition: '@asset_work_area_trigger/presets/{Asset}_{variant_name}_{action_name}_v{version}.trp'

script_t = "asset_trigger_script"
# definition: '@asset_work_area_trigger/scripts/{Asset}_{variant_name}_{action_name}_v{version}.py'

shapefile_t = "asset_trigger_shapefile"
# definition: '@asset_work_area_trigger/shapes/{Asset}_{variant_name}_{action_name}_v{version}.trs'

splitsfile_t = "asset_trigger_splitsfile"
# definition: '@asset_work_area_trigger/splits/{Asset}_{variant_name}_{action_name}_v{version}.trsplit'

weightfile_t = "asset_trigger_weightfile"
# definition: '@asset_work_area_trigger/weights/{Asset}_{variant_name}_{action_name}_v{version}.trw'


class ShotTrigger(object):
    _sg_load = load.ShotgunLoad(sg_script, sg_key)
    _sg_template = template.SGTemplate(sg_script, sg_key)

    project = None
    asset_type = None
    asset = None
    step = None
    task = None
    def __init__(self):
        super(ShotTrigger, self).__init__()

        self.work_file = cmds.file(sn=True, q=True)
        self._initialize()

    def _initialize(self):
        """Try to set the project, asset type, asset and variation from workfile"""
        if self.work_file:
            _fields = self._sg_template.fields_from_path(self.work_file)
            if _fields:
                print(_fields)
                self.asset_type = _fields.get("sg_asset_type")
                self.asset = _fields.get("Asset", None)
                self.step = _fields.get("Step", None)
                self.task = _fields.get("variant_name", None)

    def get_asset_types(self):
        """Returns all asset types in current project"""
        return [x.get('name') for x in self._sg_load.get_asset_types(force=False)]

    def get_assets(self, asset_type):
        """Returns all assets under defined asset_type"""
        return [x.get('code') for x in self._sg_load.get_assets(force=False, asset_type=asset_type)]

    def get_steps(self, asset):
        """Returns all steps under defined asset"""
        asset_id = self._sg_load.asset_id_from_name(asset)
        return [x.get("step.Step.short_name") for x in self._sg_load.get_asset_steps(force=False, asset=asset_id)]

    def get_tasks(self, asset, step):
        """Returns all asset variations under given asset"""
        asset_id = self._sg_load.asset_id_from_name(asset)
        step_id = self._sg_load.step_id_from_name(step, asset_id)
        all_task_names = [x.get("content") for x in self._sg_load.get_asset_tasks(force=False, asset=asset_id, step=step_id)]
        # hide main_ tasks
        filtered_tasks = [x for x in all_task_names if "main_" not in x.lower()]
        return filtered_tasks
        # return [x.get("content") for x in self._sg_load.get_asset_tasks(force=False, asset=asset_id, step=step_id) if not x.get("content").startswith("main_")]

