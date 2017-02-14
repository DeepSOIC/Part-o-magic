print("Loading OnOff")

from PartOMagic.Gui.Utils import msgbox
import PartOMagic.Base.Parameters as Params

import FreeCAD as App
if App.GuiUp:
    import FreeCADGui as Gui

class CommandTogglePartOMagic:
    "Switches Part-O-magic workbench on or off"
    def GetResources(self):
        from PartOMagic.Gui.Utils import getIconPath
        return {'Pixmap'  : getIconPath("PartOMagic_Power.svg"),
                'MenuText': "Disable/enable Part-o-magic",
                'Accel': "",
                'ToolTip': "Disable/enable Part-o-magic. (disables the workbench)"}
            
    def Activated(self):
        if Params.EnablePartOMagic.get():
            Params.EnablePartOMagic.set(False)
            msgbox("Part-o-Magic", "You've just DISABLED part-o-magic workbench. Please restart FreeCAD. \n\n"
                   "If you disabled it by accident, click this button again to re-enable part-o-magic now.")
        else:
            Params.EnablePartOMagic.set(True)
            msgbox("Part-o-Magic", "You've just ENABLED part-o-magic workbench.")
            
    def IsActive(self):
        return True

if App.GuiUp:
    Gui.addCommand('PartOMagic_Power',  CommandTogglePartOMagic())




class CommandEnableObserver:
    "Switches Part-O-magic observer on"
    def GetResources(self):
        from PartOMagic.Gui.Utils import getIconPath
        return {'Pixmap'  : getIconPath("PartOMagic_EnableObserver.svg"),
                'MenuText': "Enable Observer",
                'Accel': "",
                'ToolTip': "Enable Observer. (enable adding new objects to active containers, and enable visibility automation)"}
            
    def Activated(self):
        import PartOMagic.Gui.Observer as Observer
        if not Observer.isRunning():
            Observer.start()
        Params.EnableObserver.set(True)
            
    def IsActive(self):
        import PartOMagic.Gui.Observer as Observer
        return not Observer.isRunning()

if App.GuiUp:
    Gui.addCommand('PartOMagic_EnableObserver',  CommandEnableObserver())



class CommandPauseObserver:
    "Switches Part-O-magic observer off"
    def GetResources(self):
        from PartOMagic.Gui.Utils import getIconPath
        return {'Pixmap'  : getIconPath("PartOMagic_PauseObserver.svg"),
                'MenuText': "Pause Observer",
                'Accel': "",
                'ToolTip': "Pause Observer. (temporarily disable)"}
            
    def Activated(self):
        import PartOMagic.Gui.Observer as Observer
        if Observer.isRunning():
            Observer.stop()
        Params.EnableObserver.set_volatile(False)
            
    def IsActive(self):
        import PartOMagic.Gui.Observer as Observer
        return Observer.isRunning()

if App.GuiUp:
    Gui.addCommand('PartOMagic_PauseObserver',  CommandPauseObserver())



class CommandDisableObserver:
    "Switches Part-O-magic observer on"
    def GetResources(self):
        from PartOMagic.Gui.Utils import getIconPath
        return {'Pixmap'  : getIconPath("PartOMagic_DisableObserver.svg"),
                'MenuText': "Disable Observer",
                'Accel': "",
                'ToolTip': "Disable Observer. (stop adding new objects to active containers, and disable visibility automation)"}
            
    def Activated(self):
        import PartOMagic.Gui.Observer as Observer
        if Observer.isRunning():
            Observer.stop()
        Params.EnableObserver.set(False)
            
    def IsActive(self):
        return Params.EnableObserver.get_stored()

if App.GuiUp:
    Gui.addCommand('PartOMagic_DisableObserver',  CommandDisableObserver())



    
def exportedCommands():
    return ['PartOMagic_Power', 'PartOMagic_EnableObserver', 'PartOMagic_PauseObserver', 'PartOMagic_DisableObserver']