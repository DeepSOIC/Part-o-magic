
import FreeCAD as App

import PartOMagic.Base.Parameters as Params

if Params.EnablePartOMagic.get():
    rev_number = int(App.Version()[2].split(" ")[0])

    p = FreeCAD.ParamGet("User parameter:BaseApp/Workbench/Global/Toolbar")
    t0 = p.GetGroup("POMControl")
    t1 = p.GetGroup("POMContainers")
    t2 = p.GetGroup("POMTools")

    if rev_number >= 9933:
        t0.SetString("Name", "POMControl")
        t0.SetString("PartOMagic_Power", "FreeCAD")
        t0.SetString("PartOMagic_EnableObserver", "FreeCAD")
        t0.SetString("PartOMagic_PauseObserver", "FreeCAD")
        t0.SetString("PartOMagic_DisableObserver", "FreeCAD")
        t0.SetBool("Active", 1)
        t1.SetString("Name", "POMContainers")
        t1.SetString("PartDesign_Part", "FreeCAD")
        t1.SetString("PartOMagic_Module", "FreeCAD")
        t1.SetString("PartOMagic_ShapeGroup", "FreeCAD")
        t1.SetString("PartOMagic_PDShapeFeature_Additive", "FreeCAD")
        t1.SetString("PartOMagic_PDShapeFeature_Subtractive", "FreeCAD")
        t1.SetString("PartOMagic_ShapeBinder", "FreeCAD")
        t1.SetString("PartOMagic_Exporter", "FreeCAD")
        t1.SetBool("Active", 1)
        t2.SetString("Name", "POMTools")
        t2.SetString("PartOMagic_Enter", "FreeCAD")
        t2.SetString("PartOMagic_Leave", "FreeCAD")
        t2.SetString("PartOMagic_SetTip", "FreeCAD")
        t2.SetBool("Active", 1)

        import PartOMagic
        PartOMagic.importAll()
        Gui.addModule("PartOMagic")
        if Params.EnableObserver.get():
            PartOMagic.Gui.Observer.start()
    else:
        t0.SetBool("Active", 0)
        t1.SetBool("Active", 0)
        t2.SetBool("Active", 0)
        Params.EnablePartOMagic.set_volatile(False)
        App.Console.PrintError("Part-o-magic requires FreeCAD at least v0.17.9933. Yours appears to have a rev.{rev}, which is less. Part-o-magic is disabled.\n".format(rev= str(rev_number)))

if Params.EnablePartOMagic.get():
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
        # self.appendToolbar('POMControl', cmdsControl)
        self.appendMenu('Part-o-Magic', cmdsControl)
        
        self.appendMenu('Part-o-Magic', ["Separator"])
        
        import PartDesignGui #needed for the command
        
        cmdsNewContainers = ([]
            + ["PartDesign_Part"]            
            + POM.Features.exportedCommands()
            + POM.Features.PartDesign.exportedCommands()
        )
        # self.appendToolbar('POMContainers', cmdsNewContainers)
        self.appendMenu('Part-o-Magic', cmdsNewContainers)
        self.appendMenu('Part-o-Magic', ["Separator"])

        cmdsTools = ([]
            + POM.Gui.Tools.exportedCommands()
        )
        # self.appendToolbar('POMTools', cmdsTools)
        self.appendMenu('Part-o-Magic', cmdsTools)

        
    def Activated(self):
        pass

if Params.EnablePartOMagic.get():
    Gui.addWorkbench(PartOMagicWorkbench())



