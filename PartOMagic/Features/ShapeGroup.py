import FreeCAD as App
if App.GuiUp:
    import FreeCADGui as Gui
import Part

__title__="ShapeGroup container"
__author__ = "DeepSOIC"
__url__ = ""

print("loading ShapeGroup")

def makeShapeGroup(name):
    '''makeShapeGroup(name): makes a ShapeGroup object.'''
    obj = App.ActiveDocument.addObject("Part::FeaturePython",name)
    proxy = ShapeGroup(obj)
    vp_proxy = ViewProviderShapeGroup(obj.ViewObject)
    obj.ViewObject.DisplayMode = 'Flat Lines'
    return obj

class ShapeGroup:
    "The ShapeGroup object"
    def __init__(self,obj):
        self.Type = "ShapeGroup"
        obj.addExtension("App::OriginGroupExtensionPython", self)
        
        obj.addProperty('App::PropertyEnumeration', 'Operation', 'ShapeGroup', 'Sets how to group up the shapes.')
        obj.Operation = ['None', 'Compound', 'Fusion', 'Common', 'Connect', 'CompSolid']
        obj.Operation = 'Compound'
        
        obj.addProperty('App::PropertyLinkList', 'Tip', 'ShapeGroup', 'Sets which children to take shapes from.')
        
        obj.Proxy = self
        

    def execute(self,selfobj):
        tip = selfobj.Tip
        if len(tip) == 0:
            tip = selfobj.Group
        shapes = []
        for obj in tip:
            if hasattr(obj, 'Shape'):
                shapes.append(obj.Shape)
            else:
                App.Console.PrintWarning("Object {obj} has no shape, skipped for making a compound.\n".format(obj= obj.Label))
        result_shape = Part.Shape()
        opmode = selfobj.Operation
        if opmode == 'None':
            pass
        elif opmode == 'Compound':
            result_shape = Part.makeCompound(shapes)
        elif opmode == 'Fusion':
            if len(shapes)>1:
                result_shape = shapes[0].multiFuse(shapes[1:])
            else:
                result_shape = Part.makeCompound(shapes)
        elif opmode == 'Common':
            if len(shapes)>0:
                result_shape = shapes[0]
                for sh in shapes[1:]:
                    result_shape = result_shape.common(sh)
            else:
                result_shape = Part.Shape()
        else:
            raise ValueError("Operation mode {opmode} is not implemented".format(opmode= opmode))
                
        selfobj.Shape = result_shape
            
    def advanceTip(self, selfobj, new_object):
        print("advanceTip")
        if new_object.Name.startswith("ShapeBinder"): return
        import copy
        # general idea: New object is always added to the tip. If new object is an operation applied to an old object, old object is withdrawn from tip.
        old_tip = selfobj.Tip
        new_tip = copy.copy(old_tip)
        if new_object in old_tip: return # unlikely to happen. It's just a fail-safe.
        new_tip.append(new_object)
        for obj in set(new_object.OutList): # set() is here to remove duplicates, otherwise exception may arise when removing an already removed object
            if obj in old_tip:
                new_tip.remove(obj)
        
        print("advanceTip pre-compare. len = {num}".format(num= len(new_tip)))
        if new_tip == old_tip: return
        print("advanceTip write")
        selfobj.Tip = new_tip
        
