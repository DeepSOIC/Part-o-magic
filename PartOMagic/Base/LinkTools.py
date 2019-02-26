print("loading LinkTools")

import FreeCAD as App
printErr = App.Console.PrintError
printLog = App.Console.PrintLog
printWarn = App.Console.PrintWarning

class Relation(object):
    """Relation object is a unified representation of any parametric relation between documentobjects.
    linking_object.linking_property links to linked_object.
    Constructor is not supposed to be used directly. Call getDependencies or getAllDependencies"""
    
    linking_object = None #object that has the link. I.e. the dependent object. 
    linking_property = None #string - property name
    list_index = None #if property is a list, this is the index into the list.
    expression_charrange = None # if expression, where exactly in the expression. List of tuples (first_char, finish_char_plus_1)
    kind = None #either 'Link', 'Sublink', 'Child', 'Expression' or 'CellExpression'
    linked_object = None 
    sublist = None
    value_repr = None
    
    def __init__(self, linking_object, kind, linking_property, linked_object, **kwargs):
        self.linking_object = linking_object
        self.linking_property = linking_property
        self.kind = kind
        self.linked_object = linked_object
        for key in kwargs:
            setattr(self, key, kwargs[key])
    
    def __repr__(self):
        if self.is_empty():
            return '<empty Relation object>'
        
        linkto = self.linked_object.Name
        if (self.kind == 'Sublink'):
            if self.sublist is None:
                linkto = linkto + '.(None)'
            elif len(self.sublist) ==  1:
                linkto = linkto + '.' + self.sublist[0]
            else:
                linkto = linkto + '.({n} elems)'.format(n= len(self.sublist))
        
        linkfrom = self.linking_object.Name + '.' + self.linking_property 
        if self.list_index is not None:
            linkfrom = linkfrom + '['+str(self.list_index)+']'
        
        return u'<Relation object, {self.kind}, {linkfrom} links to {linkto}>'.format(self= self, linkfrom= linkfrom, linkto= linkto)
    
    def is_empty(self):
        return self.linking_object is None     or     self.linked_object is None
    
    def self_check(self):
        """Checks that the relation is still actual. If all right, simply returns. If relation is outdated raises an error."""
        prop = self.linking_property
        obj  = self.linking_object 
        kind = self.kind                 
        
        if kind == 'CellExpression':
            range = self.expression_charrange
            oldexpr = obj.getContents(prop) #raises ValueError if not a cell
            if not oldexpr.startswith('='): raise ExpressionGoneError()
            #check that the identifier is still at the indexes
            id = oldexpr[range[0]:range[1]]
            if id != self.linked_object.Name or id != self.linked_object.Label:
                raise ExpressionChangedError()
        elif kind == 'Expression':
            range = self.expression_charrange
            ee = dict(obj.ExpressionEngine)
            if not prop in ee: raise ExpressionGoneError()
            oldexpr = ee[prop]
             #check that the identifier is still at the indexes
            id = oldexpr[range[0]:range[1]]
            if id != self.linked_object.Name or id != self.linked_object.Label:
                raise ExpressionChangedError()
        elif kind == 'Child' or kind == 'Link':
            typ = obj.getTypeIdOfProperty(prop)
            val = getattr(obj, prop)
            if typ.startswith('App::PropertyLinkList'):
                if val[self.list_index] is not self.linked_object: 
                    raise LinkChangedError()
            elif typ.startswith('App::PropertyLink'):
                if val is not self.linked_object:
                    raise LinkChangedError()
            else:
                raise TypeError(u"Unexpected type of property: {typ}".format(typ= typ))
        elif kind == 'Sublink':
            typ = obj.getTypeIdOfProperty(prop)
            val = getattr(obj, prop)
            if typ.startswith('App::PropertyLinkSubList'):
                if val[self.list_index][0] is not self.linked_object:
                    raise LinkChangedError()
            elif typ.startswith('App::PropertyLinkSub'):
                if val[0] is not self.linked_object:
                    raise LinkChangedError()
            else:
                raise TypeError(u"Unexpected type of property: {typ}".format(typ= typ))
        else:
            raise TypeError(u"Unexpected kind of dependency: {kind}".format(kind= kind))

    
