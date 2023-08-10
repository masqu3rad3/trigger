"""Builds the kinematics starting from the given root and for all descendants"""
import os
from maya import cmds
from trigger.core import filelog
from trigger.core import database
from trigger.core.decorators import suppress_warnings
from trigger.core.compatibility import is_string
from trigger.library import functions, naming, joint
from trigger.library import attribute
from trigger.library import api

from trigger.base import session

from trigger import modules
import trigger.utils.space_switcher as anchor_maker

from trigger.actions import master

from trigger.ui.Qt import QtWidgets, QtGui  # for progressbar
from trigger.ui.widgets.browser import BrowserButton, FileLineEdit

log = filelog.Filelog(logname=__name__, filename="trigger_log")
db = database.Database()
#
ACTION_DATA = {
    "guides_file_path": "",
    "guide_roots": [],
    "auto_switchers": True,
    "extra_switchers": [],  # list of dictionaries?
    "after_creation": 2,  # 0=nothing 1=hide 2=delete
    "multi_selectionSets": False,
}


class Kinematics(object):
    def __init__(
        self, root_joints=None, progress_bar=None, create_switchers=True, rig_name=None
    ):
        super(Kinematics, self).__init__()
        self.progress_bar = progress_bar
        if self.progress_bar:
            self.progress_bar.setProperty("value", 0)

        self.autoSwitchers = create_switchers
        self.root_joints = root_joints if type(root_joints) == list else [root_joints]
        self.module_dict = {
            mod: eval("modules.{0}.LIMB_DATA".format(mod)) for mod in modules.__all__
        }
        self.validRootList = [
            values["members"][0] for values in self.module_dict.values()
        ]

        self.shoulderDist = 1.0
        self.hipDist = 1.0

        self.scaleRoot = None
        self.anchorLocations = []
        self.anchors = []
        self.extraSwitchers = []
        self.allSocketsList = []
        self.riggedLimbList = []
        self.totalDefJoints = []
        self.afterlife = 2  # valid values are keep=0, hide=1, delete=2
        self.multi_selectionSets = False
        self.guides_file_path = None
        self.limbCreationList = []
        self.rootGroup = None

        self.rig_name = rig_name if rig_name else "trigger"

    def feed(self, action_data):
        """Mandatory Function for builder- feeds with the Action Data from builder"""
        self.guides_file_path = action_data.get("guides_file_path")
        self.root_joints = action_data.get("guide_roots")
        if not self.root_joints:
            self.root_joints = []
        self.autoSwitchers = action_data.get("auto_switchers")
        self.extraSwitchers = action_data.get("extra_switchers")
        self.afterlife = action_data.get("after_creation")
        self.multi_selectionSets = action_data.get("multi_selectionSets", False)

    def action(self):
        root_grp = "trigger_grp"
        if self.guides_file_path:
            guides_handler = session.Session()
            guides_handler.load_session(self.guides_file_path)
        if not cmds.objExists(root_grp):
            master.Master().action()
        for root_joint in self.root_joints:
            self.collect_guides_info(root_joint)
            self.limbCreationList = self.get_limb_hierarchy(root_joint)
            self.create_limbs(self.limbCreationList)

            if self.autoSwitchers and self.anchorLocations:
                for anchor in self.anchors:
                    anchor_maker.create_space_switch(
                        anchor[0],
                        self.anchorLocations,
                        mode=anchor[1],
                        defaultVal=anchor[2],
                        listException=anchor[3],
                        skip_errors=True,
                    )

            if self.afterlife == 1:  # hide guides
                cmds.hide(root_joint)
            elif self.afterlife == 2:  # delete guides
                functions.delete_object(root_joint)

    def save_action(self, *args, **kwargs):
        """Mandatory Method"""
        # kinematics action does not have a save action, it only uses guide data
        pass

    @staticmethod
    def ui(ctrl, layout, handler, *args, **kwargs):
        """Mandatory Method"""
        guides_handler = session.Session()

        file_path_lbl = QtWidgets.QLabel(text="File Path:")
        file_path_h_lay = QtWidgets.QHBoxLayout()
        file_path_le = QtWidgets.QLineEdit()
        file_path_le = FileLineEdit()
        file_path_h_lay.addWidget(file_path_le)
        browse_path_pb = BrowserButton(
            update_widget=file_path_le,
            mode="openFile",
            filterExtensions=["Trigger Guide Files (*.trg)"],
        )
        file_path_h_lay.addWidget(browse_path_pb)
        layout.addRow(file_path_lbl, file_path_h_lay)

        guide_roots_lbl = QtWidgets.QLabel(text="Guide Roots:")
        guide_roots_h_lay = QtWidgets.QHBoxLayout()
        guide_roots_le = QtWidgets.QLineEdit()
        guide_roots_h_lay.addWidget(guide_roots_le)
        get_guide_roots_pb = QtWidgets.QPushButton(text="Get")
        guide_roots_h_lay.addWidget(get_guide_roots_pb)
        layout.addRow(guide_roots_lbl, guide_roots_h_lay)

        create_auto_sw_lbl = QtWidgets.QLabel(text="Create Auto Switchers:")
        create_auto_sw_cb = QtWidgets.QCheckBox()
        layout.addRow(create_auto_sw_lbl, create_auto_sw_cb)

        after_action_lbl = QtWidgets.QLabel(text="After Action:")
        after_action_combo = QtWidgets.QComboBox()
        after_action_combo.addItems(["Do Nothing", "Hide Guides", "Delete Guides"])
        layout.addRow(after_action_lbl, after_action_combo)

        multi_selection_sets_lbl = QtWidgets.QLabel(text="Selection Sets")
        multi_selection_sets_cb = QtWidgets.QCheckBox()
        layout.addRow(multi_selection_sets_lbl, multi_selection_sets_cb)

        # make connections with the controller object
        ctrl.connect(file_path_le, "guides_file_path", str)
        ctrl.connect(guide_roots_le, "guide_roots", list)
        ctrl.connect(create_auto_sw_cb, "auto_switchers", bool)
        ctrl.connect(after_action_combo, "after_creation", int)
        ctrl.connect(multi_selection_sets_cb, "multi_selectionSets", bool)

        ctrl.update_ui()

        def get_roots_menu():
            if file_path_le.text():
                if not os.path.isfile(file_path_le.text()):
                    log.error("Guides file does not exist")

                list_of_roots = list(
                    guides_handler.get_roots_from_file(file_path=file_path_le.text())
                )
                zort_menu = QtWidgets.QMenu()
                menu_actions = [QtWidgets.QAction(str(root)) for root in list_of_roots]
                zort_menu.addActions(menu_actions)
                for defo, menu_action in zip(list_of_roots, menu_actions):
                    menu_action.triggered.connect(
                        lambda ignore=defo, item=defo: add_root(str(item))
                    )

                zort_menu.exec_((QtGui.QCursor.pos()))

        def add_root(root):
            current_roots = guide_roots_le.text()
            if root in current_roots:
                log.warning("%s is already in the list" % root)
                return
            new_roots = (
                root if not current_roots else "{0}; {1}".format(current_roots, root)
            )
            guide_roots_le.setText(new_roots)
            ctrl.update_model()

        # Signals
        file_path_le.textChanged.connect(lambda x=0: ctrl.update_model())
        browse_path_pb.clicked.connect(lambda x=0: ctrl.update_model())
        browse_path_pb.clicked.connect(
            file_path_le.validate
        )  # to validate on initial browse result
        guide_roots_le.editingFinished.connect(lambda x=0: ctrl.update_model())
        get_guide_roots_pb.clicked.connect(get_roots_menu)
        create_auto_sw_cb.stateChanged.connect(lambda x=0: ctrl.update_model())
        after_action_combo.currentIndexChanged.connect(lambda x=0: ctrl.update_model())
        multi_selection_sets_cb.stateChanged.connect(lambda x=0: ctrl.update_model())

    def collect_guides_info(self, root_node):
        """
        Collects all the joints under the rootNode hierarchy
        Args:
            root_node: (string) All the hiearchy under this will be collected

        Returns: None

        """
        l_hip, r_hip, l_shoulder, r_shoulder = [None, None, None, None]
        all_joints = cmds.listRelatives(root_node, type="joint", allDescendents=True)
        all_joints = [] if not all_joints else all_joints
        # all_fingers = []
        for jnt in all_joints:
            limb_name, limb_type, limb_side = joint.identify(jnt, self.module_dict)
            if limb_name == "Hip" and limb_side == "L":
                l_hip = jnt
            if limb_name == "Hip" and limb_side == "R":
                r_hip = jnt
            if limb_name == "Shoulder" and limb_side == "L":
                l_shoulder = jnt
            if limb_name == "Shoulder" and limb_side == "R":
                r_shoulder = jnt

        self.hipDist = (
            functions.get_distance(l_hip, r_hip) if l_hip and r_hip else self.hipDist
        )
        self.shoulderDist = (
            functions.get_distance(l_shoulder, r_shoulder)
            if l_shoulder and r_shoulder
            else self.shoulderDist
        )

    def get_limb_hierarchy(self, node, is_root=True, parent_index=None, r_list=None):
        """Checks the given nodes entire hieararchy for roots, and catalogues the root nodes into dictionaries.

        Args:
            node (string): starts checking from this node
            is_root(bool): if True, the given joint is considered as true. Default is True. For recursion.
            parent_index(string): indicates the parent of the current node. Default is none. For recursion.
            r_list(list): If a list is provided, it appends the results into this one. For recursion

        Returns (list): list of root guide nodes in the hierarchy

        """
        if not r_list:
            r_list = []
        if is_root:
            limb_props = self.get_whole_limb(node)
            limb_props.append(parent_index)
            r_list.append(limb_props)

        # Do the same for all children recursively
        children = cmds.listRelatives(node, children=True, type="joint")
        children = children if children else []
        for jnt in children:
            c_id = joint.identify(jnt, self.module_dict)
            if c_id[0] in self.validRootList:
                self.get_limb_hierarchy(
                    jnt, is_root=True, parent_index=node, r_list=r_list
                )
            else:
                self.get_limb_hierarchy(jnt, is_root=False, r_list=r_list)
        return r_list

    def get_whole_limb(self, node):
        multi_guide_jnts = [
            value["multi_guide"]
            for value in self.module_dict.values()
            if value["multi_guide"]
        ]
        limb_dict = {}
        multi_list = []
        limb_name, limb_type, limb_side = joint.identify(node, self.module_dict)

        limb_dict[limb_name] = node
        next_node = node
        z = True
        while z:
            children = cmds.listRelatives(next_node, children=True, type="joint")
            children = [] if not children else children
            if len(children) < 1:
                z = False
            failed_children = 0
            for child in children:
                child_limb_name, child_limb_type, child_limb_side = joint.identify(
                    child, self.module_dict
                )
                if (
                    child_limb_name not in self.validRootList
                    and child_limb_type == limb_type
                ):
                    next_node = child
                    if child_limb_name in multi_guide_jnts:
                        multi_list.append(child)
                        limb_dict[child_limb_name] = multi_list
                    else:
                        limb_dict[child_limb_name] = child
                else:
                    failed_children += 1
            if len(children) == failed_children:
                z = False
        return [limb_dict, limb_type, limb_side]

    @staticmethod
    def get_nearest_socket(init_joint, limb_sockets, excluding=None):
        """
        searches through limbSockets list and gets the nearest socket to the initJoint.
        Args:
            init_joint: (pymel object) initial joint to test the distance
            limb_sockets: (list) limbSockets list
            excluding: (list) list of sockets to exclude from the search

        Returns:

        """
        excluding = excluding or []
        distance_list = []
        for socket in limb_sockets:
            if socket not in excluding:
                distance_list.append(functions.get_distance(socket, init_joint))
        index = distance_list.index(min(distance_list))
        return limb_sockets[index]

    @suppress_warnings
    def create_limbs(
        self,
        limb_creation_list=None,
        add_limb=False,
        root_plug=None,
        parent_socket=None,
        master_cont=None,
        selection_mode=False,
    ):
        """
        Creates limb with the order defined in the limbCreationList (which created with getLimbProperties)
        Args:
            limb_creation_list: (List) The list of initial limb roots for creation
            add_limb: (Boolean) If True, it adds the first node in the selection list to the rig. Default False.
                        The selection order must be with this order:
                        initial Limb root => parent joint of the existing rig => master controller of the existing rig
                        (for the extra attributes and global scaling)
            root_plug: (String) The root node of the limb to be added. Must be a valid root node.
            parent_socket: (String) The parent socket of the limb to be added. Must be a valid socket.
            master_cont: (String) The master controller of the rig to be added. Must be a valid master controller.
            selection_mode: (Boolean) If True, it uses the selection order to add the limb. Default False.

        Returns: None

        """
        if add_limb:  # this means we are adding limbs to the existing rig
            if not selection_mode:
                if root_plug and parent_socket and master_cont:
                    # check the root
                    if (
                        joint.identify(root_plug, self.module_dict)[0]
                        not in self.validRootList
                    ):
                        log.error("root must be a valid root guide node")
                    # limb_creation_list = self.get_limb_hierarchy(root_plug)
                else:
                    log.error(
                        "add_limb mode requires all root, parent and master_cont flags"
                    )
            else:
                if len(cmds.ls(selection=True)) == 3:
                    root_plug, parent_socket, master_cont = cmds.ls(selection=True)
                else:
                    log.error(
                        "Select exactly three nodes. First reference root node then target parent and finally master controller"
                    )
                if (
                    joint.identify(root_plug, self.module_dict)[0]
                    not in self.validRootList
                ):
                    log.error("First selection must be a valid root joint node")

            limb_creation_list = self.get_limb_hierarchy(root_plug)

        j_def_set = None

        if not self.multi_selectionSets:
            cmds.select(clear=True)
            if not cmds.objExists("def_jointsSet_%s" % self.rig_name):
                j_def_set = cmds.sets(name="def_jointsSet_%s" % self.rig_name)
            else:
                j_def_set = "def_jointsSet_%s" % self.rig_name

        total_limb_count = len(limb_creation_list)
        limb_counter = 0
        for x in limb_creation_list:
            if self.progress_bar:
                limb_counter = limb_counter + 1
                percent = (100 * limb_counter) / total_limb_count
                self.progress_bar.setProperty("value", percent)
                QtWidgets.QApplication.processEvents()

            if x[2] == "R":
                _side_val = "R"
                color_codes = [
                    db.userSettings.majorRightColor,
                    db.userSettings.minorRightColor,
                ]
            elif x[2] == "L":
                _side_val = "L"
                color_codes = [
                    db.userSettings.majorLeftColor,
                    db.userSettings.minorLeftColor,
                ]
            else:
                _side_val = "C"
                color_codes = [
                    db.userSettings.majorCenterColor,
                    db.userSettings.majorCenterColor,
                ]

            if self.multi_selectionSets:
                set_name = "def_%s_%s_Set" % (x[1], x[2])
                set_name = naming.unique_name(set_name)
                j_def_set = cmds.sets(name=set_name)

            module = "modules.{0}.{1}".format(x[1], x[1].capitalize())
            flags = "build_data={0}".format(x[0])
            construct_command = "{0}({1})".format(module, flags)

            limb = eval(construct_command)
            limb.colorCodes = color_codes
            limb.createLimb()

            ##############################################
            if add_limb:
                cmds.parent(limb.limbPlug, parent_socket)
                cmds.disconnectAttr(
                    "%s.scale" % parent_socket, "%s.inverseScale" % limb.limbPlug
                )
                # Good parenting / scale connections
                # get the holder group
                self.rootGroup = functions.get_parent(master_cont)
                # Create the holder group if it does not exist
                scale_grp_piv = api.get_world_translation(limb.limbPlug)
                cmds.xform(limb.scaleGrp, pivots=scale_grp_piv, worldSpace=True)
                # pass the attributes

                attribute.attribute_pass(
                    limb.scaleGrp,
                    master_cont,
                    values=True,
                    daisyChain=True,
                    overrideEx=False,
                )
                cmds.parent(limb.limbGrp, self.rootGroup)
                for s_con in limb.scaleConstraints:
                    cmds.scaleConstraint(master_cont, s_con)
            ##############################################
            else:
                if self.autoSwitchers:
                    self.anchorLocations += limb.anchorLocations
                    self.anchors += limb.anchors
                # make them unique lists
                self.anchorLocations = functions.unique_list(self.anchorLocations)

                # gather all sockets in a list
                self.allSocketsList += limb.sockets
                # add the rigged limb to the riggedLimbList
                self.riggedLimbList.append(limb)

                parent_guide_joint = x[3]
                if parent_guide_joint:
                    parent_socket = self.get_nearest_socket(
                        parent_guide_joint, self.allSocketsList, excluding=limb.sockets
                    )

                    cmds.parent(limb.limbPlug, parent_socket)
                    try:
                        cmds.disconnectAttr(
                            "%s.scale" % parent_socket,
                            "%s.inverseScale" % limb.limbPlug,
                        )
                    except RuntimeError:
                        pass

                # Good parenting / scale connections
                scale_grp_piv = api.get_world_translation(limb.limbPlug)
                cmds.xform(limb.scaleGrp, pivots=scale_grp_piv, worldSpace=True)

                attribute.attribute_pass(
                    limb.scaleGrp,
                    "pref_cont",
                    values=True,
                    daisyChain=True,
                    overrideEx=False,
                )
                if functions.get_parent(limb.limbGrp) != "trigger_grp":
                    cmds.parent(limb.limbGrp, "trigger_grp")
                for s_con in limb.scaleConstraints:
                    # if this is the root limb, use its values to scale the entire rig
                    if x == limb_creation_list[0]:
                        if not limb.controllers:
                            self.scaleRoot = "pref_cont"
                        else:
                            if is_string(limb.controllers[0]):
                                self.scaleRoot = limb.controllers[0]
                            else:
                                self.scaleRoot = limb.controllers[0].name
                    else:
                        cmds.connectAttr(
                            "%s.s" % self.scaleRoot, "%s.s" % s_con, force=True
                        )
                cmds.connectAttr(
                    "%s.s" % self.scaleRoot, "%s.s" % limb.scaleGrp, force=True
                )
                for s_attr in "xyz":
                    cmds.setAttr(
                        "{0}.s{1}".format(self.scaleRoot, s_attr),
                        edit=True,
                        keyable=True,
                        lock=False,
                    )
            self.totalDefJoints += limb.deformerJoints
            if j_def_set:
                cmds.sets(limb.deformerJoints, addElement=j_def_set)
