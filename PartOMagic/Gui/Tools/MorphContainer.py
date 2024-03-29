
import FreeCAD as App
if App.GuiUp:
    import FreeCADGui as Gui

    
from PartOMagic.Base import Containers
from PartOMagic.Gui.Utils import DelayedExecute, Transaction

def morphContainer(src_container, dst_container):
    if not Containers.isContainer(src_container):
        raise TypeError(u"{obj} is not a container".format(obj= src_container.Label))
    if not Containers.isContainer(dst_container):
        raise TypeError(u"{obj} is not a container".format(obj= dst_container.Label))
    if src_container in Containers.getContainerChain(dst_container):
        raise Containers.ContainerTreeError(u"Cannot morph {src} into {dst}, because {src} contains {dst}"
                                            .format(src= src_container.Label, dst= dst_container.Label))
    
    doc = dst_container.Document

    #origin...
    if hasattr(src_container, "Origin") and hasattr(dst_container, "Origin"):
        if dst_container.Origin is not None: 
            doc.removeObject(dst_container.Origin.Name)
        dst_container.Origin = src_container.Origin; src_container.Origin = None
    
    #content
    assert(len(dst_container.Group) == 0)
    g = src_container.Group
    src_container.Group = [] #withdraw first, add last - otherwise, error is thrown
    dst_container.Group = g 
    if hasattr(dst_container, 'Origin'):
        if hasattr(dst_container, 'Proxy') and dst_container.Origin is not None:
            #workaround for origin not being claimed as child on Py-powered containers
            dst_container.Group = [dst_container.Origin] + dst_container.Group 
        elif dst_container.Origin is not None and dst_container.Origin in dst_container.Group:
            #if converting Py container into c++-one, undo the workaround
            content = dst_container.Group 
            content.remove(dst_container.Origin)
    
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
                App.Console.PrintWarning(u"Target Tip can only point to one object. Source Tip points to {num}. Last object from source tip was taken.\n"
                                         .format(num= len(tip_list)))
                dst_container.Tip = tip_list[-1]
    
    #other properties...
    
    properties_to_avoid = set([
        # these are avoided because they need manual treatment...
        'Group',
        'Origin',
        'ExpressionEngine',
        'Tip',
        'Label',
        #.. and these should never be copied at all
        'ExtensionProxy',
        'Proxy',
    ])
    
    properties_to_copy = []
    for prop in src_container.PropertiesList:
        if len(src_container.getEditorMode(prop)) == 0: # screen out read-only and hidden properties
            if not prop in properties_to_avoid:
                properties_to_copy.append(prop)
    
    for prop in properties_to_copy:
        copyProperty(src_container, dst_container, prop)
        
    #Copy expressions
    for expr in src_container.ExpressionEngine:
        dst_container.setExpression(*expr)
        
    #redirect links
    substituteObjectInProperties(src_container, dst_container, doc.Objects)
    substituteObjectInExpressions(src_container, dst_container, doc.Objects)
    substituteObjectInSpreadsheets(src_container, dst_container, doc.Objects)
    
    label = src_container.Label
    label = label.replace(src_container.Name, dst_container.Name)
    
    Containers.withdrawObject(src_container)
    doc.removeObject(src_container.Name)
    
    #copy Label last, because otherwise it gets "001" at the end...
    dst_container.Label = label
    
def copyProperty(src, dst, prop):
    if hasattr(dst, prop):
        try:
            setattr(dst, prop, getattr(src, prop))
        except Exception as err:
            App.Console.PrintError(u"Failed to copy property {prop}: {err}\n".format(err= str(err), prop= prop))
    else:
        App.Console.PrintWarning(u"Target property missing: {prop}\n".format(prop= prop))

def substituteObjectInProperties(orig, new, within):
    """substituteObjectInProperties(orig, new, within): finds all links to orig in within, and redirects them to new. Skips containership links."""
    if hasattr(within, "isDerivedFrom") :
        within = [within]
    for obj in within:
        for prop in obj.PropertiesList:
            if prop == "Group": continue #leave containership management to PoM/FreeCAD...
            if prop == "Origin": continue
            typ = obj.getTypeIdOfProperty(prop)
            val = getattr(obj, prop)
            valchanged = False
            if typ == 'App::PropertyLink':
                if val is orig:
                    valchanged = True
                    val = new
            elif typ == 'App::PropertyLinkList':
                if orig in val:
                    valchanged = True
                    val = [(new if lnk is orig else lnk) for lnk in getattr(obj, prop)]
            elif typ == 'App::PropertyLinkSub':
                if val is not None and orig is val[0]:
                    valchanged = True
                    val = tuple([new] + val[1:])
            elif typ == 'App::PropertyLinkSubList':
                if orig in [lnk for lnk,subs in val]:
                    valchanged = True
                    val = [((new if lnk is orig else lnk), subs) for lnk,subs in val]
            if valchanged:
                try:
                    setattr(obj, prop, val)
                except Exception as err:
                    App.Console.PrintError(u"  not replaced in {obj}.{prop}. {err}\n".format(obj= obj.Name, prop= prop, err= str(err)))

                

