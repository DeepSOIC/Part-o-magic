print("loading Features")


__all__ = [
"Part",
"Module",
"ShapeGroup",
"ShapeBinder",
"Exporter",
"PartDesign"
]

def importAll():
    from . import Part
    from . import Module
    from . import ShapeGroup
    from . import ShapeBinder
    from . import Exporter
    from . import PartDesign

    for modstr in __all__:
        mod = globals()[modstr]
        if hasattr(mod, "importAll"):
            mod.importAll()

def reloadAll():
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
