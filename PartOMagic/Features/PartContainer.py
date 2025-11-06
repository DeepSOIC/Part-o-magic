
import FreeCAD as App
if App.GuiUp:
    import FreeCADGui as Gui
from PartOMagic.Gui.Utils import Transaction
from PartOMagic.Base import Containers


def CreatePart():
    with Transaction("Create Part"):
        Gui.doCommand("f = App.ActiveDocument.addObject('App::Part','Part')")
        Gui.doCommand("PartOMagic.Gui.Observer.sortNow()")
        Gui.doCommand("PartOMagic.Gui.Observer.activateContainer(f)")
    Gui.doCommand("Gui.Selection.clearSelection()")

from PartOMagic.Gui.AACommand import AACommand, CommandError
commands = []
class CommandPart(AACommand):
    "Command to create a Part container"
    def GetResources(self):
        import PartDesignGui        
        return {'CommandName': "PartOMagic_Part",
                'Pixmap'  : self.getIconPath("Tree_Annotation.svg"),
                'MenuText': "New Part container",
                'Accel': "",
                'ToolTip': "New Part container. Creates an empty Part container."}        
    def RunOrTest(self, b_run):
        if b_run: CreatePart()
commands.append(CommandPart())

exportedCommands = AACommand.registerCommands(commands)