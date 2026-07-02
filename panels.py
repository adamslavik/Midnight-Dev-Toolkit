import bpy

from . import properties


class MDT_PT_MainPanel(bpy.types.Panel):
    bl_label = "Midnight Dev Toolkit"
    bl_idname = "MDT_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Midnight DTK"

    def draw(self, context):
        layout = self.layout
        props = context.scene.mdt

        # Asset type
        box = layout.box()
        box.label(text="Asset", icon='OBJECT_DATA')
        box.prop(props, "asset_type")
        if bpy.data.collections.get(properties.EXPORT_COLLECTION_NAME) is None:
            box.label(text="Export collection not created yet", icon='INFO')

        # Export settings
        box = layout.box()
        box.label(text="GLB Export", icon='EXPORT')
        box.prop(props, "export_path")
        box.prop(props, "export_mode")

        box.separator()
        box.operator("mdt.export_glb", icon='FILE_TICK')

        # Tools
        box = layout.box()
        box.label(text="Tools", icon='TOOL_SETTINGS')
        box.operator("mdt.setup_uv", icon='UV')


classes = (
    MDT_PT_MainPanel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
