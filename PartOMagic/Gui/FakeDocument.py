import FreeCAD as App
from PartOMagic.Base import Containers
from PartOMagic.Base import Parameters

MY_ATTRS = [
    '_doc',
]

TYPE_EXCLUSIONS = [
    'App::Origin'
]

objects_handled = set()

active = False

class FakeDocument(object):
    _doc = None

    def __init__(self, doc: App.Document):
        super().__setattr__('_doc', doc)

    def addObject(self, type, *args, **kwargs):
        if not active:
            return self._doc.addObject(type, *args, **kwargs)
                
        ac = None
        try:
            ac = Containers.activeContainer()
        except Exception:
            ac = self._doc
        if ac is None:
            ac = self._doc
        if not ac.isDerivedFrom('App::Document') and ac.Document is not self._doc:
            print(f"PoM.FakeDocument: active container not in this doc\n")
            ac = self._doc
        if type in TYPE_EXCLUSIONS:
            ac - self._doc
        if ac is self._doc:
            print(f"PoM.FakeDocument: adding new object {type} to root\n")
            return self._doc.addObject(type, *args, **kwargs)
        else:
            print(f"PoM.FakeDocument: adding new object {type} to {ac.Label}\n")
            return ac.newObject(type, *args, **kwargs)
    
    def recompute(self, objects = None, force = False, *args, **kwargs) -> int:
        print("PoM.FakeDocument: recompute called")
        bypass = True
        try:
            from PartOMagic.Base import Recomputer
            bypass = (
                objects is not None
                or not active
                or defake(App.ActiveDocument) is not self._doc # we can maybe complicate things and recall active container for inactive document, but let's not go that far
            )
            if not bypass:
                print("PoM.FakeDocument: scoped recompute!")
                return Recomputer.scoped_recompute()
        except Recomputer.DependencyLoopError:
            # this one shouldn't trigger a fallback to standard recompute 
            raise
        except Exception as err:
            App.Console.PrintError(f'PoM FakeDocument: scoped recompute error {str(err)}\n  fallback to normal recompute...\n')
        print("PoM.FakeDocument: recompute bypass")
        return self._doc.recompute(objects, force, *args, **kwargs)
    
    def __getattr__(self, attrname):
        if attrname in MY_ATTRS:
            return super().__getattr__(attrname)
        return getattr(self._doc, attrname)
    
    def __setattr__(self, attrname, value):
        if attrname in MY_ATTRS:
            super().__setattr__(attrname)        
        setattr(self._doc, attrname, value)

def fakeIt():
    "make App.ActiveDocument be our fake"
    if App.ActiveDocument is None:
        return
    if isinstance(App.ActiveDocument, FakeDocument):
        #nothing to do, alrady faked
        return
    print("PoM: faking Active Document")
    App.ActiveDocument = FakeDocument(App.ActiveDocument)

def unfakeIt():
    if App.ActiveDocument is None:
        return
    if not isinstance(App.ActiveDocument, FakeDocument):
        #nothing to do, alrady unfaked
        return
    print("PoM: unfaking Active Document")
    App.ActiveDocument = App.ActiveDocument._doc

def defake(cnt):
    "returns cnt, but unwraps FakeDocument"
    if isinstance(cnt, FakeDocument):
        return cnt._doc
    return cnt

def poll():
    "reinstall hooks if necessary"
    if active:
        fakeIt()

def PoMsetActiveDocument(new_doc):
    "PoM's replacement for App.setActiveDocument"
    print("PoM: setActiveDocument hook trigger")
    ret = PoMsetActiveDocument.original(new_doc)
    if active:
        fakeIt()
    return ret

freecads_setActiveDocument = App.setActiveDocument
freecads_setActiveDocument = getattr(freecads_setActiveDocument, 'original', freecads_setActiveDocument) # avoid replacing twice
PoMsetActiveDocument.original = freecads_setActiveDocument

def PoMGetDocument(name):
    print("PoM: setGetDocument hook trigger")
    if active: # when inactive, behave like FreeCAD's, just in case someone has cached App.getDocument and thus may still be using this function
        return FakeDocument(PoMGetDocument.original(name))
    else:
        return PoMGetDocument.original(name)

freecads_getDocument = App.getDocument
freecads_getDocument = getattr(freecads_getDocument, 'original', freecads_getDocument) # avoid replacing twice
PoMGetDocument.original = freecads_getDocument

def PoMActiveDocument():
    print("PoM: setActiveDocument hook trigger")
    if active: #  when inactive, behave like FreeCAD's, just in case someone has cached App.activeDocument and thus may still be using this function
        return FakeDocument(PoMActiveDocument.original())
    else:
        return PoMActiveDocument.original()

freecads_activeDocument = App.activeDocument
freecads_activeDocument = getattr(freecads_activeDocument, 'original', freecads_activeDocument) # avoid replacing twice
PoMActiveDocument.original = freecads_activeDocument


def start():
    global active
    if active: return
    App.setActiveDocument = PoMsetActiveDocument
    App.getDocument = PoMGetDocument
    App.activeDocument = PoMActiveDocument
    fakeIt()
    active = True

def stop():
    global active
    #if not active: return
    App.setActiveDocument = PoMsetActiveDocument.original
    App.getDocument = PoMGetDocument.original
    App.activeDocument = PoMActiveDocument.original
    unfakeIt()
    active = False


# def makeFakeDocument(doc):
#     "makeFakeDocument(doc): make a subclass of FakeDocument with copied attributes of doc. This is a hack to trick FreeCAD to list all the attrs for autocompletion"
#     from copy import copy
#     attrs = dict(FakeDocument.__dict__.items())
#     prop_name: str
#     for prop_name in list(doc.__dict__.keys()) + list(type(doc).__dict__.keys()):
#         if prop_name.startswith('__') and prop_name.endswith('__'):
#             continue
#         if prop_name in MY_ATTRS:
#             continue
#         try:
#             attrs[prop_name] = None#getattr(doc, prop_name)
#         except Exception as err:
#             attrs[prop_name] = err

#     TT = type('FakeDocument_Specialized', (FakeDocument,), attrs)
#     return TT(doc)

