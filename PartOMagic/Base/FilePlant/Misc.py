def generateNewName(wanted_name, existing_names, existing_names_2 = set()):
    """generateNewName(wanted_name, existing_names): returns a unique name (by adding digits to wanted_name). Suitable for file names (but not full paths)"""
    import re
    split = wanted_name.rsplit('.',1)
    title = split[0]
    if len(split) == 2:
        ext = '.' + split[1]
    else:
        ext = ''
    
    match = re.match(r'^(.*?)(\d*)$', title)
    title,number = match.groups()
    if len(number)>0:        
        i = int(number)
        numlen = len(number)
    else:
        i = 0
        numlen = 3
    
    f2 = wanted_name
    while f2 in existing_names or f2 in existing_names_2:
        i += 1
        f2 = title + str(i).rjust(numlen, '0') + ext
    return f2

def FC_version():
    try:
        import FreeCAD
        vertup = FreeCAD.Version()
        # ['0', '18', '15518 (Git)', 'git://github.com/FreeCAD/FreeCAD.git master', '2018/12/29 16:41:25', 'master', 'e83c44200ab428b753a1e08a2e4d95
        # target format: '0.18R14726 (Git)'
        return '{0}.{1}R{2}'.format(*vertup)
    except Exception:
        return '0.18R14726 (Git)'

def recursiveNodeIterator(node):
    yield node
    for child in node:
        for it in recursiveNodeIterator(child):
            yield it
    
class ReplaceTask(object):
    """class ReplaceTask: holds a dict of names to replace, along with (optional) name<->label correspondence, to work in expressions.
    Constructor: ReplaceTask(name_replacement_dict = None, projects = None).
    If you want to remove references to an object, use None as the new name.
    Note: if you want to replace a renamed object by label as well, call addObject on both
    the original and the renamed versions of the object."""

    replacements = None # a dict. key = old name, value = new name
    labels = None ## a dict. key = label (string). value = list of names
    names = None ## a dict. key = name, value = label

    def __init__(self, name_replacement_dict = None, projects = None):
        self.names = dict()
        self.labels = dict()

        if projects is not None:
            try:
                iter(projects)
            except TypeError:
                #not iterable
                projects = [projects]            
            for prj in projects:
                self.addProject(prj)

        self.replacements = name_replacement_dict    if  name_replacement_dict is not None  else    dict()
    
    def addProject(self, project):
        for obj in project.Objects:
            self.addObject(obj.Name, obj.Label)
            
    
    def addObject(self, name, label):
        self.labels[name] = label
        names = self.names.get(label, [])
        if name not in names:
            names.append(name)
        self.names[label] = names
        
    
    def has(self, name):
        return name in self.replacements
    
    def lookup(self, name):
        return self.replacements[name]
    
    def has_label(self, label):
        try:
            self.lookup_label(label)
            return True
        except KeyError:
            return False
    
    def lookup_label(self, label):
        names = self.names.get(label, [])
        if len(names) == 1:
            new_name = self.replacements[names[0]]
            if new_name:
                return self.labels[new_name]
            else:
                return None
        elif len(names) == 0:
            raise KeyError('Label not found')
        else:
            raise KeyError('Label is not unique')
 
    #-------------------------dict-like interface-------------------------
    def __contains__(self, name):
        return self.has(name)
    
    def __getitem__(self, arg):
        return self.lookup(arg)
        
    def __setitem__(self, arg, value):
        self.replacements[arg] = value
        
