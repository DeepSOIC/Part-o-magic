from PartOMagic.Base import Containers as GT
from PartOMagic.Base.Containers import activeContainer, setActiveContainer
from PartOMagic.Base import Parameters
from PartOMagic.Features.GenericContainer import GenericContainer
from PartOMagic.Gui import FakeDocument
from PartOMagic.Gui.FakeDocument import defake

from PartOMagic.Base.Compatibility import tempovis_is_stacky
if tempovis_is_stacky():
    from Show import TempoVis
else:
    from PartOMagic.Gui.TempoVis import TempoVis

from .Utils import msgbox


import FreeCAD as App
import FreeCADGui as Gui


def getPartOf(feature):
    chain = GT.getContainerChain(feature)
    for cnt in chain[::-1]:
        if not cnt.isDerivedFrom("PartDesign::Body"):
            return cnt
    assert(False)
        
def activateContainer(container):
    '''activateContainer(container): activates, and applies visibility automation immediately.'''
    setActiveContainer(container)
    if isRunning():
        global observerInstance
        observerInstance.trackActiveContainer()

def test_exclude(feature, active_workbench):
    '''exclusions to disable automatic container management'''
    exclude_types = ["PartDesign::Feature", 
                     # "PartDesign::ShapeBinder", # disabled as an experiment
                     "Part::Datum", 
                     # "PartDesign::Body", # since active part was made none when body is active - part-o-magic is now busy sorting new Bodies to Parts
                     'PartDesign::CoordinateSystem',
                     "App::Origin", 
                     "App::Plane", 
                     "App::Line"]
    if active_workbench == "PartDesignGui::Workbench":
        exclude_types.append("Sketcher::SketchObject")
    for typ in exclude_types:
        if feature.isDerivedFrom(typ):
            return True
    return False
    
def addObjectTo(container, feature):
    if hasattr(App, 'ActiveContainer'):
        # New FreeCAD. Feature is added to the container automatically. All that's left to do is call advanceTip().
        return container

    if container.isDerivedFrom("App::Document"):
        return container
    
    if not GT.getContainer(feature).isDerivedFrom('App::Document'):
        # already sorted, keep it.
        return GT.getContainer(feature)
    App.Console.PrintWarning(f"PoM: megahack didn't do its job, using fallback method on {feature.Label}\n")
    
    # close editing before addition.
    #  Adding to container while editing causes editing to close anyway. But we want do do 
    #  that ourself, so that we know that we need to re-open it.
    bool_editingclosed = False
    if hasattr(Gui.ActiveDocument,"getInEdit"):
        if Gui.ActiveDocument.getInEdit():
            if Gui.ActiveDocument.getInEdit().Object is feature:
                Gui.ActiveDocument.resetEdit()
                bool_editingclosed = True
    
    #actual addition
    added = False
    actual_container = container
    while not added:
        try:
            GT.addObjectTo(actual_container, feature, b_advance_tip = False)
            added = True
        except App.Base.FreeCADError as err:
            #assuming it's a "not allowed" error
            #try adding to upper level container. Until Document is reached, which should never fail with FreeCADError
            actual_container = GT.getContainer(actual_container)
    if actual_container is not container:
        msgbox("Part-o-magic",u"Cannot add the new object of type {typ} to '{container}'. Feature added to '{actual_container}' instead."
                              .format(container= container.Label, actual_container= actual_container.Label, typ= feature.TypeId))
        
    # re-open editing that we had closed...
    if bool_editingclosed:
        Gui.ActiveDocument.setEdit(feature)
    
    return actual_container

