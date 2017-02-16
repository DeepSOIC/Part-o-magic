print("loading ShapeBinder")

import FreeCAD as App
if App.GuiUp:
    import FreeCADGui as Gui
from PartOMagic.Gui.Utils import *
from PartOMagic.Base import Containers

import PartDesignGui

def CreateShapeBinder(feature):
    App.ActiveDocument.openTransaction("Create Shapebinder")
    Gui.doCommand("f = App.ActiveDocument.addObject('PartDesign::ShapeBinder','ShapeBinder')")
    Gui.doCommand("f.Support = [App.ActiveDocument.{feat},('')]".format(feat= feature.Name))
    Gui.doCommand("f.recompute()")
    App.ActiveDocument.commitTransaction()
    Gui.doCommand("Gui.Selection.clearSelection()")
    Gui.doCommand("Gui.Selection.addSelection(f)")

class CommandShapeBinder:
    "Command to create a shapebinder"
    def GetResources(self):
        from PartOMagic.Gui.Utils import getIconPath
        return {'Pixmap'  : getIconPath("PartDesign_ShapeBinder.svg"),
                'MenuText': "Shapebinder",
                'Accel': "",
                'ToolTip': "Shapebinder. (create a cross-container shape reference)"}
        
    def RunOrTest(self, b_run):
        sel = Gui.Selection.getSelection()
        if len(sel)==0 :
            raise CommandError("Shapebinder", "Shapebinder command. Please select an object to import to active container, first. The object must be geometry.")
        elif len(sel)==1:
            sel = screen(sel[0])
            ac = Containers.activeContainer()
            if sel in Containers.getDirectChildren(ac):
                raise CommandError("Shapebinder", "{feat} is from active container ({cnt}). Please select an object belonging to another container.".format(feat= sel.Label, cnt= ac.Label))
            if sel in (Containers.getAllDependent(ac)+ [ac]):
                raise CommandError("ShapeBinder", "Can't create a shapebinder, because a circular dependency will result.")
            if b_run: CreateShapeBinder(sel)
        else:
            raise CommandError("Shapebinder", "Shapebinder command. You need to select exactly one object (you selected {num}).".format(num= len(sel)))
    
    def Activated(self):
        try:
            self.RunOrTest(b_run= True)
        except Exception as err:
            msgError(err)
            
    def IsActive(self):
        if not App.ActiveDocument: return False
        try:
            self.RunOrTest(b_run= False)
            return True
        except CommandError as err:
            return False
        except Exception as err:
            App.Console.PrintError(repr(err))
            return True
            

if App.GuiUp:
    Gui.addCommand('PartOMagic_ShapeBinder',  CommandShapeBinder())
    
def exportedCommands():
    return ['PartOMagic_ShapeBinder']
