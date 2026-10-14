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

# The tool registry's surfaces in Edit Mesh (tools/preview_poly.luc).
POLY_SCENES = ["poly_marking_edges", "poly_menu_faces", "poly_marking_select", "poly_checker", "poly_marking_disabled"]
# Selection in Edit Mesh (tools/preview_select.luc).
SELECT_SCENES = ["select_d_edges", "select_d_faces", "select_loop", "select_ring", "select_path", "select_similar", "select_hide"]
# Drags after tools and the interactive tools in Edit Mesh (tools/preview_drag.luc).
DRAG_SCENES = ["drag_extrude", "drag_extrude_lock", "drag_bevel", "loopcut_hover", "loopcut_slide", "edge_slide", "drag_cad_node", "revolve_face"]
# Bevel in full in Edit Mesh (tools/preview_bevel.luc).
BEVEL_SCENES = ["bevel_box", "bevel_corner", "bevel_vertex", "bevel_miter", "bevel_custom", "bevel_keys"]
# The everyday modify tools in Edit Mesh (tools/preview_modify.luc).
MODIFY_SCENES = ["modify_knife", "modify_knife_cut", "modify_bridge", "modify_bridge_pick", "modify_bridge_runs", "modify_grid_fill", "modify_solidify", "modify_poke", "modify_rip", "modify_symmetrize", "modify_screw", "modify_decimate", "modify_subdivide"]
# Primitives, Poly Pen and retopology in Edit Mesh (tools/preview_create.luc).
CREATE_SCENES = ["create_gallery", "create_box", "create_surface", "pen_strip", "retopo_sphere", "retopo_shrinkwrap"]
# The shape, topology and normals tools in Edit Mesh (tools/preview_shape.luc).
SHAPE_SCENES = ["shape_circularize", "shape_hole", "shape_straighten", "shape_space", "shape_planar", "normals_recalculated", "normals_hard", "normals_angle", "normals_seams"]
# Edit Mesh holding its result (tools/preview_held.luc).
HELD_SCENES = ["held_boxes", "held_boolean", "held_subtract", "held_cad", "held_sdf", "held_drag", "held_heavy", "held_heavy_running"]

