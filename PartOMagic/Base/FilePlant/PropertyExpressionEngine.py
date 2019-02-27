from xml.etree import ElementTree

from . import FCProperty
from PartOMagic.Base import ExpressionParser

#<Property name="ExpressionEngine" type="App::PropertyExpressionEngine">
#    <ExpressionEngine count="3">
#        <Expression path="Height" expression="Length"/>
#        <Expression path="Width" expression="Length"/>
#        <Expression path="Length" expression="Cylinder.Shape.Volume ^ (1 / 3)"/>
#    </ExpressionEngine>
#</Property>

##fixme: spreadsheet support?

class PropertyExpression(FCProperty.PropertyLink):

    def getExpressionDeps(self):
        """returns list of lists of tuples. tuple corresponds to a single use of object. Tuple is (id, (start, end_plus_1)), where id is a name or a label of the object."""
        return [ExpressionParser.expressionDeps(self._getExpression(v), None) for v in self.value]

    def inputs(self):
        depsdeps = self.getExpressionDeps()
        ret = []
        doc = self.object.project
        for deps in depsdeps:
            for id,ch_range in deps:
                if doc.getObject(id) is not None:
                    ret.append(dep.linked_object.Name)
                else:
                    t = doc.getObjectsByLabel(id)
                    if len(t) == 1:
                        ret.append(t[0].Name)
        return ret

    def replace(self, replace_task):
        n_replaced = 0
        new_val = []
        val = self.value
        depsdeps = self.getExpressionDeps()
        for i in range(len(val)):
            deps = depsdeps[i]
            expr = self._getExpression(val[i])
            for id, ch_range in deps[::-1]:
                if replacement_task.has(id):
                    new_id = replacement_task.lookup(id)
                elif replacement_task.has_label(id):
                    new_id = replacement_task.lookup_label(id)
                else:
                    new_id = None
                if new_id: #new_id is None also if replacing
                    f,t = ch_range
                    expr = expr[0:f] + new_id + expr[t:]
                    n_replaced += 1
            new_val.append(self._setExpression(val[i], expr))
        if n_replaced:
            self.value = new_val
        return n_replaced
        
    def purgeDeadLinks(self):
        #cleaning out references from an expression is not supported anyway. We could wipe out the expression completely... but let's just let FreeCAD to deal with it.
        return 0

class PropertyExpressionEngine(PropertyExpression):
    types = ['App::PropertyExpressionEngine']
    
    @property
    def value(self):
        lnn = self.node.find('ExpressionEngine')
        return [(it.get('path'), it.get('expression')) for it in lnn if it.tag == 'Expression']
    
    @value.setter
    def value(self, new_val):
        lnn = self.node.find('ExpressionEngine')
        lnn.clear()
        lnn.set('count', str(len(new_val)))
        for path,expr in new_val:
            lnn.append(ElementTree.fromstring('<Expression path="{path}" expression="{expr}"/>'.format(path= path, expr= expr)))
    
    @staticmethod
    def _getExpression(value):
        return value[1]
    
    @staticmethod
    def _setExpression(value, expr):
        return (value[0], expr)
 
   
#<Property name="cells" type="Spreadsheet::PropertySheet">
#    <Cells Count="2">
#        <Cell address="B2" content="volume" />
#        <Cell address="C2" content="=Cylinder.Shape.Volume" alias="Vol" />
#    </Cells>
#</Property>

class PropertyCells(PropertyExpression):
    types = ['Spreadsheet::PropertySheet']
    
    @property
    def value(self):
        lnn = self.node.find('Cells')
        return [it.attrib for it in lnn if it.tag == 'Expression']
    
    @value.setter
    def value(self, new_val):
        lnn = self.node.find('Cells')
        lnn.clear()
        lnn.set('count', str(len(new_val)))
        for path,expr in new_val:
            lnn.append(ElementTree.fromstring('<Expression path="{path}" expression="{expr}"/>'.format(path= path, expr= expr)))

    @staticmethod
    def _getExpression(value):
        expr = value[content]
        if not expr.startswith('='):
            return None
        else:
            return expr
    
    @staticmethod
    def _setExpression(value, expr):
        value[content] = expr
        return value
    
    

FCProperty.register_property_implementation(PropertyExpressionEngine)
FCProperty.register_property_implementation(PropertyCells)