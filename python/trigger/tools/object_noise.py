import pymel.core as pm
import random
from trigger.ui.Qt import QtWidgets, QtCore
from trigger.ui.qtmaya import get_main_maya_window
from maya import OpenMayaUI as omui

WINDOW_NAME = "Noise Expressions"


def uniqueName(name):
    baseName = name
    idcounter = 0
    while pm.objExists(name):
        name = "%s%s" % (baseName, str(idcounter + 1))
        idcounter = idcounter + 1
    return name


def alignToAlter(node1, node2, mode=0, o=(0, 0, 0)):
    """
    Aligns the first node to the second.
    Args:
        node1: Node to be aligned.
        node2: Target Node.
        mode: Specifies the alignment Mode. Valid Values: 0=position only, 1=Rotation Only, 2=Position and Rotation
        o: Offset Value. Default: (0,0,0)

    Returns:None

    """
    if type(node1) == str:
        node1 = pm.PyNode(node1)

    if type(node2) == str:
        node2 = pm.PyNode(node2)

    if mode == 0:
        ##Position Only
        tempPocon = pm.pointConstraint(node2, node1, mo=False)
        pm.delete(tempPocon)
        # targetLoc = node2.getRotatePivot(space="world")
        # pm.move(node1, targetLoc, a=True, ws=True)

    elif mode == 1:
        ##Rotation Only
        if node2.type() == "joint":
            tempOri = pm.orientConstraint(node2, node1, o=o, mo=False)
            pm.delete(tempOri)
        else:
            targetRot = node2.getRotation()
            pm.rotate(node1, targetRot, a=True, ws=True)

    elif mode == 2:
        ##Position and Rotation
        tempPacon = pm.parentConstraint(node2, node1, mo=False)
        pm.delete(tempPacon)


