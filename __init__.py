bl_info = {
    'name': 'Voronoi Linker',
    'author': 'ugorek',
    'version': (1, 9, 1),
    'blender': (3, 5, 0),  # 05.04.2023
    'description': 'Simplification of create node links.', 'location': 'Node Editor > Alt + RMB',
    'warning': '',
    'category': 'Node',
    'wiki_url': 'https://github.com/ugorek000/VoronoiLinker/blob/main/README.md',
    'tracker_url': 'https://github.com/ugorek000/VoronoiLinker/issues'
}

from . import ops,prefs,translation

def register():
    ops.register()
    prefs.register()
    translation.register()

def unregister():
    translation.unregister()
    ops.unregister()
    prefs.unregister()