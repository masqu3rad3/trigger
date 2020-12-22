#####################################################################################################################
## SkinTransfer - Python Script
## Copyright (C) Arda Kutlu
## AUTHOR:	Arda Kutlu
## e-mail: ardakutlu@gmail.com
## Web: http://www.ardakutlu.com
## VERSION:0.0.2
## CREATION DATE: 29.03.2017
## LAST MODIFIED DATE: 23.09.2020 / cmds convert

## DESCRIPTION: In addition to the default behaviour of the copy weights command, this tool additionally copies the skin cluster as well.

## USAGE: First select the source Object, then select the target object and run the script
#####################################################################################################################

import sys
from maya import cmds
from trigger.core.decorators import keepselection

@keepselection
def skinTransfer():
    """
        Transfers (copies) skin to second object in the selection list. If the target object has skin cluster, it assumes
     that the script ran before and continues with a simple copy skin weights command. If target object has no skin cluster
     it gets the joints from the first object, creates a skin cluster on the second object using these joints and finally
     copies the skin weights.
    Returns: None
    """

    #Get selected objects and find the skin cluster on the first one.
    selection = cmds.ls(sl=True)
    if (len(selection)!=2):
        cmds.error("You need to select two Objects")
        return
    # get the present skin clusters on the source and target
    sourceObjHist = cmds.listHistory(selection[0], pdo=True)
    sourceSkinClusters = cmds.ls(sourceObjHist, type="skinCluster")
    targetObjHist = cmds.listHistory(selection[1], pdo=True)
    targetSkinClusters = cmds.ls(targetObjHist, type="skinCluster")

    # if there is no skin cluster on the first object do not continue
    if (len(sourceSkinClusters)!=1):
        cmds.error ("There is no skin cluster (or more than one) on the source object")
        return
    if (len(targetSkinClusters)>1):
        cmds.error ("There is more than one skin clusters on the target object")
        return

    allInfluences=cmds.skinCluster(sourceSkinClusters[0], q=True, weightedInfluence=True)


    ## add skin cluster for each shape under the transform node
    allTransform = cmds.listRelatives(selection[1], children=True, ad=True, type="transform")
    # if the selected object has other transform nodes under it (if it is a group)
    if allTransform:
        for transform in allTransform:
            #if the node already has a skinCluster
            shapeObjHist = cmds.listHistory(transform, pdo=True)
            shapeSkinClusters = cmds.ls(shapeObjHist, type="skinCluster")
            print("presentSkinClusters", shapeSkinClusters)
            # If there is exactly one skin cluster connected to the target, continue with a simple copySkinWeights
            if len(shapeSkinClusters) == 1:
                cmds.copySkinWeights (selection[0], transform, noMirror=True, surfaceAssociation="closestPoint", influenceAssociation="closestJoint", normalize=True)
                sys.stdout.write('Success...')
                return
            # eliminate the ones without shape (eliminate the groups under the group)
            if transform.getShape() != None:
                sc = cmds.skinCluster(allInfluences, transform, tsb=True)
                cmds.copySkinWeights (selection[0], transform, noMirror=True, surfaceAssociation="closestPoint", influenceAssociation="closestJoint", normalize=True)
                sys.stdout.write('Success...')
                # return
    else:
        if len(targetSkinClusters)==0:
            sc = cmds.skinCluster(allInfluences, selection[1], tsb=True)
        cmds.copySkinWeights (selection[0], selection[1], noMirror=True, surfaceAssociation="closestPoint", influenceAssociation="closestJoint", normalize=True)
        sys.stdout.write('Success...')
        return
