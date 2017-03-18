print("loading Tip")

import FreeCAD as App
import FreeCADGui as Gui
from PartOMagic.Gui.Utils import *
from PartOMagic.Base import Containers

from PartOMagic.Gui.AACommand import AACommand, CommandError


def MoveTip(container, new_tip):
    App.ActiveDocument.openTransaction("Set Tip")
    Gui.doCommand("cnt = App.ActiveDocument.{cnt}".format(cnt= container.Name))
    Gui.doCommand("cnt.Tip = App.ActiveDocument.{tip}".format(cnt= container.Name, tip= new_tip.Name))
    App.ActiveDocument.commitTransaction()
    Gui.doCommand("App.ActiveDocument.recompute()")

commands = []
class CommandSetTip(AACommand):
    "Command to set tip feature of a module/body"
    def GetResources(self):
        import PartDesignGui
        return {'CommandName': 'PartOMagic_SetTip',
                'Pixmap'  : self.getIconPath("PartDesign_MoveTip.svg"),
                'MenuText': "Set as Tip",
                'Accel': "",
                'ToolTip': "Set as Tip. (mark this object as final shape of containing module/body)"}
        
    def RunOrTest(self, b_run):
        sel = Gui.Selection.getSelection()
        if len(sel)==0 :
            raise CommandError(self, "Set as Tip command. Please select an object to become Tip, first. The object must be geometry. ")
        elif len(sel)==1:
            sel = screen(sel[0])
            ac = Containers.activeContainer()
            if not hasattr(ac, "Tip"):
                raise CommandError(self,"{cnt} can't have Tip object (it is not a module or a body).".format(cnt= ac.Label))
            if not sel in Containers.getDirectChildren(ac):
                raise CommandError(self, "{feat} is not from active container ({cnt}). Please select an object belonging to active container.".format(feat= sel.Label, cnt= ac.Label))
            if screen(ac.Tip) is sel:
                raise CommandError(self, "{feat} is already a Tip of ({cnt}).".format(feat= sel.Label, cnt= ac.Label))
            if b_run: ac.Tip = sel
        else:
            raise CommandError(self, "Set as Tip command. You need to select exactly one object (you selected {num}).".format(num= len(sel)))
commands.append(CommandSetTip())

exportedCommands = AACommand.registerCommands(commands)