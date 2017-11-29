print("loading LinkTools")

import FreeCAD as App
printErr = App.Console.PrintError
printLog = App.Console.PrintLog
printWarn = App.Console.PrintWarning


def findLinksTo(obj, within = None):
    """findLinksTo(obj, within): finds all uses of *obj* by objects in *within*. Like InList, but with details.
    
    *within*: either None, an object, or list of objects. If None, all objects from document will be used.
    
    Returns list of tuples [(object, 'kind', 'prop_name', obj), ...]. 'kind' is the link 
    kind, either 'Link', 'Sublink', 'Child', 'Expression' or 'CellExpression'. 'prop_name' 
    is the name of property involved (either the link property, or the property the 
    expression is bound to). obj is the object being linked to, i.e. the function argument.
    """
    if within is None:
        within = obj.Document.Objects
    if hasattr(within, 'isDerivedFrom'): #single object -> convert into list
        within = [within]
    
    result = []
    
    for it in within:
        # new! use getDependencies
        for dep in getDependencies(it):
            if dep[3] is obj:
                result.append(dep)
        continue
        # find in properties
        for prop in it.PropertiesList:
            typ = it.getTypeIdOfProperty(prop)
            val = getattr(it, prop)
            if typ.startswith('App::PropertyLinkSubList'):
                if obj in [lnk for lnk,subs in val]: 
                    result.append((it, 'Sublink', prop, obj))
            elif typ.startswith('App::PropertyLinkSub'):
                if val is not None and it is val[0]:
                    result.append((it, 'Sublink', prop, obj))
            elif typ.startswith('App::PropertyLinkList'):
                if obj in val:
                    result.append((it, 'Child' if prop == 'Group' else 'Link', prop, obj))
            elif typ.startswith('App::PropertyLink'):
                if obj is val:
                    result.append((it, 'Link', prop, obj))
        
        #find in expressions bound to properties
        for prop, expr in it.ExpressionEngine:
            oldexpr = expr
            newexpr = replaceNameInExpression(expr, it.Name, '')
            if newexpr is not None: #this is a test that name was found and replaced
                result.append((it, 'Expression', prop, obj))
            
        
        #find in expressions in spreadsheet cells
        if it.isDerivedFrom('Spreadsheet::Sheet'):
            for prop in it.PropertiesList:
                try:
                    expr = it.getContents(prop) #raises ValueError if not a cell
                    if not expr.startswith('='): raise ValueError()
                except ValueError:
                    continue
                oldexpr = expr
                newexpr = replaceNameInExpression(expr, orig.Name, new.Name)
                if newexpr is not None:
                    result.append((it, 'CellExpression', prop, obj))
                
    return result

def getDependencies(obj):
    """getDependencies(obj): like obj.OutList, but with extended information.
    returns list of tuples [(object_that_links, kind, prop, object_used)]"""
    result = []
    # find in properties
    for prop in obj.PropertiesList:
        typ = obj.getTypeIdOfProperty(prop)
        val = getattr(obj, prop)
        if typ.startswith('App::PropertyLinkSubList'):
            for lnk,subs in val: 
                result.append((obj, 'Sublink', prop, lnk))
        elif typ.startswith('App::PropertyLinkSub'):
            if val is not None:
                lnk = val[0]
                result.append((obj, 'Sublink', prop, lnk))
        elif typ.startswith('App::PropertyLinkList'):
            kind = 'Child' if prop == 'Group' else 'Link'
            for lnk in val:
                result.append((obj, kind, prop, lnk))
        elif typ.startswith('App::PropertyLink'):
            if val is not None:
                lnk = val
                result.append((obj, 'Link', prop, lnk))
    
    #find in expressions bound to properties
    for prop, expr in obj.ExpressionEngine:
        deps = expressionDeps(expr, obj.Document)
        deps.discard(obj)
        for lnk in deps:
            result.append((obj, 'Expression', prop, lnk))
    
    #find in expressions in spreadsheet cells
    if obj.isDerivedFrom('Spreadsheet::Sheet'):
        for prop in obj.PropertiesList:
            try:
                expr = obj.getContents(prop) #raises ValueError if not a cell
                if not expr.startswith('='): raise ValueError()
            except ValueError:
                continue
            deps = expressionDeps(expr, obj.Document)
            deps.discard(obj) #self-references are OK in expressions, and we just ignore them.
            for lnk in deps:
                result.append((obj, 'CellExpression', prop, lnk))
    return result

    
class ReplacementError(RuntimeError):
    pass
    
