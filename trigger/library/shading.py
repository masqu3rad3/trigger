"""Collection of shading related functions"""

from maya import cmds
from trigger.core import logger
from trigger.library import functions

FEEDBACK = logger.Logger(logger_name=__name__)

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

def get_shading_groups(mesh):
    mesh_shape = cmds.listRelatives(mesh, children=True)[0]
    return cmds.listConnections(mesh_shape, type="shadingEngine")

def get_shaders(mesh):
    # mesh_shape = cmds.listRelatives(mesh, children=True)[0]
    # shading_engines = cmds.listConnections(mesh_shape, type="shadingEngine")
    shading_engines = get_shading_groups(mesh)
    shaders = ((cmds.ls(cmds.listConnections(shading_engines), materials=True)))
    return shaders


def assign_shader(shader, mesh):
    """Assings given shader to all available shading groups of mesh"""
    shading_engines = get_shading_groups(mesh)
    if not shading_engines:
        original_selection = cmds.ls(sl=True)
        cmds.select(mesh)
        sg_name = functions.uniqueName("%s_SG" % mesh)
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
        FEEDBACK.throw_error("The shader type %s is not valid. valid types are: %s" %(shader_type, ", ".join(valid_types)))

    if preset:
        valid_presets = ["glass", "skin", "fabric", "metal", "emissive"]
        if preset not in valid_presets:
            FEEDBACK.throw_error(
                "The preset %s is not valid. valid presets are: %s" % (preset, ", ".join(valid_presets)))
        if preset == "glass":
            pass
    shader = cmds.shadingNode("lambert", asShader=True, name=name)

