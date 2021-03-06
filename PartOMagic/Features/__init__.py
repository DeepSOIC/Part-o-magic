

__all__ = [
"PartContainer",
"Module",
"ShapeGroup",
"ShapeBinder",
"Ghost",
"Exporter",
"PartDesign",
"AssyFeatures"
]

def importAll():
    from . import PartContainer
    from . import Module
    from . import ShapeGroup
    from . import ShapeBinder
    from . import Ghost
    from . import Exporter
    from . import PartDesign
    from . import AssyFeatures

    for modstr in __all__:
        mod = globals()[modstr]
        if hasattr(mod, "importAll"):
            mod.importAll()

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
        if not hasattr(mod, 'reloadAll'): #do not add subpackages (PartDesign)
            if hasattr(mod, "exportedCommands"):
                result += mod.exportedCommands()
    return result
