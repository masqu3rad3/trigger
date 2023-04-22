"""tools to be used with trigger rigs

:created: 29 June 2020
:author: Arda Kutlu <arda.kutlu@rebellion.co.uk>
"""

import os
import json
import sys
import weakref
from functools import wraps
import logging

logger = logging.getLogger(__name__)

from trigger.library import fbx

from trigger.core import compatibility
from trigger.library.functions import unique_list
from trigger.ui.Qt import QtWidgets, QtCore, QtCompat
from trigger.ui import feedback
from maya import OpenMayaUI as omui
from maya import cmds
from maya import mel

__version__ = "0.0.4"
windowName = "Trigger Tool v%s" % __version__
qss = """
QPushButton
{
    color: #b1b1b1;
    background-color: #404040;
    border-width: 1px;
    border-color: #1e1e1e;
    border-style: solid;
    padding: 5px;
    font-size: 12px;
}

QPushButton:hover
{
    background-color: #505050;
    border: 1px solid #ff8d1c;
}

QPushButton:disabled {
  background-color: #303030;
  border: 1px solid #404040;
  color: #505050;
  padding: 3px;
}

QPushButton:pressed {
  background-color: #ff8d1c;
  border: 1px solid #ff8d1c;
}

QPushButton[override = "0"]{
    border-color: blue;
}

QPushButton[override = "1"]{
    border-color: green;
}

QPushButton[menuButton=true] {
  min-width: 120;
  min-height: 45;
}
"""


def _createCallbacks(function, parent, event):
    callbackIDList = []
    callbackIDList.append(
        cmds.scriptJob(e=[event, function], replacePrevious=True, parent=parent))
    return callbackIDList


def _killCallbacks(callbackIDList):
    for ID in callbackIDList:
        if cmds.scriptJob(ex=ID):
            cmds.scriptJob(kill=ID)

def undo(func):
    """Make maya commands undoable."""

    @wraps(func)
    def decorator(*args, **kwargs):
        """Use maya undo chunks to allow undo on complicated methods."""
        cmds.undoInfo(openChunk=True)
        returned = None
        try:
            returned = func(*args, **kwargs)
        except Exception as exc:  # pylint: disable=broad-except
            cmds.error(exc)
        finally:
            cmds.undoInfo(closeChunk=True)
            return returned
    return decorator

