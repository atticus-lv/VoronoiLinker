import bpy, blf, gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
from builtins import len as length
from bpy.app.translations import pgettext_iface as _tips

from math import pi, inf, sin, cos, copysign


gv_shaders = [None, None]
gv_uifac = [1.0]
gv_font_id = [0]
gv_where = [None]


def get_addon_prefs():
    return bpy.context.preferences.addons[__package__].preferences

def draw_way(vtxs, vcol, siz):
    # bgl.glEnable(bgl.GL_BLEND)
    # bgl.glEnable(bgl.GL_LINE_SMOOTH)
    gpu.state.blend_set('ALPHA')
    gv_shaders[0].bind()
    # bgl.glLineWidth(siz)
    gpu.state.line_width_set(siz)
    batch_for_shader(gv_shaders[0], 'LINE_STRIP', {'pos': vtxs, 'color': vcol}).draw(gv_shaders[0])


def draw_area_fan(vtxs, col, sm):
    # bgl.glEnable(bgl.GL_BLEND)
    # bgl.glEnable(bgl.GL_POLYGON_SMOOTH) if sm else bgl.glDisable(bgl.GL_POLYGON_SMOOTH)
    gpu.state.blend_set('ALPHA')
    gv_shaders[1].bind()
    gv_shaders[1].uniform_float('color', col)
    batch_for_shader(gv_shaders[1], 'TRI_FAN', {'pos': vtxs}).draw(gv_shaders[1])


def draw_line(ps1, ps2, sz=1, cl1=(1.0, 1.0, 1.0, 0.75), cl2=(1.0, 1.0, 1.0, 0.75), fs=[0, 0]):
    draw_way(((ps1[0] + fs[0], ps1[1] + fs[1]), (ps2[0] + fs[0], ps2[1] + fs[1])), (cl1, cl2), sz)


def draw_circle_outer(pos, rd, siz=1, col=(1.0, 1.0, 1.0, 0.75), resolution=16):
    vtxs = []
    vcol = []
    for cyc in range(resolution + 1):
        vtxs.append((
            rd * cos(cyc * 2 * pi / resolution) + pos[0], rd * sin(cyc * 2 * pi / resolution) + pos[1]))
        vcol.append(col)
    draw_way(vtxs, vcol, siz)


def draw_circle(pos, rd, col=(1.0, 1.0, 1.0, 0.75), resl=54):
    draw_area_fan([(pos[0], pos[1]),
                   *[(rd * cos(i * 2 * pi / resl) + pos[0], rd * sin(i * 2 * pi / resl) + pos[1]) for i in
                     range(resl + 1)]], col, True)


def draw_wide_point(pos, rd, colfac=Vector((1, 1, 1, 1))):
    col1 = Vector((0.5, 0.5, 0.5, 0.4))
    col2 = Vector((0.5, 0.5, 0.5, 0.4))
    col3 = Vector((1, 1, 1, 1))
    colfac = colfac if get_addon_prefs().ds_is_colored_point else Vector((1, 1, 1, 1))
    rd = (rd * rd + 10) ** .5
    rs = get_addon_prefs().ds_point_resolution
    draw_circle(pos, rd + 3, col1 * colfac, rs)
    draw_circle(pos, rd, col2 * colfac, rs)
    draw_circle(pos, rd / 1.5, col3 * colfac, rs)


def draw_rectangle(ps1, ps2, cl):
    draw_area_fan([(ps1[0], ps1[1]), (ps2[0], ps1[1]), (ps2[0], ps2[1]), (ps1[0], ps2[1])], cl, False)


def draw_rectangle_on_socket(sk, stEn, colfac=Vector((1, 1, 1, 1))):
    if get_addon_prefs().ds_is_draw_area is False:
        return
    loc = recr_get_node_final_loc(sk.node).copy() * gv_uifac[0]
    pos1 = pos_view_to_reg(loc.x, stEn[0] * gv_uifac[0])
    colfac = colfac if get_addon_prefs().ds_is_colored_area else Vector((1, 1, 1, 1))
    pos2 = pos_view_to_reg(loc.x + sk.node.dimensions.x, stEn[1] * gv_uifac[0])
    draw_rectangle(pos1, pos2, Vector((1.0, 1.0, 1.0, 0.075)) * colfac)


