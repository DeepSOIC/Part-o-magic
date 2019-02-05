print("loading FCProject.py")
import zipfile
from xml.etree import ElementTree
import io

empty_project_document_xml = (
"""<?xml version='1.0' encoding='utf-8'?>
<!--
 FreeCAD Document, see http://www.freecadweb.org for more information...
-->
<Document SchemaVersion="4" ProgramVersion="{version}" FileVersion="1">
    <Properties Count="0">
    </Properties>
    <Objects Count="0">
    </Objects>
    <ObjectData Count="0">
    </ObjectData>
</Document>
""")

empty_project_guidocument_xml = (
"""<?xml version='1.0' encoding='utf-8'?>
<!--
 FreeCAD Document, see http://www.freecadweb.org for more information...
-->
<Document SchemaVersion="1">
    <ViewProviderData Count="0">
    </ViewProviderData>
    <Camera settings=""/>
</Document>
""")

object_list_entry = (
'''<Object type="{typeid}" name="{name}" />'''
)

object_data_entry = (
'''<Object name="{name}">
</Object>
'''
)

object_vp_entry = (
'''<ViewProvider name="{name}">
</ViewProvider>
'''
)

content_base_xml = (
"""<Content>
</Content>
"""
)

def FC_version():
    try:
        import FreeCAD
        vertup = FreeCAD.Version()
        # ['0', '18', '15518 (Git)', 'git://github.com/FreeCAD/FreeCAD.git master', '2018/12/29 16:41:25', 'master', 'e83c44200ab428b753a1e08a2e4d95
        # target format: '0.18R14726 (Git)'
        return '{0}.{1}R{2}'.format(*vertup)
    except Exception:
        return '0.18R14726 (Git)'
        
def generateNewName(wanted_name, existing_names):
    """generateNewName(wanted_name, existing_names): returns a unique name (by adding digits to wanted_name). Suitable for file names (but not full paths)"""
    title, ext = wanted_name.rsplit('.',1) + ['']
    if ext:
        ext = '.' + ext
    i = 0
    f2 = f
    while f2 in existing_names:
        i += 1
        f2 = title + str(i) + ext
    return f2

