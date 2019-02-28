import FreeCAD as App

from PartOMagic.Gui.Utils import screen

print("loading Containers")

def activeContainer():
    '''activeContainer(): returns active container.
    If there is an active body, it is returned as active container. ActivePart is ignored.
    If there is no active body, active Part is returned.
    If there is no active Part either, active Document is returned.
    If no active document, None is returned.'''
    
    import FreeCAD as App
    import FreeCADGui as Gui
    
    if hasattr(App, "ActiveContainer"):
        return App.ActiveContainer.Object
    
    if Gui.ActiveDocument is None:
        return None
    if Gui.ActiveDocument.ActiveView is None:
        raise NoActiveContainerError("ActiveDocument is not none, but viewer is None. Can't determine active container.")
    activeBody = Gui.ActiveDocument.ActiveView.getActiveObject("pdbody")
    activePart = Gui.ActiveDocument.ActiveView.getActiveObject("part")
    if activeBody:
        return screen(activeBody)
    elif activePart:
        return screen(activePart)
    else:
        return App.ActiveDocument

def setActiveContainer(cnt):
    '''setActiveContainer(cnt): sets active container. To set no active container, supply ActiveDocument. None is not accepted.'''
    
    cnt = screen(cnt)
    
    import FreeCAD as App
    import FreeCADGui as Gui
    
    if hasattr(App, "ActiveContainer"):
        App.setActiveContainer(cnt)
        return

    if not isContainer(cnt):
        raise NotAContainerError("Can't make '{feat}' active as container, because it's not a container (or an unknown type of container)."
                                 .format(feat= cnt.Label))
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


def getAllDependencies(feat):
    '''getAllDependencies(feat): gets all features feat depends on, directly or indirectly. 
    Returns a list, with deepest dependencies last. feat is not included in the list, except 
    if the feature depends on itself (dependency loop).'''

    if feat.isDerivedFrom("App::Document"):
        return feat.Objects

    list_traversing_now = [feat]
    set_of_deps = set()
    list_of_deps = []
    
    while len(list_traversing_now) > 0:
        list_to_be_traversed_next = []
        for feat in list_traversing_now:
            for dep in feat.OutList:
                if not (dep in set_of_deps):
                    set_of_deps.add(dep)
                    list_of_deps.append(screen(dep))
                    list_to_be_traversed_next.append(dep)
        
        list_traversing_now = list_to_be_traversed_next
    
    return list_of_deps

def getAllDependent(feat):
    '''getAllDependent(feat): gets all features that depend on feat, directly or indirectly. 
    Returns a list, with deepest dependencies last. feat is not included in the list, except 
    if the feature depends on itself (dependency loop).'''

    if feat.isDerivedFrom("App::Document"):
        return []

    list_traversing_now = [feat]
    set_of_deps = set()
    list_of_deps = []
    
    while len(list_traversing_now) > 0:
        list_to_be_traversed_next = []
        for feat in list_traversing_now:
            for dep in feat.InList:
                if not (dep in set_of_deps):
                    set_of_deps.add(dep)
                    list_of_deps.append(screen(dep))
                    list_to_be_traversed_next.append(dep)
        
        list_traversing_now = list_to_be_traversed_next
    
    return list_of_deps

def isContainer(obj):
    '''isContainer(obj): returns True if obj is an object container, such as 
    Group, Part, Body. The important characterisic of an object being a 
    container is that it can be activated to receive new objects. Documents 
    are considered containers, too.'''
    
    obj = screen(obj)
    
    if obj.isDerivedFrom('App::Document'):
        return True
    if obj.hasExtension('App::GeoFeatureGroupExtension'):
        return True
#    if obj.hasExtension('App::GroupExtension'):
#        return True  # experimental...
    if obj.isDerivedFrom('App::Origin'):
        return True
    return False

def canBeActive(obj):
    if not isContainer(obj):
        return False
    if obj.isDerivedFrom('App::Origin'):
        return False
    return True

def isMovableContainer(obj):
    '''isMovableContainer(obj): reuturns if obj is a movable container, that 
    forms a local coordinate system.'''
    
    obj = screen(obj)
    
    if obj.isDerivedFrom('App::Document'):
        return False
    if obj.hasExtension('App::OriginGroupExtension'):
        return True
    return False

