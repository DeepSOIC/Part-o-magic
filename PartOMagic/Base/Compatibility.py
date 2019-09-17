print("Part-o-magic: Loading Compatibility")
import FreeCAD as App

def get_fc_revision_nr():
    return int(App.Version()[2].split(" ")[0])
    
def check_POM_compatible():
    """Raises CompatibilityError if PoM is known to not run"""
    try:
        rev = get_fc_revision_nr()
    except Exception as err:
        App.Console.PrintWarning(u"PartOMagic failed to detect FC version number.\n"
                                 "    {err}\n".format(err= str(err)))
        #keep going, assume the version is good enough...
        return
        
    if rev < 9933:
        raise CompatibilityError("Part-o-magic requires FreeCAD at least v0.17.9933. Yours appears to have a rev.{rev}, which is less.".format(rev= rev))
    
def scoped_links_are_supported():
    try:
        return get_fc_revision_nr() >= 12027
    except Exception as err:
        return True #assume good

class CompatibilityError(RuntimeError):
    pass
