# Midnight Dev Toolkit - Tools
# Godot-specific utilities.
#
# Roadmap:
# - Collision shape helpers
# - Material/shader helpers
# - Scene organization tools

import os

import bpy

# Naming convention, in channel order (index 0 first).
UV_CHANNEL_NAMES = ["UV_master", "UV_additional"]


class MDT_OT_SetupUV(bpy.types.Operator):
    bl_idname = "mdt.setup_uv"
    bl_label = "Setup UV Channels"
    bl_description = (
        "Rename existing UV channels to the naming convention and create any "
        "that are missing (UV_master, then UV_additional)"
    )
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return bool(cls._targets(context))

    @staticmethod
    def _targets(context):
        objs = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if not objs and context.active_object and context.active_object.type == 'MESH':
            objs = [context.active_object]
        return objs

    def execute(self, context):
        targets = self._targets(context)
        if not targets:
            self.report({'WARNING'}, "No mesh object selected")
            return {'CANCELLED'}

        for obj in targets:
            self._setup_object(obj)

        self.report({'INFO'}, f"UV channels set up on {len(targets)} object(s)")
        return {'FINISHED'}

    @staticmethod
    def _setup_object(obj):
        uv_layers = obj.data.uv_layers

        # First rename the existing channels (up to the number we manage) to
        # temporary names, so assigning the final names can't collide with a
        # channel that already carries one of those names in the wrong slot.
        existing = list(uv_layers)[:len(UV_CHANNEL_NAMES)]
        for i, layer in enumerate(existing):
            layer.name = f"__mdt_uv_tmp_{i}"

        # Rename what exists, create what's missing - preserving channel order.
        for i, name in enumerate(UV_CHANNEL_NAMES):
            if i < len(uv_layers):
                uv_layers[i].name = name
            else:
                uv_layers.new(name=name, do_init=True)


def _read_rgba(image, target_wh):
    """Return the image's pixels as an (N, 4) float array at target resolution.

    Works on a COPY so the user's source image is never modified: we force the
    copy to Non-Color (so we read the raw stored values, not sRGB-decoded ones)
    and resize it to the target if needed."""
    import numpy as np

    tmp = image.copy()
    try:
        tmp.colorspace_settings.name = 'Non-Color'
    except (TypeError, RuntimeError):
        pass
    if tuple(tmp.size) != tuple(target_wh):
        tmp.scale(target_wh[0], target_wh[1])

    count = target_wh[0] * target_wh[1] * 4
    buf = np.empty(count, dtype=np.float32)
    tmp.pixels.foreach_get(buf)
    bpy.data.images.remove(tmp)
    return buf.reshape(-1, 4)


class MDT_OT_PackChannels(bpy.types.Operator):
    bl_idname = "mdt.pack_channels"
    bl_label = "Pack & Export"
    bl_description = (
        "Pack the R/G/B/A slots into a single texture and export it with linear "
        "(Non-Color) values"
    )
    bl_options = {'REGISTER'}

    def execute(self, context):
        import numpy as np

        p = context.scene.mdt_packer

        if not p.output_path.strip():
            self.report({'ERROR'}, "Set an output path first")
            return {'CANCELLED'}

        # Which slots feed the output, depending on the R-slot mode.
        if p.add_only_a:
            if p.slot_r is None:
                self.report({'ERROR'}, "'Add only A' needs a full RGB texture in the R slot")
                return {'CANCELLED'}
            used = [img for img in (p.slot_r, p.slot_a) if img is not None]
        elif p.r_is_normal:
            if p.slot_r is None:
                self.report({'ERROR'}, "R is marked as normal map but no image is loaded in the R slot")
                return {'CANCELLED'}
            used = [img for img in (p.slot_r, p.slot_b, p.slot_a) if img is not None]
        else:
            used = [img for img in (p.slot_r, p.slot_g, p.slot_b, p.slot_a) if img is not None]

        if not used:
            self.report({'ERROR'}, "Load at least one texture")
            return {'CANCELLED'}

        # Target resolution = first loaded slot; everything else gets resized.
        target = tuple(used[0].size)
        if target[0] == 0 or target[1] == 0:
            self.report({'ERROR'}, "First loaded image has no pixel data")
            return {'CANCELLED'}
        n = target[0] * target[1]

        resized = [img.name for img in used if tuple(img.size) != target]

        # Read every distinct source once.
        cache = {img.name: _read_rgba(img, target) for img in used}

        out = np.empty((n, 4), dtype=np.float32)
        out[:, 3] = 1.0  # default alpha = opaque

        if p.add_only_a:
            # R slot holds a full RGB texture; copy RGB as-is, add alpha only.
            rgb = cache[p.slot_r.name]
            out[:, 0] = rgb[:, 0]
            out[:, 1] = rgb[:, 1]
            out[:, 2] = rgb[:, 2]
            if p.slot_a:
                out[:, 3] = cache[p.slot_a.name][:, 0]
        elif p.r_is_normal:
            nrm = cache[p.slot_r.name]
            out[:, 0] = nrm[:, 0]      # normal R
            out[:, 1] = nrm[:, 1]      # normal G
            out[:, 2] = cache[p.slot_b.name][:, 0] if p.slot_b else 0.0
            if p.slot_a:
                out[:, 3] = cache[p.slot_a.name][:, 0]
        else:
            out[:, 0] = cache[p.slot_r.name][:, 0] if p.slot_r else 0.0
            out[:, 1] = cache[p.slot_g.name][:, 0] if p.slot_g else 0.0
            out[:, 2] = cache[p.slot_b.name][:, 0] if p.slot_b else 0.0
            if p.slot_a:
                out[:, 3] = cache[p.slot_a.name][:, 0]

        # Resolve and prepare the output file path.
        out_path = bpy.path.abspath(p.output_path)
        if os.path.splitext(out_path)[1] == "":
            out_path = os.path.join(out_path, "packed.png")
        try:
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
        except OSError as e:
            self.report({'ERROR'}, f"Could not create output directory: {e}")
            return {'CANCELLED'}

        # Build the image and save raw (Non-Color) values - no sRGB encoding.
        packed = bpy.data.images.new("mdt_packed", target[0], target[1], alpha=True)
        try:
            packed.colorspace_settings.name = 'Non-Color'
            packed.pixels.foreach_set(out.reshape(-1))
            packed.filepath_raw = out_path
            packed.file_format = 'PNG'
            packed.save()
        except (RuntimeError, TypeError) as e:
            self.report({'ERROR'}, f"Failed to save packed texture: {e}")
            return {'CANCELLED'}
        finally:
            bpy.data.images.remove(packed)

        if resized:
            self.report({'WARNING'}, f"Resized to {target[0]}x{target[1]}: {', '.join(resized)}")
        self.report({'INFO'}, f"Packed texture exported: {out_path}")
        return {'FINISHED'}


classes = (
    MDT_OT_SetupUV,
    MDT_OT_PackChannels,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
