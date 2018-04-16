import FreeCAD as App
from PySide import QtCore
if App.GuiUp:
    import FreeCADGui as Gui
    from PySide import QtCore, QtGui
    Qt = QtCore.Qt
    from FreeCADGui import PySideUic as uic

from PartOMagic.Base import LinkTools
from PartOMagic.Gui.Utils import msgError, Transaction
from PartOMagic.Base import Containers

class TaskReplace(QtCore.QObject):
    form = None # task widget
    replacements = None #usually, a list. None is here instead because it's immutable.
    replaced = False
    doc = None
    
    #static
    columns = ['State', 'Object', 'Property', 'Kind', 'Value', 'Path']
    column_titles = ["State", "Object", "Property", "Kind", "Value", "Container Path"]
    column = {} # lookup ductionary, returns column index given column name.
    
    def __init__(self, replacements, doc, message= "Replacing..."):
        QtCore.QObject.__init__(self)
        
        import os
        self.form = uic.loadUi(os.path.dirname(__file__) + os.path.sep + 'TaskReplace.ui')

        self.replacements = replacements
        self.form.message.setText(message)
        
        #debug
        global instance
        instance = self
        
        if replacements:
            self.openTask()
    
    def openTask(self):
        self.fillList()
        Gui.Control.closeDialog() #just in case something else was being shown
        Gui.Control.showDialog(self)
        Gui.Selection.clearSelection() #otherwise, selection absorbs spacebar press event, interferes with list editing
        self.form.treeR.installEventFilter(self)
    
    def closeTask(self):
        self.cleanUp()
        Gui.Control.closeDialog()
    
    def cleanUp(self):
        pass
    
    def getStandardButtons(self):
        return int(QtGui.QDialogButtonBox.Ok) | int(QtGui.QDialogButtonBox.Close) | int(QtGui.QDialogButtonBox.Apply)
    
    def clicked(self,button):
        if button == QtGui.QDialogButtonBox.Apply:
            self.apply()
        elif button == QtGui.QDialogButtonBox.Close:
            self.reject()

    def apply(self):
        try:
            self.doReplace()
        except Exception as err:
            msgError(err)

    def accept(self):
        if not self.replaced:
            success = self.apply()
            if not success: return
        self.cleanUp()
        Gui.Control.closeDialog()
        
    def reject(self):
        self.cleanUp()
        Gui.Control.closeDialog()

    def doReplace(self):
        if self.replaced:
            raise RuntimeError("Already replaced, can't replace again")
        
        self.replacements = LinkTools.sortForMassReplace(self.replacements)
        successcount = 0
        failcount = 0
        
        with Transaction("Replace", self.doc):
            for repl in self.replacements:
                if repl.gui_item.checkState(0) == Qt.Checked:
                    try:
                        repl.replace()
                        repl.gui_item.setCheckState(0, Qt.Unchecked)
                        successcount += 1
                    except Exception as err:
                        repl.error = err
                        failcount += 1
                        import traceback
                        tb = traceback.format_exc()
                        App.Console.PrintError(tb+'\n\n')
        self.replaced = True
        
        self.updateList()
        if failcount == 0:
            self.form.message.setText(u"{successcount} replacements done.".format(successcount= successcount))
        else:
            self.form.message.setText(u"{failcount} of {totalcount} replacements failed. See errors in the list.".format(failcount= failcount, totalcount= failcount+successcount))
            self.form.message.setStyleSheet("QLabel { color : red; }")
        return failcount > 0      
        

    def eventFilter(self, widget, event):
        # spacebar to toggle checkboxes of selected items
        if widget is self.form.treeR:
            if event.type() == QtCore.QEvent.KeyPress:
                if event.key() == Qt.Key_Space:
                    sel = self.form.treeR.selectedItems()
                    if len(sel) > 0:
                        newstate = Qt.Unchecked if sel[0].checkState(0) == Qt.Checked else Qt.Checked
                    for it in self.form.treeR.selectedItems():
                        it.setCheckState(0, newstate)
                    return True
        return False
        
    def fillList(self):
        lw = self.form.treeR
        lw.clear()
        lw.setColumnCount(len(self.columns))
        lw.setHeaderLabels(self.column_titles)
        for repl in self.replacements:
            item = QtGui.QTreeWidgetItem(lw)
            
            item.setText(self.column['Kind'], repl.relation.kind)
            item.setText(self.column['Object'], repl.relation.linking_object.Label)
            item.setText(self.column['Property'], repl.relation.linking_property)
            try:
                chain = Containers.getContainerChain(repl.relation.linking_object)
                path = '.'.join([cnt.Name for cnt in chain] + [repl.relation.linking_object.Name])
            except Exception as err:
                import traceback
                tb = traceback.format_exc()
                App.Console.PrintError(tb+'\n\n')
                path = "!" + str(err)
            item.setText(self.column['Path'], path)
            item.setText(self.column['Value'], str(repl.relation.value_repr))
            
            repl.gui_item = item
            item.setData(0,256,repl)
            flags = Qt.ItemIsUserCheckable | Qt.ItemIsSelectable
            if not repl.disabled:
                flags = flags | Qt.ItemIsEnabled
            item.setFlags(flags)
            item.setCheckState(0, Qt.Checked if repl.checked else Qt.Unchecked)
            if repl.disabled:
                item.setText(self.column['State'], repl.disabled_reason)
    
    def updateList(self):
        """updates status fields of previously filled list"""
        redbrush = QtGui.QBrush(QtGui.QColor(255,128,128))
        for repl in self.replacements:    
            if repl.replaced:
                state = "replaced" 
            else:
                if hasattr(repl, 'error'):
                    state = "! "+str(repl.error)
                    for icol in range(len(self.columns)):
                        repl.gui_item.setBackground(icol, redbrush)
                else:
                    continue #to preserve status of disabled replacements
            repl.gui_item.setText(self.column['State'], state)
        
TaskReplace.column = {TaskReplace.columns[i]:i for i in range(len(TaskReplace.columns))}

class CancelError(RuntimeError):
    pass