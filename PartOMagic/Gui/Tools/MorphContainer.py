import FreeCAD as App
if App.GuiUp:
    import FreeCADGui as Gui

    
from PartOMagic.Base import Containers
from PartOMagic.Gui.Utils import DelayedExecute, Transaction

def morphContainer(src_container, dst_container):
    if not Containers.isContainer(src_container):
        raise TypeError("{obj} is not a container".format(obj= src_container.Label))
    if not Containers.isContainer(dst_container):
        raise TypeError("{obj} is not a container".format(obj= dst_container.Label))
    if src_container in Containers.getContainerChain(dst_container):
        raise Containers.ContainerTreeError("Cannot morph {src} into {dst}, because {src} contains {dst}"
                                            .format(src= src_container.Label, dst= dst_container.Label))
    
    doc = dst_container.Document

    #origin...
    if hasattr(src_container, "Origin") and hasattr(dst_container, "Origin"):
        if dst_container.Origin is not None: 
            doc.removeObject(dst_container.Origin.Name)
        dst_container.Origin = src_container.Origin; src_container.Origin = None
    
    #content
    assert(len(dst_container.Group) == 0)
    dst_container.Group = src_container.Group; src_container.Group = []
    
    #Tip
    if hasattr(src_container, "Tip") and hasattr(dst_container, "Tip"):
        tip_list = src_container.Tip
        if type(tip_list) is not list:
            tip_list = [tip_list] if tip_list is not None else []
        if type(dst_container.Tip) is list:
            dst_container.Tip = tip_list
        else:
            if len(tip_list) == 0:
                dst_container.Tip = None
            elif len(tip_list) == 1:
                dst_container.Tip = tip_list[0]
            else:
                App.Console.PrintWarning("Target Tip can only point to one object. Source Tip points to {num}. Last object from source tip was taken."
                                         .format(num= len(tip_list)))
                dst_container.Tip = tip_list[-1]
    
    #other properties...
    
    properties_to_avoid = set([
        # these are avoided because they need manual treatment...
        'Group',
        'Origin',
        'ExpressionEngine',
        'Tip',
        #.. and these should never be copied at all
        'ExtensionProxy',
        'Proxy',
    ])
    
    properties_to_copy = []
    for prop in src_container.PropertiesList:
        if len(src_container.getEditorMode(prop))>0: # screen out read-only and hidden properties
            if not prop in properties_to_avoid:
                properties_to_copy.append(prop)
    
    for prop in properties_to_copy:
        copyProperty(src_container, dst_container, prop)
        
    #Copy expressions
    for expr in src_container.ExpressionEngine:
        dst_container.setExpression(*expr)
        
    #redirect links
    #(todo!)
    
    Containers.withdrawObject(src_container)
    doc.removeObject(src_container.Name)
    
def copyProperty(src, dst, prop):
    if hasattr(dst, prop):
        try:
            setattr(dst, prop, getattr(src, prop))
        except Exception as err:
            App.Console.PrintError("Failed to copy property {prop}: {err}".format(err= err.message, prop= prop))
    else:
        App.Console.PrintWarning("Target property missing: {prop}".format(prop= prop))

    
    
from Show.FrozenClass import FrozenClass
class WaitForNewContainer(FrozenClass):
    """WaitForNewContainer(command, source_container): waits for new object to be added to document. 
    Runs command.Activated() when it happens. The new object is stored in attribute target_container."""
    def defineAttributes(self):
        self.source_container = None # container to be morphed
        self.target_container = None 
        self.command = None #command that invoked the waiter
        self.is_done = False

        self._freeze()
        
    def __init__(self, command, source_container):
        self.defineAttributes()
        self.command = command
        command.waiter = self
        self.source_container = source_container
        App.addDocumentObserver(self) #this will call slotCreatedObject, eventually...
    
    def slotCreatedObject(self, feature): # this will call containerAdded(), eventually
        if feature.Document is not self.source_container.Document:
            return
        if self.is_done: 
            App.removeDocumentObserver(self)
            return
        self.is_done = True
        App.removeDocumentObserver(self)
        DelayedExecute(lambda feature=feature: self.containerAdded(feature)) #right now, the container was just created. We postpone the conversion, we want the object to be fully set up.
    
    def containerAdded(self, feature):
        self.target_container = feature
        self.command.Activated()


from PartOMagic.Gui.AACommand import AACommand, CommandError
commands = []

class CommandMorphContainer(AACommand):
    "Command to morph a container into a different one"
    def GetResources(self):
        import PartDesignGui
        return {'CommandName': 'PartOMagic_MorphContainer',
                'Pixmap'  : self.getIconPath("PartOMagic_MorphContainer.svg"),
                'MenuText': "Morph container",
                'Accel': "",
                'ToolTip': "Morph container (change container type). Select the container to be morphed, then invoke this tool, then create a container of new type."}
        
    def RunOrTest(self, b_run):
        # outline.
        # 0. user click calls Activated().
        # 1. set up self.waiter, which waits for new object to be created
        # 2. waiter calls Activated() of this command, and knows what object was created
        # 3. command removes waiter, and calls morphContainer
        
        if self.waiter is not None:
            if self.waiter.is_done:
                waiter = self.waiter
                self.waiter = None
                assert(b_run)
                #enforce PoM observer to put feature into appropriate container
                from PartOMagic.Gui import Observer as pomObserver
                if pomObserver.isRunning():
                    pomObserver.observerInstance.poll()
                    
                #check
                if not Containers.isContainer(waiter.target_container): 
                    raise CommandError(self, "You created {obj}, which isn't a container. Can't morph {src} into {objt}. Morphing canceled."
                                              .format(obj= waiter.target_container, 
                                                      objt= waiter.target_container,
                                                      src= waiter.source_container))
                #make sure active container is not being messed with...
                ac = Containers.activeContainer()
                if waiter.source_container in Containers.getContainerChain(ac)+[ac]:
                    pomObserver.activateContainer(Containers.getContainer(waiter.source_container))
                if waiter.target_container in Containers.getContainerChain(ac)+[ac]:
                    pomObserver.activateContainer(Containers.getContainer(waiter.target_container))
                
                # do it!
                with Transaction("Morph container"):
                    morphContainer(waiter.source_container, waiter.target_container)
                return
            else:
                raise CommandError(self, "(waiting for new container to be created...)")
        sel = Gui.Selection.getSelection()
        if len(sel)==0 :
            raise CommandError(self, self.GetResources()['ToolTip'])
        elif len(sel)==1:
            sel = sel[0]
            if not Containers.isContainer(sel):
                raise CommandError(self, "Selected object is not a container")
            ac = Containers.activeContainer()
            if sel in Containers.getContainerChain(ac)+[ac]:
                raise CommandError(self, "Deactivate the container to be morphed first, please.")
            if b_run: self.waiter = WaitForNewContainer(self, sel)
            if b_run: Gui.Selection.clearSelection()
        else:
            raise CommandError(self, "You need to select exactly one object (you selected {num}), ad it must be a container.".format(num= len(sel)))
commands.append(CommandMorphContainer(waiter= None))


exportedCommands = AACommand.registerCommands(commands)