class Replacement(object):
    """Replacement: holds data about a link change, a single piece in a replacement job.
    The link to be replaced is in attribute .relation. .new_object is the replacement object.
    Constructor: Replacement(relation, new_object, **kwargs):
    **kwargs: additional attributes to set, like Replacement(rel, object_B, new_sublist= "somethingsomething")"""
    
    relation = None #None means the link should be erased
    new_object = None
    new_sublist = None #None means "do not change the subelement"
    replaced = False
    disabled = False #use to disable this replacement in replacement dialog (only works before dialog is created). This flag is initilized by checkSanity.
    disabled_reason = "" #this will appear in status field
    checked = True #use to define checkboxes in dialog (only works before dialog is created)
    
    def __init__(self, relation, new_object, **kwargs):
        self.relation = relation
        self.new_object = new_object
        for key in kwargs:
            setattr(self, key, kwargs[key])
        self.checkSanity()
        
    def __repr__(self):
        if self.relation is None:
            return '<empty Replace object>'
        target = "None" if self.new_object is None else self.new_object.Name
        return u'<Replace object, {self.relation.kind}, {self.relation.linking_object.Name}.{self.relation.linking_property} to set to {target}>'.format(self= self, target= target)

    def replace(self, check_dag = False):
        """replace(check_dag = False): applies this replacement.
        When doing mass-replacements, be extremely careful with expressions. Replacement 
        objects remember exact location of the identifier in string, and they must be done 
        largest-index-first to ensure expressions are not corrupted. So use massReplace 
        function.
        Same applies to removing a link from link list.
        
        @check_dag: if True, before replacement, test for cyclic dependency formation"""
        
        if self.replaced:
            raise AlreadyReplacedError("Replacement already done, can't repeat.")
        self._replace(check_dag)
        self.replaced = True


    def _replace(self, check_dag):
        # does the business of replacing. But does not set self.replaced flag, so that I can use return statement without caution.
        prop = self.relation.linking_property
        new = self.new_object
        obj = self.relation.linking_object 
        kind = self.relation.kind                 
        
        printLog(u"  replacing: {self}\n".format(self= self))
        if check_dag:
            if self.check_dag() == False:
                raise DAGError(u"Replacement will cause a cycle: {repl}".format(repl= repr(self)))
        
        try:        
            self.relation.self_check()
        except ExpressionGoneError:
            if new is None: return #during mass-replacements with no new object, expression may have been gone already as a result of previous replacement. Skip this.
            raise
        
        if kind == 'CellExpression':
            if self.relation.linked_object is self.new_object:
                printWarn(u"Replacement invoked, but nothing to do. {self}".format(self= repr(self)))
                return #nothing to do
            range = self.relation.expression_charrange
            oldexpr = obj.getContents(prop) #raises ValueError if not a cell
            if len(oldexpr) == 0 and new is None: return #during mass-replacements with no new object, expression may have been gone already as a result of previous replacement. Skip this.
            if not oldexpr.startswith('='): raise ReplacementError("No expression found for replacement")
            if new is not None:
                newexpr = oldexpr[0:range[0]] + new.Name + oldexpr[range[1]:]
            else:
                newexpr = ''
                
            if newexpr is not None:
                printLog(u"    '{oldexpr}' -> '{newexpr}'\n"
                         .format(oldexpr= oldexpr,
                                 newexpr= newexpr))
                obj.set(prop, newexpr)
        elif kind == 'Expression':
            if self.relation.linked_object is self.new_object:
                printWarn(u"Replacement invoked, but nothing to do. {self}".format(self= repr(self)))
                return #nothing to do
            ee = dict(obj.ExpressionEngine)
            if not prop in ee and new is None: return #during mass-replacements with no new object, expression may have been gone already as a result of previous replacement. Skip this.
            if not prop in ee: raise ReplacementError("No expression found for replacement")
            oldexpr = ee[prop]
            range = self.relation.expression_charrange
            if new is not None:
                newexpr = oldexpr[0:range[0]] + new.Name + oldexpr[range[1]:]
            else:
                newexpr = ''
            if newexpr is not None:
                printLog(u"    '{oldexpr}' -> '{newexpr}'\n"
                         .format(oldexpr= oldexpr,
                                 newexpr= newexpr))
                obj.setExpression(prop, newexpr)
        elif kind == 'Child' or kind == 'Link':
            if self.relation.linked_object is self.new_object:
                printWarn(u"Replacement invoked, but nothing to do. {self}".format(self= repr(self)))
                return #nothing to do
            if kind == 'Child':
                #when replacing child links, make sure the new object is not in a container. Otherwise FreeCAD throws an error.
                from PartOMagic.Base import Containers
                Containers.withdrawObject(new)
            typ = obj.getTypeIdOfProperty(prop)
            val = getattr(obj, prop)
            if typ.startswith('App::PropertyLinkList'):
                val = val[0:self.relation.list_index] + ([] if new is None else [new]) + val[self.relation.list_index+1:]
            elif typ.startswith('App::PropertyLink'):
                val = new
            else:
                raise TypeError(u"Unexpected type of property: {typ}".format(typ= typ))
            setattr(obj, prop, val)
        elif kind == 'Sublink':
            typ = obj.getTypeIdOfProperty(prop)
            val = getattr(obj, prop)
            if self.relation.linked_object is self.new_object and (self.new_sublist is None or self.relation.sublist == self.new_sublist):
                printWarn(u'Replacement invoked, but nothing to do. {self}'.format(self= repr(self)))
                return #nothing to do

            sublist = self.new_sublist if self.new_sublist is not None else self.relation.sublist
            if typ.startswith('App::PropertyLinkSubList'):
                val = val[0:self.relation.list_index] + [(new, sublist)] + val[self.relation.list_index+1:]
            elif typ.startswith('App::PropertyLinkSub'):
                val = (new, sublist)
            else:
                raise TypeError(u"Unexpected type of property: {typ}".format(typ= typ))
            setattr(obj, prop, val)
        else:
            raise TypeError(u"Unexpected kind of dependency: {kind}".format(kind= kind))
    

    def check_dag(self):
        """check_dag(): returns True if DAG-compatible, and False otherwise. Note that it may be wrong for mass-replacements"""
        if replaced:
            raise AlreadyReplacedError("Replacement already done, can't check.")
        if self.new_object is None: 
            return True
        import Containers
        deps = Containers.getAllDependent(self.relation.linking_object)
        if self.new_object in deps: 
            return False
        return True
    
    def disable(self, message):
        """disable(message): marks this replacement as disabled, and attaches a message as to 
        why it is disabled. Use for GUI purposes only. Disabling the replacement won't make 
        replace() method do nothing."""
        
        self.disabled = True
        self.disabled_reason = message
    
    def isToBeAvoided(self):
        """isToBeAvoided(): Checks the relation against a list of ones known to be unreplaceable, such as read-only 
        link properties. 
        Returns tuple (bool, message), bool is True if the link is unreplaceable, and message
        is a string, explaining why."""
        
        obj = self.relation.linking_object
        prop = self.relation.linking_property
        readonly = "Read-only property"
        if obj.isDerivedFrom('Spreadsheet::Sheet') and prop == 'docDeps':
            return (True, readonly)
        return (False, "")
    
    def checkSanity(self):
        """checkSanity(): Checks that this replacement can potentially be done. In particular, checks if the 
        property is known to be read-only. If found so, sets disabled flag.
        Returns True if the replacement is OK."""
        itba, message = self.isToBeAvoided()
        if itba:
            self.disable(message)
        return not itba