class Observer(object):
    def defineAttributes(self):
        self.activeObjects = {} # store for remembering active containers, to detect that 
        # active container was changed. Key is document name, value is 
        # tuple(last_seen_container, last_seen_activepart, last_seen_activebody). 
        
        self.lastMD = {} # last seen date-time of last modification. Dict: key is document
        # name, value is the string returned by Document.LastModifiedDate.
        
        self.TVs = {} # store for visibility states. Key is "Document.Container" (string), value is TempoVis object created when entering the container
        self.delayed_slot_calls_queue = [] # queue of lambdas/functions to execute upon next firing of the timer.
        self.addition_calls_queue = [] # queue of lambdas/functions to execute upon next slotChangedObject.
        
        self.editing = {} # last seen object in edit. Dict: key is document name, value is documentobject.
        self.edit_TVs = {} #key is document name, value is a tempovis associated with the feature being edited
        
        self.expandedness = {} #last seen expand state of objects. Dict: key = (document name, feature name), value = boolean
        
    def __init__(self):
        self.defineAttributes()
    
    #slots
    def slotCreatedObject(self, feature):
        ac = activeContainer()
        aw = Gui.activeWorkbench().GetClassName()
        #hack!! we delay call of addObject to fire from within onChanged, as doing it now 
        #results in incorrect parenting of viewproviders. Yet it has to be done
        #before recompute, otherwise the recompute fails.
        #From there, another delayed call is registered - a call to advanceTip
        #which should be called after the new object is fully set up.
        if Parameters.EnableSorting.get():
            self.addition_calls_queue.append(
            lambda self=self, feature=feature, ac=ac, aw=aw:
                self.appendToActiveContainer(feature, ac, aw)
            )

    def slotDeletedObject(self, feature):
        ac = activeContainer()
        if feature in GT.getContainerChain(ac)+[ac]:
            # active container was deleted. Need to leave it ASAP, as long as we can access the chain
            setActiveContainer(GT.getContainer(feature))
            self.poll()
        
    def slotChangedObject(self, feature, prop_name):
        if feature.hasExtension('App::GeoFeatureGroupExtension') and prop_name == 'Group':
            return #avoid adding objects from within addObject call
        self.executeDelayedSorting()
        
    
    def slotRedoDocument(self,doc):
        pass
    def slotUndoDocument(self,doc):
        pass
    def slotActivateDocument(self,doc):
        FakeDocument.poll()

    def slotRelabelDocument(self,doc):
        pass
    def slotDeletedDocument(self,doc):
        self.activeObjects.pop(doc.Name, None)
    def slotCreatedDocument(self,doc):
        doc.RecomputesFrozen = True
        pass
        
    def slotSavedDocument(self, doc): #emulated - called by polling timer when LastModifiedDate of document changes
        if activeContainer().isDerivedFrom("App::Document"):
            return
        from PartOMagic.Base.Compatibility import tempovis_is_stacky
        if tempovis_is_stacky():
            return
        from PySide import QtGui
        mb = QtGui.QMessageBox()
        mb.setIcon(mb.Icon.Warning)
        mb.setText("It looks like you've just saved your project, but didn't deactivate active container. \n\n"
                   "As of now, Part-o-magic doesn't remember visibilities of features outside of active container through save-restore. So this may cause unexpected visibility behavior when you open the document later.\n\n"
                   "It is suggested to deactivate active container before saving projects.\n\n"
                   "If you click 'Fix and Resave' button, Part-o-magic will deactivate active container, resave the document, and activate the container back.")
        mb.setWindowTitle("Part-o-magic")
        btnClose = mb.addButton(QtGui.QMessageBox.Close)
        btnResave = mb.addButton("Fix and Resave", QtGui.QMessageBox.ButtonRole.ActionRole)
        mb.setDefaultButton(btnClose)
        mb.exec_()
        if mb.clickedButton() is btnResave:
            cnt = activeContainer()
            setActiveContainer(cnt.Document)
            self.poll() #explicit call to poller, to update all visibilities
            cnt.Document.save()
            self.lastMD[App.ActiveDocument.Name] = cnt.Document.LastModifiedDate #to avoid triggering this dialog again
            setActiveContainer(cnt)
    
    def activeContainerChanged(self, oldContainer, newContainer):
        n1 = "None"
        n2 = "None"
        if oldContainer:
            n1 = oldContainer.Name
        if newContainer:
            n2 = newContainer.Name
        
        if oldContainer is None: #happens when creating new document
            return
        
        print(oldContainer, newContainer)
            
        chain_from, chain_to = GT.getContainerRelativePath(oldContainer, newContainer)
        for cnt in chain_from[::-1]:
            try:
                gc = GenericContainer(cnt)
                gc.ViewObject.call(gc.ViewObject.activationChanged, oldContainer, newContainer, event= -1)
            except Exception as err:
                App.Console.PrintError(u"Error deactivating container '{cnt}': {err}".format(cnt= cnt.Label, err= str(err)))
            self.leaveContainer(cnt)
        for cnt in chain_to:
            try:
                gc = GenericContainer(cnt)
                gc.ViewObject.call(gc.ViewObject.activationChanged, oldContainer, newContainer, event= +1)
            except Exception as err:
                App.Console.PrintError(u"Error activating container '{cnt}': {err}".format(cnt= cnt.Label, err= str(err)))
            self.enterContainer(cnt)
        
        self.updateVPs()
        
    def slotStartEditing(self, feature):
        print(u"Start Editing {f}".format(f= feature.Name))
        cnt = GT.getContainer(feature)
        # if GT.activeContainer() is not cnt:
        #     print(u"Feature being edited is not in active container. Activating {cnt}...".format(cnt= cnt.Name))
        #     Gui.ActiveDocument.resetEdit()
        #     GT.setActiveContainer(cnt)
        #     return
        from PartOMagic.Base.Utils import PlacementsFuzzyCompare as cmp
        plm : App.Placement = feature.getGlobalPlacement()
        if cmp(plm, App.Placement()) == False:
            plm_edit = App.Placement(Gui.ActiveDocument.EditingTransform)
            if cmp(plm_edit, App.Placement()) == True:
                # editing transform is zero while global placement is not. Suspicious, let's fix it. (fixes #73 wrong sketch view alignment)
                Gui.ActiveDocument.EditingTransform = plm.toMatrix()
                if feature.isDerivedFrom('Sketcher::SketchObject'):
                    Gui.ActiveDocument.ActiveView.setCameraOrientation(plm.Rotation.Q)

        if feature.isDerivedFrom("PartDesign::Boolean"):
            # show all bodies nearby...
            part = GT.getContainer(cnt)
            children = GT.getDirectChildren(part)
            children = [child for child in children if child.isDerivedFrom("Part::BodyBase")]
            children = set(children)
            children.remove(cnt)
            for obj in GT.getAllDependent(cnt):
                if obj in children:
                    children.remove(obj)
            tv = TempoVis(feature.Document)
            tv.show(children)
            self.edit_TVs[feature.Document.Name] = tv
        
    def slotFinishEditing(self, feature):
        tv = self.edit_TVs.pop(App.ActiveDocument.Name, None)
        if tv is not None:
            tv.restore()
    
    def poll(self):
        'Called by timer to poll for container changes, and other tracking'
        self.executeDelayedOperations()

        if App.ActiveDocument is None:
            return
        if GT.active3DView() is None:
            return # happens when editing a spreadsheet with 3d view closed
            
        self.executeDelayedSorting()
        self.trackActiveContainer()
        self.trackExpands()
        self.trackSaves()
        self.trackEditing()
    
    def executeDelayedSorting(self):
        while len(self.addition_calls_queue) > 0:
            lmd = self.addition_calls_queue.pop(0)
            lmd()
    
    def executeDelayedOperations(self):
        # execute delayed onChange
        try:
            for lmd in self.delayed_slot_calls_queue:
                lmd()
        finally:
            self.delayed_slot_calls_queue = []
        
    def trackActiveContainer(self):
        #watch for changes in active object
        vw = GT.active3DView()
        activeBody = vw.getActiveObject("pdbody")
        activePart = vw.getActiveObject("part")
        ac = activeContainer()
        if not App.ActiveDocument.Name in self.activeObjects:
            self.activeObjects[App.ActiveDocument.Name] = (None, None, None)
        last_ac, last_ap, last_ab = self.activeObjects[App.ActiveDocument.Name]
        if (ac, activePart, activeBody) != (last_ac, last_ap, last_ab): #we are tracking activeContainer() too, because it changes when documents are created and deleted
            new_ac = last_ac
            if activeBody != last_ab and activePart != last_ap:
                #both active container fields have changed. Set active whatever is not none, but body has priority
                if activeBody is not None:
                    new_ac = activeBody
                else:
                    new_ac = activePart
            elif activeBody != last_ab:
                #only body field changed
                new_ac = activeBody
            elif activePart != last_ap:
                #only part field changed
                new_ac = activePart
            if new_ac is None:
                new_ac = defake(App.ActiveDocument)
            if new_ac is not last_ac: #unlikely it is false, since we have detected a change....
                if not hasattr(App, 'ActiveContainer'):
                    setActiveContainer(new_ac)
                ac = activeContainer()
                assert(ac is new_ac)

            ac = activeContainer()
            try:
                self.activeContainerChanged(last_ac, ac)
            finally:
                # re-query the active containers, as they might have been altered by setActiveContainer.
                activeBody = vw.getActiveObject("pdbody")
                activePart = vw.getActiveObject("part")
                self.activeObjects[App.ActiveDocument.Name] = (ac, activePart, activeBody)
    
    def trackSaves(self):
        # detect document saves
        cur_lmd = App.ActiveDocument.LastModifiedDate
        last_lmd = self.lastMD.get(App.ActiveDocument.Name, None)
        if cur_lmd != last_lmd:
            # LastModifiedDate has changed - document was just saved!
            self.lastMD[App.ActiveDocument.Name] = cur_lmd
            if last_lmd is not None: #filter out the apparent change that happens when there was no last-seen value
                self.slotSavedDocument(defake(App.ActiveDocument))
        
    def trackEditing(self):
        #detect start/end of editing
        cur_in_edit_vp = Gui.ActiveDocument.getInEdit()
        cur_in_edit = cur_in_edit_vp.Object if cur_in_edit_vp is not None else None
        last_in_edit = self.editing.get(App.ActiveDocument.Name, None)
        if cur_in_edit is not last_in_edit:
            self.editing[App.ActiveDocument.Name] = cur_in_edit
            if last_in_edit is not None:
                self.slotFinishEditing(last_in_edit)
            if cur_in_edit is not None:
                self.slotStartEditing(cur_in_edit)
    
    def trackExpands(self):
        docname = App.ActiveDocument.Name
        for obj in App.ActiveDocument.Objects:
            objname = obj.Name
            key = (docname, objname)
            curstate = 'Expanded' in obj.State
            oldstate = self.expandedness.get(key, False)
            if curstate != oldstate:
                self.expandedness[key] = curstate
                if GT.isContainer(obj):
                    gc = GenericContainer(obj)
                    gc.ViewObject.call(gc.ViewObject.expandednessChanged, oldstate, curstate)
    
    # functions

    def appendToActiveContainer(self, feature, active_container, active_workbench):
        if test_exclude(feature, active_workbench):
            return #PartDesign manages itself
        if active_container is None: #shouldn't happen
            return
        actual_container = None #the container the object was added to. Different to active_container if active_container can't accept the object.
        if not active_container.isDerivedFrom("App::Document"):
            actual_container = addObjectTo(active_container, feature)
        if actual_container is not None and not actual_container.isDerivedFrom('App::Document') :
            self.delayed_slot_calls_queue.append(
              lambda self=self, feature=feature, ac=actual_container, aw=active_workbench:
                self.advanceTip(feature, ac, aw)
              )

    def advanceTip(self, feature, active_container, active_workbench): 
        gc = GenericContainer(active_container)
        gc.call(gc.advanceTip, feature)
    
    def enterContainer(self, cnt):
        '''enterContainer(self, cnt): when cnt either directly is being activated, or one of its child containers is being activated. Assumes container of cnt is already entered.'''
        if cnt.isDerivedFrom("App::Document"): # may happen when creating new document. Ignoring.
            return
        if Parameters.VisibilityAutomation.get() == False:
            return
        key = cnt.Document.Name+"."+cnt.Name
        if key in self.TVs:
            # just in case old tempovis associated with the container wasn't removed for some reason.
            self.TVs[key].forget()
        tv = TempoVis(cnt.Document)
        self.TVs[key] = tv
        list_hiding = [o for o in GT.getDirectChildren(GT.getContainer(cnt)) if not o is cnt]
        list_hiding = [o for o in list_hiding if not o.isDerivedFrom('App::DocumentObjectGroup')] # don't touch visibility of groups just yet...
        tv.hide(list_hiding)
        tv.show(cnt)
        
    def leaveContainer(self, cnt):
        if Parameters.VisibilityAutomation.get() == False:
            return
        assert(not cnt.isDerivedFrom("App::Document"))
        key = cnt.Document.Name+"."+cnt.Name
        tv = self.TVs[key]
        tv.restore()
        tv.forget()
        self.TVs.pop(key)
        
    def updateVPs(self):
        '''updates many viewprovider properties (except visibility, which is handled by TempoVis objects)'''
        ac = activeContainer()
        
        if ac.isDerivedFrom("App::Document"):
            objects_in = set(App.ActiveDocument.Objects)
        else:
            objects_in = set(  GT.getDirectChildren(ac)  )
        objects_out = set(App.ActiveDocument.Objects) - objects_in
        
        # make all object in context selectable. This is mainly to undo consequences of old behavior of making everything out-of-context non-selectable
        for o in objects_in:
            if hasattr(o.ViewObject, "Selectable"):
                o.ViewObject.Selectable = True
        
        for o in App.ActiveDocument.findObjects("App::Origin"):
            o.ViewObject.Visibility = GT.getContainer(o) is ac
