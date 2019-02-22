print("loading FCObject.py")
import zipfile
from xml.etree import ElementTree
import io

from .Errors import *

class PropertyContainer(object):
    """Either a DocumentObject or ViewProvider"""
    datanode = None
    objectnode = None
    Name = ''
    project = None # reference to a project this object is part of
    
    def __init__(self, name, objectnode, datanode, project):
        """__init__(name, objectnode, datanode, project): (object_node should be None for a viewprovider)"""
        self.objectnode = objectnode
        self.datanode = datanode
        self.Name = name
        self.project = project
    
    def getPropertyNode(self, prop_name):
        prop = self.datanode.find('Properties/Property[@name="{propname}"]'.format(propname= prop_name))
        if prop is None:
            raise AttributeError("Object {obj} has no property named '{prop}'".format(obj= self.Name, prop= attr_name))
        return prop
    
    @property
    def TypeId(self):
        return self.objectnode.get("type")
    
    @TypeId.setter
    def TypeId(self, new_type_id):
        self.objectnode.set('type', new_type_id)
    
    def getPropertiesNodes(self):
        return self.datanode.findall('Properties/Property')

    @property
    def PropertiesList(self):
        propsnodes = self.getPropertiesNodes()
        return [prop.get('name') for prop in propsnodes]
    
    def renameProperty(self, old_name, new_name):
        node = self.getPropertyNode(old_name)
        node.set('name', new_name)
    
    def files(self):
        """files(): returns set of filenames used by properties of this object"""
        file_set = set()
        file_list = list()
        def scanNode(node):
            attribs = node.attrib #dict of attributes
            for attr_name in attribs:
                if attr_name == 'file':
                    file_set.add(attribs[attr_name])
                    file_list.append(attribs[attr_name])
            for subnode in node:
                scanNode(subnode)
        scanNode(self.datanode)
        return file_set
    
    def _rename_file(self, rename_dict):
        """substitutes file references in properties. does not rename actual files. Returns number of occurences replaced."""
        n_renamed = 0
        def scanNode(node):
            attribs = node.attrib #dict of attributes
            for attr_name in attribs:
                if attr_name == 'file':
                    fn = attribs[attr_name]
                    if fn in rename_dict:
                        n_renamed += 1
                        node.set(attr_name, rename_dict[fn])
            for subnode in node:
                scanNode(subnode)
        scanNode(self.datanode)
        return n_renamed
    
    def dumpContent(self):
        rootnode = ElementTree.fromstring(content_base_xml)
        rootnode.extend(self.datanode)
        zipdata = io.BytesIO()
        with zipfile.ZipFile(zipdata, 'w') as zipout:
            fileorder = ['Persistence.xml'] + list(self.files())
            for fn in fileorder:
                if fn == 'Persistence.xml':
                    data = ElementTree.tostring(rootnode, encoding= 'utf-8')
                else:
                    data = self.project.readSubfile(fn)
                zipout.writestr(fn, data)
        return zipdata.getvalue()


class DocumentObject(PropertyContainer):
    @property
    def ViewObject(self):
        return self.project.getViewProvider(self.Name)
        
    def updateFCObject(self, object):
        object.restoreContent(self.dumpContent())
        if object.ViewObject:
            object.ViewObject.restoreContent(self.ViewObject.dumpContent())

class ViewProvider(PropertyContainer):
    @property
    def Object(self):
        return self.project.getObject(self.Name)

