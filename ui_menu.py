import bpy

class VL_MT_math_sub_menu(bpy.types.Menu):
    bl_label = 'my materials'
    bl_idname = 'VL_MT_math_sub_menu'

    def draw(self, context):
        layout = self.layout

        layout.label("This is a submenu")
        layout.operator("render.render")


class VL_MT_math_main_menu(bpy.types.Menu):
    bl_label = 'my materials'
    bl_idname = 'view3d.mymenu'

    def draw(self, context):
        layout = self.layout

        layout.label("This is a main menu")
        layout.menu(VL_MT_math_sub_menu.bl_idname)
        layout.operator("render.render")

def register():
    bpy.utils.register_class(VL_MT_math_sub_menu)
    bpy.utils.register_class(VL_MT_math_main_menu)

def unregister():
    bpy.utils.unregister_class(VL_MT_math_sub_menu)
    bpy.utils.unregister_class(VL_MT_math_main_menu)