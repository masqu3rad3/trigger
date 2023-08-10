import os
import re
import glob
from bisect import bisect_left
from maya import cmds
import uuid


# TODO: update the unique_name function to accept suffix to ignore
def unique_name(name, return_counter=False, suffix=None):
    """
    Searches the scene for match and returns a unique name for given name
    Args:
        name: (String) Name to query
        return_counter: (Bool) If true, returns the next available number instead of the object name
        suffix: (String) If defined and if name ends with this suffix, the increment numbers will be put before the.

    Returns: (String) uniquename

    """
    search_name = name
    base_name = name
    if suffix and name.endswith(suffix):
        base_name = name.replace(suffix, "")
    else:
        suffix = ""
    id_counter = 0
    while cmds.objExists(search_name):
        search_name = "{0}{1}{2}".format(base_name, str(id_counter + 1), suffix)
        id_counter = id_counter + 1
    if return_counter:
        return id_counter
    else:
        if id_counter:
            result_name = "{0}{1}{2}".format(base_name, str(id_counter), suffix)
        else:
            result_name = name
        return result_name


def unique_scene():
    """Make sure that everything is named uniquely.
    Returns list of renamed nodes and list of new names"""

    collection = []
    for obj in cmds.ls():
        pathway = obj.split("|")
        if len(pathway) > 1:
            unique_name(pathway[-1])
            collection.append(obj)
    collection.reverse()
    old_names = []
    new_names = []
    for xe in collection:
        pathway = xe.split("|")
        old_names.append(pathway[-1])
        new_names.append(cmds.rename(xe, unique_name(pathway[-1])))
    return old_names, new_names


def resolve_version(file_path):
    """Resolves the version of the given file"""
    no_ext = os.path.splitext(file_path)[0]
    # is_digits = re.search('.*?([0-9]+)$', no_ext.split(".")[0])
    is_digits = re.search(".*?([0-9]+)$", no_ext)
    if not is_digits:
        return 0
    return int(is_digits.groups()[0])


def resolve_file_path(file_path, new_version, force=True):
    """builds the file name with the given new version"""

    file_dir, file_name_with_ext = os.path.split(file_path)
    file_name, file_ext = os.path.splitext(file_name_with_ext)
    version = resolve_version(file_path)
    stripped_name = (
        file_name
        if not version
        else re.search("(.*)(%s)$" % str(version).zfill(3), file_name).groups()[0]
    )
    if not stripped_name.endswith("_v"):
        if force:
            return os.path.join(
                file_dir,
                "{0}_v{1}{2}".format(file_name, str(new_version).zfill(3), file_ext),
            )
        else:
            return None
    else:
        return os.path.join(
            file_dir,
            "{0}{1}{2}".format(stripped_name, str(new_version).zfill(3), file_ext),
        )


def increment(file_path, force_version=True):
    """
    Increments the version number of the given file by one
    Checks the directory and makes a cross-check
    The returned file path is the next file version which does not exist yet
    """

    file_dir, file_name_with_ext = os.path.split(file_path)
    file_name, file_ext = os.path.splitext(file_name_with_ext)

    # get the trailing digits and version free filename
    version = resolve_version(file_path)
    if not version:
        # if there are no digits, this is the first version
        if force_version:
            return os.path.join(file_dir, "{0}_v001{1}".format(file_name, file_ext))
        else:
            return None
    stripped_name = (
        file_name
        if not version
        else file_name.replace("_v%s" % (str(version).zfill(3)), "_v{0}")
    )
    # check if this has a proper version naming convention
    if "_v{0}" not in stripped_name:
        if force_version:
            parts = file_name.split(".")
            parts[0] = "%s_v001" % parts[0]
            forced_filename = ".".join(parts)
            return os.path.join(file_dir, "{0}{1}".format(forced_filename, file_ext))

    files_on_server = glob.glob(
        os.path.join(file_dir, "{0}{1}".format(stripped_name.format("*"), file_ext))
    )
    if not files_on_server:
        return file_path

    last_saved_version = resolve_version(max(files_on_server, key=resolve_version))
    next_version = max(version + 1, last_saved_version + 1)
    return os.path.join(
        file_dir,
        "{0}{1}".format(stripped_name.format(str(next_version).zfill(3)), file_ext),
    )


