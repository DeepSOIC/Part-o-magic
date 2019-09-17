print("Part-o-magic: loading Features")


__all__ = [
"Instance",
"MuxAssembly",
]

def importAll():
    from . import Instance
    from . import MuxAssembly

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
        if not hasattr(mod, 'reloadAll'): #do not add subpackages
            if hasattr(mod, "exportedCommands"):
                result += mod.exportedCommands()
    return result