class TriggerTool(object):
    def __init__(self):
        super(TriggerTool, self).__init__()
        self.definitions = self.load_globals()
        self.mapping = self.load_import_mapping()

        # self.all_ctrls = self.get_all_controllers()

        self.overrideNamespace = False

        self.namespace = None

        # self.zero_dictionary = {"translate": (0,0,0), "rotate": (0,0,0), "scale": (1,1,1)}
        self.zero_dictionary = {"tx": 0, "ty": 0, "tz": 0, "rx": 0, "ry": 0, "rz": 0, "sx": 1, "sy": 1, "sz": 1}

    def _get_all_controls(self):
        """Selects all controllers based on the override settings"""
        selection = cmds.ls(sl=True)
        if self.overrideNamespace and selection:
            namespace = self.get_selected_namespace()
        else:
            namespace = self.namespace
        if namespace:
            select_keys = ["%s:%s" % (namespace, key) for key in self.definitions["controller_keys"]]
        else:
            select_keys = list(self.definitions["controller_keys"])

        return (y for y in (cmds.ls(select_keys, transforms=True, exactType="transform")) if cmds.listRelatives(y, children=True, shapes=True)) # this returns a generator

    def _get_key_controls(self, key_list):
        exclude_list = self.definitions["exclude"]
        all_conts = self._get_all_controls()
        if exclude_list:
            if self.namespace:
                exclude_list = ["%s:%s" %(self.namespace, element) for element in exclude_list]
            all_conts = [cont for cont in all_conts if cont not in exclude_list]
        for cont in all_conts:
            for key in self.definitions[key_list]:
                if key.lower() in cont.lower():
                    yield cont

    def _get_mirror_controls(self):
        selection = cmds.ls(sl=True)
        if not selection:
            return
        for node in selection:
            for side in self.definitions["side_pairs"]:
                if side[0] in node:
                    other_side = node.replace(side[0], side[1])
                    if cmds.objExists(other_side):
                        yield other_side
                    else:
                        cmds.warning("Pair of %s does not exist" % node)
                elif side[1] in node:
                    other_side = node.replace(side[1], side[0])
                    if cmds.objExists(other_side):
                        yield other_side
                    else:
                        cmds.warning("Pair of %s does not exist" % node)
                else:
                    yield node
                    # cmds.warning("%s is single sided or pair cannot be found" % node)

    @undo
    def select_body(self, modifier="replace", selectVisible=False):
        ctrls = self._get_key_controls("body_keys")
        if selectVisible:
            ctrls = filter(self._filter_visibles, ctrls)
        if modifier == "replace":
            cmds.select(ctrls)
        elif modifier == "add":
            cmds.select(ctrls, add=True)
        elif modifier == "subtract":
            cmds.select(ctrls, d=True)

    @undo
    def select_face(self, modifier="replace", selectVisible=False):
        ctrls = self._get_key_controls("face_keys")
        if selectVisible:
            ctrls = filter(self._filter_visibles, ctrls)
        if modifier == "replace":
            cmds.select(ctrls)
        elif modifier == "add":
            cmds.select(ctrls, add=True)
        elif modifier == "subtract":
            cmds.select(ctrls, d=True)

    @undo
    def select_tweakers(self, modifier="replace", selectVisible=False):
        ctrls = self._get_key_controls("tweaker_keys")
        if selectVisible:
            ctrls = filter(self._filter_visibles, ctrls)
        if modifier == "replace":
            cmds.select(ctrls)
        elif modifier == "add":
            cmds.select(ctrls, add=True)
        elif modifier == "subtract":
            cmds.select(ctrls, d=True)

    @undo
    def select_mirror(self, modifier="replace", selectVisible=False):
        mirror_gen = self._get_mirror_controls()
        if selectVisible:
            mirror_gen = filter(self._filter_visibles, mirror_gen)
        if mirror_gen:
            # cmds.select(self._get_mirror_controls(), add=add)
            if modifier == "replace":
                cmds.select(mirror_gen)
            elif modifier == "add":
                cmds.select(mirror_gen, add=True)
            elif modifier == "subtract":
                cmds.select(mirror_gen, d=True)

    @undo
    def zero_pose(self, selectedOnly=True):
        modified = []
        if selectedOnly:
            controls = cmds.ls(sl=True)
        else:
            controls = self._get_all_controls()
        for cont in controls:
            for attr, value in self.zero_dictionary.items():
                try:
                    cmds.setAttr("%s.%s" %(cont, attr), value)
                    modified.append("%s.%s" %(cont, attr))
                except RuntimeError:
                    pass
            custom_attrs = cmds.listAttr(cont, ud=True)

            if custom_attrs:
                for attr in custom_attrs:
                    if cmds.attributeQuery(attr, node=cont, storable=True, k=True):
                        default_value = cmds.attributeQuery(attr, node=cont, listDefault=True)
                        if default_value:
                            try:
                                cmds.setAttr("%s.%s" % (cont, attr), default_value[0])
                                modified.append("%s.%s" % (cont, attr))
                            except RuntimeError: pass
        return modified

    @undo
    def reset_pose(self, selectedOnly=False):
        modified = self.zero_pose(selectedOnly=selectedOnly)
        for attr in modified:
            key = cmds.listConnections(attr, connections=False, destination=False, source=True, scn=True)
            if key:
                if cmds.objectType(key[0]) == "animCurveTA" or\
                    cmds.objectType(key[0]) == "animCurveTL" or\
                        cmds.objectType(key[0]) == "animCurveTU":
                    cmds.delete(key[0])

    @undo
    def mirror_pose(self, mode, swap=False):
        selected_conts = cmds.ls(sl=True)
        mirror_conts = unique_list(list(self._get_mirror_controls()))
        for mirror_cont, orig_cont in zip(mirror_conts, selected_conts):
            for nmb, attr in enumerate("xyz"):
                orig_t_value = cmds.getAttr("%s.t%s" %(orig_cont, attr))
                swap_t_value = cmds.getAttr("%s.t%s" %(mirror_cont, attr))
                mirror_t_value = orig_t_value * self.definitions["mirror_modes"][mode][0][nmb]
                try:
                    cmds.setAttr("%s.t%s" %(mirror_cont, attr), mirror_t_value)
                    if swap:
                        cmds.setAttr("%s.t%s" % (orig_cont, attr), swap_t_value * self.definitions["mirror_modes"][mode][0][nmb])
                except:
                    pass
                orig_r_value = cmds.getAttr("%s.r%s" % (orig_cont, attr))
                swap_r_value = cmds.getAttr("%s.r%s" %(mirror_cont, attr))
                mirror_r_value = orig_r_value * self.definitions["mirror_modes"][mode][1][nmb]
                try:
                    cmds.setAttr("%s.r%s" % (mirror_cont, attr), mirror_r_value)
                    if swap:
                        cmds.setAttr("%s.r%s" % (orig_cont, attr), swap_r_value * self.definitions["mirror_modes"][mode][0][nmb])
                except:
                    pass

    def load_globals(self):
        """Loads the given json file"""
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(dir_path, "panel_globals.json")
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'r') as f:
                    definitions = json.load(f)
                    return definitions
            except ValueError:
                cmds.error("Corrupted JSON file => %s" % file_path)
        else:
            cmds.warning("Definition file cannot be found. Using default settings")
            default_definitions = {
                "controller_keys": ["ctrl*", "crtl*", "*cont"],
                "body_keys": ["character", "pelvis", "arm", "leg", "knee", "foot", "clavicle", "elbow","finger", "spine", "head", "hand", "toe", "collar", "torso", "neck", "thumb", "skirt", "hair"],
                "face_keys": ["jaw", "eye", "cheek", "mouth", "lip", "eyelid", "scalp", "nose", "teeth", "stretch", "brow", "grin", "chin", "grumpy"],
                "tweaker_keys": ["twk"],
                "side_pairs": [["_L_","_R_"],["L_", "R_"]],
                "exclude": ["ctrl_character"],
                "mirror_modes": {"A": [[1, 1, -1],[-1, -1, 1]],
                                 "B": [[-1, 1, 1],[1, -1, -1]],
                                 "C": [[-1, -1, -1],[1, 1, 1]],
                                 "D": [[1, 1, 1],[1, 1, 1]]
                                 }
            }
            self.save_globals(default_definitions)
            return default_definitions

    def load_import_mapping(self):
        # first look at the home folder
        documents_file_path = os.path.join(os.path.expanduser("~"), "panel_importmapping.json")
        if os.path.isfile(documents_file_path):
            file_path = documents_file_path
        else:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            file_path = os.path.join(dir_path, "panel_importmapping.json")
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'r') as f:
                    definitions = json.load(f)
                    return definitions
            except ValueError:
                cmds.error("Corrupted JSON file => %s" % file_path)
        else:
            cmds.error("Definition file cannot be found. Using default settings")

    def save_globals(self, definitions_data):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(dir_path, "panel_globals.json")
        with open(file_path, "w") as f:
            json.dump(definitions_data, f, indent=4)

    def get_scene_namespaces(self):
        garbage = ['UI', 'shared']
        return filter(lambda x: x not in garbage, cmds.namespaceInfo(listOnlyNamespaces=True))

    def get_selected_namespace(self):
        sel = cmds.ls(sl=True, sns=True)
        if sel:
            if ':' in sel[0]:
                return sel[0].rsplit(':')[0]
            else:
                return ""

    def set_namespace(self, namespace):
        self.namespace = namespace

    def _filter_visibles(self, node):
        checklist = cmds.ls(node, long=True)[0].split('|')[1:-1] + [node]
        for parent in checklist:
            if (cmds.getAttr("%s.v" % parent) == 0):
                return False
        return True

    @undo
    def import_animation(self, bind_pose_path, fbx_path):
        fbx_namespace = "_trigger_"
        # anim_fbx_namepace = "_trigger_anim_fbx"
        self._load_fbx_plugin()
        fbx_import_settings = {
            "FBXImportMergeBackNullPivots": "-v true",
            "FBXImportMode": "-v add",
            "FBXImportSetLockedAttribute": "-v false",
            "FBXImportUnlockNormals": "-v false",
            "FBXImportScaleFactor": "1.0",
            "FBXImportProtectDrivenKeys": "-v true",
            "FBXImportShapes": "-v true",
            "FBXImportQuaternion": "-v euler",
            "FBXImportCameras": "-v true",
            "FBXImportSetMayaFrameRate": "-v false",
            "FBXImportResamplingRateSource": "-v Scene",
            "FBXImportGenerateLog": "-v false",
            "FBXImportConstraints": "-v true",
            "FBXImportLights": "-v true",
            "FBXImportConvertDeformingNullsToJoint": "-v true",
            "FBXImportFillTimeline": "-v false",
            "FBXImportMergeAnimationLayers": "-v true",
            "FBXImportHardEdges": "-v false",
            "FBXImportAxisConversionEnable": "-v true",
            "FBXImportCacheFile": "-v true",
            "FBXImportUpAxis": "y",
            "FBXImportSkins": "-v true",
            "FBXImportConvertUnitString": "-v true",
            "FBXImportForcedFileAxis": "-v disabled"
        }
        for item in fbx_import_settings.items():
            mel.eval('%s %s' % (item[0], item[1]))

        bind_pose_nodes = fbx.load(bind_pose_path, merge_mode="add", animation=False, skins=True)
        # cmds.file(bind_pose_path, reference=True, mergeNamespacesOnClash=True, namespace=fbx_namespace)
        # updated_mapping = self._update_mapping_dictionary(self.mapping, fbx_namespace, self.namespace)
        self._stick_to_joints(self.mapping)
        # cmds.file(fbx_path, reference=True, mergeNamespacesOnClash=True, namespace=fbx_namespace)

        # anim_nodes = fbx.load(fbx_path, merge_mode="merge", animation=True, skins=True)
        # self._bake_ctrls(updated_mapping)

        # self._bake_ctrls(self.mapping)

        # cmds.file(fbx_path, rr=True)
        # delete imported fbx nodes
        # all_nodes = list(set(bind_pose_nodes + anim_nodes))
        # cmds.delete(all_nodes)

    def _info_pop(self, textTitle="info", textHeader="", textInfo="", type="I"):
        self.msg = QtWidgets.QMessageBox(parent=self)
        if type == "I":
            self.msg.setIcon(QtWidgets.QMessageBox.Information)
        if type == "C":
            self.msg.setIcon(QtWidgets.QMessageBox.Critical)

        self.msg.setText(textHeader)
        self.msg.setInformativeText(textInfo)
        self.msg.setWindowTitle(textTitle)
        self.msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        self.msg.button(QtWidgets.QMessageBox.Ok).setFixedHeight(30)
        self.msg.button(QtWidgets.QMessageBox.Ok).setFixedWidth(100)
        self.msg.show()


    def _load_fbx_plugin(self):
        if not cmds.pluginInfo('fbxmaya', l=True, q=True):
            try:
                cmds.loadPlugin('fbxmaya')
            except:
                msg = "FBX Plugin cannot be initialized."
                cmds.error(msg)

    def _stick_to_joints(self, mapping_dictionary):
        for joint, cont in mapping_dictionary.items():
            # import pdb
            # pdb.set_trace()

            if cmds.objExists(joint) and cmds.objExists(cont):

                locked_translates_raw = cmds.listAttr("%s.t" % cont, l=True, sn=True)
                locked_translates = [attr.replace("t", "") for attr in
                                     locked_translates_raw] if locked_translates_raw else []
                locked_rotates_raw = cmds.listAttr("%s.r" % cont, l=True, sn=True)
                locked_rotates = [attr.replace("r", "") for attr in locked_rotates_raw] if locked_rotates_raw else []
                cmds.parentConstraint(joint, cont, maintainOffset=True, st=locked_translates, sr=locked_rotates)

    def _bake_ctrls(self, mapping_dictionary):
        for joint, cont in mapping_dictionary.items():
            if cmds.objExists(joint) and cmds.objExists(cont):
                first = cmds.findKeyframe(joint, which="first")
                last = cmds.findKeyframe(joint, which="last") + 1 # makes sure round up
                cmds.bakeResults(cont, t=(first, last), simulation=False)


    def _update_mapping_dictionary(self, mapping_dictionary, joint_namespace, cont_namespace):
        """Updates the mapping dictionary with namespaces"""
        jnt_template = "{0}:{1}" if joint_namespace else "{0}{1}"
        cont_template = "{0}:{1}" if cont_namespace else "{0}{1}"
        updated_mapping_dictionary = {
            jnt_template.format(joint_namespace, joint): cont_template.format(cont_namespace, cont) for joint, cont in
            mapping_dictionary.items()}
        return updated_mapping_dictionary

