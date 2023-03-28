import FreeCAD as App
if App.GuiUp:
    import FreeCADGui as Gui
import Part

__title__="PDShapeFeature container"
__author__ = "DeepSOIC"
__url__ = ""


from PartOMagic.Base.Utils import transformCopy, shallowCopy
from PartOMagic.Base.Utils import PlacementsFuzzyCompare

def makePDShapeFeature(name, body):
    '''makePDShapeFeature(name): makes a PDShapeFeature object.'''
    obj = body.newObject('PartDesign::FeaturePython',name)
    proxy = PDShapeFeature(obj)
    vp_proxy = ViewProviderPDShapeFeature(obj.ViewObject)
    return obj

class PDShapeFeature:
    "The PDShapeFeature object"
    def __init__(self,obj):
        self.Type = 'PDShapeFeature'
        obj.addExtension('App::OriginGroupExtensionPython')
        
        try:
            obj.addProperty('App::PropertyLinkChild','Tip',"PartDesign","Object to use to form the feature")
        except Exception:
            #for older FC
            obj.addProperty('App::PropertyLink','Tip',"PartDesign","Object to use to form the feature")
        
        obj.addProperty('App::PropertyEnumeration', 'AddSubType', "PartDesign", "Feature kind")
        obj.addProperty('Part::PropertyPartShape', 'AddSubShape', "PartDesign", "Shape that forms the feature") #TODO: expose PartDesign::AddSub, and use it, instead of mimicking it
        obj.AddSubType = ['Additive', 'Subtractive']
        
        obj.setEditorMode('Placement', 0) #non-readonly non-hidden
        
        obj.Proxy = self
        

    def execute(self,selfobj):
        import Part
        selfobj.AddSubShape = shallowCopy(selfobj.Tip.Shape, selfobj.Placement)
        base_feature = selfobj.BaseFeature
        result_shape = None
        if selfobj.AddSubType == 'Additive':
            if base_feature is None:
                result_shape = selfobj.AddSubShape.Solids[0]
            else:
                result_shape = base_feature.Shape.fuse(selfobj.AddSubShape).Solids[0]
        elif selfobj.AddSubType == 'Subtractive':
            result_shape = base_feature.Shape.cut(selfobj.AddSubShape).Solids[0]
        else:
            raise ValueError("AddSub Type not implemented: {t}".format(t= selfobj.AddSubType))
        if not PlacementsFuzzyCompare(selfobj.Placement, result_shape.Placement):
            result_shape = transformCopy(result_shape, selfobj.Placement.inverse()) #the goal is that Placement of selfobj doesn't move the result shape, only the shape being fused up
        selfobj.Shape = result_shape
            
    def advanceTip(self, selfobj, new_object):
        from PartOMagic.Gui.Utils import screen
        old_tip = screen(selfobj.Tip)
        new_tip = old_tip
        if old_tip is None:
            new_tip = new_object
        if old_tip in new_object.OutList:
            new_tip = new_object
        
        if new_tip is None: return
        if new_tip is old_tip: return
        if new_tip.Name.startswith('Clone'): return
        if new_tip.Name.startswith('ShapeBinder'): return
        selfobj.Tip = new_tip

    def onDocumentRestored(self, selfobj):
        import PartOMagic.Base.Compatibility as compat
        if compat.scoped_links_are_supported():
            #check that Tip is scoped properly. Recreate the property if not.
            if not 'Child' in selfobj.getTypeIdOfProperty('Tip'):
                v = selfobj.Tip
                t = selfobj.getTypeIdOfProperty('Tip')
                g = selfobj.getGroupOfProperty('Tip')
                d = selfobj.getDocumentationOfProperty('Tip')
                selfobj.removeProperty('Tip')
                selfobj.addProperty(t+'Child','Tip', g, d)
                selfobj.Tip = v
        
