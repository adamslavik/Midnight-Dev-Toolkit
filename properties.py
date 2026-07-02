import bpy
from bpy.props import StringProperty, EnumProperty

EXPORT_COLLECTION_NAME = "Export"


def ensure_export_collection(context):
    """Create the 'Export' collection if it doesn't exist yet and link it to
    the scene. Idempotent: an existing collection is reused, never recreated."""
    coll = bpy.data.collections.get(EXPORT_COLLECTION_NAME)
    if coll is None:
        coll = bpy.data.collections.new(EXPORT_COLLECTION_NAME)

    scene_children = context.scene.collection.children
    if scene_children.get(EXPORT_COLLECTION_NAME) is None:
        scene_children.link(coll)

    return coll


def _on_asset_type_changed(self, context):
    # Selecting an asset type creates the Export collection (only if missing).
    ensure_export_collection(context)


class MDT_SceneProperties(bpy.types.PropertyGroup):
    asset_type: EnumProperty(
        name="Asset Type",
        description="Type of asset being exported to Godot",
        items=[
            ('VEHICLE', "Vehicle", "Vehicle asset"),
            ('CHUNK', "Chunk", "World chunk / terrain piece"),
            ('CHARACTER', "Character", "Character asset"),
            ('PROP', "Prop", "Prop / static asset"),
        ],
        default='VEHICLE',
        update=_on_asset_type_changed,
    )

    export_path: StringProperty(
        name="Export Path",
        description="Directory where GLB files will be exported",
        default="//export/",
        subtype='DIR_PATH',
    )

    export_mode: EnumProperty(
        name="Export Mode",
        description="How to export objects from the Export collection",
        items=[
            ('SINGLE', "Single File", "Export the whole Export collection as one GLB file"),
            ('BATCH', "Batch Export", "Export each object in the Export collection as a separate GLB file"),
        ],
        default='SINGLE',
    )


def register():
    bpy.utils.register_class(MDT_SceneProperties)
    bpy.types.Scene.mdt = bpy.props.PointerProperty(type=MDT_SceneProperties)


def unregister():
    del bpy.types.Scene.mdt
    bpy.utils.unregister_class(MDT_SceneProperties)
