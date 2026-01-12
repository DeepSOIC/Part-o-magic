import FreeCAD as App
import PartOMagic.Base.Containers as Containers

def dbg_print_objects(objects, hint):
    print(hint)
    for obj in objects:
        print("  " + obj.Label)

def topological_sort(objects: list[App.DocumentObject]) -> tuple[list[App.DocumentObject], set[App.DocumentObject], list[App.DocumentObject]]:
    "returns: (list1, set, list2). If successful, list1 is the topoligically sorted objects, starting with the one to be recomputed first, others are empty.\n"
    "if not successful: list1 is sorted part before the interdependent blob, set is the blob with dependency cycles, and list2 is the trailing sorted part"
    remaining = set(objects)
    sorted_fromstart = []
    sorted_fromend = []
    # filter inputs/outputs to objects we are sorting
    inputs = {obj : set(obj.OutList).intersection(remaining) for obj in remaining}
    outputs = {obj : set(obj.InList).intersection(remaining) for obj in remaining}

    made_progress = True # make first iteration happen
    while made_progress:
        # find objects with no inputs remaining, they are ready to be recomputed
        collected = set()
        for obj in remaining:
            if not inputs[obj]:
                collected.add(obj)
                sorted_fromstart.append(obj)
        #dbg_print_objects(collected, "collected objects with no inputs")
        remaining.difference_update(collected)
        # and remode them from all inputs
        for obj in remaining:
            inputs[obj].difference_update(collected)
        
        made_progress = bool(collected)

        # find objects with no inputs remaining, they are ready to be recomputed
        collected = set()
        for obj in remaining:
            if not outputs[obj]:
                collected.add(obj)
                sorted_fromend.append(obj)
        #dbg_print_objects(collected, "collected objects with no outputs")
        remaining.difference_update(collected)
        # and remode them from all inputs
        for obj in remaining:
            outputs[obj].difference_update(collected)

        made_progress = made_progress or bool(collected)
    
    if remaining:
        return sorted_fromstart, remaining, sorted_fromend[::-1]
    else:
        return sorted_fromstart + sorted_fromend[::-1], set(), list() 

def current_scope() -> set[App.DocumentObject]:
    ac = Containers.activeContainer()
    return container_scope(ac)

def container_scope(cnt) -> set[App.DocumentObject]:
    if cnt.isDerivedFrom('App::Document'):
        return cnt.Objects
    objects = Containers.getAllDependencies(cnt)
    objects.add(cnt)
    return objects

def recompute_is_needed(scope: set[App.DocumentObject]):
    touched = [obj for obj in scope if 'Touched' in obj.State or obj.MustExecute]
    return len(touched) > 0

def find_features_to_recompute(scope: set[App.DocumentObject]) -> set[App.DocumentObject]:
    touched = [obj for obj in scope if 'Touched' in obj.State or obj.MustExecute]
    return Containers.getAllDependent2(touched) & scope

def scoped_recompute(scope : (set[App.DocumentObject] | App.Document | App.DocumentObject | None) = None, warn_noop : bool = False):
    if scope is None:
        scope = Containers.activeContainer()
    
    if hasattr(scope, 'isDerivedFrom'):
         if scope.isDerivedFrom('App::Document'):
             print("PoM.scoped_recompute: full document, bypassing")
             return scope.recompute(None, True, True)
         scope = container_scope(scope)
    
    objects = find_features_to_recompute(current_scope())
    list1, blob, list2 = topological_sort(objects)
    if blob:
        App.Console.PrintLog("there is a dependency loop among these objects:\n") # topological_sort does not fully isolate dependency loops, it could be that there are two loops connectrd with valid dependencies
        for obj in blob:
            App.Console.PrintLog(f"  {obj.Label}")
        raise 

    if list1:
        print("PoM.scoped_recompute: recomputing")
        for it in list1:
            print("  " + it.Label)
        list1[0].Document.recompute(list1, True)
    else:
        print("PoM.scoped_recompute: list empty")
        if warn_noop:
            App.Console.PrintUserWarning("PoM scoped recompute: nothing to do")
        return 0


class DependencyLoopError(RuntimeError):
    "raised when there is a dependency loop"