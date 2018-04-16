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
            repls = LT.replaceObject(old, new, [parent])
            with Transaction("Replace {old} with {new} in {scope}".format(old= old.Name, new= new.Name, scope= "project" if parent is None else parent.Name  )):
                LT.mass_replace(repls)
            
            kinds = [repl.relation.kind for repl in repls if repl.replaced]
                
            msg = (
                "Of total {n} links, replaced {n_links} regular links, {n_sublinks} subelement links, {n_expr} expression references. Failed: {n_fail}"
                " Please recompute to see the changes."
                .format(
                  n= len(repls), 
                  n_links= kinds.count('Link'), 
                  n_sublinks= kinds.count('Sublink'),
                  n_expr= kinds.count('Expression') + kinds.count('CellExpression'),
                  n_fail= len(kinds) - len(repls)
                )
            )
            
            msgbox('Part-o-magic Replace Object', msg)
            
commands.append(CommandReplaceObject())

exportedCommands = AACommand.registerCommands(commands)