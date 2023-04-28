import bpy
from bpy.types import Operator
from bpy.app.translations import pgettext_iface as tip_

from .draw_utils.bl_ui_draw_op import BL_UI_OT_draw_operator
from .draw_utils.bl_ui_button import BL_UI_Button
from .draw_utils.bl_ui_drag_panel import BL_UI_Drag_Panel
from .draw_utils.bl_ui_textbox import BL_UI_Textbox

from .utils import get_all_nodes, filter_context_node, get_theme_cat_color, darker_color

node_cat = {}


class VL_OT_drag_menus(BL_UI_OT_draw_operator, Operator):
    bl_idname = 'vl.drag_menus'
    bl_label = 'Drag Menus'
    # bl_options = {'UNDO_GROUPED', 'INTERNAL', 'BLOCKING', 'GRAB_CURSOR'}

    buttons = list()
    draw_area = "NODE_EDITOR"
    area_y = 0

    def __init__(self):
        super().__init__()
        self.buttons.clear()

        # 面板提示
        self.panel = BL_UI_Drag_Panel(100, 300, 300, 290)
        self.panel.bg_color = 0.2, 0.2, 0.2, 0.9

        self.search_bar = BL_UI_Textbox(10, 50, 120, 50)
        self.search_bar.bg_color = 0.5, 0.5, 0.5, 0.9
        self.search_bar.text_size = 30

        nodes = filter_context_node(get_all_nodes())

        i = 0
        # print(nodes)
        for index, (cat, nodeid_label) in enumerate(nodes.items()):
            for node_id, node_label in nodeid_label.items():
                x, y = 20, 30 + i * 30
                i += 1
                btn = BL_UI_Button(x, y, 120, 30)
                # btn.bg_color = (0.1, 0.1, 0.1, 0.8)
                # btn.hover_bg_color = (0.6, 0.6, 0.6, 0.8)
                clr = get_theme_cat_color(node_id)
                btn.bg_color = darker_color(clr, factor=0.6)
                btn.hover_bg_color = clr
                btn.text = tip_(node_label)

                # button1.set_image("//img/scale_24.png")
                # self.button1.set_image_size((24,24))
                # button1.set_image_position((4, 2))
                btn.set_mouse_down(self.add_node, node_id)

                self.buttons.append(btn)

                # init ui
                if y < 100 or y > bpy.context.area.height - 15:
                    self.hide_node_btn(btn)

        # ensure_nodegroup_asset()
        #
        # for i, (name, path) in enumerate(asset_path_dict.items()):
        #     x, y = 140, 30 + i * 30
        #
        #     btn = BL_UI_Button(x, y, 120, 30)
        #     btn.bg_color = (0.8, 0.3, 0.1, 0.8)
        #     btn.hover_bg_color = (0.6, 0.6, 0.6, 0.8)
        #     btn.text = name
        #     btn.set_mouse_down(self.add_asset_node, (name, path))
        #
        #     self.buttons.append(btn)
        #
        #     # init ui
        #     if y < 100 or y > bpy.context.area.height - 15:
        #         self.hide_node_btn(btn)

    def on_invoke(self, context, event):

        widgets_panel = []
        widgets = [self.panel]
        widgets += widgets_panel

        self.init_widgets(context, self.buttons)

        # Open the panel at the mouse location
        # self.panel.add_widgets(widgets_panel)
        # self.panel.set_location(context.area.width * 0.8,
        #                         context.area.height * 1)

    def add_node(self, node_type):
        bpy.ops.node.select_all(action='DESELECT')
        print("ADD NODE", " ", node_type)
        nt = bpy.context.space_data.edit_tree
        node = nt.nodes.new(type=node_type)
        node.location = bpy.context.space_data.cursor_location
        nt.nodes.active = node
        bpy.ops.transform.translate("INVOKE_DEFAULT", release_confirm=True)

    def add_asset_node(self, info):
        name, path = info
        print(info)

        bpy.ops.node.select_all(action='DESELECT')
        print("ADD NODE", " ", name)
        nt = bpy.context.space_data.edit_tree
        node = nt.nodes.new(type='ShaderNodeGroup')
        node.location = bpy.context.space_data.cursor_location
        nt.nodes.active = node

        ng = bpy.data.node_groups.get(name)
        if ng is None:
            with bpy.data.libraries.load(path, assets_only=True) as (data_from, data_to):
                data_to.node_groups = [name]
            ng = data_to.node_groups[0]

        node.node_tree = ng

        bpy.ops.transform.translate("INVOKE_DEFAULT", release_confirm=True)

    def hide_node_btn(self, btn):
        btn._ignore_event = True

        btn.bg_color = list(btn.bg_color[:3]) + [0]
        btn.hover_bg_color = list(btn.hover_bg_color[:3]) + [0]
        btn.text_color = list(btn.text_color[:3]) + [0]

    def show_node_btn(self, btn):
        btn._ignore_event = False

        btn.bg_color = list(btn.bg_color[:3]) + [0.8]
        btn.hover_bg_color = list(btn.hover_bg_color[:3]) + [1]
        btn.text_color = list(btn.text_color[:3]) + [1]

    def modal(self, context, event):
        if self.handle_scroll(context, event):
            return {"RUNNING_MODAL"}

        return super().modal(context, event)

    def handle_scroll(self, context, event):
        if 20 < event.mouse_region_x < 120 + 20:
            move = None
            if event.type == 'WHEELUPMOUSE':
                move = 90
            elif event.type == 'WHEELDOWNMOUSE':
                move = -90

            if move:
                for btn in self.buttons:
                    btn.get_area_height()
                    x, y = btn._textpos
                    dist_y = y + move
                    btn.update(x, dist_y)

                    # clear out
                    if dist_y < 100 or dist_y > context.area.height - 15:
                        self.hide_node_btn(btn)
                    else:
                        self.show_node_btn(btn)

                return True


def draw_menu(self, context):
    layout = self.layout
    layout.operator(VL_OT_drag_menus.bl_idname)


def register():
    bpy.utils.register_class(VL_OT_drag_menus)
    bpy.types.NODE_MT_view.prepend(draw_menu)


def unregister():
    bpy.utils.unregister_class(VL_OT_drag_menus)
    bpy.types.NODE_MT_view.remove(draw_menu)
