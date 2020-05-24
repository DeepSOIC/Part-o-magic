__all__ = [
"Icons",
]

def importAll():
    from . import Icons

    
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