def massReplace(replacements, check_dag = False):
    """massReplace(replacements, check_dag = False): Does a number of replaces at once. 
    Takes care to make sure the order is correct, so that expression char indexes and link-list 
    indexes are not mixed up in the process.
    check_dag: tests for dependency loop before each replacement. It's quite stupid, it 
    doesn't take into account the replacements that are pending. Slow."""
    
    if len(replacements) == 0:
        raise NothingToReplace("Nothing to replace")
    
    order = sortForMassReplace(replacements)
    
    errs = []
    for repl in order:
        try:
            repl.replace()
        except Exception as err:
            printErr(str(err))
            errs.append(err)
            repl.error = err
    if len(errs)>0:
        raise MassReplaceErrorList('{failed} of {total} replacements failed.', errs)

def sortForMassReplace(replacements):
    """sortForMassReplace(replacements): sorts replacements, so they can be applied one by one without invalidating each other
    Returns: sorted list. Original list is not touched."""
    def sort_func(repl):
        i1 = 0 if repl.relation.list_index is None else repl.relation.list_index
        i2 = 0 if repl.relation.expression_charrange is None else repl.relation.expression_charrange[0]
        return (i1, i2)
    return sorted(replacements, key= sort_func)[::-1]
    

def getDependencies(object, property = None):
    """getDependencies(object, property = None): Returns list of object dependencies as Relation objects, for @prop property of the object. 
    If @prop is None, all properties are scanned, and this is an elaborate equivalent of OutList."""
    
    if property is None: 
        props = object.PropertiesList
    else:
        props = [property]
    
    result = []
    for prop in props:
        typ = object.getTypeIdOfProperty(prop)
        val = getattr(object, prop)
        if typ.startswith('App::PropertyLinkSubList'):
            for i in range(len(val)):
                obj, sublist = val[i]
                result.append(Relation(object, 'Sublink', prop, obj, sublist= sublist, list_index= i, value_repr= obj.Name + "." + repr(sublist)))
        elif typ.startswith('App::PropertyLinkSub'):
            if val is not None:
                obj, sublist = val
                result.append(Relation(object, 'Sublink', prop, obj, sublist= sublist, value_repr= obj.Name + "." + repr(sublist)))
        elif typ.startswith('App::PropertyLinkList'):
            value_repr = '['+', '.join([obj.Name for obj in val]) + ']'
            for i in range(len(val)):
                obj = val[i]
                kind = 'Link'
                if prop == 'Group':
                    kind = 'Child'
                if prop == 'OriginFeatures' and object.isDerivedFrom('App::Origin'):
                    kind = 'Child'
                result.append(Relation(object, kind, prop, obj, list_index= i, value_repr= value_repr))
        elif typ.startswith('App::PropertyLink'):
            if val is not None:
                kind = 'Link'
                if prop == 'Origin' and object.hasExtension('App::OriginGroupExtension'): 
                    kind = 'Child'
                result.append(Relation(object, kind, prop, val, value_repr= val.Name))
    
    #scan expressions bound to properties
    for itprop, expr in object.ExpressionEngine:
        if property is not None and property != itprop: continue
        deps = expressionDeps(expr, object.Document)
        for dep in deps:
            if dep.linked_object is not object: #skip self-references
                dep.linking_object = object
                dep.linking_property = itprop
                dep.value_repr = expr
                result.append(dep)
    
    #scan expressions in spreadsheet cells
    if object.isDerivedFrom('Spreadsheet::Sheet'):
        for itprop in props:
            try:
                expr = object.getContents(itprop) #raises ValueError if not a cell
                if not expr.startswith('='): 
                    continue
            except ValueError:
                continue
            deps = expressionDeps(expr, object.Document)
            for dep in deps:
                if dep.linked_object is not object: #skip self-references
                    dep.linking_object = object
                    dep.linking_property = itprop
                    dep.kind = 'CellExpression'
                    dep.value_repr = expr
                    result.append(dep)

    return result


