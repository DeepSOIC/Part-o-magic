print("loading MuxAssembly")

import FreeCAD as App
if App.GuiUp:
    import FreeCADGui as Gui
import Part

from PartOMagic.Features import Ghost as mGhost
Ghost = mGhost.Ghost
from PartOMagic.Base import Containers
from PartOMagic.Base.Utils import shallowCopy

__title__="MuxAssembly feature (converts assembly into compound)"
__author__ = "DeepSOIC"
__url__ = ""


def compoundFromAssembly(root, flatten, exclude, recursive = True, visit_set = None):
    if visit_set is None:
        visit_set = set()
    
    #recursion guard
    if root in visit_set:
        raise ValueError("Circular dependency")
    visit_set.add(root)
    
    if hasattr(root, 'Shape'):
        return root.Shape
    else:
        children = Containers.getDirectChildren(root)
        shapes = []
        for child in children:
            if child.Name in exclude:
                continue
            if child.isDerivedFrom('App::Origin'):
                continue #otherwise, origins create empty compounds - undesirable.
            if hasattr(child, 'Shape'):
                shapes.append(child.Shape)
            elif Containers.isContainer(child) and recursive:
                cmp = compoundFromAssembly(child, flatten, exclude, recursive, visit_set)
                if flatten:
                    shapes.extend(cmp.childShapes())
                else:
                    shapes.append(cmp)
        transform = root.Placement if hasattr(root, 'Placement') else None
        ret = Part.makeCompound(shapes)
        if transform is not None:
            ret.Placement = transform
        return ret

def make():
    '''make(): makes a MUX object.'''
    obj = App.ActiveDocument.addObject('Part::FeaturePython','MUX')
    proxy = MUX(obj)
    vp_proxy = ViewProviderMUX(obj.ViewObject)
    return obj

class MUX(Ghost):
    "MUX object, converts assembly into a compound"
    
    def __init__(self,selfobj):
        Ghost.__init__(self, selfobj)
        
        selfobj.IAm = 'PartOMagic.MUX'
        
        selfobj.addProperty('App::PropertyBool','FlattenCompound',"MUX","If true, compound nesting does not follow nesting of Parts. If False, compound nesting follows nexting of parts.")
        selfobj.addProperty('App::PropertyStringList', 'ExclusionList', "MUX", 'List of names of objects to exclude from compound')
        selfobj.addProperty('App::PropertyEnumeration', 'Traversal', "MUX", 'Sets if to look for shapes in nested containers')
        selfobj.Traversal = ['Direct children', 'Recursive']
        selfobj.Traversal = 'Recursive'
        
    def execute(self,selfobj):
        transform = self.getTransform(selfobj)
        selfobj.Shape = compoundFromAssembly(selfobj.Base, selfobj.FlattenCompound, selfobj.ExclusionList, recursive= selfobj.Traversal == 'Recursive')

        toleave,toenter = self.path
        if True: #(toleave and selfobj.UseForwardPlacements)  or  (toenter and selfobj.UseInversePlacements):
            selfobj.Placement = transform.multiply(selfobj.Base.Placement)
            selfobj.setEditorMode('Placement', 1) #read-only
        else:
            selfobj.setEditorMode('Placement', 0) #editable
        
        path = ''
        for cnt in toenter:
            path += '../'
        for cnt in toleave:
            path += cnt.Name + '/'
        labelf = u'{name} {label} from {path}' if toleave or toenter else u'{name} {label}'
        selfobj.Label = labelf.format(label= selfobj.Base.Label, name= selfobj.Name, path= path[:-1])
    
    
class ViewProviderMUX:
    "A View Provider for the MUX object"

    def __init__(self,vobj):
        vobj.Proxy = self
        
    def getIcon(self):
        from PartOMagic.Gui.Utils import getIconPath
        return getIconPath("PartOMagic_MUX.svg")

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
        
    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

def Create(sel):
    from PartOMagic.Gui.Utils import Transaction
    with Transaction("Create MUX"):
        Gui.addModule("PartOMagic.Features.AssyFeatures.MuxAssembly")
        Gui.doCommand("f = PartOMagic.Features.AssyFeatures.MuxAssembly.make()")
        Gui.doCommand("f.Base = App.ActiveDocument.{objname}".format(objname= sel.Name))
        Gui.doCommand("Gui.Selection.clearSelection()")
        Gui.doCommand("Gui.Selection.addSelection(f)")
        Gui.doCommand("App.ActiveDocument.recompute()")
        Gui.doCommand("f.Base.ViewObject.hide()")



# -------------------------- Gui command --------------------------------------------------
from PartOMagic.Gui.AACommand import AACommand, CommandError
commands = []
class CommandMUX(AACommand):
    "Command to create MUX feature"
    def GetResources(self):
        import PartDesignGui #needed for icon
        return {'CommandName': 'PartOMagic_MUXAssembly',
                'Pixmap'  : self.getIconPath("PartOMagic_MUX.svg"),
                'MenuText': "MUX assembly (Part to Compound)",
                'Accel': "",
                'ToolTip': "MUX Assembly. Creates a compound from shapes found in selected Part."}
        
    def RunOrTest(self, b_run):
        sel = Gui.Selection.getSelection()
        if len(sel)==0 :
            raise CommandError(self, "MUX Assembly command. Please select a Part container, then invoke the tool. A mux object will be created, a compound of all features of Part.")
        elif len(sel)==1:
            sel = sel[0]
            ac = Containers.activeContainer()
            if b_run: 
                if sel in (Containers.getAllDependent(ac)+ [ac]):
                    raise CommandError(self, "Can't create MUX here, because a circular dependency will result.")
                Create(sel)
        else:
            raise CommandError(self, u"MUX Assembly command. You need to select exactly one object (you selected {num}).".format(num= len(sel)))    
        
commands.append(CommandMUX())
# -------------------------- /Gui command --------------------------------------------------

exportedCommands = AACommand.registerCommands(commands)
