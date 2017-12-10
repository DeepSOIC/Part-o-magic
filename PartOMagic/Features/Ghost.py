print("loading Ghost")

import FreeCAD as App
if App.GuiUp:
    import FreeCADGui as Gui
import Part

__title__="Ghost feature (shapebinder)"
__author__ = "DeepSOIC"
__url__ = ""


from PartOMagic.Base import Containers
from PartOMagic.Gui.Utils import DelayedExecute

class GhostError(RuntimeError):
    pass

def makeGhost(name, type= 'Part::FeaturePython'):
    '''makeGhost(name): makes a Ghost object.'''
    obj = App.ActiveDocument.addObject(type,name)
    proxy = Ghost(obj)
    vp_proxy = ViewProviderGhost(obj.ViewObject)
    return obj

class Ghost:
    "The Ghost object, an alternative shapebinder"
    def __init__(self,selfobj):
        selfobj.addProperty('App::PropertyLinkGlobal','Base',"Ghost","Shape of ghost")
        selfobj.addProperty('App::PropertyLinkListGlobal','PlacementLinks',"Ghost", "Extra dependencies, for ensuring recompute order")
        selfobj.setEditorMode('PlacementLinks', 1) #read-only
        selfobj.addProperty('App::PropertyBool', 'UseForwardPlacements', "Ghost", "If true, applies placements of containers base object is in.")
        selfobj.UseForwardPlacements = True
        selfobj.addProperty('App::PropertyBool', 'UseInversePlacements', "Ghost", "If true, applies invese placements of containers the ghost is in.")
        selfobj.UseInversePlacements = True

        for prop in ['Placement', ]:
            selfobj.setEditorMode(prop, 1)
        for prop in selfobj.PropertiesList:
            if selfobj.getGroupOfProperty(prop) == "Attachment":
                selfobj.setEditorMode(prop, 2) #hidden
        
        selfobj.Proxy = self
        
        self._implicit_deps = None #complete list of containers whose placements are being used
    
    def updateDeps(self, selfobj, check_only = False):
        """update PlacementLinks to match with container path"""
        toleave,toenter = Containers.getContainerRelativePath(Containers.getContainer(selfobj.Base), Containers.getContainer(selfobj))
        leave_deps = []
        if selfobj.UseForwardPlacements:
            for cnt in toleave[::-1]:
                if hasattr(cnt, 'Placement'):
                    leave_deps.append(cnt)
        enter_deps = []
        if selfobj.UseInversePlacements:
            for cnt in toenter:
                if hasattr(cnt, 'Placement'):
                    enter_deps.append(cnt)
        if selfobj.PlacementLinks != leave_deps or not hasattr(self, '_implicit_deps') or self._implicit_deps != enter_deps:
            if check_only:
                App.Console.PrintError("Placement dependencies of {feat} are out of sync!\n".format(feat= selfobj.Name))
            else:
                selfobj.PlacementLinks = leave_deps
                self._implicit_deps = enter_deps
                selfobj.touch()

        for dep in enter_deps:
            for (prop, expr) in dep.ExpressionEngine:
                if prop.startswith('Placement'):
                    raise GhostError(
                        '{dep} has expression bound to its placement. {ghost} uses it, but is inside of the container, so it can\'t be properly recomputed.'
                        .format(dep= dep.Label, ghost= selfobj.Label)
                    )
    
    def execute(self,selfobj):
        self.updateDeps(selfobj, check_only= True)
        toleave,toenter = Containers.getContainerRelativePath(Containers.getContainer(selfobj.Base), Containers.getContainer(selfobj))
        transform = App.Placement()
        if selfobj.UseForwardPlacements:
            for cnt in toleave[::-1]:
                if hasattr(cnt, 'Placement'):
                    transform = cnt.Placement.multiply(transform)
        if selfobj.UseInversePlacements:
            for cnt in toenter:
                if hasattr(cnt, 'Placement'):
                    transform = cnt.Placement.inverse().multiply(transform)
        selfobj.Shape = selfobj.Base.Shape
        selfobj.Placement = transform.multiply(selfobj.Base.Placement)
        
        path = ''
        for cnt in toenter:
            path += '../'
        for cnt in toleave:
            path += cnt.Name + '/'
        selfobj.Label = '{name} {label} from {path}'.format(label= selfobj.Base.Label, name= selfobj.Name, path= path[:-1])
    
    def onChanged(self, selfobj, propname):
        if 'Restore' in selfobj.State:
            return
        if propname in ['Base', 'UseForwardPlacements', 'UseInversePlacements']:
            self.updateDeps(selfobj)
            
    def onDocumentRestored(self, selfobj):
        self.updateDeps(selfobj)