def findLinksTo(obj, within = None):
    """findLinksTo(obj, within = None): finds all uses of *obj* by objects in *within*. Like InList, but with details.
    
    *within*: either None, an object, or list of objects. If None, all objects from document will be used.
    
    Returns list of Relation objects. """
    
    if within is None:
        within = obj.Document.Objects
    if hasattr(within, 'isDerivedFrom'): #single object -> convert into list
        within = [within]
    
    result = []
    
    for it in within:
        # new! use getDependencies
        for dep in getDependencies(it):
            if dep.linked_object is obj:
                result.append(dep)
        continue
    return result


def allRelations(document):
    """allRelations(document): Returns list of all parametric relations in the document.
    returns: list of Relation objects."""
    
    result = []
    for obj in document.Objects:
        result += getDependencies(obj)
    return result
    

def replaceObject(orig, new, within = None, do_it = True, child_links_too = False):
    """replaceObject(orig, new, within = None, do_it = True, child_links_too = False): redirects all uses of @orig to point to @new instead. 
    If @do_it is True, just makes it happen, and returns list of replacements done. If @do_it is False, 
    returns list of replacements to be done, which can then be applied by calling massReplace.
    @within is object or list where to search. If None, whole project is searched.
    @child_links_too: if true, will try to replace in childship links same as in regular links. 
    Note that it may fail, because FreeCAD won't allow same object be in two containers at 
    any time, even for transient moments."""
    rels = findLinksTo(orig, within)
    repls = [Replacement(rel, new) for rel in rels if rel.kind != 'Child' or child_links_too]
    if do_it: 
        massReplace(repls, check_dag= True)
    else:
        return repls    


namechars = [chr(c) for c in range(ord('a'), ord('z')+1)]
namechars += [chr(c) for c in range(ord('A'), ord('Z')+1)]
namechars += [chr(c) for c in range(ord('0'), ord('9')+1)]
namechars += ['_']
namechars = set(namechars)

def replaceNameInExpression(expr, old_name, new_name):
    """replaceNameInExpression(expr, old_name, new_name): replaces an identifier in an expression.
    expr: expression (a string).
    Return: If not found, returns None. If replaced, returns new expression."""
 
    #FIXME: prevent replacement of function names
    global namechars

    valchanged = False
    n = len(old_name)
    i = len(expr)
    while True:
        i = expr.rfind(old_name, 0,i)
        if i == -1:
            break
        
        #match found, but that can be a match inside of a different name. Test if characters around are non-naming.
        match = True
        if i > 0:
            if expr[i-1] in namechars:
                match = False
        if i+n < len(expr):
            if expr[i+n] in namechars:
                match = False
        
        #replace it
        if match:
            valchanged = True
            expr = expr[0:i] + new_name + expr[i+n : ]
    if valchanged:
        return expr
    else:
        return None


