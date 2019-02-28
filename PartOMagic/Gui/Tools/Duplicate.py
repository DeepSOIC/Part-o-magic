print("loading Duplicate")

import FreeCAD as App
import FreeCADGui as Gui
from PartOMagic.Base import Containers
from PartOMagic.Base.FilePlant import FCProject

from PartOMagic.Gui.AACommand import AACommand, CommandError
from PartOMagic.Gui.Utils import Transaction
from PartOMagic.Gui import Observer


def duplicateObjects(objects, top_objects, target_cnt):
    with Transaction("PoM Duplicate"):
        keeper = Observer.suspend()
        namelist = [obj.Name for obj in objects]
        doc = objects[0].Document
        tmp_prj = FCProject.fromFC(doc, namelist)
        map = tmp_prj.mergeToFC(doc)
        for obj in top_objects:
            new_top_obj = doc.getObject(map[obj.Name])
            Containers.addObjectTo(target_cnt, new_top_obj, b_advance_tip= True)
        keeper.release()

def expandList(objects):
    """Expands the list of objects to include all children of all container in the list.
    Returns tuple of lists: (full_list, top_list, implicit_list). Full_list has all objects. 
    Top_list has top-level objects (those not being a child of any of objects). 
    Implicit_list is of those being a child of any of objects."""
    
    #filter out duplicates, just in case. Do it the hard way, to preserve order (but i'm not sure order preservation ever matters)
    seen = set()
    filtered = []
    for obj in objects:
        if obj not in seen:
            filtered.append(obj)
        seen.add(obj)
    objects = filtered; del(filtered)
    
    #scan the tree
    to_add = []
    added = set(objects)
    top_set = set(objects)
    implicit_set = set()
    for obj in objects:
        if Containers.isContainer(obj):
            for child in Containers.recursiveChildren(obj):
                top_set.discard(child)
                implicit_set.add(child)
                to_add.append(child)
                added.add(child)
    full_list = objects + to_add
    top_list = [obj for obj in full_list if obj in top_set] # could just =list(top_set). But we want to preserve order as much as possible.
    implicit_list = [obj for obj in full_list if obj in implicit_set]
    return (full_list, top_list, implicit_list)

commands = []
class CommandDuplicateObject(AACommand):
    "Command to transfer an object into active container"
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
                (full_list, top_list, implicit_list) = expandList(sel)
                duplicateObjects(full_list, top_list, Containers.activeContainer())
commands.append(CommandDuplicateObject())

exportedCommands = AACommand.registerCommands(commands)