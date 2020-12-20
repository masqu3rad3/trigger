import os
import re
import glob
from bisect import bisect_left
from maya import cmds

def uniqueName(name, return_counter=False):
    """
    Searches the scene for match and returns a unique name for given name
    Args:
        name: (String) Name to query
        return_counter: (Bool) If true, returns the next available number insted of the object name

    Returns: (String) uniquename

    """
    baseName = name
    idcounter = 0
    while cmds.objExists(name):
        name = "%s%s" % (baseName, str(idcounter + 1))
        idcounter = idcounter + 1
    if return_counter:
        return idcounter
    else:
        return name

def uniqueScene():
    """Makes sure that everything is named uniquely. Returns list of renamed nodes and list of new names"""

    collection = []
    for obj in cmds.ls():
        pathway = obj.split("|")
        if len(pathway) > 1:
            uniqueName(pathway[-1])
            collection.append(obj)
    collection.reverse()
    old_names = []
    new_names = []
    for xe in collection:
        pathway = xe.split("|")
        old_names.append(pathway[-1])
        new_names.append(cmds.rename(xe, uniqueName(pathway[-1])))
    return old_names, new_names

def resolve_version(file_path):
    """Resolves the version of the given file"""

    no_ext = os.path.splitext(file_path)[0]
    is_digits = re.search('.*?([0-9]+)$', no_ext)
    if not is_digits:
        return 0
    return int(is_digits.groups()[0])

def resolve_file_path(file_path, new_version, force=True):
    """builds the file name with the given new version"""

    file_dir, file_name_with_ext = os.path.split(file_path)
    file_name, file_ext = os.path.splitext(file_name_with_ext)
    version = resolve_version(file_path)
    stripped_name = file_name if not version else re.search("(.*)(%s)$" % str(version).zfill(3), file_name).groups()[0]
    if not stripped_name.endswith("_v"):
        if force:
            return os.path.join(file_dir, "{0}_v{1}{2}".format(file_name, str(new_version).zfill(3), file_ext))
        else: return None
    else:
        return os.path.join(file_dir, "{0}{1}{2}".format(stripped_name, str(new_version).zfill(3), file_ext))

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
    stripped_name = file_name if not version else re.search("(.*)(%s)$" % str(version).zfill(3), file_name).groups()[0]
    # check if this is has a proper version naming convention
    if not stripped_name.endswith("_v"):
        if force_version:
            return os.path.join(file_dir, "{0}_v001{1}".format(file_name, file_ext))
        else: return None

    files_on_server = glob.glob(os.path.join(file_dir, "{0}*{1}".format(stripped_name, file_ext)))
    if not files_on_server:
        return file_path

    last_saved_version = resolve_version(max(files_on_server, key=resolve_version))
    next_version = max(version + 1, last_saved_version + 1)
    return os.path.join(file_dir, "{0}{1}{2}".format(stripped_name, str(next_version).zfill(3), file_ext))


def get_all_versions(file_path):
    """Checks the disk and returns all existing versions of a file in a list"""

    file_dir, file_name_with_ext = os.path.split(file_path)
    file_name, file_ext = os.path.splitext(file_name_with_ext)

    version = resolve_version(file_path)
    if not version:
        return None

    stripped_name = file_name if not version else re.search("(.*)(%s)$" % str(version).zfill(3), file_name).groups()[0]
    files_on_server = glob.glob(os.path.join(file_dir, "{0}*{1}".format(stripped_name, file_ext)))
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
        id = all_versions.index(current_version)
        if id != len(all_versions):
            next_version = all_versions[id+1]
        else:
            return file_path
    # if the given file path version is not in the disk
    else:
        id = bisect_left(all_versions, current_version)
        if id != len(all_versions):
            next_version = all_versions[id]
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
        id = all_versions.index(current_version)
        if id != 0:
            prev_version = all_versions[id-1]
        else:
            return file_path
    # if the given file path version is not in the disk
    else:
        id = bisect_left(all_versions, current_version)
        if id != 0:
            prev_version = all_versions[id-1]
        else:
            return file_path
    return resolve_file_path(file_path=file_path, new_version=prev_version)
