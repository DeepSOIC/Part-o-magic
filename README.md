# Part-o-magic

PoM is an experimental add-on module for FreeCAD v0.21, that changes behavior across whole FreeCAD to embrace Active Container, allowing one to easily focus on a piece of a large project.

PoM's main features are:

* all new objects are added to active Part/Body/other_container. From all workbenches.

* visibility automation for active container. 
When you activate a Body, PoM automatically hides everything else. 
When you are finished and deactivate it, everything is shown back again, while the inner things of the body such as sketches and datum planes are hidden.

* Module container, which is PartDesign Body but for Part workbench (and Draft, and Sketcher, and Lattice2, and so on).

* container-aware duplication tool

* object replacement tool

Beware. 
Part-o-magic is an epic hack. 
It will collide (collides already) with similar functionality in FreeCAD as it is introduced. 
If you experience problems: switch to Part-o-magic workbench, and disable Observer. 
This turns off Part-o-magic's functions that affect the whole FreeCAD, but lets you still recompute your project with PoM features in it.

![figure](https://raw.githubusercontent.com/wiki/DeepSOIC/Part-o-magic/pictures/rotating-plate.png)

# Install

If you are on FreeCAD 0.21 - just install master branch of Part-o-magic with addon manager:

1. Launch FreeCAD. 
2. In menu, pick Tools->Addon Manager. 
3. Select Part-o-magic in the list, and click Install.
4. Restart FreeCAD.

After restart, you should notice: 
* Part-o-magic workbench should appear in the workbench selector. 
* A small global toolbar with a selection of Part-o-magic tools should appear. 
* Behavior of PartDesign workbench should change drastically - that is due to Observer running.

If you are on FreeCAD 0.20 and older: install [release-1.0.0](https://github.com/DeepSOIC/Part-o-magic/releases/tag/v1.0.0).

Since this cannot be done with Addon Manager, you'll have to do it manually.

1. download [source code zip file](https://github.com/DeepSOIC/Part-o-magic/archive/refs/tags/v1.0.0.zip)
2. unpack the content of `Part-o-magic-1.0.0` folder within the zip into a folder named `Part-o-magic` in where FreeCAD can pick it up as a module (for example, on Windows, it's `%appdata%/FreeCAD/Mod`)
3. Done! Run FreecAD, you should see Part-o-Magic workbench in the list, and the global toolbar.
4. (to verify you have the right PoM version) create a new project, and create a Module container from Part-o-magic workbench. If it is created without errors, you are running the correct version.

# Uninstall

Just use Addon Manager.

BTW, if you just find the invasive nature of PoM unacceptable, you can just disable PoM Observer instead of completely uninstalling the workbench. 
Switch to PoM and press Stop button on the toolbar. 
This turns off all the invasive automation stuff, but features of part-o-magic can still be recomputed in your projects that have them.

If you completely uninstall the workbench (delete Mod/Part-o-magic folder), part-o-magic features you used in your projects will stop working.

Important. 
Part-o-magic messes with "DisplayModeBody" properties of PartDesign Body objects. 
If you uninstall Part-o-magic, or disable Observer, it will cause somewhat unusual behavior of any projects that were saved with part-o-magic enabled and had any container objects present. 
You can reset them manually with property editor, or run this simple snippet in Py console:

    for obj in App.ActiveDocument.Objects:
        if hasattr(obj.ViewObject, "DisplayModeBody"):
            obj.ViewObject.DisplayModeBody = "Through"
        if hasattr(obj.ViewObject, "Selectable"):
            obj.ViewObject.Selectable = True

# list of features

## "Observer"

### Active container everywhere

In PartDesign, all new features are automatically added to Body. Observer expands this to all workbenches of FreeCAD: new objects, made in any workbench, are automatically added to active container. 

That works (well, it should) in absolutely every workbench, including add-on workbenches and macros!

### Visibility automation

When you activate a container, the container is switched into Through mode, so you see individual contained objects.
When you leave it, you see only the final shape (Tip), but not contained objects. Also, when you activate a container, anything outside of it is automatically hidden, so that you can focus on editing the piece.

### Tree automation

when you activate a container, it is automatically expanded in tree. When deactivated, it is automatically collapsed. With the aim to show you only the features that make up the container, so that you can focus on editing the piece.

### Editing automation

When you try to edit a feature, PoM will check if the container of the feature is active, and activate it. (as of now, it has to cancel the editing, so please invoke the edititng again). If the right container is not activated, you may not even see the feature.

## Containers

### Module container

It's an analog of PartDesign Body, but for Part and other workbenches. It groups together features that were used to create a final shape, and exposes the final shape (Tip) as its own. 

When you enter module, you can edit it - add new features from any workbench, including PartDesign Bodies, in order to arrive to the final result shape (typically a solid, but it can be any other type of b-rep shape). When you leave Module, you see Module as the final result. The final result is shape copied from Tip object. Tip object can be assigned with Set Tip tool in PoM.

### ShapeGroup container 

ShapeGroup similar to Module, but it can expose multiple objects to the outside. 

It is somewhat similar to what is called a "group" in vector graphics software. You can group up existing objects, and enter a group to modify its contents (as well as add new objects).

It also can do an operation between objects to be exposed, for example fusing them together into one.

### PartDesign Additive shape, PartDesign Subtractive shape containers

These are just like Modules, but they integrate themselves as PartDesign features. They allow to integrate other workbench tools into PartDesign workflow.

### Ghost (obsolete)

Obsolete! Ghost tool still works, but is obsolete, because 1) FreeCAD's Shapebinder supports it too now; 2) FreeCAD's Subshape Link does that too.  

Ghost is a placement-aware version of shapebinder. It is a tool to bring a copy of a shape from one container into another, applying a proper transform.

Ghost supports both extracting an object from a container, and importing an object from a higher-level container. The latter is somewhat limited: it will not work properly if Placement of the container the Ghost is in, changes as a result of a recompute (for example if there is an expression bound to the placement).

### Morph container tool

Created a Module, but later realized you want ShapeGroup instead? Of course, you can create a new container, drag-drop stuff... The "Morph container" tool is for simplifying the process. It takes care of moving stuff, redirecting links, and deletion of the remaining old empty container.

## Other features

* Set Tip. Works on PartDesign Bodies and Module-like things.

* Enter and Leave. Work on almost everything (can be used to enter/leave containers, and edit objects (e.g. open a sketch)).

* Exporter feature, for keeping exported files up to date with project.

* an advanced Object Replacement tool, with container support, and UI to pick specific replacements.

* X-ray tool. For getting through objects to select concealed objects.

* Align View, a one-button replacement for standard view buttons.

* Object duplication tool that can duplicate containers without causing a mess.

# Should I use PoM?

FreeCAD's evolution (as of v0.20) has somewhat diverged from Part-o-magic's concept of how things should work. But Part-o-magic way of modeling still works in 0.21, and a bunch of tools offered by PoM are still valuable.

Part-o-magic's tools to disable Observer were made to allow you continue to use projects you made with PoM, even when FreeCAD progress renders PoM obsolete. So you can at least be a little bit confident that ShapeGroup feature won't quickly go bust.
