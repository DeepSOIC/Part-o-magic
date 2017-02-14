
import FreeCAD as App

import PartOMagic.Base.Parameters as Params

if Params.EnablePartOMagic.get():
    rev_number = int(App.Version()[2].replace("(Git)",""))
    if rev_number >= 9933:
        import PartOMagic
        PartOMagic.importAll()
        Gui.addModule("PartOMagic")
        if Params.EnableObserver.get():
            PartOMagic.Gui.Observer.start()
    else:
        Params.EnablePartOMagic.set_volatile(False)
        App.Console.PrintError("Part-o-magic requires FreeCAD at least v0.17.9933. Yours appears to have a rev.{rev}, which is less. Part-o-magic is disabled.\n".format(rev= str(rev_number)))

if Params.EnablePartOMagic.get():
    # substitute TempoVis's isContainer with a more modern one
    import Show.TempoVis 
    Show.TempoVis = PartOMagic.Gui.TempoVis.TempoVis

class PartOMagicWorkbench (Workbench):
    MenuText = 'Part-o-magic'
    ToolTip = "Part-o-magic: experimental group and Part and Body automation"

    def __init__(self):
        # Hack: obtain path to POM by loading a dummy Py module
        import os
        import PartOMagic
        self.__class__.Icon = os.path.dirname(PartOMagic.__file__) + u"/Gui/Icons/icons/PartOMagic.svg".replace("/", os.path.sep)

    def Initialize(self):
        import PartOMagic as POM
        POM.importAll()

        cmdsControl = ([]
            + POM.Gui.Control.exportedCommands()
        )
        self.appendToolbar('POMControl', cmdsControl)
        self.appendMenu('Part-o-Magic', cmdsControl)
        
        self.appendMenu('Part-o-Magic', ["Separator"])
        
        cmdsNewContainers = ([]
            + ["PartDesign_Part"]            
            + ["PartDesign_Body"]            
            + POM.Features.exportedCommands()
        )
        self.appendToolbar('POMContainers', cmdsNewContainers)
        self.appendMenu('Part-o-Magic', cmdsNewContainers)

        self.appendMenu('Part-o-Magic', ["Separator"])

        cmdsTools = ([]
            + POM.Gui.Tools.exportedCommands()
        )
        self.appendToolbar('POMTools', cmdsTools)
        self.appendMenu('Part-o-Magic', cmdsTools)

        
    def Activated(self):
        pass

if Params.EnablePartOMagic.get():
    Gui.addWorkbench(PartOMagicWorkbench())



