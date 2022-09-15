# notes:
## USE DG Evolution from Preferences -> Settings -> Animation to avoid
## refresh issues with starting frame

# import the api
import maya.OpenMaya as om
import maya.OpenMayaMPx as ompx
import maya.OpenMayaAnim as omanim
import math

name = "rollerMatic"
id = om.MTypeId(0x01032)


# Node definition
class RollerMatic(ompx.MPxNode):
    aInMesh = om.MObject()

    aEnableRolling = om.MObject()

    aStartRotation = om.MObject()

    aInPosition = om.MObject()

    aUpVector = om.MObject()

    aGroundHeight = om.MObject()

    aOutRotation = om.MObject()

    aOutPosition = om.MObject()

    aStartFrame = om.MObject()

    aTime = om.MObject()

    amultiplier = om.MObject()

    curPosition = om.MVector(0,0,0)
    prevPosition = None

    prevRotation = om.MQuaternion(0,0,0,1)

    def __init__(self):
        ompx.MPxNode.__init__(self)

        self.multiplier = 1.0

    def getRot(self, pos, prePos, radius):

        if not prePos:
            return self.prevRotation
        if pos == prePos:
            return self.prevRotation # no distance traveled

        dif = (pos-prePos) # difference in positions
        len = dif.length() # distance traveled
        vec = dif / len # normalized movement vector

        rotax = vec ^ om.MVector(0,-1,0) # rotation axis (cross product)

        pi=3.14159265359
        # Rotation amount in Degrees
        angle = 360*len/((radius) * pi) * self.multiplier

        # build a Quaternion rotation value from rotation vector and angle value
        rotdif = om.MQuaternion(math.radians(angle), rotax)
        # multiply the previous rotation(quat) and current rotation to ADD values
        rot1 = self.prevRotation * rotdif

        return rot1



    def compute(self, plug, dataBlock):
        if plug == RollerMatic.aInMesh or \
                plug == RollerMatic.aInPosition or \
                plug == RollerMatic.aOutRotation:

            self.multiplier = dataBlock.inputValue(RollerMatic.amultiplier).asFloat()

            # get enable attribute
            dataHandleEnable = dataBlock.inputValue(RollerMatic.aEnableRolling)
            statusRolling = dataHandleEnable.asBool()

            # get the input is mesh
            dataHandle = dataBlock.inputValue(RollerMatic.aInMesh)

            inPlug = om.MPlug(self.thisMObject(), RollerMatic.aInMesh)
            connections = om.MPlugArray()
            inPlug.connectedTo(connections, True, False)
            mDependNode = om.MFnDependencyNode(connections[0].node())
            mSelectionList = om.MSelectionList()
            mSelectionList.add(mDependNode.name())
            mDagPath = om.MDagPath()
            mSelectionList.getDagPath(0, mDagPath)
            meshFn = om.MFnMesh(mDagPath)
            bBox = meshFn.boundingBox()
            matrix = mDagPath.exclusiveMatrix()
            bmin = bBox.min() * matrix
            bmax = bBox.max() * matrix

            mDagPath.inclusiveMatrix()

            dif = bmax - bmin # difference in positions
            radius = dif.length() # distance between min and max

            outputHandleRot = dataBlock.outputValue(RollerMatic.aOutRotation)
            outputHandlePos = dataBlock.outputValue(RollerMatic.aOutPosition)

            dataHandleStartRot = dataBlock.inputValue(RollerMatic.aStartRotation)
            startRotationAsFloat = dataHandleStartRot.asFloat3()
            startRotationEuler = om.MEulerRotation(math.radians(startRotationAsFloat[0]), math.radians(startRotationAsFloat[1]), math.radians(startRotationAsFloat[2]))
            # startRotationEuler = om.MEulerRotation((startRotationAsFloat[0]), (startRotationAsFloat[1]), (startRotationAsFloat[2]))

            dataHandleStartFrame = dataBlock.inputValue(RollerMatic.aStartFrame)
            startFrameAsFloat = dataHandleStartFrame.asFloat()

            # get position
            dataHandlePos = dataBlock.inputValue(RollerMatic.aInPosition)
            dataPosAsFloat3 = dataHandlePos.asFloat3()
            self.curPosition = om.MVector(dataPosAsFloat3[0], dataPosAsFloat3[1], dataPosAsFloat3[2])

            # get time
            # dataHandleTime = dataBlock.inputValue(RollerMatic.aTime)
            # time = dataHandleTime.asFloat()

            timeData = dataBlock.inputValue(RollerMatic.aTime)
            tempTime = timeData.asTime()
            time = int(tempTime.asUnits(om.MTime.kFilm))

            if statusRolling:
                # return om.kUnknownParameter

                if time <= startFrameAsFloat:
                    rotationQuat = startRotationEuler.asQuaternion()
                else:
                    rotationQuat = self.getRot(self.curPosition, self.prevPosition, radius)
                # rotationQuat = self.getRot(self.curPosition, self.prevPosition, radius)

                # targetRotationQuat = rotationQuat * startRotationEuler.asQuaternion()
                # rotationEuler = targetRotationQuat.asEulerRotation()
                rotationEuler = rotationQuat.asEulerRotation()
                outputHandleRot.set3Float(math.degrees(rotationEuler.x), math.degrees(rotationEuler.y), math.degrees(rotationEuler.z))
                # outputHandleRot.set3Float((rotationEuler.x), (rotationEuler.y), (rotationEuler.z))

                self.prevRotation = rotationQuat
                self.prevPosition = self.curPosition

            # get current output position y
            dataHandlePosY = dataBlock.inputValue(RollerMatic.aOutPosition)
            prePosY_float = dataHandlePosY.asFloat3()

            # get points in world space
            vertPoints = om.MPointArray()
            meshFn.getPoints(vertPoints, om.MSpace.kWorld)

            dataHandleGH = dataBlock.inputValue(RollerMatic.aGroundHeight)
            groundHeight = -(dataHandleGH.asFloat())

            # get up vector
            dataHandleUpVector = dataBlock.inputValue( RollerMatic.aUpVector)
            upVectorAsFloat3 = dataHandleUpVector.asFloat3()

            # calculate matrix from up vector and position
            vy = om.MVector(upVectorAsFloat3[0], upVectorAsFloat3[1], upVectorAsFloat3[2])
            vy.normalize()
            vx = vy ^ om.MVector(1,0,0)
            vx.normalize()
            vz = vx ^ vy
            vz.normalize()
            vy = (vx ^ vz)
            vy.normalize()

            util = om.MScriptUtil()
            newMatrix = om.MMatrix()

            vpos = om.MVector(self.curPosition[0], -prePosY_float[1] + groundHeight, self.curPosition[2])
            # vpos = om.MVector(self.curPosition[0],  self.curPosition[1], self.curPosition[2])
            # vpos = om.MVector(0, -prePosY_float[1] + groundHeight, 0)
            # matrixList = [vx[0], vx[1], vx[2], -vy[0], -vy[1], -vy[2], -vz[0], -vz[1], -vz[2], 0, vpos[0],
            #               vpos[1], vpos[2], 1]
            matrixList = [vx[0], vx[1], vx[2], 0, -vy[0], -vy[1], -vy[2], 0, vz[0], vz[1], vz[2], 0, vpos[0],
                          vpos[1], vpos[2], 1]
            util.createMatrixFromList(matrixList, newMatrix)
            # newMatrix[0][0] = vx[0]
            # newMatrix[0][1] = vx[1]
            # newMatrix[0][2] = vx[2]
            # newMatrix[1][0] = vy[1]
            # newMatrix[1][1] = vy[2]
            # newMatrix[1][2] = vy[3]
            # newMatrix[2][0] = vz[0]
            # newMatrix[2][1] = vz[1]
            # newMatrix[2][2] = vz[2]
            # newMatrix[3][0] = self.curPosition[0]
            # newMatrix[3][1] = -prePosY_float[1]+groundHeight
            # newMatrix[3][2] = self.curPosition[2]
            # newMatrix[3][3] = 1
            yPosArray = [(vertPoints[v] * newMatrix)[1] for v in range(vertPoints.length())]
            minY = min(yPosArray)
            # self.curPosition = om.MVector(self.curPosition[0], -minY, self.curPosition[2]) * newMatrix
            outputHandlePos.set3Float(self.curPosition[0], -minY, self.curPosition[2])
            # outputHandlePos.set3Float(super_m[0], super_m[1], super_m[2])

            dataBlock.setClean(plug)
        else:
            return om.kUnknownParameter


        #     # # matrix
        #     vy = om.MVector(upVectorAsFloat3[0],upVectorAsFloat3[1],upVectorAsFloat3[2])
        #     vz = om.MVector(0,0,1)
        #
        #     vpos = om.MVector(0,-prePosY_float[1]+groundHeight,0)
        #
        #     vx = (vy^vz)
        #     vy = (vx^vz)
        #     util = om.MScriptUtil()
        #     newMatrix = om.MMatrix()
        #     matrixList = [vx[0],vx[1],vx[2],0, -vy[0],-vy[1],-vy[2],0, -vz[0],-vz[1],-vz[2],0, vpos[0],vpos[1],vpos[2],1]
        #     util.createMatrixFromList(matrixList, newMatrix)
        #
        #     # collect y positions
        #     yPosArray = [(vertPoints[v]*newMatrix)[1] for v in range(vertPoints.length())]
        #     minY = min(yPosArray)
        #
        #     outputHandlePos.set3Float(self.curPosition[0], -minY, self.curPosition[2])
        #
        #     dataBlock.setClean(plug)
        # else:
        #     return om.kUnknownParameter


