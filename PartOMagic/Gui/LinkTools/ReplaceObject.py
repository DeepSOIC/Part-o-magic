import FreeCAD as App
import FreeCADGui as Gui
from PartOMagic.Gui.Utils import *
from PartOMagic.Base import Containers

from PartOMagic.Gui.AACommand import AACommand, CommandError

commands = []
class CommandReplaceObject(AACommand):
    "Command to replace an object in parametric history with another object"
    def GetResources(self):
        import PartDesignGui
        return {'CommandName': 'PartOMagic_ReplaceObject',
                'Pixmap'  : self.getIconPath("PartOMagic_ReplaceObject.svg"),
                'MenuText': "Replace object",
                'Accel': "",
                'ToolTip': "Replace object. Select new, old, and parent. Order matters. Parent is optional."}
        
    def RunOrTest(self, b_run):
        sel = Gui.Selection.getSelection()
        if 2 < len(sel) < 3 :
            raise CommandError(self, "Please select two or three objects. Currently selected {n}".format(n= len(sel)))
        if b_run:
            old = sel[0]
            new = sel[1]
            parent = sel[2] if len(sel) > 2 else None
                
            from PartOMagic.Base import LinkTools as LT
            rels = LT.findLinksTo(old)
            avoid = LT.getAllDependencyObjects(new)
            avoid.add(new)
            repls = [LT.Replacement(rel, new) for rel in rels]
            
            n_checked = 0
            for repl in repls:
                if repl.relation.linking_object in avoid:
                    repl.disable("dependency loop")
                repl.checked = not(repl.disabled)
                if parent:
                    if repl.relation.linking_object is not parent:
                        repl.checked = False
                if repl.checked:
                    n_checked += 1

            if len(repls) == 0:
                raise CommandError(self, u"Nothing depends on {old}, nothing to replace.".format(old= old.Label))
            
            if n_checked == 0 and len(repls)>0:
                msgBox("No regular replacable dependencies found, nothing uses {old}. Please pick wanted replacements manually in the dialog.".format(old= old.Label))
            
            
            import TaskReplace
            task = TaskReplace.TaskReplace(repls, old.Document, message= u"Replacing {old} with {new}".format(old= old.Label, new= new.Label))
            
commands.append(CommandReplaceObject())

exportedCommands = AACommand.registerCommands(commands)