def draw_is_linked(loc, ofsx, ofsy, sk_col):
    ofsx += ((
                     20 + get_addon_prefs().ds_text_dist_from_cursor) * 1.5 + get_addon_prefs().ds_text_frame_offset) * copysign(
        1,
        ofsx) + 4
    if get_addon_prefs().ds_is_draw_marker is False:
        return
    vec = pos_view_to_reg(loc.x, loc.y)
    gc = 0.65
    col1 = (0, 0, 0, 0.5)
    col2 = (gc, gc, gc, max(max(sk_col[0], sk_col[1]), sk_col[2]) * .9)
    col3 = (sk_col[0], sk_col[1], sk_col[2], .925)
    draw_circle_outer([vec[0] + ofsx + 1.5, vec[1] + 3.5 + ofsy], 9.0, 3.0, col1)
    draw_circle_outer([vec[0] + ofsx - 3.5, vec[1] - 5 + ofsy], 9.0, 3.0, col1)
    draw_circle_outer([vec[0] + ofsx, vec[1] + 5 + ofsy], 9.0, 3.0, col2)
    draw_circle_outer([vec[0] + ofsx - 5, vec[1] - 3.5 + ofsy], 9.0, 3.0, col2)
    draw_circle_outer([vec[0] + ofsx, vec[1] + 5 + ofsy], 9.0, 1.0, col3)
    draw_circle_outer([vec[0] + ofsx - 5, vec[1] - 3.5 + ofsy], 9.0, 1.0, col3)


def draw_text(pos, ofsx, ofsy, txt, draw_col):
    txt_ = _tips(txt)
    isdrsh = get_addon_prefs().ds_is_draw_sk_text_shadow
    if isdrsh:
        blf.enable(gv_font_id[0], blf.SHADOW)
        sdcol = get_addon_prefs().ds_shadow_col
        blf.shadow(gv_font_id[0], [0, 3, 5][get_addon_prefs().ds_shadow_blur], sdcol[0], sdcol[1], sdcol[2], sdcol[3])
        sdofs = get_addon_prefs().ds_shadow_offset
        blf.shadow_offset(gv_font_id[0], sdofs[0], sdofs[1])
    else:
        blf.disable(gv_font_id[0], blf.SHADOW)
    tof = get_addon_prefs().ds_text_frame_offset
    txsz = get_addon_prefs().ds_font_size
    blf.size(gv_font_id[0], txsz, 72)
    txdim = [blf.dimensions(gv_font_id[0], txt_)[0], blf.dimensions(gv_font_id[0], '█')[1]]
    pos = [pos[0] - (txdim[0] + tof + 10) * (ofsx < 0) + (tof + 1) * (ofsx > -1), pos[1] + tof]
    pw = 1 / 1.975
    muv = round((txdim[1] + tof * 2) * ofsy)
    pos1 = [pos[0] + ofsx - tof, pos[1] + muv - tof]
    pos2 = [pos[0] + ofsx + 10 + txdim[0] + tof, pos[1] + muv + txdim[1] + tof]
    list = [.4, .55, .7, .85, 1]
    uh = 1 / len(list) * (txdim[1] + tof * 2)
    if get_addon_prefs().ds_text_style == 'Classic':
        for cyc in range(len(list)):
            draw_rectangle([pos1[0], pos1[1] + cyc * uh], [pos2[0], pos1[1] + cyc * uh + uh],
                           (draw_col[0] / 2, draw_col[1] / 2, draw_col[2] / 2, list[cyc]))
        col = (draw_col[0] ** pw, draw_col[1] ** pw, draw_col[2] ** pw, 1)
        draw_line(pos1, [pos2[0], pos1[1]], 1, col, col)
        draw_line([pos2[0], pos1[1]], pos2, 1, col, col)
        draw_line(pos2, [pos1[0], pos2[1]], 1, col, col)
        draw_line([pos1[0], pos2[1]], pos1, 1, col, col)
        col = (col[0], col[1], col[2], .375)
        thS = get_addon_prefs().ds_text_lineframe_offset
        draw_line(pos1, [pos2[0], pos1[1]], 1, col, col, [0, -thS])
        draw_line([pos2[0], pos1[1]], pos2, 1, col, col, [+thS, 0])
        draw_line(pos2, [pos1[0], pos2[1]], 1, col, col, [0, +thS])
        draw_line([pos1[0], pos2[1]], pos1, 1, col, col, [-thS, 0])
        draw_line([pos1[0] - thS, pos1[1]], [pos1[0], pos1[1] - thS], 1, col, col)
        draw_line([pos2[0] + thS, pos1[1]], [pos2[0], pos1[1] - thS], 1, col, col)
        draw_line([pos2[0] + thS, pos2[1]], [pos2[0], pos2[1] + thS], 1, col, col)
        draw_line([pos1[0] - thS, pos2[1]], [pos1[0], pos2[1] + thS], 1, col, col)
    elif get_addon_prefs().ds_text_style == 'Simplified':
        draw_rectangle([pos1[0], pos1[1]], [pos2[0], pos2[1]],
                       (draw_col[0] / 2.4, draw_col[1] / 2.4, draw_col[2] / 2.4, .8))
        col = (.1, .1, .1, .95)
        draw_line(pos1, [pos2[0], pos1[1]], 2, col, col)
        draw_line([pos2[0], pos1[1]], pos2, 2, col, col)
        draw_line(pos2, [pos1[0], pos2[1]], 2, col, col)
        draw_line([pos1[0], pos2[1]], pos1, 2, col, col)
    blf.position(gv_font_id[0], pos[0] + ofsx + 3.5, pos[1] + muv + txdim[1] * .3, 0)
    blf.color(gv_font_id[0], draw_col[0] ** pw, draw_col[1] ** pw, draw_col[2] ** pw, 1.0)
    blf.draw(gv_font_id[0], txt_)
    return [txdim[0] + tof, txdim[1] + tof * 2]


