print("loading Utils")

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
    
    
def getIconPath(icon_dot_svg):
    return ":/icons/" + icon_dot_svg

class CommandError(Exception):
    def __init__(self, title, message):
        self.title = title
        self.message = message

class CancelError(Exception):
    pass

