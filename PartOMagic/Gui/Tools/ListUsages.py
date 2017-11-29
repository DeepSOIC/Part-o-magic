print("loading ListUsages")

import FreeCAD as App
import FreeCADGui as Gui
from PartOMagic.Gui.Utils import *
from PartOMagic.Base import Containers

from PartOMagic.Gui.AACommand import AACommand, CommandError

commands = []
class CommandListUsages(AACommand):
    "Command to show a list of objects that use the object"
    def GetResources(self):
        import PartDesignGui
        return {'CommandName': 'PartOMagic_ListUsages',
                'Pixmap'  : self.getIconPath("PartOMagic_ListUsages.svg"),
                'MenuText': "Used by who?",
                'Accel': "",
                'ToolTip': "Used by who? (lists which objects use selected object, and how)"}
        
    def RunOrTest(self, b_run):
        sel = Gui.Selection.getSelection()
        if len(sel)!=1 :
            raise CommandError(self, "Please select one object. Currently selected {n}".format(n= len(sel)))
        if b_run:
            from PartOMagic.Base import LinkTools as LT
            uses = LT.findLinksTo(sel[0])
            uses_str = '\n'.join([
                (lnk_from.Name + '.' + prop +' (' + kind + ')') for (lnk_from, kind, prop, lnk_to) in uses  ])
            if len(uses_str) == 0: uses_str = "(nothing)"
                
            links = LT.getDependencies(sel[0])
            links_str = '\n'.join([
                (lnk_to.Name + " as " + prop +' (' + kind + ')') for (lnk_from, kind, prop, lnk_to) in links  ])
            if len(links_str) == 0: links_str = "(nothing)"
                
            msg = ("==== {obj} uses: ====\n"
                   "{links_str}\n\n"
                   "====Links to {obj}:====\n"
                   "{uses_str}").format(obj= sel[0].Label, uses_str= uses_str, links_str= links_str)

            from PySide import QtGui
            mb = QtGui.QMessageBox()
            mb.setIcon(mb.Icon.Information)
            mb.setText(msg)
            mb.setWindowTitle("Used by who?")
            btnClose = mb.addButton(QtGui.QMessageBox.StandardButton.Close)
            btnCopy = mb.addButton("Copy to clipboard", QtGui.QMessageBox.ButtonRole.ActionRole)
            btnSelect = mb.addButton("Select dependent objects", QtGui.QMessageBox.ButtonRole.ActionRole)
            mb.setDefaultButton(btnClose)
            mb.exec_()
            
            if mb.clickedButton() is btnCopy:
                cb = QtGui.QClipboard()
                cb.setText(msg)
            if mb.clickedButton() is btnSelect:
                objs = set([obj for obj,dummy,dummy,dummy in uses])
                Gui.Selection.clearSelection()
                for obj in objs:
                    Gui.Selection.addSelection(obj)

commands.append(CommandListUsages())

exportedCommands = AACommand.registerCommands(commands)