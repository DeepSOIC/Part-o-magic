
import FreeCAD as App
if App.GuiUp:
    import FreeCADGui as Gui
from PartOMagic.Gui.Utils import *
from PartOMagic.Base import Containers


def CreateShapeBinder(feature):
    App.ActiveDocument.openTransaction("Create Shapebinder")
    Gui.doCommand("f = App.ActiveDocument.addObject('PartDesign::ShapeBinder','ShapeBinder')")
    Gui.doCommand("f.Support = [App.ActiveDocument.{feat},('')]".format(feat= feature.Name))
    Gui.doCommand("f.recompute()")
    App.ActiveDocument.commitTransaction()
    Gui.doCommand("Gui.Selection.clearSelection()")
    Gui.doCommand("Gui.Selection.addSelection(f)")

from PartOMagic.Gui.AACommand import AACommand, CommandError
commands = []
class CommandShapeBinder(AACommand):
    "Command to create a shapebinder"
    def GetResources(self):
        import PartDesignGui        
        return {'CommandName': "PartOMagic_ShapeBinder",
                'Pixmap'  : self.getIconPath("PartDesign_ShapeBinder.svg"),
                'MenuText': "Shapebinder",
                'Accel': "",
                'ToolTip': "Shapebinder. (create a cross-container shape reference)"}
        
    def RunOrTest(self, b_run):
        sel = Gui.Selection.getSelection()
        if len(sel)==0 :
            raise CommandError(self, "Shapebinder command. Please select an object to import to active container, first. The object must be geometry.")
        elif len(sel)==1:
            sel = screen(sel[0])
            ac = Containers.activeContainer()
            if sel in Containers.getDirectChildren(ac):
                raise CommandError(self, u"{feat} is from active container ({cnt}). Please select an object belonging to another container.".format(feat= sel.Label, cnt= ac.Label))
            if sel in (Containers.getAllDependent(ac)+ [ac]):
                raise CommandError(self, "Can't create a shapebinder, because a circular dependency will result.")
            if b_run: CreateShapeBinder(sel)
        else:
            raise CommandError(self, u"Shapebinder command. You need to select exactly one object (you selected {num}).".format(num= len(sel)))
commands.append(CommandShapeBinder())

exportedCommands = AACommand.registerCommands(commands)