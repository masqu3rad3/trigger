import sys
paths=sys.path
pathRoot = None
pathToAdd = "/tik_autorigger"
for i in paths:
    if "maya/scripts" in i:
        pathRoot = i
if pathRoot != None:
    sys.path.append(pathRoot+pathToAdd)
else:
    raise ValueError('Cannot get the script path to Tik_AutoRigger')
