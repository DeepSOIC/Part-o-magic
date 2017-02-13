print("loading Tip")

import FreeCAD as App
import FreeCADGui as Gui
from PartOMagic.Gui.Utils import *
from PartOMagic.Base import Containers

def MoveTip(container, new_tip):
    App.ActiveDocument.openTransaction("Set Tip")
    Gui.doCommand("cnt = App.ActiveDocument.{cnt}".format(cnt= container.Name))
    Gui.doCommand("cnt.Tip = App.ActiveDocument.{tip}".format(cnt= container.Name, tip= new_tip.Name))
    App.ActiveDocument.commitTransaction()
    Gui.doCommand("App.ActiveDocument.recompute()")


class CommandSetTip:
    "Command to set tip feature of a module/body"
    def GetResources(self):
        from PartOMagic.Gui.Utils import getIconPath
        return {'Pixmap'  : getIconPath("PartDesign_MoveTip.svg"),
                'MenuText': "Set as Tip",
                'Accel': "",
                'ToolTip': "Set as Tip. (mark this object as final shape of containing module/body)"}
        
    def RunOrTest(self, b_run):
        sel = Gui.Selection.getSelection()
        if len(sel)==0 :
            raise CommandError("Set as Tip", "Set as Tip command. Please select an object to become Tip, first. The object must be geometry. ")
        elif len(sel)==1:
            sel = screen(sel[0])
            ac = Containers.activeContainer()
            if not hasattr(ac, "Tip"):
                raise CommandError("Set as Tip","{cnt} can't have Tip object (it is not a module or a body).".format(cnt= ac.Label))
            if not sel in getDirectChildren(ac):
                raise CommandError("Set as Tip", "{feat} is not from active container ({cnt}). Please select an object belonging to active container.".format(feat= sel.Label, cnt= ac.Label))
            if screen(ac.Tip) is sel:
                raise CommandError("Set as Tip", "{feat} is already a Tip of ({cnt}).".format(feat= sel.Label, cnt= ac.Label))
            if b_run: ac.Tip = sel
        else:
            raise CommandError("Set as Tip", "Set as Tip command. You need to select exactly one object (you selected {num}).".format(num= len(sel)))
    
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
    Gui.addCommand('PartOMagic_SetTip',  CommandSetTip())
    
def exportedCommands():
    return ['PartOMagic_SetTip']

