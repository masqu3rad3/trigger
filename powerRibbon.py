##Creates a power ribbon joint chain between given locations

################################
######### POWER RIBBON Func ##########
################################

import pymel.core as pm

import extraProcedures as extra
reload(extra)

import contIcons as icon
reload(icon)

class PowerRibbon():

    def __init__(self):
        self.contCurves_ORE = None
        self.contCurve_Start = None
        self.contCurve_End = None
        self.endLock = None
        self.scaleGrp = None
        self.nonScaleGrp = None
        self.attPassCont = None
        self.defJoints = None
        self.noTouchData = None
        self.moveAxis = None

    def createPowerRibbon(self, inits,
                          suffix="",
                          side="C",
                          npResolution=5.0,
                          jResolution=5.0,
                          blResolution=25.0,
                          dropoff=2.0):

        npResolution=1.0*npResolution
        jResolution = 1.0 * jResolution

        ## Make sure the suffix is unique
        # idCounter=0
        # while pm.objExists("scaleGrp_" + suffix):
        #     suffix = "%s%s" % (suffix, str(idCounter + 1))
        suffix=(extra.uniqueName("scaleGrp_%s" %(suffix))).replace("scaleGrp_", "")


        if len(inits)<2:
            pm.error("Power Ribbon setup needs at least 2 initial joints")
            return

        rootPoint = inits[0].getTranslation(space="world")

        ## Create Groups
        self.scaleGrp = pm.group(name="scaleGrp_" + suffix, em=True)
        extra.alignTo(self.scaleGrp, inits[0], 0)
        self.nonScaleGrp = pm.group(name="NonScaleGrp_" + suffix, em=True)

        ## Get the orientation axises
        upAxis, mirroAxis, spineDir = extra.getRigAxes(inits[0])




