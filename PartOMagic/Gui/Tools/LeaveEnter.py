print("Part-o-magic: loading LeaveEnter")

import FreeCAD as App
import FreeCADGui as Gui
from PartOMagic.Gui.Utils import screen
from PartOMagic.Base import Containers
from PartOMagic.Gui.AACommand import AACommand, CommandError

commands = []

class _CommandEnter(AACommand):
    "Command to enter a feature"
    def GetResources(self):
        import SketcherGui #needed for icons
        return {'CommandName': 'PartOMagic_Enter',
                'Pixmap'  : self.getIconPath("Sketcher_EditSketch.svg"),
                'MenuText': "Enter object",
                'Accel': "",
                'ToolTip': "Enter object. (activate a container, or open a sketch for editing)"}
        
    def RunOrTest(self, b_run):
        if Gui.ActiveDocument:
            in_edit = Gui.ActiveDocument.getInEdit()
            if in_edit is not None:
                raise CommandError(self, u"{object} is currently being edited. Can't enter anything.".format(object= in_edit.Object.Label))
        sel = Gui.Selection.getSelection()
        if len(sel)==0 :
            raise CommandError(self, "Enter Object command. Please select an object to enter, first. It can be a container, or a sketch.")
        elif len(sel)==1:
            sel = screen(sel[0])
            ac = Containers.activeContainer()
            if Containers.isContainer(sel):
                if sel in Containers.getContainerChain(ac) + [ac]:
                    raise CommandError(self, "Already inside this object")
                if b_run: Containers.setActiveContainer(sel)
                if b_run: Gui.Selection.clearSelection()
            else:
                cnt = Containers.getContainer(sel)
                if ac is cnt:
                    if b_run: Gui.ActiveDocument.setEdit(sel)
                else:
                    if b_run: Containers.setActiveContainer(cnt)
        else:
            raise CommandError(self, u"Enter Object command. You need to select exactly one object (you selected {num}).".format(num= len(sel)))            
commandEnter = _CommandEnter()
commands.append(commandEnter)



class _CommandLeave(AACommand):
    "Command to leave editing or a container"
    def GetResources(self):
        import SketcherGui #needed for icons
        return {'CommandName': 'PartOMagic_Leave',
                'Pixmap'  : self.getIconPath("Sketcher_LeaveSketch.svg"),
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
                raise CommandError(self, "Nothing to leave.")
            if b_run: Containers.setActiveContainer(Containers.getContainer(ac))
            if b_run: Gui.Selection.clearSelection()
            if b_run: Gui.Selection.addSelection(ac)    
            if b_run: App.ActiveDocument.recompute() #fixme: scoped recompute, maybe?
commandLeave = _CommandLeave()
commands.append(commandLeave)

exportedCommands = AACommand.registerCommands(commands)