class FCProject(object):
    document_xml = None #ElementTree object of parsed Document.xml 
    guidocument_xml = None #ElementTree object of parsed GuiDocument.xml
    zip = None #zip file object, for a project opened from a FCStd file
    filename = None #(str) file name associated with this project
    files = None #dict filename -> bytestream, contains all files
    _app_filelist = None
    _gui_filelist = None
        
    def __init__(self, filename = None):
        if filename is not None:
            self.readFile(filename)
        else:
            self.empty()
    
    def empty(self, init_xml = True):
        """empty(init_xml = True): initializes an empty project. Discards all data. Initializes XMLs for adding objects, if init_xml is true."""
        if init_xml:
            self.document_xml = ElementTree.ElementTree(
              element= ElementTree.fromstring(
                empty_project_document_xml.format(version= FC_version())
              )
            )
            self.guidocument_xml = ElementTree.ElementTree(
              element= ElementTree.fromstring(
                empty_project_guidocument_xml
              )
            )
        self.zip = None #zip file object, for a project opened from a FCStd file
        self.filename = None #(str) file name associated with this project
        self.files = {} 
        self._app_filelist = []
        self._gui_filelist = []
        
        
    def readFile(self,filename):
        zip = zipfile.ZipFile(filename)
        self.empty(init_xml = False)

        self.filename = filename
        self.zip = zip
        
        filelist = self.zip.namelist()
        self.document_xml = ElementTree.parse(self.zip.open('Document.xml'))
        if 'GuiDocument.xml' in filelist:
            self.guidocument_xml = ElementTree.parse(self.zip.open('GuiDocument.xml'))
        curlist = self._app_filelist
        for fn in filelist:
            if fn == 'Document.xml':
                pass
            elif fn == 'GuiDocument.xml':
                curlist = self._gui_filelist
            else:
                curlist.append(fn)
                
    def fromStream(self, name, typeid, bs_app, bs_vp = None):
        self.empty()

        def fetchFiles(z, filelist_ref):           
            for fn in z.namelist():
                if fn == 'Persistence.xml':
                    pass
                else:
                    filelist_ref.append(fn)
                    data = z.open(fn).read()
                    self.files[fn] = data
        
        objdatanode = ElementTree.fromstring(object_data_entry.format(name= name))
        
        zip_app = zipfile.ZipFile(io.BytesIO(bs_app))
        global bs_et #debug
        global bs_et_data #debug
        bs_et = ElementTree.parse(zip_app.open('Persistence.xml'))
        bs_et_data = bs_et.getroot()
        objdatanode.extend(bs_et_data)
        if bs_et_data.find('Extensions') is not None:
            objdatanode.set('Extensions', 'True')
        fetchFiles(zip_app, self._app_filelist)        

        if bs_vp:
            objvpnode = ElementTree.fromstring(object_vp_entry.format(name= name))
        
            zip_gui = zipfile.ZipFile(io.BytesIO(bs_vp))
            bs_et = ElementTree.parse(zip_gui.open('Persistence.xml'))
            bs_et_data = bs_et.getroot()
            objvpnode.extend(bs_et_data)
            if bs_et_data.find('Extensions') is not None:
                objvpnode.set('Extensions', 'True')
            fetchFiles(zip_gui, self._gui_filelist)
        else:
            self.guidocument_xml = None
            
        self.node_objectlist.append(ElementTree.fromstring(object_list_entry.format(name= name, typeid= typeid)))
        self.node_objectdata.append(objdatanode)
        if bs_vp:
            self.node_vpdata.append(objvpnode)
        self._updateLengths()
        
    def fromObject(self, obj):
        bs_app = obj.dumpContent()
        if obj.ViewObject is not None:
            bs_vp = obj.ViewObject.dumpContent()
        self.fromStream(obj.Name, obj.TypeId, bs_app, bs_vp)
    
    def _updateLengths(self):
        n_objects = len(self.node_objectlist)
        self.node_objectdata.set('Count', str(n_objects))
        self.node_objectlist.set('Count', str(n_objects))
        if self.guidocument_xml is not None:
            self.node_vpdata.set('Count', str(n_objects))
    
    def _fetchInternalFiles(self):
        """reads out all files from the zip and stores contents in cache dict. If the project was created from scratch, does nothing."""
        if not self.zip: 
            return
        z = self.zip
        filelist = z.namelist()
        for filename in filelist:
            data = z.open(filename).read()
            self.files[filename] = data
    
    def writeFile(self, filename):
        """writeFile(filename): writes out an FCStd file"""
        with zipfile.ZipFile(filename, 'w') as zipout:
            fileorder = ['Document.xml'] + self._app_filelist
            if self.guidocument_xml is not None:
                fileorder += ['GuiDocument.xml'] + self._gui_filelist
                
            for subfn in fileorder:
                zipout.writestr(subfn, self.readSubfile(subfn))
    
    def readSubfile(self, subfn):
        """readSubfile(subfn): returns/generates data of file in a project. Returns a bytestring."""
        if subfn == 'Document.xml':
            return ElementTree.tostring(self.document_xml.getroot(), encoding= 'utf-8')
        elif subfn == 'GuiDocument.xml':
            return ElementTree.tostring(self.guidocument_xml.getroot(), encoding= 'utf-8')
        elif subfn in self.files:
            return self.files[subfn]
        elif self.zip is not None:
            return self.zip.read(subfn)
        else:
            raise FileNotFoundError('{id} has no file named {fn} in it'.format(name= repr(self)))

        
    @property
    def node_objectlist(self):
        return self.document_xml.find('Objects')
    
    @property
    def node_objectdata(self):
        return self.document_xml.find('ObjectData')
    
    @property
    def node_vpdata(self):
        if not self.guidocument_xml:
            return None
        return self.guidocument_xml.find('ViewProviderData')

    @property
    def Name(self):
        if self.document_xml is not None:
            return self.document_xml.find('Properties/Property[@name="Label"]/String').get('value')
        else:
            return None
    
    @property
    def program_version(self):
        program_version_string = self.program_version_string
        
        # parse version string, which typically looks like this: "0.17R8361 (Git)"
        import re
        match = re.match(r"(\d+)\.(\d+)\R(\d+).+",program_version_string)
        major,minor,rev = match.groups()
        major = int(major); minor = int(minor); rev = int(rev)
        return (major,minor,rev)
    
    @property
    def program_version_string(self):
        return self.document_xml.getroot().get('ProgramVersion')
        
    def set_program_version(self, version_tuple, imprint_old = False):
        major,minor,rev = version_tuple
        self.set_program_version_string('{major}.{minor}R{rev} (Git)'.format(**vars()), imprint_old)
        
    def set_program_version_string(self, version_string, imprint_old = False):
        if imprint_old:
            if self.document_xml.getroot().get('ConvertedFromVersion') is None: #make sure to not overwrite...
                self.document_xml.getroot().set('ConvertedFromVersion', self.program_version_string)
        self.document_xml.getroot().set('ProgramVersion', version_string)
    
    def listObjects(self):
        "listObjects(): returns list of object names"
        return [obj.get('name') for obj in self.node_objectlist]
    
    def listObjectsOfType(self, type_id):
        "getObjectsOfType(type_id): returns list of object names with type equal to type_id (string). Note that exact comparison is done, isDerivedFrom is not supported"
        objectnodes = self.node_objectlist.findall('*[@type="{type}"]'.format(type= type_id))
        return [obj.get('name') for obj in objectnodes]
    
    def findObjects(self, type_id):
        'findObjects(type_id): returns list of App objects by C++ type'
        return [self.getObject(obj_name) for obj_name in self.listObjectsOfType(type_id)]
    
    def getObject(self, object_name):
        object_node = self.node_objectlist.find('Object[@name="{name}"]'.format(name= object_name))
        if object_node is None:
            raise KeyError("There is no object named {name} in this project".format(name= object_name))
        data_node = self.node_objectdata.find('Object[@name="{name}"]'.format(name= object_name))
        assert(data_node is not None)
        return DocumentObject(object_name, object_node, data_node, self)

    def getViewProvider(self, object_name):
        object_node = self.node_objectlist.find('Object[@name="{name}"]'.format(name= object_name))
        if object_node is None:
            raise KeyError("There is no object named {name} in this project".format(name= object_name))
        if self.guidocument_xml is None: return None
        data_node = self.node_vpdata.find('ViewProvider[@name="{name}"]'.format(name= object_name))
        if data_node is None:
            warn("Failed to find viewprovider for object {obj}".format(obj= object_name))
            return None
        return ViewProvider(object_name, None, data_node, self)
    
    @property
    def Objects(self):
        # this is probably somewhat inefficient, but we'll stick with it for a while
        return [self.getObject(object_name) for object_name in self.listObjects()]
    
    def loadObjectsToFC(self, doc, namelist):
        emu_objs = [self.getObject(name) for name in namelist]
        target_objs = [doc.addObject(emu_obj.TypeId, emu_obj.Name) for emu_obj in emu_objs]
        for i in range(len(namelist)):
            if emu_objs[i].Name != target_objs[i].Name:
                raise NameCollisionError("name {name} already taken".format(name= emu_objs[i].Name))
        for i in range(len(namelist)):
            emu_objs[i].updateFCObject(target_objs[i])


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

def load(project_filename):
    "load(project_filename): reads an FCStd file and returns FCProject object"
    project = FCProject(project_filename)
    return project

def warn(message):
    import sys
    freecad = sys.modules.get('FreeCAD', None)
    if freecad is None:
        print(message)
    else:
        freecad.Console.PrintWarning(message + '\n')

class FileplantError(RuntimeError):
    pass
class NameCollisionError(FileplantError):
    pass
