#!/usr/bin/env python3
"""Build a distributable Blender extension zip for Midnight Dev Toolkit.

Usage:
    python build.py                # build a zip of the current version
    python build.py --bump patch   # 0.1.1 -> 0.1.2, then build
    python build.py --bump minor   # 0.1.1 -> 0.2.0, then build
    python build.py --bump major   # 0.1.1 -> 1.0.0, then build
    python build.py --set 0.5.0    # set an exact version, then build

Version bumping is OPTIONAL - without --bump/--set the current version in
blender_manifest.toml is used as-is and nothing is modified.
"""

import argparse
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "blender_manifest.toml"

# What ships inside the addon zip. build.py itself is a dev tool, not shipped.
EXTRA_FILES = ["README.md", "LICENSE"]


def read_version():
    text = MANIFEST.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, flags=re.MULTILINE)
    if not match:
        raise SystemExit("Could not find a version in blender_manifest.toml")
    return match.group(1)


def write_version(new_version):
    text = MANIFEST.read_text(encoding="utf-8")
    text = re.sub(
        r'^(version\s*=\s*)"[^"]+"',
        rf'\g<1>"{new_version}"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    MANIFEST.write_text(text, encoding="utf-8")


def bump_version(version, part):
    try:
        major, minor, patch = (int(x) for x in version.split("."))
    except ValueError:
        raise SystemExit(f"Version '{version}' is not in MAJOR.MINOR.PATCH form")
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"  # patch


def collect_files():
    """Every .py (except this build script) plus the manifest and extras."""
    files = [MANIFEST.name]
    files += sorted(p.name for p in ROOT.glob("*.py") if p.name != "build.py")
    files += [name for name in EXTRA_FILES if (ROOT / name).exists()]
    return files


def build(version):
    zip_path = ROOT / f"midnight_dev_toolkit-{version}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for name in collect_files():
            z.write(ROOT / name, name)  # arcname = root of zip
    print(f"Built {zip_path.name}")
    for name in collect_files():
        print(f"   {name}")


def main():
    parser = argparse.ArgumentParser(description="Build the Midnight Dev Toolkit extension zip.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--bump", choices=["major", "minor", "patch"], help="Increase the version before building")
    group.add_argument("--set", dest="set_version", metavar="X.Y.Z", help="Set an exact version before building")
    args = parser.parse_args()

    version = read_version()

    if args.set_version:
        version = args.set_version
        write_version(version)
        print(f"Version set to {version}")
    elif args.bump:
        version = bump_version(version, args.bump)
        write_version(version)
        print(f"Version bumped to {version}")

    build(version)


if __name__ == "__main__":
    main()