def draw_sk_text(pos, ofsx, ofsy, Sk):
    if get_addon_prefs().ds_is_draw_sk_text is False:
        return [0, 0]
    try:
        sk_col = get_sk_col(Sk)
    except:
        sk_col = (1, 0, 0, 1)
    sk_col = sk_col if get_addon_prefs().ds_is_colored_sk_text else (.9, .9, .9, 1)
    txt = Sk.name if Sk.bl_idname != 'NodeSocketVirtual' else 'Virtual'
    return draw_text(pos, ofsx, ofsy, txt, sk_col)


def get_sk_col(Sk):
    return Sk.draw_color(bpy.context, Sk.node)


def vec_4_pow(vec, pw):
    return Vector((vec.x ** pw, vec.y ** pw, vec.z ** pw, vec.w ** pw))


def get_sk_vec_col(Sk, apw):
    return vec_4_pow(Vector(Sk.draw_color(bpy.context, Sk.node)), 1 / apw)




def set_font():
    gv_font_id[0] = blf.load(r'C:\Windows\Fonts\consola.ttf')
    gv_font_id[0] = 0 if gv_font_id[0] == -1 else gv_font_id[
        0]  # for change Blender themes


def pos_view_to_reg(x, y):
    return bpy.context.region.view2d.view_to_region(x, y, clip=False)


def prepar_get_wp(loc, offsetx):
    pos = pos_view_to_reg(loc.x + offsetx, loc.y)
    rd = \
        pos_view_to_reg(loc.x + offsetx + 6 * get_addon_prefs().ds_point_radius, loc.y)[0] - pos[0]
    return pos, rd


