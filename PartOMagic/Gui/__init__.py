print("Part-o-magic: loading Gui")


__all__ = [
"Utils",
"Observer",
"TempoVis",
"AACommand",
"Control",
"Tools",
"LinkTools",
"Icons",
"CommandCollection1",
"GlobalToolbar",
"View",
]

def importAll():
    from . import Utils
    from . import Observer
    from . import TempoVis
    from . import AACommand
    from . import Control
    from . import Tools
    from . import LinkTools
    from . import Icons
    from . import CommandCollection1
    from . import GlobalToolbar
    from . import View
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
