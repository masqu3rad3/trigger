"""Collection of shading related functions"""

from maya import cmds
from trigger.core import io
from trigger.core.decorators import keepselection


def get_file_nodes(mesh_transforms):
    """Returns all file nodes connected to the given mesh transforms."""
    return_list = []
    for transform in mesh_transforms:
        # Get the shading group from the selected mesh
        shading_groups = cmds.listConnections(transform, type='shadingEngine')
        if not shading_groups:
            continue
        all_inputs = []
        for sg in shading_groups:
            all_inputs.extend(cmds.listHistory(sg))

        unique_inputs = set(all_inputs)

        file_nodes = cmds.ls(unique_inputs, type="file")
        if len(file_nodes) != 0:
            return_list.extend(file_nodes)
    return_list = set(return_list)
    return return_list


def find_file_node(plug):
    """Find recursively the first file node connected to the plug."""
    connected_node = cmds.listConnections(plug, source=True)
    if cmds.objectType(connected_node) == "file":
        return connected_node[0]
    else:
        connections = cmds.listConnections(connected_node, source=True, destination=False, plugs=True, connections=True)
        if connections:
            active_plugs = connections[::2]
            for sub_plug in active_plugs:
                # if the plug is connected to the node itself don't go into the cycle loop
                if sub_plug.split(".")[0] == connected_node[0]:
                    continue
                else:
                    return find_file_node(sub_plug)


def get_shading_groups(mesh):
    """Return all shading groups of the given mesh."""
    mesh_shape = cmds.listRelatives(mesh, children=True, fullPath=True)[0]
    return cmds.listConnections(mesh_shape, type="shadingEngine")


def get_shaders(mesh):
    """Return all shaders connected to the given mesh"""
    shading_engines = get_shading_groups(mesh)
    shaders = (cmds.ls(cmds.listConnections(shading_engines), materials=True))
    return shaders


def get_all_materials():
    """Return all materials IN USE."""
    for shading_engine in cmds.ls(type='shadingEngine'):
        if cmds.sets(shading_engine, q=True):
            for material in cmds.ls(cmds.listConnections(shading_engine), materials=True):
                yield material


def assign_shader(shader, mesh=None, shading_group=None):
    """Assign given shader to all available shading groups of mesh."""
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
    """Create a new shading engine and connect it to the given mesh."""
    name = name or "%s_SG" % mesh
    shading_group = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=name)
    return shading_group


def collect_material_database():
    """Collect all basic shader information from scene into a dictionary.

    Note that, this function ONLY collects the shader attribute values as it is. It does not collect
    any connected node information like ramp, file etc.
    """
    excluded_mats = ['lambert1', 'standardSurface1', 'particleCloud1']
    excluded_attrs = ['message', 'caching', 'frozen', 'isHistoricallyInteresting', 'nodeState', 'binMembership', ]
    all_materials = [mat for mat in cmds.ls(materials=True) if mat not in excluded_mats]

    material_dict = {}
    for mat in all_materials:
        material_dict[mat] = {}
        material_dict[mat]["shaderType"] = cmds.objectType(mat)
        all_attrs = [attr for attr in cmds.listAttr(mat, visible=True) if attr not in excluded_attrs]
        for attr in all_attrs:
            material_dict[mat][attr] = cmds.getAttr("{0}.{1}".format(mat, attr))
    return material_dict


def create_preview_shader(database, material_id, name=None, mesh=None):
    """Create a preview shader based on the template on given database.

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
            if isinstance(value, list):
                cmds.setAttr("{0}.{1}".format(shader, attr), *value[0])
            elif isinstance(value, str):
                cmds.setAttr("{0}.{1}".format(shader, attr), value, type="string")
            else:
                cmds.setAttr("{0}.{1}".format(shader, attr), value)
    if mesh:
        assign_shader(shader, mesh=mesh)
    return shader
