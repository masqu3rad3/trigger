"""Collection of deformer related functions"""

from maya import cmds

from trigger.core.decorators import undo, keepselection
from trigger.library import functions
from trigger.library import naming
from trigger.core import compatibility as compat


def get_deformers(mesh=None, namesOnly=False):
    """Collects defomers in a dictionary by type

    Args:
        mesh (str): Shape or transform node
    Return:
        dictionary: {<type>: [list of deformers]}

    """

    valid_deformers = ["skinCluster", "blendShape", "nonLinear", "cluster", "jiggle", "deltaMush"]
    if cmds.about(q=True, api=True) >= 20180400:
        valid_deformers.append("ffd")
    # get deformer from mesh
    if not mesh:
        mesh = cmds.ls(sl=True)
    history = cmds.listHistory(mesh, pruneDagObjects=True)

    deformer_data = {deformer_type: cmds.ls(history, type=deformer_type, shapes=True) for deformer_type in
                     valid_deformers}
    if namesOnly:
        name_list = compat.flatten([value for key, value in deformer_data.items()])
        return name_list
    else:
        return deformer_data

def get_influencers(deformer):
    return cmds.aliasAttr(deformer, q=True)[::2]

@undo
def connect_bs_targets(
        driver_attr,
        targets_dictionary,
        driver_range=None,
        force_new=False,
        front_of_chain=True,
        bs_node_name=None
):
    """Creates or adds Blendshape target and connects them into the same controller attribute

    Args:
        driver_attr (String): driver attribute which controls. tooth_ctrl.gumRetract
        targets_dictionary (Dict): Dictionary for the targets.
                    Format: {<base>: <target_blendShape>}
                    Example: {
                        "face_mesh": "faceGumRetract",
                        "meniscus": "meniscusGumRetract",
                    }
        driver_range (List): If defined, remaps the driver attribute. Example: [0, 100]
        force_new (Bool): If True, a new blendshape will be created for each mesh even though there are existing ones.
        front_of_chain: Created blendshapes will be added front of the chain. Default True
        bs_node_name: If a new blendshape node will be created it will take this name. If a blendshape node with this
                        name exists, it will use that one.
    """
    if not bs_node_name:
        bs_node_name = naming.uniqueName("trigger_blendShape")
    if driver_range:
        custom_range = True
    else:
        custom_range = False
        driver_range = [0, 1]

    # check the driver, create a float attr if not present
    ch_node, ch_attr = driver_attr.split(".")
    assert cmds.objExists(ch_node), (
            "The Driver object (%s) does not exist in the scene" % ch_node
    )
    attr_state = cmds.attributeQuery(ch_attr, node=ch_node, exists=True)
    if not attr_state:
        cmds.addAttr(
            ch_node,
            ln=ch_attr,
            at="float",
            min=driver_range[0],
            max=driver_range[1],
            k=True,
        )
    else:
        # check if the given values are in range
        min_val = cmds.addAttr("%s.%s" % (ch_node, ch_attr), q=True, min=True)
        max_val = cmds.addAttr("%s.%s" % (ch_node, ch_attr), q=True, max=True)
        if min_val > driver_range[0]:
            cmds.addAttr("%s.%s" % (ch_node, ch_attr), e=True, min=driver_range[0])
        if max_val < driver_range[1]:
            cmds.addAttr("%s.%s" % (ch_node, ch_attr), e=True, max=driver_range[1])

    if custom_range:
        remap_node = cmds.createNode("remapValue")
        cmds.setAttr("{0}.inputMin".format(remap_node), driver_range[0])
        cmds.setAttr("{0}.inputMax".format(remap_node), driver_range[1])
        cmds.setAttr("{0}.outputMin".format(remap_node), 0)
        cmds.setAttr("{0}.outputMax".format(remap_node), 1)
        cmds.connectAttr(driver_attr, "{0}.inputValue".format(remap_node))
        driver_attr = "{0}.outValue".format(remap_node)

    bs_attrs = []
    for base, target_shape in targets_dictionary.items():
        # get the blendshape
        history = cmds.listHistory(base, pdo=True)
        bs_nodes = cmds.ls(history, type="blendShape")
        if force_new or not bs_nodes:
            bs_node = cmds.blendShape(
                target_shape, base, w=[0, 1], foc=front_of_chain, sd=True, name=bs_node_name
            )[0]
        else:
            if bs_node_name in bs_nodes:
                bs_node = bs_node_name
            else:
                bs_node = bs_nodes[0]
            next_index = cmds.blendShape(bs_node, q=True, wc=True)
            cmds.blendShape(
                bs_node,
                edit=True,
                t=(base, next_index, target_shape, 1.0),
                w=[next_index, 1.0],
            )
        bs_attrs.append("{0}.{1}".format(bs_node, target_shape))

    for bs_attr in bs_attrs:
        cmds.connectAttr(driver_attr, bs_attr)

