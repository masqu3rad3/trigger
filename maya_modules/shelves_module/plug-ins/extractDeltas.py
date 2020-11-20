# ----------------------------------------------------------------------------------------------
#
# extractDeltas.py
# v1.4
#
# extract a modeled corrective shape from a deformed skinned mesh
#
# original c++ extract deltas plugin by James Jacobs
#
# python conversion, improvements and maintenance by Ingo Clemens
# www.braverabbit.com
#
# brave rabbit, Ingo Clemens 2014
#
# versions:
#
# 1.4 - included mel scripts
# 1.3 - improved shape comparison without the need of blendshapes
# 1.2 - added the vertex list flag to work only on a given component list
# 1.1 - optimized performance because it now works on sculpted points only
#		(0.06 - c++ version, 1.88 - version 1.0, 0.14 - version 1.1)
# 1.0 - initial python conversion
#
# ----------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# ----------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------
#
#	USE AND MODIFY AT YOUR OWN RISK!!
#
# ----------------------------------------------------------------------------------------------


import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
import maya.cmds as cmds
from maya.mel import eval as meval
import re
import sys

kPluginCmdName = 'extractDeltas'


# --------------------------------------------------------------------------------
# argument flags
# --------------------------------------------------------------------------------

helpFlag = '-h'
helpFlagLong = '-help'

skinFlag = '-s'
skinFlagLong = '-skin'

correctiveFlag = '-c'
correctiveFlagLong = '-corrective'

vertexListFlag = '-vl'
vertexListFlagLong = '-vertexList'

helpText = ''
helpText += '\n Description: Extract a modeled corrective shape from a deformed skinned mesh.'
helpText += '\n'
helpText += '\n Flags: extractDeltas		-h		-help			<n/a>		this message'
helpText += '\n							-s		-skin			<string>	the name of the skinned mesh'
helpText += '\n							-c		-corrective		<string>	the name of the sculpted shape'
helpText += '\n							-vl		-vertexList		<string>	optional list of vertices, comma separated string'
helpText += '\n Usage: Execute the command with the following arguments:'
helpText += '\n Execute: extractDeltas -s <mesh with skin cluster> -c <corrective mesh name>'


# --------------------------------------------------------------------------------
# main command
# --------------------------------------------------------------------------------

