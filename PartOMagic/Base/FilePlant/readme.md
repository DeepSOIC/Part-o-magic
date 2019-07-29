# FilePlant

## What?

FilePlant is a FCStd file parser/reader/writer utility. It is mostly a pure python implementation, with only a few places where FreeCAD is needed, and can potentially be stripped off of Part-o-magic into a standalone python module that doesn't need FreeCAD at all.

## Features

* read an FCStd file and browse objects and properties.

	#load project "a_Project.FCStd" (it's a file path) and print out label of object named "Sketch" 
	from PartOMagic.Base.FilePlant import FCProject
	prj = FCProject.load("a_Project.FCStd")
	print(prj.Object("Sketch").Property("Label").value)

* with ViewProvider support

	#load project "a_Project.FCStd" (it's a file path) and print out if "Sketch" is visible 
	from PartOMagic.Base.FilePlant import FCProject
	prj = FCProject.load("a_Project.FCStd")
	print(prj.Object("Sketch").ViewObject.Property("Visibility").value) #doesn't work, but only because there is no parser for boolean property type yet

* modify objects in FCStd files

	#load project "a_Project.FCStd" (it's a file path) and change label of "Sketch" to "The Greatest Sketch ever" 
	from PartOMagic.Base.FilePlant import FCProject
	prj = FCProject.load("a_Project.FCStd")
	prj.Object("Sketch").Property("Label").value = "The Greatest Sketch ever"
	prj.writeFile("a_Project.FCStd")

* write out objects in a currently loaded project as FCStd files

	#writes out the object named "Sketch" from project opened in FreeCAD, into a file named "Sketch.FCStd".
	from PartOMagic.Base.FilePlant import FCProject
	prj = FCProject.fromFC(FreeCAD.ActiveDocument,["Sketch"])
	prj.purgeDeadLinks() #optional
	prj.writeFile("Sketch.FCStd")

* update objects in currently opened FC project using data from an object in an FCStd file

	#updates "Sketch" in current project with data from "Sketch002" object stored in "AnotherProject.FCStd" file
	prj = FCProject.load("AnotherProject.FCStd")
	prj.Object("Sketch002").updateFCObject(App.ActiveDocument.Sketch)

* merge projects without loading them into FreeCAD:

	prj1 = FCProject.load("Project1.FCStd")
	prj2 = FCProject.load("Project2.FCStd")
	prj1.merge(prj2)
	prj1.writeFile("Merged.FCStd")

* rename objects in FCStd files, taking care to remap links




