__doc__ = 'module that registers preference page'

def addPreferences():
    import os
    import FreeCADGui as Gui

    Gui.addPreferencePage(os.path.dirname(__file__) + '/partomagic-pref-general.ui'.replace('/', os.path.sep),"PartOMagic") 

addPreferences()
