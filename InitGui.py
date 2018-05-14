
import FreeCAD as App

import PartOMagic.Base.Parameters as Params

if Params.EnablePartOMagic.get():
    import PartOMagic.Base.Compatibility as compat
    try:
        compat.check_POM_compatible()
        import PartOMagic
        PartOMagic.importAll()
        Gui.addModule("PartOMagic")
        if Params.EnableObserver.get():
            PartOMagic.Gui.Observer.start()
    except compat.CompatibilityError as err:
        Params.EnablePartOMagic.set_volatile(False)
        App.Console.PrintError("Part-o-magic is disabled.\n    {err}".format(err= str(err)))

if Params.EnablePartOMagic.get():
    try:
        import Show.Containers
        # good tempovis, do not replace.
    except ImportError:
        # old TempoVis
        # substitute TempoVis's isContainer with a more modern one
        import Show.TempoVis 
        Show.TempoVis = PartOMagic.Gui.TempoVis.TempoVis

if Params.EnablePartOMagic.get():
    # global toolbar - update only if missing
    if not PartOMagic.Gui.GlobalToolbar.isRegistered():
        PartOMagic.Gui.GlobalToolbar.registerToolbar()
    # PartDesign toolbar - always update
    PartOMagic.Gui.GlobalToolbar.registerPDToolbar()

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
        self.appendMenu('Part-o-Magic', cmdsControl)
        cmdsControl.remove('PartOMagic_Power') #don't add this command to toolbar
        self.appendToolbar('POMControl', cmdsControl)
        
        self.appendMenu('Part-o-Magic', ["Separator"])
        
        cmdsNewContainers = ([]  
            + POM.Features.exportedCommands()
            + POM.Features.PartDesign.exportedCommands()
        )
        self.appendToolbar('POMContainers', cmdsNewContainers)
        self.appendMenu('Part-o-Magic', cmdsNewContainers)

        self.appendMenu('Part-o-Magic', ["Separator"])

        cmdsTools = ([]
            + POM.Gui.Tools.exportedCommands()
        )
        self.appendToolbar('POMTools', cmdsTools)
        self.appendMenu('Part-o-Magic', cmdsTools)

        self.appendMenu('Part-o-Magic', ["Separator"])

        cmdsLinkTools = ([]
            + POM.Gui.LinkTools.exportedCommands()
        )
        self.appendToolbar('POMLinkTools', cmdsLinkTools)
        self.appendMenu('Part-o-Magic', cmdsLinkTools)

        self.appendMenu('Part-o-Magic', ["Separator"])

        cmdsView = ([]
            + POM.Gui.View.exportedCommands()
        )
        self.appendToolbar('POMView', cmdsView)
        self.appendMenu('Part-o-Magic', cmdsView)

        
    def Activated(self):
        pass

if Params.EnablePartOMagic.get():
    Gui.addWorkbench(PartOMagicWorkbench())



