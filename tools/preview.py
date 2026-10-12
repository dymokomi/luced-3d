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
# A trap ends the run: no crash window is started to wait for a click
# (luce-ui's LUCE_CRASH_WINDOW).
os.environ["LUCE_CRASH_WINDOW"] = "0"


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
parser.add_argument("--scene", choices=["default", "context_menu", "freeze_flags", "light_move", "camera_move", "outline_cad", "outline_splats", "outline_volume", "selection_cad", "selection_patch", "selection_splats", "contexts", "contexts_menu", "edit", "modeling", "spreadsheet", "occlusion", "menu", "shading", "outliner", "cad", "cad_wire", "analytic", "gizmo_move", "gizmo_rotate", "gizmo_scale", "gizmo_pivot", "param_copy", "param_ladder", "param_menu", "render", "shader", "takes", "objects", "cad_node", "cad_round", "cad_corners", "cad_smooth", "cad_twice", "cad_twice_chamfer", "cad_pick", "cad_peek", "cad_sketch", "ux_tools", "sketch_curves", "sketch_polygon", "sketch_trim", "sketch_snap", "project", "splats", "script", "render_mode", "project_settings", "timeline", "grid", "nested", "create_menu", "create_menu_geo", "modify_menu", "marquee_components", "marquee_objects", "marquee_network", "nothing_selected", "through_depth", "sketch_marquee", "node_menu", "canvas_menu", "cad_glyphs", "cad_window", "cad_profiles", "cad_extrude", "cad_face_menu", "cad_rollback", "cad_marking", "cad_edge_menu", "cad_dims", "cad_typing", "cad_dim_edit", "cad_face_sketch", "cad_lost", "cad_slice", "cad_auto", "cad_face_open", "cad_origin", "cad_typed", "cad_conflict", "cad_project_face", "cad_project_body", "cad_project_silhouette", "cad_two_sides", "cad_to_object", "cad_revolve", "cad_axis_pick", "cad_press_pull", "cad_fillet_arrow", "cad_g3_chain", "cad_chamfer_types", "cad_rule_fillet", "direct_sketch", "direct_extrude", "direct_menu", "direct_face_menu", "direct_marking", "direct_face_sketch", "direct_move_face", "direct_offset", "direct_shell", "direct_failed", "direct_combine", "direct_axis", "direct_sketches", "direct_sketch_menu", "cad_crossing", "cad_repeat", "cad_filter", "cad_thin", "cad_face_extrude", "cad_through", "cad_bodies", "cad_revolve_to", "cad_full_round", "cad_chamfer_corner", "cad_chamfer_blend", "cad_shown_sketch", "cad_variable", "cad_setback", "cad_variable_chain", "cad_variable_slanted", "cad_round_rib", "cad_round_rib_g2", "cad_round_drafted", "cad_round_rib_end", "cad_cv_nets", "cad_sketch_point", "cad_tangency", "cad_dome_chamfer", "cad_dome_fillet", "cad_dome_fillet_g2", "cad_flat_shaft_g2", "cad_flat_shaft_g1", "cad_flat_shaft_g3", "cad_dome_fillet_g3", "cad_dome_chamfer_angle", "cad_variable_cone", "cad_variable_chain_rolled", "cad_variable_slanted_rolled", "cad_dome_rolled", "cad_plate_chain", "cad_plate_chain_variable", "modify_shell", "modify_face_menu", "modify_marking", "modify_combine", "modify_move", "modify_split_face", "modify_split_edge", "timeline_strip", "timeline_rolled", "timeline_refused", "surf_check", "surf_check_g1", "surf_check_g3", "surf_combs", "surf_deviation", "surf_band", "surf_draft", "surf_cv_nuv", "surf_cv_row", "surf_rebuild", "surf_insert", "surf_convert", "surf_insert_click", "surf_curves", "surf_curve_menu", "surf_blend", "surf_blend_g4", "surf_curve_cvs", "surf_blend_node", "surf_blend_handles", "surf_stretch", "surf_isoparm", "surf_curve_combs", "surf_project", "surf_trim_markers", "surf_trim_keep", "surf_divide", "surf_surface_menu", "surf_intersect", "surf_stitch", "surf_project_node"] + [f"tutorial_p{k}" for k in range(12)] + [f"tutorial_d{k}" for k in range(10)] + ["tutorial_rolled", "tutorial_forward", "kernel_holed_ball", "kernel_tee"], default="default")
parser.add_argument("--background", action="store_true", help="Run actual background graph computation while capturing")
parser.add_argument("--file", type=Path, help="External STEP file for the cad scene, the .prisma for the project scene, or a PLY for the splats scene")
parser.add_argument("--edge-size", type=float, default=0.0)
parser.add_argument("--tolerance", type=float, default=0.0, help="STEP File-node import tolerance in source units; 0 uses the file")
parser.add_argument("--group", default="", help="Isolate imported object paths through a Blast node")
parser.add_argument("--patch", type=int, default=-1, help="Isolate an original CAD patch AFTER the complete cook, preserving global stations and display triangles")
parser.add_argument("--patch-neighbors", action="store_true", help="Include CAD patches sharing a mesh edge with the selected patch, after the complete cook")
parser.add_argument("--neutral", action="store_true", help="Use neutral material instead of imported Cd for isolated patch inspection")
parser.add_argument("--mode", type=int, choices=[0, 1, 2, 3, 4, 5, 7, 8, 9, 10], default=3, help="Display mode; 5 render, 7 zebra, 8 isophotes, 9 curvature, 10 draft")
parser.add_argument("--cad-quality", type=int, choices=[8, 16, 32, 64], default=16, help="Viewport CAD mesh divisions")
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
    shutil.copy2(ROOT / "tools/preview_cad.luc", project / "src/preview_cad.luc")
    shutil.copy2(ROOT / "tools/preview_features.luc", project / "src/preview_features.luc")
    shutil.copy2(ROOT / "tools/preview_direct.luc", project / "src/preview_direct.luc")
    shutil.copy2(ROOT / "tools/preview_history.luc", project / "src/preview_history.luc")
    shutil.copy2(ROOT / "tools/preview_parity.luc", project / "src/preview_parity.luc")
    shutil.copy2(ROOT / "tools/preview_parity2.luc", project / "src/preview_parity2.luc")
    shutil.copy2(ROOT / "tools/preview_surfacing.luc", project / "src/preview_surfacing.luc")
    shutil.copy2(ROOT / "tools/preview_align.luc", project / "src/preview_align.luc")
    shutil.copy2(ROOT / "tools/preview_support.luc", project / "src/preview_support.luc")
    # The tutorial scenes build the part with the end-to-end test's own code.
    shutil.copy2(ROOT / "tools/preview_tutorial.luc", project / "src/preview_tutorial.luc")
    shutil.copy2(ROOT / "tools/preview_kernel.luc", project / "src/preview_kernel.luc")
    shutil.copy2(ROOT / "tests/editor/cad_tutorial_tests.luc", project / "src/cad_tutorial_tests.luc")
    shutil.copy2(ROOT / "tests/editor/sketch_support.luc", project / "src/sketch_support.luc")
    native = (ROOT.parent / "luce-gpu/tests/gpu/native.lucb").read_text()
    native += "\n" + (ROOT / "tools/readback.lucb").read_text()
    (project / "src/probe.lucb").write_text(native)
    binary = project / "preview"
    build(project, binary, arguments.opt)
    ppm = project / "preview.ppm"
    subprocess.run([str(binary), str(ppm), arguments.scene, str(arguments.file.resolve()) if arguments.file else "", str(arguments.edge_size), str(arguments.mode), "background" if arguments.background else "sync", arguments.group, "orbit" if arguments.orbit else "still", str(arguments.zoom), str(arguments.yaw), str(arguments.pitch), str(arguments.rotation_x) if arguments.rotation_x is not None else "", *(str(value) for value in arguments.target or ["", "", ""]), str(arguments.width), str(arguments.height), "viewport" if arguments.viewport_only else "editor", str(arguments.patch), "neutral" if arguments.neutral else "color", "neighbors" if arguments.patch_neighbors else "single", str(arguments.tolerance), str(arguments.cad_quality)], check=True, timeout=arguments.timeout)
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
