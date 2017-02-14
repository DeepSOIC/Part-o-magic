print("loading Icons")


__all__ = [
"Icons",
]

def importAll():
    from . import Icons

    
def reloadAll():
    for modstr in __all__:
        mod = globals()[modstr]
        reload(mod)
        if hasattr(mod, "reloadAll"):
            mod.reloadAll()
