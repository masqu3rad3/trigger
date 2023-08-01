'''
This plugin was ported to python from C++,
All credits by Anno Schachner
original plugin is here https://github.com/wiremas/tension
https://vimeo.com/315989835
'''

import sys
import maya.api.OpenMaya as om2
import maya.OpenMaya as om

kPluginNodeName = "tensionMap"
origAttrName = "orig"
deformedAttrName = 'deform'
kPluginNodeClassify = 'utility/general'
kPluginNodeId = om2.MTypeId( 0x86018 )


def maya_useNewAPI():
	pass

aOrigShape = om2.MObject()
aDeformedShape = om2.MObject()
aOutShape = om2.MObject()
aColorRamp = om2.MObject()



class tensionMap( om2.MPxNode ):

	isDeformedDirty = True
	isOrigDirty = True
	origEdgeLenArray = []
	deformedEdgeLenArray = []


	def __init__( self ):
		om2.MPxNode.__init__( self )

	def initialize_ramp( self, parentNode, rampObj, index, position, value, interpolation ):

		rampPlug = om2.MPlug( parentNode, rampObj )
		elementPlug = rampPlug.elementByLogicalIndex(index)
		positionPlug = elementPlug.child(0)
		positionPlug.setFloat(position)
		valuePlug = elementPlug.child(1)
		valuePlug.child(0).setFloat(value[0])
		valuePlug.child(1).setFloat(value[1])
		valuePlug.child(2).setFloat(value[2])

		interpPlug = elementPlug.child(2)
		interpPlug.setInt(interpolation)

	def postConstructor( self ):
		self.initialize_ramp( self.thisMObject(), self.aColorRamp, 0, 0.0, om2.MColor(( 0, 1, 0 )), 1 )
		self.initialize_ramp( self.thisMObject(), self.aColorRamp, 1, 0.5, om2.MColor(( 0, 0, 0 )), 1 )
		self.initialize_ramp( self.thisMObject(), self.aColorRamp, 2, 1.0, om2.MColor(( 1, 0, 0 )), 1 )

	def setDependentsDirty( self, dirtyPlug, affectedPlugs ):
		if dirtyPlug.partialName() == deformedAttrName:
			self.isDeformedDirty = True
		else:
			self.isDeformedDirty = False

		if dirtyPlug.partialName() == origAttrName:
			self.isOrigDirty = True
		else:
			self.isOrigDirty = False

	def compute( self, plug, data ):

		if plug == self.aOutShape:
			thisObj = self.thisMObject()
			origHandle = data.inputValue( self.aOrigShape )
			deformedHandle = data.inputValue( self.aDeformedShape )
			outHandle = data.outputValue( self.aOutShape )
			colorAttribute = om2.MRampAttribute( thisObj, self.aColorRamp )

			if self.isOrigDirty:
				self.origEdgeLenArray = self.getEdgeLen( origHandle )
			if self.isDeformedDirty:
				self.deformedEdgeLenArray = self.getEdgeLen( deformedHandle )

			outHandle.copy( deformedHandle )
			outHandle.setMObject( deformedHandle.asMesh() )

			outMesh = outHandle.asMesh()
			meshFn = om2.MFnMesh( outMesh )
			numVerts = meshFn.numVertices
			vertColors = om2.MColorArray()
			vertIds = om2.MIntArray()
			vertColors.setLength( numVerts )
			vertIds.setLength( numVerts )

			for i in range(numVerts):
				delta = 0
				vertColor = om2.MColor()
				if len(self.origEdgeLenArray) == len(self.deformedEdgeLenArray):
					delta = ( ( self.origEdgeLenArray[i] - self.deformedEdgeLenArray[i] ) / self.origEdgeLenArray[i] ) + 0.5
				else:
					delta = 0.5
				vertColor = colorAttribute.getValueAtPosition(delta)
				vertColors.__setitem__(i, vertColor )
				vertIds.__setitem__(i, i)
			meshFn.setVertexColors( vertColors, vertIds )
		data.setClean( plug )

	def getEdgeLen( self, meshHandle ):
		edgeLenArray = []

		meshObj = meshHandle.asMesh()
		edgeIter = om2.MItMeshEdge( meshObj )
		vertIter = om2.MItMeshVertex( meshObj )
		while not vertIter.isDone():
			lengthSum = 0.0
			connectedEdges = om2.MIntArray()
			connectedEdges = vertIter.getConnectedEdges()
			for i in range( connectedEdges.__len__() ):
				edgeIter.setIndex( connectedEdges[i] )
				length = edgeIter.length(om2.MSpace.kWorld)
				lengthSum += length * 1.0

			lengthSum = lengthSum / connectedEdges.__len__()
			edgeLenArray.append( lengthSum )
			vertIter.next()
		return edgeLenArray


def nodeCreator():
	return tensionMap()


def initialize():
	tAttr = om2.MFnTypedAttribute()

	tensionMap.aOrigShape = tAttr.create( origAttrName, origAttrName, om2.MFnMeshData.kMesh )
	tAttr.storable = True

	tensionMap.aDeformedShape = tAttr.create( deformedAttrName, deformedAttrName, om2.MFnMeshData.kMesh )
	tAttr.storable = True

	tensionMap.aOutShape = tAttr.create( "out", "out", om2.MFnMeshData.kMesh )
	tAttr.writable = False
	tAttr.storable = False

	tensionMap.aColorRamp = om2.MRampAttribute().createColorRamp("color", "color")
	tensionMap.addAttribute( tensionMap.aOrigShape )
	tensionMap.addAttribute( tensionMap.aDeformedShape )
	tensionMap.addAttribute( tensionMap.aOutShape )
	tensionMap.addAttribute( tensionMap.aColorRamp )
	tensionMap.attributeAffects( tensionMap.aOrigShape, tensionMap.aOutShape )
	tensionMap.attributeAffects( tensionMap.aDeformedShape, tensionMap.aOutShape )
	tensionMap.attributeAffects( tensionMap.aColorRamp, tensionMap.aOutShape )


# AE template that put the main attributes into the main attribute section
#@staticmethod
def AEtemplateString(nodeName):
	templStr = ''
	templStr += 'global proc AE%sTemplate(string $nodeName)\n' % nodeName
	templStr += '{\n'
	templStr += 'editorTemplate -beginScrollLayout;\n'
	templStr += '	editorTemplate -beginLayout "Color Remaping" -collapse 0;\n'
	templStr += '		AEaddRampControl( $nodeName + ".color" );\n'
	templStr += '	editorTemplate -endLayout;\n'

	templStr += 'editorTemplate -addExtraControls; // add any other attributes\n'
	templStr += 'editorTemplate -endScrollLayout;\n'
	templStr += '}\n'

	return templStr


def initializePlugin( mobject ):
	mplugin = om2.MFnPlugin( mobject )
	try:
		mplugin.registerNode( kPluginNodeName, kPluginNodeId, nodeCreator, initialize )
		om.MGlobal.executeCommand( AEtemplateString( kPluginNodeName ) )
	except:
		sys.stderr.write( "Failed to register node: " + kPluginNodeName )
		raise


def uninitializePlugin(mobject):
	mplugin = om2.MFnPlugin( mobject )
	try:
		mplugin.deregisterNode( kPluginNodeId )
	except:
		sys.stderr.write( 'Failed to deregister node: ' + kPluginNodeName )
		raise