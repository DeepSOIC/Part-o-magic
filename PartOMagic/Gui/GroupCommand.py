
#example:
#Gui.addCommand('PartOMagic_Collection1',
# GroupCommand(
#    list_of_commands= myFeatures.exportedCommands() + ['PartOMagic_SetTip'],
#    menu_text= "PartOMagic collection 1",
#    tooltip= ""
#   )
# )
class GroupCommand(object):
    def __init__(self, list_of_commands, menu_text, tooltip, for_edit= False):
        self.list_of_commands = [(cmd+'_AA' if cmd.startswith('PartOMagic') else cmd) for cmd in list_of_commands]
        self.menu_text = menu_text
        self.tooltip = tooltip
        
    def GetCommands(self):
        return tuple(self.list_of_commands) # a tuple of command names that you want to group

    def GetDefaultCommand(self): # return the index of the tuple of the default command. This method is optional and when not implemented '0' is used  
        return 0

    def GetResources(self):
        return { 'MenuText': self.menu_text, 'ToolTip': self.tooltip}
        
    def IsActive(self): # optional
        return True
