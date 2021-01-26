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
from trigger.library import selection
from trigger.ui import feedback

@keepselection
def skinTransfer(source=None, target=None):
    """
        Transfers (copies) skin to second object in the selection list. If the target object has skin cluster, it assumes
     that the script ran before and continues with a simple copy skin weights command. If target object has no skin cluster
     it gets the joints from the first object, creates a skin cluster on the second object using these joints and finally
     copies the skin weights.
    Returns: None
    """

    if not source or not target:
        #Get selected objects and find the skin cluster on the first one.
        sel, msg = selection.validate(min=2, max=2, meshesOnly=True, transforms=True)
        if not sel:
            feedback.Feedback().pop_info(title="Selection Error", text=msg, critical=True)
            return
        source = sel[0]
        target = sel[0]

    # get the present skin clusters on the source and target
    sourceObjHist = cmds.listHistory(source, pdo=True)
    sourceSkinClusters = cmds.ls(sourceObjHist, type="skinCluster")
    targetObjHist = cmds.listHistory(target, pdo=True)
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
    allTransform = cmds.listRelatives(target, children=True, ad=True, type="transform")
    # if the selected object has other transform nodes under it (if it is a group)
    if allTransform:
        for transform in allTransform:
            #if the node already has a skinCluster
            shapeObjHist = cmds.listHistory(transform, pdo=True)
            shapeSkinClusters = cmds.ls(shapeObjHist, type="skinCluster")
            print("presentSkinClusters", shapeSkinClusters)
            # If there is exactly one skin cluster connected to the target, continue with a simple copySkinWeights
            if len(shapeSkinClusters) == 1:
                cmds.copySkinWeights (source, transform, noMirror=True, surfaceAssociation="closestPoint", influenceAssociation="closestJoint", normalize=True)
                sys.stdout.write('Success...')
                return
            # eliminate the ones without shape (eliminate the groups under the group)
            if transform.getShape() != None:
                sc = cmds.skinCluster(allInfluences, transform, tsb=True)
                cmds.copySkinWeights (source, transform, noMirror=True, surfaceAssociation="closestPoint", influenceAssociation="closestJoint", normalize=True)
                sys.stdout.write('Success...')
                # return
    else:
        if len(targetSkinClusters)==0:
            sc = cmds.skinCluster(allInfluences, target, tsb=True)
        cmds.copySkinWeights (source, target, noMirror=True, surfaceAssociation="closestPoint", influenceAssociation="closestJoint", normalize=True)
        sys.stdout.write('Success...')
        return
