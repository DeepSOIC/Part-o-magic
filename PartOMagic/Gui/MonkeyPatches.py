import FreeCAD as App
from PartOMagic.Base import Parameters

def move_input_objects(self, objects):
    """move_input_objects has been monkeypatched by Part-o-magic"""
    targetGroup = None
    for obj in objects:
        obj.Visibility = False
        parent = obj.getParent()
        if parent:
            # parent.removeObject(obj)
            targetGroup = parent
    return None #targetGroup

def monkeypatch_Part():
    try:
        from BOPTools import BOPFeatures
    except ImportError:
        App.Console.PrintLog("Part-o-magic: BOPFeatures missing, skipping monkeypatching\n")
    else:
        if hasattr(BOPFeatures.BOPFeatures, 'move_input_objects'):
            BOPFeatures.BOPFeatures.move_input_objects = move_input_objects
            App.Console.PrintLog("Part-o-magic: monkeypatching Part.BOPTools.BOPFeatures done\n")
        else:
            App.Console.PrintWarning("Part-o-magic: monkeypatching Part.BOPTools.BOPFeatures failed - move_input_objects() method is missing\n")

def monkeypatch_all():
    try:
        monkeypatch_Part()
    except Exception as err:
        import sys
        b_tb =  err is sys.exc_info()[1]
        if b_tb:
            import traceback
            tb = traceback.format_exc()
            App.Console.PrintError(tb+'\n')

if Parameters.EnableObserver.get() and Parameters.EnablePartOMagic.get():
    monkeypatch_all()