def debug_draw_callback(sender, context):
    def DrawDbText(pos, txt, r=1, g=1, b=1):
        blf.size(gv_font_id[0], 14, 72)
        blf.position(gv_font_id[0], pos[0] + 10, pos[1], 0)
        blf.color(gv_font_id[0], r, g, b, 1.0)
        blf.draw(gv_font_id[0], txt)

    mouse_pos = context.space_data.cursor_location * gv_uifac[0]
    wp = prepar_get_wp(mouse_pos, 0)
    draw_wide_point(wp[0], wp[1])
    DrawDbText(pos_view_to_reg(mouse_pos[0], mouse_pos[1]), 'Cursor position here.')
    list_nodes = gen_nearest_node_list(context.space_data.edit_tree.nodes, mouse_pos)
    sco = 0
    for li in list_nodes:
        if li[1].type == 'FRAME': continue
        wp = prepar_get_wp(li[2], 0)
        draw_wide_point(wp[0], wp[1], Vector((1, .5, .5, 1)))
        DrawDbText(wp[0], str(sco) + ' Node goal here', g=.5, b=.5)
        sco += 1

    list_socket_in, list_socket_out = gen_nearest_sockets_list(list_nodes[0][1], mouse_pos)
    if list_socket_out:
        wp = prepar_get_wp(list_socket_out[0][2], 0)
        draw_wide_point(wp[0], wp[1], Vector((.5, .5, 1, 1)))
        DrawDbText(wp[0], 'Nearest socketOut here', r=.75, g=.75)
    if list_socket_in:
        wp = prepar_get_wp(list_socket_in[0][2], 0)
        draw_wide_point(wp[0], wp[1], Vector((.5, 1, .5, 1)))
        DrawDbText(wp[0], 'Nearest socketIn here', r=.5, b=.5)


def ui_scale():
    return bpy.context.preferences.system.dpi * bpy.context.preferences.system.pixel_size / 72


def recr_get_node_final_loc(nd):
    return nd.location if nd.parent is None else nd.location + recr_get_node_final_loc(nd.parent)


def gen_nearest_node_list(nodes,
                          pick_pos):  # Выдаёт список "ближайших нод". Честное поле расстояний. Спасибо RayMarching'у, без него я бы до такого не допёр.
    def ToSign(vec2):
        return Vector((copysign(1, vec2[0]), copysign(1, vec2[1])))  # Для запоминания своего квадранта перед abs().

    list_nodes = []
    for nd in nodes:
        # Расчехлить иерархию родителей и получить итоговую позицию нода. Подготовить размер нода
        nd_location = recr_get_node_final_loc(nd)
        nd_size = Vector((4, 4)) if nd.bl_idname == 'NodeReroute' else nd.dimensions / ui_scale()
        # Для рероута позицию в центр. Для нода позицию в нижний левый угол, чтобы быть миро-ориентированным и спокойно прибавлять половину размера нода
        nd_location = nd_location - nd_size / 2 if nd.bl_idname == 'NodeReroute' else nd_location - Vector(
            (0, nd_size[1]))
        # field_uv -- сырой от pick_pos. field_xy -- абсолютные предыдущего, нужен для восстановления направления
        field_uv = pick_pos - (nd_location + nd_size / 2)
        field_xy = Vector((abs(field_uv.x), abs(field_uv.y))) - nd_size / 2
        # Сконструировать внутренности чтобы корректно находить ближайшего при наслаивающихся нодов
        field_en = ToSign(field_xy)
        field_en = min(abs(field_xy.x), abs(field_xy.y)) * (field_en.x + field_en.y == -2)
        field_xy = Vector((max(field_xy.x, 0), max(field_xy.y, 0)))
        # Добавить в список отработанный нод. Ближайшая позиция = курсор - восстановленное направление
        list_nodes.append((field_xy.length + field_en, nd, pick_pos - field_xy * ToSign(field_uv)))
    list_nodes.sort(key=lambda list_nodes: list_nodes[0])
    return list_nodes


