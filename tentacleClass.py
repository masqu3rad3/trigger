import pymel.core as pm
import extraProcedures as extra

reload(extra)

import contIcons as icon

reload(icon)

import twistSplineClass as twistSpline

reload(twistSpline)


class Tentacle(object):

    def __init__(self):
        self.scaleGrp = None
        self.limbPlug = None
        self.nonScaleGrp = None
        self.cont_IK_OFF = None
        self.sockets = []
        self.scaleConstraints = []
        self.anchors = []
        self.anchorLocations = []

    def createTentacle(self, inits, suffix="", resolution=4, dropoff=2.0):
        if not isinstance(inits, list):
            ## parse the dictionary inits into a list
            sRoot=inits.get("Root")
            try:
                tentacles=reversed(inits.get("Tentacle"))
                tentacleEnd = inits.get("TentacleEnd")
                inits = [sRoot] + sorted(tentacles) + [tentacleEnd]
            except:
                tentacleEnd = inits.get("TentacleEnd")
                inits = [sRoot] + [tentacleEnd]

        idCounter = 0
        ## create an unique suffix
        while pm.objExists("scaleGrp_" + "tentacle" + suffix):
            suffix = "%s%s" %(suffix, str(idCounter + 1))

        if (len(inits) < 2):
            pm.error("Insufficient Tentacle Initialization Joints")
            return

        iconSize = extra.getDistance(inits[0], inits[len(inits)-1])
        rootPoint = inits[0].getTranslation(space="world")
        endPoint = inits[-1].getTranslation(space="world")

        ## get the up axis
        axisDict={"x":(1.0,0.0,0.0),"y":(0.0,1.0,0.0),"z":(0.0,0.0,1.0),"-x":(-1.0,0.0,0.0),"-y":(0.0,-1.0,0.0),"-z":(0.0,0.0,-1.0)}
        spineDir = {"x": (-1.0, 0.0, 0.0), "y": (0.0, -1.0, 0.0), "z": (0.0, 0.0, 1.0), "-x": (1.0, 0.0, 0.0), "-y": (0.0, 1.0, 0.0), "-z": (0.0, 0.0, 1.0)}
        if pm.attributeQuery("upAxis", node=inits[0], exists=True):
            try:
                self.upAxis=axisDict[pm.getAttr(inits[0].upAxis).lower()]
            except:
                pm.warning("upAxis attribute is not valid, proceeding with default value (y up)")
                self.upAxis = (0.0, 1.0, 0.0)
        else:
            pm.warning("upAxis attribute of the root node does not exist. Using default value (y up)")
            self.upAxis = (0.0, 1.0, 0.0)
        ## get the mirror axis
        if pm.attributeQuery("mirrorAxis", node=inits[0], exists=True):
            try:
                self.mirrorAxis=axisDict[pm.getAttr(inits[0].mirrorAxis).lower()]
            except:
                pm.warning("mirrorAxis attribute is not valid, proceeding with default value (scene x)")
                self.mirrorAxis= (1.0, 0.0, 0.0)
        else:
            pm.warning("mirrorAxis attribute of the root node does not exist. Using default value (scene x)")
            self.mirrorAxis = (1.0, 0.0, 0.0)

        ## get spine Direction
        if pm.attributeQuery("lookAxis", node=inits[0], exists=True):
            try:
                self.spineDir = spineDir[pm.getAttr(inits[0].lookAxis).lower()]
            except:
                pm.warning("Cannot get spine direction from lookAxis attribute, proceeding with default value (-x)")
                self.spineDir = (-1.0, 0.0, 0.0)
        else:
            pm.warning("lookAxis attribute of the root node does not exist. Using default value (-x) for spine direction")
            self.spineDir = (1.0, 0.0, 0.0)

        #     _____            _             _ _
        #    / ____|          | |           | | |
        #   | |     ___  _ __ | |_ _ __ ___ | | | ___ _ __ ___
        #   | |    / _ \| '_ \| __| '__/ _ \| | |/ _ \ '__/ __|
        #   | |___| (_) | | | | |_| | | (_) | | |  __/ |  \__ \
        #    \_____\___/|_| |_|\__|_|  \___/|_|_|\___|_|  |___/
        #
        #

        tentacle = twistSpline.twistSpline()
        tentacle.createTspline(inits, "spine" + suffix, resolution, dropoff=dropoff)