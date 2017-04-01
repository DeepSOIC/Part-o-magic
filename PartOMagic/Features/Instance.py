import FreeCAD as App

from PartOMagic.Gui.Utils import Transaction



def CreateInstance():
    import FreeCADGui as Gui
    sel = Gui.Selection.getSelectionEx(App.ActiveDocument.Name)
    objs = [selobj.Object for selobj in sel]
    with Transaction("Create Instance"):
        for obj in objs:
            objname = obj.Name
            reprname = repr(obj.Name + '_i000')
            Gui.doCommand("f = App.ActiveDocument.addObject('App::Link',{reprname})\n"
                          "f.Source = App.ActiveDocument.{objname}\n".format(**vars()))
            Gui.doCommand("f.Label = 'instance{num} of {obj}'.format(num= f.Name[-3:], obj= f.Source.Label)")
    Gui.doCommand("Gui.Selection.clearSelection()")



from PartOMagic.Gui.AACommand import AACommand, CommandError
commands = []
class CommandPart(AACommand):
    "Command to create an instance of an object"
    def GetResources(self):
        return {'CommandName': "PartOMagic_Instance",
                'Pixmap'  : self.getIconPath("PartOMagic_Instance.svg"),
                'MenuText': "Make instance (realthunder's App::Link)",
                'Accel': "",
                'ToolTip': "Make instance: create a visual clone of selected object."}        
    def RunOrTest(self, b_run):
        import FreeCADGui as Gui
        if len(Gui.Selection.getSelectionEx(App.ActiveDocument.Name))==0:
            raise CommandError(self, "Please select one or more objects, first. Instances of these objects will be created.")
        if b_run: CreateInstance()
commands.append(CommandPart())

exportedCommands = AACommand.registerCommands(commands)