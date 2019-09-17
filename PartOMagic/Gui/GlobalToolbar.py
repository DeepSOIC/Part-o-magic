print("Part-o-magic: Loading GlobalToolbar")

from . import CommandCollection1
from .Tools import LeaveEnter
from .View import SnapView, XRay
from PartOMagic.Features import PartDesign as POMPartDesign

import FreeCAD as App

def findToolbar(name, label, workbench, create = False):
    """findToolbar(name, label, workbench, create= False): returns tuple "User parameter:BaseApp/Workbench/Global/Toolbar", "toolbar_group_name"."""
    tb_root = "User parameter:BaseApp/Workbench/{workbench}/Toolbar".format(workbench= workbench)
    pp = App.ParamGet(tb_root)
    if pp.HasGroup(name):
        return [tb_root, name]
    
    for i in range(10):
        g = 'Custom_'+str(i)
        if pp.HasGroup(g) and pp.GetGroup(g).GetString('Name') == label:
            print("has custom!")
            return [tb_root, g]
    if create:
        return [tb_root, name]
    return None

def findGlobalToolbar(name, label, create = False):
    return findToolbar(name, label, 'Global', create)

def findPDToolbar(name, label, create = False):
    return findToolbar(name, label, 'PartDesignWorkbench', create)
    
def registerToolbar():
    p = App.ParamGet('/'.join(findGlobalToolbar("PartOMagic_3", "Part-o-Magic global v3", create= True)))
    p.SetString("Name", "Part-o-Magic global v3")
    p.SetString(CommandCollection1.exportedCommands()[0], "FreeCAD")
    p.SetString(LeaveEnter.commandEnter.command_name, "FreeCAD")
    p.SetString(LeaveEnter.commandLeave.command_name, "FreeCAD")
    p.SetString(SnapView.commandSnapView.command_name, "FreeCAD")
    p.SetString(XRay.commandXRay.command_name, "FreeCAD")
    
    
    p.SetBool("Active", 1)
    
    #remove old version of the toolbar
    tb = findGlobalToolbar('PartOMagic', "Part-o-Magic global")
    if tb:
        print("Delete")
        App.ParamGet(tb[0]).RemGroup(tb[1])
    tb = findGlobalToolbar('PartOMagic_2', "Part-o-Magic global")
    if tb:
        print("Delete2")
        App.ParamGet(tb[0]).RemGroup(tb[1])

    
def isRegistered():
    return findGlobalToolbar("PartOMagic_3", "Part-o-Magic global v3") is not None
    
def registerPDToolbar():
    creating_anew = not isPDRegistered()
    p = App.ParamGet('/'.join(findPDToolbar('PartOMagic',"Part-o-Magic PartDesign", create= True)))
    p.SetString("Name", "Part-o-Magic PartDesign")
    for cmd in POMPartDesign.exportedCommands():
        p.SetString(cmd, "FreeCAD")
    if creating_anew:
        p.SetBool("Active", 1)

def isPDRegistered():
    return findPDToolbar('PartOMagic',"Part-o-Magic PartDesign")
