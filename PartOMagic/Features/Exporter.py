import FreeCAD as App
if App.GuiUp:
    import FreeCADGui as Gui
import Part

__title__="Exporter feature"
__author__ = "DeepSOIC"
__url__ = ""

print("loading Exporter")

from PartOMagic.Base.Utils import addProperty
    
def makeExporter(name):
    '''makeExporter(name): makes a Exporter object.'''
    obj = App.ActiveDocument.addObject("App::FeaturePython",name)
    proxy = Exporter(obj)
    vp_proxy = ViewProviderExporter(obj.ViewObject)
    return obj

def log(message):
    App.Console.PrintLog(message+'\n')

class Exporter:
    "Exporter feature python proxy object"
    def __init__(self,obj):
        self.Type = 'Exporter'
        self.initProperties(obj)
        obj.Proxy = self
        
    def initProperties(self, selfobj):
        addProperty(selfobj, 'App::PropertyLink','ObjectToExport',"Exporter","Object to use to form the feature")
        addProperty(selfobj, 'App::PropertyString', 'FilePath', "Exporter", "Relative or absolute path to file to write. Hint: type '%Label%.step'.")
        addProperty(selfobj, 'App::PropertyString', 'FullActualPath', "Exporter", "Path to the last file that was written", readonly= True)        
        
        if addProperty(
            selfobj, 'App::PropertyEnumeration', 'ExportingFrequency', "Exporter", "Set when to export the file. (double-click always works)",
            ['On double-click only', 'Export once','When project is saved', 'Every recompute'] 
        ):
            selfobj.ExportingFrequency = 'When project is saved'
        
        if addProperty(
            selfobj, 'App::PropertyEnumeration', 'ContainerMode', "Exporter", "Sets what to export if exporting a container",
            ['Feed straight to exporter', 'Feed tip features to exporter','Feed all children', '(Auto)']
        ):
            selfobj.ContainerMode = '(Auto)'
        
        addProperty(selfobj, 'App::PropertyEnumeration', 'MultiMode', "Exporter", "Sets how to deal with multitude of objects, when exporting containers",
            ['Write one file', 'Write many files']
        )
        
        addProperty(selfobj, 'App::PropertyLength', 'MeshAccuracy', "Meshing", 
            "Sets the accuracy of mesh export. The exported mesh should deviate from perfect shape by no more than specified value. If zero, visualization mesh is used."
        )
        

    def execute(self,selfobj):
        self.initProperties(selfobj) #to make sure MeshAccuracy is added to old objects
        
        if selfobj.ExportingFrequency == 'On double-click only' or selfobj.ExportingFrequency == 'When project is saved': return
        
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
        
        if selfobj.MeshAccuracy > 1e-7:
            for obj in objects_to_export:
                if hasattr(obj, 'Shape'):
                    obj.Shape.tessellate(selfobj.MeshAccuracy)
                else:
                    App.Console.PrintWarning("Exporter {exporter}: object to export ({object}) has no b-rep shape. Can't re-tessellate."
                                              .format(exporter= selfobj.Name, object= obj.Label))
        
        vardict = {
            'project_name'               : selfobj.Document.Name,
            'project_filetitle'          : path.splitext(path.basename(selfobj.Document.FileName))[0],
            'project_filename'           : path.basename(selfobj.Document.FileName),
            'project_folder'             : path.split(path.split(selfobj.Document.FileName)[0])[1],
            'project_label'              : selfobj.Document.Label,
            'exporter_label'             : selfobj.Label,
            'exporter_name'              : selfobj.Name,
            'exporter_container_label'   : Containers.getContainer(selfobj).Label,
            'exporter_container_name'    : Containers.getContainer(selfobj).Name,
        }
        
        def addObjectVars(obj):
            vardict['object_name'             ] = obj.Name
            vardict['object_label'            ] = obj.Label
            vardict['object_container_label'  ] = Containers.getContainer(obj).Label
            vardict['object_container_name'   ] = Containers.getContainer(obj).Name
        
        try:
            if selfobj.MultiMode == 'Write one file':
                addObjectVars(selfobj.ObjectToExport)
                filepath = filepath.replace('%Label%', selfobj.ObjectToExport.Label).format(**vardict)
                mod.export(objects_to_export, filepath)
                print("Exported {file}".format(file= filepath))
                if selfobj.FullActualPath != filepath: #check, to avoid touching all exporters upon every file save
                    selfobj.FullActualPath = filepath
            elif selfobj.MultiMode == 'Write many files':
                files_written = set()
                for obj in objects_to_export:
                    addObjectVars(obj)
                    thisfilepath = filepath.replace('%Label%', obj.Label).format(**vardict)
                    if thisfilepath in files_written:
                        raise ValueError('Exporter {exporter} is supposed to write multiple files, but the filenames repeat: {fn}. Please make sure a variable is used in the file name, such as {{object_name}}, or {{object_label}}.'
                            .format(exporter= selfobj.Label, fn= thisfilepath))
                    mod.export([obj], thisfilepath)
                    print("Exported {file}".format(file= thisfilepath))
                if selfobj.FullActualPath != thisfilepath: #check, to avoid touching all exporters upon every file save
                    selfobj.FullActualPath = thisfilepath
            else:
                raise NotImplementedError("Unexpected MultiMode: {mode}".format(mode= repr(selfobj.MultiMode)))
        except KeyError as ke:
            key = ke.args[0]
            message = ('Variable name not recognized: {key}.\n\nVariables available:\n{varlist}'
                .format(
                    key= key,
                    varlist = '\n'.join(['{' + var + '}' + ': ' + vardict[var] for var in vardict])
                )
            )
            raise KeyError(message)
    
    def onDocumentSaved_POM(self, selfobj):
        if selfobj.ExportingFrequency != 'When project is saved': return
        log("Exporter {exporter} is saving a file...".format(exporter= selfobj.Label))
        self.export(selfobj)
        
