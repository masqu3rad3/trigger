from maya import cmds
from trigger.library import functions as extra
from trigger.core import feedback
FEEDBACK = feedback.Feedback(__name__)

class Root(object):
    def __init__(self):
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

    def createRoot(self, build_data=None, inits=None, suffix="", *args, **kwargs):
        """
        This will create a 'mid node' called root. This single joint will act as a socket for other limbs to connect to.
        Args:
            inits: (dictionary or list) This is plural for naming convention only. In fact, the function accepts only one joint. If it is a dictionary, the key must be 'Root' and if it is a list it must contain only a single element
            suffix: (string) Name suffix for the nodes will be created

        Returns: None

        """
        if build_data:
            if len(build_data.keys()) > 1:
                FEEDBACK.throw_error("Root can only have one initial joint")
                return
            rootInit = build_data["Root"]
        elif inits:
            if len(inits) > 1:
                cmds.error("Root can only have one initial joint")
                return
            rootInit = inits[0]
        else:
            FEEDBACK.throw_error("Class needs either build_data or arminits to be constructed")


        suffix=(extra.uniqueName("limbGrp_%s" %(suffix))).replace("limbGrp_", "")

        print("Creating Root %s" %suffix)

        self.scaleGrp = cmds.group(name="scaleGrp_" + suffix, em=True)
        # suffix=(extra.uniqueName("limbGrp_%s" % suffix)).replace("limbGrp_", "")
        self.limbGrp = cmds.group(name="limbGrp_%s" % suffix, em=True)
        cmds.parent(self.scaleGrp, self.nonScaleGrp, self.cont_IK_OFF, self.limbGrp)

        self.scaleConstraints.append(self.scaleGrp)

        defJ_root = cmds.joint(name="jDef_{0}".format(suffix))
        extra.alignTo(defJ_root, rootInit, position=True, rotation=False)

        extra.colorize(defJ_root, self.colorCodes[0])
        self.limbPlug = defJ_root
        self.sockets.append(defJ_root)
        self.deformerJoints.append(defJ_root)