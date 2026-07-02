import bpy
import os
import shutil
import tempfile
import zipfile

from bpy.props import StringProperty

# The package name Blender registers this addon under (e.g.
# "bl_ext.user_default.midnight_dev_toolkit"). Used to look up our own prefs.
ADDON_ID = __package__

# The directory the addon is currently installed in - update copies land here.
PACKAGE_DIR = os.path.dirname(__file__)

# Only these file types get copied in during an update.
_SOURCE_EXTENSIONS = (".py", ".toml")


def _read_manifest_version():
    """Read the installed addon version fresh from blender_manifest.toml.

    Called on every preferences redraw (not cached), so it always reflects the
    file currently on disk - even if a self-update didn't reload cleanly."""
    manifest = os.path.join(PACKAGE_DIR, "blender_manifest.toml")
    try:
        import tomllib
        with open(manifest, "rb") as f:
            return tomllib.load(f).get("version", "unknown")
    except (OSError, ValueError, ImportError):
        return "unknown"



def _find_manifest_dir(base):
    """Return the directory inside 'base' that holds blender_manifest.toml."""
    for dirpath, _dirs, files in os.walk(base):
        if "blender_manifest.toml" in files:
            return dirpath
    return None


def _resolve_source_root(path):
    """Resolve the update source to a directory containing the addon files.

    Accepts either a .zip (extracted to a temp dir) or a folder. Returns
    (root_dir, tempdir_or_None); the caller must remove tempdir when done.
    """
    path = bpy.path.abspath(path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Path does not exist: {path}")

    if os.path.isfile(path) and path.lower().endswith(".zip"):
        tmp = tempfile.mkdtemp(prefix="mdt_update_")
        with zipfile.ZipFile(path) as zf:
            zf.extractall(tmp)
        root = _find_manifest_dir(tmp)
        if root is None:
            shutil.rmtree(tmp, ignore_errors=True)
            raise FileNotFoundError("blender_manifest.toml not found inside the zip")
        return root, tmp

    if os.path.isdir(path):
        root = _find_manifest_dir(path)
        if root is None:
            raise FileNotFoundError("blender_manifest.toml not found in the folder")
        return root, None

    raise ValueError("Source must be a .zip file or a folder")


def _install_from(root):
    """Copy every .py/.toml file from 'root' into the installed package dir,
    preserving any sub-folder structure. Returns the number of files copied."""
    copied = 0
    for dirpath, _dirs, files in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        dst_dir = PACKAGE_DIR if rel_dir == "." else os.path.join(PACKAGE_DIR, rel_dir)
        for name in files:
            if not name.lower().endswith(_SOURCE_EXTENSIONS):
                continue
            os.makedirs(dst_dir, exist_ok=True)
            shutil.copy2(os.path.join(dirpath, name), os.path.join(dst_dir, name))
            copied += 1
    return copied


def _deferred_reload():
    """Reload ONLY this addon from the freshly copied files.

    Runs from a timer, after the operator returns, so we don't unregister
    ourselves mid-execute. We disable the addon, drop its modules from the
    import cache (so Python re-reads them from disk instead of serving the old
    cached code), then re-enable it. This is far more reliable than a global
    script reload, which can leave an extension unregistered and 'gone'."""
    import sys
    import addon_utils

    try:
        addon_utils.disable(ADDON_ID, default_set=False)
    except Exception as e:  # noqa: BLE001 - never let the timer raise
        print(f"[Midnight Dev Toolkit] disable during update failed: {e}")

    for name in [n for n in list(sys.modules) if n == ADDON_ID or n.startswith(ADDON_ID + ".")]:
        del sys.modules[name]

    try:
        addon_utils.enable(ADDON_ID, default_set=True, persistent=True)
        print("[Midnight Dev Toolkit] reloaded after update")
    except Exception as e:  # noqa: BLE001
        print(f"[Midnight Dev Toolkit] re-enable during update failed: {e}")

    return None  # one-shot timer


class MDT_OT_UpdateAddon(bpy.types.Operator):
    bl_idname = "mdt.update_addon"
    bl_label = "Update Addon From Disk"
    bl_description = "Copy the addon files from the update source and reload the addon"
    bl_options = {'REGISTER'}

    def execute(self, context):
        prefs = context.preferences.addons[ADDON_ID].preferences
        source = prefs.update_source.strip()
        if not source:
            self.report({'ERROR'}, "Set the update source path first")
            return {'CANCELLED'}

        tmp = None
        try:
            root, tmp = _resolve_source_root(source)
            if os.path.normcase(os.path.abspath(root)) == os.path.normcase(os.path.abspath(PACKAGE_DIR)):
                self.report({'ERROR'}, "Source is the installed addon itself - nothing to update")
                return {'CANCELLED'}
            copied = _install_from(root)
        except (FileNotFoundError, ValueError, zipfile.BadZipFile, OSError) as e:
            self.report({'ERROR'}, f"Update failed: {e}")
            return {'CANCELLED'}
        finally:
            if tmp:
                shutil.rmtree(tmp, ignore_errors=True)

        if copied == 0:
            self.report({'WARNING'}, "No .py/.toml files found to copy")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Updated {copied} file(s). Reloading addon...")
        bpy.app.timers.register(_deferred_reload, first_interval=0.1)
        return {'FINISHED'}


class MDT_Preferences(bpy.types.AddonPreferences):
    bl_idname = ADDON_ID

    update_source: StringProperty(
        name="Update Source",
        description="Path to the addon .zip file or source folder on disk",
        subtype='FILE_PATH',
    )

    def draw(self, context):
        layout = self.layout

        layout.label(text=f"Version on disk (live): {_read_manifest_version()}", icon='CHECKMARK')

        col = layout.column(align=True)
        col.label(text="Local update - point to a .zip or a source folder:")
        col.prop(self, "update_source", text="")
        col.operator("mdt.update_addon", icon='FILE_REFRESH')


classes = (
    MDT_OT_UpdateAddon,
    MDT_Preferences,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
