
import FreeCAD as App

from typing import Self, Callable

class Parameter(object):
    path = "User parameter:BaseApp/Preferences/Mod/PartOMagic"
    param = ""
    type = ""
    default = None
    method_dict = {"Bool": ("GetBool", "SetBool")}
    subscribers = None

    def __init__(self):
        self.subscribers = []

    def get(self):
        if not hasattr(self, "_value"):
            self._value = self.get_stored()
        return self._value
    
    def get_stored(self):
        return getattr(App.ParamGet(self.path), self.method_dict[self.type][0])(self.param, self.default)

    def set(self, val):
        getattr(App.ParamGet(self.path), self.method_dict[self.type][1])(self.param, val)

    def set_volatile(self, val):
        "Changes parameter for part-o-magic, but doesn't write it to preferences. It will self-reset on restart."
        old_val = self.get()
        self._value = val
        if val != old_val:
            for func in self.subscribers:
                func(self, old_val, val)
    
    def reset_volatile(self):
        self.set_volatile(self.get_stored())
    
    def __bool__(self):
        # this is here mainly to prevent "if Parameters.Something: # missing .get()" cause hard-to-catch bugs
        if self.type == 'Bool':
            return self.get()
        else:
            raise NotImplementedError(f"Parameter {self.param} is not a boolean")
    
    def subscribe(self, func: Callable[[Self, any, any], None]):
        if not func in self.subscribers:
            self.subscribers.append(func)

    def unsubscribe(self, func):
        try:
            self.subscribers.remove(func)
        except ValueError:
            return False
        else:
            return True

# sadly, this does not work... Would have been nice though
class Observer(object):
    def onChange(self, param_grp, param_name):
        print(f"PoM: {param_name} changed")
        from PartOMagic.Base import Parameters
        if hasattr(Parameters, param_name):
            getattr(Parameters, param_name).reset_volatile()
    
    def __init__(self, path):
        self.p = App.ParamGet(path) # p going out of scope causes the subscription to be lost =( so we are saving it
        self.p.Attach(self)
_observer1 = Observer(Parameter.path)

class _paramEnableObserver(Parameter):
    "Sets if PartOMagic Observer is enabled (Observer sorts new objects to active containers,\n\
     and enables visibility automation for container activation)"
    param = "EnableObserver"
    type = "Bool"
    default = 1
EnableObserver = _paramEnableObserver()

class _paramEnablePartOMagic(Parameter):
    "Sets if PartOMagic workbench is enabled (if disabled, no commands are added, so no )"
    param = "EnablePartOMagic"
    type = "Bool"
    default = 1
EnablePartOMagic = _paramEnablePartOMagic()

class _paramUseFileplantToDuplicate(Parameter):
    "Sets if PartOMagic uses FilePlant to copy objects. If False, uses Document.copyObject function."
    param = "UseFileplantToDuplicate"
    type = "Bool"
    default = 0
UseFileplantToDuplicate = _paramUseFileplantToDuplicate()

class _paramEnableSorting(Parameter):
    "add objects to active container?"
    param = "EnableSorting"
    type = "Bool"
    default = 1
EnableSorting = _paramEnableSorting()

class _paramVisibilityAutomation(Parameter):
    "hide stuff when entering?"
    param = "VisibilityAutomation"
    type = "Bool"
    default = 1
VisibilityAutomation = _paramVisibilityAutomation()
