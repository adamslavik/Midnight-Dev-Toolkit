# Per-asset-type glTF export settings.
#
# Each profile is a dict of keyword arguments passed to bpy.ops.export_scene.gltf.
# Keys that don't exist in the running Blender's glTF exporter are filtered out
# by operators.py before the call, so a renamed/removed option never crashes.

# Prop: static, non-skinned mesh with baked custom normals. Materials are
# exported, but texture images are NOT embedded (textures have their own,
# separate export pipeline).
PROP = {
    'export_apply': False,          # export model has no modifiers
    'export_normals': True,         # baked custom split normals
    'export_tangents': True,        # needed for normal maps
    'export_texcoords': True,       # UV_master / UV_additional
    'export_vertex_color': 'ACTIVE',  # always export the active RGBA color attribute
    'export_materials': 'EXPORT',
    'export_image_format': 'NONE',  # don't embed textures - exported separately
    'export_skins': False,          # non-skinned
    'export_animations': False,     # static
    'export_cameras': False,
    'export_lights': False,
    'export_extras': True,          # pass custom properties through to Godot
}


EXPORT_PROFILES = {
    'PROP': PROP,
    # VEHICLE / CHUNK / CHARACTER: to be defined - fall back to exporter defaults.
}


def get_profile(asset_type):
    """Return the glTF export kwargs for an asset type (empty dict if undefined)."""
    return dict(EXPORT_PROFILES.get(asset_type, {}))