def gen_nearest_sockets_list(nd,
                             pick_pos):  # Выдаёт список "ближайших сокетов". Честное поле расстояний ячейками Вороного.
    list_socket_in = []
    list_socket_out = []
    # Обработать исключающую ситуацию, когда искать не у кого
    if nd is None:
        return [], []
    # Так же расшифровать иерархию родителей, как и в поиске ближайшего нода, потому что теперь ищутся сокеты
    nd_location = recr_get_node_final_loc(nd)
    nd_dim = Vector(nd.dimensions / ui_scale())
    # Если рероут, то имеем простой вариант не требующий вычисления, вход и выход всего одни, позиция сокета -- он сам
    if nd.bl_idname == 'NodeReroute':
        len = Vector(pick_pos - nd_location).length
        list_socket_in.append([len, nd.inputs[0], nd_location, (-1, -1)])
        list_socket_out.append([len, nd.outputs[0], nd_location, (-1, -1)])
        return list_socket_in, list_socket_out

    def GetFromPut(side_mark, who_puts):
        list_whom = []
        # Установить "каретку" в первый сокет своей стороны. Верхний если выход, нижний если вход
        sk_loc_car = Vector((nd_location.x + nd_dim.x, nd_location.y - 35)) if side_mark == 1 else Vector(
            (nd_location.x, nd_location.y - nd_dim.y + 16))
        for wh in who_puts:
            # Игнорировать выключенные и спрятанные
            if not (wh.enabled and not wh.hide): continue

            muv = 0  # для высоты варпа от вектор-сокетов-не-в-одну-строчку.
            # Если текущий сокет -- входящий вектор, и он же свободный и не спрятан в одну строчку
            if (side_mark == -1) and (wh.type == 'VECTOR') and (wh.is_linked is False) and (wh.hide_value is False):
                # Ручками вычисляем занимаемую высоту сокета.
                # Для сферы направления у ShaderNodeNormal и таких же у групп. И для особо-отличившихся нод с векторами, которые могут быть в одну строчку
                if str(wh.bl_rna).find('VectorDirection') != -1:
                    sk_loc_car.y += 20 * 2
                    muv = 2
                elif (nd.type not in ('BSDF_PRINCIPLED', 'SUBSURFACE_SCATTERING')) or (
                        (wh.name not in ('Subsurface Radius', 'Radius'))):
                    sk_loc_car.y += 30 * 2
                    muv = 3
            goal_pos = sk_loc_car.copy()
            # skHigLigHei так же учитывает текущую высоту мульти-инпута подсчётом количества соединений, но только для входов
            list_whom.append([
                (pick_pos - sk_loc_car).length,
                wh,
                goal_pos,
                (goal_pos.y - 11 - muv * 20, goal_pos.y + 11 + max(
                    length(wh.links) - 2, 0) * 5 * (side_mark == -1))
            ])

            # Сдвинуть до следующего на своё направление
            sk_loc_car.y -= 22 * side_mark
        return list_whom

    list_socket_in = GetFromPut(-1, reversed(nd.inputs))
    list_socket_out = GetFromPut(1, nd.outputs)
    list_socket_in.sort(key=lambda list_socket_in: list_socket_in[0])
    list_socket_out.sort(key=lambda list_socket_out: list_socket_out[0])
    return list_socket_in, list_socket_out


list_sk_perms = ['VALUE', 'RGBA', 'VECTOR', 'INT', 'BOOLEAN']

