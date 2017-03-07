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
        obj.addProperty('App::PropertyString', 'FilePath', "Exporter", "Relative or absolute path to file to write")
        obj.addProperty('App::PropertyEnumeration', 'ExportingFrequency', "Exporter", "Set when to export the file.")
        obj.ExportingFrequency = ['Disabled', 'Export once', 'Every recompute'] 
        obj.ExportingFrequency = 'Every recompute'
        
        obj.Proxy = self
        

    def execute(self,selfobj):
        if selfobj.ExportingFrequency == 'Disabled': return
        
        self.export(selfobj)
        
        if selfobj.ExportingFrequency == 'Export once':
            selfobj.ExportingFrequency == 'Disabled'

    def export(self, selfobj):
        from PartOMagic.Base import Containers
        for obj in Containers.getAllDependencies(selfobj):
            if 'Invalid' in obj.State:
                raise RuntimeError("File not exported, because {feat} is in error state.".format(feat= obj.Label))
    
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
        
        mod.export([selfobj.ObjectToExport], filepath)
        print("Exported {file}".format(file= filepath))
 

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
