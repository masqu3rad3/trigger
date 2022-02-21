"""Shotgrid toolkit"""
import re

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
# definition: '@asset_work_area_trigger/{Asset}_{variant_name}_{part_name}_v{version}.tr'

lookfile_t = "asset_trigger_lookfile"
# definition: '@asset_work_area_trigger/look/{Asset}_{variant_name}_{action_name}_v{version}.trl'

presetsfile_t = "asset_trigger_presetsfile"
# definition: '@asset_work_area_trigger/presets/{Asset}_{variant_name}_{action_name}_v{version}.trp'

script_t = "asset_trigger_script"
# definition: '@asset_work_area_trigger/scripts/{Asset}_{variant_name}_{action_name}_v{version}.py'

shapefile_t = "asset_trigger_shapefile"
# definition: '@asset_work_area_trigger/shapes/{Asset}_{variant_name}_{action_name}_v{version}.ma'

splitsfile_t = "asset_trigger_splitsfile"
# definition: '@asset_work_area_trigger/splits/{Asset}_{variant_name}_{action_name}_v{version}.trsplit'

weightfile_t = "asset_trigger_weightfile"
# definition: '@asset_work_area_trigger/weights/{Asset}_{variant_name}_{action_name}_v{version}.trw'


class VersionControl(object):
    _sg_load = load.ShotgunLoad(sg_script, sg_key)
    _sg_template = template.SGTemplate(sg_script, sg_key)

    controller = "rbl_shotgrid"
    # project = None
    # asset_type = None
    # asset = None
    # step = None
    # _task = None
    # variant = None
    # session = None
    # session_version = None
    # _sessions_db = {}
    def __init__(self):
        super(VersionControl, self).__init__()

        self.work_file = cmds.file(sn=True, q=True)

        self.project = None
        self.asset_type = None
        self.asset = None
        self.step = None
        self._task = None
        self.variant = None
        self.session = None
        self.session_version = None
        self._sessions_db = {}

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
                # print("*****")
                self.variant = _fields.get("variant_name", None)
                self._task = "{0}_{1}".format(self.variant, self.step)
                # get the first encountered session if there are tr sessions
                _sessions = self.get_sessions(self.asset, self.step, self.variant)
                self.session = _sessions[0] if _sessions else None

    @property
    def task(self):
        return self._task

    @task.setter
    def task(self, val):
        """When defining task, define the variation too"""
        self._task = val
        self.variant = self._variant_from_task(val)

    @staticmethod
    def _variant_from_task(task_name):
        match = re.match("([A-Z0-9a-z]*)(_([A-Z0-9a-z]*))", task_name)
        if match:
            return match.groups()[0]
        return None

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

    def get_sessions(self, asset, step, variant):
        """Returns trigger session (.tr) files under the asset"""
        _session_data = self.__get_session_data(asset, step, variant)
        return list(sorted(_session_data.keys()))

    def get_versions(self, asset, step, variant, session_part_name):
        """Returns the versions of specified trigger session file"""
        _session_data = self.__get_session_data(asset, step, variant)
        return _session_data.get(session_part_name, [])

    def __get_session_data(self, asset, step, variant):
        """Returns dictionary containing session data where keys are part names, values are version numbers"""
        self._sessions_db.clear()
        tk = self._sg_template.tk  # get tk instance from sg_template, or elsewhere if you already have an instance
        sg_temp = tk.templates.get(session_t)
        fields = {"Asset": asset, "Step": step,
                  "variant_name": variant}  # assemble all of the fields you know
        paths = tk.paths_from_template(sg_temp, fields, ["version"],
                                       skip_missing_optional_keys=True)  # the third arg is a list of all the fields you don't know, and you need to use the "skip_missing_optional_keys=True" option

        for path in paths:
            _f = sg_temp.get_fields(path)
            part_name = _f.get("part_name", None)
            ver = _f.get("version", None)
            if self._sessions_db.get(part_name, None):
                self._sessions_db[part_name].append(ver)
            else:
                self._sessions_db[part_name] = [ver]
        return self._sessions_db  # This should list all the paths that match the above query

    # def get_sessions(self):
    #     """Returns trigger session (.tr) files under the asset"""
    #     tk = self._sg_template.tk  # get tk instance from sg_template, or elsewhere if you already have an instance
    #     sg_template = tk.templates.get(session)
    #     fields = {"sg_asset_type": self.asset_type, "Asset": self.asset, "Step": self.step,
    #               "variant_name": self.variant}  # assemble all of the fields you know
    #     paths = tk.paths_from_template(sg_template, fields, ["version"],
    #                                    skip_missing_optional_keys=True)  # the third arg is a list of all the fields you don't know, and you need to use the "skip_missing_optional_keys=True" option
    #     return paths  # This should list all the paths that match the above query

    # def get_next_session(self):

    def request_new_session_path(self, part_name):
        asset_id = self._sg_load.asset_id_from_name(self.asset)
        task_id = self._sg_load.task_id_from_name(self.task, asset_id=asset_id)
        # set the session file
        self.session = part_name
        return self._sg_template.output_path_from_template(session_t, task_id, 1, part_name=part_name)

    # def request_new_version_path(self):
    #     """Version increment path"""
    #     if not self.session:
    #         log.error("No session (part_name) set")
    #     asset_id = self._sg_load.asset_id_from_name(self.asset)
    #     task_id = self._sg_load.task_id_from_name(self.task, asset_id=asset_id)
    #     version = self._sg_template.current_version_from_template_list([session_t], task_id) or 0
    #     print(self.asset, self.task, self.session, version)
    #     path = self._sg_template.output_path_from_template(session_t, task_id, version + 1, part_name=self.session)
    #     return path
    def request_new_version_path(self):
        """Version increment path"""
        if not self.session:
            log.error("No session (part_name) set")
        asset_id = self._sg_load.asset_id_from_name(self.asset)
        task_id = self._sg_load.task_id_from_name(self.task, asset_id=asset_id)
        # version = self._sg_template.current_version_from_template_list([session_t], task_id) or 0
        _dict = self.__get_session_data(self.asset, self.step, self.variant)
        version = max(_dict.get(self.session, [0]))
        path = self._sg_template.output_path_from_template(session_t, task_id, version + 1, part_name=self.session)
        return path

    def get_session_path(self):
        asset_id = self._sg_load.asset_id_from_name(self.asset)
        task_id = self._sg_load.task_id_from_name(self.task, asset_id=asset_id)
        return self._sg_template.output_path_from_template(session_t, task_id, self.session_version, part_name=self.session)

    # def get_task_path(self):
        

    # def get_latest_path(self, trigger_template, **kwargs):
    #     asset_id = self._sg_load.asset_id_from_name(self.asset)
    #     print("asset_id", asset_id)
    #     task_id = self._sg_load.task_id_from_name(self.task, asset_id=asset_id)
    #     print("task_id", task_id)
    #     version = self._sg_template.current_version_from_template_list([trigger_template], task_id) or 1
    #     print("version", version)
    #     path = self._sg_template.output_path_from_template(trigger_template, task_id, version, **kwargs)
    #     return path
    #     # pass

    # def get_next_path(self, trigger_template):
    #     pass
    #
    # def get_previous_path(self, trigger_template):
    #     pass
    #
    # def is_latest(self, trigger_template):
    #     pass