def objectNoise(node, rotate=True, translate=True, scale=False, randomSeed=True):
    if randomSeed:
        seedVal = random.randint(1, 99999)
    else:
        seedVal = 12345

    # Create noise locator and master controller
    locator = pm.spaceLocator(name=uniqueName("Loc_%s" % node.name()))
    controller = pm.circle(name=uniqueName("cont_loc_%s" % node.name()), nr=(0, 1, 0))[
        0
    ]
    pm.parent(locator, controller)
    alignToAlter(controller, node, mode=2)

    # check if the target object has a parent
    originalParent = pm.listRelatives(node, p=True)
    if len(originalParent) > 0:
        pm.parent(controller, originalParent[0], r=False)
    pm.parent(node, locator)

    # Create rotation noise attributes if rotate flag is set

    pm.addAttr(
        controller,
        longName="seedRND",
        niceName="Seed",
        at="long",
        k=True,
        defaultValue=seedVal,
    )

    if rotate:
        pm.addAttr(
            controller,
            longName="rotationAtt",
            niceName="##ROTATION##",
            at="enum",
            enumName="-------",
            k=True,
        )
        pm.setAttr(controller.rotationAtt, l=True)
        pm.addAttr(
            controller,
            longName="rotSpeed",
            niceName="Overall_Rotation_Speed",
            at="float",
            defaultValue=10,
            k=True,
        )

        pm.addAttr(
            controller,
            longName="xRotType",
            niceName="X_Rotation_Type",
            at="enum",
            enumName="Noise:Sinus:Continuous",
            k=True,
        )
        pm.addAttr(
            controller,
            longName="yRotType",
            niceName="Y_Rotation_Type",
            at="enum",
            enumName="Noise:Sinus:Continuous",
            k=True,
        )
        pm.addAttr(
            controller,
            longName="zRotType",
            niceName="Z_Rotation_Type",
            at="enum",
            enumName="Noise:Sinus:Continuous",
            k=True,
        )

        pm.addAttr(
            controller,
            longName="xRotMult",
            niceName="X_Rotation_Multiplier",
            at="float",
            defaultValue=1,
            k=True,
        )
        pm.addAttr(
            controller,
            longName="yRotMult",
            niceName="Y_Rotation_Multiplier",
            at="float",
            defaultValue=1,
            k=True,
        )
        pm.addAttr(
            controller,
            longName="zRotMult",
            niceName="Z_Rotation_Multiplier",
            at="float",
            defaultValue=1,
            k=True,
        )

        pm.addAttr(
            controller,
            longName="xRotMax",
            niceName="X_Rotation_Max",
            at="float",
            defaultValue=25,
            k=True,
        )
        pm.addAttr(
            controller,
            longName="yRotMax",
            niceName="Y_Rotation_Max",
            at="float",
            defaultValue=25,
            k=True,
        )
        pm.addAttr(
            controller,
            longName="zRotMax",
            niceName="Z_Rotation_Max",
            at="float",
            defaultValue=25,
            k=True,
        )

    if translate:
        pm.addAttr(
            controller,
            longName="positionAtt",
            niceName="##POSITION##",
            at="enum",
            enumName="-------",
            k=True,
        )
        pm.setAttr(controller.positionAtt, l=True)
        pm.addAttr(
            controller,
            longName="posSpeed",
            niceName="Overall_Position_Speed",
            at="float",
            defaultValue=1,
            k=True,
        )

        pm.addAttr(
            controller,
            longName="xPosType",
            niceName="X_Position_Type",
            at="enum",
            enumName="Noise:Sinus",
            k=True,
        )
        pm.addAttr(
            controller,
            longName="yPosType",
            niceName="Y_Position_Type",
            at="enum",
            enumName="Noise:Sinus",
            k=True,
        )
        pm.addAttr(
            controller,
            longName="zPosType",
            niceName="Z_Position_Type",
            at="enum",
            enumName="Noise:Sinus",
            k=True,
        )

        pm.addAttr(
            controller,
            longName="xPosMult",
            niceName="X_Position_Multiplier",
            at="float",
            defaultValue=1,
            k=True,
        )
        pm.addAttr(
            controller,
            longName="yPosMult",
            niceName="Y_Position_Multiplier",
            at="float",
            defaultValue=1,
            k=True,
        )
        pm.addAttr(
            controller,
            longName="zPosMult",
            niceName="Z_Position_Multiplier",
            at="float",
            defaultValue=1,
            k=True,
        )

        pm.addAttr(
            controller,
            longName="xPosMax",
            niceName="X_Position_Max",
            at="float",
            defaultValue=1,
            k=True,
        )
        pm.addAttr(
            controller,
            longName="yPosMax",
            niceName="Y_Position_Max",
            at="float",
            defaultValue=1,
            k=True,
        )
        pm.addAttr(
            controller,
            longName="zPosMax",
            niceName="Z_Position_Max",
            at="float",
            defaultValue=1,
            k=True,
        )

    if scale:
        pm.addAttr(
            controller,
            longName="scaleAtt",
            niceName="##SCALE##",
            at="enum",
            enumName="-------",
            k=True,
        )
        pm.setAttr(controller.scaleAtt, l=True)
        pm.addAttr(
            controller,
            longName="scaSpeed",
            niceName="Overall_Scale_Speed",
            at="float",
            defaultValue=1,
            k=True,
        )

        pm.addAttr(
            controller,
            longName="xScaType",
            niceName="X_Scale_Type",
            at="enum",
            enumName="Noise:Sinus",
            k=True,
        )
        pm.addAttr(
            controller,
            longName="yScaType",
            niceName="Y_Scale_Type",
            at="enum",
            enumName="Noise:Sinus",
            k=True,
        )
        pm.addAttr(
            controller,
            longName="zScaType",
            niceName="Z_Scale_Type",
            at="enum",
            enumName="Noise:Sinus",
            k=True,
        )

        pm.addAttr(
            controller,
            longName="xScaMult",
            niceName="X_Scale_Multiplier",
            at="float",
            defaultValue=1,
            k=True,
        )
        pm.addAttr(
            controller,
            longName="yScaMult",
            niceName="Y_Scale_Multiplier",
            at="float",
            defaultValue=1,
            k=True,
        )
        pm.addAttr(
            controller,
            longName="zScaMult",
            niceName="Z_Scale_Multiplier",
            at="float",
            defaultValue=1,
            k=True,
        )

        pm.addAttr(
            controller,
            longName="xScaMax",
            niceName="X_Scale_Max",
            at="float",
            defaultValue=1,
            k=True,
        )
        pm.addAttr(
            controller,
            longName="yScaMax",
            niceName="Y_Scale_Max",
            at="float",
            defaultValue=1,
            k=True,
        )
        pm.addAttr(
            controller,
            longName="zScaMax",
            niceName="Z_Scale_Max",
            at="float",
            defaultValue=1,
            k=True,
        )

        pm.addAttr(
            controller,
            longName="uniformScale",
            niceName="Uniform_Scale",
            at="enum",
            enumName="True:False",
            k=True,
        )

    exp = """
    $seedRND= {0}.seedRND;
    seed $seedRND;
    $geoRandomX=rand(1000);;
    $geoRandomY=rand(1000);
    $geoRandomZ=rand(1000);;
    """.format(
        controller
    )

    if rotate:
        noiseExpRot = """
        $rotSpeed={0}.rotSpeed;
        $xRotType={0}.xRotType;
        $xRotMult={0}.xRotMult;
        $xRotMax={0}.xRotMax;
        $yRotType={0}.yRotType;
        $yRotMult={0}.yRotMult;
        $yRotMax={0}.yRotMax;
        $zRotType={0}.zRotType;
        $zRotMult={0}.zRotMult;
        $zRotMax={0}.zRotMax;

        if ($xRotType==0)//Noise Movement
        {{{1}.rotateX=(noise((time*$rotSpeed+$geoRandomX)*($xRotMult)))*$xRotMax;}}
        if ($xRotType==1)//Sinus Movement
        {{{1}.rotateX=(sin((time*$rotSpeed+$geoRandomX)*($xRotMult)))*$xRotMax;}}
        if ($xRotType==2)//Continuous Movement
        {{{1}.rotateX=((time*5*($rotSpeed*$xRotMult)));}}
        if ($yRotType==0)//Noise Movement
        {{{1}.rotateY=(noise((time*$rotSpeed+$geoRandomY)*($yRotMult)))*$yRotMax;}}
        if ($yRotType==1)//Sinus Movement
        {{{1}.rotateY=(sin((time*$rotSpeed+$geoRandomY)*($yRotMult)))*$yRotMax;}}
        if ($yRotType==2)//Continuous Movement
        {{{1}.rotateY=((time*5*($rotSpeed*$yRotMult)));}}
        if ($zRotType==0)//Noise Movement
        {{{1}.rotateZ=(noise((time*$rotSpeed+$geoRandomZ)*($zRotMult)))*$zRotMax;}}
        if ($zRotType==1)//Sinus Movement
        {{{1}.rotateZ=(sin((time*$rotSpeed+$geoRandomZ)*($zRotMult)))*$zRotMax;}}
        if ($zRotType==2)//Continuous Movement
        {{{1}.rotateZ=((time*5*($rotSpeed*$zRotMult)));}}
        """.format(
            controller, locator
        )

        exp += noiseExpRot

    if translate:
        noiseExpPos = """
        $posSpeed={0}.posSpeed;
        $xPosType={0}.xPosType;
        $xPosMult={0}.xPosMult;
        $xPosMax={0}.xPosMax;
        $yPosType={0}.yPosType;
        $yPosMult={0}.yPosMult;
        $yPosMax={0}.yPosMax;
        $zPosType={0}.zPosType;
        $zPosMult={0}.zPosMult;
        $zPosMax= {0}.zPosMax;
        
        if ($xPosType==0)//Noise Movement
        {{{1}.translateX=(noise((time*$posSpeed+$geoRandomX)*($xPosMult)))*$xPosMax;}}
        if ($xPosType==1)//Sinus Movement
        {{{1}.translateX=(sin((time*$posSpeed+$geoRandomX)*($xPosMult)))*$xPosMax;}}
        if ($yPosType==0)//Noise Movement
        {{{1}.translateY=(noise((time*$posSpeed+$geoRandomY)*($yPosMult)))*$yPosMax;}}
        if ($yPosType==1)//Sinus Movement
        {{{1}.translateY=(sin((time*$posSpeed+$geoRandomY)*($yPosMult)))*$yPosMax;}}
        if ($zPosType==0)//Noise Movement
        {{{1}.translateZ=(noise((time*$posSpeed+$geoRandomZ)*($zPosMult)))*$zPosMax;}}
        if ($zPosType==1)//Sinus Movement
        {{{1}.translateZ=(sin((time*$posSpeed+$geoRandomZ)*($zPosMult)))*$zPosMax;}}
        """.format(
            controller, locator
        )
        exp += noiseExpPos

    if scale:
        noiseExpPos = """
        $scaSpeed={0}.scaSpeed;
        $xScaType={0}.xScaType;
        $xScaMult={0}.xScaMult;
        $xScaMax={0}.xScaMax;
        $yScaType={0}.yScaType;
        $yScaMult={0}.yScaMult;
        $yScaMax={0}.yScaMax;
        $zScaType={0}.zScaType;
        $zScaMult={0}.zScaMult;
        $zScaMax= {0}.zScaMax;
        $sRandX=$geoRandomX;
        $sRandY=$geoRandomY;
        $sRandZ=$geoRandomZ;
        
        if ({0}.uniformScale==0)//if not uniform
        {{
        $sRandX=$geoRandomX;
        $sRandY=$geoRandomX;
        $sRandZ=$geoRandomX;
        }}

        if ($xScaType==0)//Noise Movement
        {{{1}.scaleX=1+(noise((time*$scaSpeed+$sRandX)*($xScaMult)))*$xScaMax;}}
        if ($xScaType==1)//Sinus Movement
        {{{1}.scaleX=1+(sin((time*$scaSpeed+$sRandX)*($xScaMult)))*$xScaMax;}}
        if ($yScaType==0)//Noise Movement
        {{{1}.scaleY=1+(noise((time*$scaSpeed+$sRandY)*($yScaMult)))*$yScaMax;}}
        if ($yScaType==1)//Sinus Movement
        {{{1}.scaleY=1+(sin((time*$scaSpeed+$sRandY)*($yScaMult)))*$yScaMax;}}
        if ($zScaType==0)//Noise Movement
        {{{1}.scaleZ=1+(noise((time*$scaSpeed+$sRandZ)*($zScaMult)))*$zScaMax;}}
        if ($zScaType==1)//Sinus Movement
        {{{1}.scaleZ=1+(sin((time*$scaSpeed+$sRandZ)*($zScaMult)))*$zScaMax;}}
        """.format(
            controller, locator
        )
        exp += noiseExpPos

    pm.expression(string=exp, name="%s_noiseExp" % node)


