import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty


class MDT_SceneProperties(bpy.types.PropertyGroup):
    export_path: StringProperty(
        name="Export Path",
        description="Directory where GLB files will be exported",
        default="//export/",
        subtype='DIR_PATH',
    )

    export_selected: BoolProperty(
        name="Selected Only",
        description="Export only selected objects",
        default=False,
    )

    export_mode: EnumProperty(
        name="Export Mode",
        description="How to export objects",
        items=[
            ('SINGLE', "Single File", "Export everything as one GLB file"),
            ('BATCH', "Batch Export", "Export each object as a separate GLB file"),
        ],
        default='SINGLE',
    )


def register():
    bpy.utils.register_class(MDT_SceneProperties)
    bpy.types.Scene.mdt = bpy.props.PointerProperty(type=MDT_SceneProperties)


def unregister():
    del bpy.types.Scene.mdt
    bpy.utils.unregister_class(MDT_SceneProperties)