def dock_window(dialog_class):
    try:
        cmds.deleteUI(dialog_class.CONTROL_NAME)
        logger.info('removed workspace {}'.format(dialog_class.CONTROL_NAME))
    except:
        pass

    # building the workspace control with maya.cmds
    main_control = cmds.workspaceControl(dialog_class.CONTROL_NAME, restore=True, dtc=["AttributeEditor", "top"], iw=100, mw=80, wp='preferred', label=dialog_class.DOCK_LABEL_NAME)

    # now lets get a C++ pointer to it using OpenMaya
    control_widget = omui.MQtUtil.findControl(dialog_class.CONTROL_NAME)
    # conver the C++ pointer to Qt object we can use
    if sys.version_info.major == 3:
        control_wrap = QtCompat.wrapInstance(int(control_widget), QtWidgets.QWidget)
    else:
        control_wrap = QtCompat.wrapInstance(long(control_widget), QtWidgets.QWidget)

    # control_wrap is the widget of the docking window and now we can start working with it:
    control_wrap.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    win = dialog_class(control_wrap)

    # after maya is ready we should restore the window since it may not be visible
    cmds.evalDeferred(lambda *args: cmds.workspaceControl(main_control, e=True, rs=True))

    # will return the class of the dock content.
    return win.run()

class MainUI(QtWidgets.QWidget):

    instances = list()
    CONTROL_NAME = "triggerTools"
    DOCK_LABEL_NAME = windowName

    # def __init__(self):
    def __init__(self, parent=None):
        super(MainUI, self).__init__(parent)


        # let's keep track of our docks so we only have one at a time.
        MainUI.delete_instances()
        self.__class__.instances.append(weakref.proxy(self))
        self.window_name = self.CONTROL_NAME
        self.ui = parent
        self.main_layout = parent.layout()
        self.main_layout.setContentsMargins(2, 2, 2, 2)

        self.centralwidget = QtWidgets.QWidget()
        self.main_layout.addWidget(self.centralwidget)
        self.centralwidget.setStyleSheet(qss)
        self.setWindowTitle(windowName)
        self.setObjectName(windowName)
