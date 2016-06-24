import pomDepGraphTools as GT
import FreeCAD as App
import FreeCADGui as Gui
from pomTempoVis import TempoVis
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
    '''setActiveContainer(cnt): sets active container. To set no active container, supply ActiveDocument. None is not accepted.'''
    assert(GT.isContainer(cnt))
    if cnt.isDerivedFrom("Part::BodyBase"):
        Gui.ActiveDocument.ActiveView.setActiveObject("pdbody", cnt)
        part = None
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
    
def test_exclude(feature, active_workbench):
    '''exclusions to disable automatic container management'''
    exclude_types = ["PartDesign::Feature", 
                     "PartDesign::ShapeBinder",
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
    if container.isDerivedFrom("App::Document"):
        return #already there!
    if container.isDerivedFrom("PartDesign::Body"):
        #Part-o-magic is not supposed add stuff to PartDesign bodies, as it is managed by PartDesign.
        tmp = container
        container = getPartOf(container)
        msgbox("Part-o-magic","Cannot add the new object of type {typ} to {body}, because bodies accept only PartDesign features. Feature added to {cnt} instead."
                              .format(body= tmp.Label, cnt= container.Label, typ= feature.TypeId))
    if GT.isContainer(feature):
        #make sure we are not creating a container dependency loop, as doing so crashes FreeCAD. see http://forum.freecadweb.org/viewtopic.php?f=10&t=15936
        if feature in (GT.getContainerChain(container) + [container]):
            raise ValueError("Attempting to add {feat} to {cont} failed: doing so will cause container dependency loop."
                            .format(feat= feature.Name, cont= container.Name))
    if not GT.getContainer(feature).isDerivedFrom("App::Document"):
        # prevent adding objects to a container if the object is already in a container. 
        # This should partially fix unexpected behavior on undoing deletion, duplication, 
        # and the like.
        App.Console.PrintWarning("Part-o-magic: attempted to add {feat} to container {cnt_to}, but the feature already belongs to {cnt_feat}. Aborted.\n"
                                 .format(feat= feature.Label,
                                         cnt_to= container.Label,
                                         cnt_feat= GT.getContainer(feature).Label))
        raise ValueError("Feature already in (another) container.")
    if container.isDerivedFrom("App::DocumentObjectGroup"):
        container.addObject(feature)
    elif container.isDerivedFrom("Part::BodyBase"):
        container.Model = container.Model + [feature]
        
        # a bit of "smartness" here =) . Setting Tip!
        if feature.isDerivedFrom("Part::Feature"):
            if container.Tip is not None: 
                if container.Tip in feature.OutList:
                    # something was created that immediately derives from shape of current tip. Probably it's time to replace the Tip!
                    container.Tip = feature
            else:
                #first suitable thing added to the body will be made Tip.
                container.Tip = feature
    else:
        raise TypeError("Don't know how to add a feature to a container of type {typ}".format(typ= container.TypeId))

class Observer(FrozenClass):
    def defineAttributes(self):
        self.activeObjects = {} # store for remembering active containers, to detect that 
        # active container was changed. Key is document name, value is 
        # tuple(last_seen_container, last_seen_activepart, last_seen_activebody). 
        
        self.lastMD = {} # last seen date-time of last modification. Dict: key is document
        # name, value is the string returned by Document.LastModifiedDate.
        
        self.TVs = {} # store for visibility states. Key is "Document.Container" (string), value is TempoVis object created when entering the container
        self.delayed_slot_calls_queue = [] # queue of lambdas
        
        self._freeze()
        
    def __init__(self):
        self.defineAttributes()
    
    #slots
    def slotCreatedObject(self, feature):
        ac = activeContainer()
        aw = Gui.activeWorkbench().GetClassName()
        self.delayed_slot_calls_queue.append(
          lambda self=self, feature=feature, ac=ac, aw=aw:
            self.slotCreatedObject_delayed(feature, ac, aw)
          )
        if feature.isDerivedFrom("Sketcher::SketchObject"):
            # workaround: add it to container immediately, otherwise edit mode is exited, which is annoying
            self.activeObjectWatcher()
    
    def slotCreatedObject_delayed(self, feature, active_container, active_workbench): 
        # active_container is remembered at the time the object was actually created. 
        # This is a hack to make nesting Parts possible.
        if test_exclude(feature, active_workbench):
            return #PartDesign manages itself
        if active_container is None: #shouldn't happen
            return
        if not active_container.isDerivedFrom("App::Document"):
            addObjectTo(active_container, feature)
        

    def slotDeletedObject(self, feature):
        print ("deleted {feat}. container chain: {chain}"
                .format(feat= feature.Name, chain= ".".join([cnt.Name for cnt in GT.getContainerChain(feature)])))
        ac = activeContainer()
        if feature in GT.getContainerChain(ac)+[ac]:
            # active container was deleted. Need to leave it ASAP, as long as we can access the chain
            setActiveContainer(GT.getContainer(feature))
            self.activeObjectWatcher()
        
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
        
    def slotSavedDocument(self, doc): #emulated - called by polling timer when LastModifiedDate of document changes
        if activeContainer().isDerivedFrom("App::Document"):
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
            self.activeObjectWatcher() #explicit call to poller, to update all visibilities
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
        # execute delayed onChange
        try:
            for lmd in self.delayed_slot_calls_queue:
                lmd()
        finally:
            self.delayed_slot_calls_queue = []
        
        if App.ActiveDocument is None:
            return

        #watch for changes in active object
        activeBody = Gui.ActiveDocument.ActiveView.getActiveObject("pdbody")
        activePart = Gui.ActiveDocument.ActiveView.getActiveObject("part")
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
                new_ac = App.ActiveDocument
            if new_ac is not last_ac: #unlikely it is false, since we have detected a change....
                setActiveContainer(new_ac)

            ac = activeContainer()
            assert(ac is new_ac)
            try:
                self.activeContainerChanged(last_ac, ac)
            finally:
                # re-query the ative containers, as they might have been altered by setActiveContainer.
                activeBody = Gui.ActiveDocument.ActiveView.getActiveObject("pdbody")
                activePart = Gui.ActiveDocument.ActiveView.getActiveObject("part")
                self.activeObjects[App.ActiveDocument.Name] = (ac, activePart, activeBody)
        
        # detect document saves
        cur_lmd = App.ActiveDocument.LastModifiedDate
        last_lmd = self.lastMD.get(App.ActiveDocument.Name, None)
        if cur_lmd != last_lmd:
            # LastModifiedDate has changed - document was just saved!
            self.lastMD[App.ActiveDocument.Name] = cur_lmd
            if last_lmd is not None: #filter out the apparent change that happens when there was no last-seen value
                self.slotSavedDocument(App.ActiveDocument)
        
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
        
        if ac.isDerivedFrom("App::Document"):
            objects_in = set(App.ActiveDocument.Objects)
        else:
            objects_in = set(  GT.getDirectChildren(ac)  )
        objects_out = set(App.ActiveDocument.Objects) - objects_in
        
        for o in objects_in:
            if hasattr(o.ViewObject, "Selectable"):
                o.ViewObject.Selectable = True
        for o in objects_out:
            if hasattr(o.ViewObject, "Selectable"):
                o.ViewObject.Selectable = False
        
        active_chain = GT.getContainerChain(ac) + [ac]
        for o in App.ActiveDocument.findObjects("Part::BodyBase"):
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
    