@undo
def localize(mesh, blendshape_node, local_target_name="LocalRig", group_name=None):
    """Creates a local rig by duplicating and using the duplicate as the blendshape target to the original mesh.

    Arguments:
        mesh {String} -- Original mesh
        blendshape_node {String} -- Name of the existing blendshape node on the original mesh. If this is an unexisting node, a new blendshape will be created with this name

    Keyword Arguments:
        local_target_name {String} -- Name of the localized target. If non given, default duplicate name will be used. (default: {LocalRig})

    Returns:
        [String] -- Name of the local target
    """

    # create a holding group
    local_rig_grp = "%s_grp" %local_target_name if not group_name else group_name
    if not cmds.objExists(local_rig_grp):
        cmds.group(name=local_rig_grp, em=True)

    if cmds.objExists(local_target_name):
        local_mesh = local_target_name
    else:
        # duplicate once
        local_mesh = cmds.duplicate(mesh, name=local_target_name)[0]
        # get rid of any inbetweens, unlock transforms
        attrs = ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "v"]
        for attr in attrs:
            cmds.setAttr("%s.%s" %(local_mesh, attr), e=True, k=True, l=False)
        # delete intermediate objects
        shapes = cmds.listRelatives(local_mesh, children=True)
        _ = [cmds.delete(shape) for shape in shapes if cmds.getAttr("%s.intermediateObject" % shape) == 1]



    if cmds.objExists(blendshape_node):
        shape = cmds.listRelatives(mesh, c=True, s=True)[0]
        # check the shape if it contains the blendshape
        if blendshape_node not in cmds.listConnections(shape):
            cmds.error(
                "Specified blendshape_node ({0}) exists in the scene but not connected to the specified mesh ({1})".format(
                    blendshape_node, mesh))
        # query the existing targets
        next_index = cmds.blendShape(blendshape_node, q=True, wc=True)
        # this returns the total number of used indices. Theoratically, if index inputs follows order
        # it should return an empty index number. However:
        # if somewhere before another shape is inserted into a random weight input,
        # this assumption wont work
        cmds.blendShape(blendshape_node, edit=True, t=(mesh, next_index, local_mesh, 1.0), w=[next_index, 1.0])

    else:
        # create a blendshape
        cmds.blendShape(local_mesh, mesh, w=[0, 1], name=blendshape_node, foc=True)

    if functions.getParent(local_mesh) != local_rig_grp:
        cmds.parent(local_mesh, local_rig_grp)

    return local_mesh


def cluster(mesh):
    original_selection = cmds.ls(sl=True)
    cmds.select(mesh)
    cmds.CreateCluster()
    shape = cmds.listRelatives(mesh, shapes=True)[0]
    cluster = cmds.listConnections(shape, type="cluster")[-1]
    cluster_handle = cmds.listConnections(cluster, type="transform")[-1]
    cmds.select(original_selection)
    return cluster, cluster_handle

def get_bs_index_by_name(bs_node, target_name):
    attr = bs_node + '.w[{}]'
    weightCount = cmds.blendShape(bs_node, q=True, wc=True)
    for index in range(weightCount):
        if cmds.aliasAttr(attr.format(index), q=True) == target_name:
            return index
    return -1

@keepselection
def create_proximity_wrap(driver, driven, **kwargs):
    # get arguments
    wrap_mode_dict = {"offset": 0, "surface": 1, "snap": 2, "rigid": 3, "cluster":4}
    wrap_mode = kwargs.get('wrap_mode', 1)
    try: wrap_mode = int(wrap_mode)
    except ValueError:
        wrap_mode = wrap_mode_dict[wrap_mode.lower()]
    name = kwargs.get('name', 'tr_proximityWrap')
    max_drivers = kwargs.get('max_drivers', 1)
    falloff_scale = kwargs.get('falloff_scale', 0.01)
    smooth_influences = kwargs.get('smooth_influences', 0)
    smooth_normals = kwargs.get('smooth_normals', 0)
    soft_normalization = kwargs.get('soft_normalization', 0)
    span_samples = kwargs.get('span_samples', 1)

    cmds.select(driven)
    cmds.ProximityWrap()
    node_history = cmds.listHistory(driven)
    wrap_node = [node for node in node_history if cmds.objectType(node) == "proximityWrap"][0]
    wrap_node = cmds.rename(wrap_node, "proximity_wrap_{0}".format(name))
    driver_shape = cmds.listRelatives(driver, c=True, type="shape")[0]

    # check if there is another orig shape
    if not cmds.objExists("{0}Orig".format(driver_shape)):
        temp = cmds.duplicate(driver_shape)[0]
        orig_shape = cmds.listRelatives(temp, c=True, type="shape")[0]
        cmds.parent(orig_shape, driver, r=True, shape=True)
        orig_shape = cmds.rename(orig_shape, "%sOrig" % driver_shape)
        cmds.delete(temp)
        cmds.setAttr("{0}.intermediateObject".format(orig_shape), 1)
    else:
        orig_shape = "{0}Orig".format(driver_shape)

    cmds.connectAttr("{0}.outMesh".format(driver_shape), "{0}.drivers[0].driverGeometry".format(wrap_node))
    cmds.connectAttr("{0}.outMesh".format(orig_shape), "{0}.drivers[0].driverBindGeometry".format(wrap_node))

    cmds.setAttr("{0}.wrapMode".format(wrap_node), wrap_mode)
    cmds.setAttr("{0}.maxDrivers".format(wrap_node), max_drivers)
    cmds.setAttr("{0}.falloffScale".format(wrap_node), falloff_scale)
    cmds.setAttr("{0}.smoothInfluences".format(wrap_node), smooth_influences)
    cmds.setAttr("{0}.smoothNormals".format(wrap_node), smooth_normals)
    cmds.setAttr("{0}.softNormalization".format(wrap_node), soft_normalization)
    cmds.setAttr("{0}.spanSamples".format(wrap_node), span_samples)

    return wrap_node

