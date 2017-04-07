
class GenericContainer(object):
    "Implements default behavior of containers in PoM (mostly aimed at C++ ones)"
    selfobj = None
    ViewObject = None
    
    def __init__(self, container):
        self.selfobj = container
        self.ViewObject = ViewProviderGenericContainer(container)
    
    def call(self, method, *args, **kwargs):
        "call(method, *args): if the object's proxy overrides the method, call the override. Else call standard implementation."
        if hasattr(self.selfobj, 'Proxy') and hasattr(self.selfobj.Proxy, method.__name__):
            getattr(self.selfobj.Proxy, method.__name__)(self.selfobj, *args, **kwargs)
        else:
            getattr(self, method.__name__)(*args, **kwargs)
    
    def advanceTip(self, new_object):
        pass

class ViewProviderGenericContainer(object):
    "Implements default behavior of containers in PoM (mostly aimed at C++ ones)"
    selfobj = None
    selfvp = None
    
    def __init__(self, container):
        self.selfvp = None if not hasattr(container, 'ViewObject') else container.ViewObject
        self.selfobj = self.selfvp.Object

    def call(self, method, *args, **kwargs):
        "call(method, *args): if the viewprovider's proxy overrides the method, call the override. Else call standard implementation."
        if self.selfvp is None: return
        if hasattr(self.selfvp, 'Proxy') and hasattr(self.selfvp.Proxy, method.__name__):
            getattr(self.selfvp.Proxy, method.__name__)(self.selfvp, *args, **kwargs)
        else:
            getattr(self, method.__name__)(*args, **kwargs)
    
    def activationChanged(self, old_active_container, new_active_container, event):
        # event: -1 = leaving (active container was self or another container inside, new container is outside)
        #        +1 = entering (active container was outside, new active container is inside)
        self.call(self.doDisplayModeAutomation, old_active_container, new_active_container, event)
        self.call(self.doTreeAutomation, old_active_container, new_active_container, event)
            
    def doDisplayModeAutomation(self, old_active_container, new_active_cntainer, event):
        # event: -1 = show public stuff
        #        +1 = show private stuff
        o = self.selfobj
        if event == +1:
            if o.isDerivedFrom('PartDesign::Body'):
                dm = "Through"
                if o.ViewObject.DisplayModeBody != dm: # check if actual change needed, to avoid potential slowdown
                    o.ViewObject.DisplayModeBody = dm
                    o.ViewObject.Visibility = o.ViewObject.Visibility #workaround for bug: http://forum.freecadweb.org/viewtopic.php?f=3&t=15845
        elif event == -1:
            if o.isDerivedFrom('PartDesign::Body'):
                dm = "Tip"
                if o.ViewObject.DisplayModeBody != dm: # check if actual change needed, to avoid potential slowdown
                    o.ViewObject.DisplayModeBody = dm
                    o.ViewObject.Visibility = o.ViewObject.Visibility #workaround for bug: http://forum.freecadweb.org/viewtopic.php?f=3&t=15845
        
    def doTreeAutomation(self, old_active_container, new_active_cntainer, event):
        import FreeCADGui as Gui
        if event == +1:
            Gui.ActiveDocument.toggleTreeItem(self.selfobj, 2 ) #expand
        elif event == -1:
            if not (self.selfobj.isDerivedFrom('App::Part') or self.selfobj.isDerivedFrom('App::DocumentObjectGroup')):
                Gui.ActiveDocument.toggleTreeItem(self.selfobj, 1 ) #collapse        


