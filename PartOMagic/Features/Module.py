import FreeCAD as App
if App.GuiUp:
    import FreeCADGui as Gui
import Part

import PartDesignGui #needed for icon

__title__="Module container"
__author__ = "DeepSOIC"
__url__ = ""

print("loading Module")

def transformCopy(shape, extra_placement = None):
    """transformCopy(shape, extra_placement = None): creates a deep copy shape with shape's placement applied to 
    the subelements (the placement of returned shape is zero)."""
    
    if extra_placement is None:
        extra_placement = App.Placement()
    ret = shape.copy()
    if ret.ShapeType == "Vertex":
        # oddly, on Vertex, transformShape behaves strangely. So we'll create a new vertex instead.
        ret = Part.Vertex(extra_placement.multVec(ret.Point))
    else:
        ret.transformShape(extra_placement.multiply(ret.Placement).toMatrix(), True)
        ret.Placement = App.Placement() #reset placement
    return ret


def makeModule(name):
    '''makeModule(name): makes a Module object.'''
    obj = App.ActiveDocument.addObject("Part::FeaturePython",name)
    proxy = _Module(obj)
    vp_proxy = _ViewProviderModule(obj.ViewObject)
    return obj

class _Module:
    "The Module object"
    def __init__(self,obj):
        self.Type = "Module"
        obj.addExtension("App::OriginGroupExtensionPython", self)
        obj.addProperty("App::PropertyLink","Tip","Module","Object to be exposed to the outside")
        
        obj.Proxy = self
        

    def execute(self,selfobj):
        from PartOMagic.Gui.Utils import screen
        if selfobj.Tip is not None:
            selfobj.Shape = transformCopy(screen(selfobj.Tip).Shape)
        else:
            selfobj.Shape = Part.Shape()
            
    def advanceTip(self, selfobj, new_object):
        print("advanceTip")
        from PartOMagic.Gui.Utils import screen
        old_tip = screen(selfobj.Tip)
        new_tip = old_tip
        if old_tip is None:
            new_tip = new_object
        if old_tip in new_object.OutList:
            new_tip = new_object
        
        if new_tip is None: return
        if new_tip is old_tip: return
        if new_tip.Name.startswith("Clone"): return
        if new_tip.Name.startswith("ShapeBinder"): return
        selfobj.Tip = new_tip
        
class _ViewProviderModule:
    "A View Provider for the Module object"

    def __init__(self,vobj):
        vobj.addExtension("Gui::ViewProviderGeoFeatureGroupExtensionPython", self)
        vobj.Proxy = self
        
    def getIcon(self):
        from PartOMagic.Gui.Utils import getIconPath
        return getIconPath("PartDesign_Body_Tree.svg")

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
    
    def doubleClicked(self, vobj):
        from PartOMagic.Gui.Observer import activeContainer, setActiveContainer
        ac = activeContainer()
        if ac is vobj.Object:
            setActiveContainer(vobj.Object.Document) #deactivate self
        else:
            setActiveContainer(vobj.Object) #activate self
            Gui.Selection.clearSelection()
        return True
    
    def activationChanged(self, vobj, old_active_container, new_active_container, event):
        # event: -1 = leaving (active container was self or another container inside, new container is outside)
        #        +1 = entering (active container was outside, new active container is inside)
        if event == +1:
            self.oldMode = vobj.DisplayMode
            vobj.DisplayMode = 'Group'
        elif event == -1:
            if self.oldMode == 'Group':
                self.oldMode = 'Flat Lines'
            vobj.DisplayMode = self.oldMode
  
    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

def CreateModule(name):
    App.ActiveDocument.openTransaction("Create Module")
    Gui.addModule("PartOMagic.Features.Module")
    Gui.doCommand("f = PartOMagic.Features.Module.makeModule(name = '"+name+"')")
    Gui.doCommand("PartOMagic.Base.Containers.setActiveContainer(f)")
    Gui.doCommand("Gui.Selection.clearSelection()")
    App.ActiveDocument.commitTransaction()


# -------------------------- /common stuff --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

class _CommandModule:
    "Command to create Module feature"
    def GetResources(self):
        from PartOMagic.Gui.Utils import getIconPath
        return {'Pixmap'  : getIconPath("PartDesign_Body_Create_New.svg"),
                'MenuText': "New Module container",
                'Accel': "",
                'ToolTip': "New Module container. Module is like PartDesign Body, but for Part workbench and friends."}
        
    def Activated(self):
        CreateModule(name = "Module")
            
    def IsActive(self):
        if App.ActiveDocument:
            return True
        else:
            return False

if App.GuiUp:
    Gui.addCommand('PartOMagic_Module',  _CommandModule())

# -------------------------- /Gui command --------------------------------------------------

def exportedCommands():
    return ['PartOMagic_Module']
