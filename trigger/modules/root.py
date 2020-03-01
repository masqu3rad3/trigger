import pymel.core as pm
import trigger.library.functions as extra

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

    def createRoot(self, inits, suffix=""):
        """
        This will create a 'mid node' called root. This single joint will act as a socket for other limbs to connect to.
        Args:
            inits: (dictionary or list) This is plural for naming convention only. In fact, the function accepts only one joint. If it is a dictionary, the key must be 'Root' and if it is a list it must contain only a single element
            suffix: (string) Name suffix for the nodes will be created

        Returns: None

        """
        if isinstance(inits, dict):
            if len(inits.keys()) > 1:
                pm.error("Root can only have one initial joint")
                return
            rootInit = inits["Root"]
        elif isinstance(inits, list):
            if len(inits) > 1:
                pm.error("Root can only have one initial joint")
                return
            rootInit = inits[0]

        # idCounter = 0
        # ## create an unique suffix
        # while pm.objExists("scaleGrp_" + suffix):
        #     suffix = "%s%s" % (suffix, str(idCounter + 1))

        suffix=(extra.uniqueName("limbGrp_%s" %(suffix))).replace("limbGrp_", "")


        print "Creating Root %s" %suffix

        self.scaleGrp = pm.group(name="scaleGrp_" + suffix, em=True)
        # suffix=(extra.uniqueName("limbGrp_%s" % suffix)).replace("limbGrp_", "")
        self.limbGrp = pm.group(name="limbGrp_%s" % suffix, em=True)
        pm.parent(self.scaleGrp, self.nonScaleGrp, self.cont_IK_OFF, self.limbGrp)

        self.scaleConstraints.append(self.scaleGrp)

        defJ_root = pm.joint(name="jDef_{0}".format(suffix))
        extra.alignTo(defJ_root, rootInit)

        extra.colorize(defJ_root, self.colorCodes[0])
        self.limbPlug = defJ_root
        self.sockets.append(defJ_root)
        self.deformerJoints.append(defJ_root)