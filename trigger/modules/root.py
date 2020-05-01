from maya import cmds

from trigger.core import settings
from trigger.library import functions as extra
from trigger.core import feedback
FEEDBACK = feedback.Feedback(__name__)

class Root(settings.Settings):
    def __init__(self, build_data=None, inits=None, suffix="", *args, **kwargs):
        super(Root, self).__init__()
        if build_data:
            if len(build_data.keys()) > 1:
                FEEDBACK.throw_error("Root can only have one initial joint")
                return
            self.rootInit = build_data["Root"]
        elif inits:
            if len(inits) > 1:
                cmds.error("Root can only have one initial joint")
                return
            self.rootInit = inits[0]
        else:
            FEEDBACK.throw_error("Class needs either build_data or inits to be constructed")

        self.suffix=(extra.uniqueName("limbGrp_%s" %(suffix))).replace("limbGrp_", "")
        self.limbGrp = None
        self.scaleGrp = None
        self.limbPlug = None
        self.nonScaleGrp = None
        self.cont_IK_OFF = None
        self.sockets = []
        self.scaleConstraints = []
        self.anchors = []
        self.anchorLocations = []
        self.deformerJoints = []
        self.colorCodes = []

    def createLimb(self):
        """
        This will create a 'mid node' called root. This single joint will act as a socket for other limbs to connect to.
        Args:
            inits: (dictionary or list) This is plural for naming convention only. In fact, the function accepts only one joint. If it is a dictionary, the key must be 'Root' and if it is a list it must contain only a single element
            suffix: (string) Name suffix for the nodes will be created

        Returns: None

        """
        FEEDBACK.info("Creating Root %s" %self.suffix)

        self.scaleGrp = cmds.group(name="scaleGrp_%s" % self.suffix, em=True)
        # suffix=(extra.uniqueName("limbGrp_%s" % suffix)).replace("limbGrp_", "")
        self.limbGrp = cmds.group(name="limbGrp_%s" % self.suffix, em=True)
        cmds.parent(self.scaleGrp, self.nonScaleGrp, self.cont_IK_OFF, self.limbGrp)

        self.scaleConstraints.append(self.scaleGrp)

        FEEDBACK.warning("ANAN", self.rootInit)
        defJ_root = cmds.joint(name="jDef_%s" % self.suffix)
        extra.alignTo(defJ_root, self.rootInit, position=True, rotation=False)

        extra.colorize(defJ_root, self.colorCodes[0])
        self.limbPlug = defJ_root
        self.sockets.append(defJ_root)
        self.deformerJoints.append(defJ_root)