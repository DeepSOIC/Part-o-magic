from xml.etree import ElementTree
import io

from .Misc import ReplaceTask, recursiveNodeIterator
property_xml = """<Property name="{name}" type="{type_id}"></Property>"""

class Property(object):
    node = None
    object = None
    
    def __init__(self, node, object):
        self.object = object
        self.node = node
    
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
    def name(self):
        return self.node.get('name')
    
    @name.setter
    def name(self, new_name):
        return self.node.set('name', new_name)
        
    @property
    def value(self):
        raise NotImplementedError()
    
    def getAsAttribute(self):
        """getAsAttribute(): returns a value like FreeCAD returns the value of a property when it's accessed as an attribute of an object"""
        return self.value
        
    def inputs(self):
        """inputs(): returns list of object names linked by this property"""
        return []
    
    def replace(self, replace_task):
        """replace(replace_task): replaces links to objects. Should be a ReplaceTask object. Returns number of replacements done."""
        return 0
    
    def _rename_file(self, rename_dict):
        n_renamed = 0
        for node in recursiveNodeIterator(self.node):
            attribs = node.attrib #dict of attributes
            for attr_name in attribs:
                if attr_name == 'file':
                    fn = attribs[attr_name]
                    if fn in rename_dict:
                        n_renamed += 1
                        node.set(attr_name, rename_dict[fn])
            
        return n_renamed

    def files(self):
        """files(): returns set of filenames used by properties of this object"""
        file_set = set()
        file_list = list()
        for node in recursiveNodeIterator(self.node):
            attribs = node.attrib #dict of attributes
            for attr_name in attribs:
                if attr_name == 'file':
                    file_set.add(attribs[attr_name])
                    file_list.append(attribs[attr_name])
        return file_set
    
    def purgeDeadLinks(self):
        return 0

    
class PropertyLink_Abstract(Property):
    def inputs():
        raise NotImplementedError()
    
    def replace(self, replace_task):
        raise NotImplementedError()
    
    def purgeDeadLinks(self):
        ins = self.inputs()
        
        task = ReplaceTask
        for it in ins:
            if not self.object.project.has(it):
                task[it] = None
        if len(task) > 0:
            return self.replace(task)
        else:
            return 0

#<Property name="link" type="App::PropertyLink" group="" doc="" attr="0" ro="0" hide="0">
#    <Link value="Box"/>
#</Property>
class PropertyLink(PropertyLink_Abstract):
    types = ['App::PropertyLink', 'App::PropertyLinkGlobal', 'App::PropertyLinkChild']
    
    @property
    def value(self):
        v = self.node.find('Link').get('value')
        if v == '':
            return None
        else:
            return v
    
    @value.setter
    def value(self, new_val):
        if new_val is None:
            new_val = ''
        self.node.find('Link').set('value', new_val)
    
    def getObject(self):
        return self.object.project.Object(self.value)

    def getAsAttribute(self):
        ret = self.getObject()
        ret.fetchAttributes()
        return ret
        
    def inputs(self):
        v = self.value
        return [v] if v is not None else []
    
    def replace(self, replace_task):
        if self.value in replace_task:
            self.value = replace_task[self.value]
            return 1
        else:
            return 0
    
    def purgeDeadLinks():
        if not self.object.project.has(self.value):
            self.value = None
    
    
#<Property name="Group" type="App::PropertyLinkList">
#    <LinkList count="3">
#        <Link value="Cone"/>
#        <Link value="Cylinder"/>
#        <Link value="Box"/>
#    </LinkList>
#</Property>
class PropertyLinkList(PropertyLink):
    types = ['App::PropertyLinkList', 'App::PropertyLinkListChild', 'App::PropertyLinkListGlobal']
    
    @property
    def value(self):
        lnn = self.node.find('LinkList')
        return [it.get('value') for it in lnn if it.tag == 'Link']
    
    @value.setter
    def value(self, new_val):
        #purge out Nones.
        new_val = [it for it in new_val if it is not None]

        lnn = self.node.find('LinkList')
        lnn.clear() #removes attributes too, bastard =(
        lnn.set('count', str(len(new_val)))
        for it in new_val:
            lnn.append(ElementTree.fromstring('<Link value="{val}"/>'.format(val= it)))

    def getAsAttribute(self):
        return [self.object.project.getObject(it) for it in self.value]
        
    def inputs(self):
        return self.value
    
    def replace(self, replace_task):
        n_replaced = 0
        new_val = []
        for v in self.value:
            if v in replace_task:
                v = replace_task[v]
                n_replaced += 1
            new_val.append(v)
        if n_replaced:
            self.value = new_val
        return n_replaced