if not "observerInstance" in globals():
    observerInstance = None
    timer = None
else:
    print("observerInstance already present (module reloading...)")
    if isRunning():
        stop()
        start()

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
    timer.connect(QtCore.SIGNAL("timeout()"), observerInstance.poll)
    timer.start()

    if Parameters.FakeDocument.get():
        FakeDocument.start()
    Parameters.FakeDocument.subscribe(_slotFakeDocumentChanged)
    
    global suspend_counter
    suspend_counter = 0
    
def stop():
    global observerInstance
    if observerInstance is None:
        return
    App.removeDocumentObserver(observerInstance)
    observerInstance = None
    
    global timer
    timer.stop()
    timer = None

    FakeDocument.stop()
    Parameters.FakeDocument.unsubscribe(_slotFakeDocumentChanged)

    global suspend_counter
    suspend_counter = None
    
def isRunning():
    global observerInstance
    return observerInstance is not None

def suspend():
    """Suspends Observer (new objects will not be sorted, and so forth). 
    Returns a keeper object that can be deleted or used in a with block to unsuspend.
    Observer will drop everything that happens while it's suspended, it will not try to catch up once unsuspended."""
    global observerInstance
    global suspend_counter
    if not isRunning():
        return Keeper(None)
    if suspend_counter == 0:
        App.removeDocumentObserver(observerInstance)
        FakeDocument.stop()
    suspend_counter += 1
    return Keeper(_resume)

def _resume():
    """do not call! Resume a suspend by calling .release method on keeper object returned by suspend."""
    global suspend_counter
    if suspend_counter == 0: return
    suspend_counter -= 1
    if suspend_counter == 0:
        App.addDocumentObserver(observerInstance)
        if Parameters.FakeDocument.get():
            FakeDocument.start()

def _slotFakeDocumentChanged(p, old_val, val):
    if isRunning():
        if val:
            FakeDocument.start()
        else:
            FakeDocument.stop()
    
class Keeper(object):
    undo_func = None
    def __init__(self, undo_func):
        self.undo_func = undo_func
    
    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
    
    def release(self):
        if self.undo_func is not None:
            self.undo_func()
            self.undo_func = None

    def __del__(self):
        self.release()

def sortNow():
    "sort new objects into containers now"
    global observerInstance
    if observerInstance is not None:
        observerInstance.executeDelayedSorting()