import bpy
from bpy.props import BoolProperty, FloatProperty, IntProperty, EnumProperty, FloatVectorProperty, StringProperty, \
    IntVectorProperty

list_addon_keymaps = []


class VoronoiAddonPrefs(bpy.types.AddonPreferences):
    bl_idname = __package__

    ds_line_width: IntProperty(name='Line Width', default=1, min=1, max=16, subtype='FACTOR')
    ds_point_offset_x: FloatProperty(name='Point offset X', default=20, min=-50, max=50)
    ds_point_resolution: IntProperty(name='Point resolution', default=54, min=3, max=64)
    ds_point_radius: FloatProperty(name='Point radius scale', default=1, min=0, max=3)
    ds_is_draw_sk_text: BoolProperty(name='Text', default=True)
    ds_is_colored_sk_text: BoolProperty(name='Text', default=True)
    ds_is_draw_marker: BoolProperty(name='Markers', default=True)
    ds_is_colored_marker: BoolProperty(name='Markers', default=True)
    ds_is_draw_point: BoolProperty(name='Points', default=True)
    ds_is_colored_point: BoolProperty(name='Points', default=True)
    ds_is_draw_line: BoolProperty(name='Line', default=True)
    ds_is_colored_line: BoolProperty(name='Line', default=True)
    ds_is_draw_area: BoolProperty(name='Socket Area', default=True)
    ds_is_colored_area: BoolProperty(name='Socket Area', default=True)
    ds_text_style: EnumProperty(name='Text Frame Style', default='Classic',
                                items={('Classic', 'Classic', ''), ('Simplified', 'Simplified', ''),
                                       ('Text', 'Only text', '')})

    vlds_is_always_line: BoolProperty(name='Always draw line for VoronoiLinker', default=False)
    vm_preview_hk_inverse: BoolProperty(name='Previews hotkey inverse', default=False)
    vm_is_one_skip: BoolProperty(name='One Choise to skip', default=True,
                                 description='If the selection contains a single element, skip the selection and add it immediately')
    vm_menu_style: EnumProperty(name='Mixer Menu Style', default='Pie',
                                items={('Pie', 'Pie', ''), ('List', 'List', '')})
    vp_is_live_preview: BoolProperty(name='Live Preview', default=True)
    vp_select_previewed_node: BoolProperty(name='Select Previewed Node', default=True,
                                           description='Select and set acttive for node that was used by VoronoiPreview')
    ds_text_frame_offset: IntProperty(name='Text Frame Offset', default=0, min=0, max=24, subtype='FACTOR')
    ds_font_size: IntProperty(name='Text Size', default=28, min=10, max=48)
    a_display_advanced: BoolProperty(name='Display advanced options', default=False)
    ds_text_dist_from_cursor: FloatProperty(name='Text distance from cursor', default=25, min=5, max=50)
    ds_text_lineframe_offset: FloatProperty(name='Text Line-frame offset', default=2, min=0, max=10)
    ds_is_draw_sk_text_shadow: BoolProperty(name='Draw Text Shadow', default=True)
    ds_shadow_col: FloatVectorProperty(name='Shadow Color', default=[0.0, 0.0, 0.0, .5], size=4, min=0, max=1,
                                       subtype='COLOR')
    ds_shadow_offset: IntVectorProperty(name='Shadow Offset', default=[2, -2], size=2, min=-20, max=20)
    ds_shadow_blur: IntProperty(name='Shadow Blur', default=2, min=0, max=2)
    va_allow_classic_compos_viewer: BoolProperty(name='Allow classic Compositor viewer', default=False)
    va_allow_classic_geo_viewer: BoolProperty(name='Allow classic GeoNodes viewer', default=True)
    vh_draw_text_for_unhide: BoolProperty(name='Draw text for unhide node', default=False)
    ds_is_draw_debug: BoolProperty(name='draw debug', default=False)
    fm_is_included: BoolProperty(name='Include Fast Math Pie', default=True)
    fm_is_empty_hold: BoolProperty(name='Empty placeholders', default=True)
    fm_trigger_activate: EnumProperty(name='Activate trigger', default='FMA0',
                                      items={('FMA0', 'If at least one is a math socket', ''),
                                             ('FMA1', 'If everyone is a math socket', '')})

    def draw(self, context):
        col0 = self.layout.column()
        col1 = col0.column(align=True)
        col1.prop(self, 'va_allow_classic_compos_viewer')
        col1.prop(self, 'va_allow_classic_geo_viewer')
        box = col0.box()
        col1 = box.column(align=True)
        col1.label(text='Draw settings:')
        col1.prop(self, 'ds_point_offset_x')
        col1.prop(self, 'ds_text_frame_offset')
        col1.prop(self, 'ds_font_size')
        box = col1.box()
        box.prop(self, 'a_display_advanced')
        if self.a_display_advanced:
            col2 = box.column()
            col3 = col2.column(align=True)
            col3.prop(self, 'ds_line_width')
            col3.prop(self, 'ds_point_radius')
            col3.prop(self, 'ds_point_resolution')
            col3 = col2.column(align=True)
            col3.prop(self, 'ds_text_dist_from_cursor')
            col3.prop(self, 'ds_text_lineframe_offset')
            col3 = col2.column(align=True)
            box = col2.box()
            col4 = box.column()
            col4.prop(self, 'ds_is_draw_sk_text_shadow')
            if self.ds_is_draw_sk_text_shadow:
                row = col4.row(align=True)
                row.prop(self, 'ds_shadow_col')
                row = col4.row(align=True)
                row.prop(self, 'ds_shadow_offset')
                col4.prop(self, 'ds_shadow_blur')
            col2.prop(self, 'ds_is_draw_debug')

        row = col1.row()
        row.use_property_split = True
        col_split1 = row.column(heading='Draw')
        col_split1.prop(self, 'ds_is_draw_sk_text')
        col_split1.prop(self, 'ds_is_draw_marker')
        col_split1.prop(self, 'ds_is_draw_point')
        col_split1.prop(self, 'ds_is_draw_line')
        col_split1.prop(self, 'ds_is_draw_area')

        col_split2 = row.column(heading='Color')
        col_split2.prop(self, 'ds_is_colored_sk_text')
        col_split2.prop(self, 'ds_is_colored_marker')
        col_split2.prop(self, 'ds_is_colored_point')
        col_split2.prop(self, 'ds_is_colored_line')
        col_split2.prop(self, 'ds_is_colored_area')

        col1.prop(self, 'ds_text_style')
        col1.prop(self, 'vlds_is_always_line')
        box = col0.box()
        col1 = box.column(align=True)
        col1.label(text='Mixer settings:')
        col1.prop(self, 'vm_menu_style')
        col1.prop(self, 'vm_is_one_skip')
        box = box.box()
        col1 = box.column(align=True)
        col1.prop(self, 'fm_is_included')
        if self.fm_is_included:
            box = col1.box()
            col1 = box.column(align=True)
            col1.prop(self, 'fm_trigger_activate')
            col1.prop(self, 'fm_is_empty_hold')
        box = col0.box()
        col1 = box.column(align=True)
        col1.label(text='Preview settings:')
        col1.prop(self, 'vp_is_live_preview')
        col1.prop(self, 'vp_select_previewed_node')
        col1.prop(self, 'vm_preview_hk_inverse')
        box = col0.box()
        col1 = box.column(align=True)
        col1.label(text='Hider settings:')
        col1.prop(self, 'vh_draw_text_for_unhide')