class ObjectNoiseUI(QtWidgets.QDialog):
    def __init__(self):
        for entry in QtWidgets.QApplication.allWidgets():
            try:
                if entry.objectName() == WINDOW_NAME:
                    entry.close()
            except (AttributeError, TypeError):
                pass
        parent = get_main_maya_window()
        super(ObjectNoiseUI, self).__init__(parent=parent)

        self.setWindowTitle(WINDOW_NAME)
        self.setObjectName(WINDOW_NAME)
        self.buildUI()

    def buildUI(self):
        self.setObjectName(WINDOW_NAME)
        self.resize(140, 180)
        self.setWindowTitle(WINDOW_NAME)
        self.rotation_checkBox = QtWidgets.QCheckBox(self)
        self.rotation_checkBox.setGeometry(QtCore.QRect(30, 20, 70, 17))
        self.rotation_checkBox.setText(("Rotation"))
        self.rotation_checkBox.setChecked(True)
        self.rotation_checkBox.setObjectName(("rotation_checkBox"))
        self.position_checkBox = QtWidgets.QCheckBox(self)
        self.position_checkBox.setGeometry(QtCore.QRect(30, 50, 70, 17))
        self.position_checkBox.setText(("Position"))
        self.position_checkBox.setChecked(True)
        self.position_checkBox.setObjectName(("scale_checkBox"))
        self.scale_checkBox = QtWidgets.QCheckBox(self)
        self.scale_checkBox.setGeometry(QtCore.QRect(30, 80, 70, 17))
        self.scale_checkBox.setText(("Scale"))
        self.scale_checkBox.setChecked(False)
        self.scale_checkBox.setObjectName(("scale_checkBox"))
        self.randomseed_checkBox = QtWidgets.QCheckBox(self)
        self.randomseed_checkBox.setGeometry(QtCore.QRect(30, 110, 91, 17))
        self.randomseed_checkBox.setText(("Random Seed"))
        self.randomseed_checkBox.setChecked(True)
        self.randomseed_checkBox.setObjectName(("randomseed_checkBox"))
        self.createnoise_pushButton = QtWidgets.QPushButton(self)
        self.createnoise_pushButton.setGeometry(QtCore.QRect(30, 140, 81, 23))
        self.createnoise_pushButton.setText(("Create Noise"))
        self.createnoise_pushButton.setObjectName(("createnoise_pushButton"))

        self.createnoise_pushButton.clicked.connect(self.onCreateNoise)

    def onCreateNoise(self):
        with pm.UndoChunk():
            selection = pm.ls(sl=True)
            if len(selection) == 0:
                pm.warning("You need to select at least one object - Nothing happened")
            for i in selection:
                objectNoise(
                    i,
                    translate=self.position_checkBox.isChecked(),
                    rotate=self.rotation_checkBox.isChecked(),
                    scale=self.scale_checkBox.isChecked(),
                    randomSeed=self.randomseed_checkBox.isChecked(),
                )
