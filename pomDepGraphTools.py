import FreeCAD as App

def getAllDependencies(feat):
    '''getAllDependencies(feat): gets all features feat depends on, directly or indirectly. 
    Returns a list, with deepest dependencies last. feat is not included in the list, except 
    if the feature depends on itself (dependency loop).'''
    list_traversing_now = [feat]
    set_of_deps = set()
    list_of_deps = []
    
    while len(list_traversing_now) > 0:
        list_to_be_traversed_next = []
        for feat in list_traversing_now:
            for dep in feat.OutList:
                if not (dep in set_of_deps):
                    set_of_deps.add(dep)
                    list_of_deps.append(dep)
                    list_to_be_traversed_next.append(dep)
        
        list_traversing_now = list_to_be_traversed_next
    
    return list_of_deps

def getAllDependent(feat):
    '''getAllDependent(feat): gets all features that depend on feat, directly or indirectly. 
    Returns a list, with deepest dependencies last. feat is not included in the list, except 
    if the feature depends on itself (dependency loop).'''
    list_traversing_now = [feat]
    set_of_deps = set()
    list_of_deps = []
    
    while len(list_traversing_now) > 0:
        list_to_be_traversed_next = []
        for feat in list_traversing_now:
            for dep in feat.InList:
                if not (dep in set_of_deps):
                    set_of_deps.add(dep)
                    list_of_deps.append(dep)
                    list_to_be_traversed_next.append(dep)
        
        list_traversing_now = list_to_be_traversed_next
    
    return list_of_deps

def isContainer(obj):
    '''isContainer(obj): returns True if obj is an object container, such as 
    Group, Part, Body. The important characterisic of an object being a 
    container is its action on visibility of linked objects. E.g. a 
    Part::Compound is not a group, because it does not affect visibility 
    of originals. Documents are considered containers, too.'''
    
    if obj.isDerivedFrom("App::DocumentObjectGroup"):
        return True
    if obj.isDerivedFrom("PartDesign::Body"):
        return True
    if obj.isDerivedFrom("App::Origin"):
        return True
    if obj.isDerivedFrom('App::Document'):
        return True

def getContainer(feat):
    cnt = None
    for dep in feat.InList:
        if isContainer(dep):
            if not cnt is None:
                raise ValueError("Container tree is not a tree")
            cnt = dep
    if cnt is None: 
        return feat.Document
    return cnt

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
                        list_of_deps.append(dep)
                        list_to_be_traversed_next.append(dep)
        if len(list_to_be_traversed_next) > 1:
            raise ValueError("Container tree is not a tree")
        list_traversing_now = list_to_be_traversed_next
    
    return [feat.Document] + list_of_deps[::-1]

def getContainerRelativePath(container_from, container_to):
    '''getContainerRelativePath(container_from, container_to): finds container 
    relationship. Returns tuple of two lists. First list is the list of containers 
    to leave. Second list is the list of containers to enter. All lists start from 
    the highest-level container (the ones directly after getCommonContainer).'''

    if not isContainer(container_from):
        raise TypeError("container_from is not a container!")
    if not isContainer(container_to):
        raise TypeError("container_to is not a container!")
    
    chain_from = getContainerChain(container_from) + [container_from]
    chain_to = getContainerChain(container_to) + [container_to]
    
    #find common leading sequence, and chop it off
    i = 0
    for i in range(min(len(chain_from), len(chain_to))):
        if chain_from[i] is not chain_to[i]:
            break;
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
    for i in range(min_path_length):
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
        raise TypeError("container_from is not a container!")
    if not isContainer(container_to):
        raise TypeError("container_to is not a container!")
    (list_leave, list_enter) = getContainerRelativePath(container_from, container_to)

    trf = App.Placement()
    for cnt in list_leave[::-1]:
        if hasattr(cnt, "Placement"):
            trf = cnt.Placement.multiply(trf)
    for cnt in list_enter:
        if hasattr(cnt, "Placement"):
            trf = cnt.Placement.inverse().multiply(trf)
    return trf