class Observer(object):
    _timer = None
    lastMD = None #dict. Key = project name, value = whatever is returned by App.ActiveDocument.LastModifiedDate
    
    def start(self):
        self.stop()
        self.lastMD = {}
        from PySide import QtCore
        timer = QtCore.QTimer()
        self._timer = timer
        timer.setInterval(500)
        timer.connect(QtCore.SIGNAL("timeout()"), self.poll)
        timer.start()
        
    def stop(self):
        if self._timer != None:
            self._timer.stop()
            self._timer = None
            
    def is_running(self):
        return self._timer is not None
    
    def poll(self):
        # detect document saves
        if App.ActiveDocument is None: return
        cur_lmd = App.ActiveDocument.LastModifiedDate
        if cur_lmd == 'Unknown': cur_lmd = None
        last_lmd = self.lastMD.get(App.ActiveDocument.Name, None)
        if cur_lmd != last_lmd:
            # LastModifiedDate has changed - document was just saved!
            # print('mod date for doc {doc} changed from {last_lmd} to {cur_lmd}'.format(doc= App.ActiveDocument.Name, last_lmd= repr(last_lmd), cur_lmd= repr(cur_lmd)))
            self.lastMD[App.ActiveDocument.Name] = cur_lmd
            if last_lmd is not None: #filter out the apparent change that happens when there was no last-seen value
                self.slotSavedDocument(App.ActiveDocument)
    def slotSavedDocument(self, doc):
        errs = []
        log("Project was just saved: {doc}. Scanning for exporter objects...".format(doc= doc.Name))
        for obj in doc.Objects:
            if hasattr(obj, 'Proxy'):
                if hasattr(obj.Proxy, 'onDocumentSaved_POM'):
                    try:
                        obj.Proxy.onDocumentSaved_POM(obj)
                    except Exception as err:
                        App.Console.PrintError("Exporting '{exporter}' failed: {err}.\n"
                            .format(exporter= obj.Label, err= str(err)))
                        errs.append((obj, err))
        if errs:
            if App.GuiUp:
                from PartOMagic.Gui import Utils
                if len(errs) == 1:
                    obj, err = errs[0]
                    Utils.msgError(err, "Exporter '{exporter}' failed to save file: {{err}}".format(exporter= obj.Label))
                else:
                    Utils.msgError(RuntimeError('{n} exporters failed to save files. See Report view for more information.'.format(n= len(errs))))


#stop old observer, if reloading this module
if 'activeObserver' in vars():
    activeObserver.stop()
    activeObserver = None
#start obsrever
activeObserver = Observer()
activeObserver.start()

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
        self.exportNow()
    
    def exportNow(self):
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
        
    def setupContextMenu(self,vobj,menu):
        from PySide import QtCore,QtGui
        action1 = QtGui.QAction(QtGui.QIcon(":/icons/Part_Export.svg"),"Export now!",menu)
        QtCore.QObject.connect(action1,QtCore.SIGNAL("triggered()"), self.exportNow)
        menu.addAction(action1)


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

from PartOMagic.Gui.AACommand import AACommand, CommandError
commands = []

class CommandExporter(AACommand):
    "Command to create Exporter feature"
    def GetResources(self):
        return {'CommandName': 'PartOMagic_Exporter',
                'Pixmap'  : self.getIconPath('Part_Export.svg'),
                'MenuText': "Create Export feature",
                'Accel': '',
                'ToolTip': "Create Export feature. It can export a given object to a file whenever it changes, or on demand."}
        
    def RunOrTest(self, b_run):
        if len(Gui.Selection.getSelection()) == 1:
            if b_run: CreateExporter('Exporter')
        else:
            raise CommandError(self, "Creates an exporter feature, which will automatically export an object whenever it changes.\n\nPlease select an object, then invoke this command.")
commands.append(CommandExporter())
# -------------------------- /Gui command --------------------------------------------------

exportedCommands = AACommand.registerCommands(commands)