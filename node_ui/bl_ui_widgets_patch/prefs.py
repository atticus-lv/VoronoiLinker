# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# --- ### Header
bl_info = {"name": "BL UI Widgets",
           "description": "UI Widgets to draw in the 3D view",
           "author": "Marcelo M. Marques (fork of Jayanam's original project)",
           "version": (1, 0, 2),
           "blender": (2, 80, 75),
           "location": "View3D > viewport area",
           "support": "COMMUNITY",
           "category": "3D View",
           "warning": "Version numbering diverges from Jayanam's original project",
           "doc_url": "https://github.com/mmmrqs/bl_ui_widgets",
           "tracker_url": "https://github.com/mmmrqs/bl_ui_widgets/issues"
           }

# --- ### Change log

# v1.0.2 (10.31.2021) - by Marcelo M. Marques
# Chang: the logic that retrieves region.width of the 3d view screen which has the Remote Control

# v1.0.1 (09.20.2021) - by Marcelo M. Marques
# Chang: just some pep8 code formatting

# v1.0.0 (09.01.2021) - by Marcelo M. Marques
# Added: initial creation

# --- ### Imports
import bpy

from bpy.types import AddonPreferences, Operator
from bpy.props import StringProperty, IntProperty, BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty

from . bl_ui_draw_op import get_3d_area_and_region


class BL_UI_Widget_Preferences(AddonPreferences):
    bl_idname = __package__

    RC_UI_BIND: BoolProperty(
        name="General scaling for 'Remote Control' panel",
        description="If (ON): remote panel size changes per Blender interface's resolution scale.\nIf (OFF): remote panel size can only change per its own addon scaling factor",
        default=True
    )

    RC_SCALE: FloatProperty(
        name="",
        description="Scaling to be applied on the 'Remote Control' panel over (in addition to) the interface's resolution scale",
        default=1.0,
        max=2.00,
        min=0.50,
        soft_max=2.00,
        soft_min=0.50,
        step=1,
        precision=2,
        unit='NONE'
    )

    RC_SLIDE: BoolProperty(
        name="Keep Remote Control panel pinned when resizing viewport",
        description="If (ON): remote panel slides together with viewport's bottom border.\nIf (OFF): remote panel stays in place regardless of viewport resizing",
        default=False
    )

    RC_POSITION: BoolProperty(
        name="Remote Control panel position per scene",
        description="If (ON): remote panel initial position is the same as in the last opened scene.\nIf (OFF): remote panel remembers its position per each scene",
        default=False
    )

    RC_POS_X: IntProperty(
        name="",
        description="Remote Control panel position X from latest opened scene",
        default=-10000
    )

    RC_POS_Y: IntProperty(
        name="",
        description="Remote Control panel position Y from latest opened scene",
        default=-10000
    )

    RC_PAN_W: IntProperty(
        name="",
        description="Panel width saved on 'drag_panel_op.py'"
    )

    RC_PAN_H: IntProperty(
        name="",
        description="Panel height saved on 'drag_panel_op.py'"
    )

    def ui_scale(self, value):
        if bpy.context.preferences.addons[__package__].preferences.RC_UI_BIND:
            # From Preferences/Interface/"Display"
            return (value * bpy.context.preferences.view.ui_scale)
        else:
            return (value)

    def over_scale(self, value):
        over_scale = bpy.context.preferences.addons[__package__].preferences.RC_SCALE
        return (self.ui_scale(value) * over_scale)

    def draw(self, context):
        layout = self.layout

        split = layout.split(factor=0.45, align=True)
        split.label(text="General scaling for panel:", icon='DECORATE')
        splat = split.split(factor=0.8, align=True)
        splat.prop(self, 'RC_UI_BIND', text=" Bound to Blender's UI")

        split = layout.split(factor=0.45, align=True)
        split.label(text="User defined addon scaling:", icon='DECORATE')
        splat = split.split(factor=0.4, align=True)
        splat.prop(self, 'RC_SCALE', text="")

        split = layout.split(factor=0.45, align=True)
        split.label(text="Panel sliding option:", icon='DECORATE')
        splat = split.split(factor=0.8, align=True)
        splat.prop(self, 'RC_SLIDE', text=" Move along viewport border")

        split = layout.split(factor=0.45, align=True)
        split.label(text="Opening screen position:", icon='DECORATE')
        splat = split.split(factor=0.8, align=True)
        splat.prop(self, 'RC_POSITION', text=" Same as in the last opened scene")

        if bpy.context.scene.get("bl_ui_panel_saved_data") is None:
            coords = "x: 0    " + \
                     "y: 0    "
        else:
            panH = bpy.context.preferences.addons[__package__].preferences.RC_PAN_H     # Panel height
            pos_x = int(round(bpy.context.scene.get("bl_ui_panel_saved_data")["panX"]))
            pos_y = int(round(bpy.context.scene.get("bl_ui_panel_saved_data")["panY"]))
            # Note: Because of the scaling logic it was necessary to make this weird correction math below
            coords = "x: " + str(pos_x) + "    " + \
                     "y: " + str(pos_y + int(panH * (self.over_scale(1) - 1))) + "    "

        split = layout.split(factor=0.45, align=True)
        split.label(text="Current screen position:", icon='DECORATE')
        splat = split.split(factor=0.4, align=True)
        splat.label(text=coords)
        splot = splat.split(factor=0.455, align=True)
        splot.operator(Reset_Coords.bl_idname)

        layout.separator()
        box = layout.box()
        row = box.row(align=True)
        box.scale_y = 0.5
        box.label(text=" Additional information and Acknowledge:")
        box.label(text="")
        box.label(text=" - This addon prepared and packaged by Marcelo M Marques (mmmrqs@gmail.com)")
        box.label(text="   (upgrades at https://github.com/mmmrqs/bl_ui_widgets)")
        box.label(text=" - BL UI Widgets original project by Jayanam (jayanam.games@gmail.com)")
        box.label(text="   (download it from https://github.com/jayanam/bl_ui_widgets)")
        box.label(text="")
        box.label(text=" Special thanks to: @batFINGER, Shane Ambler (sambler), vananders, and many others,")
        box.label(text=" for their posts on the community forums, which have been crucial for making this addon.")
        box.label(text="")


