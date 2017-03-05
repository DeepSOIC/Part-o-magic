print("loading LeaveEnter")

import FreeCAD as App
import FreeCADGui as Gui
from PartOMagic.Gui.Utils import *
from PartOMagic.Base import Containers

import SketcherGui #needed for icons

class CommandEnter:
    "Command to enter a feature"
    def GetResources(self):
        from PartOMagic.Gui.Utils import getIconPath
        return {'Pixmap'  : getIconPath("Sketcher_EditSketch.svg"),
                'MenuText': "Enter object",
                'Accel': "",
                'ToolTip': "Enter object. (activate a container, or open a sketch for editing)"}
        
    def RunOrTest(self, b_run):
        sel = Gui.Selection.getSelection()
        if len(sel)==0 :
            raise CommandError("Enter Object", "Enter Object command. Please select an object to enter, first. It can be a container, or a sketch.")
        elif len(sel)==1:
            sel = screen(sel[0])
            ac = Containers.activeContainer()
            if Containers.isContainer(sel):
                if sel in Containers.getContainerChain(ac) + [ac]:
                    raise CommandError("Enter Object", "Already inside this object")
                if b_run: Containers.setActiveContainer(sel)
                if b_run: Gui.Selection.clearSelection()
            else:
                cnt = Containers.getContainer(sel)
                if ac is cnt:
                    if b_run: Gui.ActiveDocument.setEdit(sel)
                else:
                    if b_run: Containers.setActiveContainer(cnt)
        else:
            raise CommandError("Enter Object", "Enter Object command. You need to select exactly one object (you selected {num}).".format(num= len(sel)))
    
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
    Gui.addCommand('PartOMagic_Enter',  CommandEnter())




class CommandLeave:
    "Command to leave editing or a container"
    def GetResources(self):
        from PartOMagic.Gui.Utils import getIconPath
        return {'Pixmap'  : getIconPath("Sketcher_LeaveSketch.svg"),
                'MenuText': "Leave object",
                'Accel': "",
                'ToolTip': "Leave object. (close sketch editing, or close task dialog, or leave a container).",
                'CmdType': "ForEdit"}
        
    def RunOrTest(self, b_run):
        if Gui.ActiveDocument.getInEdit() is not None:
            if b_run: 
                Gui.ActiveDocument.resetEdit()
                App.ActiveDocument.recompute()
                App.ActiveDocument.commitTransaction()
        elif Gui.Control.activeDialog():
            if b_run:
                Gui.Control.closeDialog()
                App.ActiveDocument.recompute()
                App.ActiveDocument.commitTransaction()
        else:
            ac = Containers.activeContainer()
            if ac.isDerivedFrom("App::Document"):
                raise CommandError("Leave Object", "Nothing to leave.")
            if b_run: Containers.setActiveContainer(Containers.getContainer(ac))
            if b_run: Gui.Selection.clearSelection()
            if b_run: Gui.Selection.addSelection(ac)
    
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
    Gui.addCommand('PartOMagic_Leave',  CommandLeave())
def exportedCommands():
    return ['PartOMagic_Enter', 'PartOMagic_Leave']