def create_wrap(influence, surface, **kwargs):
    ## TODO: refine the function and move to the library

    shapes = cmds.listRelatives(influence, shapes=True)
    influenceShape = shapes[0]

    shapes = cmds.listRelatives(surface, shapes=True)
    surfaceShape = shapes[0]

    # create wrap deformer
    weightThreshold = kwargs.get('weightThreshold', 0.0)
    maxDistance = kwargs.get('maxDistance', 1.0)
    exclusiveBind = kwargs.get('exclusiveBind', False)
    autoWeightThreshold = kwargs.get('autoWeightThreshold', True)
    falloffMode = kwargs.get('falloffMode', 0)

    wrapData = cmds.deformer(surface, type='wrap')
    wrapNode = wrapData[0]

    cmds.setAttr(wrapNode + '.weightThreshold', weightThreshold)
    cmds.setAttr(wrapNode + '.maxDistance', maxDistance)
    cmds.setAttr(wrapNode + '.exclusiveBind', exclusiveBind)
    cmds.setAttr(wrapNode + '.autoWeightThreshold', autoWeightThreshold)
    cmds.setAttr(wrapNode + '.falloffMode', falloffMode)

    cmds.connectAttr(surface + '.worldMatrix[0]', wrapNode + '.geomMatrix')

    # add influence
    duplicateData = cmds.duplicate(influence, name=influence + 'Base')
    base = duplicateData[0]
    shapes = cmds.listRelatives(base, shapes=True)
    baseShape = shapes[0]
    cmds.hide(base)

    # create dropoff attr if it doesn't exist
    if not cmds.attributeQuery('dropoff', n=influence, exists=True):
        cmds.addAttr(influence, sn='dr', ln='dropoff', dv=4.0, min=0.0, max=20.0)
        cmds.setAttr(influence + '.dr', k=True)

    # if type mesh
    if cmds.nodeType(influenceShape) == 'mesh':
        # create smoothness attr if it doesn't exist
        if not cmds.attributeQuery('smoothness', n=influence, exists=True):
            cmds.addAttr(influence, sn='smt', ln='smoothness', dv=0.0, min=0.0)
            cmds.setAttr(influence + '.smt', k=True)

        # create the inflType attr if it doesn't exist
        if not cmds.attributeQuery('inflType', n=influence, exists=True):
            cmds.addAttr(influence, at='short', sn='ift', ln='inflType', dv=2, min=1, max=2)

        cmds.connectAttr(influenceShape + '.worldMesh', wrapNode + '.driverPoints[0]')
        cmds.connectAttr(baseShape + '.worldMesh', wrapNode + '.basePoints[0]')
        cmds.connectAttr(influence + '.inflType', wrapNode + '.inflType[0]')
        cmds.connectAttr(influence + '.smoothness', wrapNode + '.smoothness[0]')

    # if type nurbsCurve or nurbsSurface
    if cmds.nodeType(influenceShape) == 'nurbsCurve' or cmds.nodeType(influenceShape) == 'nurbsSurface':
        # create the wrapSamples attr if it doesn't exist
        if not cmds.attributeQuery('wrapSamples', n=influence, exists=True):
            cmds.addAttr(influence, at='short', sn='wsm', ln='wrapSamples', dv=10, min=1)
            cmds.setAttr(influence + '.wsm', k=True)

        cmds.connectAttr(influenceShape + '.ws', wrapNode + '.driverPoints[0]')
        cmds.connectAttr(baseShape + '.ws', wrapNode + '.basePoints[0]')
        cmds.connectAttr(influence + '.wsm', wrapNode + '.nurbsSamples[0]')

    cmds.connectAttr(influence + '.dropoff', wrapNode + '.dropoff[0]')
    # I want to return a pyNode object for the wrap deformer.
    # I do not see the reason to rewrite the code here into pymel.
    return wrapNode, base