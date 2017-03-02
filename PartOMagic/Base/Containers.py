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
    
    if Gui.ActiveDocument is None:
        return None
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
    if obj.hasExtension('App::OriginGroupExtension'):
        return True
    #if obj.hasExtension('App::GroupExtension'):
    #    return True  # as of now, groups cannot be treated like containers.
    if obj.isDerivedFrom('App::Origin'):
        return True
    return False

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
    
def addObjectTo(container, feature, b_advance_tip = True):
    
    container = screen(container)
    feature = screen(feature)
    
    print("adding {feat} to {container}".format(feat= feature.Label, container= container.Label))
    cnt_old = getContainer(feature)
    if not cnt_old.isDerivedFrom('App::Document') and cnt_old is not container:
        raise AlreadyInContainerError("Object '{obj}' is already in '{cnt_old}'. Cannot add it to '{cnt_new}'"
                        .format(obj= feature.Label, cnt_old= cnt_old.Label, cnt_new= container.Label))
        
    if cnt_old is container:
        return #nothing to do
        
    if feature is container :
        raise ContainerError("Attempting to add {feat} to itself. Feature can't contain itself.".format(feat= feature.Label))

    if container.hasExtension("App::GroupExtension"):
        container.addObject(feature)
        if b_advance_tip:
            try:
                container.Proxy.advanceTip(container, feature)
            except AttributeError:
                pass
            except Exception as err:
                App.Console.printError("Tip advancement routine failed with an error when adding {feat} to {cnt}. {err}"
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
    cnt_old = getContainer(feature)
    if cnt_old.isDerivedFrom('App::Document'):
        return
    if container.hasExtension("App::GroupExtension"):
        if feature not in container.Group:
            raise SpecialChildError("{feat} is a special child of {container} and can't be withdrawn.".format(feat= feature.Label, container= container.Label))
        container.removeObject(feature)
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
                if isContainer(dep):
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
