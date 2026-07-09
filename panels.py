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


class MDT_PT_ToolsPanel(bpy.types.Panel):
    bl_label = "Tools"
    bl_idname = "MDT_PT_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "MDT_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.operator("mdt.setup_uv", icon='UV')


class MDT_PT_ChannelPackerPanel(bpy.types.Panel):
    bl_label = "RGBA Channel Packer"
    bl_idname = "MDT_PT_channel_packer"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "MDT_PT_tools"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        pk = context.scene.mdt_packer

        # Mode toggles first (mutually exclusive, handled in properties).
        col = layout.column(align=True)
        col.prop(pk, "add_only_a")
        if not pk.add_only_a:
            col.prop(pk, "r_is_normal")

        col = layout.column(align=True)

        # R / RGB slot - the channel icon leads the row (no separate label).
        row = col.row(align=True)
        row.label(text="", icon='IMAGE_RGB_ALPHA' if pk.add_only_a else 'RGB_RED')
        row.template_ID(pk, "slot_r", open="image.open")

        # G / B slots are hidden when the R slot already covers them.
        if not pk.add_only_a:
            if pk.r_is_normal:
                col.label(text="G: filled by normal map (R+G)", icon='INFO')
            else:
                row = col.row(align=True)
                row.label(text="", icon='RGB_GREEN')
                row.template_ID(pk, "slot_g", open="image.open")

            row = col.row(align=True)
            row.label(text="", icon='RGB_BLUE')
            row.template_ID(pk, "slot_b", open="image.open")

        row = col.row(align=True)
        row.label(text="", icon='IMAGE_ALPHA')
        row.template_ID(pk, "slot_a", open="image.open")

        layout.separator()
        layout.prop(pk, "output_path")
        layout.operator("mdt.pack_channels", icon='EXPORT')


classes = (
    MDT_PT_MainPanel,
    MDT_PT_ToolsPanel,
    MDT_PT_ChannelPackerPanel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
