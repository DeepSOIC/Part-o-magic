import FreeCAD as App
import FreeCADGui as Gui
import Part

__title__="Module container"
__author__ = "DeepSOIC"
__url__ = ""

print("loading Module")

def transformCopy(shape, extra_placement = None):
    """transformCopy(shape, extra_placement = None): creates a deep copy shape with shape's placement applied to 
    the subelements (the placement of returned shape is zero)."""
    
    if extra_placement is None:
        extra_placement = FreeCAD.Placement()
    ret = shape.copy()
    if ret.ShapeType == "Vertex":
        # oddly, on Vertex, transformShape behaves strangely. So we'll create a new vertex instead.
        ret = Part.Vertex(extra_placement.multVec(ret.Point))
    else:
        ret.transformShape(extra_placement.multiply(ret.Placement).toMatrix(), True)
        ret.Placement = FreeCAD.Placement() #reset placement
    return ret


def makeModule(name):
    '''makeModule(name): makes a Module object.'''
    obj = App.ActiveDocument.addObject("App::GeometryPython",name) # to be updated to Part::FeaturePython, once I figure out how to deal with viewproviders
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
        if selfobj.Tip is not None:
            selfobj.Shape = transformCopy(selfobj.Tip.Shape)
        else:
            selfobj.Shape = Part.Shape()
        
class _ViewProviderModule:
    "A View Provider for the Module object"

    def __init__(self,vobj):
        vobj.addExtension("Gui::ViewProviderGeoFeatureGroupExtensionPython", self)
        vobj.Proxy = self
        
    def getIcon(self):
        return getIconPath("PartOMagic_Module.svg")

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

  
    def setEdit(self,vobj,mode):
        from PartOMagic.Gui.Observer import setActiveContainer
        setActiveContainer(self.Object)
        #Gui.ActiveDocument.resetEdit()
        return True
    
    def unsetEdit(self,vobj,mode):
        return True

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

#    def claimChildren(self):
#        children = [self.Object.Base]
#        if self.Object.Stencil:
#            children.append(self.Object.Stencil)
#        return children

#    def onDelete(self, feature, subelements): # subelements is a tuple of strings
#        if not self.ViewObject.DontUnhideOnDelete:
#            try:
#                self.Object.Base.ViewObject.show()
#                if self.Object.Stencil:
#                    self.Object.Stencil.ViewObject.show()
#            except Exception as err:
#                App.Console.PrintError("Error in onDelete: " + err.message)
#        return True

def CreateModule(name):
    App.ActiveDocument.openTransaction("Create Module")
    Gui.addModule("PartOMagic.Features.Module")
    Gui.doCommand("f = PartOMagic.Features.Module.makeModule(name = '"+name+"')")
    #Gui.doCommand("PartOMagic.Gui.Observer.setActiveContainer(f)")
    App.ActiveDocument.commitTransaction()


# -------------------------- /common stuff --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

class _CommandModule:
    "Command to create Module feature"
    def GetResources(self):
        from PartOMagic.Gui.Utils import getIconPath
        return {'Pixmap'  : getIconPath("PartOMagic_Module.svg"),
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

exportedCommands = ['PartOMagic_Module']

# -------------------------- /Gui command --------------------------------------------------
