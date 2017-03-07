import FreeCAD as App
if App.GuiUp:
    import FreeCADGui as Gui
import Part

__title__="Exporter feature"
__author__ = "DeepSOIC"
__url__ = ""

print("loading Exporter")
    
def makeExporter(name):
    '''makeExporter(name): makes a Exporter object.'''
    obj = App.ActiveDocument.addObject("App::FeaturePython",name)
    proxy = Exporter(obj)
    vp_proxy = ViewProviderExporter(obj.ViewObject)
    return obj

class Exporter:
    "Exporter feature python proxy object"
    def __init__(self,obj):
        self.Type = 'Exporter'
        obj.addProperty('App::PropertyLink','ObjectToExport',"Exporter","Object to use to form the feature")
        obj.addProperty('App::PropertyString', 'FilePath', "Exporter", "Relative or absolute path to file to write. Hint: type '%Label%.step'.")
        obj.addProperty('App::PropertyString', 'FullActualPath', "Exporter", "Path to the last file that was written")        
        obj.setEditorMode('FullActualPath', 1)#read-only
        
        obj.addProperty('App::PropertyEnumeration', 'ExportingFrequency', "Exporter", "Set when to export the file. (double-click always works)")
        obj.ExportingFrequency = ['On double-click only', 'Export once', 'Every recompute'] 
        obj.ExportingFrequency = 'Every recompute'
        
        obj.addProperty('App::PropertyEnumeration', 'ContainerMode', "Exporter", "Sets what to export if exporting a container" )
        obj.ContainerMode = ['Feed straight to exporter', 'Feed tip features to exporter','Feed all children', '(Auto)']
        obj.ContainerMode = '(Auto)'
        
        obj.addProperty('App::PropertyEnumeration', 'MultiMode', "Exporter", "Sets how to deal with multitude of objects, when exporting containers")
        obj.MultiMode = ['Write one file', 'Write many files']
        
        obj.Proxy = self
        

    def execute(self,selfobj):
        if selfobj.ExportingFrequency == 'On double-click only': return
        
        self.export(selfobj)
        
        if selfobj.ExportingFrequency == 'Export once':
            selfobj.ExportingFrequency == 'On double-click only'

    def export(self, selfobj):
        #check the model
        from PartOMagic.Base import Containers
        for obj in Containers.getAllDependencies(selfobj):
            if 'Invalid' in obj.State:
                raise RuntimeError("File not exported, because {feat} is in error state.".format(feat= obj.Label))
    
        #form absolute path
        filepath = selfobj.FilePath
        
        from os import path
        extension = path.splitext(filepath)[1][1:]
        if len(extension)<1:
            raise ValueError("File has no extension, can't determine export type.")

        import importlib
        mod = importlib.import_module(App.getExportType(extension)[0])
        
        if not path.isabs(filepath):
            if len(selfobj.Document.FileName)==0:
                raise ValueError("Can't save to a relative path, because the project is not saved to a file.")
            context = path.dirname(selfobj.Document.FileName)
            filepath = path.join(context, filepath)
        
        #collect what to export
        objects_to_export = []
        containermode = selfobj.ContainerMode
        if hasattr(selfobj.ObjectToExport, "Group"):
            if containermode == '(Auto)':
                if hasattr(selfobj.ObjectToExport, 'Shape'):
                    containermode = 'Feed straight to exporter' 
                elif hasattr(selfobj.ObjectToExport, 'Tip'):
                    containermode = 'Feed tip features to exporter'
                else:
                    containermode = 'Feed all children'
                selfobj.ContainerMode = containermode
            if containermode == 'Feed straight to exporter':
                objects_to_export.append(selfobj.ObjectToExport)
            elif containermode == 'Feed tip features to exporter':
                objects_to_export += selfobj.ObjectToExport.Tip if type(selfobj.ObjectToExport.Tip) is list else [selfobj.ObjectToExport.Tip]
            elif containermode == 'Feed all children':
                objects_to_export += selfobj.ObjectToExport.Group
            else: 
                raise NotImplementedError("Unexpected contaner mode {mode}".format(mode= repr(containermode)))
        else:
            objects_to_export.append(selfobj.ObjectToExport)
        
        if selfobj.MultiMode == 'Write one file':
            filepath = filepath.replace('%Label%', selfobj.ObjectToExport.Label)
            mod.export(objects_to_export, filepath)
            print("Exported {file}".format(file= filepath))
            selfobj.FullActualPath = filepath
        elif selfobj.MultiMode == 'Write many files':
            if not '%Label%' in filepath:
                raise ValueError("In multi-file export, you must include %Label% into the file name.")
            for obj in objects_to_export:
                thisfilepath = filepath.replace('%Label%', obj.Label)
                mod.export([obj], thisfilepath)
                print("Exported {file}".format(file= thisfilepath))
            selfobj.FullActualPath = thisfilepath
        else:
            raise NotImplementedError("Unexpected MultiMode: {mode}".format(mode= repr(selfobj.MultiMode)))
        
        
 

class ViewProviderExporter:
    "A View Provider for the Exporter object"

    def __init__(self,vobj):
        vobj.Proxy = self
        
    def getIcon(self):
        from PartOMagic.Gui.Utils import getIconPath
        return getIconPath('Part_Export.svg')

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
    
    def doubleClicked(self, vobj):
        try:
            self.Object.Proxy.export(self.Object)
            self.Object.purgeTouched()
        except Exception as err:
            from PartOMagic.Gui.Utils import msgError
            msgError(err)
      
    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None

def CreateExporter(name):
    App.ActiveDocument.openTransaction("Create Exporter")
    Gui.addModule('PartOMagic.Features.Exporter')
    Gui.doCommand('sel = Gui.Selection.getSelection()[0]')
    Gui.doCommand('f = PartOMagic.Features.Exporter.makeExporter(name = {name})'.format(name= repr(name)))
    Gui.doCommand('f.Label = "Export {obj}".format(obj= sel.Label)')
    Gui.doCommand('f.ObjectToExport = sel')
    Gui.doCommand('Gui.Selection.clearSelection()')
    Gui.doCommand('Gui.Selection.addSelection(f)')
    App.ActiveDocument.commitTransaction()


# -------------------------- /common stuff --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------

class CommandExporter:
    "Command to create Exporter feature"
    def GetResources(self):
        from PartOMagic.Gui.Utils import getIconPath
        return {'Pixmap'  : getIconPath('Part_Export.svg'),
                'MenuText': "Create Export feature",
                'Accel': '',
                'ToolTip': "Create Export feature. It can export a given object to a file whenever it changes, or on demand."}
        
    def Activated(self):
        CreateExporter('Exporter')
            
    def IsActive(self):
        return len(Gui.Selection.getSelection()) == 1

if App.GuiUp:
    Gui.addCommand('PartOMagic_Exporter',  CommandExporter())
# -------------------------- /Gui command --------------------------------------------------

def exportedCommands():
    return ['PartOMagic_Exporter']
