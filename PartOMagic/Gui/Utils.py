print("loading Utils")

#TODO: remove this:
def getIconPath(icon_dot_svg):
    import PartOMagic.Gui.Icons.Icons
    return ":/icons/" + icon_dot_svg

def msgbox(title, text):
    from PySide import QtGui
    mb = QtGui.QMessageBox()
    mb.setIcon(mb.Icon.Information)
    mb.setText(text)
    mb.setWindowTitle(title)
    mb.exec_()
    
def msgError(err):
    from PySide import QtGui
    if type(err) is CancelError: return
    mb = QtGui.QMessageBox()
    mb.setIcon(mb.Icon.Warning)
    mb.setText(err.message)
    if hasattr(err, "title"):
        mb.setWindowTitle(err.title)
    else:
        mb.setWindowTitle("Error")
    mb.exec_()
    
    
class CancelError(Exception):
    pass

def screen(feature):
    """screen(feature): protects link properties from being overwritten. 
    This is to be used as workaround for a bug where modifying an object accessed through 
    a link property of another object results in the latter being touched.
    
    returns: feature"""
    if not hasattr(feature,"isDerivedFrom"):
        return feature
    if not feature.isDerivedFrom("App::DocumentObject"):
        return feature
    if feature.Document is None:
        return feature
    feature = getattr(feature.Document, feature.Name)
    return feature