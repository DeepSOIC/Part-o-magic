library = {} #dict. Key = object, Value = TempoVis_instance


def XRay(obj):
    import FreeCAD as App
    import Show
    
    global library
    if obj is None:
        for itobj in library:
            tv = library[itobj]
            tv.restore()
        library = {}
        return
    if obj in library:
        tv = library.pop(obj)
        tv.restore()
    else:
        tv = Show.TempoVis(App.ActiveDocument)
        tv.modifyVPProperty(obj, 'Transparency', 80)
        tv.modifyVPProperty(obj, 'DisplayMode', 'Shaded')
        tv.setUnpickable(obj)
        library[obj] = tv
    

from PartOMagic.Gui.AACommand import AACommand, CommandError
commands = []

class CommandXRay(AACommand):
    "Command to select through object"
    def GetResources(self):
        return {'CommandName': 'PartOMagic_XRay',
                'Pixmap'  : self.getIconPath("PartOMagic_XRay.svg"),
                'MenuText': "X-ray selected object",
                'Accel': "",
                'ToolTip': "X-ray: makes an object transparent and click-through.",
                'CmdType': 'ForEdit'}
        
    def RunOrTest(self, b_run):
        import FreeCADGui as Gui
        sel = Gui.Selection.getSelectionEx()
        global library
        if len(sel) == 0 and len(library) == 0 :
            raise CommandError(self, "Please select an object to make transparent, and invoke this command.")
        if b_run:
            if len(sel) == 0:
                XRay(None)
            else:
                for selobj in sel:
                    XRay(selobj.Object)
                Gui.Selection.clearSelection()
                Gui.Selection.clearPreselection()
                

commandXRay = CommandXRay()
commands.append(commandXRay)


exportedCommands = AACommand.registerCommands(commands)