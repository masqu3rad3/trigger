from maya import cmds
import re

def get_animation_info(type_index=0, exclude=None, include=None, replace=None, default_value=None, nice_name=True):
    """Get all animation curves in the scene and return data for specific type
    """
    # collect all animation curves in the scene
    default_value = default_value or [""]
    replace = replace or ["", ""]
    anim_curves = cmds.ls(type="animCurve")
    if include:
        anim_curves = [x for x in anim_curves if all(y in x for y in include)]
    exclude = exclude or []
    if exclude:
        anim_curves = [x for x in anim_curves if all(y not in x for y in exclude)]

    active_animations = []
    for anim_curve in anim_curves:
        # query the first keyframe value of the animation curve
        initial_value = cmds.keyframe(anim_curve, query=True, eval=True, index=(0, 0)) or [0.0]
        current_value = cmds.keyframe(anim_curve, query=True, eval=True) or initial_value
        # if the current value is not the same as the first keyframe, collect it

        display_name = anim_curve.replace(replace[0], replace[1])
        if nice_name:
            display_name = get_nice_name(display_name)
        if initial_value != current_value:
            active_animations.append("{}: {}".format(display_name, round(current_value[0], 2)))


    # if the length of the active animation list within the type_index limits, return it
    if len(active_animations) > type_index:
        return active_animations[type_index]
    else:
        return default_value[0]

def get_nice_name(input_str):
    """Convert camel case or snake case to nice name."""
    # Use regular expression to split the string at camel case boundaries
    words = re.findall(r"[A-Z][a-z]*|[a-z]+", input_str)
    # Capitalize the first letter of each word and join them with a space
    nice_name = " ".join(word.capitalize() for word in words)
    return nice_name

