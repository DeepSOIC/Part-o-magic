print("Loading GlobalToolbar")

from . import CommandCollection1
from .Tools import LeaveEnter
from PartOMagic.Base import Parameters

import FreeCAD as App

def registerToolbar():
    p = App.ParamGet("User parameter:BaseApp/Workbench/Global/Toolbar/PartOMagic")
    p.SetString("Name", "Part-o-Magic global")
    p.SetString(CommandCollection1.exportedCommands()[0], "FreeCAD")
    p.SetString(LeaveEnter.commandEnter.command_name, "FreeCAD")
    p.SetString(LeaveEnter.commandLeave.command_name, "FreeCAD")
    p.SetBool("Active", 1)
    
def isRegistered():
    p = App.ParamGet("User parameter:BaseApp/Workbench/Global/Toolbar")
    return p.HasGroup("PartOMagic")