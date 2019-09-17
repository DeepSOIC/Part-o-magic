print("Part-o-magic: loading TransferObject")

import FreeCAD as App
import FreeCADGui as Gui
from PartOMagic.Base import Containers

from PartOMagic.Gui.AACommand import AACommand, CommandError
from PartOMagic.Gui.Utils import Transaction


def TransferObject(objects, target_cnt):
    with Transaction("Transfer object"):
        for obj in objects:
            Containers.moveObjectTo(obj, target_cnt)

commands = []
class CommandTransferObject(AACommand):
    "Command to transfer an object into active container"
    def GetResources(self):
        import PartDesignGui
        return {'CommandName': 'PartOMagic_TransferObject',
                'Pixmap'  : self.getIconPath("PartOMagic_TransferObject.svg"),
                'MenuText': "Transfer object",
                'Accel': "",
                'ToolTip': "Transfer object. (withdraw selected object from its container into active container)"}
        
    def RunOrTest(self, b_run):
        sel = Gui.Selection.getSelection()
        if len(sel)==0 :
            raise CommandError(self,"No object selected. Please select an object from another container, first.")
        elif len(sel)==1:
            sel = sel[0]
            cnt = Containers.getContainer(sel)
            if cnt is Containers.activeContainer():
                raise CommandError(self, "This object is already in active container. Please select an object that is not in active container, or activate another container.")
            if b_run: TransferObject([sel], Containers.activeContainer())
        else:
            # multiple selection. Checking is involved. Let's just assume it's correct.
            if b_run: TransferObject(sel, Containers.activeContainer())
commands.append(CommandTransferObject())

exportedCommands = AACommand.registerCommands(commands)