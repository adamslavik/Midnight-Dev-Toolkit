import bpy
import os


class MDT_OT_ExportGLB(bpy.types.Operator):
    bl_idname = "mdt.export_glb"
    bl_label = "Export GLB"
    bl_description = "Export scene to GLB for Godot"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.mdt
        export_path = bpy.path.abspath(props.export_path)

        if not os.path.exists(export_path):
            os.makedirs(export_path)

        if props.export_mode == 'SINGLE':
            self.export_single(context, export_path, props)
        else:
            self.export_batch(context, export_path, props)

        return {'FINISHED'}

    def export_single(self, context, export_path, props):
        filename = bpy.path.basename(bpy.data.filepath) or "untitled"
        filename = os.path.splitext(filename)[0]
        filepath = os.path.join(export_path, f"{filename}.glb")

        bpy.ops.export_scene.gltf(
            filepath=filepath,
            export_format='GLB',
            use_selection=props.export_selected,
            export_apply=True,
        )

        self.report({'INFO'}, f"Exported: {filepath}")

    def export_batch(self, context, export_path, props):
        if props.export_selected:
            objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        else:
            objects = [obj for obj in context.scene.objects if obj.type == 'MESH']

        if not objects:
            self.report({'WARNING'}, "No mesh objects to export")
            return

        original_selection = context.selected_objects[:]
        original_active = context.view_layer.objects.active

        for obj in objects:
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj

            filepath = os.path.join(export_path, f"{obj.name}.glb")

            bpy.ops.export_scene.gltf(
                filepath=filepath,
                export_format='GLB',
                use_selection=True,
                export_apply=True,
            )

        # Restore selection
        bpy.ops.object.select_all(action='DESELECT')
        for obj in original_selection:
            obj.select_set(True)
        context.view_layer.objects.active = original_active

        self.report({'INFO'}, f"Batch exported {len(objects)} objects to: {export_path}")


classes = (
    MDT_OT_ExportGLB,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
