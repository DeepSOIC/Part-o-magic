# Part-o-magic
PoM is an experimental add-on module for FreeCAD v0.17. (It won't work with FC v0.16.)

The goal is to experiment with UI and ways to bring assembly infrastructure into the whole FreeCAD. Saw that new PartDesign things called Part and Body? The aim of Part-o-magic is to bring similar things to every workbench in FreeCAD, and make working with them more convenient.

With Part-o-magic, organizing a multi-part project (i.e. an assembly) is much easier.

Beware. Part-o-magic is an epic hack. It will collide with similar functionality in FreeCAD as it is introduced. In case of doubt, you can always switch to Part-o-magic workbench, and disable Observer.

![figure](https://raw.githubusercontent.com/wiki/DeepSOIC/Part-o-magic/pictures/rotating-plate.png)

# Install
Scroll to top of page, and download zip.

In Path/To/Macros/Mod, create a directory named Part-o-magic, and put the contents of repository there. Restart FreeCAD. Part-o-magic workbench should appear in workbench selector.

Part-o-magic will soon be added to add-on library for easy install, hopefully =)

# Uninstall

You can disable PoM Observer, as well as the whole workbench, using buttons on the workbench. If you disable the workbench, all the automation stuff should switch off, but features of part-o-magic can still be recomputed in your projects that have them.

If you completely uninstall the workbench (delete Mod/Part-o-magic folder), part-o-magic features you used in your projects will stop working.

Important. Part-o-magic messes with "DisplayModeBody" properties of PartDesign Body objects. If you uninstall Part-o-magic, or disable its automation stuff, it will cause somewhat unusual behavior of any projects that were saved with part-o-magic enabled and had any container objects present. You can reset them manually with property editor, or run this simple snippet in Py console:

    for obj in App.ActiveDocument.Objects:
        if hasattr(obj.ViewObject, "DisplayModeBody"):
            obj.ViewObject.DisplayModeBody = "Through"
        if hasattr(obj.ViewObject, "Selectable"):
            obj.ViewObject.Selectable = True

# Main features

## "Observer"

### Active container everywhere
In PartDesign, all new features are automatically added to Body. Observer expands this to all workbenches of FreeCAD: new objects, made in any workbench, are automatically added to active container. 

That works (well, it should) in absolutely every workbench, including add-on workbenches and macros!

### Visibility automation: 
when you activate a container, the container is switched into Through mode, so you see individual contained objects. When you leave it, you see only the final shape (Tip), but not contained objects. Also, when you activate a container, anything outside of it is automatically hidden, so that you can focus on editing the piece.

### Tree automation: 
when you activate a container, it is automatically expanded in tree. When deactivated, it is automatically collapsed. With the aim to show you only the features that make up the container, so that you can focus on editing the piece.

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

## Misc features

* tool for altering Tip. Works on PartDesign Bodies and Module-like things.

* buttons to enter and leave objects. Work on almost everything (can be used to enter/leave containers, and edit objects (e.g. open a sketch)).

* button to create Part container

* button to create Shapebinders (works outside of PartDesign, too). ShapeBinders are a mean to import geometry from one container to another.

* Exporter feature, for keeping exported files up to date with project.

* buttons to disable Part-o-magic (there's a good chance part-o-magic will break soon). If PoM is disabled, PoM containers should still work, albeit not very useful because they rely on part-o-magic's automatic object addition.

# Should I use PoM?

If you are into FreeCAD projects with multiple parts, you should definitely try out Part-o-magic. Even though it doesn't yet offer actual assembly capabilities, it can help you organize your in-place modeled parts.

If you want to be on the bleeding edge of assembly capabilities of FreeCAD, you should check it out for getting a general feel of where it may be going, and give valuable feedback on what is done right in part-o-magic and you'd like to see that in assembly, and what is wrong.

Part-o-magic's tools to disable Observer were made to allow you continue to use projects you made with PoM, even when FreeCAD progress renders PoM obsolete. So you can at least be a little bit confident that ShapeGroup feature won't quickly go bust.