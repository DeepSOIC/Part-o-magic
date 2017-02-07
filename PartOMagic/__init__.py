__title__ = "Part-o-magic package"
__doc__ = """Experimental container automation for FreeCAD"""


__all__ = [
"Base",
"Gui",
"Features",
]

def importAll():
    "importAll(): imports all modules of Part-o-magic"
    from . import Base
    from . import Gui
    from . import Features
    for modstr in __all__:
        mod = globals()[modstr]
        if hasattr(mod, "importAll"):
            mod.importAll()

def reloadAll():
    "reloadAll(): reloads all modules of Part-o-magic. Useful for debugging."
    for modstr in __all__:
        mod = globals()[modstr]
        reload(mod)
        if hasattr(mod, "reloadAll"):
            mod.reloadAll()

    import FreeCAD
    if FreeCAD.GuiUp:
        addCommands()

def addCommands():
    pass
