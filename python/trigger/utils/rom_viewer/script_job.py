from maya import cmds

def get_animation_info(type_index=0):
    """Get all animation curves in the scene and return data for specific type
    """
    # collect all animation curves in the scene
    anim_curves = cmds.ls(type="animCurve")

    active_animations = []
    for anim_curve in anim_curves:
        # query the first keyframe value of the animation curve
        initial_value = cmds.keyframe(anim_curve, query=True, eval=True, index=(0, 0))
        current_value = cmds.keyframe(anim_curve, query=True, eval=True)
        # if the current value is not the same as the first keyframe, collect it
        if initial_value != current_value:
            active_animations.append("{}: {}".format(anim_curve, round(current_value[0], 2)))

    # if the length of the activa animation list within the type_index limits, return it
    if len(active_animations) > type_index:
        return active_animations[type_index]
    else:
        return "-"