class Reset_Coords(bpy.types.Operator):
    bl_idname = "object.reset_coords"
    bl_label = "Reset Pos"
    bl_description = "Resets the 'Remote Control' panel screen position for this current session only.\n" \
                     "Use this button to recover the panel if it has got stuck out of the viewport area.\n" \
                     "You will need to reopen the panel for the new screen position to take effect"

    @classmethod
    def poll(cls, context):
        return (not bpy.context.scene.get("bl_ui_panel_saved_data") is None)

    def invoke(self, context, event):
        return self.execute(context)

    def execute(self, context):
        panW = bpy.context.preferences.addons[__package__].preferences.RC_PAN_W  # Panel width
        panH = bpy.context.preferences.addons[__package__].preferences.RC_PAN_H  # Panel height
        panX = 100             # Panel X coordinate, for top-left corner (some default, case it fails below)
        panY = panH + 40 - 1   # Panel Y coordinate, for top-left corner

        region = get_3d_area_and_region(prefs=True)[1]
        if region:
            if bpy.context.preferences.addons[__package__].preferences.RC_UI_BIND:
                # From Preferences/Interface/"Display"
                ui_scale = bpy.context.preferences.view.ui_scale
            else:
                ui_scale = 1
            over_scale = bpy.context.preferences.addons[__package__].preferences.RC_SCALE
            # Need this just because I want the panel to be centered
            panX = int((region.width - (panW * ui_scale * over_scale)) / 2.0) + 1
        try:
            bpy.context.preferences.addons[__package__].preferences.RC_POS_X = panX
            bpy.context.preferences.addons[__package__].preferences.RC_POS_Y = panY
            bpy.context.scene.get("bl_ui_panel_saved_data")["panX"] = panX
            bpy.context.scene.get("bl_ui_panel_saved_data")["panY"] = panY
            bpy.context.scene.var.RemoVisible = False
            bpy.context.scene.var.btnRemoText = "Open Remote Control"
        except Exception as e:
            pass
        return {'FINISHED'}


# Registration
def register():
    bpy.utils.register_class(Reset_Coords)
    bpy.utils.register_class(BL_UI_Widget_Preferences)


def unregister():
    bpy.utils.unregister_class(BL_UI_Widget_Preferences)
    bpy.utils.unregister_class(Reset_Coords)


if __name__ == '__main__':
    register()
