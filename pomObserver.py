import pomDepGraphTools as GT
import FreeCAD as App
import FreeCADGui as Gui
from AttachmentEditor.TempoVis import TempoVis
from AttachmentEditor.FrozenClass import FrozenClass

def activeContainer():
    '''activeContainer(): returns active container.
    If there is an active body, it is returned as active container. ActivePart is ignored.
    If there is no active body, active Part is returned.
    If there is no active Part either, active Document is returned.
    If no active document, None is returned.'''
    
    if Gui.ActiveDocument is None:
        return None
    activeBody = Gui.ActiveDocument.ActiveView.getActiveObject("pdbody")
    activePart = Gui.ActiveDocument.ActiveView.getActiveObject("part")
    if activeBody:
        return activeBody
    elif activePart:
        return activePart
    else:
        return App.ActiveDocument

def setActiveContainer(cnt):
    assert(GT.isContainer(cnt))
    if cnt.isDerivedFrom("PartDesign::Feature"):
        Gui.ActiveDocument.ActiveView.setActiveObject("pdbody", cnt)
        part = getPartOf(cnt)
    else:
        part = cnt
        Gui.ActiveDocument.ActiveView.setActiveObject("pdbody", None)
    if part:
        if part.isDerivedFrom("App::Document"):
            part = None
    Gui.ActiveDocument.ActiveView.setActiveObject("part", part)
        
def getPartOf(feature):
    chain = GT.getContainerChain(feature)
    for cnt in chain[::-1]:
        if not cnt.isDerivedFrom("PartDesign::Body"):
            return cnt
    assert(False)

def msgbox(title, text):
    from PySide import QtGui
    mb = QtGui.QMessageBox()
    mb.setIcon(mb.Icon.Information)
    mb.setText(text)
    mb.setWindowTitle(title)
    mb.exec_()
    
def test_exclude(feature):
    '''exclusions to disable automatic container management'''
    exclude_types = ["PartDesign::Feature", 
                     "PartDesign::ShapeBinder"
                     "PartDesign::Datum", 
                     "PartDesign::Body", 
                     'PartDesign::CoordinateSystem',
                     "App::Origin", 
                     "App::Plane", 
                     "App::Line"]
    if Gui.activeWorkbench().GetClassName() == "PartDesignGui::Workbench":
        exclude_types.append("Sketcher::SketchObject")
    for typ in exclude_types:
        if feature.isDerivedFrom(typ):
            return True
    return False

