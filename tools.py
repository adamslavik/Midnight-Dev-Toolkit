# Midnight Dev Toolkit - Tools
# Godot-specific utilities.
#
# Roadmap:
# - Collision shape helpers
# - Material/shader helpers
# - Scene organization tools

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


classes = (
    MDT_OT_SetupUV,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
