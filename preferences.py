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
    """Read the installed addon version from blender_manifest.toml.

    Evaluated at import time, so after a successful update + script reload the
    module is re-imported and this reflects the freshly copied manifest."""
    manifest = os.path.join(PACKAGE_DIR, "blender_manifest.toml")
    try:
        import tomllib
        with open(manifest, "rb") as f:
            return tomllib.load(f).get("version", "unknown")
    except (OSError, ValueError, ImportError):
        return "unknown"


ADDON_VERSION = _read_manifest_version()


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
    """Run after the operator returns, so we don't unregister mid-execute."""
    bpy.ops.script.reload()
    return None  # one-shot timer


class MDT_OT_UpdateAddon(bpy.types.Operator):
    bl_idname = "mdt.update_addon"
    bl_label = "Update Addon From Disk"
    bl_description = "Copy the addon files from the update source and reload Blender's scripts"
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

        self.report({'INFO'}, f"Updated {copied} file(s). Reloading scripts...")
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

        layout.label(text=f"Installed version: {ADDON_VERSION}", icon='CHECKMARK')

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