def substituteObjectInExpressions(orig, new, within):
    if hasattr(within, "isDerivedFrom") :
        within = [within]
    for obj in within:
        for prop, expr in obj.ExpressionEngine:
            oldexpr = expr
            newexpr = replaceNameInExpression(expr, orig.Name, new.Name)
            if newexpr is not None:
                try:
                    obj.setExpression(prop, newexpr)
                except Exception as err:
                    App.Console.PrintError(str(err)+'\n')

def substituteObjectInSpreadsheets(orig, new, within):
    if hasattr(within, "isDerivedFrom") :
        within = [within]
    within = [obj for obj in within if obj.isDerivedFrom('Spreadsheet::Sheet')]
    for obj in within:
        for prop in obj.PropertiesList:
            try:
                expr = obj.getContents(prop) #raises ValueError if not a cell
                if not expr.startswith('='): raise ValueError()
            except ValueError:
                continue
            oldexpr = expr
            newexpr = replaceNameInExpression(expr, orig.Name, new.Name)
            if newexpr is not None:
                try:
                    obj.set(prop, newexpr)
                except Exception as err:
                    App.Console.PrintError(str(err)+'\n')

def replaceNameInExpression(expr, old_name, new_name):
    'If not found, returns None. If replaced, returns new expression.'
    global namechars
    if not "namechars" in vars():
        namechars = [chr(c) for c in range(ord('a'), ord('z')+1)]
        namechars += [chr(c) for c in range(ord('A'), ord('Z')+1)]
        namechars += [chr(c) for c in range(ord('0'), ord('9')+1)]
        namechars += ['_']
        namechars = set(namechars)

    valchanged = False
    n = len(old_name)
    i = len(expr)
    while True:
        i = expr.rfind(old_name, 0,i)
        if i == -1:
            break
        
        #match found, but that can be a match inside of a different name. Test if characters around are non-naming.
        match = True
        if i > 0:
            if expr[i-1] in namechars:
                match = False
        if i+n < len(expr):
            if expr[i+n] in namechars:
                match = False
        
        #replace it
        if match:
            valchanged = True
            expr = expr[0:i] + new_name + expr[i+n : ]
    if valchanged:
        return expr
    else:
        return None


class WaitForNewContainer(object):
    """WaitForNewContainer(command, source_container): waits for new object to be added to document. 
    Runs command.Activated() when it happens. The new object is stored in attribute target_container."""
    def defineAttributes(self):
        self.source_container = None # container to be morphed
        self.target_container = None 
        self.new_objects = []
        self.command = None #command that invoked the waiter
        self.is_done = False
        self._trigger = None # storage for DelayedExecute object

        #self._freeze()
        
    def __init__(self, command, source_container):
        self.defineAttributes()
        self.command = command
        command.waiter = self
        self.source_container = source_container
        App.addDocumentObserver(self) #this will call slotCreatedObject, eventually...
    
    def slotCreatedObject(self, feature): # this will call containerAdded(), eventually
        if feature.Document is not self.source_container.Document:
            return
        self.new_objects.append(feature)
        if self._trigger is None:
            self._trigger = DelayedExecute(self.containerAdded) #right now, the container was just created. We postpone the conversion, we want the object to be fully set up.
    
    def containerAdded(self):
        App.removeDocumentObserver(self)
        for obj in self.new_objects:
            if Containers.canBeActive(obj):
                if self.target_container is not None:
                    raise CommandError(self.command, "More than one container was created. I have no idea what to do! --Part-o-Magic")
                self.target_container = obj #if multiple objects had been created, pick one that is a container
        if self.target_container is None:
            self.target_container = self.new_objects[0] #return something... so that an error message is displayed.
        self.is_done = True
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
                    raise CommandError(self, u"You created {obj}, which isn't a container. Can't morph {src} into {objt}. Morphing canceled."
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
            raise CommandError(self, u"You need to select exactly one object (you selected {num}), ad it must be a container.".format(num= len(sel)))
commands.append(CommandMorphContainer(waiter= None))


exportedCommands = AACommand.registerCommands(commands)