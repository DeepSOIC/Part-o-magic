print("loading FilePlant")


__all__ = [
'FCProject',
]

def importAll():
    from . import FCProject
    for modstr in __all__:
        mod = globals()[modstr]
        if hasattr(mod, 'importAll'):
            mod.importAll()

def reloadAll():
    try: #py2-3 compatibility: obtain reload() function
        reload
    except Exception:
        from importlib import reload
        
    for modstr in __all__:
        mod = globals()[modstr]
        reload(mod)
        if hasattr(mod, 'reloadAll'):
            mod.reloadAll()
