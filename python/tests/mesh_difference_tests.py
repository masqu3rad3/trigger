import maya.cmds as cmds
import maya.mel as mel
import maya.api.OpenMaya as api
import time
import pdb


def get_std_deviation(value_list):
    if not value_list:
        return 0
    avg = sum(value_list) / len(value_list)
    var = sum((x - avg) ** 2 for x in value_list) / len(value_list)
    std = var ** 0.5
    return std


def getAllVerts(node):
    """
    Using Maya Python API 2.0
    """
    # ___________Selection___________
    # # 1 # Query the selection list
    # selectionLs = api.MGlobal.getActiveSelectionList()
    #
    # # 2 # Get the dag path of the first item in the selection list
    # selObj = selectionLs.getDagPath(0)

    selectionLs = api.MSelectionList()
    selectionLs.add(node)
    selObj = selectionLs.getDagPath(0)

    # ___________Query vertex position ___________
    # create a Mesh functionset from our dag object
    mfnObject = api.MFnMesh(selObj)

    return mfnObject.getPoints(api.MSpace.kWorld)


def get_difference(node_a, node_b, threshold=0.0, at_time=None):
    if at_time:
        cmds.currentTime(at_time)
    a_vertices = getAllVerts(node_a)
    b_vertices = getAllVerts(node_b)
    for a, b in zip(a_vertices, b_vertices):
        d = a.distanceTo(b)
        if d > threshold:
            yield (d)


joint_mesh = "face_IDskin_GUIDE"
bs_mesh = "trigger_morphMesh"

dif = get_difference(joint_mesh, bs_mesh, 0.001)
std_deviation = get_std_deviation(list(dif))
# print(std_deviation)

# j_vertices = getAllVerts(joint_mesh)
# b_vertices = getAllVerts(bs_mesh)
# for j, b in zip(j_vertices, b_vertices):
#     d = j.distanceTo(b)
#     if d > 0.2:
#         print(d)
#         break

# type(j_hand.originalData["throatUp"]["timeGap"][1])

print("----------------------------------------------------------------------------------")
t_dict = {}
for shape, data in sorted(j_hand.originalData.items()):
    dif = list(get_difference(joint_mesh, bs_mesh, 0.001, at_time=data["timeGap"][-1]))
    std_deviation = round(get_std_deviation(dif), 3)

    # print("{0}{1}: {2} - {3}".format(shape, " "*(55-len(shape)),str(len(dif)).zfill(5), std_deviation))
    t_dict[shape] = "{0}: {1} - {2}".format(" " * (55 - len(shape)), str(len(dif)).zfill(5), std_deviation)
    # print("{0}{1}: {2}".format(shape, " "*(55-len(shape)),len(list(dif))))

compare_list = ["LouterBrowRaiser", "LinnerBrowRaiser", "RneckStretch", "RnasolabialFurrow", "ULjawDrop"]
for shape in compare_list:
    print(shape, t_dict[shape])

