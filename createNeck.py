import pymel.core as pm

import extraProcedures as extra
reload(extra)

import contIcons as icon
reload(icon)

import createSplineIK as spline
reload(spline)

neckStart = pm.PyNode("jInit_neck")
headStart = pm.PyNode("jInit_head")
headEnd = pm.PyNode("jInit_headEnd")
jawStart = pm.PyNode("jInit_jawStart")
jawEnd = pm.PyNode("jInit_jawEnd")

neckDist=extra.getDistance(neckStart, headStart)
headDist=extra.getDistance(headStart, headEnd)
## create Controllers
neckScale=(neckDist/2, neckDist/2, neckDist/2)
icon.curvedCircle(name="cont_neck", scale=neckScale, location=(neckStart.getTranslation(space="world")))

headScale=(headDist)

spline.createSplineIK([neckStart,headStart],"neckSplineIK", 4, dropoff=2)