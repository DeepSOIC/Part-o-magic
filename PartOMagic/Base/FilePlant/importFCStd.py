import FreeCAD

def insert(filename,docname):
    #called when freecad wants to import a file
    from . import FCProject
    prj = FCProject.load(filename)
    try:
        doc = FreeCAD.getDocument(docname)
    except NameError:
        doc = FreeCAD.newDocument(docname)
    prj.mergeToFC(doc)
    
def export(exportList,filename,tessellation=1):
    #called when freecad exports a file
    from . import FCProject
    prj = FCProject.fromFC(FreeCAD.ActiveDocument,[obj.Name for obj in exportList])
    prj.writeFile(filename)
