import bpy


class MDT_PT_MainPanel(bpy.types.Panel):
    bl_label = "Midnight Dev Toolkit"
    bl_idname = "MDT_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Midnight"

    def draw(self, context):
        layout = self.layout
        props = context.scene.mdt

        # Export settings
        box = layout.box()
        box.label(text="GLB Export", icon='EXPORT')
        box.prop(props, "export_path")
        box.prop(props, "export_mode")
        box.prop(props, "export_selected")

        box.separator()
        box.operator("mdt.export_glb", icon='FILE_TICK')

        # Tools placeholder
        box = layout.box()
        box.label(text="Tools", icon='TOOL_SETTINGS')
        box.label(text="Coming soon...", icon='TIME')


classes = (
    MDT_PT_MainPanel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
