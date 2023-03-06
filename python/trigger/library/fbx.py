"""Module for FBX file format operations"""

from maya import cmds
from maya import mel
from trigger.core import validate

validate.plugin("fbxmaya")

import_settings = {
    'merge_mode': 'FBXImportMode -v {}',
    'smoothing_groups': 'FBXProperty Import|IncludeGrp|Geometry|SmoothingGroups -v {}',
    'unlock_normals': 'FBXProperty Import|IncludeGrp|Geometry|UnlockNormals -v {}',
    'hard_edges': 'FBXProperty Import|IncludeGrp|Geometry|HardEdges -v {}',
    'blind_data': 'FBXProperty Import|IncludeGrp|Geometry|BlindData -v {}',
    'animation': 'FBXProperty Import|IncludeGrp|Animation -v {}',
    'timeline': 'FBXProperty Import|IncludeGrp|Animation|ExtraGrp|TimeLine -v {}',
    'bake_animation_layers': 'FBXProperty Import|IncludeGrp|Animation|ExtraGrp|BakeAnimationLayers -v {}',
    'markers': 'FBXProperty Import|IncludeGrp|Animation|ExtraGrp|Markers -v {}',
    'quaternion': 'FBXProperty Import|IncludeGrp|Animation|ExtraGrp|Quaternion -v "{}"',
    'protect_driven_keys': 'FBXProperty Import|IncludeGrp|Animation|ExtraGrp|ProtectDrivenKeys -v {}',
    'deform_nulls_as_joints': 'FBXProperty Import|IncludeGrp|Animation|ExtraGrp|DeformNullsAsJoints -v {}',
    'nulls_to_pivot': 'FBXProperty Import|IncludeGrp|Animation|ExtraGrp|NullsToPivot -v {}',
    'point_cache': 'FBXProperty Import|IncludeGrp|Animation|ExtraGrp|PointCache -v {}',
    'deformation': 'FBXProperty Import|IncludeGrp|Animation|Deformation -v {}',
    'skins': 'FBXProperty Import|IncludeGrp|Animation|Deformation|Skins -v {}',
    'shape': 'FBXProperty Import|IncludeGrp|Animation|Deformation|Shape -v {}',
    'force_weight_normalize': 'FBXProperty Import|IncludeGrp|Animation|Deformation|ForceWeightNormalize -v {}',
    'sampling_rate_selector': 'FBXProperty Import|IncludeGrp|Animation|SamplingPanel|SamplingRateSelector -v "{}"',
    'curve_filter_sampling_rate': 'FBXProperty Import|IncludeGrp|Animation|SamplingPanel|CurveFilterSamplingRate -v {}',
    'curve_filter': 'FBXProperty Import|IncludeGrp|Animation|CurveFilter -v {}',
    'constraint': 'FBXProperty Import|IncludeGrp|Animation|ConstraintsGrp|Constraint -v {}',
    'character_type': 'FBXProperty Import|IncludeGrp|Animation|ConstraintsGrp|CharacterType -v "{}"',
    'camera': 'FBXProperty Import|IncludeGrp|CameraGrp|Camera -v {}',
    'light': 'FBXProperty Import|IncludeGrp|LightGrp|Light -v {}',
    'audio': 'FBXProperty Import|IncludeGrp|Audio -v {}',
    'dynamic_scale_conversion': 'FBXProperty Import|AdvOptGrp|UnitsGrp|DynamicScaleConversion -v {}',
    'units_selector': 'FBXProperty Import|AdvOptGrp|UnitsGrp|UnitsSelector -v "{}"',
    'axis_conversion': 'FBXProperty Import|AdvOptGrp|AxisConvGrp|AxisConversion -v {}',
    'up_axis': 'FBXProperty Import|AdvOptGrp|AxisConvGrp|UpAxis -v "{}"',
    'show_warnings_manager': 'FBXProperty Import|AdvOptGrp|UI|ShowWarningsManager -v {}',
    'generate_log_data': 'FBXProperty Import|AdvOptGrp|UI|GenerateLogData -v {}',
    'remove_bad_polygons': 'FBXProperty Import|AdvOptGrp|Performance|RemoveBadPolysFromMesh -v {}',
}


