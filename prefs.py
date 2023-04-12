import bpy
from bpy.props import BoolProperty, FloatProperty, IntProperty, EnumProperty, FloatVectorProperty, StringProperty, \
    IntVectorProperty
import rna_keymap_ui

list_addon_keymaps = []


class VoronoiAddonPrefs(bpy.types.AddonPreferences):
    bl_idname = __package__

    ui: EnumProperty(items=[
        ('DRAW', 'Draw', 'Draw'),
        ('SETTINGS', 'Settings', 'Settings'),
        ('KEYMAP', 'Keymap', 'Keymap'),
    ])

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
                                items={('Classic', 'Default', ''),
                                       ('Simplified', 'Simple', ''),
                                       ('Text', 'Text', '')})

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
        layout = self.layout
        row = layout.row(align=True)
        row.prop(self, 'ui', expand=True)
        match self.ui:
            case 'DRAW':
                self.draw_draw(context, layout)
            case 'SETTINGS':
                self.draw_settings(context, layout)
            case 'KEYMAP':
                self.draw_keymaps(context, layout)

    def draw_draw(self, context, layout):

        layout.prop(self, 'ds_text_style')
        layout.prop(self, 'vlds_is_always_line')

        row = layout.row()
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

        box = layout.box()
        col1 = box.column(align=True)
        col1.prop(self, 'ds_point_offset_x')
        col1.prop(self, 'ds_text_frame_offset')
        col1.prop(self, 'ds_font_size')
        col1.separator()
        box = col1.box()
        box.prop(self, 'a_display_advanced', text='Advanced',
                 icon='TRIA_DOWN' if self.a_display_advanced else 'TRIA_RIGHT',emboss=False)
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
            col2.prop(self, 'ds_is_draw_debug',text = 'Debug')

    def draw_keymaps(self, context, layout):
        col = layout.column()
        # col.label(text="Keymap", icon="KEYINGSET")
        km = None
        wm = bpy.context.window_manager
        kc = wm.keyconfigs.user

        old_km_name = ""
        get_kmi_l = []

        for km_add, kmi_add in list_addon_keymaps:
            for km_con in kc.keymaps:
                if km_add.name == km_con.name:
                    km = km_con
                    break

            for kmi_con in km.keymap_items:
                if kmi_add.idname == kmi_con.idname and kmi_add.name == kmi_con.name:
                    get_kmi_l.append((km, kmi_con))

        get_kmi_l = sorted(set(get_kmi_l), key=get_kmi_l.index)

        for km, kmi in get_kmi_l:
            if not km.name == old_km_name:
                col.label(text=str(km.name), icon="DOT")

            col.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)

            old_km_name = km.name

    def draw_settings(self, context, layout):
        col1 = layout.column(align=True)
        col1.prop(self, 'va_allow_classic_compos_viewer')
        col1.prop(self, 'va_allow_classic_geo_viewer')

        box = layout.box()
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

        box = layout.box()
        col1 = box.column(align=True)
        col1.label(text='Preview settings:')
        col1.prop(self, 'vp_is_live_preview')
        col1.prop(self, 'vp_select_previewed_node')
        col1.prop(self, 'vm_preview_hk_inverse')
        box = layout.box()
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