def creator():
    return ompx.asMPxPtr(RollerMatic())

def initialize():
    tAttr = om.MFnTypedAttribute()
    nAttr = om.MFnNumericAttribute()
    uAttr = om.MFnUnitAttribute()
    #
    # input mesh
    RollerMatic.aInMesh = tAttr.create("inMesh", "in", om.MFnData.kMesh)
    tAttr.setStorable(1)
    RollerMatic.addAttribute(RollerMatic.aInMesh)

    # enable attribute
    RollerMatic.aEnableRolling = nAttr.create("enableRolling", "er", om.MFnNumericData.kBoolean, 1.0)
    nAttr.setKeyable(1)
    RollerMatic.addAttribute(RollerMatic.aEnableRolling)

    # up vector X
    RollerMatic.aUpVectorX = nAttr.create("upVectorX", "upx", om.MFnNumericData.kFloat, 0.0)
    RollerMatic.addAttribute(RollerMatic.aUpVectorX)
    # up vector Y
    RollerMatic.aUpVectorY = nAttr.create("upVectorY", "upy", om.MFnNumericData.kFloat, 1.0)
    RollerMatic.addAttribute(RollerMatic.aUpVectorY)
    # up vector Z
    RollerMatic.aUpVectorZ = nAttr.create("upVectorZ", "upz", om.MFnNumericData.kFloat, 0.0)
    RollerMatic.addAttribute(RollerMatic.aUpVectorZ)

    RollerMatic.aUpVector = nAttr.create("upVector", "up", RollerMatic.aUpVectorX,
                                                    RollerMatic.aUpVectorY,
                                                    RollerMatic.aUpVectorZ)
    nAttr.setStorable(0)
    RollerMatic.addAttribute(RollerMatic.aUpVector)


    # input position
    RollerMatic.aInPositionX = nAttr.create("inPositionX", "ipx", om.MFnNumericData.kFloat, 0.0)
    nAttr.setStorable(0)
    RollerMatic.addAttribute(RollerMatic.aInPositionX)

    RollerMatic.aInPositionY = nAttr.create("inPositionY", "ipy", om.MFnNumericData.kFloat, 0.0)
    nAttr.setStorable(0)
    RollerMatic.addAttribute(RollerMatic.aInPositionY)

    RollerMatic.aInPositionZ = nAttr.create("inPositionZ", "ipz", om.MFnNumericData.kFloat, 0.0)
    nAttr.setStorable(0)
    RollerMatic.addAttribute(RollerMatic.aInPositionZ)
    RollerMatic.aInPosition = nAttr.create("inPosition", "ip", RollerMatic.aInPositionX,
                                                    RollerMatic.aInPositionY,
                                                    RollerMatic.aInPositionZ)
    nAttr.setStorable(0)
    nAttr.setKeyable(1)
    # nAttr.setWritable(1)
    RollerMatic.addAttribute(RollerMatic.aInPosition)

    # starting Frame
    RollerMatic.aStartFrame = nAttr.create("startFrame", "sf", om.MFnNumericData.kFloat, 1.0)
    nAttr.setStorable(0)
    RollerMatic.addAttribute(RollerMatic.aStartFrame)

    # ground Height
    RollerMatic.aGroundHeight = nAttr.create("groundHeight", "gh", om.MFnNumericData.kFloat, 0.0)
    nAttr.setStorable(0)
    RollerMatic.addAttribute(RollerMatic.aGroundHeight)

    # time
    # RollerMatic.aTime = nAttr.create("time", "t", om.MFnNumericData.kFloat, 0.0)
    RollerMatic.aTime = uAttr.create("time", "t", om.MFnUnitAttribute.kTime, 0.0)
    # nAttr.setStorable(0)
    nAttr.setKeyable(1)
    RollerMatic.addAttribute(RollerMatic.aTime)

    # start Rotation
    RollerMatic.aStartRotationX = nAttr.create("startRotationX", "srx", om.MFnNumericData.kFloat, 0.0)
    nAttr.setStorable(0)
    RollerMatic.addAttribute(RollerMatic.aStartRotationX)

    RollerMatic.aStartRotationY = nAttr.create("startRotationY", "sry", om.MFnNumericData.kFloat, 0.0)
    nAttr.setStorable(0)
    RollerMatic.addAttribute(RollerMatic.aStartRotationY)

    RollerMatic.aStartRotationZ = nAttr.create("startRotationZ", "srz", om.MFnNumericData.kFloat, 0.0)
    nAttr.setStorable(0)
    RollerMatic.addAttribute(RollerMatic.aStartRotationZ)
    RollerMatic.aStartRotation = nAttr.create("startRotation", "sr", RollerMatic.aStartRotationX,
                                                    RollerMatic.aStartRotationY,
                                                    RollerMatic.aStartRotationZ)
    nAttr.setStorable(0)
    nAttr.setKeyable(1)
    RollerMatic.addAttribute(RollerMatic.aStartRotation)

    RollerMatic.amultiplier = nAttr.create("multiplier", "m", om.MFnNumericData.kFloat, 1.0)
    nAttr.setStorable(0)
    nAttr.setKeyable(1)
    RollerMatic.addAttribute(RollerMatic.amultiplier)

    # output position
    RollerMatic.aOutPositionX = nAttr.create("outPositionX", "opx", om.MFnNumericData.kFloat, 0.0)
    # nAttr.setStorable(0)
    # nAttr.setWritable(0)
    RollerMatic.addAttribute(RollerMatic.aOutPositionX)

    RollerMatic.aOutPositionY = nAttr.create("outPositionY", "opy", om.MFnNumericData.kFloat, 0.0)
    # nAttr.setStorable(0)
    # nAttr.setWritable(0)
    RollerMatic.addAttribute(RollerMatic.aOutPositionY)

    RollerMatic.aOutPositionZ = nAttr.create("outPositionZ", "opz", om.MFnNumericData.kFloat, 0.0)
    # nAttr.setStorable(0)
    # nAttr.setWritable(0)
    RollerMatic.addAttribute(RollerMatic.aOutPositionZ)

    RollerMatic.aOutPosition = nAttr.create("outPosition", "op", RollerMatic.aOutPositionX,
                                                   RollerMatic.aOutPositionY,
                                                   RollerMatic.aOutPositionZ)
    # nAttr.setStorable(0)
    # nAttr.setKeyable(0)
    # nAttr.setWritable(1)
    RollerMatic.addAttribute(RollerMatic.aOutPosition)


    # output rotation
    RollerMatic.aOutRotationX = nAttr.create("outRotationX", "orx", om.MFnNumericData.kFloat, 0.0)
    # RollerMatic.aOutRotationX = uAttr.create("outRotationX", "orx", uAttr.kAngle, 0.0)
    # nAttr.setStorable(0)
    # nAttr.setWritable(0)
    RollerMatic.addAttribute(RollerMatic.aOutRotationX)

    RollerMatic.aOutRotationY = nAttr.create("outRotationY", "ory", om.MFnNumericData.kFloat, 0.0)
    # RollerMatic.aOutRotationY = uAttr.create("outRotationY", "ory", uAttr.kAngle, 0.0)
    # nAttr.setStorable(0)
    # nAttr.setWritable(0)
    RollerMatic.addAttribute(RollerMatic.aOutRotationY)

    RollerMatic.aOutRotationZ = nAttr.create("outRotationZ", "orz", om.MFnNumericData.kFloat, 0.0)
    # RollerMatic.aOutRotationZ = uAttr.create("outRotationZ", "orz", uAttr.kAngle, 0.0)
    # nAttr.setStorable(0)
    # nAttr.setWritable(0)
    RollerMatic.addAttribute(RollerMatic.aOutRotationZ)

    RollerMatic.aOutRotation = nAttr.create("outRotation", "or", RollerMatic.aOutRotationX, RollerMatic.aOutRotationY, RollerMatic.aOutRotationZ)
    # RollerMatic.aOutRotation = uAttr.create("outRotation", "or", RollerMatic.aOutRotationX, RollerMatic.aOutRotationY, RollerMatic.aOutRotationZ)
    # nAttr.setStorable(0)
    # nAttr.setKeyable(0)
    # nAttr.setWritable(1)
    RollerMatic.addAttribute(RollerMatic.aOutRotation)

    # dependencies
    RollerMatic.attributeAffects(RollerMatic.aInPosition, RollerMatic.aOutPosition)
    RollerMatic.attributeAffects(RollerMatic.aInPosition, RollerMatic.aOutRotation)
    RollerMatic.attributeAffects(RollerMatic.aInMesh, RollerMatic.aOutPosition)
    RollerMatic.attributeAffects(RollerMatic.aInMesh, RollerMatic.aOutRotation)
    RollerMatic.attributeAffects(RollerMatic.aStartRotation, RollerMatic.aOutPosition)
    RollerMatic.attributeAffects(RollerMatic.aStartRotation, RollerMatic.aOutRotation)
    RollerMatic.attributeAffects(RollerMatic.aTime, RollerMatic.aOutPosition)
    RollerMatic.attributeAffects(RollerMatic.aTime, RollerMatic.aOutRotation)
    RollerMatic.attributeAffects(RollerMatic.aGroundHeight, RollerMatic.aOutPosition)
    RollerMatic.attributeAffects(RollerMatic.aGroundHeight, RollerMatic.aOutRotation)
    RollerMatic.attributeAffects(RollerMatic.aEnableRolling, RollerMatic.aOutPosition)
    RollerMatic.attributeAffects(RollerMatic.aEnableRolling, RollerMatic.aOutRotation)
    RollerMatic.attributeAffects(RollerMatic.amultiplier, RollerMatic.aOutPosition)
    RollerMatic.attributeAffects(RollerMatic.amultiplier, RollerMatic.aOutRotation)
    RollerMatic.attributeAffects(RollerMatic.aGroundHeight, RollerMatic.aOutPosition)
    RollerMatic.attributeAffects(RollerMatic.aGroundHeight, RollerMatic.aOutRotation)


def initializePlugin(plugin):
    pluginFn = ompx.MFnPlugin(plugin, "Arda Kutlu", "0.0.1")
    try:
        pluginFn.registerNode(
            name,
            id,
            creator,
            initialize,
                              )
    except:
        om.MGlobal.displayError('Failed to register node: %s' % RollerMatic.name)
        raise

def uninitializePlugin(plugin):
    pluginFn = ompx.MFnPlugin(plugin)

    try:
        pluginFn.deregisterNode(id)
    except:
        om.MGlobal.displayError('Failed to unregister node: %s' % RollerMatic.name)
        raise