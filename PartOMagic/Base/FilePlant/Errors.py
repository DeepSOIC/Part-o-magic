
class FileplantError(RuntimeError):
    pass
class NameCollisionError(FileplantError):
    pass


def warn(message):
    import sys
    freecad = sys.modules.get('FreeCAD', None)
    if freecad is None:
        print(message)
    else:
        freecad.Console.PrintWarning(message + '\n')