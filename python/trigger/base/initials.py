import importlib
from maya import cmds
import maya.api.OpenMaya as om

from trigger.core.decorators import undo
from trigger.core import database

from trigger.library import functions, naming
from trigger.library import joint
from trigger.library import connection
from trigger.library import attribute

from trigger import modules

from trigger.core import filelog

log = filelog.Filelog(logname=__name__, filename="trigger_log")
db = database.Database()


class Initials(object):
    def __init__(self):
        super(Initials, self).__init__()
        self.parseSettings()
        self.projectName = "trigger"

        self.module_dict =  {module_name: data["guide"].limb_data for module_name, data in modules.class_data.items()}
        self.valid_limbs = self.module_dict.keys()
        self.validRootList = [
            values["members"][0] for values in self.module_dict.values()
        ]
        self.non_sided_limbs = [
            limb for limb in self.valid_limbs if not self.module_dict[limb]["sided"]
        ]

    def parseSettings(self):
        parsingDictionary = {
            "+x": (1, 0, 0),
            "+y": (0, 1, 0),
            "+z": (0, 0, 1),
            "-x": (-1, 0, 0),
            "-y": (0, -1, 0),
            "-z": (0, 0, -1),
        }
        self.upVector_asString = db.userSettings.upAxis
        self.lookVector_asString = db.userSettings.lookAxis
        self.mirrorVector_asString = db.userSettings.mirrorAxis

        self.upVector = om.MVector(parsingDictionary[db.userSettings.upAxis])
        self.lookVector = om.MVector(parsingDictionary[db.userSettings.lookAxis])
        self.mirrorVector = om.MVector(parsingDictionary[db.userSettings.mirrorAxis])

        # get transformation matrix:
        self.upVector.normalize()
        self.lookVector.normalize()
        # get the third axis with the cross vector
        side_vect = self.upVector ^ self.lookVector
        # recross in case up and front were not originally orthoganl:
        front_vect = side_vect ^ self.upVector
        # the new matrix is
        self.tMatrix = om.MMatrix(
            (
                (side_vect.x, side_vect.y, side_vect.z, 0),
                (self.upVector.x, self.upVector.y, self.upVector.z, 0),
                (front_vect.x, front_vect.y, front_vect.z, 0),
                (0, 0, 0, 1),
            )
        )

    def autoGet(self, parentBone):
        """
        Gets the mirror of the given object by its name. Returns the left if it finds right and vice versa
        Args:
            parentBone: (string) the object which name will be checked

        Returns: (Tuple) None/String, alignment of the given Obj(string),
                alignment of the returned Obj(string)  Ex.: (bone_left, "left", "right")

        """
        if not cmds.objExists(parentBone):
            log.warning("Joints cannot be identified automatically")
            return None, None, None
        if parentBone.startswith("R_"):
            mirrorBoneName = parentBone.replace("R_", "L_")
            alignmentGiven = "right"
            alignmentReturn = "left"
        elif parentBone.startswith("L_"):
            mirrorBoneName = parentBone.replace("L_", "R_")
            alignmentGiven = "left"
            alignmentReturn = "right"
        elif parentBone.startswith("C_"):
            return None, "both", None
        else:
            log.warning("Joints cannot be identified automatically")
            return None, None, None
        if cmds.objExists(mirrorBoneName):
            return mirrorBoneName, alignmentGiven, alignmentReturn
        else:
            # log.warning("cannot find mirror Joint automatically")
            return None, alignmentGiven, None

    @undo
    def initLimb(
        self,
        limb_name,
        whichSide="left",
        constrainedTo=None,
        parentNode=None,
        defineAs=False,
        *args,
        **kwargs
    ):
        if limb_name not in self.valid_limbs:
            log.error("%s is not a valid limb" % limb_name)

        currentselection = cmds.ls(sl=True)

        ## Create the holder group if it does not exist
        holderGroup = "{0}_refGuides".format(self.projectName)
        if not cmds.objExists(holderGroup):
            holderGroup = cmds.group(name=holderGroup, em=True)

        ## skip side related stuff for no-side related limbs
        if limb_name in self.non_sided_limbs:
            whichSide = "c"
            side = "C"
        else:
            ## check validity of side arguments
            valid_sides = ["left", "right", "center", "both", "auto"]
            if whichSide not in valid_sides:
                # log.error(
                #     "side argument '%s' is not valid. Valid arguments are: %s" % (whichSide, valid_sides))
                raise ValueError
            if (
                len(cmds.ls(sl=True, type="joint")) != 1
                and whichSide == "auto"
                and defineAs == False
            ):
                log.warning("You need to select a single joint to use Auto method")
                return
            ## get the necessary info from arguments
            if whichSide == "left":
                side = "L"
            elif whichSide == "right":
                side = "R"
            else:
                side = "C"

        limb_group_name = naming.parse([limb_name], side=side)
        limb_group_name = naming.unique_name(
            "{}_guides".format(limb_group_name), suffix="_guides"
        )
        # limb_group_name = limb_group_name.replace("_guides", "")
        # strip the side and suffix and get the name of the limb
        limb_name_parts = limb_group_name.split("_")[:-1]  # don't include the suffix
        # remove the side and suffix
        limb_name_parts = [
            part for part in limb_name_parts if part not in ["L", "R", "C", "grp"]
        ]
        unique_limb = "_".join(limb_name_parts)

        ## if defineAs is True, define the selected joints as the given limb instead creating new ones.
        if defineAs:
            # TODO: AUTO argument can be included by running a seperate method to determine the side of the root joint according to the matrix
            construct_command = "modules.{0}.Guides(suffix='{1}', side='{2}')".format(
                limb_name, unique_limb, side
            )
            guide = eval(construct_command)
            guide.convertJoints(currentselection)
            self.adjust_guide_display(guide)
            return

        if not parentNode:
            if cmds.ls(selection=True, type="joint"):
                j = cmds.ls(selection=True)[-1]
                try:
                    if joint.identify(j, self.module_dict)[1] in self.valid_limbs:
                        masterParent = cmds.ls(sl=True)[-1]
                    else:
                        masterParent = None
                except KeyError:
                    masterParent = None
            else:
                masterParent = None
        else:
            masterParent = parentNode
        if whichSide == "both":
            locators1, jnt_dict_side1 = self.initLimb(limb_name, "left", **kwargs)
            locators2, jnt_dict_side2 = self.initLimb(
                limb_name, "right", constrainedTo=locators1, **kwargs
            )
            jnt_dict_side1.update(jnt_dict_side2)
            return (locators1 + locators2), jnt_dict_side1
        if whichSide == "auto" and masterParent:
            mirrorParent, givenAlignment, returnAlignment = self.autoGet(masterParent)
            locators1, jnt_dict_side1 = self.initLimb(
                limb_name, givenAlignment, **kwargs
            )
            if mirrorParent:
                locators2, jnt_dict_side2 = self.initLimb(
                    limb_name,
                    returnAlignment,
                    constrainedTo=locators1,
                    parentNode=mirrorParent,
                    **kwargs
                )
                total_locators = locators1 + locators2
                jnt_dict_side1.update(jnt_dict_side2)
            else:
                total_locators = locators1
            return total_locators, jnt_dict_side1

        limb_group = cmds.group(empty=True, name=limb_group_name)
        cmds.parent(limb_group, holderGroup)
        cmds.select(clear=True)

        guide = modules.class_data[limb_name]["guide"](side=side, suffix=unique_limb, tMatrix=self.tMatrix, upVector=self.upVector, mirrorVector=self.mirrorVector, lookVector=self.lookVector, **kwargs)
        guide.createGuides()

        self.adjust_guide_display(guide)

        cmds.select(d=True)

        ### Constrain locating

        # loc_grp = cmds.group(name=("locGrp_%s" % unique_limb), em=True)
        loc_grp = cmds.group(
            name=naming.parse([unique_limb, "locators"], side=side, suffix="grp"),
            em=True,
        )
        cmds.setAttr("{0}.v".format(loc_grp), 0)
        locatorsList = []

        for jnt in range(0, len(guide.guideJoints)):
            locator = cmds.spaceLocator(name="loc_%s" % guide.guideJoints[jnt])[0]
            locatorsList.append(locator)
            if constrainedTo:
                functions.align_to(
                    locator, guide.guideJoints[jnt], position=True, rotation=False
                )
                connection.connect_mirror(
                    constrainedTo[jnt],
                    locatorsList[jnt],
                    mirror_axis=self.mirrorVector_asString,
                )

                functions.align_to(
                    guide.guideJoints[jnt], locator, position=True, rotation=False
                )
                cmds.parentConstraint(locator, guide.guideJoints[jnt], mo=True)
                # extra.matrixConstraint(locator, limbJoints[jnt], mo=True)
            else:
                cmds.parentConstraint(guide.guideJoints[jnt], locator, mo=False)
                # extra.matrixConstraint(limbJoints[jnt], locator, mo=False)

            cmds.parent(locator, loc_grp)
        cmds.parent(loc_grp, limb_group)

        ### MOVE THE LIMB TO THE DESIRED LOCATION
        if masterParent:
            if not constrainedTo:
                # align the none constrained near to the selected joint
                functions.align_to(guide.guideJoints[0], masterParent)
                # move it a little along the mirrorAxis
                # move it along offsetvector
                cmds.move(
                    guide.offsetVector[0],
                    guide.offsetVector[1],
                    guide.offsetVector[2],
                    guide.guideJoints[0],
                    relative=True,
                )
            else:
                for jnt in guide.guideJoints:
                    attribute.lock_and_hide(
                        jnt, ["tx", "ty", "tz", "rx", "ry", "rz"], hide=False
                    )
            cmds.parent(guide.guideJoints[0], masterParent)
        else:
            cmds.parent(guide.guideJoints[0], limb_group)
        cmds.select(currentselection)

        return locatorsList, {side: guide.guideJoints}

    def _getMirror(self, vector):
        """Returns reflection of the vector along the mirror axis"""
        return vector - 2 * (vector * self.mirrorVector) * self.mirrorVector

    @undo
    def initHumanoid(self, spineSegments=3, neckSegments=3, fingers=5):
        _, base_dict = self.initLimb("base", "center")
        base = base_dict["C"][0]
        cmds.select(base)
        _, spine_dict = self.initLimb("spine", "auto", segments=spineSegments)
        pelvis = spine_dict["C"][0]
        cmds.setAttr("%s.ty" % pelvis, 14)
        chest = spine_dict["C"][-1]
        cmds.select(pelvis)
        _, leg_dict = self.initLimb("leg", "auto")
        cmds.select(chest)
        _, arm_dict = self.initLimb("arm", "auto")
        _, head_dict = self.initLimb("head", "auto", segments=neckSegments)
        left_hand = arm_dict["L"][-1]
        fingers = []
        for nmb in range(5):
            cmds.select(left_hand)
            _, finger_dict = self.initLimb("finger", whichSide="auto", segments=3)
            # import pdb
            # pdb.set_trace()
            # fingers.append(finger_dict["L"])
            fingers.append(finger_dict)

        thumb_pos_data = [
            (1.1, 0.9, 0.25),
            (0.8, 0.0, 0.0),
            (0.55, 0.0, 0.00012367864829724757),
            (0.45, 0.0, 0.0),
        ]
        thumb_rot_data = [
            (31.0, 45.0, 3.0000000000000004),
            (-1.0, -2.0, 17.0),
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0),
        ]
        index_pos_data = [
            (2.0, 0.55, 0.0),
            (1.0, 0.0, 0.0),
            (0.65, 0.0, 0.0),
            (0.6, 0.0, 0.0),
        ]
        index_rot_data = [
            (1.0, 17.0, -3.0000000000000004),
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0),
        ]
        middle_pos_data = [
            (2.0, -0.05, -0.09983537560644819),
            (0.9997424668383346, 0.0, 0.0),
            (0.7, 0.0, 0.0),
            (0.7, 0.0, 0.0),
        ]
        middle_rot_data = [
            (0.0, 7.805352401908098, -0.9999999999999998),
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0),
        ]
        ring_pos_data = [
            (1.8, -0.55, -0.10011550541107042),
            (0.95, 0.0, 0.0),
            (0.7, 0.0, 0.0),
            (0.6, 0.0, 0.0),
        ]
        ring_rot_data = [
            (0.0, -5.0, -1.0),
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0),
        ]
        pinky_pos_data = [
            (1.5, -1.1, 0.0),
            (0.8, 0.0, 0.0),
            (0.5, 0.0, 0.0),
            (0.5, 0.0, 0.0),
        ]
        pinky_rot_data = [
            (0.0, -12.000000000000002, 0.0),
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0),
        ]

        for nmb, member in enumerate(fingers[0]["L"]):
            cmds.xform(
                member,
                absolute=True,
                translation=thumb_pos_data[nmb],
                rotation=thumb_rot_data[nmb],
            )
        cmds.setAttr("%s.fingerType" % fingers[0]["L"][0], 1)
        cmds.setAttr("%s.fingerType" % fingers[0]["R"][0], 1)

        # for nmb, member in enumerate(fingers[0]):
        #     cmds.xform(member, absolute=True, translation=thumb_pos_data[nmb], rotation=thumb_rot_data[nmb])
        # cmds.setAttr("%s.fingerType" % fingers[0][0], 1)

        for nmb, member in enumerate(fingers[1]["L"]):
            cmds.xform(
                member,
                absolute=True,
                translation=index_pos_data[nmb],
                rotation=index_rot_data[nmb],
            )
        cmds.setAttr("%s.fingerType" % fingers[1]["L"][0], 2)
        cmds.setAttr("%s.fingerType" % fingers[1]["R"][0], 2)

        for nmb, member in enumerate(fingers[2]["L"]):
            cmds.xform(
                member,
                absolute=True,
                translation=middle_pos_data[nmb],
                rotation=middle_rot_data[nmb],
            )
        cmds.setAttr("%s.fingerType" % fingers[2]["L"][0], 3)
        cmds.setAttr("%s.fingerType" % fingers[2]["R"][0], 3)

        for nmb, member in enumerate(fingers[3]["L"]):
            cmds.xform(
                member,
                absolute=True,
                translation=ring_pos_data[nmb],
                rotation=ring_rot_data[nmb],
            )
        cmds.setAttr("%s.fingerType" % fingers[3]["L"][0], 4)
        cmds.setAttr("%s.fingerType" % fingers[3]["L"][0], 4)

        for nmb, member in enumerate(fingers[4]["L"]):
            cmds.xform(
                member,
                absolute=True,
                translation=pinky_pos_data[nmb],
                rotation=pinky_rot_data[nmb],
            )
        cmds.setAttr("%s.fingerType" % fingers[4]["L"][0], 5)
        cmds.setAttr("%s.fingerType" % fingers[4]["R"][0], 5)
        return True

    def adjust_guide_display(self, guide_object):
        """Adjusts the display proerties of guid joints according to the settings. Accepts guide object as input"""

        for jnt in guide_object.guideJoints:
            cmds.setAttr("%s.displayLocalAxis" % jnt, 1)
            cmds.setAttr("%s.drawLabel" % jnt, 1)

        if guide_object.side == "C":
            functions.colorize(
                guide_object.guideJoints, db.userSettings.majorCenterColor, shape=False
            )
        if guide_object.side == "L":
            functions.colorize(
                guide_object.guideJoints, db.userSettings.majorLeftColor, shape=False
            )
        if guide_object.side == "R":
            functions.colorize(
                guide_object.guideJoints, db.userSettings.majorRightColor, shape=False
            )

    def get_scene_roots(self):
        """collects the root joints in the scene and returns the dictionary with properties"""
        all_joints = cmds.ls(type="joint")
        # get roots
        guide_roots = [
            jnt for jnt in all_joints if joint.get_joint_type(jnt) in self.validRootList
        ]
        roots_dictionary_list = []
        for jnt in guide_roots:
            # get module name
            try:
                module_name = cmds.getAttr("%s.moduleName" % jnt)
            except ValueError:
                continue
            # get module info
            j_type, limb, side = joint.identify(jnt, self.module_dict)
            roots_dictionary_list.append(
                {
                    "module_name": module_name,
                    "side": side,
                    "root_joint": jnt,
                    "module_type": limb,
                }
            )

        return roots_dictionary_list

    def select_root(self, joint_name):
        cmds.select(joint_name)

    def get_property(self, jnt, attr):
        try:
            return cmds.getAttr("%s.%s" % (jnt, attr))
        except ValueError:
            log.warning("Attribute cannot find %s.%s" % (jnt, attr))
            return False

    def set_property(self, jnt, attr, value):
        if type(value) == int or type(value) == float or type(value) == bool:
            cmds.setAttr("%s.%s" % (jnt, attr), value)
        else:
            cmds.setAttr("%s.%s" % (jnt, attr), value, type="string")

    def get_extra_properties(self, module_type):
        module_type_dict = self.module_dict.get(module_type)
        if module_type_dict:
            return module_type_dict["properties"]

    def get_user_attrs(self, jnt):
        """
        Returns a list of dictionaries for every supported custom attribute

        This is part of guide data collection and this data is going to be used while re-creating guides
        """

        supported_attrs = [
            "long",
            "short",
            "bool",
            "enum",
            "float",
            "double",
            "string",
            "typed",
        ]  # wtf is typed
        list_of_dicts = []
        user_attr_list = cmds.listAttr(jnt, userDefined=True)
        if not user_attr_list:
            return []
        for attr in user_attr_list:
            attr_type = cmds.attributeQuery(attr, node=jnt, at=True)
            if attr_type not in supported_attrs:
                continue
            tmp_dict = {}
            tmp_dict["attr_name"] = cmds.attributeQuery(attr, node=jnt, ln=True)
            tmp_dict["attr_type"] = attr_type
            tmp_dict["nice_name"] = cmds.attributeQuery(attr, node=jnt, nn=True)
            tmp_dict["default_value"] = cmds.getAttr("%s.%s" % (jnt, attr))
            if attr_type == "enum":
                tmp_dict["enum_list"] = cmds.attributeQuery(attr, node=jnt, le=True)[0]
            elif attr_type == "bool":
                pass
            elif attr_type == "typed":
                ## Wtf is "typed" anyway??
                tmp_dict["attr_type"] = "string"
            else:
                try:
                    tmp_dict["min_value"] = cmds.attributeQuery(
                        attr, node=jnt, min=True
                    )[0]
                except RuntimeError:
                    pass
                try:
                    tmp_dict["max_value"] = cmds.attributeQuery(
                        attr, node=jnt, max=True
                    )[0]
                except RuntimeError:
                    pass

            list_of_dicts.append(tmp_dict)
        return list_of_dicts

    def getWholeLimb(self, node):
        multi_guide_jnts = [
            value["multi_guide"]
            for value in self.module_dict.values()
            if value["multi_guide"]
        ]
        limb_dict = {}
        multiList = []
        limb_name, limb_type, limb_side = joint.identify(node, self.module_dict)

        limb_dict[limb_name] = node
        nextNode = node
        z = True
        while z:
            children = cmds.listRelatives(nextNode, children=True, type="joint")
            children = [] if not children else children
            if len(children) < 1:
                z = False
            failedChildren = 0
            for child in children:
                child_limb_name, child_limb_type, child_limb_side = joint.identify(
                    child, self.module_dict
                )
                if (
                    child_limb_name not in self.validRootList
                    and child_limb_type == limb_type
                ):
                    nextNode = child
                    if child_limb_name in multi_guide_jnts:
                        multiList.append(child)
                        limb_dict[child_limb_name] = multiList
                    else:
                        limb_dict[child_limb_name] = child
                else:
                    failedChildren += 1
            if len(children) == failedChildren:
                z = False
        return [limb_dict, limb_type, limb_side]

    @undo
    def test_build(self, root_jnt=None, progress_bar=None):
        kinematics = importlib.import_module("trigger.actions.kinematics")
        if not root_jnt:
            selection = cmds.ls(selection=True)
            if len(selection) == 1:
                root_jnt = selection[0]
            else:
                log.warning("Select a single root_jnt joint")
        if not cmds.objectType(root_jnt, isType="joint"):
            log.error("root_jnt is not a joint")
        root_name, root_type, root_side = joint.identify(root_jnt, self.module_dict)
        if root_name not in self.validRootList:
            log.error("Selected joint is not in the valid Guide Root")

        test_kinematics = kinematics.Kinematics(root_jnt, progress_bar=progress_bar)
        test_kinematics.afterlife = 0
        test_kinematics.action()
        return test_kinematics