#
        self.centralwidget.setFocusPolicy(QtCore.Qt.StrongFocus)
#
        self.dynamicButtons = []
        self.tr_tool = TriggerTool()
        self.feedback = feedback.Feedback()

        self.buildUI()
        self.init_values()
        self.callbackIDList = _createCallbacks(self.populate_namespaces, windowName, "PostSceneRead")

    def closeEvent(self, event):
        if self.isCallback:
            _killCallbacks(self.callbackIDList)

    @staticmethod
    def delete_instances():
        for ins in MainUI.instances:
            logger.info('Delete {}'.format(ins))
            try:
                ins.setParent(None)
                ins.deleteLater()
            except:
                # ignore the fact that the actual parent has already been deleted by Maya...
                pass

            MainUI.instances.remove(ins)
            del ins

    def run(self):
        return self

    def modifiedSelect(self, command):
        mods = QtWidgets.QApplication.keyboardModifiers()
        isShift = mods & QtCore.Qt.ShiftModifier
        isCtrl = mods & QtCore.Qt.ControlModifier

        if isShift and isCtrl:
            modifier = "replace"
        elif isShift:
            modifier = "add"
        elif isCtrl:
            modifier = "subtract"
        else:
            modifier = "replace"

        selectVisible = self.select_only_visible_cb.isChecked()

        if command == "selectFace":
            self.tr_tool.select_face(modifier=modifier, selectVisible=selectVisible)
        elif command == "selectBody":
            self.tr_tool.select_body(modifier=modifier, selectVisible=selectVisible)
        elif command == "selectTweakers":
            self.tr_tool.select_tweakers(modifier=modifier, selectVisible=selectVisible)
        elif command == "selectMirror":
            self.tr_tool.select_mirror(modifier=modifier, selectVisible=selectVisible)


    def buildUI(self):
        self.main_vlay = QtWidgets.QVBoxLayout(self.centralwidget)
        self.main_vlay.setContentsMargins(5, 5, 5, 5)
        self.main_vlay.setSpacing(5)
        self.main_vlay.setObjectName("main_vlay")

        self.select_and_pose_hlay = QtWidgets.QHBoxLayout()

        self.select_gbox = QtWidgets.QGroupBox(self.centralwidget)
        self.select_gbox.setTitle("Select")

        self.select_grp_vlay = QtWidgets.QVBoxLayout(self.select_gbox)
        self.select_grp_vlay.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.select_grp_vlay.setContentsMargins(5, 0, 0, 5)
        self.select_grp_vlay.setSpacing(5)

        self.select_vlay = QtWidgets.QVBoxLayout()
        self.select_vlay.setSizeConstraint(QtWidgets.QLayout.SetMaximumSize)
        self.select_vlay.setSpacing(5)

        self.all_body_pb = QtWidgets.QPushButton(self.select_gbox)
        # self.all_body_pb = ModifierButton(self.select_gbox)
        self.all_body_pb.setText("All Body")
        self.select_vlay.addWidget(self.all_body_pb)
        self.dynamicButtons.append(self.all_body_pb)

        self.all_face_pb = QtWidgets.QPushButton(self.select_gbox)
        self.all_face_pb.setText("All Face")
        self.select_vlay.addWidget(self.all_face_pb)
        self.dynamicButtons.append(self.all_face_pb)

        self.select_mirror_pb = QtWidgets.QPushButton(self.select_gbox)
        self.select_mirror_pb.setText("Select Mirror")
        self.select_vlay.addWidget(self.select_mirror_pb)

        self.all_tweakers_pb = QtWidgets.QPushButton(self.select_gbox)
        self.all_tweakers_pb.setText("All Tweakers")
        self.select_vlay.addWidget(self.all_tweakers_pb)
        self.dynamicButtons.append(self.all_tweakers_pb)

        self.select_grp_vlay.addLayout(self.select_vlay)
        self.select_and_pose_hlay.addWidget(self.select_gbox)

        self.pose_gbox = QtWidgets.QGroupBox(self.centralwidget)
        self.pose_gbox.setTitle("Pose")

        self.pose_grp_vlay = QtWidgets.QVBoxLayout(self.pose_gbox)
        self.pose_grp_vlay.setContentsMargins(5, 0, 5, 0)
        self.pose_grp_vlay.setSpacing(5)

        self.pose_ctrls_vlay = QtWidgets.QVBoxLayout()
        self.pose_ctrls_vlay.setSpacing(5)

        self.copy_mirror_pb = QtWidgets.QPushButton(self.pose_gbox)
        self.copy_mirror_pb.setText("Copy Mirror")
        self.pose_ctrls_vlay.addWidget(self.copy_mirror_pb)

        self.swap_mirror_pb = QtWidgets.QPushButton(self.pose_gbox)
        self.swap_mirror_pb.setText("Swap Mirror")
        self.pose_ctrls_vlay.addWidget(self.swap_mirror_pb)

        self.zero_tpose_pb = QtWidgets.QPushButton(self.pose_gbox)
        self.zero_tpose_pb.setText(" Zero T-Pose")
        self.pose_ctrls_vlay.addWidget(self.zero_tpose_pb)
        self.dynamicButtons.append(self.zero_tpose_pb)

        self.reset_tpose_pb = QtWidgets.QPushButton(self.pose_gbox)
        self.reset_tpose_pb.setText("Reset T-Pose")
        self.dynamicButtons.append(self.reset_tpose_pb)

        self.pose_ctrls_vlay.addWidget(self.reset_tpose_pb)

        self.pose_grp_vlay.addLayout(self.pose_ctrls_vlay)

        self.select_and_pose_hlay.addWidget(self.pose_gbox)

        self.main_vlay.addLayout(self.select_and_pose_hlay)

        self.settings_gbox = QtWidgets.QGroupBox(self.centralwidget)
        self.settings_gbox.setTitle("Settings")

        self.settings_grp_vlay = QtWidgets.QVBoxLayout(self.settings_gbox)
        self.settings_grp_vlay.setContentsMargins(5, 0, 5, 0)
        self.settings_grp_vlay.setSpacing(5)

        self.select_only_visible_cb = QtWidgets.QCheckBox(self.centralwidget)
        self.select_only_visible_cb.setText("Select Only Visible")
        self.select_only_visible_cb.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.settings_grp_vlay.addWidget(self.select_only_visible_cb)

        self.override_namespace_cb = QtWidgets.QCheckBox(self.centralwidget)
        self.override_namespace_cb.setText("Override with selection")
        self.override_namespace_cb.setLayoutDirection(QtCore.Qt.RightToLeft)
        self.settings_grp_vlay.addWidget(self.override_namespace_cb)

        self.namespace_hlay = QtWidgets.QHBoxLayout()
        self.namespace_hlay.setSpacing(0)

        self.namespace_lbl = QtWidgets.QLabel(self.settings_gbox)
        self.namespace_lbl.setText("Namespace")
        self.namespace_hlay.addWidget(self.namespace_lbl)

        self.namespace_combo = QtWidgets.QComboBox(self.settings_gbox)
        self.namespace_hlay.addWidget(self.namespace_combo)
        self.namespace_refresh_pb = QtWidgets.QPushButton(self.settings_gbox)
        self.namespace_refresh_pb.setText("R")
        self.namespace_refresh_pb.setMinimumWidth(30)
        self.namespace_refresh_pb.setMaximumWidth(30)
        self.namespace_hlay.addWidget(self.namespace_refresh_pb)
        self.settings_grp_vlay.addLayout(self.namespace_hlay)

        self.mirror_mode_hlay = QtWidgets.QHBoxLayout()
        self.mirror_mode_hlay.setSpacing(0)

        self.mirror_mode_lbl = QtWidgets.QLabel(self.settings_gbox)
        self.mirror_mode_lbl.setText("Mirror Mode")
        self.mirror_mode_hlay.addWidget(self.mirror_mode_lbl)

        self.mirror_mode_combo = QtWidgets.QComboBox(self.settings_gbox)
        self.mirror_mode_hlay.addWidget(self.mirror_mode_combo)
        self.mirror_mode_combo.addItems(sorted(self.tr_tool.definitions["mirror_modes"].keys()))

        self.settings_grp_vlay.addLayout(self.mirror_mode_hlay)

        self.main_vlay.addWidget(self.settings_gbox)


        self.import_gbox = QtWidgets.QGroupBox(self.centralwidget)
        self.import_gbox.setTitle("Import FBX")

        self.import_grp_vlay = QtWidgets.QVBoxLayout(self.import_gbox)
        self.import_grp_vlay.setContentsMargins(5, 0, 5, 0)
        self.import_grp_vlay.setSpacing(5)

        self.import_grp_hlay0 = QtWidgets.QHBoxLayout()
        self.import_grp_vlay.addLayout(self.import_grp_hlay0)
        self.import_bind_pose_le = QtWidgets.QLineEdit(self.import_gbox)
        self.import_bind_pose_le.setPlaceholderText("Browse a Bind Pose FBX file")
        self.import_grp_hlay0.addWidget(self.import_bind_pose_le)
        self.import_bind_pose_browse_pb = QtWidgets.QPushButton(self.import_gbox)
        self.import_bind_pose_browse_pb.setText("...")
        self.import_grp_hlay0.addWidget(self.import_bind_pose_browse_pb)

        self.import_grp_hlay1 = QtWidgets.QHBoxLayout(self.import_gbox)
        self.import_grp_vlay.addLayout(self.import_grp_hlay1)
        self.import_le = QtWidgets.QLineEdit(self.import_gbox)
        self.import_le.setPlaceholderText("Browse a FBX file")
        self.import_grp_hlay1.addWidget(self.import_le)
        self.import_browse_pb = QtWidgets.QPushButton(self.import_gbox)
        self.import_browse_pb.setText("...")
        self.import_grp_hlay1.addWidget(self.import_browse_pb)
        self.import_animation_pb = QtWidgets.QPushButton(self.import_gbox)
        self.import_animation_pb.setText("Remap Animation")
        self.import_grp_vlay.addWidget(self.import_animation_pb)

        self.main_vlay.addWidget(self.import_gbox)

        ######3 SIGNALS #######

        self.namespace_combo.currentTextChanged.connect(lambda x: self.tr_tool.set_namespace(x))
        self.namespace_refresh_pb.clicked.connect(self.populate_namespaces)
        self.all_body_pb.clicked.connect(lambda x: self.modifiedSelect(command="selectBody"))
        self.all_face_pb.clicked.connect(lambda x: self.modifiedSelect(command="selectFace"))

        self.all_tweakers_pb.clicked.connect(lambda x: self.modifiedSelect(command="selectTweakers"))

        self.select_mirror_pb.clicked.connect(lambda x: self.modifiedSelect(command="selectMirror"))

        self.copy_mirror_pb.clicked.connect(lambda x: self.tr_tool.mirror_pose(self.mirror_mode_combo.currentText()))
        self.swap_mirror_pb.clicked.connect(lambda x: self.tr_tool.mirror_pose(self.mirror_mode_combo.currentText(), swap=True))
        self.zero_tpose_pb.clicked.connect(self.tr_tool.zero_pose)
        self.reset_tpose_pb.clicked.connect(self.tr_tool.reset_pose)
        self.override_namespace_cb.stateChanged.connect(self.on_override_namespace)

        self.import_browse_pb.clicked.connect(self.on_import_browse)
        self.import_bind_pose_browse_pb.clicked.connect(self.on_import_bind_pose_browse)
        self.import_animation_pb.clicked.connect(self.on_import_animation)

    def on_import_bind_pose_browse(self):
        dlg = QtWidgets.QFileDialog()
        dlg.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        if dlg.exec_():
            selectedroot = os.path.normpath(compatibility.encode(dlg.selectedFiles()[0]))
            self.import_bind_pose_le.setText(selectedroot)

    def on_import_browse(self):
        dlg = QtWidgets.QFileDialog()
        dlg.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        if dlg.exec_():
            # selectedroot = os.path.normpath(unicode(dlg.selectedFiles()[0])).encode("utf-8")
            selectedroot = os.path.normpath(compatibility.encode(dlg.selectedFiles()[0]))
            self.import_le.setText(selectedroot)

    def on_import_animation(self):
        bind_pose_path = os.path.normpath(self.import_bind_pose_le.text())
        fbx_path = os.path.normpath(self.import_le.text())
        if not bind_pose_path or not fbx_path:
            self.feedback.pop_info(title="Missing Fields", text="Please select a bind pose and an animation file")
            return
        self.tr_tool.import_animation(bind_pose_path, fbx_path)

    def on_override_namespace(self):
        state = self.override_namespace_cb.checkState()
        self.namespace_combo.setEnabled(not state)
        self.tr_tool.overrideNamespace = state

        for button in self.dynamicButtons:
            button.setProperty("override", "%s" % str(int(bool(state))))
            button.style().polish(button)

    def populate_namespaces(self):
        self.namespace_combo.clear()
        self.namespace_combo.addItem("")
        self.namespace_combo.addItems(self.tr_tool.get_scene_namespaces())

    def init_values(self):
        self.populate_namespaces()
        self.on_override_namespace()




# class ModifierButton(QtWidgets.QPushButton):
#
# 	def __init__(self, *args, **kwargs):
# 		super(ModifierButton, self).__init__(*args, **kwargs)
# 		self.__isShiftPressed = False
#
# 		self.clicked.connect(self.handleClick)
#
# 	def keyPressEvent(self, event):
# 		super(ModifierButton, self).keyPressEvent(event)
# 		self._processKeyEvent(event)
#
# 	def keyReleaseEvent(self, event):
# 		super(ModifierButton, self).keyReleaseEvent(event)
# 		self._processKeyEvent(event)
#
# 	def _processKeyEvent(self, event):
# 		isShift = event.modifiers() & QtCore.Qt.ShiftModifier
# 		self.__isShiftPressed = bool(isShift)
#
# 	def handleClick(self):
# 		print "Shift pressed?", self.__isShiftPressed