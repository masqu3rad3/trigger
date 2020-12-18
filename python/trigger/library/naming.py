import os
import re
import glob
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

def increment(file_path, force_version=True):
    """
    Increments the version number of the given file by one

    Checks the directory and makes a cross-check
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


# def get_next_version(file_path):
#     current_version = resolve_version(file_path)
#     all_versions = get_all_versions(file_path)
#
#
# testlist = [1, 4, 5, 6, 8]
# testlist.index(9)
# min(testlist, key=lambda x: abs(x - 3))
#
# print(get_all_versions(test_file))