import pomDepGraphTools as GT
import FreeCAD as App
import FreeCADGui as Gui

def activeContainer():
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
        if not cnt.isDerivedFrom("PartDesign::Feature"):
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
                     "PartDesign::Datum", 
                     "PartDesign::Body", 
                     "App::Origin", 
                     "App::Plane", 
                     "App.Line",
                     "PartDesign::ShapeBinder"]
    for typ in exclude_types:
        if feature.isDerivedFrom(typ):
            return True
    return False

class Observer(object):
    def __init__(self):
        self.activeObjects = {}
        
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
    
    def activeObjectWatcher(self):
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
    