class ViewProviderShapeGroup:
    "A View Provider for the ShapeGroup object"

    def __init__(self,vobj):
        vobj.addExtension("Gui::ViewProviderGeoFeatureGroupExtensionPython", self)
        vobj.Proxy = self
        
    def getIcon(self):
        from PartOMagic.Gui.Utils import getIconPath
        return getIconPath("PartOMagic_ShapeGroup.svg")

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
        
    def setEdit(self, selfvp, mode):
        print("ShapeGroup enter edit mode {num}".format(num= mode))
        if mode == 0:
            try:
                selfobj = selfvp.Object
                #ensure right container is active
                from PartOMagic.Base import Containers
                container = Containers.getContainer(selfobj)
                if Containers.activeContainer() is not Containers.getContainer(selfobj):
                    from PartOMagic.Gui import Observer
                    Observer.activateContainer(container)

                selfobj.Document.openTransaction('Edit Tip of {sg}'.format(sg= selfobj.Label))
                
                #prepare scene
                from PartOMagic.Gui.TempoVis import TempoVis
                self.tv = TempoVis(selfobj.Document)
                tv = self.tv
                #update visibilities of children to match what's in tip
                children = selfobj.Group
                tip = selfobj.Tip
                for child in children:
                    tv.modifyVPProperty(child, 'Visibility', child in tip)
                #ensure children are visible, and nothing else...
                tv.modifyVPProperty(selfobj, 'DisplayMode','Group')
                tv.show(selfobj)
                for child in Containers.getDirectChildren(container):
                    if child is not selfobj:
                        tv.hide(child)
                
                #start editing
                self.observer = VisibilityObserver(selfobj.Group, self.editCallback)
            except Exception as err:
                App.Console.PrintError("Error in ShapeGroup setEdit: {err}\n".format(err= err.message))
                return False
            return True
        raise NotImplementedError()
        
    def editCallback(self, child, visible):
        selfobj = self.Object
        if visible:
            if not child in selfobj.Tip:
                selfobj.Tip = selfobj.Tip + [child]
        else:
            if child in selfobj.Tip:
                tip = selfobj.Tip
                tip.remove(child)
                selfobj.Tip = tip
    
    def unsetEdit(self, selfvp, mode):
        if mode == 0:
            selfobj = selfvp.Object
            self.observer.poll() #to make sure last change is incorporated
            self.observer.stop()
            self.tv.restore()
            selfobj.Document.commitTransaction()
            return True
        raise NotImplementedError()

def CreateShapeGroup(name):
    App.ActiveDocument.openTransaction("Create ShapeGroup")
    Gui.addModule("PartOMagic.Features.ShapeGroup")
    Gui.doCommand("sel = Gui.Selection.getSelectionEx()")
    Gui.doCommand("f = PartOMagic.Features.ShapeGroup.makeShapeGroup(name = '"+name+"')")
    Gui.doCommand("Gui.Selection.clearSelection()")
    Gui.doCommand("if len(sel) == 0:\n"
                  "    PartOMagic.Base.Containers.setActiveContainer(f)\n"
                  "else:\n"
                  "    for so in sel:\n"
                  "        PartOMagic.Base.Containers.moveObjectTo(so.Object, f)\n"
                  "    f.Tip = f.Group\n"
                  "    App.ActiveDocument.recompute()\n"
                  "    Gui.Selection.addSelection(f)")
    App.ActiveDocument.commitTransaction()

from FrozenClass import FrozenClass
class VisibilityObserver(FrozenClass):
    '''VisibilityObserver tracks changes to visibilities of provided list of objects, and notifies by calling a callback function.
Constructor:
    observer = VisibilityObserver(list_of_objects, callback)
        list_of_objects: list of objects of type App::DocumentObject
        callback: function with footprint: myCallback(object, b_visible), where b_visible 
            is the new state of object's visibility
It is recommended to explicitly stop the observer using `observer.stop()`
    '''
    def __define_attributes(self):
        self.timer = None
        self.vismap = {} # key = feature, value = last seen state of visibility
        self.list_of_objects = []
        self.callback = None 
    
    def __init__(self, list_of_objects, callback):
        self.__define_attributes()
        self._freeze()
        
        self.list_of_objects = list_of_objects
        self.callback = callback

        from PySide import QtCore
        timer = QtCore.QTimer()
        timer.setInterval(300)
        timer.connect(QtCore.SIGNAL("timeout()"), self.poll)
        timer.start()
        self.timer = timer
    
    def stop(self):
        self.timer.stop
        self.timer = None
        
    def __del__(self):
        self.stop()
        
    def poll(self):
        for obj in self.list_of_objects:
            vis = obj.ViewObject.Visibility
            if self.vismap.get(obj, vis) != vis:
                self.callback(obj, vis)
            self.vismap[obj] = vis


# -------------------------- Gui command --------------------------------------------------

class _CommandShapeGroup:
    "Command to create ShapeGroup feature"
    def GetResources(self):
        from PartOMagic.Gui.Utils import getIconPath
        return {'Pixmap'  : getIconPath("PartOMagic_ShapeGroup.svg"),
                'MenuText': "New ShapeGroup container",
                'Accel': "",
                'ToolTip': "New ShapeGroup container. ShapeGroup is like Part Compound or Part Union, but can be activated to receive new objects."}
        
    def Activated(self):
        CreateShapeGroup(name = "ShapeGroup")
            
    def IsActive(self):
        if App.ActiveDocument:
            return True
        else:
            return False

if App.GuiUp:
    Gui.addCommand('PartOMagic_ShapeGroup',  _CommandShapeGroup())

# -------------------------- /Gui command --------------------------------------------------

def exportedCommands():
    return ['PartOMagic_ShapeGroup']
