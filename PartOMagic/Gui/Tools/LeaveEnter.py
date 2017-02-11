print("loading LeaveEnter")

import FreeCAD as App
import FreeCADGui as Gui
from PartOMagic.Gui.Utils import *
from PartOMagic.Base import Containers

class CommandEnter:
    "Command to create Module feature"
    def GetResources(self):
        from PartOMagic.Gui.Utils import getIconPath
        return {'Pixmap'  : getIconPath("Sketcher_EditSketch.svg"),
                'MenuText': "Enter object",
                'Accel': "",
                'ToolTip': "Enter object. (activate a container, or open a sketch for editing)."}
        
    def RunOrTest(self, b_run):
        sel = Gui.Selection.getSelection()
        if len(sel)==0 :
            raise CommandError("Enter Object", "Enter Object command. Please select an object to enter, first. It can be a container, or a sketch")
        elif len(sel)==1:
            sel = screen(sel[0])
            ac = Containers.activeContainer()
            if Containers.isContainer(sel):
                if sel in Containers.getContainerChain(ac) + [ac]:
                    raise CommandError("Enter Object", "Already inside this object")
                if b_run: Containers.setActiveContainer(sel)
            else:
                cnt = Containers.getContainer(sel)
                if ac is cnt:
                    if b_run: sel.ViewObject.startEditing()
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
        #return True #temporarily disabled. Fixes mysterious Module tip changes
        
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

def exportedCommands():
    return ['PartOMagic_Enter']