class extractDeltas(OpenMayaMPx.MPxCommand):
	
	def __init__(self):
		OpenMayaMPx.MPxCommand.__init__(self)
		
	def doIt(self, args):
		
		self.dagModifier = OpenMaya.MDagModifier()
		
		skinName = ''
		correctiveName = ''
		resultName = ''
		listString = ''
		
		# --------------------------------------------------------------------------------
		# parse the arguments
		# --------------------------------------------------------------------------------
		
		argData = OpenMaya.MArgDatabase(self.syntax(), args)
		
		# help flag
		if argData.isFlagSet(helpFlag):
			self.setResult(helpText)
			return
		
		# skin flag
		if argData.isFlagSet(skinFlag):
			skinName = argData.flagArgumentString(skinFlag, 0)
		
		# corrective flag
		if argData.isFlagSet(correctiveFlag):
			correctiveName = argData.flagArgumentString(correctiveFlag, 0)
		
		# vertex list flag
		if argData.isFlagSet(vertexListFlag):
			listString = argData.flagArgumentString(vertexListFlag, 0)
		
		# --------------------------------------------------------------------------------
		# check the selection
		# --------------------------------------------------------------------------------
		
		sel = []
		if skinName != '' and correctiveName != '':
			sel.append(skinName)
			sel.append(correctiveName)
		else:
			sel = cmds.ls(sl = True, tr = True)
		
		shapeList = []
		
		for i in range(len(sel)):
			shapes = cmds.listRelatives(sel[i], s = True)
			if shapes == None:
				OpenMaya.MGlobal.displayError(sel[i] + ' has no shape node.')
				return
			if cmds.nodeType(shapes[0]) != 'mesh':
				OpenMaya.MGlobal.displayError(shapes[0] + ' is not a mesh object.')
				return
			elif i == 0 and len(shapes) > 1:
				skin = cmds.listConnections(shapes[0], type = 'skinCluster')
				if skin == None:
					OpenMaya.MGlobal.displayError(shapes[0] + ' is not bound to a skin cluster.')
					return
				if cmds.getAttr(shapes[1] + '.intermediateObject'):
					shapeList.append(shapes[1])
				else:
					OpenMaya.MGlobal.displayError(shapes[1] + ' is not an intermediate/original shape node.')	
					return
			shapeList.append(shapes[0])
		
		if len(shapeList) != 3:
			OpenMaya.MGlobal.displayError('Select a skinned mesh with a valid original shape node and a target mesh object.')
			return
		
		selList = OpenMaya.MSelectionList()
		for sl in shapeList:
			selList.add(sl)
		
		intermediateObj = OpenMaya.MObject()
		skinObj = OpenMaya.MObject()
		targetObj = OpenMaya.MObject()
		
		selList.getDependNode(0, intermediateObj)
		selList.getDependNode(1, skinObj)
		selList.getDependNode(2, targetObj)
		
		# --------------------------------------------------------------------------------
		# define the mesh functions and get the points
		# --------------------------------------------------------------------------------
		
		skinFn = OpenMaya.MFnMesh()
		skinFn.setObject(skinObj)
		targetFn = OpenMaya.MFnMesh()
		targetFn.setObject(targetObj)
		intermediateFn = OpenMaya.MFnMesh()
		intermediateFn.setObject(intermediateObj)
		
		skinPoints = OpenMaya.MPointArray()
		skinFn.getPoints(skinPoints)
		targetPoints = OpenMaya.MPointArray()
		targetFn.getPoints(targetPoints)
		intermediatePoints = OpenMaya.MPointArray()
		intermediateFn.getPoints(intermediatePoints)
		
		extractPoints = OpenMaya.MPointArray(intermediatePoints)
		
		# --------------------------------------------------------------------------------
		# get the delta points through a temporary blendShape node
		# --------------------------------------------------------------------------------
		
		pointList = []
		for i in range(0, skinPoints.length()):
			if skinPoints[i] != targetPoints[i]:
				pointList.append(i)
		
		if len(pointList) == 0:
			OpenMaya.MGlobal.displayError('No shape extracted. Both meshes are identical.')	
			return
		
		# create an intersection list between the delta points and the given vertex list
		vList = []
		if listString != '':
			array = listString.split(',')
			array = map(int, array)
			intersectList = list(set(pointList) & set(array))
			pointList = intersectList
		
		# --------------------------------------------------------------------------------
		# duplicate the original
		# --------------------------------------------------------------------------------
		
		resultFn = OpenMaya.MFnMesh()
		resultObj = OpenMaya.MObject()
		
		# copies the mesh using API functions but its not easily undoable
		#resultObj = resultFn.copy(intermediateObj, OpenMaya.cvar.MObject_kNullObj)
		# duplicating the mesh through maya commands is a bit more complex
		# but the undo comes for free
		
		resultMesh = cmds.duplicate(shapeList[0], rc = True)
		shapes = cmds.listRelatives(resultMesh, s = True)
		# delete the main shape node and deactivate the intermediate object
		cmds.delete(shapes[0])
		cmds.setAttr(shapes[1] + '.intermediateObject', 0)
		cmds.rename(shapes[1], shapes[0])
		attrList = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']
		for a in attrList:
			cmds.setAttr(resultMesh[0] + '.' + a, l = False)
		
		selList.clear()
		selList.add(shapes[0])
		selList.getDependNode(0, resultObj)
		resultFn.setObject(resultObj)
		
		resultPoints = OpenMaya.MPointArray()
		resultFn.getPoints(resultPoints)
		
		# --------------------------------------------------------------------------------
		# build a relative coordinate space by first preturbing
		# the origional mesh and then building a coordinate space
		# on the skinned mesh
		# --------------------------------------------------------------------------------
		
		xArray = OpenMaya.MPointArray(intermediatePoints)
		yArray = OpenMaya.MPointArray(intermediatePoints)
		zArray = OpenMaya.MPointArray(intermediatePoints)
		
		xPointArray = OpenMaya.MPointArray()
		yPointArray = OpenMaya.MPointArray()
		zPointArray = OpenMaya.MPointArray()
		
		for i in pointList:
			xArray.set(i, intermediatePoints[i].x + 1.0, intermediatePoints[i].y, intermediatePoints[i].z)
			yArray.set(i, intermediatePoints[i].x, intermediatePoints[i].y + 1.0, intermediatePoints[i].z)
			zArray.set(i, intermediatePoints[i].x, intermediatePoints[i].y, intermediatePoints[i].z + 1.0)
		
		intermediateFn.setPoints(xArray)
		skinFn.getPoints(xPointArray)
		
		for i in pointList:
			offX = xPointArray[i].x - skinPoints[i].x
			offY = xPointArray[i].y - skinPoints[i].y
			offZ = xPointArray[i].z - skinPoints[i].z
			xPointArray.set(i, offX, offY, offZ)
		
		intermediateFn.setPoints(yArray)
		skinFn.getPoints(yPointArray)
		
		for i in pointList:
			offX = yPointArray[i].x - skinPoints[i].x
			offY = yPointArray[i].y - skinPoints[i].y
			offZ = yPointArray[i].z - skinPoints[i].z
			yPointArray.set(i, offX, offY, offZ)
		
		intermediateFn.setPoints(zArray)
		skinFn.getPoints(zPointArray)
		
		for i in pointList:
			offX = zPointArray[i].x - skinPoints[i].x
			offY = zPointArray[i].y - skinPoints[i].y
			offZ = zPointArray[i].z - skinPoints[i].z
			zPointArray.set(i, offX, offY, offZ)
		
		# set the original points back
		intermediateFn.setPoints(intermediatePoints)
		
		# --------------------------------------------------------------------------------
		# perform the extraction from the skinned mesh
		# --------------------------------------------------------------------------------
		
		for i in pointList:
			extractItems = 	[zPointArray[i].x, zPointArray[i].y, zPointArray[i].z, 0.0, 
							xPointArray[i].x, xPointArray[i].y, xPointArray[i].z, 0.0, 
							yPointArray[i].x, yPointArray[i].y, yPointArray[i].z, 0.0, 
							skinPoints[i].x, skinPoints[i].y, skinPoints[i].z, 1.0]
			
			resultItems = 	[0.0, 0.0, 1.0, 0.0, 
							1.0, 0.0, 0.0, 0.0, 
							0.0, 1.0, 0.0, 0.0, 
							resultPoints[i].x, resultPoints[i].y, resultPoints[i].z, 1.0]
			
			extractMatrix = OpenMaya.MMatrix()
			OpenMaya.MScriptUtil.createMatrixFromList(extractItems, extractMatrix)
			
			resultMatrix = OpenMaya.MMatrix()
			OpenMaya.MScriptUtil.createMatrixFromList(resultItems, resultMatrix)
			
			point = OpenMaya.MPoint()
			point = targetPoints[i] * extractMatrix.inverse()
			point *= resultMatrix
			extractPoints.set(point, i)
		
		resultFn.setPoints(extractPoints)
		
		# --------------------------------------------------------------------------------
		# cleanup
		# --------------------------------------------------------------------------------
		
		cmds.sets(resultFn.fullPathName(), e = True, fe = 'initialShadingGroup')
		parentNode = cmds.listRelatives(resultFn.fullPathName(), p = True)
		resultName = cmds.rename(parentNode, sel[1] + '_corrective')
		
		self.setResult(resultName)
		
		return self.redoIt()

	def redoIt(self):
		self.dagModifier.doIt()
	
	def undoIt(self):
		self.dagModifier.undoIt()
	
	def isUndoable(self):
		return True