class ViewProviderGhost:
    "A View Provider for the Ghost object"

    def __init__(self,vobj):
        vobj.Proxy = self
        c = (1.0, 0.6, 0.95, 0.0)
        vobj.ShapeColor = c
        vobj.LineColor = c
        vobj.PointColor = c
        vobj.Transparency = 60
        
    def getIcon(self):
        from PartOMagic.Gui.Utils import getIconPath
        return getIconPath("PartOMagic_Ghost.svg")

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
    
    def doubleClicked(self, vobj):
        Containers.setActiveContainer(Containers.getContainer(vobj.Object.Base))
        return True
    
    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

oneshot = None #delayed execution of ghost updater

class Observer(object):
    def slotChangedObject(self, feature, prop_name):
        if prop_name == 'Group': 
            if not Containers.isContainer(feature): 
                return
            if 'Restore' in feature.State:
                return
            if App.GuiUp:
                global oneshot
                if oneshot is None or oneshot.is_done:
                    oneshot = DelayedExecute((lambda doc = feature.Document: updateAllGhosts(doc)), delay= 100)
            else:
                updateAllGhosts(feature.Document)
        elif prop_name == 'Placement':
            if not Containers.isContainer(feature): 
                return
            if 'Restore' in feature.State:
                return
            onContainerPlacementChanged(feature)
            

#stop old observer, if reloading this module
if 'observer' in vars():
    App.removeDocumentObserver(observer)
    observer = None
#start obsrever
observer = Observer()
App.addDocumentObserver(observer)


def updateAllGhosts(doc):
    for obj in doc.Objects:
        if not hasattr(obj, 'Proxy'): 
            continue
        if hasattr(obj.Proxy, 'updateDeps'):
            try:
                obj.Proxy.updateDeps(obj)
            except Exception as err:
                App.Console.PrintError(
                        "Updating dependencies of ghost '{obj}' failed:\n    {err}\n"
                        .format(err= str(err),
                                obj= obj.Label) 
                )

def onContainerPlacementChanged(cnt):
    for obj in cnt.Document.Objects:
        if not hasattr(obj, 'Proxy'): 
            continue
        if hasattr(obj.Proxy, '_implicit_deps'):
            try:
                if cnt in obj.Proxy._implicit_deps:
                    obj.touch()
            except Exception as err:
                App.Console.PrintError(
                        "Tracking moves of containers for ghost '{obj}' failed:\n    {err}\n"
                        .format(err= str(err),
                                obj= obj.Label) 
                )


def CreateGhost(name, sel):
    typ = 'Part::Part2DObjectPython' if sel.isDerivedFrom('Part::Part2DObject') else 'Part::FeaturePython'
    from PartOMagic.Gui.Utils import Transaction
    with Transaction("Create Ghost"):
        Gui.addModule("PartOMagic.Features.Ghost")
        Gui.doCommand("f = PartOMagic.Features.Ghost.makeGhost(name= {name}, type= {typ})".format(name= repr(name), typ= repr(typ)))
        Gui.doCommand("f.Base = App.ActiveDocument.{objname}".format(objname= sel.Name))
        Gui.doCommand("Gui.Selection.clearSelection()")
        Gui.doCommand("Gui.Selection.addSelection(f)")
        Gui.doCommand("App.ActiveDocument.recompute()")



# -------------------------- Gui command --------------------------------------------------
from PartOMagic.Gui.AACommand import AACommand, CommandError
commands = []
class CommandGhost(AACommand):
    "Command to create Ghost feature"
    def GetResources(self):
        import PartDesignGui #needed for icon
        return {'CommandName': 'PartOMagic_Ghost',
                'Pixmap'  : self.getIconPath("PartOMagic_Ghost.svg"),
                'MenuText': "Make Ghost of selected object",
                'Accel': "",
                'ToolTip': "Make Ghost. Creates a ghost of a shape from another container. AKA Shapebinder."}
        
    def RunOrTest(self, b_run):
        sel = Gui.Selection.getSelection()
        if len(sel)==0 :
            raise CommandError(self, "Make Ghost command. Please select an object to import to active container, first. The object must be geometry.")
        elif len(sel)==1:
            sel = sel[0]
            ac = Containers.activeContainer()
            if sel in Containers.getDirectChildren(ac):
                raise CommandError(self, 
                    "{feat} is from active container ({cnt}). Please select an object belonging to another container."
                    .format(feat= sel.Label, cnt= ac.Label)
                )
            if sel in (Containers.getAllDependent(ac)+ [ac]):
                raise CommandError(self, "Can't create a ghost here, because a circular dependency will result.")
            if b_run: 
                CreateGhost('Ghost', sel)
        else:
            raise CommandError(self, "Make Ghost command. You need to select exactly one object (you selected {num}).".format(num= len(sel)))    
        
commands.append(CommandGhost())
# -------------------------- /Gui command --------------------------------------------------

exportedCommands = AACommand.registerCommands(commands)