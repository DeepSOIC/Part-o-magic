import FreeCAD as App

class Parameter(object):
    path = ""
    param = ""
    type = ""
    default = None
    method_dict = {"Bool": ("GetBool", "SetBool")}
    def get(self):
        if not hasattr(self, "_value"):
            self._value = getattr(App.ParamGet(self.path), self.method_dict[self.type][0])(self.param, self.default)
        return self._value

    def set(self, val):
        getattr(App.ParamGet(self.path), self.method_dict[self.type][1])(self.param, val)
        self._value = val

    def set_volatile(self, val):
        "Changes parameter for part-o-magic, but doesn't write it to preferences. It will self-reset on restart."
        self._value = val

class _paramEnableObserver(Parameter):
    "Sets if PartOMagic Observer is enabled (Observer sorts new objects to active containers,\n\
     and enables visibility automation for container activation)"
    path = "User parameter:BaseApp/Preferences/Mod/PartOMagic"
    param = "EnableObserver"
    type = "Bool"
    default = 1
EnableObserver = _paramEnableObserver()

class _paramEnablePartOMagic(Parameter):
    "Sets if PartOMagic workbench is enabled (if disabled, no commands are added, so no )"
    path = "User parameter:BaseApp/Preferences/Mod/PartOMagic"
    param = "EnablePartOMagic"
    type = "Bool"
    default = 1
EnablePartOMagic = _paramEnablePartOMagic()