#<Property name="linksub" type="App::PropertyLinkSub" group="" doc="" attr="0" ro="0" hide="0">
#    <LinkSub value="Box" count="2">
#        <Sub value="Edge1"/>
#        <Sub value="Edge3"/>
#    </LinkSub>
#</Property>
class PropertyLinkSub(PropertyLink):
    types = ['App::PropertyLinkSub', 'App::PropertyLinkSubChild', 'App::PropertyLinkSubGlobal']
    
    @property
    def value(self):
        lnn = self.node.find('LinkSub')
        obj = lnn.get('value')
        if obj == '':
            return None
        else:
            return (obj, [it.get('value') for it in lnn if it.tag == 'Sub'])
    
    @value.setter
    def value(self, new_val):
        if new_val == None or new_val[0] is None:
            new_val = ('', [])

        name, sublist = new_val
        lnn = self.node.find('LinkSub')
        lnn.clear() #removes attributes too, bastard =(
        lnn.set('count', str(len(sublist)))
        lnn.set('value', name)
        for it in sublist:
            lnn.append(ElementTree.fromstring('<Sub value="{val}"/>'.format(val= it)))

    def getAsAttribute(self):
        name,subs = self.value
        return self.object.project.getObject(name), subs

    def inputs(self):
        v = self.value
        if len(v[0])>0:
            return [v[0]]
        else:
            return []
    
    def replace(self, replace_task):
        name,subs = self.value
        if name in replace_task:
            v = (replace_task[name], subs)
            self.value = v
            return 1
        else:
            return 0

#<Property name="linksublist" type="App::PropertyLinkSubList" group="" doc="" attr="0" ro="0" hide="0">
#    <LinkSubList count="3">
#        <Link obj="Box" sub="Edge1"/>
#        <Link obj="Box" sub="Edge3"/>
#        <Link obj="Cylinder" sub=""/>
#    </LinkSubList>
#</Property>
class PropertyLinkSubList(PropertyLink):
    types = ['App::PropertyLinkSubList', 'App::PropertyLinkSubListChild', 'App::PropertyLinkSubListGlobal']
    
    @property
    def value(self):
        lnn = self.node.find('LinkSubList')
        return [(it.get('obj'), it.get('sub')) for it in lnn if it.tag == 'Link']
    
    @value.setter
    def value(self, new_val):
        #purge out Nones (may come from a replacement).
        new_val = [it for it in new_val if it is not None]
        new_val = [it for it in new_val if it[0] is not None]

        lnn = self.node.find('LinkSubList')
        lnn.clear() #removes attributes too, bastard =(
        lnn.set('count', str(len(new_val)))
        for it in new_val:
            lnn.append(ElementTree.fromstring('<Link value="{val}" sub="{sub}"/>'.format(val= it[0], sub= it[1])))

    def getAsAttribute(self):
        return [(self.object.project.getObject(name), sub) for name,sub in self.value]

    def inputs(self):
        return [name for name,sub in self.value]
    
    def replace(self, replace_task):
        n_replaced = 0
        new_val = []
        for v in self.value:
            if v[0] in replace_task:
                v = (replace_task[v[0]], v[1])
                n_replaced += 1
            new_val.append(v)
        if n_replaced:
            self.value = new_val
        return n_replaced


#<Property name="Label" type="App::PropertyString">
#    <String value="linker"/>
#</Property>
class PropertyString(Property):
    types = ['App::PropertyString']
    
    @property
    def value(self):
        return self.node.find('String').get('value')
    
    @value.setter
    def value(self, new_val):
        self.node.find('String').set('value', new_val)    

#-----------------------------------------------------------------------------------------------------------------------------------------------------

property_classes = [PropertyLink, PropertyLinkSub, PropertyLinkList, PropertyLinkSubList, PropertyString]
type2class = {}

def register_property_implementation(cls):
    """register_property_implementation(cls): registers a py class that implements a property. cls.types should list applicable C++ types (strings like 'App::PropertySomethingSomething')."""
    global type2class
    for tt in cls.types:
        type2class[tt] = cls
    
def init_types():
    for cls in property_classes:
        register_property_implementation(cls)

init_types()

def CastProperty(prop_node, object):
    '''CastProperty(prop_node, object): returns a property object of appropriate type constructed around given property node.
    If property type is not supported, returns Property instance. 
    @object should be an instance of FilePlant's PropertyContainer. Can be None, but then, some methods may fail.'''
    
    prop = Property(prop_node, object)
    tt = prop.TypeId
    if tt in type2class:    
        prop = type2class[tt](prop_node, object)
    return prop
