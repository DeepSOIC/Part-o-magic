print("Part-o-magic: loading FilePlant")


__all__ = [
'FCProject',
'FCObject',
'FCProperty',
'PropertyExpressionEngine',
]

def importAll():
    from . import FCProject
    from . import FCObject
    from . import FCProperty
    from . import PropertyExpressionEngine
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
