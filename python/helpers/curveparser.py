import sys
import re
def curveParser(melCommand):
    """
    This function parses the mel curve creation command to pymel. Useful for the situations where you want to design curves freely and easily convert the command to pymel equivilant
    Args:
        melCommand: (String)
    Returns: (String) pymel command as string (needs to be executed)
    """
    ## get positions

    curveMode = re.findall(r'-d(..)', melCommand)
    curveMode = curveMode[0].replace(" ", "")

    p = melCommand.split("-p", 1)[1]
    p = p.split("-k", 1)[0]
    positions = p.split("-p")
    positions[0][0].strip(" ")
    posFormatted = ""
    for ws in range(len(positions)):
        pItem = positions[ws][1:-1]
        pItem = pItem.replace(" ", ",")
        # posFormatted=pItem
        pItem = "({0})".format(pItem)
        if not ws == 0 or ws == len(positions):
            posFormatted += ","
        posFormatted += pItem

    ## get keys
    k = melCommand.split("-k", 1)[1]
    keys = k.split("-k")
    # remove the last ';'
    keys[-1].replace(" ;", "")

    kFormatted = ""
    for x in range(len(keys)):
        pItem = keys[x][1:-1]
        pItem = pItem.replace(" ", "")

        if not x == 0 or x == len(keys):
            pItem = pItem.replace(";", "")
            kFormatted += ","

        kFormatted += pItem

    curveCommand = "cmds.curve(d={0}, p=[{1}], k=[{2}])".format(curveMode, posFormatted, kFormatted)
    print(curveCommand)
    return curveCommand

if __name__ == '__main__':
    if sys.version_info.major > 2:
        melCommand = input()
    else:
        melCommand = raw_input()
    if melCommand:
        curveParser(melCommand)