def reset_import_settings():
    """Reset import settings to default"""
    mel.eval("FBXResetImport")


def _format(value):
    """Format value for mel command"""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return value


def _set_fbx_import_settings(**kwargs):
    """Build FBX import settings"""
    for key, value in kwargs.items():
        value = _format(value)
        if key in import_settings.keys():
            cmd = import_settings[key].format(value)
            print("-----------------")
            print("-----------------")
            print("-----------------")
            print(cmd)
            print("-----------------")
            print("-----------------")
            print("-----------------")

            mel.eval(cmd)


def load(
        file_path,
        merge_mode="merge",  # add, merge, exmerge, exmergekeyedxforms
        smoothing_groups=False,
        unlock_normals=False,
        hard_edges=False,
        blind_data=True,
        animation=True,
        take=-1,  # take index. -1 for latest
        timeline=False,
        bake_animation_layers=True,
        markers=False,
        quaternion="resample",  # resample, euler, quaternion
        protect_driven_keys=False,
        deform_nulls_as_joints=True,
        nulls_to_pivot=True,
        point_cache=True,
        deformation=True,
        skins=True,
        shape=True,
        force_weight_normalize=False,
        sampling_rate_selector="Scene",  # Scene, File, Custom
        curve_filter_sampling_rate=24.0,
        curve_filter=False,
        constraint=True,
        character_type="HumanIK",  # None, HumanIK
        camera=True,
        light=True,
        audio=True,
        dynamic_scale_conversion=True,
        units_selector="Centimeters",  # Centimeters, Meters, Millimeters, Kilometers, Inches, Feet, Yards, Miles
        axis_conversion=False,
        up_axis="Y",  # Y, Z
        show_warnings_manager=False,
        generate_log_data=False,
        remove_bad_polys_from_mesh=True,
):
    """
    Load FBX file.
    Args:
        file_path (str): Path to FBX file
        merge_mode (str): Merge mode.
                                add: Adds the content of the FBX file to the scene.
                                merge: Adds new content and updates animation for existing content.
                                exmerge: updates existing animation and poses. No new content is added.
                                exmergekeyedxforms: only updates keyed animation.
                                Defaults to merge.
        smoothing_groups (bool): Import smoothing groups. Defaults to False.
        unlock_normals (bool): Unlock normals. Defaults to False.
        hard_edges (bool): Import hard edges. Defaults to False.
        blind_data (bool): Import blind data. Defaults to True.
        animation (bool): Import animation. Defaults to True.
        take (int): Take index. -1 for latest. 0 No animation. Defaults to -1.
        timeline (bool): Fills the scene timeline on import (instead of using the Maya default). Defaults to False.
        bake_animation_layers (bool): Activate Bake animation layers to bake (or Plot) animation layers contained in
                                the incoming file. Defaults to True.
        markers (bool): Import markers. Defaults to False.
        quaternion (str): Specifies how to handle quaternion imports. Options are:
                                resample: Resample as Euler interpolation.
                                euler: Set as Euler interpolation.
                                quaternion: Retain quaternion interpolation.
                                Defaults to resample.
        protect_driven_keys (bool): Protect driven keys. Defaults to False.
        deform_nulls_as_joints (bool): Activate this option to convert deforming elements into Maya joints.
                                If this option is not active, all elements other than joints being used to deform are
                                converted to locators. Defaults to True.
        nulls_to_pivot (bool): Activate this option only when you import older (pre-MotionBuilder 5.5) FBX files that
                                contain an animated joint hierarchy, for example, an animated character. This option
                                lets you assign the rotation transformation of the null (or joints) elements in the
                                hierarchy that are used as pre- and post-rotation to the joint orient and the rotate
                                axis of the original node. The pre-rotation and post-rotation nodes are then deleted.
                                Older files created with the Export Pre/Post Rotation as Nulls option are merged back
                                to the original Maya setup. Defaults to True.
        point_cache (bool): Activate this option to import FBX-exported geometry cache data during the FBX import
                                process. Defaults to True.
        deformation (bool): Activate this option to import FBX-exported deformation data during the FBX import process.
                                Defaults to True.
        skins (bool): Activate this option to import FBX-exported skin data during the FBX import process.
                                Defaults to True.
        shape (bool): Activate this option to import all geometry Blend Shapes into your scene. Defaults to True.
        force_weight_normalize (bool): Activate this option to normalize weight assignment. Defaults to False.
        sampling_rate_selector (str): Specifies the sampling rate for animation curves. Options are:
                                Scene: Use the scene's current sampling rate.
                                File: Use the sampling rate specified in the FBX file.
                                Custom: Use the sampling rate specified in the Curve Filter Sampling Rate field.
                                Defaults to Scene.
        curve_filter_sampling_rate (float): Specifies the sampling rate for animation curves. Defaults to 24.0.
        curve_filter (bool): Activate this option to filter animation curves. Defaults to False.
        constraint (bool): Activate this option to import FBX-exported constraint data during the FBX import process.
                                Defaults to True.
        character_type (str): Specifies the character type. Options are:
                                None: No character type.
                                HumanIK: HumanIK character type.
                                Defaults to HumanIK.
        camera (bool): import FBX-exported camera data during the FBX import process. Defaults to True.
        light (bool): import FBX-exported light data during the FBX import process. Defaults to True.
        audio (bool): import FBX-exported audio data during the FBX import process. Defaults to True.
        dynamic_scale_conversion (bool): Activate this option to convert the scale of the incoming FBX file to the
                                current scene's units. Defaults to True.
        units_selector (str): Specifies the units for the incoming FBX file. Options are:
                                Centimeters: Centimeters.
                                Meters: Meters.
                                Millimeters: Millimeters.
                                Kilometers: Kilometers.
                                Inches: Inches.
                                Feet: Feet.
                                Yards: Yards.
                                Miles: Miles.
                                Defaults to Centimeters.
        axis_conversion (bool): Activate this option to convert the axis of the incoming FBX file to the current scene's
                                axis. Defaults to False.
        up_axis (str): Specifies the up axis for the incoming FBX file. Options are:
                                Y: Y.
                                Z: Z.
        show_warnings_manager (bool): Option to show the warnings manager. Defaults to False.
        generate_log_data (bool): Option to generate log data. Defaults to False.
        remove_bad_polys_from_mesh (bool): Option to remove bad polygons from mesh. Defaults to True.

    Returns:
        Imported nodes.

    """
    quaternion = {
        "resample": "Resample As Euler Interpolation",
        "euler": "Set As Euler Interpolation",
        "quaternion": "Retain Quaternion Interpolation",
    }.get(quaternion, "Resample As Euler Interpolation")

    reset_import_settings()
    _set_fbx_import_settings(**locals())

    file_path = file_path.replace("\\", "//")  ## for compatibility with mel syntax.
    import_cmd = ('FBXImport -f "{0}" -t {1};'.format(file_path, take))
    # grab a list of nodes before importing
    nodes_before = cmds.ls()
    mel.eval(import_cmd)
    # grab a list of nodes after importing
    nodes_after = cmds.ls()
    # get the difference between the two lists
    imported_nodes = list(set(nodes_after) - set(nodes_before))
    return imported_nodes