def getDirectChildren(container):
    
    container = screen(container)
    
    if not isContainer(container): 
        raise NotAContainerError("getDirectChildren: supplied object is not a contianer. It must be a container.")
    if container.isDerivedFrom("App::Document"):
        # find all objects not contained by any Part or Body
        result = set(container.Objects)
        for obj in container.Objects:
            if isContainer(obj):
                children = set(getDirectChildren(obj))
                result = result - children
        return result
    elif container.hasExtension("App::GroupExtension"):
        result = container.Group
        if container.hasExtension("App::OriginGroupExtension"):
            if container.Origin is not None:
                result.append(container.Origin)
        return result
    elif container.isDerivedFrom("App::Origin"):
        return container.OriginFeatures
    raise ContainerUnsupportedError("getDirectChildren: unexpected container type!")
    
def recursiveChildren(container):
    for child in getDirectChildren(container):
        yield child
        if isContainer(child):
            for subchild in recursiveChildren(child):
                yield subchild

def addObjectTo(container, feature, b_advance_tip = True):
    
    container = screen(container)
    feature = screen(feature)
    
    cnt_old = getContainer(feature)
    if not cnt_old.isDerivedFrom('App::Document') and cnt_old is not container:
        raise AlreadyInContainerError(u"Object '{obj}' is already in '{cnt_old}'. Cannot add it to '{cnt_new}'"
                        .format(obj= feature.Label, cnt_old= cnt_old.Label, cnt_new= container.Label))
        
    if cnt_old is container:
        return #nothing to do
        
    if feature is container :
        raise ContainerError(u"Attempting to add {feat} to itself. Feature can't contain itself.".format(feat= feature.Label))

    if container.hasExtension("App::GroupExtension"):
        #container.addObject(feature)
        container.Group = container.Group + [feature]
        if b_advance_tip:
            try:
                container.Proxy.advanceTip(container, feature)
            except AttributeError:
                pass
            except Exception as err:
                App.Console.printError(u"Tip advancement routine failed with an error when adding {feat} to {cnt}. {err}"
                                       .format(feat= feature.Label, 
                                               cnt= container.Label,
                                               err= err.message))
        return
    
    raise ContainerUnsupportedError("No idea how to add objects to containers of type {typ}".format(typ= container.TypeId))
    
def moveObjectTo(feature, container):
    cnt_old = getContainer(feature)
    if cnt_old is container:
        return #nothing to do
        
    withdrawObject(feature)
    addObjectTo(container, feature, b_advance_tip= False)

def withdrawObject(feature):
    container = getContainer(feature)
    if container.isDerivedFrom('App::Document'):
        return
    if container.hasExtension("App::GroupExtension"):
        if feature not in container.Group:
            raise SpecialChildError(u"{feat} is a special child of {container} and can't be withdrawn.".format(feat= feature.Label, container= container.Label))
        #container.removeObject(feature)
        container.Group = [child for child in container.Group if child is not feature]
        assert(feature not in container.Group) #test it was actually removed
    

def getContainer(feat):
    
    feat = screen(feat)
    
    cnt = None
    for dep in feat.InList:
        if isContainer(dep):
            if feat in getDirectChildren(dep):
                if cnt is not None and dep is not cnt:
                    raise ContainerTreeError("Container tree is not a tree")
                cnt = dep
    if cnt is None: 
        return feat.Document
    return screen(cnt)

def getContainerChain(feat):
    '''getContainerChain(feat): return a list of containers feat is in. 
    Last container directly contains the feature. 
    Example of output:  [<document>,<SuperPart>,<Part>,<Body>]'''
    
    if feat.isDerivedFrom('App::Document'):
        return []
    
    list_traversing_now = [feat]
    set_of_deps = set()
    list_of_deps = []
    
    while len(list_traversing_now) > 0:
        list_to_be_traversed_next = []
        for feat in list_traversing_now:
            for dep in feat.InList:
                if isContainer(dep) and feat in getDirectChildren(dep):
                    if not (dep in set_of_deps):
                        set_of_deps.add(dep)
                        list_of_deps.append(screen(dep))
                        list_to_be_traversed_next.append(dep)
        if len(list_to_be_traversed_next) > 1:
            raise ContainerTreeError("Container tree is not a tree")
        list_traversing_now = list_to_be_traversed_next
    
    return [feat.Document] + list_of_deps[::-1]

