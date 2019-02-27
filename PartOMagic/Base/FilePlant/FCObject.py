print("loading FCObject.py")
import zipfile
from xml.etree import ElementTree
import io

from .Errors import *
from . import FCProperty

content_base_xml = (
"""<Content>
</Content>
"""
)


#objectnode:
#<Object type="PartDesign::Body" name="Body001" />

#datanode:
#<Object name="Body001" Extensions="True">
#    <Extensions Count="1">
#        <Extension type="App::OriginGroupExtension" name="OriginGroupExtension">
#        </Extension>
#    </Extensions>
#    <Properties Count="8">
#        <Property name="BaseFeature" type="App::PropertyLink">
#            <Link value=""/>
#        </Property>

class PropertyContainer(object):
    """Either a DocumentObject or ViewProvider"""
    datanode = None
    objectnode = None
    project = None # reference to a project this object is part of
    
    def __init__(self, objectnode, datanode, project):
        self.objectnode = objectnode
        self.datanode = datanode
        self.project = project
    
    @property
    def Name(self):
        """Name: a writable property. Writing to Name will rename the object and its viewprovider, but not update links to the object. To rename and update links, use renameObject method of a Project."""
        return self.datanode.get('name')
    
    def _rename(self, new_name):
        if self.objectnode is not None:
            self.objectnode.set('name', new_name)
        self.datanode.set('name', new_name)
            
    def getPropertyNode(self, prop_name):
        prop = self.datanode.find('Properties/Property[@name="{propname}"]'.format(propname= prop_name))
        if prop is None:
            raise AttributeError("Object {obj} has no property named '{prop}'".format(obj= self.Name, prop= prop_name))
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
    
    def Property(self, prop_name):
        return FCProperty.CastProperty(self.getPropertyNode(prop_name), self)
    
    @property
    def Properties(self):
        #fixme: inefficient!
        return [self.Property(prop_name) for prop_name in self.PropertiesList]
    
    def files(self):
        """files(): returns set of filenames used by properties of this object"""
        file_set = set()
        for prop in self.Properties:
            file_set |= prop.files()
        return file_set
    
    def _rename_file(self, rename_dict):
        """substitutes file references in properties. does not rename actual files. Returns number of occurences replaced."""
        n_renamed = 0
        for prop in self.Properties:
            n_renamed += prop._rename_file(rename_dict)
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
        
    @property
    def Label(self):
        return self.Property('Label').value
    
    @Label.setter
    def Label(self, new_value):
        self.Property('Label').value = new_value
    
    def fetchAttributes(self):
        """fetchAttributes(self): makes object properties accessible as attributes. """
        pass
        #doesn't work - descriptors are only applied when the attribute is a class attribute =(
        #for prop_name in self.PropertiesList:
        #    if prop_name != 'Label': #Label is defined explicitly
        #        self.__dict__[prop_name] = PropertyAsAttribute(prop_name, self) #use instance dictionary instead of setattr, using setattr over a descriptor will do a different thing.
    
    def replace(self, replace_task):
        cnt = 0
        for prop in self.Properties:
            cnt += prop.replace(replace_task)
        return cnt

    def purgeDeadLinks(self):
        cnt = 0
        for prop in self.Properties:
            cnt += prop.purgeDeadLinks()
        return cnt
        

#class PropertyAsAttribute(object):
#    prop_name = None
#    object = None
#    def __init__(self, prop_name, obj):
#        self.prop_name = prop_name 
#        self.object = obj
#    
#    def __get__(self, obj, type = None):
#        return self.object.Property(self.prop_name).getAsAttribute()

class DocumentObject(PropertyContainer):
    @property
    def ViewObject(self):
        return self.project.getViewProvider(self.Name)
    
    @property
    def Name(self):
        return super(DocumentObject, self).Name

    @Name.setter
    def Name(self, new_name):
        vp = self.ViewObject
        self._rename(new_name)
        if vp:
            vp._rename(new_name)

    def rename(self, new_name, update_label = True):
        old_name = self.Name
        self.Name = new_name
        if update_label:
            self.Label = self.Label.replace(old_name, new_name)
        
    def updateFCObject(self, obj):
        obj.restoreContent(self.dumpContent())
        if obj.ViewObject:
            obj.ViewObject.restoreContent(self.ViewObject.dumpContent())

class ViewProvider(PropertyContainer):
    @property
    def Object(self):
        return self.project.getObject(self.Name)

