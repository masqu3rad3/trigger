"""Collection of shading related functions"""

from maya import cmds
from trigger.core import io
from trigger.core.decorators import keepselection

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
    mesh_shape = cmds.listRelatives(mesh, children=True, fullPath=True)[0]
    return cmds.listConnections(mesh_shape, type="shadingEngine")

def get_shaders(mesh):
    shading_engines = get_shading_groups(mesh)
    shaders = ((cmds.ls(cmds.listConnections(shading_engines), materials=True)))
    return shaders

def get_all_materials():
    "Returns all materials IN USE"
    for shading_engine in cmds.ls(type='shadingEngine'):
        if cmds.sets(shading_engine, q=True):
            for material in cmds.ls(cmds.listConnections(shading_engine), materials=True):
                yield material

def assign_shader(shader, mesh=None, shading_group=None):
    """Assings given shader to all available shading groups of mesh"""
    if not mesh and not shading_group:
        raise Exception("One of the mesh or shading_group arguments must be defined")
    if mesh:
        shading_engines = get_shading_groups(mesh)
        if not shading_engines:
            shading_engines = [create_shading_engine(mesh)]
        for sg in shading_engines:
            if sg == "initialShadingGroup":
                sg = create_shading_engine(mesh)
            cmds.connectAttr("%s.outColor" % shader, "%s.surfaceShader" % sg, f=True)
            cmds.sets(mesh, e=True, forceElement=sg)
    elif shading_group:
        cmds.connectAttr("%s.outColor" % shader, "%s.surfaceShader" % shading_group, f=True)
    else:
        raise Exception("Only one of the mesh or shading_group arguments should be defined")

@keepselection
def create_shading_engine(mesh, name=None):
    name = name or "%s_SG" % mesh
    shading_group = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=name)
    return shading_group

def collect_material_database():
    """
    Collects all basic shader information from scene into a dictionary
    Note that, this function ONLY collects the shader attribute values as it is. It does not collect
    any connected node information like ramp, file etc.
    """
    excluded_mats = ['lambert1', 'standardSurface1', 'particleCloud1']
    excluded_attrs = ['message', 'caching', 'frozen', 'isHistoricallyInteresting', 'nodeState', 'binMembership', ]
    all_materials = [mat for mat in cmds.ls(materials=True) if not mat in excluded_mats]

    material_dict = {}
    for mat in all_materials:
        material_dict[mat] = {}
        material_dict[mat]["shaderType"] = cmds.objectType(mat)
        all_attrs = [attr for attr in cmds.listAttr(mat, visible=True) if attr not in excluded_attrs]
        for attr in all_attrs:
            material_dict[mat][attr] = cmds.getAttr("{0}.{1}".format(mat, attr))
    return material_dict


def create_preview_shader(database, material_id, name=None, mesh=None):
    """
    Creates a preview shader based on the template on given database

    Args:
        database: (dictionary) dictionary item collected with 'collect_material_database' function
        material_id: (string) key id which needs to exist in the provided dictionary. If not, default standardSurface
                                will be used instead
        name: (string) Name of the new shader. Optional. If not provided <material_id>_M template will be used
        mesh: (string) Mesh that will be assigned. The Shading groups will be preserved if there are multi sgs

    Returns:

    """
    name = name or "%s_M" % material_id
    material_data = database.get(material_id)
    if not material_data:
        shader = cmds.shadingNode("standardSurface", asShader=True, name=name)
    else:
        shader_type = database[material_id]["shaderType"]
        attributes = database[material_id]
        del attributes["shaderType"]
        shader = cmds.shadingNode(shader_type, asShader=True, name=name)
        for attr, value in attributes.items():
            if type(value) == list:
                cmds.setAttr("{0}.{1}".format(shader, attr), *value[0])
            elif type(value) == str:
                cmds.setAttr("{0}.{1}".format(shader, attr), value, type="string")
            else:
                cmds.setAttr("{0}.{1}".format(shader, attr), value)
    if mesh:
        assign_shader(shader, mesh=mesh)
    return shader

def save_material_database(file_path):
    database = collect_material_database()
    io_handler = io.IO(file_path=file_path)
    io_handler.write(database)

def load_material_database(file_path):
    io_handler = io.IO(file_path=file_path)
    database = io_handler.read()
    return database

