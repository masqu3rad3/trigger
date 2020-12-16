"""Release for windows users"""

import shutil
import os
import stat


def copyfile(src, dst, forceDir=False):
    targetPath = os.path.join(dst, os.path.basename(src))
    if forceDir:
        if not os.path.isdir(os.path.normpath(dst)):
            os.makedirs(os.path.normpath(dst))

    shutil.copyfile(src, targetPath)


def copytree(src, dst, symlinks=False, ignore=None):
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    if not os.path.isdir(dst):  # This one line does the trick
        os.makedirs(dst)
    errors = []
    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                copytree(srcname, dstname, symlinks, ignore)
            else:
                # Will raise a SpecialFileError for unsupported file types
                shutil.copy2(srcname, dstname)

        except shutil.Error as err:
            errors.extend(err.args[0])
        except EnvironmentError as why:
            errors.append((srcname, dstname, str(why)))
    try:
        shutil.copystat(src, dst)
    except OSError as why:
        if WindowsError is not None and isinstance(why, WindowsError):
            # Copying file access times may fail on Windows
            pass
        else:
            errors.extend((src, dst, str(why)))
    if errors:
        raise shutil.Error(errors)


latest_release = "/mnt/ps-storage01/appdepot/dev_packages/arda.kutlu/rigging/latest/"
current_folder = os.path.dirname(os.path.abspath(__file__))
python_folder = os.path.join(current_folder, "python")

file_list = [
os.path.join(current_folder, "package.py"),
]


try:
    shutil.rmtree(latest_release)
except:
    pass

copytree(python_folder, os.path.join(latest_release, "python"))
for item in file_list:
    copyfile(item, latest_release)


print("*"*30)
print("Package copied to:\n%s" % latest_release)
print("*"*30)
print("Success...")