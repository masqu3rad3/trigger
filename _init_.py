import sys

path = "%s/%s" % (sys.path[len(sys.path)-1],"tik_autorigger")

if not path in sys.path:
    sys.path.append(path)