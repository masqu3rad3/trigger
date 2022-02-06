"""Face Camera"""

from maya import cmds
from maya import mel
from trigger.core import io
from trigger.core import filelog
from trigger.core.decorators import tracktime

from trigger.library import transform, selection

from trigger.ui.Qt import QtWidgets
from trigger.ui import custom_widgets
from trigger.ui import feedback

from PySide2 import QtWidgets # temp

log = filelog.Filelog(logname=__name__, filename="trigger_log")


ACTION_DATA = {
    "name": "faceCam",
    "face_mesh": "",
    "parent_node": "",
    "focal_length": 50.0,
    "initial_distance": 7.0,
    "limits": None,
    "limit_multiplier": 1.0,
}

# Name of the class MUST be the capitalized version of file name. eg. morph.py => Morph, split_shapes.py => Split_shapes
class Face_cam(object):
    def __init__(self, *args, **kwargs):
        super(Face_cam, self).__init__()

        # user defined variables
        self.cameraName = "faceCam"
        self.faceMesh = None
        self.parentNode = None
        self.focalLength = 50.0
        self.initialDistance = 7.0,
        self.limitMultiplier = 1.0

        # class variables

    def feed(self, action_data, *args, **kwargs):
        """Mandatory Method - Feeds the instance with the action data stored in actions session"""
        self.cameraName = action_data.get("name", self.cameraName)
        self.faceMesh = action_data.get("face_mesh", self.faceMesh)
        self.parentNode = action_data.get("parent_node", self.parentNode)
        self.focalLength = action_data.get("focal_length", self.focalLength)
        self.initialDistance = action_data.get("initial_distance", self.initialDistance)
        self.limitMultiplier = action_data.get("limit_multiplier", self.limitMultiplier)

    def action(self):
        """Mandatory Method - Execute Action"""
        # everything in this method will be executed automatically.
        # This method does not accept any arguments. all the user variable must be defined to the instance before

        self.create_face_camera(
            name=self.cameraName,
            face_mesh=self.faceMesh,
            parent=self.parentNode,
            focal=self.focalLength,
            distance=self.initialDistance,
            limit_mult=self.limitMultiplier,
            rig_grp="rig_grp",
            hidden=True,
        )

    def save_action(self, file_path=None, *args, **kwargs):
        """Mandatory Method - Save Action"""
        # This method will be called automatically and accepts no arguments.
        # If the action has an option to save files, this method will be used by the UI.
        # Else, this method can stay empty
        pass

    def ui(self, ctrl, layout, handler, *args, **kwargs):
        """
        Mandatory Method - UI setting definitions

        Args:
            ctrl: (model_ctrl) ctrl object instance of /ui/model_ctrl. Updates UI and Model
            layout: (QLayout) The layout object from the main ui. All setting widgets should be added to this layout
            handler: (actions_session) An instance of the actions_session. TRY NOT TO USE HANDLER UNLESS ABSOLUTELY NECESSARY
            *args:
            **kwargs:

        Returns: None

        """

        name_lbl = QtWidgets.QLabel(text="Camera Name")
        name_le = QtWidgets.QLineEdit()
        layout.addRow(name_lbl, name_le)

        face_mesh_lbl = QtWidgets.QLabel(text="Face Mesh")
        face_mesh_leBox = custom_widgets.LineEditBoxLayout(buttonsPosition="right")
        face_mesh_leBox.buttonGet.setText("<")
        face_mesh_leBox.buttonGet.setMaximumWidth(30)
        layout.addRow(face_mesh_lbl, face_mesh_leBox)

        parent_node_lbl = QtWidgets.QLabel(text="Parent Node")
        parent_node_leBox = custom_widgets.LineEditBoxLayout(buttonsPosition="right")
        parent_node_leBox.buttonGet.setText("<")
        parent_node_leBox.buttonGet.setMaximumWidth(30)
        layout.addRow(parent_node_lbl, parent_node_leBox)

        focal_length_lbl = QtWidgets.QLabel(text="Focal Length")
        focal_length_sp = QtWidgets.QDoubleSpinBox()
        layout.addRow(focal_length_lbl, focal_length_sp)

        initial_distance_lbl = QtWidgets.QLabel(text="Initial Distance")
        initial_distance_sp = QtWidgets.QDoubleSpinBox()
        initial_distance_sp.setMinimum(-999999)
        initial_distance_sp.setMaximum(999999)
        layout.addRow(initial_distance_lbl, initial_distance_sp)

        limit_multiplier_lbl = QtWidgets.QLabel(text="Limit Multiplier")
        limit_multiplier_sp = QtWidgets.QDoubleSpinBox()
        layout.addRow(limit_multiplier_lbl, limit_multiplier_sp)

        ctrl.connect(name_le, "name", str)
        ctrl.connect(face_mesh_leBox.viewWidget, "face_mesh", str)
        ctrl.connect(parent_node_leBox.viewWidget, "parent_node", str)
        ctrl.connect(focal_length_sp, "focal_length", float)
        ctrl.connect(focal_length_sp, "focal_length", float)
        ctrl.connect(initial_distance_sp, "initial_distance", float)
        ctrl.connect(limit_multiplier_sp, "limit_multiplier", float)
        ctrl.update_ui()

        def get_selected_face():
            sel, msg = selection.validate(min=1, max=1, meshesOnly=True, transforms=True)
            if sel:
                face_mesh_leBox.viewWidget.setText(sel[0])
                ctrl.update_model()
            else:
                feedback.Feedback().pop_info(title="Selection Error", text=msg, critical=True)

        def get_selected_parent():
            sel, msg = selection.validate(min=1, max=1, transforms=True)
            if sel:
                parent_node_leBox.viewWidget.setText(sel[0])
                ctrl.update_model()
            else:
                feedback.Feedback().pop_info(title="Selection Error", text=msg, critical=True)

        # SIGNALS

        name_le.textChanged.connect(lambda x=0: ctrl.update_model())
        face_mesh_leBox.buttonGet.clicked.connect(get_selected_face)
        parent_node_leBox.buttonGet.clicked.connect(get_selected_parent)
        face_mesh_leBox.viewWidget.textChanged.connect(lambda x=0: ctrl.update_model())
        parent_node_leBox.viewWidget.textChanged.connect(lambda x=0: ctrl.update_model())
        focal_length_sp.valueChanged.connect(lambda x=0: ctrl.update_model())
        initial_distance_sp.valueChanged.connect(lambda x=0: ctrl.update_model())
        limit_multiplier_sp.valueChanged.connect(lambda x=0: ctrl.update_model())

    @staticmethod
    def create_face_camera(
            aim_pos=None,
            face_mesh=None,
            parent=None,
            name="faceCam",
            focal=50.0,
            distance=7.0,
            limits=None,
            rig_grp=None,
            limit_mult=1.0,
            hidden=True,
    ):
        """Creates a face camera locked to the face.
        Args:
            aim_pos (tuple or list): World space position data for initial focus.
            face_mesh (string): If the mesh is defined the center of the object will
            be used as aim_pos and bounding box as limits. aim_pos and limits arguments
            always override.
            parent (string): (optional) The group which will be parent constrained to.
            name (str): Name of the camera. Default is 'faceCam'.
            focal (float): Focal length value in mm.
            distance (float): Initial distance to the face.
            limits (list): (optional) list of min/max tuple values to define the limits. Tuples represent X, Y, Z
                        Example: limits=[(-2,2), (-1,1), (-3,3)]
            rig_grp (string): (optional) The group which will be the camera group tucked away..
            limit_mult (float): multiplies the limits. Makes sense when used with face_mesh bounding box
            hidden (boolean): If True, hides the rig group
        Returns:
            String: camera group transform node
        """

        if face_mesh:
            if not aim_pos:
                aim_pos = cmds.objectCenter(face_mesh, gl=True)
            raw = cmds.xform(face_mesh, q=1, bb=1)
            bounds = [
                (raw[0] - aim_pos[0], raw[3] - aim_pos[0]),
                (raw[1] - aim_pos[1], raw[4] - aim_pos[1]),
                (raw[2] - aim_pos[2], raw[5] - aim_pos[2]),
            ]
        elif limits:
            if face_mesh:
                log.warning("face_mesh flag is overriden by limits")
            bounds = limits
        else:
            bounds = None

        if not aim_pos and not limits:
            log.error("One of the limits, aim_pos or face_mesh arguments must be defined")
            raise Exception("One of the limits, aim_pos or face_mesh arguments must be defined")

        cam = cmds.camera(
            filmFit="Fill",
            horizontalPan=0,
            shutterAngle=144,
            verticalPan=0,
            horizontalFilmOffset=0,
            focalLength=focal,
            centerOfInterest=5,
            motionBlur=0,
            horizontalFilmAperture=0.967717,
            overscan=1,
            panZoomEnabled=0,
            nearClipPlane=0.1,
            farClipPlane=10000,
            orthographic=0,
            verticalFilmOffset=0,
            verticalFilmAperture=0.735238,
            lensSqueezeRatio=1,
            orthographicWidth=30,
            cameraScale=1,
            zoom=1,
        )[0]
        cam = cmds.rename(cam, name)

        mel.eval('cameraMakeNode(3, "")')

        cam_grp = cmds.listRelatives(cam, parent=True)[0]

        _, aim, up = cmds.listRelatives(cam_grp)

        cmds.setAttr("{0}.tz".format(cam), distance)
        cmds.setAttr("{0}.tz".format(up), distance)
        cmds.setAttr("{0}.tz".format(aim), 0)

        cmds.setAttr(
            "{0}.translate".format(cam_grp), aim_pos[0], aim_pos[1], aim_pos[2]
        )
        if bounds:
            for attr, bound in zip("xyz", bounds):
                transform.set_limits(
                    aim,
                    "t{0}".format(attr),
                    bound[0] * limit_mult,
                    bound[1] * limit_mult,
                )

        if parent:
            cmds.parentConstraint(parent, cam_grp, mo=True)
            cmds.scaleConstraint(parent, cam_grp, mo=True)

        cmds.pointConstraint(cam, up, mo=True)
        if rig_grp:
            cmds.parent(cam_grp, rig_grp)
        if hidden:
            cmds.hide(cam_grp)
        return cam_grp
