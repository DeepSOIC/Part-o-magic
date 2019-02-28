def makeObject(doc, type_id, name):
    import FreeCAD
    obs = Observer(doc)
    FreeCAD.addDocumentObserver(obs)
    try:
        obj = doc.addObject(type_id, name)
    finally:
        FreeCAD.removeDocumentObserver(obs)
    #some objects add extra objects automatically (e.g. Part makes an Origin). Can't prevent their creation. But can delete.
    for n in obs.new_objects:
        if n != obj.Name:
            doc.removeObject(n)
    return obj
    

class Observer(object):
    new_objects = None
    doc = None

    def __init__(self, doc):
        self.new_objects = []
        self.doc = doc

    def slotCreatedObject(self, feature):
        if feature.Document is self.doc:
            self.new_objects.append(feature.Name)