# Stage 8's deformers, sculpt and Mesh Check (tools/preview_deform.luc).
DEFORM_SCENES = ["deform_bend", "deform_twist", "deform_lattice", "sculpt_draw", "sculpt_drag", "mesh_check", "hard_marks"]
# The viewport tool shelf (tools/preview_shelf.luc).
SHELF_SCENES = ["shelf_mesh", "shelf_cad", "shelf_full_screen", "shelf_quad", "shelf_disabled"]
# Icon review: the A/S/D marking menus per place, networks of many node kinds (tools/preview_icons.luc).
ICON_SCENES = [f"icons_{p}_{k}" for p in ["mesh", "cad", "sketch", "direct"] for k in "asd"] + ["icons_direct_none_s", "icons_net_geo", "icons_net_cad", "icons_net_scene", "icons_net_shader", "icons_net_fields"]
# The viewport's panes and cameras (tools/preview_viewport.luc).
VIEWPORT_SCENES = ["view_quad", "view_maximized", "view_full_screen", "view_camera_menu", "view_cube", "view_top_grid", "view_look_through", "view_cad_quad", "view_wire_quad", "view_cad_raised"]

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--scene", choices=["default", "context_menu", "freeze_flags", "light_move", "camera_move", "outline_cad", "outline_splats", "outline_volume", "selection_cad", "selection_patch", "selection_splats", "contexts", "contexts_menu", "edit", "modeling", "spreadsheet", "occlusion", "menu", "shading", "outliner", "cad", "cad_wire", "analytic", "gizmo_move", "gizmo_rotate", "gizmo_scale", "gizmo_pivot", "param_copy", "param_ladder", "param_menu", "render", "shader", "takes", "objects", "cad_node", "cad_round", "cad_corners", "cad_smooth", "cad_twice", "cad_twice_chamfer", "cad_pick", "cad_peek", "cad_sketch", "ux_tools", "sketch_curves", "sketch_polygon", "sketch_trim", "sketch_snap", "project", "splats", "script", "render_mode", "project_settings", "timeline", "grid", "nested", "create_menu", "create_menu_geo", "modify_menu", "marquee_components", "marquee_objects", "marquee_network", "nothing_selected", "through_depth", "sketch_marquee", "node_menu", "canvas_menu", "cad_glyphs", "cad_window", "cad_profiles", "cad_extrude", "cad_face_menu", "cad_rollback", "cad_marking", "cad_edge_menu", "cad_dims", "cad_typing", "cad_dim_edit", "cad_face_sketch", "cad_lost", "cad_slice", "cad_auto", "cad_face_open", "cad_origin", "cad_typed", "cad_conflict", "cad_project_face", "cad_project_body", "cad_project_silhouette", "cad_two_sides", "cad_to_object", "cad_revolve", "cad_axis_pick", "cad_press_pull", "cad_fillet_arrow", "cad_g3_chain", "cad_chamfer_types", "cad_rule_fillet", "direct_sketch", "direct_extrude", "direct_menu", "direct_face_menu", "direct_marking", "direct_face_sketch", "direct_move_face", "direct_offset", "direct_shell", "direct_failed", "direct_combine", "direct_axis", "direct_sketches", "direct_sketch_menu", "cad_crossing", "cad_repeat", "cad_filter", "cad_thin", "cad_face_extrude", "cad_through", "cad_bodies", "cad_revolve_to", "cad_full_round", "cad_chamfer_corner", "cad_chamfer_blend", "cad_shown_sketch", "cad_variable", "cad_setback", "cad_variable_chain", "cad_variable_slanted", "cad_round_rib", "cad_round_rib_g2", "cad_round_drafted", "cad_round_rib_end", "cad_cv_nets", "cad_sketch_point", "cad_tangency", "cad_dome_chamfer", "cad_dome_fillet", "cad_dome_fillet_g2", "cad_flat_shaft_g2", "cad_flat_shaft_g1", "cad_flat_shaft_g3", "cad_dome_fillet_g3", "cad_dome_chamfer_angle", "cad_variable_cone", "cad_variable_chain_rolled", "cad_variable_slanted_rolled", "cad_dome_rolled", "cad_plate_chain", "cad_plate_chain_variable", "modify_shell", "modify_face_menu", "modify_marking", "modify_combine", "modify_move", "modify_split_face", "modify_split_edge", "timeline_strip", "timeline_rolled", "timeline_refused", "surf_check", "surf_check_g1", "surf_check_g3", "surf_combs", "surf_deviation", "surf_band", "surf_draft", "surf_cv_nuv", "surf_cv_row", "surf_rebuild", "surf_insert", "surf_convert", "surf_insert_click", "surf_curves", "surf_curve_menu", "surf_blend", "surf_blend_g4", "surf_curve_cvs", "surf_blend_node", "surf_blend_handles", "surf_stretch", "surf_isoparm", "surf_curve_combs", "surf_project", "surf_trim_markers", "surf_trim_keep", "surf_divide", "surf_surface_menu", "surf_intersect", "surf_stitch", "surf_project_node", "surf_align_waiting", "surf_align", "surf_align_proxy", "surf_align_isoparm", "surf_align_node", "surf_symmetry", "surf_trim_3d", "surf_square_waiting", "surf_square", "surf_square_node", "surf_skin", "surf_rail", "surf_profile", "surf_planar", "surf_sheets", "surf_extend", "surf_cap", "surf_square_picks", "surf_blend_isoparms", "surf_rail_spine", "surf_skin_crown", "surf_fillet_waiting", "surf_fillet", "surf_blend", "surf_blend_profile", "surf_tube", "surf_blend_node", "surf_fill_waiting", "surf_fill_quad", "surf_fill_lid", "surf_fill_lid_g2", "surf_fill_molded", "surf_fill_nsided", "surf_fill_node", "surf_fillet_variable", "surf8_conic", "surf8_g2_depth", "surf8_limits", "surf8_setback", "surf8_bridge", "surf8_corner", "surf8_corner_center", "surf8_corner_g2", "cad_fillet_step", "cad_fillet_sets", "cad_variable_corner", "cad_fillet_step_sets", "cad_reblend"] + [f"tutorial_p{k}" for k in range(12)] + [f"tutorial_d{k}" for k in range(10)] + ["tutorial_rolled", "tutorial_forward", "kernel_crossed_pipes", "kernel_holed_ball", "kernel_tee", "kernel_coincident", "kernel_six_holes", "kernel_shell", "kernel_overflow", "kernel_cliff", "kernel_rounded_shell", "kernel_apex", "kernel_apex_g1", "kernel_moved_top", "kernel_healed_corner", "kernel_thin_stitch", "kernel_g2_shell", "kernel_cliff_edge", "kernel_rolled_on", "kernel_y_boss", "kernel_y_boss_g2", "kernel_y_ell", "kernel_mixed_g2", "kernel_vertex_blend", "kernel_inside_rolled", "kernel_notch_end", "kernel_three_sided", "kernel_ell_shell"] + VIEWPORT_SCENES + POLY_SCENES + SELECT_SCENES + DRAG_SCENES + BEVEL_SCENES + MODIFY_SCENES + CREATE_SCENES + SHAPE_SCENES + HELD_SCENES + DEFORM_SCENES + ICON_SCENES + SHELF_SCENES, default="default")
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
    shutil.copy2(ROOT / "tools/preview_build.luc", project / "src/preview_build.luc")
    shutil.copy2(ROOT / "tools/preview_blend.luc", project / "src/preview_blend.luc")
    shutil.copy2(ROOT / "tools/preview_fill.luc", project / "src/preview_fill.luc")
    shutil.copy2(ROOT / "tools/preview_corner.luc", project / "src/preview_corner.luc")
    shutil.copy2(ROOT / "tools/preview_support.luc", project / "src/preview_support.luc")
    # The tutorial scenes build the part with the end-to-end test's own code.
    shutil.copy2(ROOT / "tools/preview_tutorial.luc", project / "src/preview_tutorial.luc")
    shutil.copy2(ROOT / "tools/preview_kernel.luc", project / "src/preview_kernel.luc")
    shutil.copy2(ROOT / "tools/preview_viewport.luc", project / "src/preview_viewport.luc")
    shutil.copy2(ROOT / "tools/preview_poly.luc", project / "src/preview_poly.luc")
    shutil.copy2(ROOT / "tools/preview_select.luc", project / "src/preview_select.luc")
    shutil.copy2(ROOT / "tools/preview_drag.luc", project / "src/preview_drag.luc")
    shutil.copy2(ROOT / "tools/preview_bevel.luc", project / "src/preview_bevel.luc")
    shutil.copy2(ROOT / "tools/preview_modify.luc", project / "src/preview_modify.luc")
    shutil.copy2(ROOT / "tools/preview_create.luc", project / "src/preview_create.luc")
    shutil.copy2(ROOT / "tools/preview_shape.luc", project / "src/preview_shape.luc")
    shutil.copy2(ROOT / "tools/preview_held.luc", project / "src/preview_held.luc")
    shutil.copy2(ROOT / "tools/preview_deform.luc", project / "src/preview_deform.luc")
    shutil.copy2(ROOT / "tools/preview_icons.luc", project / "src/preview_icons.luc")
    shutil.copy2(ROOT / "tools/preview_shelf.luc", project / "src/preview_shelf.luc")
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
