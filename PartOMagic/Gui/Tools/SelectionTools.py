print("loading Duplicate")

import FreeCAD as App
import FreeCADGui as Gui
from PartOMagic.Base import Containers

from PartOMagic.Gui.AACommand import AACommand, CommandError
from PartOMagic.Gui.GroupCommand import GroupCommand
from PySide import QtCore, QtGui

def select(objects):
    km = QtGui.QApplication.keyboardModifiers()
    ctrl_is_down = bool(km & QtCore.Qt.ControlModifier)
    if not ctrl_is_down:
        Gui.Selection.clearSelection()
    for obj in objects:
        Gui.Selection.addSelection(obj)


commands = []
class CommandSelectExpand(AACommand):
    
    def GetResources(self):
        import PartDesignGui
        return {'CommandName': 'PartOMagic_Select_ChildrenRecursive',
                'Pixmap'  : self.getIconPath("PartOMagic_Select_ChildrenRecursive.svg"),
                'MenuText': "Select children (recursive)",
                'Accel': "",
                'ToolTip': "Select children (recursive). (add all children of selected objects to selection, recursively; only container childship is considered)"}
        
    def RunOrTest(self, b_run):
        sel = Gui.Selection.getSelection()
        if len(sel)==0 :
            raise CommandError(self,"No object selected. Please select something, first.")
        else:
            if b_run: 
                (full_list, top_list, implicit_list) = Containers.expandList(sel)
                select(implicit_list)
commands.append(CommandSelectExpand())

class CommandSelectChildren(AACommand):
    
    def GetResources(self):
        import PartDesignGui
        return {'CommandName': 'PartOMagic_Select_Children',
                'Pixmap'  : self.getIconPath("PartOMagic_Select_Children.svg"),
                'MenuText': "Select children",
                'Accel': "",
                'ToolTip': "Select children. (selects children of selected container)"}
        
    def RunOrTest(self, b_run):
        sel = Gui.Selection.getSelection()
        if len(sel)==0 :
            raise CommandError(self,"No object selected. Please select something, first.")
        else:
            if b_run: 
                new_sel = []
                for obj in sel:
                    if Containers.isContainer(obj):
                        new_sel.extend(Containers.getDirectChildren(obj))
                    else:
                        new_sel.extend(obj.ViewObject.claimChildren())
                select(new_sel)
commands.append(CommandSelectChildren())

class CommandSelectAll(AACommand):
    
    def GetResources(self):
        import PartDesignGui
        return {'CommandName': 'PartOMagic_Select_All',
                'Pixmap'  : self.getIconPath("PartOMagic_Select_All.svg"),
                'MenuText': "Select all (in active container)",
                'Accel': "",
                'ToolTip': "Select all (in active container). (select all objects in active container)"}
        
    def RunOrTest(self, b_run):
        if b_run: 
            children = Containers.getDirectChildren(Containers.activeContainer())
            select(children)
commands.append(CommandSelectAll())

class CommandSelectInvert(AACommand):
    
    def GetResources(self):
        import PartDesignGui
        return {'CommandName': 'PartOMagic_Select_Invert',
                'Pixmap'  : self.getIconPath("PartOMagic_Select_Invert.svg"),
                'MenuText': "Invert selection (in active container)",
                'Accel': "",
                'ToolTip': "Select all (in active container). (select all objects in active container)"}
        
    def RunOrTest(self, b_run):
        if b_run: 
            sel = set(Gui.Selection.getSelection())
            children = Containers.getDirectChildren(Containers.activeContainer())
            for child in children:
                if child in sel:
                    Gui.Selection.removeSelection(child)
                else:
                    Gui.Selection.addSelection(child)
commands.append(CommandSelectInvert())

class CommandSelectMem(AACommand):
    buffer = []
    def GetResources(self):
        import PartDesignGui
        return {'CommandName': 'PartOMagic_Select_BSwap',
                'Pixmap'  : self.getIconPath("PartOMagic_Select_BSwap.svg"),
                'MenuText': "Selection buffer swap",
                'Accel': "",
                'ToolTip': "Selection buffer swap. (restores previously remembered selection, and remembers current selection)"}
        
    def RunOrTest(self, b_run):
        if b_run: 
            sel = Gui.Selection.getSelectionEx()
            buf = self.buffer
            Gui.Selection.clearSelection()
            for it in buf:
                try:
                    it.Object #throws if the object has been deleted
                except Exception:
                    continue
                subs = it.SubElementNames
                pts = it.PickedPoints
                if subs:
                    for isub in range(len(subs)):
                        Gui.Selection.addSelection(it.Object, subs[isub], *pts[isub])
                else:
                    Gui.Selection.addSelection(it.Object)
            self.buffer = sel
commands.append(CommandSelectMem())
AACommand.registerCommands(commands)


Gui.addCommand('PartOMagic_SelectGroupCommand',
 GroupCommand(
    list_of_commands= [cmd.command_name for cmd in commands],
    menu_text= "Select",
    tooltip= ""
 )
)

exportedCommands = lambda:['PartOMagic_SelectGroupCommand']