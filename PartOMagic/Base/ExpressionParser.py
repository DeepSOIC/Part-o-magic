print("loading ExpressionParser")
__doc__ = "ExpressionParser: minimalistic routines for extracting information from expressions"

namechars = [chr(c) for c in range(ord('a'), ord('z')+1)]
namechars += [chr(c) for c in range(ord('A'), ord('Z')+1)]
namechars += [chr(c) for c in range(ord('0'), ord('9')+1)]
namechars += ['_']
namechars = set(namechars)

def expressionDeps(expr, doc):
    """expressionDeps(expr, doc): returns set of objects referenced by the expression, as list of Relations with unfilled linking_object.
    expr: expression, as a string
    doc: document where to look up objects by names/labels. 
      If doc is None, all names are assumed valid. A list of tuples is returned instead of list
      of relations: [(name_or_label, (start, end_plus_1))]. This may falsely recognize property 
      self-references as objects, for example in '=Placement.Base.x' will list 'Placement' 
      as an object. """
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
        
    if doc is None:
        #nowhere to look up. Returning the simplified variant: 
        return ids #list of tuples, [(name_or_label, (start, end_plus_1))]
    else:
        from .LinkTools import Relation
        #look up objects
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
