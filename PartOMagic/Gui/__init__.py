print("loading Gui")


__all__ = [
"Utils",
"Observer",
"TempoVis",
"Tools",
"Icons",
]

def importAll():
    from . import Utils
    from . import Observer
    from . import TempoVis
    from . import Tools
    from . import Icons
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
