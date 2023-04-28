import bpy
import nodeitems_utils

from colorsys import rgb_to_hsv
from colorsys import hsv_to_rgb

node_item_cache = {}


def correct_name(name):
    if name == 'convertor_node':
        return 'converter_node'
    return name


def get_theme_cat_color(type='Input'):
    ne = bpy.context.preferences.themes['Default'].node_editor
    try:
        attr = correct_name(f"{type.lower()}_node")
        clr = getattr(ne, attr)
        clr = list(clr)
        clr.append(0.8)
    except AttributeError:
        clr = (0.1, 0.1, 0.1, 0.8)

    return clr


def darker_color(clr, factor=0.5):
    rgb = clr[:3]
    hsv = rgb_to_hsv(*rgb)
    hsv = (hsv[0], hsv[1], hsv[2] * factor)
    res = hsv_to_rgb(*hsv)
    res = list(res) + [clr[3]]

    return res


def find_geo_nodes_src_code_nodes(cat_name):
    import re
    import inspect as ist

    re_rule = r'node_add_menu.add_node_type\(layout, (.*?)\)'
    cls = getattr(bpy.types, cat_name)
    src = ist.getsource(cls)

    res = re.findall(re_rule, src)

    return res


def get_all_nodes() -> dict:
    nodes = {}  # {category:[node, node, ...], ...}
    node_item_cache.clear()
    # ddir = lambda data, filter_str: [i for i in dir(data) if i.startswith(filter_str)]

    cats = [name for name in dir(bpy.types) if
            name.startswith("NODE_MT_category_") or name.startswith(' NODE_MT_geometry_node')]

    for cat in cats:
        nodes[cat] = {}

        try:
            get_nodes = lambda cat: [i for i in getattr(bpy.types, cat).category.items(None)]
            cat_nodes = get_nodes(cat)
            for node in cat_nodes:
                nodes[cat][node.nodetype] = node.label

        except Exception as e:
            # print(e)
            cat_nodes = find_geo_nodes_src_code_nodes(cat)
            for nodetype in cat_nodes:
                node_id = nodetype[1:-1]  # remove quotes

                if node_id not in node_item_cache:
                    node = nodeitems_utils.NodeItem(node_id)
                    node_item_cache[node_id] = node.label
                else:
                    node = node_item_cache[node_id]

                nodes[cat][node_id] = node.label

    return nodes


def filter_context_node(nodes):
    nt = bpy.context.space_data.node_tree
    ret = {}

    def enumerate_nodes(cat_nodes):
        for cat, node_list in cat_nodes.items():
            if cat.startswith('NODE_MT_category_'):
                cat_name = cat.removeprefix('NODE_MT_category_')
            else:
                cat_name = cat.removeprefix('NODE_MT_geometry_node_')
            yield cat_name, node_list

    if nt.bl_idname == 'CompositorNodeTree':
        for cat_name, node_list in enumerate_nodes(nodes):
            if cat_name.startswith('CMP'):
                ret[cat_name] = node_list

    elif nt.bl_idname == 'ShaderNodeTree':
        for cat_name, node_list in enumerate_nodes(nodes):
            if cat_name.startswith('SH'):
                ret[cat_name] = node_list

    elif nt.bl_idname == 'GeometryNodeTree':
        for cat_name, node_list in enumerate_nodes(nodes):
            if cat_name.startswith('PRIMITIVES') or cat_name.startswith('GEO'):
                ret[cat_name] = node_list

    return ret
