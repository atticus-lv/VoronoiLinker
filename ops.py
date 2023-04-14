### BEGIN LICENSE BLOCK
# I don't understand about licenses.
# Do what you want with it.
### END LICENSE BLOCK

# Этот аддон является самописом лично для меня, который я сделал публичным для всех желающих. Наслаждайтесь!
# This addon is a self-writing for me personally, which I made publicly available to everyone wishing. Enjoy!

import bpy, gpu
from bpy.props import StringProperty
from mathutils import Vector
from builtins import len as length
from bpy.app.translations import pgettext_iface as _tips

from .draw_utils import (
    gv_where, gv_shaders, gv_uifac, list_sk_perms,
    get_addon_prefs,
    set_font, ui_scale, gen_nearest_node_list, gen_nearest_sockets_list,
    pos_view_to_reg, get_sk_col, get_sk_vec_col, prepar_get_wp,
    draw_sk_text, draw_wide_point, draw_line, draw_is_linked, draw_text, draw_rectangle_on_socket,
    voronoi_Linker_draw_callback, debug_draw_callback, voronoi_mass_linker_draw_callback
)

displayWho = [0]
displayList = [[]]


class NODE_OT_voronoi_linker(bpy.types.Operator):
    bl_idname = 'node.a_voronoi_linker'
    bl_label = 'Voronoi Linker'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.area.type == 'NODE_EDITOR') and (context.space_data.edit_tree)

    def next_assign(sender, context, isBoth):
        pick_pos = context.space_data.cursor_location
        list_nodes = gen_nearest_node_list(context.space_data.edit_tree.nodes, pick_pos)
        # If not allowed, then the previous one remains, which is not convenient. Therefore, it is reset every time before the search.
        sender.list_sk_goal_in = []
        for li in list_nodes:
            nd = li[1]

            if (nd.type == 'FRAME'): continue
            if (nd.hide is True) and (nd.type != 'REROUTE'): continue

            list_socket_in, list_socket_out = gen_nearest_sockets_list(nd, pick_pos)
            # This tool will trigger on any output
            if isBoth:
                sender.list_sk_goal_out = list_socket_out[0] if list_socket_out else []
            # Get entry by conditions:
            if len(list_socket_in) == 0:  # Trigger on nodes without inputs, and reset the previous result if any.
                sender.list_sk_goal_in = []
                break  # break can be done, because there is nowhere else to look for the input.

            # The first entry is always isBoth=True, however, the node may not have exits.
            if not sender.list_sk_goal_out: break

            skout = sender.list_sk_goal_out[1]

            for lsi in list_socket_in:
                skin = lsi[1]
                # Для разрешённой-группы-между-собой разрешить "переходы". Рероутом для удобства можно в любой сокет минуя различные типы
                tgl = ((skin.type in list_sk_perms) and (skout.type in list_sk_perms) or (
                        skout.node.type == 'REROUTE'))
                # Любой сокет для виртуального выхода, разрешить в виртуальный для любого сокета. Обоим в себя запретить
                tgl = (tgl) or (
                        (skin.bl_idname == 'NodeSocketVirtual') ^ (skout.bl_idname == 'NodeSocketVirtual'))
                # Если имена типов одинаковые, но не виртуальные
                tgl = (tgl) or (skin.bl_idname == skout.bl_idname) and (
                    not ((skin.bl_idname == 'NodeSocketVirtual') and (skout.bl_idname == 'NodeSocketVirtual')))
                if tgl:
                    sender.list_sk_goal_in = lsi
                    break  # Without a break, the goal will be the furthest from the cursor that satisfies the conditions.
            # Final validation check
            if sender.list_sk_goal_in:
                if (sender.list_sk_goal_out[1].node == sender.list_sk_goal_in[1].node):
                    sender.list_sk_goal_in = []
                elif (sender.list_sk_goal_out[1].is_linked):
                    for lk in sender.list_sk_goal_out[1].links:
                        # Benefit from break is minimal, multi-inputs with many connections are rare
                        if lk.to_socket == sender.list_sk_goal_in[1]:
                            sender.list_sk_goal_in = []
                            break
            break  # Only the first closest one that meets the conditions needs to be processed.

    def link_(self, tree):
        try:
            lk = tree.links.new(self.list_sk_goal_out[1], self.list_sk_goal_in[1])
        except:
            pass  # NodeSocketUndefined

        tgl = (lk.from_socket.bl_idname == 'NodeSocketVirtual') + (
                lk.to_socket.bl_idname == 'NodeSocketVirtual') * 2

        if tgl > 0:  # In version 3.5, a new socket is not automatically created.
            if tgl == 1:
                tree.inputs.new(lk.to_socket.bl_idname, lk.to_socket.name)
                tree.links.remove(lk)
                tree.links.new(self.list_sk_goal_out[1].node.outputs[-2], self.list_sk_goal_in[1])
            else:
                tree.outputs.new(lk.from_socket.bl_idname, lk.from_socket.name)
                tree.links.remove(lk)
                tree.links.new(self.list_sk_goal_out[1], self.list_sk_goal_in[1].node.inputs[-2])

        # If multi-input - implement an adequate connection order. What is the meaning of the last being molded into the beginning?
        if self.list_sk_goal_in[1].is_multi_input:
            list_sk_links = []
            for lk in self.list_sk_goal_in[1].links:
                list_sk_links.append((lk.from_socket, lk.to_socket))
                tree.links.remove(lk)
            if self.list_sk_goal_out[1].bl_idname == 'NodeSocketVirtual':
                self.list_sk_goal_out[1] = self.list_sk_goal_out[1].node.outputs[
                    length(self.list_sk_goal_out[1].node.outputs) - 2]
            tree.links.new(self.list_sk_goal_out[1], self.list_sk_goal_in[1])
            for cyc in range(0, length(list_sk_links) - 1):
                tree.links.new(list_sk_links[cyc][0], list_sk_links[cyc][1])

    def modal(self, context, event):
        context.area.tag_redraw()
        tree = context.space_data.edit_tree

        match event.type:
            case 'MOUSEMOVE':
                NODE_OT_voronoi_linker.next_assign(self, context, False)
            case 'RIGHTMOUSE' | 'ESC':
                bpy.types.SpaceNodeEditor.draw_handler_remove(self.dcb_handle, 'WINDOW')

                if event.value != 'RELEASE' or not self.list_sk_goal_in or not self.list_sk_goal_out:
                    return {'CANCELLED'}

                self.link_(tree)

                return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.list_sk_goal_out = []
        self.list_sk_goal_in = []
        gv_uifac[0] = ui_scale()
        gv_where[0] = context.space_data
        set_font()
        context.area.tag_redraw()
        NODE_OT_voronoi_linker.next_assign(self, context, True)
        self.dcb_handle = bpy.types.SpaceNodeEditor.draw_handler_add(voronoi_Linker_draw_callback, (self, context),
                                                                     'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class NODE_OT_voronoi_mass_linker(bpy.types.Operator):
    bl_idname = 'node.a_voronoi_masslinker'
    bl_label = 'Voronoi Linker'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.area.type == 'NODE_EDITOR') and (context.space_data.edit_tree)

    def next_assign(sender, context, isBoth):
        pick_pos = context.space_data.cursor_location
        list_nodes = gen_nearest_node_list(context.space_data.edit_tree.nodes, pick_pos)
        for li in list_nodes:
            nd = li[1]
            if (nd.type == 'FRAME') or ((nd.hide is True) and (nd.type != 'REROUTE')): continue
            sender.nd_goal_in = nd
            if isBoth:
                sender.nd_goal_out = nd
            break
        if sender.nd_goal_out == sender.nd_goal_in:
            sender.nd_goal_in = None

    def modal(self, context, event):
        context.area.tag_redraw()
        match event.type:
            case 'MOUSEMOVE':
                NODE_OT_voronoi_mass_linker.next_assign(self, context, False)
            case 'RIGHTMOUSE' | 'ESC':
                bpy.types.SpaceNodeEditor.draw_handler_remove(self.dcb_handle, 'WINDOW')
                if (event.value != 'RELEASE') or (self.nd_goal_out is None) or (self.nd_goal_in is None): return {
                    'CANCELLED'}
                tree = context.space_data.edit_tree
                for lsks in self.list_equalSks:
                    try:
                        tree.links.new(lsks[0][1], lsks[1][1])
                    except:
                        pass
                return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.nd_goal_out = None
        self.nd_goal_in = None
        gv_uifac[0] = ui_scale()
        gv_where[0] = context.space_data
        set_font()
        context.area.tag_redraw()
        NODE_OT_voronoi_mass_linker.next_assign(self, context, True)
        self.dcb_handle = bpy.types.SpaceNodeEditor.draw_handler_add(voronoi_mass_linker_draw_callback, (self, context),
                                                                     'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


def voronoi_mixer_draw_callback(sender, context):
    if gv_where[0] != context.space_data:
        return
    gv_shaders[0] = gpu.shader.from_builtin('2D_SMOOTH_COLOR')
    gv_shaders[1] = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    # bgl.glHint(bgl.GL_LINE_SMOOTH_HINT, bgl.GL_NICEST)
    mouse_pos = context.space_data.cursor_location * gv_uifac[0]
    mouse_region_pos = pos_view_to_reg(mouse_pos.x, mouse_pos.y)
    lw = get_addon_prefs().ds_line_width
    if get_addon_prefs().ds_is_draw_debug:
        debug_draw_callback(sender, context)
        return

    def MixerDrawSk(Sk, ys, lys):
        txtdim = draw_sk_text(pos_view_to_reg(mouse_pos.x, mouse_pos.y), get_addon_prefs().ds_text_dist_from_cursor, ys,
                              Sk)
        if Sk.is_linked:
            draw_is_linked(mouse_pos, txtdim[0], txtdim[1] * lys * .75,
                           get_sk_col(Sk) if get_addon_prefs().ds_is_colored_marker else (.9, .9, .9, 1))

    if (sender.list_sk_goal_out1 == []):
        if get_addon_prefs().ds_is_draw_point:
            wp1 = prepar_get_wp(mouse_pos, -get_addon_prefs().ds_point_offset_x * .75)
            wp2 = prepar_get_wp(mouse_pos, get_addon_prefs().ds_point_offset_x * .75)
            draw_wide_point(wp1[0], wp1[1])
            draw_wide_point(wp2[0], wp2[1])
    elif (sender.list_sk_goal_out1) and (sender.list_sk_goal_out2 == []):
        draw_rectangle_on_socket(sender.list_sk_goal_out1[1], sender.list_sk_goal_out1[3],
                                 get_sk_vec_col(sender.list_sk_goal_out1[1], 2.2))
        wp1 = prepar_get_wp(sender.list_sk_goal_out1[2] * gv_uifac[0], get_addon_prefs().ds_point_offset_x)
        wp2 = prepar_get_wp(mouse_pos, 0)
        col = Vector((1, 1, 1, 1))
        if get_addon_prefs().ds_is_draw_line:
            draw_line(wp1[0], mouse_region_pos, lw,
                      get_sk_col(sender.list_sk_goal_out1[1]) if get_addon_prefs().ds_is_colored_line else col, col)
        if get_addon_prefs().ds_is_draw_point:
            draw_wide_point(wp1[0], wp1[1], get_sk_vec_col(sender.list_sk_goal_out1[1], 2.2))
            draw_wide_point(wp2[0], wp2[1])
        MixerDrawSk(sender.list_sk_goal_out1[1], -.5, 0)
    else:
        draw_rectangle_on_socket(sender.list_sk_goal_out1[1], sender.list_sk_goal_out1[3],
                                 get_sk_vec_col(sender.list_sk_goal_out1[1], 2.2))
        draw_rectangle_on_socket(sender.list_sk_goal_out2[1], sender.list_sk_goal_out2[3],
                                 get_sk_vec_col(sender.list_sk_goal_out2[1], 2.2))
        if get_addon_prefs().ds_is_colored_line:
            col1 = get_sk_col(sender.list_sk_goal_out1[1])
            col2 = get_sk_col(sender.list_sk_goal_out2[1])
        else:
            col1 = (1, 1, 1, 1)
            col2 = (1, 1, 1, 1)
        wp1 = prepar_get_wp(sender.list_sk_goal_out1[2] * gv_uifac[0], get_addon_prefs().ds_point_offset_x)
        wp2 = prepar_get_wp(sender.list_sk_goal_out2[2] * gv_uifac[0], get_addon_prefs().ds_point_offset_x)
        if get_addon_prefs().ds_is_draw_line:
            draw_line(mouse_region_pos, wp2[0], lw, col2, col2)
            draw_line(wp1[0], mouse_region_pos, lw, col1, col1)
        if get_addon_prefs().ds_is_draw_point:
            draw_wide_point(wp1[0], wp1[1], get_sk_vec_col(sender.list_sk_goal_out1[1], 2.2))
            draw_wide_point(wp2[0], wp2[1], get_sk_vec_col(sender.list_sk_goal_out2[1], 2.2))
        MixerDrawSk(sender.list_sk_goal_out1[1], .25, 1)
        MixerDrawSk(sender.list_sk_goal_out2[1], -1.25, -1)


class NODE_OT_voronoi_mixer(bpy.types.Operator):
    bl_idname = 'node.a_voronoi_mixer'
    bl_label = 'Voronoi Mixer'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.area.type == 'NODE_EDITOR' and context.space_data.edit_tree

    def next_assign(sender, context, isBoth):
        pick_pos = context.space_data.cursor_location
        list_nodes = gen_nearest_node_list(context.space_data.edit_tree.nodes, pick_pos)
        for li in list_nodes:
            nd = li[1]
            if (nd.type == 'FRAME') or ((nd.hide is True) and (nd.type != 'REROUTE')):
                continue
            list_socket_in, list_socket_out = gen_nearest_sockets_list(nd, pick_pos)
            # Этот инструмент триггерится на любой выход для первого
            if isBoth:
                sender.list_sk_goal_out1 = list_socket_out[0] if list_socket_out else []
            # Для второго по условиям:
            skout1 = sender.list_sk_goal_out1[1] if sender.list_sk_goal_out1 else None

            if not skout1: break

            for lso in list_socket_out:
                skout2 = lso[1]
                # Критерии типов у Миксера такие же, как и в Линкере
                tgl = ((skout2.type in list_sk_perms) and (skout1.type in list_sk_perms) or (
                        skout1.node.type == 'REROUTE'))
                tgl = (tgl) or ((skout2.bl_idname == 'NodeSocketVirtual') ^ (
                        skout1.bl_idname == 'NodeSocketVirtual'))
                tgl = (tgl) or (skout2.bl_idname == skout1.bl_idname) and (not (
                        (skout2.bl_idname == 'NodeSocketVirtual') and (
                        skout1.bl_idname == 'NodeSocketVirtual')))
                # Добавляется разрешение для виртуальных в рамках одного нода, чтобы первый клик не выбирал сразу два сокета
                tgl = (tgl) or (skout1.bl_idname == 'NodeSocketVirtual') and (skout1.node == skout2.node)
                if tgl:
                    sender.list_sk_goal_out2 = lso
                    break
            # Финальная проверка на корректность
            if sender.list_sk_goal_out2:
                if (skout1 == sender.list_sk_goal_out2[1]):
                    sender.list_sk_goal_out2 = []
            break

    def modal(self, context, event):
        context.area.tag_redraw()
        match event.type:
            case 'MOUSEMOVE':
                NODE_OT_voronoi_mixer.next_assign(self, context, False)
            case 'RIGHTMOUSE' | 'ESC':
                bpy.types.SpaceNodeEditor.draw_handler_remove(self.dcb_handle, 'WINDOW')
                if event.value != 'RELEASE': return {'CANCELLED'}
                if (self.list_sk_goal_out1) and (self.list_sk_goal_out2):
                    mixerSks[0] = self.list_sk_goal_out1[1]
                    mixerSks[1] = self.list_sk_goal_out2[1]
                    mixerSkTyp[0] = mixerSks[0].type if mixerSks[0].bl_idname != 'NodeSocketVirtual' else mixerSks[
                        1].type
                    if get_addon_prefs().fm_is_included:
                        tgl0 = get_addon_prefs().fm_trigger_activate == 'FMA1'
                        displayWho[0] = mixerSks[0].bl_idname == 'NodeSocketVector'
                        Check = lambda sk: sk.bl_idname in ['NodeSocketFloat', 'NodeSocketVector', 'NodeSocketInt']
                        tgl1 = Check(mixerSks[0])
                        tgl2 = Check(mixerSks[1])
                        if (tgl0) and (tgl1) and (tgl2) or (not tgl0) and ((tgl1) or (tgl2)):
                            bpy.ops.node.voronoi_fastmath('INVOKE_DEFAULT')
                            return {'FINISHED'}
                    dm = dictMixerMain[context.space_data.tree_type][mixerSkTyp[0]]

                    if len(dm) == 0: return {'FINISHED'}
                    if (get_addon_prefs().vm_is_one_skip) and (len(dm) == 1):
                        do_mix(context, dm[0])
                    else:
                        if get_addon_prefs().vm_menu_style == 'Pie':
                            bpy.ops.wm.call_menu_pie(name='VL_MT_voronoi_mixer_menu')
                        else:
                            bpy.ops.wm.call_menu(name='VL_MT_voronoi_mixer_menu')

                elif (self.list_sk_goal_out1) and (self.list_sk_goal_out2 == []) and (
                        get_addon_prefs().fm_is_included):
                    mixerSks[0] = self.list_sk_goal_out1[1]
                    displayWho[0] = mixerSks[0].bl_idname == 'NodeSocketVector'
                    if mixerSks[0].bl_idname in ['NodeSocketFloat', 'NodeSocketVector', 'NodeSocketInt']:
                        bpy.ops.node.voronoi_fastmath('INVOKE_DEFAULT')
                return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):

        self.list_sk_goal_out1 = []
        self.list_sk_goal_out2 = []
        gv_uifac[0] = ui_scale()
        gv_where[0] = context.space_data
        set_font()
        context.area.tag_redraw()
        NODE_OT_voronoi_mixer.next_assign(self, context, True)
        self.dcb_handle = bpy.types.SpaceNodeEditor.draw_handler_add(voronoi_mixer_draw_callback, (self, context),
                                                                     'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


mixerSks = [None, None]
mixerSkTyp = [None]
dict_mixer_defs = {'GeometryNodeSwitch': [-1, -1, 'Switch'], 'ShaderNodeMixShader': [1, 2, 'Mix'],
                   'ShaderNodeAddShader': [0, 1, 'Add'], 'ShaderNodeMixRGB': [1, 2, 'Mix RGB'],
                   'ShaderNodeMath': [0, 1, 'Max'], 'ShaderNodeVectorMath': [0, 1, 'Max'],
                   'FunctionNodeBooleanMath': [0, 1, 'Or'], 'FunctionNodeCompare': [-1, -1, 'Compare'],
                   'GeometryNodeCurveToMesh': [0, 1, 'Curve to Mesh'],
                   'GeometryNodeInstanceOnPoints': [0, 2, 'Instance on Points'],
                   'GeometryNodeMeshBoolean': [0, 1, 'Boolean'], 'GeometryNodeStringJoin': [1, 1, 'Join'],
                   'GeometryNodeJoinGeometry': [0, 0, 'Join'], 'GeometryNodeGeometryToInstance': [0, 0, 'To Instance'],
                   'CompositorNodeMixRGB': [1, 2, 'Mix'], 'CompositorNodeMath': [0, 1, 'Max'],
                   'CompositorNodeSwitch': [0, 1, 'Switch'], 'CompositorNodeAlphaOver': [1, 2, 'Alpha Over'],
                   'CompositorNodeSplitViewer': [0, 1, 'Split Viewer'],
                   'CompositorNodeSwitchView': [0, 1, 'Switch View'], 'TextureNodeMixRGB': [1, 2, 'Mix'],
                   'TextureNodeMath': [0, 1, 'Max'], 'TextureNodeTexture': [0, 1, 'Texture'],
                   'TextureNodeDistance': [0, 1, 'Distance'], 'ShaderNodeMix': [-1, -1, 'Mix']}
dict_mixer_switch_type = {'VALUE': 'FLOAT', 'INT': 'FLOAT'}
dict_mixer_user_sk_name = {'VALUE': 'Float', 'RGBA': 'Color'}
dict_mixer_mix_int = {'INT': 'VALUE'}


def do_mix(context, who):
    tree = context.space_data.edit_tree
    if tree is None: return

    bpy.ops.node.add_node('INVOKE_DEFAULT', type=who, use_transform=True)
    active_nd = tree.nodes.active
    active_nd.width = 140
    match active_nd.bl_idname:
        case 'ShaderNodeMath' | 'ShaderNodeVectorMath' | 'CompositorNodeMath' | 'TextureNodeMath':
            active_nd.operation = 'MAXIMUM'
        case 'FunctionNodeBooleanMath':
            active_nd.operation = 'OR'
        case 'TextureNodeTexture':
            active_nd.show_preview = False
        case 'GeometryNodeSwitch':
            active_nd.input_type = dict_mixer_switch_type.get(mixerSkTyp[0], mixerSkTyp[0])
        case 'FunctionNodeCompare':
            active_nd.data_type = dict_mixer_switch_type.get(mixerSkTyp[0], mixerSkTyp[0])
            active_nd.operation = active_nd.operation if active_nd.data_type != 'FLOAT' else 'EQUAL'
        case 'ShaderNodeMix':
            active_nd.data_type = dict_mixer_switch_type.get(mixerSkTyp[0], mixerSkTyp[0])

    match active_nd.bl_idname:
        case 'GeometryNodeSwitch' | 'FunctionNodeCompare' | 'ShaderNodeMix':
            tgl = active_nd.bl_idname != 'FunctionNodeCompare'
            foundSkList = [sk for sk in (reversed(active_nd.inputs) if tgl else active_nd.inputs) if
                           sk.type == dict_mixer_mix_int.get(mixerSkTyp[0], mixerSkTyp[0])]
            tree.links.new(mixerSks[0], foundSkList[tgl])
            tree.links.new(mixerSks[1], foundSkList[not tgl])
        case _:
            if active_nd.inputs[dict_mixer_defs[active_nd.bl_idname][0]].is_multi_input:
                tree.links.new(mixerSks[1], active_nd.inputs[dict_mixer_defs[active_nd.bl_idname][1]])
            tree.links.new(mixerSks[0], active_nd.inputs[dict_mixer_defs[active_nd.bl_idname][0]])
            if active_nd.inputs[dict_mixer_defs[active_nd.bl_idname][0]].is_multi_input is False:
                tree.links.new(mixerSks[1], active_nd.inputs[dict_mixer_defs[active_nd.bl_idname][1]])


class NODE_OT_voronoi_mixer_mixer(bpy.types.Operator):
    bl_idname = 'node.voronoi_mixer_mixer'
    bl_label = 'Voronoi Mixer Mixer'
    bl_options = {'UNDO'}
    who: StringProperty()

    def execute(self, context):
        do_mix(context, self.who)
        return {'FINISHED'}


dictMixerMain = {'ShaderNodeTree': {'SHADER': ['ShaderNodeMixShader', 'ShaderNodeAddShader'],
                                    'VALUE': ['ShaderNodeMix', 'ShaderNodeMixRGB', 'ShaderNodeMath'],
                                    'RGBA': ['ShaderNodeMix', 'ShaderNodeMixRGB'],
                                    'VECTOR': ['ShaderNodeMix', 'ShaderNodeMixRGB', 'ShaderNodeVectorMath'],
                                    'INT': ['ShaderNodeMix', 'ShaderNodeMixRGB', 'ShaderNodeMath']},
                 'GeometryNodeTree': {
                     'VALUE': ['GeometryNodeSwitch', 'ShaderNodeMixRGB', 'FunctionNodeCompare', 'ShaderNodeMath'],
                     'RGBA': ['GeometryNodeSwitch', 'ShaderNodeMixRGB', 'FunctionNodeCompare'],
                     'VECTOR': ['GeometryNodeSwitch', 'ShaderNodeMixRGB', 'FunctionNodeCompare',
                                'ShaderNodeVectorMath'],
                     'STRING': ['GeometryNodeSwitch', 'FunctionNodeCompare', 'GeometryNodeStringJoin'],
                     'INT': ['GeometryNodeSwitch', 'ShaderNodeMixRGB', 'FunctionNodeCompare', 'ShaderNodeMath'],
                     'GEOMETRY': ['GeometryNodeSwitch', 'GeometryNodeJoinGeometry', 'GeometryNodeInstanceOnPoints',
                                  'GeometryNodeCurveToMesh', 'GeometryNodeMeshBoolean',
                                  'GeometryNodeGeometryToInstance'],
                     'BOOLEAN': ['GeometryNodeSwitch', 'ShaderNodeMixRGB', 'ShaderNodeMath', 'FunctionNodeBooleanMath'],
                     'OBJECT': ['GeometryNodeSwitch'], 'MATERIAL': ['GeometryNodeSwitch'],
                     'COLLECTION': ['GeometryNodeSwitch'], 'TEXTURE': ['GeometryNodeSwitch'],
                     'IMAGE': ['GeometryNodeSwitch']}, 'CompositorNodeTree': {
        'VALUE': ['CompositorNodeMixRGB', 'CompositorNodeSwitch', 'CompositorNodeSplitViewer',
                  'CompositorNodeSwitchView', 'CompositorNodeMath'],
        'RGBA': ['CompositorNodeMixRGB', 'CompositorNodeSwitch', 'CompositorNodeSplitViewer',
                 'CompositorNodeSwitchView', 'CompositorNodeAlphaOver'],
        'VECTOR': ['CompositorNodeMixRGB', 'CompositorNodeSwitch', 'CompositorNodeSplitViewer',
                   'CompositorNodeSwitchView'],
        'INT': ['CompositorNodeMixRGB', 'CompositorNodeSwitch', 'CompositorNodeSplitViewer', 'CompositorNodeSwitchView',
                'CompositorNodeMath']},
                 'TextureNodeTree': {'VALUE': ['TextureNodeMixRGB', 'TextureNodeMath', 'TextureNodeTexture'],
                                     'RGBA': ['TextureNodeMixRGB', 'TextureNodeTexture'],
                                     'VECTOR': ['TextureNodeMixRGB', 'TextureNodeDistance'],
                                     'INT': ['TextureNodeMixRGB', 'TextureNodeMath', 'TextureNodeTexture']}}


class VL_MT_voronoi_mixer_menu(bpy.types.Menu):
    bl_idname = 'VL_MT_voronoi_mixer_menu'
    bl_label = ''

    def draw(self, context):
        who = self.layout.menu_pie() if get_addon_prefs().vm_menu_style == 'Pie' else self.layout
        text = dict_mixer_user_sk_name.get(mixerSkTyp[0], mixerSkTyp[0].capitalize())
        who.label(text=_tips(text))
        for li in dictMixerMain[context.space_data.tree_type][mixerSkTyp[0]]:
            who.operator('node.voronoi_mixer_mixer', text=_tips(dict_mixer_defs[li][2])).who = li


def voronoi_previewer_draw_callback(sender, context):
    if gv_where[0] != context.space_data:
        return
    gv_shaders[0] = gpu.shader.from_builtin('2D_SMOOTH_COLOR')
    gv_shaders[1] = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    # bgl.glHint(bgl.GL_LINE_SMOOTH_HINT, bgl.GL_NICEST)
    mouse_pos = context.space_data.cursor_location * gv_uifac[0]
    mouse_region_pos = pos_view_to_reg(mouse_pos.x, mouse_pos.y)
    lw = get_addon_prefs().ds_line_width
    if get_addon_prefs().ds_is_draw_debug:
        debug_draw_callback(sender, context)
        return
    if (sender.list_sk_goal_out == []) or (sender.list_sk_goal_out[1] is None):  # Второе условие -- для (1).
        if get_addon_prefs().ds_is_draw_point:
            wp = prepar_get_wp(mouse_pos, 0)
            draw_wide_point(wp[0], wp[1])
    else:
        draw_rectangle_on_socket(sender.list_sk_goal_out[1], sender.list_sk_goal_out[3],
                                 get_sk_vec_col(sender.list_sk_goal_out[1], 2.2))
        col = get_sk_col(sender.list_sk_goal_out[1]) if get_addon_prefs().ds_is_colored_line else (1, 1, 1, 1)
        wp = prepar_get_wp(sender.list_sk_goal_out[2] * gv_uifac[0], get_addon_prefs().ds_point_offset_x)
        if get_addon_prefs().ds_is_draw_line:
            draw_line(wp[0], mouse_region_pos, lw, col, col)
        if get_addon_prefs().ds_is_draw_point:
            draw_wide_point(wp[0], wp[1], get_sk_vec_col(sender.list_sk_goal_out[1], 2.2))

        def PreviewerDrawSk(Sk):
            txtdim = draw_sk_text(pos_view_to_reg(mouse_pos.x, mouse_pos.y), get_addon_prefs().ds_text_dist_from_cursor,
                                  -.5,
                                  Sk)
            if Sk.is_linked:
                draw_is_linked(mouse_pos, txtdim[0], 0,
                               get_sk_col(Sk) if get_addon_prefs().ds_is_colored_marker else (.9, .9, .9, 1))

        PreviewerDrawSk(sender.list_sk_goal_out[1])


class NODE_OT_voronoi_previewer(bpy.types.Operator):
    bl_idname = 'node.a_voronoi_previewer'
    bl_label = 'Voronoi Previewer'
    bl_options = {'UNDO'}

    def next_assign(sender, context):
        pick_pos = context.space_data.cursor_location
        list_nodes = gen_nearest_node_list(context.space_data.edit_tree.nodes, pick_pos)
        ancohor_exist = context.space_data.edit_tree.nodes.get(
            'Voronoi_Anchor') != None  # Если в геонодах есть якорь, то не триггериться только на геосокеты.
        for li in list_nodes:
            nd = li[1]
            # Если в геометрических нодах, игнорировать ноды без выводов геометрии
            if (context.space_data.tree_type == 'GeometryNodeTree') and (ancohor_exist is False):
                if [ndo for ndo in nd.outputs if ndo.type == 'GEOMETRY'] == []:
                    continue
            # Стандартное условие
            tgl = (nd.type != 'FRAME') and ((nd.hide is False) or (nd.type == 'REROUTE'))
            # Игнорировать свой собственный спец-рероут-якорь (полное совпадение имени и заголовка)
            tgl = (tgl) and (not ((nd.name == 'Voronoi_Anchor') and (nd.label == 'Voronoi_Anchor')))
            # Игнорировать ноды с пустыми выходами, чтобы точка не висела просто так и нод не мешал для удобного использования инструмента
            tgl = (tgl) and (len(nd.outputs) != 0)
            if tgl:
                list_socket_in, list_socket_out = gen_nearest_sockets_list(nd, pick_pos)
                for lso in list_socket_out:
                    skout = lso[1]
                    # Этот инструмент триггерится на любой выход кроме виртуального. В геометрических нодах искать только выходы геометрии
                    tgl = (skout.bl_idname != 'NodeSocketVirtual') and (
                            (context.space_data.tree_type != 'GeometryNodeTree') or (skout.type == 'GEOMETRY') or (
                        ancohor_exist))
                    if tgl:
                        sender.list_sk_goal_out = lso
                        break
                break
        if (get_addon_prefs().vp_is_live_preview) and (sender.list_sk_goal_out):
            sender.list_sk_goal_out[1] = VoronoiPreviewer_DoPreview(context, sender.list_sk_goal_out[1])

    def modal(self, context, event):
        context.area.tag_redraw()
        match event.type:
            case 'MOUSEMOVE':
                NODE_OT_voronoi_previewer.next_assign(self, context)
            case 'LEFTMOUSE' | 'RIGHTMOUSE' | 'ESC':
                bpy.types.SpaceNodeEditor.draw_handler_remove(self.dcb_handle, 'WINDOW')
                if event.value != 'RELEASE' or not self.list_sk_goal_out:
                    return {'CANCELLED'}
                self.list_sk_goal_out[1] = VoronoiPreviewer_DoPreview(context, self.list_sk_goal_out[1])
                return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if (context.area.type != 'NODE_EDITOR') or (context.space_data.edit_tree is None):
            return {'CANCELLED'}
        if ('FINISHED' in bpy.ops.node.select('INVOKE_DEFAULT')):
            match context.space_data.tree_type:
                case 'GeometryNodeTree':
                    if get_addon_prefs().va_allow_classic_geo_viewer:
                        return {'PASS_THROUGH'}
                case 'CompositorNodeTree':
                    if get_addon_prefs().va_allow_classic_compos_viewer:
                        return {'PASS_THROUGH'}
        if (event.type == 'RIGHTMOUSE') ^ get_addon_prefs().vm_preview_hk_inverse:
            nodes = context.space_data.edit_tree.nodes
            for nd in nodes:
                nd.select = False
            nnd = (nodes.get('Voronoi_Anchor') or nodes.new('NodeReroute'))
            nnd.name = 'Voronoi_Anchor'
            nnd.label = 'Voronoi_Anchor'
            nnd.location = context.space_data.cursor_location
            nnd.select = True
            return {'FINISHED'}
        else:
            self.list_sk_goal_out = []
            gv_uifac[0] = ui_scale()
            gv_where[0] = context.space_data
            set_font()
            context.area.tag_redraw()
            NODE_OT_voronoi_previewer.next_assign(self, context)
            self.dcb_handle = bpy.types.SpaceNodeEditor.draw_handler_add(voronoi_previewer_draw_callback,
                                                                         (self, context),
                                                                         'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


list_shader_shaders_with_color = ['BSDF_ANISOTROPIC', 'BSDF_DIFFUSE', 'EMISSION', 'BSDF_GLASS', 'BSDF_GLOSSY',
                                  'BSDF_HAIR', 'BSDF_HAIR_PRINCIPLED', 'PRINCIPLED_VOLUME', 'BACKGROUND',
                                  'BSDF_REFRACTION', 'SUBSURFACE_SCATTERING', 'BSDF_TOON', 'BSDF_TRANSLUCENT',
                                  'BSDF_TRANSPARENT', 'BSDF_VELVET', 'VOLUME_ABSORPTION', 'VOLUME_SCATTER']


def VoronoiPreviewer_DoPreview(context, goalSk):
    def GetSocketIndex(socket):
        return int(socket.path_from_id().split('.')[-1].split('[')[-1][:-1])

    def GetTrueTreeWay(context, nd):
        # Идею рекурсивного нахождения пути через активный нод дерева я взял у NodeWrangler'a его функции "get_active_tree"
        # которая использовала "while tree.nodes.active != context.active_node:" (строка 613 версии 3.43).
        # Этот способ имеет недостатки, ибо активным нодом может оказаться не нод-группа, банально тем что можно открыть два окна редактора узлов и спокойно нарушить этот "путь".
        # Я мирился с этим маленьким и редким недостатком до того, пока в один прекрасный момент не возмутился от странности этого метода.
        # После отправился на сёрфинг api документации и открытого исходного кода. Результатом было банальное обнаружение ".space_data.path"
        # См. https://docs.blender.org/api/current/bpy.types.SpaceNodeEditorPath.html
        # Это "честный" api, дающий доступ у редактора узлов к пути от базы до финального дерева, отображаемого прямо сейчас.
        # Аддон, написанный 5-ю людьми, что встроен в Блендер по умолчанию, использует столь странный похожий на костыль метод получения пути? Может я что-то понимаю не так?
        way_trnd = []
        if False:  # bad way by parody on NodeWrangler
            wyc_tree = context.space_data.node_tree
            lim = 0  # lim'ит нужен для предохранителя вечного цикла.
            while (wyc_tree != context.space_data.edit_tree) and (lim < 64):
                way_trnd.insert(0, (wyc_tree, wyc_tree.nodes.active))
                wyc_tree = wyc_tree.nodes.active.node_tree
                lim += 1
            way_trnd.insert(0, (wyc_tree, nd))
        else:  # best way by my study of the api docs
            # Как я могу судить, сама суть реализации редактора узлов не хранит нод, через который пользователь зашёл в группу (Но это не точно).
            way_trnd = [[pn.node_tree, pn.node_tree.nodes.active] for pn in reversed(context.space_data.path)]
            # Поэтому если активным оказалась не нод-группа, то заменить на первого по имени (или ничего, если не найдено)
            for cyc in range(1, length(way_trnd)):
                wtn = way_trnd[cyc]
                if (wtn[1] is None) or (wtn[1].type != 'GROUP') or (wtn[1].node_tree != way_trnd[cyc - 1][0]):
                    wtn[1] = None  # Если не найден, то останется имеющийся неправильный. Поэтому обнулить его.
                    for nd in wtn[0].nodes:
                        if (nd.type == 'GROUP') and (nd.node_tree == way_trnd[cyc - 1][0]):
                            wtn[1] = nd
                            break
        return way_trnd

    # Для (1):
    if not goalSk:
        return None

    def GetSkIndex(sk):
        return int(sk.path_from_id().split('.')[-1].split('[')[-1][:-1])

    skix = GetSkIndex(goalSk)
    # Удалить все свои следы предыдущего использования для нод-групп текущего типа редактора
    for ng in bpy.data.node_groups:
        if ng.type != context.space_data.node_tree.type: continue
        if sk := ng.outputs.get('voronoi_preview'):
            ng.outputs.remove(sk)
    # (1)Переполучить сокет. Нужен для ситуациях присасывания к сокетам "voronoi_preview", которые исчезли
    goalSk = goalSk.node.outputs[skix] if skix < length(goalSk.node.outputs) else None
    # Если неудача, то выйти
    if goalSk is None:
        return None
    # Иначе выстроить путь:
    cur_tree = context.space_data.edit_tree
    list_way_trnd = GetTrueTreeWay(context, goalSk.node)
    hig_way = len(list_way_trnd) - 1
    ix_sk_last_used = -1
    is_zero_preview_gen = True
    for cyc in range(hig_way + 1):
        if (list_way_trnd[cyc][1] is None) and (cyc > 0):
            continue  # Проверка по той же причине, по которой мне не нравился способ от NW.
        node_in = None
        sock_out = None
        sock_in = None
        # Найти принимающий нод текущего уровня
        if cyc != hig_way:
            for nd in list_way_trnd[cyc][0].nodes:
                if (nd.type in ['GROUP_OUTPUT', 'OUTPUT_MATERIAL', 'OUTPUT_WORLD', 'OUTPUT_LIGHT', 'COMPOSITE',
                                'OUTPUT']) and (nd.is_active_output):
                    node_in = nd
        else:
            match context.space_data.tree_type:
                case 'ShaderNodeTree':
                    for nd in list_way_trnd[hig_way][0].nodes:
                        if nd.type in ['OUTPUT_MATERIAL', 'OUTPUT_WORLD', 'OUTPUT_LIGHT', 'OUTPUT_LINESTYLE', 'OUTPUT']:
                            sock_in = nd.inputs[(goalSk.name == 'Volume') * (nd.type in ['OUTPUT_MATERIAL',
                                                                                         'OUTPUT_WORLD'])] if nd.is_active_output else sock_in
                case 'CompositorNodeTree':
                    for nd in list_way_trnd[hig_way][0].nodes:
                        sock_in = nd.inputs[0] if (nd.type == 'VIEWER') else sock_in
                    if sock_in is None:
                        for nd in list_way_trnd[hig_way][0].nodes:
                            sock_in = nd.inputs[0] if (nd.type == 'COMPOSITE') else sock_in
                case 'GeometryNodeTree':
                    for nd in list_way_trnd[hig_way][0].nodes:
                        if nd.type != 'GROUP_OUTPUT': continue
                        lis = [sk for sk in nd.inputs if sk.type == 'GEOMETRY']
                        if not lis: continue
                        sock_in = lis[0]
                        break

                case 'TextureNodeTree':
                    for nd in list_way_trnd[hig_way][0].nodes:
                        sock_in = nd.inputs[0] if (nd.type == 'OUTPUT') else sock_in
            if sock_in:
                node_in = sock_in.node  # Иначе корень не имеет вывода.
        # Определить сокет отправляющего нода
        if cyc == 0:
            sock_out = goalSk
        else:
            sock_out = list_way_trnd[cyc][1].outputs.get('voronoi_preview')
            if (sock_out is None) and (ix_sk_last_used in range(0, length(list_way_trnd[cyc][1].outputs))):
                sock_out = list_way_trnd[cyc][1].outputs[ix_sk_last_used]
            if sock_out is None:
                continue  # Если нод-группа не имеет выходов
        # Определить сокет принимающего нода:
        for sl in sock_out.links:
            if sl.to_node == node_in:
                sock_in = sl.to_socket
                ix_sk_last_used = GetSocketIndex(sock_in)
        if (sock_in is None) and (cyc != hig_way):  # cyc!=hig_way -- если корень потерял вывод.
            sock_in = list_way_trnd[cyc][0].outputs.get('voronoi_preview')
            if sock_in is None:
                txt = 'NodeSocketColor' if context.space_data.tree_type != 'GeometryNodeTree' else 'NodeSocketGeometry'
                txt = 'NodeSocketShader' if sock_out.type == 'SHADER' else txt
                list_way_trnd[cyc][0].outputs.new(txt, 'voronoi_preview')
                if node_in is None:
                    node_in = list_way_trnd[cyc][0].nodes.new('NodeGroupOutput')
                    node_in.location = list_way_trnd[cyc][1].location
                    node_in.location.x += list_way_trnd[cyc][1].width * 2
                sock_in = node_in.inputs.get('voronoi_preview')
                sock_in.hide_value = True
                is_zero_preview_gen = False
        # Удобный сразу-в-шейдер. "and(sock_in)" -- если у корня нет вывода
        if (sock_out.type in ('RGBA')) and (cyc == hig_way) and (sock_in) and (len(sock_in.links) != 0):
            if (sock_in.links[0].from_node.type in list_shader_shaders_with_color) and (is_zero_preview_gen):
                if len(sock_in.links[0].from_socket.links) == 1:
                    sock_in = sock_in.links[0].from_node.inputs.get('Color')
        # Соединить:
        nd_va = list_way_trnd[cyc][0].nodes.get('Voronoi_Anchor')
        if nd_va:
            list_way_trnd[cyc][0].links.new(sock_out, nd_va.inputs[0])
            break  # Завершение после напарывания повышает возможности использования якоря.
        elif (sock_out) and (sock_in) and ((sock_in.name == 'voronoi_preview') or (cyc == hig_way)):
            list_way_trnd[cyc][0].links.new(sock_out, sock_in)
    # Выделить предпросматриваемый нод:
    if get_addon_prefs().vp_select_previewed_node:
        for nd in cur_tree.nodes:
            nd.select = False
        cur_tree.nodes.active = goalSk.node
        goalSk.node.select = True
    return goalSk  # Возвращать сокет. Нужно для (1).


def VoronoiHiderDrawCallback(sender, context):
    if gv_where[0] != context.space_data:
        return
    gv_shaders[0] = gpu.shader.from_builtin('2D_SMOOTH_COLOR')
    gv_shaders[1] = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    # bgl.glHint(bgl.GL_LINE_SMOOTH_HINT, bgl.GL_NICEST)
    mouse_pos = context.space_data.cursor_location * gv_uifac[0]
    mouse_region_pos = pos_view_to_reg(mouse_pos.x, mouse_pos.y)
    lw = get_addon_prefs().ds_line_width
    if get_addon_prefs().ds_is_draw_debug:
        debug_draw_callback(sender, context)
        return
    if sender.is_target_node:
        if (sender.list_nd_goal == []):
            if get_addon_prefs().ds_is_draw_point:
                wp = prepar_get_wp(mouse_pos, 0)
                draw_wide_point(wp[0], wp[1])
        else:
            wp = prepar_get_wp(sender.list_nd_goal[2] * gv_uifac[0], 0)
            col = (1, 1, 1, 1)
            if get_addon_prefs().ds_is_draw_line:
                draw_line(wp[0], mouse_region_pos, lw, col, col)
            if get_addon_prefs().ds_is_draw_point:
                draw_wide_point(wp[0], wp[1])
            if get_addon_prefs().vh_draw_text_for_unhide:
                lbl = sender.list_nd_goal[1].label
                l_ys = [.25, -1.25] if lbl else [-.5, -.5]
                draw_text(pos_view_to_reg(mouse_pos.x, mouse_pos.y), get_addon_prefs().ds_text_dist_from_cursor,
                          l_ys[0],
                          sender.list_nd_goal[1].name, (1, 1, 1, 1))
                if lbl:
                    draw_text(pos_view_to_reg(mouse_pos.x, mouse_pos.y), get_addon_prefs().ds_text_dist_from_cursor,
                              l_ys[1],
                              lbl, (1, 1, 1, 1))
    else:
        if (sender.list_sk_goal == []):
            if get_addon_prefs().ds_is_draw_point:
                wp = prepar_get_wp(mouse_pos, 0)
                draw_wide_point(wp[0], wp[1])
        else:
            draw_rectangle_on_socket(sender.list_sk_goal[1], sender.list_sk_goal[3],
                                     get_sk_vec_col(sender.list_sk_goal[1], 2.2))
            col = get_sk_col(sender.list_sk_goal[1]) if get_addon_prefs().ds_is_colored_line else (1, 1, 1, 1)
            wp = prepar_get_wp(sender.list_sk_goal[2] * gv_uifac[0],
                               get_addon_prefs().ds_point_offset_x * (sender.list_sk_goal[1].is_output * 2 - 1))
            if get_addon_prefs().ds_is_draw_line:
                draw_line(wp[0], mouse_region_pos, lw, col, col)
            if get_addon_prefs().ds_is_draw_point:
                draw_wide_point(wp[0], wp[1], get_sk_vec_col(sender.list_sk_goal[1], 2.2))

            def HiderDrawSk(Sk):
                txtdim = draw_sk_text(pos_view_to_reg(mouse_pos.x, mouse_pos.y),
                                      get_addon_prefs().ds_text_dist_from_cursor * (Sk.is_output * 2 - 1), -.5, Sk)
                if Sk.is_linked:
                    draw_is_linked(mouse_pos, txtdim[0] * (Sk.is_output * 2 - 1), 0,
                                   get_sk_col(Sk) if get_addon_prefs().ds_is_colored_marker else (.9, .9, .9, 1))

            HiderDrawSk(sender.list_sk_goal[1])


class NODE_OT_voronoi_hider(bpy.types.Operator):
    bl_idname = 'node.voronoi_hider'
    bl_label = 'Voronoi Hider'
    bl_options = {'UNDO'}

    def next_assign(sender, context):
        sender.list_sk_goal = []
        pick_pos = context.space_data.cursor_location
        list_nodes = gen_nearest_node_list(context.space_data.edit_tree.nodes, pick_pos)
        for li in list_nodes:
            nd = li[1]
            if not nd.type in ['FRAME', 'REROUTE']:
                sender.list_nd_goal = li
                list_socket_in, list_socket_out = gen_nearest_sockets_list(nd, pick_pos)

                def MucGetNotLinked(list_sks):
                    for sk in list_sks:
                        if sk[1].is_linked is False:
                            return sk
                    return None

                skin = MucGetNotLinked(list_socket_in)
                skout = MucGetNotLinked(list_socket_out)
                if (skin) or (skout):
                    if skin is None:
                        sender.list_sk_goal = skout
                    elif skout is None:
                        sender.list_sk_goal = skin
                    else:
                        sender.list_sk_goal = skin if skin[0] < skout[0] else skout
                break

    def modal(self, context, event):
        context.area.tag_redraw()
        match event.type:
            case 'MOUSEMOVE':
                NODE_OT_voronoi_hider.next_assign(self, context)
            case 'ESC':
                bpy.types.SpaceNodeEditor.draw_handler_remove(self.dcb_handle, 'WINDOW')
                return {'CANCELLED'}
            case 'E':
                if (event.is_repeat is False) and (event.value == 'RELEASE'):
                    bpy.types.SpaceNodeEditor.draw_handler_remove(self.dcb_handle, 'WINDOW')
                    if self.is_target_node is False:
                        if self.list_sk_goal:
                            self.list_sk_goal[1].hide = True
                    elif self.list_nd_goal:
                        for ni in self.list_nd_goal[1].inputs:
                            ni.hide = False
                        for no in self.list_nd_goal[1].outputs:
                            no.hide = False
                    return {'FINISHED'}
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.list_sk_goal = []
        self.list_nd_goal = []
        self.is_target_node = (event.shift) and (event.ctrl)
        gv_uifac[0] = ui_scale()
        gv_where[0] = context.space_data
        set_font()
        context.area.tag_redraw()
        NODE_OT_voronoi_hider.next_assign(self, context)
        self.dcb_handle = bpy.types.SpaceNodeEditor.draw_handler_add(VoronoiHiderDrawCallback, (self, context),
                                                                     'WINDOW', 'POST_PIXEL')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


NT_MATH_MAP = {  # 0 for math, 1 for vector math
    0: {
        'ShaderNodeTree': 'ShaderNodeMath',
        'GeometryNodeTree': 'ShaderNodeMath',
        'CompositorNodeTree': 'CompositorNodeMath',
        'TextureNodeTree': 'TextureNodeMath'
    },
    1: {
        'ShaderNodeTree': 'ShaderNodeVectorMath',
        'GeometryNodeTree': 'ShaderNodeVectorMath'
    }
}

MATH_MAP = {
    'Functions': [
        'ADD', 'SUBTRACT', 'MULTIPLY', 'DIVIDE', 'MULTIPLY', 'POWER', 'LOGARITHM', 'SQRT', 'INVERSE_SQRT', 'ABSOLUTE',
        'EXPONENT'

    ],
    'Comparisons': [
        'MINIMUM', 'MAXIMUM', 'LESS_THAN', 'GREATER_THAN', 'SIGN', 'COMPARE', 'SMOOTH_MIN', 'SMOOTH_MAX',
    ],
    'Rounding': [
        'ROUND', 'FLOOR', 'CEIL', 'TRUNC',
        'FRACT', 'MODULO', 'WRAP', 'SNAP',
    ],
    'Trigonometry': [
        'SINE', 'COSINE', 'TANGENT',
        'ARCSINE', 'ARCCOSINE', 'ARCTANGENT', 'ARCTAN2'
    ],
    'Conversion': [
        'RADIANS', 'DEGREES'
    ]
}

VEC_MATH_MAP = {
    'Basic': [
        'SCALE', 'LENGTH', 'DISTANCE'
    ],
    'Rays': [
        'DOT_PRODUCT', 'CROSS_PRODUCT', 'FACEFORWARD', 'PROJECT', 'REFRACT', 'REFLECT'
    ],
    'Functions': [
        'SUBTRACT', 'ADD', 'DIVIDE', 'MULTIPLY', 'ABSOLUTE', 'MULTIPLY_ADD'
    ],
    'Trigonometry': [
        'SINE', 'COSINE', 'TANGENT'
    ],
    'Rounding': [
        'MINIMUM', 'MAXIMUM', 'FLOOR', 'CEIL', 'MODULO', 'FRACTION', 'WRAP', 'SNAP'
    ],
    'Normalization': [
        'NORMALIZE'
    ]
}


def reg_menu_cls(label, op_list):
    def _menu_draw(_cls, _context):
        col = _cls.layout.column(align=True)
        for operation in op_list:
            texts = operation.split('_')
            text = ' '.join([t.capitalize() for t in texts])

            col.operator('node.voronoi_add_math_node',
                         text=_tips(text)).operation = operation

    cls = type('DynMenu', (bpy.types.Menu,), {
        'bl_idname': f'VL_MT_voronoi_math_node_menu_{label}',
        'bl_label': label,
        'draw': _menu_draw
    })

    return cls


class NODE_OT_voronoi_add_math_node(bpy.types.Operator):
    bl_idname = 'node.voronoi_add_math_node'
    bl_label = 'Add Math Node'

    operation: StringProperty()

    def execute(self, context):
        tree = context.space_data.edit_tree
        typ = NT_MATH_MAP[displayWho[0]].get(context.space_data.tree_type, None)
        if typ is None: return {'CANCELLED'}

        bpy.ops.node.add_node('INVOKE_DEFAULT', type=typ, use_transform=True)

        aNd = context.space_data.edit_tree.nodes.active
        aNd.operation = self.operation
        tree.links.new(mixerSks[0], aNd.inputs[0])
        if mixerSks[1]:  tree.links.new(mixerSks[1], aNd.inputs[1])
        return {'FINISHED'}


class NODE_OT_voronoi_fastmath(bpy.types.Operator):
    bl_idname = 'node.voronoi_fastmath'
    bl_label = 'Fast Maths Pie'

    bridge: StringProperty()
    operation: StringProperty()
    dep_cls = None

    @classmethod
    def poll(cls, context):
        return context.space_data.edit_tree

    def modal(self, context, event):
        self.bridge = ''
        return {'FINISHED'}

    def invoke(self, context, event):
        if NODE_OT_voronoi_fastmath.dep_cls:
            bpy.utils.unregister_class(NODE_OT_voronoi_fastmath.dep_cls)
        NODE_OT_voronoi_fastmath.dep_cls = None

        whoList = MATH_MAP if displayWho[0] == 0 else VEC_MATH_MAP

        displayList[0] = list(whoList.keys())

        def draw(self, context):
            for label in displayList[0]:
                self.layout.menu(f'VL_MT_voronoi_math_node_menu_{label}', text=label)

        NODE_OT_voronoi_fastmath.dep_cls = type('DynMenu', (bpy.types.Menu,), {
            'bl_idname': f'VL_MT_voronoi_math_node_menu',
            'bl_label': 'Maths',
            'draw': draw
        })
        bpy.utils.register_class(NODE_OT_voronoi_fastmath.dep_cls)
        bpy.ops.wm.call_menu('INVOKE_DEFAULT', name='VL_MT_voronoi_math_node_menu')

        return {'RUNNING_MODAL'}


menu_class = {}  # register class for menu
op_classes = [NODE_OT_voronoi_linker, NODE_OT_voronoi_mass_linker, NODE_OT_voronoi_mixer, NODE_OT_voronoi_mixer_mixer,
              VL_MT_voronoi_mixer_menu, NODE_OT_voronoi_previewer,
              NODE_OT_voronoi_hider, NODE_OT_voronoi_add_math_node, NODE_OT_voronoi_fastmath]


def register():
    for label, op_list in MATH_MAP.items():
        menu_class[label] = reg_menu_cls(label, op_list)

    for label, op_list in VEC_MATH_MAP.items():
        menu_class[label] = reg_menu_cls(label, op_list)

    for cls in menu_class.values():
        bpy.utils.register_class(cls)

    for li in op_classes:
        bpy.utils.register_class(li)


def unregister():
    for cls in menu_class.values():
        bpy.utils.unregister_class(cls)

    for li in reversed(op_classes):
        bpy.utils.unregister_class(li)


if __name__ == '__main__':
    register()
