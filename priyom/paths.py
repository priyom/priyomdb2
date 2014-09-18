import os

_pathdict = None

def paths(coderoot, dataroot=None):
    coderoot = os.path.abspath(coderoot)

    if not dataroot:
        dataroot = os.path.join(coderoot, "resources")
    else:
        dataroot = os.path.abspath(dataroot)

    templates = os.path.join(dataroot, "templates")
    css = os.path.join(dataroot, "css")
    l10n = os.path.join(dataroot, "messages")
    img = os.path.join(dataroot, "img")

    return {
        "_code": coderoot,
        "_data": dataroot,
        "templates": templates,
        "css": css,
        "l10n": l10n,
        "img": img
    }

def set_paths(pathdict):
    global _pathdict
    _pathdict = pathdict

def get_code_path(realm=None):
    global _pathdict
    if realm is None:
        realm = "_code"
    try:
        return _pathdict[realm]
    except KeyError:
        return os.path.join(_pathdict["_code"], realm)

def get_data_path(realm):
    global _pathdict
    try:
        return _pathdict[realm]
    except KeyError:
        return os.path.join(_pathdict["_data"], realm)
