print("Part-o-magic: loading View")


__all__ = [
"SnapView",
"XRay"
]

def importAll():
    from . import SnapView
    from . import XRay

def reloadAll():
    try: #py2-3 compatibility: obtain reload() function
        reload
    except Exception:
        from importlib import reload

    for modstr in __all__:
        mod = globals()[modstr]
        reload(mod)
        if hasattr(mod, "reloadAll"):
            mod.reloadAll()

def exportedCommands():
    result = []
    for modstr in __all__:
        mod = globals()[modstr]
        if hasattr(mod, "exportedCommands"):
            result += mod.exportedCommands()
    return result