# --------------------------------------------------------------------------------
# define the syntax, needed to make it work with mel and python
# --------------------------------------------------------------------------------

# creator
def cmdCreator():
	return OpenMayaMPx.asMPxPtr(extractDeltas())
	
def syntaxCreator():
	syn = OpenMaya.MSyntax()
	syn.addFlag(helpFlag, helpFlagLong)
	syn.addFlag(skinFlag, skinFlagLong, OpenMaya.MSyntax.kString)
	syn.addFlag(correctiveFlag, correctiveFlagLong, OpenMaya.MSyntax.kString)
	syn.addFlag(vertexListFlag, vertexListFlagLong, OpenMaya.MSyntax.kString)
	return syn

# initialization
def initializePlugin(mobject):
	mplugin = OpenMayaMPx.MFnPlugin(mobject, 'Original plugin by James Jacobs / Python adaption by Ingo Clemens', '1.4', 'Any')
	try:
		mplugin.registerCommand(kPluginCmdName, cmdCreator, syntaxCreator)
	except:
		sys.stderr.write('Failed to register command: %s\n' % kPluginCmdName)
		raise

def uninitializePlugin(mobject):
	mplugin = OpenMayaMPx.MFnPlugin(mobject)
	try:
		mplugin.deregisterCommand(kPluginCmdName)
	except:
		sys.stderr.write( 'Failed to unregister command: %s\n' % kPluginCmdName )
		raise

# --------------------------------------------------------------------------------
# mel procedures
# --------------------------------------------------------------------------------

mel = '''

global proc extractDeltasDuplicateMesh()
{
	string $sel[] = `ls -sl`;
	string $shapes[] = `listRelatives -s $sel[0]`;
	string $skin[] = `listConnections -type "skinCluster" $shapes[0]`;
	if (`size($skin)`)
	{
		string $dup[] = `duplicate -rr -rc $sel`;
		$shapes = `listRelatives -s $dup[0]`;
		for ($s in $shapes)
		{
			if (`getAttr ($s + ".intermediateObject")`)
			{
				delete $s;
			}
		}
		setAttr -l 0 ($dup[0] + ".tx");
		setAttr -l 0 ($dup[0] + ".ty");
		setAttr -l 0 ($dup[0] + ".tz");
		setAttr -l 0 ($dup[0] + ".rx");
		setAttr -l 0 ($dup[0] + ".ry");
		setAttr -l 0 ($dup[0] + ".rz");
		setAttr -l 0 ($dup[0] + ".sx");
		setAttr -l 0 ($dup[0] + ".sy");
		setAttr -l 0 ($dup[0] + ".sz");
	}
}

global proc performExtractDeltas()
{
	string $sel[] = `ls -sl -tr`;
	string $shapes[];
	for ($s in $sel)
	{
		$shapes = `listRelatives -s $s`;
		for ($sh in $shapes)
		{
			if (`nodeType $sh` != "mesh")
			{
				error "The selected geometry is no polygon object!";
			}
		}
	}
	if (size($sel) == 2)
	{
		$shapes = `listRelatives -s $sel[0]`;
		string $skin[] = `listConnections -type "skinCluster" $shapes[0]`;
		if (!`size($skin)`)
		{
			error "The first selected object is not bound to a skin cluster!";
		}
	}
	else
	{
		error "Please select two polygonal objects!";
	}
	extractDeltas -s $sel[0] -c $sel[1];
}

'''
meval(mel)
