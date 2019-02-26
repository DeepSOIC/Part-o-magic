from xml.etree import ElementTree

from . import FCProperty
from PartOMagic.Base import LinkTools

#<Property name="ExpressionEngine" type="App::PropertyExpressionEngine">
#    <ExpressionEngine count="3">
#        <Expression path="Height" expression="Length"/>
#        <Expression path="Width" expression="Length"/>
#        <Expression path="Length" expression="Cylinder.Shape.Volume ^ (1 / 3)"/>
#    </ExpressionEngine>
#</Property>

##fixme: spreadsheet support?

class PropertyExpressionEngine(FCProperty.PropertyLink):
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
    
    def getExpressionDeps(self):
        v = self.value
        ret = []
        for path,expr in v:
            deps = LinkTools.expressionDeps(expr, self.object.project)
            ret.append(deps)
        return ret
    
    def inputs(self):
        depsdeps = self.getExpressionDeps()
        ret = []
        for deps in depsdeps:
            for dep in deps:
                ret.append(dep.linked_object.Name)
        return ret
    
    def replace(self, replacement_dict):
        n_replaced = 0
        new_val = []
        val = self.value
        depsdeps = self.getExpressionDeps()
        for i in range(len(val)):
            deps = depsdeps[i]
            expr = val[i][1]
            for dep in deps[::-1]:
                if dep.linked_object.Name in replacement_dict:
                    f,t = dep.expression_charrange
                    expr = expr[0:f] + replacement_dict[dep.linked_object.Name] + expr[t:]
                    n_replaced += 1
            new_val.append((val[i][0], expr))
        if n_replaced:
            self.value = new_val
        return n_replaced

FCProperty.register_property_implementation(PropertyExpressionEngine)