def getContainerRelativePath(container_from, container_to):
    '''getContainerRelativePath(container_from, container_to): finds container 
    relationship. Returns tuple of two lists. First list is the list of containers 
    to leave. Second list is the list of containers to enter. All lists start from 
    the highest-level container (the ones directly after getCommonContainer).'''

    if not isContainer(container_from):
        raise NotAContainerError("container_from is not a container!")
    if not isContainer(container_to):
        raise NotAContainerError("container_to is not a container!")
    
    chain_from = getContainerChain(container_from) + [container_from]
    chain_to = getContainerChain(container_to) + [container_to]
    
    #find common leading sequence, and chop it off
    i = 0
    min_path_length = min(len(chain_from), len(chain_to))
    for i in range(min_path_length + 1):
        if i == min_path_length:
            break
        if chain_from[i] is not chain_to[i]:
            break
    # now i points to first level where container chains differ
    chain_from = chain_from[i:]
    chain_to = chain_to[i:]
    
    return (chain_from, chain_to)
    
def getCommonContainer(feat_list):
    '''getCommonContainer(feat_list): Returns the deepest common container that 
    contains all features from the list. Returns None if no shared container 
    exists (i.e. features are fom different documents).'''
    
    if len(feat_list) == 0:
        raise ValueError("Empty list supplied, nothing to do")
    list_of_chains = [getContainerChain(feat) for feat in feat_list]
    min_path_length = min([len(chain) for chain in list_of_chains])

    i = 0
    for i in range(min_path_length + 1):
        if i == min_path_length:
            break
        cnt0 = list_of_chains[0][i]
        for l in list_of_chains:
            if l[i] is not cnt0:
                break
    # now i points to first level where container chains differ
    i -= 1
    if i < 0:
        return None #can happen if features are not from one document
    return list_of_chains[0][i]

def getTransformation(container_from, container_to):
    '''getTransformation(container_from, container_to): returns a Placement, which will 
    transform a vector in local coordinates of container_from to local coordinates 
    of container_to.'''
    if not isContainer(container_from):
        raise NotAContainerError("container_from is not a container!")
    if not isContainer(container_to):
        raise NotAContainerError("container_to is not a container!")
    (list_leave, list_enter) = getContainerRelativePath(container_from, container_to)

    trf = App.Placement()
    for cnt in list_leave[::-1]:
        if hasattr(cnt, "Placement"):
            trf = cnt.Placement.multiply(trf)
    for cnt in list_enter:
        if hasattr(cnt, "Placement"):
            trf = cnt.Placement.inverse().multiply(trf)
    return trf
    
def expandList(objects):
    """expandList(objects): Expands the list of objects to include all children of all container in the list.
    Returns tuple of lists: (full_list, top_list, implicit_list). Full_list has all objects and children. 
    Top_list has top-level objects (those not being a child of any of objects). 
    Implicit_list is of those being a child of any of objects."""
    
    #filter out duplicates, just in case. Do it the hard way, to preserve order (but i'm not sure order preservation ever matters)
    seen = set()
    filtered = []
    for obj in objects:
        if obj not in seen:
            filtered.append(obj)
        seen.add(obj)
    objects = filtered; del(filtered)
    
    #scan the tree
    to_add = []
    added = set(objects)
    top_set = set(objects)
    implicit_set = set()
    for obj in objects:
        if isContainer(obj):
            for child in recursiveChildren(obj):
                top_set.discard(child)
                implicit_set.add(child)
                to_add.append(child)
                added.add(child)
    full_list = objects + to_add
    top_list = [obj for obj in full_list if obj in top_set] # could just =list(top_set). But we want to preserve order as much as possible.
    implicit_list = [obj for obj in full_list if obj in implicit_set]
    return (full_list, top_list, implicit_list)

#def inSameCS(object1, object2):
#    (list_leave, list_enter) = getContainerRelativePath(getContainer(object1), getContainer(object2))

# Errors
class ContainerError(ValueError):
    pass
class ContainerTreeError(ContainerError):
    pass
class AlreadyInContainerError(ContainerError):
    pass
class ContainerUnsupportedError(ContainerError):
    pass
class NotAContainerError(ContainerError):
    pass
class SpecialChildError(ContainerError): # happens when attempting to withdraw origin from container
    pass
class GuiContainerError(ValueError):
    pass
class NoActiveContainerError(GuiContainerError): #raised by activeContainer if in spreadsheet or drawing sheet is active
    pass
