import bpy
import os
import re

from . import properties
from . import profiles


def _sanitize_filename(name):
    """Replace characters that are illegal in filenames on Windows/Godot."""
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', name).strip()
    return cleaned or "unnamed"


def _filter_gltf_kwargs(kwargs):
    """Drop any keys the running Blender's glTF exporter doesn't know about,
    so a renamed/removed option can never crash the export. Returns
    (valid_kwargs, dropped_keys)."""
    valid_keys = set(bpy.ops.export_scene.gltf.get_rna_type().properties.keys())
    valid = {k: v for k, v in kwargs.items() if k in valid_keys}
    dropped = [k for k in kwargs if k not in valid_keys]
    return valid, dropped


class MDT_OT_ExportGLB(bpy.types.Operator):
    bl_idname = "mdt.export_glb"
    bl_label = "Export GLB"
    bl_description = "Export the Export collection to GLB for Godot"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.mdt

        if not props.export_path.strip():
            self.report({'ERROR'}, "Export path is not set")
            return {'CANCELLED'}

        export_path = bpy.path.abspath(props.export_path)

        try:
            os.makedirs(export_path, exist_ok=True)
        except OSError as e:
            self.report({'ERROR'}, f"Could not create export directory: {e}")
            return {'CANCELLED'}

        coll = bpy.data.collections.get(properties.EXPORT_COLLECTION_NAME)
        if coll is None:
            self.report(
                {'ERROR'},
                f"'{properties.EXPORT_COLLECTION_NAME}' collection not found. Select an asset type first.",
            )
            return {'CANCELLED'}

        objects = [obj for obj in coll.all_objects if obj.type == 'MESH']
        if not objects:
            self.report(
                {'WARNING'},
                f"No mesh objects in '{properties.EXPORT_COLLECTION_NAME}' collection",
            )
            return {'CANCELLED'}

        # Build the export settings from the asset-type profile.
        gltf_kwargs = {'export_format': 'GLB', 'use_selection': True}
        gltf_kwargs.update(profiles.get_profile(props.asset_type))
        gltf_kwargs, dropped = _filter_gltf_kwargs(gltf_kwargs)
        if dropped:
            self.report({'WARNING'}, f"Ignored unsupported export options: {', '.join(dropped)}")

        # Object operators used below (select_all, etc.) require Object Mode, so
        # switch out of Edit/Sculpt/Vertex Paint/... and restore the mode after.
        active = context.view_layer.objects.active
        prev_mode = active.mode if active else 'OBJECT'
        if prev_mode != 'OBJECT':
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except RuntimeError as e:
                self.report({'ERROR'}, f"Could not switch to Object Mode: {e}")
                return {'CANCELLED'}

        try:
            if props.export_mode == 'SINGLE':
                return self.export_single(context, export_path, objects, gltf_kwargs)
            return self.export_batch(context, export_path, objects, gltf_kwargs)
        finally:
            if prev_mode != 'OBJECT' and active is not None:
                context.view_layer.objects.active = active
                try:
                    bpy.ops.object.mode_set(mode=prev_mode)
                except RuntimeError:
                    pass  # object may no longer support that mode; leave in Object Mode

    def export_single(self, context, export_path, objects, gltf_kwargs):
        filename = os.path.splitext(bpy.path.basename(bpy.data.filepath))[0] or "untitled"
        filepath = os.path.join(export_path, f"{_sanitize_filename(filename)}.glb")

        original_selection = context.selected_objects[:]
        original_active = context.view_layer.objects.active
        try:
            bpy.ops.object.select_all(action='DESELECT')
            for obj in objects:
                obj.select_set(True)
            context.view_layer.objects.active = objects[0]

            bpy.ops.export_scene.gltf(filepath=filepath, **gltf_kwargs)
        except (RuntimeError, TypeError) as e:
            self.report({'ERROR'}, f"Export failed: {e}")
            return {'CANCELLED'}
        finally:
            self._restore_selection(context, original_selection, original_active)

        self.report({'INFO'}, f"Exported: {filepath}")
        return {'FINISHED'}

    def export_batch(self, context, export_path, objects, gltf_kwargs):
        original_selection = context.selected_objects[:]
        original_active = context.view_layer.objects.active
        exported = 0
        try:
            for obj in objects:
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                context.view_layer.objects.active = obj

                filepath = os.path.join(export_path, f"{_sanitize_filename(obj.name)}.glb")
                bpy.ops.export_scene.gltf(filepath=filepath, **gltf_kwargs)
                exported += 1
        except (RuntimeError, TypeError) as e:
            self.report({'ERROR'}, f"Export failed on '{obj.name}': {e}")
            return {'CANCELLED'}
        finally:
            self._restore_selection(context, original_selection, original_active)

        self.report({'INFO'}, f"Batch exported {exported} object(s) to: {export_path}")
        return {'FINISHED'}

    @staticmethod
    def _restore_selection(context, selection, active):
        bpy.ops.object.select_all(action='DESELECT')
        for obj in selection:
            try:
                obj.select_set(True)
            except ReferenceError:
                pass  # object was removed during export
        context.view_layer.objects.active = active


classes = (
    MDT_OT_ExportGLB,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
