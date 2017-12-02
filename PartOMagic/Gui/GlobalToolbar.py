print("Loading GlobalToolbar")

from . import CommandCollection1
from .Tools import LeaveEnter
from .View import SnapView
from PartOMagic.Features import PartDesign as POMPartDesign

import FreeCAD as App

def registerToolbar():
    p = App.ParamGet("User parameter:BaseApp/Workbench/Global/Toolbar/PartOMagic_2")
    p.SetString("Name", "Part-o-Magic global")
    p.SetString(CommandCollection1.exportedCommands()[0], "FreeCAD")
    p.SetString(LeaveEnter.commandEnter.command_name, "FreeCAD")
    p.SetString(LeaveEnter.commandLeave.command_name, "FreeCAD")
    p.SetString(SnapView.commandSnapView.command_name, "FreeCAD")
    
    
    p.SetBool("Active", 1)
    
    #remove old version of the toolbar
    p_t = App.ParamGet("User parameter:BaseApp/Workbench/Global/Toolbar")
    if p_t.HasGroup('PartOMagic'):
        p_t.RemGroup('PartOMagic')
    
def isRegistered():
    p = App.ParamGet("User parameter:BaseApp/Workbench/Global/Toolbar")
    return p.HasGroup("PartOMagic_2")
    
def registerPDToolbar():
    creating_anew = not isPDRegistered()
    p = App.ParamGet("User parameter:BaseApp/Workbench/PartDesignWorkbench/Toolbar/PartOMagic")
    p.SetString("Name", "Part-o-Magic PartDesign")
    for cmd in POMPartDesign.exportedCommands():
        p.SetString(cmd, "FreeCAD")
    if creating_anew:
        p.SetBool("Active", 1)

def isPDRegistered():
    p = App.ParamGet("User parameter:BaseApp/PartDesignWorkbench/Global/Toolbar")
    return p.HasGroup("PartOMagic")
