import FreeCAD as App
import Part

def shallowCopy(shape, extra_placement = None):
    """shallowCopy(shape, extra_placement = None): creates a shallow copy of a shape. The 
    copy will match by isSame/isEqual/isPartner tests, but will have an independent placement."""
    
    copiers = {
      "Vertex": lambda sh: sh.Vertexes[0],
      "Edge": lambda sh: sh.Edges[0],
      "Wire": lambda sh: sh.Wires[0],
      "Face": lambda sh: sh.Faces[0],
      "Shell": lambda sh: sh.Shells[0],
      "Solid": lambda sh: sh.Solids[0],
      "CompSolid": lambda sh: sh.CompSolids[0],
      "Compound": lambda sh: sh.Compounds[0],
      }
    copier = copiers.get(shape.ShapeType)
    if copier is None:
        copier = lambda sh: sh.copy()
        App.Console.PrintWarning("PartOMagic: shallowCopy: unexpected shape type '{typ}'. Using deep copy instead.\n".format(typ= shape.ShapeType))
    ret = copier(shape)
    if extra_placement is not None:
        ret.Placement = extra_placement.multiply(ret.Placement)
    return ret
    
def deepCopy(shape, extra_placement = None):
    """deepCopy(shape, extra_placement = None): Copies all subshapes. The copy will not match by isSame/isEqual/
    isPartner tests."""
    
    ret = shape.copy()
    if extra_placement is not None:
        ret.Placement = extra_placement.multiply(ret.Placement)
    return ret    
    
def transformCopy(shape, extra_placement = None):
    """transformCopy(shape, extra_placement = None): creates a deep copy shape with shape's placement applied to 
    the subelements (the placement of returned shape is zero)."""
    
    if extra_placement is None:
        extra_placement = App.Placement()
    ret = shape.copy()
    if ret.ShapeType == "Vertex":
        # oddly, on Vertex, transformShape behaves strangely. So we'll create a new vertex instead.
        ret = Part.Vertex(extra_placement.multVec(ret.Point))
    else:
        ret.transformShape(extra_placement.multiply(ret.Placement).toMatrix(), True)
        ret.Placement = App.Placement() #reset placement
    return ret

def transformCopy_Smart(shape, feature_placement):
    "transformCopy_Smart(shape, feature_placement): unlike transformCopy, creates a shallow copy if possible."
    if shape.isNull():
        return shape
    if PlacementsFuzzyCompare(shape.Placement, App.Placement()):
        sh = shallowCopy(shape)
    else:
        sh = transformCopy(shape)
    sh.Placement = feature_placement
    return sh

def PlacementsFuzzyCompare(plm1, plm2):
    pos_eq = (plm1.Base - plm2.Base).Length < 1e-7   # 1e-7 is OCC's Precision::Confusion
    
    q1 = plm1.Rotation.Q
    q2 = plm2.Rotation.Q
    # rotations are equal if q1 == q2 or q1 == -q2. 
    # Invert one of Q's if their scalar product is negative, before comparison.
    if q1[0]*q2[0] + q1[1]*q2[1] + q1[2]*q2[2] + q1[3]*q2[3] < 0:
        q2 = [-v for v in q2]
    rot_eq = (  abs(q1[0]-q2[0]) + 
                abs(q1[1]-q2[1]) + 
                abs(q1[2]-q2[2]) + 
                abs(q1[3]-q2[3])  ) < 1e-12   # 1e-12 is OCC's Precision::Angular (in radians)
    return pos_eq and rot_eq

def addProperty(docobj, proptype, propname, group, tooltip, defvalue = None, readonly = False):
    """assureProperty(docobj, proptype, propname, defvalue, group, tooltip): adds
    a property if one is missing, and sets its value to default. Does nothing if property 
    already exists. Returns True if property was created, or False if not."""
    
    if propname in docobj.PropertiesList:
        #todo: check type match
        return False
        
    docobj.addProperty(proptype, propname, group, tooltip)
    if defvalue is not None:
        setattr(docobj, propname, defvalue)
    if readonly:
        docobj.setEditorMode(propname, 1)
    return True
