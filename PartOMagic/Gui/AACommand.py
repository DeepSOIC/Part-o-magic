'''AACommand module is here to automate some stuff of command addition within Part-o-magic.

Example command implementation follows.

from PartOMagic.Gui.AACommand import AACommand, CommandError
commands = []
class CommandEnter(AACommand):
    "Command to enter a feature"
    def GetResources(self):
        import SketcherGui #needed for icons
        return {'CommandName': 'PartOMagic_Enter',  # !!! <----- compared to standard FreeCAD command definition, add this!
                'Pixmap'  : self.getIconPath('Sketcher_EditSketch.svg'),
                'MenuText': "Enter object",
                'Accel': "",
                'ToolTip': "Enter object. (activate a container, or open a sketch for editing)"}
        
    def RunOrTest(self, b_run):
        # !!! RunOrTest is called by AACommand from within both IsActive and Activate. 
        # if b_run is True, the call is from Activated, and you need to perform the action.
        # if b_run is False, you should do a dry run: check the conditions, and throw errors, but not do the thing!
        # if conditions are not met.
        
        sel = Gui.Selection.getSelection()
        if len(sel)==0 :
            raise CommandError(self, "Enter Object command. Please select an object to enter, first. It can be a container, or a sketch.")
            #if you raise CommandError, command is inactive. If you throw any other error, 
            # command is inactive too, but the error is printed to report view.
        elif len(sel)==1:
            if b_run: Containers.setActiveContainer(sel) # !!! <---- check for b_run is very important! otherwise the command will run every half a second, and screw everything up!
            if b_run: Gui.Selection.clearSelection()
        else:
            raise CommandError(self, u"Enter Object command. You need to select exactly one object (you selected {num}).".format(num= len(sel)))            
        
        # Returning without any error is the signal that the command is active! Return value is ignored.
        # Any error thrown when b_run is True will pop up as error message (except CancelError).
       
commands.append(CommandEnter())

# (add more to commands)

exportedCommands = AACommand.registerCommands(commands)

--------------------
AACommand constructor takes any keyword arguments, and adds them as attributes of instance.
E.g. 
cmd = AACommand(my_type= 'additive')
# cmd.my_type == 'additive'

AACommand is not registered automatically. Use register() method.
AACommand.registerCommands() static method is convenient to register a list of commands, 
and make exportedCommands() function at the same time.
'''


print("loading AACommand")

import FreeCAD as App
from PartOMagic.Base.Containers import NoActiveContainerError

from PartOMagic.Gui.Utils import msgError

class CommandError(Exception):
    def __init__(self, command, message):
        self.command = command
        try:
            self.title = "Part-o-Magic "+ command.GetResources()['MenuText']
        except Exception as err:
            self.title = "<ERROR READING OUT MenuText>"
        self.message = message
        self.show_msg_on_delete = True
    
    def __del__(self):
        if self.show_msg_on_delete:
            msgError(self)
        
registeredCommands = {} #dict, key = command name, value = instance of command

class AACommand(object):
    "Command class prototype. Any keyword arguments supplied to constructor are added as attributes"
    def __define_attributes(self):
        self.AA = False #AA stands for "Always Active". If true, IsActive always returns true, and error message is shown if conditions are not met (such as not right selection).
        self.command_name = None # string specifying command name
        self.command_name_aa = None
        self.is_registered = False
        self.aa_command_instance = None
    
    def __init__(self, **kwargs):
        self.__define_attributes()
        for arg in kwargs:
            setattr(self, arg, kwargs[arg])
    
    def register(self):
        if self.isRegistered():
            import FreeCAD as App
            App.Console.PrintWarning(u"Re-registering command {cmd}\n".format(cmd= self.command_name))
            
        if self.command_name is None:
            self.command_name = self.GetResources()['CommandName']
        
        import FreeCADGui as Gui
        Gui.addCommand(self.command_name, self)
        global registeredCommands
        registeredCommands[self.command_name] = self
        self.is_registered = True
        
        #also register an AA version of the command
        if not self.AA:
            self.command_name_aa = self.command_name + '_AA'
            import copy
            cpy = copy.copy(self)
            cpy.AA = True
            cpy.command_name = self.command_name_aa
            cpy.is_registered = False #since we copied an already registered command, it thinks it's registered too.
            cpy.register()
            self.aa_command_instance = cpy
        
        return self.command_name
    
    def isRegistered(self):
        return self.is_registered

    def RunOrTest(self, b_run):
        raise CommandError(self, "command not implemented")
        # override this. if b_run, run the actual code. If not, do a dry run and throw CommandErrors if conditions are not met.
    
    def Activated(self):
        # you generally shouldn't override this. Override RunOrTest instead.
        try:
            self.RunOrTest(b_run= True)
        except CommandError as err:
            pass
        except Exception as err:
            msgError(err)
            raise
            
    def IsActive(self):
        # you generally shouldn't override this. Override RunOrTest instead.
        if not App.ActiveDocument: return False
        if self.AA: return True 
        try:
            self.RunOrTest(b_run= False)
            return True
        except CommandError as err:
            err.show_msg_on_delete = False
            return False
        except NoActiveContainerError as err:
            #handling these to prevent error train in report view, when in spreadsheet for example
            return False
        except Exception as err:
            App.Console.PrintError(repr(err))
            return True

    def getIconPath(self, icon_dot_svg):
        import PartOMagic.Gui.Icons.Icons
        return ":/icons/" + icon_dot_svg
    
    @staticmethod
    def registerCommands(list_of_commands):
        'registerCommands(list_of_commands): registers commands, and returns typical implementation of exportedCommands()'
        f_ret = lambda: _exportedCommands(list_of_commands)
        if App.GuiUp:
            f_ret()# to actually register them
        return f_ret
            
def _exportedCommands(commands):
    if not commands[0].isRegistered():
        for cmd in commands:
            cmd.register()
    return [cmd.command_name for cmd in commands]
