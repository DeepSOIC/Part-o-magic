import FreeCAD as App

rev_number = int(App.Version()[2].replace("(Git)",""))
if rev_number >= 9933:
    import PartOMagic
    PartOMagic.importAll()
    if App.GuiUp:
        Gui.addModule("PartOMagic")
        PartOMagic.Gui.Observer.start()
else:
    App.Console.PrintError("Part-o-magic requires FreeCAD at least v0.17.9933. Yours appears to have a rev.{rev}, which is less. Part-o-magic is disabled.\n".format(rev= str(rev_number)))