def voronoi_Linker_draw_callback(sender, context):
    if gv_where[0] != context.space_data:
        return
    gv_shaders[0] = gpu.shader.from_builtin('2D_SMOOTH_COLOR')
    gv_shaders[1] = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    # bgl.glHint(bgl.GL_LINE_SMOOTH_HINT, bgl.GL_NICEST)
    if get_addon_prefs().ds_is_draw_debug:
        debug_draw_callback(sender, context)
        return
    mouse_pos = context.space_data.cursor_location * gv_uifac[0]
    lw = get_addon_prefs().ds_line_width

    def LinkerDrawSk(Sk):
        txtdim = draw_sk_text(pos_view_to_reg(mouse_pos.x, mouse_pos.y),
                              -get_addon_prefs().ds_text_dist_from_cursor * (Sk.is_output * 2 - 1), -.5, Sk)
        if Sk.is_linked:
            draw_is_linked(mouse_pos, -txtdim[0] * (Sk.is_output * 2 - 1), 0,
                           get_sk_col(Sk) if get_addon_prefs().ds_is_colored_marker else (.9, .9, .9, 1))

    if (sender.list_sk_goal_out == []):
        if get_addon_prefs().ds_is_draw_point:
            wp1 = prepar_get_wp(mouse_pos, -get_addon_prefs().ds_point_offset_x * .75)
            wp2 = prepar_get_wp(mouse_pos, get_addon_prefs().ds_point_offset_x * .75)
            draw_wide_point(wp1[0], wp1[1])
            draw_wide_point(wp2[0], wp2[1])
        if (get_addon_prefs().vlds_is_always_line) and (get_addon_prefs().ds_is_draw_line):
            draw_line(wp1[0], wp2[0], lw, (1, 1, 1, 1), (1, 1, 1, 1))
    elif (sender.list_sk_goal_out) and (sender.list_sk_goal_in == []):
        draw_rectangle_on_socket(sender.list_sk_goal_out[1], sender.list_sk_goal_out[3],
                                 get_sk_vec_col(sender.list_sk_goal_out[1], 2.2))
        wp1 = prepar_get_wp(sender.list_sk_goal_out[2] * gv_uifac[0], get_addon_prefs().ds_point_offset_x)
        wp2 = prepar_get_wp(mouse_pos, 0)
        if (get_addon_prefs().vlds_is_always_line) and (get_addon_prefs().ds_is_draw_line):
            draw_line(wp1[0], wp2[0], lw,
                      get_sk_col(sender.list_sk_goal_out[1]) if get_addon_prefs().ds_is_colored_line else (1, 1, 1, 1),
                      (1, 1, 1, 1))
        if get_addon_prefs().ds_is_draw_point:
            draw_wide_point(wp1[0], wp1[1], get_sk_vec_col(sender.list_sk_goal_out[1], 2.2))
            draw_wide_point(wp2[0], wp2[1])
        LinkerDrawSk(sender.list_sk_goal_out[1])
    else:
        draw_rectangle_on_socket(sender.list_sk_goal_out[1], sender.list_sk_goal_out[3],
                                 get_sk_vec_col(sender.list_sk_goal_out[1], 2.2))
        draw_rectangle_on_socket(sender.list_sk_goal_in[1], sender.list_sk_goal_in[3],
                                 get_sk_vec_col(sender.list_sk_goal_in[1], 2.2))
        if get_addon_prefs().ds_is_colored_line:
            col1 = get_sk_col(sender.list_sk_goal_out[1])
            col2 = get_sk_col(sender.list_sk_goal_in[1])
        else:
            col1 = (1, 1, 1, 1)
            col2 = (1, 1, 1, 1)
        wp1 = prepar_get_wp(sender.list_sk_goal_out[2] * gv_uifac[0], get_addon_prefs().ds_point_offset_x)
        wp2 = prepar_get_wp(sender.list_sk_goal_in[2] * gv_uifac[0], -get_addon_prefs().ds_point_offset_x)
        if get_addon_prefs().ds_is_draw_line:
            draw_line(wp1[0], wp2[0], lw, col1, col2)
        if get_addon_prefs().ds_is_draw_point:
            draw_wide_point(wp1[0], wp1[1], get_sk_vec_col(sender.list_sk_goal_out[1], 2.2))
            draw_wide_point(wp2[0], wp2[1], get_sk_vec_col(sender.list_sk_goal_in[1], 2.2))
        LinkerDrawSk(sender.list_sk_goal_out[1])
        LinkerDrawSk(sender.list_sk_goal_in[1])

