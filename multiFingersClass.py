import pymel.core as pm
import extraProcedures as extra

reload(extra)
import contIcons as icon

reload(icon)
import fingerClass as fc

reload(fc)


class multiFingers(object):
    rootMaster = None
    allControllers = []
    defJoints = []

    def rigFingers(self, rootBone, controller, suffix="", mirror=False):
        """
        Rigs all the child fingers (or similar limbs) If there is a thumb finger is present, it the reference Joints name should contain the word 'thumb' in it 
        Args:
            rootBone: (class) Parent of all limbs. For example a hand joint or foot joint.
            controller: (class) Controller object which will hold the custom attributes.
            suffix: (String, optional) This string will be added at the end of the names of the new nodes.
            mirror: If True, the controllers will be mirrored for the right limb.
    
        Returns: List [Master Root, All Controllers' connection group, Deformer joints List]
    
        """
        rootPosition = rootBone.getTranslation(space="world")
        self.rootMaster = pm.spaceLocator(name="handMaster_" + suffix)
        extra.alignTo(self.rootMaster, rootBone, 2)
        pm.select(d=True)
        # deformerJoints=[]
        jDef_Root = pm.joint(name="jDef_fingerRoot_" + suffix, p=rootPosition, radius=1.0)
        self.defJoints.append([jDef_Root])
        extra.alignTo(jDef_Root, rootBone, 2)
        deformerJoints = [[jDef_Root]]
        pm.parent(jDef_Root, self.rootMaster)
        fingerRoots = pm.listRelatives(rootBone, children=True, type="joint")
        # fingerCount=len(fingerRoots)

        self.allControllers= []

        for i in fingerRoots:
            fingerBones = pm.listRelatives(i, children=True, ad=True, type="joint")
            fingerBones.append(i)
            fingerBones = list(reversed(fingerBones))
            if len(fingerBones) > 2:
                finger = fc.finger()
                finger.rigSingleFinger(controller, fingerBones, suffix, mirror=mirror)
                self.allControllers.append(finger.conts)
                pm.parent(finger.fingerRoot, self.rootMaster)
                pm.parent(finger.defJoints[0], jDef_Root)
                self.defJoints.append(finger.defJoints)