def replaceObject(orig, new, task):
    """replaceObject(orig, new, task): replaces object *orig* with *new* in links listed by *task*.
    *task*: list of tuples [(object, 'kind', 'prop_name'), ...]. Use findLinksTo to generate tasks.
    
    Raises ReplacementError if unsuccessful, which contains list of actual exceptions as args[1]."""
    
    errors = 0
    for (dep, kind, prop) in within:
        try:
            printLog("  replacing: {kind} {dep}.{prop}\n"
                     .format(kind= kind, dep= dep, prop= prop))
            if kind == 'CellExpression':
                oldexpr = dep.getContents(prop) #raises ValueError if not a cell
                if not oldexpr.startswith('='): raise ValueError()
                if new is not None:
                    newexpr = replaceNameInExpression(expr, orig.Name, new.Name)
                else:
                    newexpr = ''
                    
                if newexpr is not None:
                    printLog("    '{oldexpr}' -> '{newexpr}'\n"
                             .format(oldexpr= oldexpr,
                                     newexpr= newexpr))
                    dep.set(prop, newexpr)
            elif kind == 'Expression':
                oldexpr = dict(dep.ExpressionEngine)[prop]
                if new is not None:
                    newexpr = replaceNameInExpression(expr, orig.Name, new.Name)
                else:
                    newexpr = ''
                if newexpr is not None:
                    printLog("    '{oldexpr}' -> '{newexpr}'\n"
                             .format(oldexpr= oldexpr,
                                     newexpr= newexpr))
                    dep.setExpression(prop, newexpr)
            elif kind == 'Child' or kind == 'Link':
                typ = dep.getTypeIdOfProperty(prop)
                val = getattr(dep, prop)
                valchanged = False
                if typ.startswith('App::PropertyLinkList'):
                    if orig in val:
                        valchanged = True
                        val = [(new if lnk is orig else lnk) for lnk in val]
                elif typ.startswith('App::PropertyLink'):
                    if obj is val:
                        valchanged = True
                        val = new
                else:
                    raise TypeError("Unexpected type of property: {typ}".format(typ= typ))
                if not valchanged: raise ValueError("Object usage not found, nothing to replace")
                setattr(dep, prop, val)
            elif kind == 'Sublink':
                typ = dep.getTypeIdOfProperty(prop)
                val = getattr(dep, prop)
                valchanged = False
                if typ.startswith('App::PropertyLinkSubList'):
                    if orig in [lnk for lnk,subs in val]: 
                        valchanged = True
                        val = [((new if lnk is orig else lnk), subs) for lnk,subs in val]
                elif typ.startswith('App::PropertyLinkSub'):
                    if val is not None and orig is val[0]:
                        valchanged = True
                        val = tuple([new] + val[1:])
                else:
                    raise TypeError("Unexpected type of property: {typ}".format(typ= typ))
                if not valchanged: raise ValueError("Object usage not found, nothing to replace")
                setattr(dep, prop, val)
            else:
                raise TypeError("Unexpected kind of dependency: {kind}".format(kind= kind))
        except Exception as err:
            printErr("    FAILED. {err}\n".format(err= repr(err)))
            errors.append(err)
        
        if len(errors)>0:
            raise ReplacementError("Replacement failed with {n} errors".format(n= len(errors)), errors)

namechars = [chr(c) for c in range(ord('a'), ord('z')+1)]
namechars += [chr(c) for c in range(ord('A'), ord('Z')+1)]
namechars += [chr(c) for c in range(ord('0'), ord('9')+1)]
namechars += ['_']
namechars = set(namechars)

def replaceNameInExpression(expr, old_name, new_name):
    'If not found, returns None. If replaced, returns new expression.'
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
    """expressionDeps(expr, doc): returns set of objects referenced by the expression."""
    global namechars
    startchars = set("+-*/(%^&\[<>;, ")
    endchars = set(".")
    
    ids = []
    start = 0
    finish = 0
    for i in range(len(expr)):
        if expr[i] in startchars:
            start = i+1
        elif expr[i] in endchars:
            finish = i
            if finish - start > 0:
                ids.append(expr[start:finish])
            start = len(expr)
        elif expr[i] not in namechars:
            finish = i
            start = len(expr)
    
    #debug
    for id in ids: 
        print(id)
    
    ret = set()
    for id in ids:
        # try by name
        obj = doc.getObject(id)
        if obj is None:
            # try by label
            objs = App.ActiveDocument.getObjectsByLabel(id)
            if len(objs) == 1:
                obj = objs[0]
        if obj is not None:
            ret.add(obj)
        else:
            printWarn("identifier in expression not recognized: {id}".format(id= id))
            
    return ret