import FreeCAD as App
import FreeCADGui as Gui
from PartOMagic.Base import Containers
from PartOMagic.Base.FilePlant import FCProject
from PartOMagic.Base import Parameters

from PartOMagic.Gui.AACommand import AACommand, CommandError
from PartOMagic.Gui.Utils import Transaction
from PartOMagic.Gui import Observer


def duplicateObjects(objects, top_objects, target_cnt):
    with Transaction("PoM Duplicate"):
        with Observer.suspend():    
            doc : App.Document = objects[0].Document

            if Parameters.UseFileplantToDuplicate.get():
                objset = set(objects)
                namelist = [obj.Name for obj in doc.TopologicalSortedObjects if obj in objset][::-1]
                
                tmp_prj = FCProject.fromFC(doc, namelist)
                map = tmp_prj.mergeToFC(doc)
            else:
                copied_objects = doc.copyObject(objects)
                map = {old_obj.Name : new_obj.Name for (old_obj, new_obj) in zip(objects, copied_objects)}

            for obj in top_objects:
                new_top_obj = doc.getObject(map[obj.Name])
                Containers.addObjectTo(target_cnt, new_top_obj, b_advance_tip= True)





commands = []
class CommandDuplicateObject(AACommand):
    "Command duplicate objects"
    def GetResources(self):
        import PartDesignGui
        return {'CommandName': 'PartOMagic_Duplicate',
                'Pixmap'  : self.getIconPath("PartOMagic_Duplicate.svg"),
                'MenuText': "Duplicate objects",
                'Accel': "",
                'ToolTip': "Duplicate objects (container-aware). (Copy selected objects and all their children; don't copy all dependent objects)"}
        
    def RunOrTest(self, b_run):
        sel = Gui.Selection.getSelection()
        if len(sel)==0 :
            raise CommandError(self,"No object selected. Please select objects to duplicate, first.")
        else:
            if b_run: 
                (full_list, top_list, implicit_list) = Containers.expandList(sel)
                duplicateObjects(full_list, top_list, Containers.activeContainer())
commands.append(CommandDuplicateObject())

exportedCommands = AACommand.registerCommands(commands)