#!/usr/bin/env python3
"""Capture a real Metal frame using luce-gpu's observer, without screen access."""
from pathlib import Path
import argparse
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib

ROOT = Path(__file__).resolve().parents[1]


def prepare(project):
    """A copy of the package whose path dependencies point at the siblings."""
    shutil.copytree(ROOT / "src", project / "src")
    manifest = (ROOT / "package.prisma").read_text()
    manifest = re.sub(r'"\.\./([^"]+)"', lambda m: f'"{ROOT.parent / m.group(1)}"', manifest)
    (project / "package.prisma").write_text(manifest)


def build(project, binary, optimization="0"):
    cache = Path(os.environ.get("LUCE_TEST_CACHE", str(ROOT / "build/test-cache")))
    cache.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ, LUCE_CACHE=str(cache))
    subprocess.run([os.environ.get("LUCE", "luce"), "build", str(project / "src/main.luc"), "--native", "--opt", optimization, "-o", str(binary)],
                   check=True, env=environment, timeout=480)

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--scene", choices=["default", "edit", "modeling", "spreadsheet", "occlusion", "menu", "shading", "outliner", "cad", "cad_wire", "analytic", "gizmo_move", "gizmo_rotate", "gizmo_scale", "gizmo_pivot", "param_copy", "param_ladder", "param_menu", "render", "shader", "takes", "objects"], default="default")
parser.add_argument("--background", action="store_true", help="Run actual background graph computation while capturing")
parser.add_argument("--file", type=Path, help="External STEP file for the cad scene")
parser.add_argument("--edge-size", type=float, default=0.0)
parser.add_argument("--tolerance", type=float, default=0.0, help="STEP File-node import tolerance in source units; 0 uses the file")
parser.add_argument("--group", default="", help="Isolate imported object paths through a Blast node")
parser.add_argument("--patch", type=int, default=-1, help="Isolate an original CAD patch AFTER the complete cook, preserving global stations and display triangles")
parser.add_argument("--patch-neighbors", action="store_true", help="Include CAD patches sharing a mesh edge with the selected patch, after the complete cook")
parser.add_argument("--neutral", action="store_true", help="Use neutral material instead of imported Cd for isolated patch inspection")
parser.add_argument("--mode", type=int, choices=range(5), default=3)
parser.add_argument("--output", type=Path)
parser.add_argument("--opt", choices=["0", "1", "2", "3"], default="0")
parser.add_argument("--timeout", type=float, default=180, help="Maximum native capture runtime in seconds")
parser.add_argument("--orbit", action="store_true", help="Time 300 native orbit callbacks after 35 warm-up frames")
parser.add_argument("--zoom", type=float, default=0.75, help="Multiply framed camera distance for reproducible close-ups")
parser.add_argument("--yaw", type=float, default=0.7, help="Camera yaw in radians")
parser.add_argument("--pitch", type=float, default=0.5, help="Camera pitch in radians")
parser.add_argument("--rotation-x", type=float, help="Override model X rotation in degrees")
parser.add_argument("--target", type=float, nargs=3, help="World-space camera target for a reproducible detail capture")
parser.add_argument("--width", type=int, default=2200, help="Requested logical window width (default: 2200)")
parser.add_argument("--height", type=int, default=1400, help="Requested logical window height (default: 1400)")
parser.add_argument("--viewport-only", action="store_true", help="Use the full window for inspecting mesh detail")
arguments = parser.parse_args()
if arguments.patch_neighbors and arguments.patch < 0:
    parser.error("--patch-neighbors requires --patch")
if not 800 <= arguments.width <= 8192 or not 600 <= arguments.height <= 8192:
    parser.error("Capture size must be 800–8192 by 600–8192")


def chunk(tag, payload):
    return struct.pack(">I", len(payload)) + tag + payload + struct.pack(">I", zlib.crc32(tag + payload) & 0xffffffff)


with tempfile.TemporaryDirectory(prefix="luced-3d-preview-") as temporary:
    project = Path(temporary)
    prepare(project)
    shutil.copy2(ROOT / "tools/preview.luc", project / "src/main.luc")
    native = (ROOT.parent / "luce-gpu/tests/gpu/native.lucb").read_text()
    native += "\n" + (ROOT / "tools/readback.lucb").read_text()
    (project / "src/probe.lucb").write_text(native)
    binary = project / "preview"
    build(project, binary, arguments.opt)
    ppm = project / "preview.ppm"
    subprocess.run([str(binary), str(ppm), arguments.scene, str(arguments.file.resolve()) if arguments.file else "", str(arguments.edge_size), str(arguments.mode), "background" if arguments.background else "sync", arguments.group, "orbit" if arguments.orbit else "still", str(arguments.zoom), str(arguments.yaw), str(arguments.pitch), str(arguments.rotation_x) if arguments.rotation_x is not None else "", *(str(value) for value in arguments.target or ["", "", ""]), str(arguments.width), str(arguments.height), "viewport" if arguments.viewport_only else "editor", str(arguments.patch), "neutral" if arguments.neutral else "color", "neighbors" if arguments.patch_neighbors else "single", str(arguments.tolerance)], check=True, timeout=arguments.timeout)
    header, dimensions, maximum, pixels = ppm.read_bytes().split(b"\n", 3)
    assert header == b"P6" and maximum == b"255"
    width, height = map(int, dimensions.split())
    rows = b"".join(b"\0" + pixels[y * width * 3:(y + 1) * width * 3] for y in range(height))
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b"")
    # Captures go to build/; copy a hero image into docs/ by hand when a doc needs it.
    output = arguments.output or ROOT / (f"build/preview_{arguments.scene}.png" if arguments.scene != "default" else "build/preview.png")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(png)
    print(f"{output} ({width} × {height} actual pixels)")
