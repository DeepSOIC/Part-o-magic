print("Part-o-magic: Loading CommandCollection1")

import PartOMagic.Gui as myGui
myGui.Tools.importAll()
import PartOMagic.Features as myFeatures
myFeatures.importAll()
from .GroupCommand import GroupCommand

import FreeCADGui as Gui

Gui.addCommand('PartOMagic_Collection1',
 GroupCommand(
    list_of_commands= myFeatures.exportedCommands() + ['PartOMagic_SetTip'],
    menu_text= "PartOMagic collection 1",
    tooltip= ""
   )
 )

def exportedCommands():
    return ['PartOMagic_Collection1']