def get_all_versions(file_path):
    """Checks the disk and returns all existing versions of a file in a list"""

    file_dir, file_name_with_ext = os.path.split(file_path)
    file_name, file_ext = os.path.splitext(file_name_with_ext)

    version = resolve_version(file_path)
    if not version:
        return None

    stripped_name = (
        file_name
        if not version
        else file_name.replace("_v%s" % (str(version).zfill(3)), "_v{0}")
    )
    files_on_server = glob.glob(
        os.path.join(file_dir, "{0}{1}".format(stripped_name.format("*"), file_ext))
    )
    if not files_on_server:
        return None

    return sorted(list(map(resolve_version, files_on_server)))


def get_next_version(file_path):
    """Gets the next EXISTING version of the file"""

    current_version = resolve_version(file_path)
    all_versions = get_all_versions(file_path)
    if not all_versions:
        return file_path
    # if the given file path version does exist:
    if current_version in all_versions:
        uid = all_versions.index(current_version)
        if uid != len(all_versions) - 1:
            next_version = all_versions[uid + 1]
        else:
            return file_path
    # if the given file path version is not in the disk
    else:
        uid = bisect_left(all_versions, current_version)
        if uid != len(all_versions) - 1:
            next_version = all_versions[uid]
        else:
            return file_path
    return resolve_file_path(file_path=file_path, new_version=next_version)


def get_previous_version(file_path):
    """Gets the previous EXISTING version of the file"""

    current_version = resolve_version(file_path)
    all_versions = get_all_versions(file_path)
    if not all_versions:
        return file_path
    # if the given file path version does exist:
    if current_version in all_versions:
        uid = all_versions.index(current_version)
        if uid != 0:
            prev_version = all_versions[uid - 1]
        else:
            return file_path
    # if the given file path version is not in the disk
    else:
        uid = bisect_left(all_versions, current_version)
        if uid != 0:
            prev_version = all_versions[uid - 1]
        else:
            return file_path
    return resolve_file_path(file_path=file_path, new_version=prev_version)


def is_latest_version(file_path):
    """Check if the file is the latest version."""
    current_version = resolve_version(file_path)
    all_versions = get_all_versions(file_path)
    if not all_versions:
        return False
    if current_version not in all_versions:
        return False
    uid = all_versions.index(current_version)
    if uid == len(all_versions) - 1:
        return True
    else:
        return False


def get_uuid(prefix="uuid", short=True, no_dashes=True):
    """
    Create an uuid1 to prevent clashing issues.

    Args:
        prefix: adds this to the start. Useful for making it compatible as node names.
        short: uses the first part of uuid until the first dash
        no_dashes: if True, the dashes in uuid will be removed

    Returns: (string) uuid

    """
    _uuid = str(uuid.uuid1())
    if short:
        _uuid = _uuid.split("-")[0]
    if no_dashes:
        _uuid = _uuid.replace("-", "")
    if prefix:
        _uuid = "%s%s" % (prefix, _uuid)
    return _uuid


def get_part_name(node_dag_path):
    """Gets a nice shorter name from the tagged mesh names"""
    node_name = node_dag_path.split("|")[-1]
    parts = node_name.split("_")
    if not parts:
        return node_name
    if len(parts) == 4:
        return parts[1]
    else:
        return parts[0]


def rename_skinclusters():
    """Rename all skinClusters to match to the geometry names."""
    all_skins = cmds.ls(type="skinCluster")

    for skin in all_skins:
        mesh_name = cmds.listConnections(
            "%s.outputGeometry" % skin, shapes=False, source=False, destination=True
        )[0]
        sc_name = "%s_%s" % (mesh_name.split("|")[-1], "skinCluster")
        cmds.rename(skin, sc_name)


def parse(labels, prefix="", suffix="", side=""):
    """Parse object name with given parameters"""
    if not isinstance(labels, (list, tuple)):
        labels = [labels]
    elements = [side, prefix] + labels + [suffix]
    # filter the elements to remove empty strings
    elements = [str(e) for e in elements if e != ""]
    return "_".join(elements)