def save(file_path):
    """Export the given file path."""
    cmds.file(file_path, e=True, type="FBX", force=True, options="v=0")

#############################################################################
# Output of FBXProperties mel command
#############################################################################
# PATH: Import|PlugInGrp|PlugInUIWidth    ( TYPE: Integer ) ( VALUE: 500 )
# PATH: Import|PlugInGrp|PlugInUIHeight    ( TYPE: Integer ) ( VALUE: 500 )
# PATH: Import|PlugInGrp|PlugInUIXpos    ( TYPE: Integer ) ( VALUE: 100 )
# PATH: Import|PlugInGrp|PlugInUIYpos    ( TYPE: Integer ) ( VALUE: 100 )
# PATH: Import|PlugInGrp|UILIndex    ( TYPE: Enum )  ( VALUE: "ENU" )  (POSSIBLE VALUES: "ENU" "DEU" "FRA" "JPN" "KOR" "CHS" "PTB"  )
# PATH: Import|IncludeGrp|MergeMode    ( TYPE: Enum )  ( VALUE: "Add and update animation" )  (POSSIBLE VALUES: "Add" "Add and update animation" "Update animation" "Update animation (keyed transforms)"  )
# PATH: Import|IncludeGrp|Geometry|SmoothingGroups    ( TYPE: Bool ) ( VALUE: "false" )
# PATH: Import|IncludeGrp|Geometry|UnlockNormals    ( TYPE: Bool ) ( VALUE: "false" )
# PATH: Import|IncludeGrp|Geometry|HardEdges    ( TYPE: Bool ) ( VALUE: "false" )
# PATH: Import|IncludeGrp|Geometry|BlindData    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|IncludeGrp|Animation    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|IncludeGrp|Animation|ExtraGrp|Take    ( TYPE: Enum )  ( VALUE: "No Animation" )  (POSSIBLE VALUES: "No Animation" "Take 001"  )
# PATH: Import|IncludeGrp|Animation|ExtraGrp|TimeLine    ( TYPE: Bool ) ( VALUE: "false" )
# PATH: Import|IncludeGrp|Animation|ExtraGrp|BakeAnimationLayers    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|IncludeGrp|Animation|ExtraGrp|Markers    ( TYPE: Bool ) ( VALUE: "false" )
# PATH: Import|IncludeGrp|Animation|ExtraGrp|Quaternion    ( TYPE: Enum )  ( VALUE: "Resample As Euler Interpolation" )  (POSSIBLE VALUES: "Retain Quaternion Interpolation" "Set As Euler Interpolation" "Resample As Euler Interpolation"  )
# PATH: Import|IncludeGrp|Animation|ExtraGrp|ProtectDrivenKeys    ( TYPE: Bool ) ( VALUE: "false" )
# PATH: Import|IncludeGrp|Animation|ExtraGrp|DeformNullsAsJoints    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|IncludeGrp|Animation|ExtraGrp|NullsToPivot    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|IncludeGrp|Animation|ExtraGrp|PointCache    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|IncludeGrp|Animation|Deformation    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|IncludeGrp|Animation|Deformation|Skins    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|IncludeGrp|Animation|Deformation|Shape    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|IncludeGrp|Animation|Deformation|ForceWeightNormalize    ( TYPE: Bool ) ( VALUE: "false" )
# PATH: Import|IncludeGrp|Animation|SamplingPanel|SamplingRateSelector    ( TYPE: Enum )  ( VALUE: "Scene" )  (POSSIBLE VALUES: "Scene" "File" "Custom"  )
# PATH: Import|IncludeGrp|Animation|SamplingPanel|CurveFilterSamplingRate    ( TYPE: Number ) ( VALUE: 24.000000 )
# PATH: Import|IncludeGrp|Animation|CurveFilter    ( TYPE: Bool ) ( VALUE: "false" )
# PATH: Import|IncludeGrp|Animation|ConstraintsGrp|Constraint    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|IncludeGrp|Animation|ConstraintsGrp|CharacterType    ( TYPE: Enum )  ( VALUE: "HumanIK" )  (POSSIBLE VALUES: "None" "HumanIK"  )
# PATH: Import|IncludeGrp|CameraGrp|Camera    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|IncludeGrp|LightGrp|Light    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|IncludeGrp|Audio    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|UnitsGrp|DynamicScaleConversion    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|UnitsGrp|UnitsSelector    ( TYPE: Enum )  ( VALUE: "Centimeters" )  (POSSIBLE VALUES: "Millimeters" "Centimeters" "Decimeters" "Meters" "Kilometers" "Inches" "Feet" "Yards" "Miles"  )
# PATH: Import|AdvOptGrp|AxisConvGrp|AxisConversion    ( TYPE: Bool ) ( VALUE: "false" )
# PATH: Import|AdvOptGrp|AxisConvGrp|UpAxis    ( TYPE: Enum )  ( VALUE: "Y" )  (POSSIBLE VALUES: "Y" "Z"  )
# PATH: Import|AdvOptGrp|UI|ShowWarningsManager    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|UI|GenerateLogData    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|FileFormat|Obj|ReferenceNode    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|FileFormat|Max_3ds|ReferenceNode    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|FileFormat|Max_3ds|Texture    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|FileFormat|Max_3ds|Material    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|FileFormat|Max_3ds|Animation    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|FileFormat|Max_3ds|Mesh    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|FileFormat|Max_3ds|Light    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|FileFormat|Max_3ds|Camera    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|FileFormat|Max_3ds|AmbientLight    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|FileFormat|Max_3ds|Rescaling    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|FileFormat|Max_3ds|Filter    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|FileFormat|Max_3ds|Smoothgroup    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|FileFormat|Motion_Base|MotionFrameCount    ( TYPE: Integer ) ( VALUE: 0 )
# PATH: Import|AdvOptGrp|FileFormat|Motion_Base|MotionFrameRate    ( TYPE: Number ) ( VALUE: 0.000000 )
# PATH: Import|AdvOptGrp|FileFormat|Motion_Base|MotionActorPrefix    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|FileFormat|Motion_Base|MotionRenameDuplicateNames    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|FileFormat|Motion_Base|MotionExactZeroAsOccluded    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|FileFormat|Motion_Base|MotionSetOccludedToLastValidPos    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|FileFormat|Motion_Base|MotionAsOpticalSegments    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|FileFormat|Motion_Base|MotionASFSceneOwned    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|FileFormat|Motion_Base|MotionUpAxisUsedInFile    ( TYPE: Integer ) ( VALUE: 3 )
# PATH: Import|AdvOptGrp|FileFormat|Biovision_BVH|MotionCreateReferenceNode    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|FileFormat|MotionAnalysis_HTR|MotionCreateReferenceNode    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|FileFormat|MotionAnalysis_HTR|MotionBaseTInOffset    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|FileFormat|MotionAnalysis_HTR|MotionBaseRInPrerotation    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|FileFormat|Acclaim_ASF|MotionCreateReferenceNode    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|FileFormat|Acclaim_ASF|MotionDummyNodes    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|FileFormat|Acclaim_ASF|MotionLimits    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|FileFormat|Acclaim_ASF|MotionBaseTInOffset    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|FileFormat|Acclaim_ASF|MotionBaseRInPrerotation    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|FileFormat|Acclaim_AMC|MotionCreateReferenceNode    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|FileFormat|Acclaim_AMC|MotionDummyNodes    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|FileFormat|Acclaim_AMC|MotionLimits    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|FileFormat|Acclaim_AMC|MotionBaseTInOffset    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|FileFormat|Acclaim_AMC|MotionBaseRInPrerotation    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|Dxf|WeldVertices    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|Dxf|ObjectDerivation    ( TYPE: Enum )  ( VALUE: "By layer" )  (POSSIBLE VALUES: "By layer" "By entity" "By block"  )
# PATH: Import|AdvOptGrp|Dxf|ReferenceNode    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Import|AdvOptGrp|Performance|RemoveBadPolysFromMesh    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|PlugInGrp|PlugInUIWidth    ( TYPE: Integer ) ( VALUE: 500 )
# PATH: Export|PlugInGrp|PlugInUIHeight    ( TYPE: Integer ) ( VALUE: 500 )
# PATH: Export|PlugInGrp|PlugInUIXpos    ( TYPE: Integer ) ( VALUE: 100 )
# PATH: Export|PlugInGrp|PlugInUIYpos    ( TYPE: Integer ) ( VALUE: 100 )
# PATH: Export|PlugInGrp|UILIndex    ( TYPE: Enum )  ( VALUE: "ENU" )  (POSSIBLE VALUES: "ENU" "DEU" "FRA" "JPN" "KOR" "CHS" "PTB"  )
# PATH: Export|IncludeGrp|Geometry|SmoothingGroups    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|IncludeGrp|Geometry|expHardEdges    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|IncludeGrp|Geometry|TangentsandBinormals    ( TYPE: Bool ) ( VALUE: "false" )
# PATH: Export|IncludeGrp|Geometry|SmoothMesh    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|IncludeGrp|Geometry|SelectionSet    ( TYPE: Bool ) ( VALUE: "false" )
# PATH: Export|IncludeGrp|Geometry|BlindData    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|IncludeGrp|Geometry|AnimationOnly    ( TYPE: Bool ) ( VALUE: "false" )
# PATH: Export|IncludeGrp|Geometry|Instances    ( TYPE: Bool ) ( VALUE: "false" )
# PATH: Export|IncludeGrp|Geometry|ContainerObjects    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|IncludeGrp|Geometry|Triangulate    ( TYPE: Bool ) ( VALUE: "false" )
# PATH: Export|IncludeGrp|Geometry|GeometryNurbsSurfaceAs    ( TYPE: Enum )  ( VALUE: "NURBS" )  (POSSIBLE VALUES: "NURBS" "Interactive Display Mesh" "Software Render Mesh"  )
# PATH: Export|IncludeGrp|Animation    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|IncludeGrp|Animation|ExtraGrp|UseSceneName    ( TYPE: Bool ) ( VALUE: "false" )
# PATH: Export|IncludeGrp|Animation|ExtraGrp|RemoveSingleKey    ( TYPE: Bool ) ( VALUE: "false" )
# PATH: Export|IncludeGrp|Animation|ExtraGrp|Quaternion    ( TYPE: Enum )  ( VALUE: "Resample As Euler Interpolation" )  (POSSIBLE VALUES: "Retain Quaternion Interpolation" "Set As Euler Interpolation" "Resample As Euler Interpolation"  )
# PATH: Export|IncludeGrp|Animation|BakeComplexAnimation    ( TYPE: Bool ) ( VALUE: "false" )
# PATH: Export|IncludeGrp|Animation|BakeComplexAnimation|BakeFrameStart    ( TYPE: Integer ) ( VALUE: 1 )
# PATH: Export|IncludeGrp|Animation|BakeComplexAnimation|BakeFrameEnd    ( TYPE: Integer ) ( VALUE: 10 )
# PATH: Export|IncludeGrp|Animation|BakeComplexAnimation|BakeFrameStep    ( TYPE: Integer ) ( VALUE: 1 )
# PATH: Export|IncludeGrp|Animation|BakeComplexAnimation|ResampleAnimationCurves    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|IncludeGrp|Animation|BakeComplexAnimation|HideComplexAnimationBakedWarning    ( TYPE: Bool ) ( VALUE: "false" )
# PATH: Export|IncludeGrp|Animation|Deformation    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|IncludeGrp|Animation|Deformation|Skins    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|IncludeGrp|Animation|Deformation|Shape    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|IncludeGrp|Animation|Deformation|ShapeAttributes    ( TYPE: Bool ) ( VALUE: "false" )
# PATH: Export|IncludeGrp|Animation|Deformation|ShapeAttributes|ShapeAttributesValues    ( TYPE: Enum )  ( VALUE: "Relative" )  (POSSIBLE VALUES: "Relative" "Absolute"  )
# PATH: Export|IncludeGrp|Animation|CurveFilter    ( TYPE: Bool ) ( VALUE: "false" )
# PATH: Export|IncludeGrp|Animation|CurveFilter|CurveFilterApplyCstKeyRed    ( TYPE: Bool ) ( VALUE: "false" )
# PATH: Export|IncludeGrp|Animation|CurveFilter|CurveFilterApplyCstKeyRed|CurveFilterCstKeyRedTPrec    ( TYPE: Number ) ( VALUE: 0.000090 )
# PATH: Export|IncludeGrp|Animation|CurveFilter|CurveFilterApplyCstKeyRed|CurveFilterCstKeyRedRPrec    ( TYPE: Number ) ( VALUE: 0.009000 )
# PATH: Export|IncludeGrp|Animation|CurveFilter|CurveFilterApplyCstKeyRed|CurveFilterCstKeyRedSPrec    ( TYPE: Number ) ( VALUE: 0.004000 )
# PATH: Export|IncludeGrp|Animation|CurveFilter|CurveFilterApplyCstKeyRed|CurveFilterCstKeyRedOPrec    ( TYPE: Number ) ( VALUE: 0.009000 )
# PATH: Export|IncludeGrp|Animation|CurveFilter|CurveFilterApplyCstKeyRed|AutoTangentsOnly    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|IncludeGrp|Animation|PointCache    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|IncludeGrp|Animation|PointCache|SelectionSetNameAsPointCache    ( TYPE: Enum )  ( VALUE: " " )  (POSSIBLE VALUES: " "  )
# PATH: Export|IncludeGrp|Animation|ConstraintsGrp|Constraint    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|IncludeGrp|Animation|ConstraintsGrp|Character    ( TYPE: Bool ) ( VALUE: "false" )
# PATH: Export|IncludeGrp|CameraGrp|Camera    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|IncludeGrp|LightGrp|Light    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|IncludeGrp|Audio    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|IncludeGrp|EmbedTextureGrp|EmbedTexture    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|IncludeGrp|BindPose    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|IncludeGrp|PivotToNulls    ( TYPE: Bool ) ( VALUE: "false" )
# PATH: Export|IncludeGrp|BypassRrsInheritance    ( TYPE: Bool ) ( VALUE: "false" )
# PATH: Export|IncludeGrp|InputConnectionsGrp|IncludeChildren    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|IncludeGrp|InputConnectionsGrp|InputConnections    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|AdvOptGrp|UnitsGrp|DynamicScaleConversion    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|AdvOptGrp|UnitsGrp|UnitsSelector    ( TYPE: Enum )  ( VALUE: "" )  (POSSIBLE VALUES:  )
# PATH: Export|AdvOptGrp|AxisConvGrp|UpAxis    ( TYPE: Enum )  ( VALUE: "Y" )  (POSSIBLE VALUES: "Y" "Z"  )
# PATH: Export|AdvOptGrp|UI|ShowWarningsManager    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|AdvOptGrp|UI|GenerateLogData    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|AdvOptGrp|FileFormat|Obj|Triangulate    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|AdvOptGrp|FileFormat|Obj|Deformation    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|AdvOptGrp|FileFormat|Motion_Base|MotionFrameCount    ( TYPE: Integer ) ( VALUE: 0 )
# PATH: Export|AdvOptGrp|FileFormat|Motion_Base|MotionFromGlobalPosition    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|AdvOptGrp|FileFormat|Motion_Base|MotionFrameRate    ( TYPE: Number ) ( VALUE: 30.000000 )
# PATH: Export|AdvOptGrp|FileFormat|Motion_Base|MotionGapsAsValidData    ( TYPE: Bool ) ( VALUE: "false" )
# PATH: Export|AdvOptGrp|FileFormat|Motion_Base|MotionC3DRealFormat    ( TYPE: Bool ) ( VALUE: "false" )
# PATH: Export|AdvOptGrp|FileFormat|Motion_Base|MotionASFSceneOwned    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|AdvOptGrp|FileFormat|Biovision_BVH|MotionTranslation    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|AdvOptGrp|FileFormat|Acclaim_ASF|MotionTranslation    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|AdvOptGrp|FileFormat|Acclaim_ASF|MotionFrameRateUsed    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|AdvOptGrp|FileFormat|Acclaim_ASF|MotionFrameRange    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|AdvOptGrp|FileFormat|Acclaim_ASF|MotionWriteDefaultAsBaseTR    ( TYPE: Bool ) ( VALUE: "false" )
# PATH: Export|AdvOptGrp|FileFormat|Acclaim_AMC|MotionTranslation    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|AdvOptGrp|FileFormat|Acclaim_AMC|MotionFrameRateUsed    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|AdvOptGrp|FileFormat|Acclaim_AMC|MotionFrameRange    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|AdvOptGrp|FileFormat|Acclaim_AMC|MotionWriteDefaultAsBaseTR    ( TYPE: Bool ) ( VALUE: "false" )
# PATH: Export|AdvOptGrp|Fbx|AsciiFbx    ( TYPE: Enum )  ( VALUE: "Binary" )  (POSSIBLE VALUES: "Binary" "ASCII"  )
# PATH: Export|AdvOptGrp|Fbx|ExportFileVersion    ( TYPE: Alias )  ( VALUE: "FBX201400" )  (POSSIBLE VALUES: "FBX202000" "FBX201900" "FBX201800" "FBX201600" "FBX201400" "FBX201300" "FBX201200" "FBX201100" "FBX201000" "FBX200900" "FBX200611"  )
# PATH: Export|AdvOptGrp|Dxf|Deformation    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|AdvOptGrp|Dxf|Triangulate    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|AdvOptGrp|Collada|Triangulate    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|AdvOptGrp|Collada|SingleMatrix    ( TYPE: Bool ) ( VALUE: "true" )
# PATH: Export|AdvOptGrp|Collada|FrameRate    ( TYPE: Number ) ( VALUE: 24.000000 )
