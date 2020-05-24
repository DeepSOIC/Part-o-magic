import FreeCAD as App
if App.GuiUp:
    import FreeCADGui as Gui
import Part

__title__="Module container"
__author__ = "DeepSOIC"
__url__ = ""


from PartOMagic.Base.Utils import transformCopy_Smart

def makeModule(name):
    '''makeModule(name): makes a Module object.'''
    obj = App.ActiveDocument.addObject("Part::FeaturePython",name)
    proxy = _Module(obj)
    origin = App.ActiveDocument.addObject('App::Origin', 'Origin')
    obj.Origin = origin
    vp_proxy = _ViewProviderModule(obj.ViewObject)
    return obj

class _Module:
    "The Module object"
    def __init__(self,obj):
        self.Type = "Module"
        obj.addExtension('App::OriginGroupExtensionPython', self)
        try:
            obj.addProperty('App::PropertyLinkChild','Tip',"Module","Object to be exposed to the outside")
        except Exception:
            #for older FC
            obj.addProperty('App::PropertyLink','Tip',"Module","Object to be exposed to the outside") 
        
        obj.Proxy = self
        
    def execute(self,selfobj):
        from PartOMagic.Gui.Utils import screen
        if selfobj.Tip is not None:
            selfobj.Shape = transformCopy_Smart(screen(selfobj.Tip).Shape, selfobj.Placement)
        else:
            selfobj.Shape = Part.Shape()
            
    def advanceTip(self, selfobj, new_object):
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
        
    def onDocumentRestored(self, selfobj):
        import PartOMagic.Base.Compatibility as compat
        if compat.scoped_links_are_supported():
            #check that Tip is scoped properly. Recreate the property if not.
            if not 'Child' in selfobj.getTypeIdOfProperty('Tip'):
                v = selfobj.Tip
                t = selfobj.getTypeIdOfProperty('Tip')
                g = selfobj.getGroupOfProperty('Tip')
                d = selfobj.getDocumentationOfProperty('Tip')
                selfobj.removeProperty('Tip')
                selfobj.addProperty(t+'Child','Tip', g, d)
                selfobj.Tip = v
        
class _ViewProviderModule:
    "A View Provider for the Module object"

    def __init__(self,vobj):
        vobj.addExtension("Gui::ViewProviderOriginGroupExtensionPython", self)
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
    
    def doDisplayModeAutomation(self, vobj, old_active_container, new_active_container, event):
        # event: -1 = show public stuff
        #        +1 = show private stuff
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
from PartOMagic.Gui.AACommand import AACommand, CommandError
commands = []
class CommandModule(AACommand):
    "Command to create Module feature"
    def GetResources(self):
        import PartDesignGui #needed for icon
        return {'CommandName': 'PartOMagic_Module',
                'Pixmap'  : self.getIconPath("PartDesign_Body_Create_New.svg"),
                'MenuText': "New Module container",
                'Accel': "",
                'ToolTip': "New Module container. Module is like PartDesign Body, but for Part workbench and friends."}
        
    def RunOrTest(self, b_run):
        if b_run: CreateModule(name = "Module")
commands.append(CommandModule())
# -------------------------- /Gui command --------------------------------------------------

exportedCommands = AACommand.registerCommands(commands)