from .ops import (
    NODE_OT_voronoi_linker,
    NODE_OT_voronoi_mass_linker,
    NODE_OT_voronoi_mixer,
    NODE_OT_voronoi_previewer,
    NODE_OT_voronoi_hider,
)

kmi_defs = ((NODE_OT_voronoi_linker.bl_idname, 'RIGHTMOUSE', False, False, True),
            (NODE_OT_voronoi_mass_linker.bl_idname, 'RIGHTMOUSE', True, True, True),
            (NODE_OT_voronoi_mixer.bl_idname, 'RIGHTMOUSE', True, False, True),
            (NODE_OT_voronoi_previewer.bl_idname, 'LEFTMOUSE', True, True, False),
            (NODE_OT_voronoi_previewer.bl_idname, 'RIGHTMOUSE', True, True, False),
            (NODE_OT_voronoi_hider.bl_idname, 'E', True, False, False),
            (NODE_OT_voronoi_hider.bl_idname, 'E', True, True, False))


def register():
    km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
    for (bl_id, key, Shift, Ctrl, Alt) in kmi_defs:
        kmi = km.keymap_items.new(idname=bl_id, type=key, value='PRESS', shift=Shift, ctrl=Ctrl,
                                  alt=Alt)
        list_addon_keymaps.append((km, kmi))

    bpy.utils.register_class(VoronoiAddonPrefs)


def unregister():
    for km, kmi in list_addon_keymaps:
        km.keymap_items.remove(kmi)
    list_addon_keymaps.clear()

    bpy.utils.unregister_class(VoronoiAddonPrefs)
