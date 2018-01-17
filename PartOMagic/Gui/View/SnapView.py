import FreeCAD as App
Plm = App.Placement
Rot = App.Rotation
V = App.Vector



def snapRot(rot):
    """snapRot(rot): returns tuple (new_rotation, action_done).
    action_done is either 'untilt', 'std', or 'nothing'."""
    view_dirs = [
        V( 1, 0,0),
        V( 1, 1,0),
        V( 0, 1,0),
        V(-1, 1,0),
        V(-1, 0,0),
        V(-1,-1,0),
        V( 0,-1,0),
        V( 1,-1,0),

        V( 1, 0,1),
        V( 1, 1,1),
        V( 0, 1,1),
        V(-1, 1,1),
        V(-1, 0,1),
        V(-1,-1,1),
        V( 0,-1,1),
        V( 1,-1,1),

        V( 1, 0,-1),
        V( 1, 1,-1),
        V( 0, 1,-1),
        V(-1, 1,-1),
        V(-1, 0,-1),
        V(-1,-1,-1),
        V( 0,-1,-1),
        V( 1,-1,-1),

        V(0,0,1),
        V(0,0,-1)
        ]

    for v in view_dirs:
        v.normalize()
        
    view_dir = rot.multVec(V(0,0,-1)) #current view direction
    
    rot_upright = Rot(V(),V(0,0,1),view_dir*(-1), "ZYX")
    
    if rots_equal(rot, rot_upright):
        # view is already upright. Align it to nearest standard view.
        v_nearest = V()
        for v in view_dirs:
            if (v - view_dir).Length < (v_nearest - view_dir).Length:
                v_nearest = v

        new_view_rot = Rot(V(),V(),v_nearest*(-1))
        changed = not rots_equal(new_view_rot, rot)
        return (new_view_rot, 'std' if changed else 'nothing')
    else:
        # view is not upright (tilted). Remove the tilt, keeping view direction.
        return (rot_upright, 'untilt')

orig_rot = None
last_seen_rot = None

def snapView():
    global orig_rot
    global last_seen_rot
    
    import FreeCADGui as Gui
    rot = Gui.ActiveDocument.ActiveView.getCameraOrientation()
    rotated_by_user = last_seen_rot is None or not rots_equal(rot, last_seen_rot)
    
    new_rot, act = snapRot(rot)
    if act == 'nothing':
        if orig_rot is not None:
            new_rot = orig_rot
            orig_rot = None
    else:
        if rotated_by_user:
            orig_rot = rot
    Gui.ActiveDocument.ActiveView.setCameraOrientation(new_rot)    
    last_seen_rot = new_rot if act != 'nothing' else None

def rots_equal(rot1, rot2):
    q1 = rot1.Q
    q2 = rot2.Q
    # rotations are equal if q1 == q2 or q1 == -q2. 
    # Invert one of Q's if their scalar product is negative, before comparison.
    if q1[0]*q2[0] + q1[1]*q2[1] + q1[2]*q2[2] + q1[3]*q2[3] < 0:
        q2 = [-v for v in q2]
    rot_eq = (  abs(q1[0]-q2[0]) + 
                abs(q1[1]-q2[1]) + 
                abs(q1[2]-q2[2]) + 
                abs(q1[3]-q2[3])  ) < 1e-4   # 1e-4 is a made-up number. This much camera rotation should be unnoticeable.
    return rot_eq


# =================command====================


from PartOMagic.Gui.AACommand import AACommand, CommandError
commands = []

class CommandSnapView(AACommand):
    "Command to straighten up view"
    def GetResources(self):
        import PartDesignGui
        return {'CommandName': 'PartOMagic_SnapView',
                'Pixmap'  : self.getIconPath("PartOMagic_SnapView.svg"),
                'MenuText': "Straighten camera (tri-state)",
                'Accel': "",
                'ToolTip': "Straighten camera (tri-state). First click aligns camera upright without changing view direction. Second click snaps to nearest standard view. Third click restores original view.",
                'CmdType': 'ForEdit'}
        
    def RunOrTest(self, b_run):
        import FreeCADGui as Gui
        if Gui.ActiveDocument is None:
            raise CommandError(self, "No open project")
        if not hasattr(Gui.ActiveDocument.ActiveView, 'getCameraOrientation'):
            raise CommandError(self, "Not 3d view")
        if b_run:
            Gui.addModule('PartOMagic.Gui.View.SnapView')
            Gui.doCommand('PartOMagic.Gui.View.SnapView.snapView()')

commandSnapView = CommandSnapView()
commands.append(commandSnapView)


exportedCommands = AACommand.registerCommands(commands)