def expressionDeps(expr, doc):
    """expressionDeps(expr, doc): returns set of objects referenced by the expression, as list of Relations with unfilled linking_object.
    expr: expression, as a string
    doc: document where to look up objects by names/labels"""
    global namechars
    startchars = set("+-*/(%^&\[<>;, =")
    endchars = set(".")
    
    ids = [] #list of tuples: (identifier, (start, end_plus_1))
    start = 0
    finish = 0
    for i in range(len(expr)):
        if expr[i] in startchars:
            start = i+1
        elif expr[i] in endchars:
            finish = i
            if finish - start > 0:
                ids.append((expr[start:finish], (start, finish)))
            start = len(expr)
        elif expr[i] not in namechars:
            finish = i
            start = len(expr)
        
    ret = []
    for id, id_range in ids:
        # try by name
        
        obj = doc.getObject(id)
        if obj is None:
            # try by label
            objs = doc.getObjectsByLabel(id)
            if len(objs) == 1:
                obj = objs[0]
        if obj is not None:
            ret.append(Relation(None, 'Expression', None, obj, expression_charrange= id_range))
        else:
            printWarn(u"identifier in expression not recognized: {id}".format(id= id))
            
    return ret
    
    
    
def getAllDependentObjects(feat):
    '''getAllDependentObjects(feat): gets all features that depend on feat, directly or indirectly. 
    Returns a set of document objects. feat is not included in the list, except 
    if the feature depends on itself (dependency loop).'''

    if feat.isDerivedFrom("App::Document"):
        return set()

    list_traversing_now = [feat]
    set_of_deps = set()
    
    while len(list_traversing_now) > 0:
        list_to_be_traversed_next = []
        for feat in list_traversing_now:
            for dep in feat.InList:
                if not (dep in set_of_deps):
                    set_of_deps.add(dep)
                    list_to_be_traversed_next.append(dep)
        
        list_traversing_now = list_to_be_traversed_next
    
    return set_of_deps

def getAllDependencyObjects(feat):
    '''getAllDependencyObjects(feat): gets all features feat depends on, directly or indirectly. 
    Returns a set. feat is not included in the list, except 
    if the feature depends on itself (dependency loop).'''

    if feat.isDerivedFrom("App::Document"):
        return feat.Objects

    list_traversing_now = [feat]
    set_of_deps = set()
    
    while len(list_traversing_now) > 0:
        list_to_be_traversed_next = []
        for feat in list_traversing_now:
            for dep in feat.OutList:
                if not (dep in set_of_deps):
                    set_of_deps.add(dep)
                    list_to_be_traversed_next.append(dep)
        
        list_traversing_now = list_to_be_traversed_next
    
    return set_of_deps
    
class ReplacementError(RuntimeError):
    """Base class for errors that arise when executing a Replacement object. Note that it may fire other types of errors, too."""
    def __str__(self):
        if self.args:
            return self.args[0]
        else:
            return type(self).__name__
            
class AlreadyReplacedError(ReplacementError):
    """Thrown when Replacement object is executed twice"""
class DAGError(ReplacementError):
    """Thrown when the replacement would create a cyclic dependency"""

class RelationOutdatedError(ReplacementError):
    """Base class for errors happening due to changes to object between Replacement object creation and deletion."""
class ExpressionGoneError(RelationOutdatedError):
    """Thrown when expression was gone between replace object creation and execution"""
class ExpressionChanedError(RelationOutdatedError):
    """Thrown when expression has changed between replace object creation and execution"""
class LinkChangedError(RelationOutdatedError):
    """Thrown when link has changed between replace object creation and execution"""
    
class MassReplaceError(RuntimeError):
    """base class for mass-replace errors"""
    def __str__(self):
        if self.args:
            return self.args[0]
        else:
            return type(self).__name__

class MassReplaceErrorList(RuntimeError):
    """Thrown when some replacements in mass replace failed. List of errors available as self.args[1]"""
    def __str__(self):
        if self.args:
            return self.args[0]
        else:
            return type(self).__name__

class NothingToReplaceError(ReplacementError):
    """Thrown when empty replacements list is supplied to massReplace"""
    