class ViewProviderPDShapeFeature:
    "A View Provider for the PDShapeFeature object"

    def __init__(self,vobj):
        vobj.addExtension('Gui::ViewProviderGeoFeatureGroupExtensionPython')
        vobj.Proxy = self
        
    def getIcon(self):
        from PartOMagic.Gui.Utils import getIconPath
        return getIconPath('PartOMagic_PDShapeFeature_{Additive}.svg'.format(Additive= self.Object.AddSubType) )

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
    
    def doubleClicked(self, vobj):
        from PartOMagic.Gui.Observer import activeContainer, setActiveContainer
        ac = activeContainer()
        if ac is vobj.Object:
            setActiveContainer(vobj.Object.Document) #deactivate self
        else:
            setActiveContainer(vobj.Object) #activate self
            Gui.Selection.clearSelection()
        return True
    
    def doDisplayModeAutomation(self, vobj, old_active_container, new_active_container, event):
        # event: -1 = leaving (active container was self or another container inside, new container is outside)
        #        +1 = entering (active container was outside, new active container is inside)
        if event == +1:
            self.oldMode = vobj.DisplayMode
            vobj.DisplayMode = 'Group'
        elif event == -1:
            if self.oldMode == 'Group':
                self.oldMode = 'Flat Lines'
            vobj.DisplayMode = self.oldMode
  
    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None
        
    def onDelete(self, viewprovider, subelements): # subelements is a tuple of strings
        try:
            selfobj = self.Object
            import PartOMagic.Base.Containers as Containers
            body = Containers.getContainer(selfobj)
            if not body.isDerivedFrom('PartDesign::Body'): return
            
            if self.ViewObject.Visibility and selfobj.BaseFeature:
                selfobj.BaseFeature.ViewObject.show()
                
            body.removeObject(selfobj)
            
        except Exception as err:
            App.Console.PrintError("Error in onDelete: " + err.message)
        return True


def CreatePDShapeFeature(name, add_sub_type= 'Additive'):
    App.ActiveDocument.openTransaction("Create PDShapeFeature")
    Gui.addModule('PartOMagic.Features.PDShapeFeature')
    Gui.doCommand('body = PartOMagic.Base.Containers.activeContainer()')
    Gui.doCommand('f = PartOMagic.Features.PDShapeFeature.makePDShapeFeature(name = {name}, body= body)'.format(name= repr(name)))
    Gui.doCommand('if f.BaseFeature:\n'
                  '    f.BaseFeature.ViewObject.hide()')
    Gui.doCommand('f.AddSubType = {t}'.format(t= repr(add_sub_type)))
    Gui.doCommand('PartOMagic.Base.Containers.setActiveContainer(f)')
    Gui.doCommand('Gui.Selection.clearSelection()')
    App.ActiveDocument.commitTransaction()


# -------------------------- /common stuff --------------------------------------------------

# -------------------------- Gui command --------------------------------------------------
from PartOMagic.Gui.AACommand import AACommand, CommandError
commands = []
class CommandPDShapeFeature(AACommand):
    "Command to create PDShapeFeature feature"        
    def GetResources(self):
        if self.add_sub_type == 'Additive':
            return {'CommandName': 'PartOMagic_PDShapeFeature_Additive',
                    'Pixmap'  : self.getIconPath('PartOMagic_PDShapeFeature_Additive.svg'),
                    'MenuText': "PartDesign addive shape".format(additive= self.add_sub_type),
                    'Accel': '',
                    'ToolTip': "New PartDesign additive shape container. This allows to insert non-PartDesign things into PartDesign sequence."}
        elif self.add_sub_type == 'Subtractive':
            return {'CommandName': 'PartOMagic_PDShapeFeature_Subtractive',
                    'Pixmap'  : self.getIconPath('PartOMagic_PDShapeFeature_Subtractive.svg'),
                    'MenuText': "PartDesign subtractive shape".format(additive= self.add_sub_type),
                    'Accel': '',
                    'ToolTip': "New PartDesign subtractive shape container. This allows to insert non-PartDesign things into PartDesign sequence."}
        
    def RunOrTest(self, b_run):
        from PartOMagic.Base.Containers import activeContainer
        ac = activeContainer()
        if ac is None:
            raise CommandError(self, "No active container!")
        if not ac.isDerivedFrom('PartDesign::Body'):
            raise CommandError(self, "Active container is not a PartDesign Body. Please activate a PartDesign Body, first.")
        if ac.Tip is None and self.add_sub_type != 'Additive':
            raise CommandError(self, "There is no material to subtract from. Either use additive shape feature instead, or add some material to the body.")
        if b_run: CreatePDShapeFeature('{Additive}Shape'.format(Additive= self.add_sub_type), self.add_sub_type)

commands.append(CommandPDShapeFeature(add_sub_type= 'Additive'))
commands.append(CommandPDShapeFeature(add_sub_type= 'Subtractive'))

exportedCommands = AACommand.registerCommands(commands)