class Observer(FrozenClass):
    def defineAttributes(self):
        self.activeObjects = {} # store for remembering active containers, to detect that active container was changed. Key is document name, value is container object.
        self.TVs = {} # store for visibility states. Key is "Document.Container" (string), value is TempoVis object created when entering the container
        
        self._freeze()
        
    def __init__(self):
        self.defineAttributes()
    
    #slots
    
    def slotCreatedObject(self, feature):
        if test_exclude(feature):
            return #PartDesign manages itself
        if activeContainer() is None: #shouldn't happen
            return
        if activeContainer().isDerivedFrom("PartDesign::Body"):
            msgbox("Part-o-magic","Cannot add the new object to body, because bodies accept only PartDesign features. ActiveBody is deactivated, and feature added to active part.")
            setActiveContainer(getPartOf(activeContainer()))
        if not activeContainer().isDerivedFrom("App::Document"):
            activeContainer().addObject(feature)

    def slotDeletedObject(self, feature):
        pass
    #def slotChangedObject(self, feature, prop_name):
    #    pass
    def slotRedoDocument(self,doc):
        pass
    def slotUndoDocument(self,doc):
        pass
    def slotActivateDocument(self,doc):
        pass
    def slotRelabelDocument(self,doc):
        pass
    def slotDeletedDocument(self,doc):
        pass
    def slotCreatedDocument(self,doc):
        pass
    
    def activeContainerChanged(self, oldContainer, newContainer):
        n1 = "None"
        n2 = "None"
        if oldContainer:
            n1 = oldContainer.Name
        if newContainer:
            n2 = newContainer.Name
        print "container changed from {c1} to {c2}".format(c1= n1, c2= n2)
        
        if oldContainer is None: #happens when creating new document
            return
            
        chain_from, chain_to = GT.getContainerRelativePath(oldContainer, newContainer)
        for cnt in chain_from[::-1]:
            self.leaveContainer(cnt)
        for cnt in chain_to:
            self.enterContainer(cnt)
        
        self.updateVPs()
    
    def activeObjectWatcher(self):
        'Called by timer to poll for container changes'
        if App.ActiveDocument is None:
            return
        ac = activeContainer()
        if not App.ActiveDocument.Name in self.activeObjects:
            self.activeObjects[App.ActiveDocument.Name] = None
        if self.activeObjects[App.ActiveDocument.Name] is not ac:
            try:
                self.activeContainerChanged(self.activeObjects[App.ActiveDocument.Name], ac)
            finally:
                self.activeObjects[App.ActiveDocument.Name] = ac
    
    # functions
    
    def enterContainer(self, cnt):
        '''enterContainer(self, cnt): when cnt either directly is being activated, or one of its child containers is being activated. Assumes container of cnt is already entered.'''
        print "entering "+cnt.Name
        if cnt.isDerivedFrom("App::Document"): # may happen when creating new document. Ignoring.
            return
        key = cnt.Document.Name+"."+cnt.Name
        if key in self.TVs:
            # just in case old tempovis associated with the container wasn't removed for some reason.
            self.TVs[key].forget()
        tv = TempoVis(cnt.Document)
        self.TVs[key] = tv
        list_hiding = [o for o in GT.getDirectChildren(GT.getContainer(cnt)) if not o is cnt]
        print [o.Name for o in list_hiding]
        tv.hide(list_hiding)
        tv.show(cnt)
        
    def leaveContainer(self, cnt):
        print "leaving "+cnt.Name
        assert(not cnt.isDerivedFrom("App::Document"))
        key = cnt.Document.Name+"."+cnt.Name
        tv = self.TVs[key]
        tv.restore()
        tv.forget()
        self.TVs.pop(key)
        
    def updateVPs(self):
        '''updates many viewprovider properties (except visibility, which is handled by TempoVis objets)'''
        ac = activeContainer()
        objects_in = set(  GT.getDirectChildren(ac)  )
        objects_out = set(App.ActiveDocument.Objects) - objects_in
        for o in objects_in:
            if hasattr(o.ViewObject, "Selectable"):
                o.ViewObject.Selectable = True
        for o in objects_out:
            if hasattr(o.ViewObject, "Selectable"):
                o.ViewObject.Selectable = False
        
        active_chain = GT.getContainerChain(ac) + [ac]
        for o in App.ActiveDocument.findObjects("PartDesign::Body"):
            dm = "Through" if o in active_chain else "Tip"
            if o.ViewObject.DisplayModeBody != dm: # check if actual change needed, to avoid potential slowdown
                o.ViewObject.DisplayModeBody = dm
                o.ViewObject.Visibility = o.ViewObject.Visibility #workaround for bug: http://forum.freecadweb.org/viewtopic.php?f=3&t=15845
                
        for o in App.ActiveDocument.findObjects("App::Origin"):
            o.ViewObject.Visibility = GT.getContainer(o) is ac
observerInstance = None
timer = None

def start():
    global observerInstance
    if observerInstance is not None:
        return
    observerInstance = Observer()
    App.addDocumentObserver(observerInstance)
    
    global timer
    from PySide import QtCore
    timer = QtCore.QTimer()
    timer.setInterval(300)
    timer.connect(QtCore.SIGNAL("timeout()"), observerInstance.activeObjectWatcher)
    timer.start()
    
def stop():
    global observerInstance
    if observerInstance is None:
        return
    App.removeDocumentObserver(observerInstance)
    observerInstance = None
    
    global timer
    timer.stop()
    timer = None
    
