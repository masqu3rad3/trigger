"""Collection of shading related functions"""

from maya import cmds
from trigger.core import filelog
from trigger.library import naming

log = filelog.Filelog(logname=__name__, filename="trigger_log")


def get_file_nodes(objList):
    returnList = []
    if not objList:
        return returnList
    for obj in objList:
        # Get the shading group from the selected mesh
        sg = cmds.listConnections(obj, type='shadingEngine')
        if not sg:
            continue
        allInputs = []
        for i in sg:
            allInputs.extend(cmds.listHistory(i))

        uniqueInputs =set(allInputs)

        fileNodes = cmds.ls(uniqueInputs, type="file")
        if len(fileNodes) != 0:
            returnList.extend(fileNodes)
    returnList = set(returnList)
    return returnList

def find_file_node(plug):
    """Recursively finds the first file node connected to the plug"""

    connected_node = cmds.listConnections(plug, source=True)
    if cmds.objectType(connected_node) == "file":
        return connected_node[0]
    else:
        connections = cmds.listConnections(connected_node, source=True, destination=False, plugs=True, connections=True)
        if connections:
            active_plugs = connections[::2]
            for sub_plug in active_plugs:
                # print(sub_plug, connected_node[0])
                # if the plug is connected to the node itself dont go into the cycle loop
                if sub_plug.split(".")[0] == connected_node[0]:
                    continue
                else:
                    return find_file_node(sub_plug)

def get_shading_groups(mesh):
    mesh_shape = cmds.listRelatives(mesh, children=True)[0]
    return cmds.listConnections(mesh_shape, type="shadingEngine")

def get_shaders(mesh):
    shading_engines = get_shading_groups(mesh)
    shaders = ((cmds.ls(cmds.listConnections(shading_engines), materials=True)))
    return shaders

def get_all_materials():
    for shading_engine in cmds.ls(type='shadingEngine'):
        if cmds.sets(shading_engine, q=True):
            for material in cmds.ls(cmds.listConnections(shading_engine), materials=True):
                yield material

def assign_shader(shader, mesh):
    """Assings given shader to all available shading groups of mesh"""
    shading_engines = get_shading_groups(mesh)
    if not shading_engines:
        original_selection = cmds.ls(sl=True)
        cmds.select(mesh)
        sg_name = naming.uniqueName("%s_SG" % mesh)
        cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg_name)
        cmds.select(original_selection)
        shading_engines = [sg_name]
    for sg in shading_engines:
        cmds.connectAttr("%s.outColor" % shader, "%s.surfaceShader" % sg, f=True)
        cmds.sets(mesh, e=True, forceElement=sg)



def create_preview_shader(shader_type="blinn", preset=None, diffuse=None, mask=None, name="triggerShader", *args, **kwargs):
    """
    Creates a basic shader for visualization purposes

    Args:
        shader_type:
        name:

    Returns:

    """
    # TODO WIP
    valid_types = ["lambert", "surfaceShader", "blinn", "phong", "standardShader"]
    if shader_type not in valid_types:
        log.error("The shader type %s is not valid. valid types are: %s" % (shader_type, ", ".join(valid_types)))

    if preset:
        valid_presets = ["glass", "skin", "fabric", "metal", "emissive"]
        if preset not in valid_presets:
            log.error(
                "The preset %s is not valid. valid presets are: %s" % (preset, ", ".join(valid_presets)))
        if preset == "glass":
            pass
    shader = cmds.shadingNode("lambert", asShader=True, name=name)
