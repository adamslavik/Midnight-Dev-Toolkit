import bpy
from bpy.props import StringProperty, EnumProperty, BoolProperty, PointerProperty

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


def _on_r_is_normal(self, context):
    # 'R is normal map' and 'Add only A' are mutually exclusive R-slot modes.
    if self.r_is_normal:
        self.add_only_a = False


def _on_add_only_a(self, context):
    if self.add_only_a:
        self.r_is_normal = False


class MDT_PackerProperties(bpy.types.PropertyGroup):
    slot_r: PointerProperty(name="R", type=bpy.types.Image)
    slot_g: PointerProperty(name="G", type=bpy.types.Image)
    slot_b: PointerProperty(name="B", type=bpy.types.Image)
    slot_a: PointerProperty(name="A", type=bpy.types.Image)

    r_is_normal: BoolProperty(
        name="R is Normal Map",
        description="Treat the R slot as a normal map: its R and G fill the output R and G, "
                    "the blue channel is discarded (reconstruct it in the Godot shader)",
        default=False,
        update=_on_r_is_normal,
    )

    add_only_a: BoolProperty(
        name="Add only A",
        description="Use the R slot as a full RGB texture and only add an alpha channel "
                    "from the A slot (RGB is copied unchanged)",
        default=False,
        update=_on_add_only_a,
    )

    output_path: StringProperty(
        name="Output",
        description="Where to save the packed texture (linear / Non-Color PNG)",
        default="//packed.png",
        subtype='FILE_PATH',
    )


def register():
    bpy.utils.register_class(MDT_SceneProperties)
    bpy.utils.register_class(MDT_PackerProperties)
    bpy.types.Scene.mdt = bpy.props.PointerProperty(type=MDT_SceneProperties)
    bpy.types.Scene.mdt_packer = bpy.props.PointerProperty(type=MDT_PackerProperties)


def unregister():
    del bpy.types.Scene.mdt_packer
    del bpy.types.Scene.mdt
    bpy.utils.unregister_class(MDT_PackerProperties)
    bpy.utils.unregister_class(MDT_SceneProperties)