def voronoi_mass_linker_draw_callback(sender, context):
    if gv_where[0] != context.space_data:
        return
    gv_shaders[0] = gpu.shader.from_builtin('2D_SMOOTH_COLOR')
    gv_shaders[1] = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    # bgl.glHint(bgl.GL_LINE_SMOOTH_HINT, bgl.GL_NICEST)
    if get_addon_prefs().ds_is_draw_debug:
        debug_draw_callback(sender, context)
        return
    mouse_pos = context.space_data.cursor_location * gv_uifac[0]
    lw = get_addon_prefs().ds_line_width

    def LinkerDrawSk(Sk):
        txtdim = draw_sk_text(pos_view_to_reg(mouse_pos.x, mouse_pos.y),
                              -get_addon_prefs().ds_text_dist_from_cursor * (Sk.is_output * 2 - 1), -.5, Sk)
        if Sk.is_linked:
            draw_is_linked(mouse_pos, -txtdim[0] * (Sk.is_output * 2 - 1), 0,
                           get_sk_col(Sk) if get_addon_prefs().ds_is_colored_marker else (.9, .9, .9, 1))

    def DrawIfNone():
        wp = prepar_get_wp(mouse_pos, 0)
        draw_wide_point(wp[0], wp[1])

    if (sender.nd_goal_out is None):
        DrawIfNone()
    elif (sender.nd_goal_out) and (sender.nd_goal_in is None):
        list_Sks = gen_nearest_sockets_list(sender.nd_goal_out, mouse_pos)[1]
        if list_Sks == []:
            DrawIfNone()
        for lsk in list_Sks:
            draw_rectangle_on_socket(lsk[1], lsk[3], get_sk_vec_col(lsk[1], 2.2))
            wp1 = prepar_get_wp(lsk[2] * gv_uifac[0], get_addon_prefs().ds_point_offset_x)
            wp2 = prepar_get_wp(mouse_pos, 0)
            if (get_addon_prefs().vlds_is_always_line) and (get_addon_prefs().ds_is_draw_line):
                draw_line(wp1[0], wp2[0], lw,
                          get_sk_col(lsk[1]) if get_addon_prefs().ds_is_colored_line else (1, 1, 1, 1),
                          (1, 1, 1, 1))
            if get_addon_prefs().ds_is_draw_point:
                draw_wide_point(wp1[0], wp1[1], get_sk_vec_col(lsk[1], 2.2))
                draw_wide_point(wp2[0], wp2[1])
    else:
        list_SksOut = gen_nearest_sockets_list(sender.nd_goal_out, mouse_pos)[1]
        list_SksIn = gen_nearest_sockets_list(sender.nd_goal_in, mouse_pos)[0]
        sender.list_equalSks = []
        for sko in list_SksOut:
            for ski in list_SksIn:
                if (sko[1].name == ski[1].name) and (ski[1].is_linked is False):
                    sender.list_equalSks.append((sko, ski))
                    continue
        if sender.list_equalSks == []:
            DrawIfNone()
        for lsks in sender.list_equalSks:
            draw_rectangle_on_socket(lsks[0][1], lsks[0][3], get_sk_vec_col(lsks[0][1], 2.2))
            draw_rectangle_on_socket(lsks[1][1], lsks[1][3], get_sk_vec_col(lsks[1][1], 2.2))
            if get_addon_prefs().ds_is_colored_line:
                col1 = get_sk_col(lsks[0][1])
                col2 = get_sk_col(lsks[1][1])
            else:
                col1 = (1, 1, 1, 1)
                col2 = (1, 1, 1, 1)
            wp1 = prepar_get_wp(lsks[0][2] * gv_uifac[0], get_addon_prefs().ds_point_offset_x)
            wp2 = prepar_get_wp(lsks[1][2] * gv_uifac[0], -get_addon_prefs().ds_point_offset_x)
            if get_addon_prefs().ds_is_draw_line:
                draw_line(wp1[0], wp2[0], lw, col1, col2)
            if get_addon_prefs().ds_is_draw_point:
                draw_wide_point(wp1[0], wp1[1], get_sk_vec_col(lsks[0][1], 2.2))
                draw_wide_point(wp2[0], wp2[1], get_sk_vec_col(lsks[1][1], 2.2))
