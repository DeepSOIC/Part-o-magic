from xml.etree import ElementTree
import io

property_xml = """<Property name="{name}" type="{type_id}"></Property>"""

class Property(object):
    node = None
    Object = None
    
    def __init__(self, node, object):
        self.Object = object
        self.node = Node
    
    @staticmethod
    def new(object, type_id, name):
        prop = Property(
            None, 
            ElementTree.fromstring(
                property_xml.format(
                    name= name,
                    type_id= type_id
                )
            )
        )
    
    @property
    def TypeId(self):
        return self.node.get('type')
    
    @property
    def Name(self):
        return self.node.get('name')
    
    @Name.setter:
    def Name(self, new_name):
        return self.node.set('name', new_name)
    
class PropertyLink_Abstract(Property):
    def inputs():
        """inputs: returns list of object names linked by this property"""
        raise NotImplementedError()

