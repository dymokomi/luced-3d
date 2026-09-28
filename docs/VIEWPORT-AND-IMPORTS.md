# Viewport and imports — 2026-09-27

## Implemented

`luce-3d.WireRenderer` expands world-space endpoint pairs into constant logical-
pixel-width triangles in homogeneous clip space. It clips the near plane and
submits depth-tested batches. The grid stays one logical pixel wide at all camera
distances. This is portable wire rendering, not world-space strips or a
backend-specific wide-line primitive.

Edit edges and selected-face fills share scene depth, so partially hidden edges
are clipped per fragment. The regression capture is `preview_occlusion.png`.
Edge picking tests the perspective-correct point nearest the pointer, not the
edge midpoint. Translation handles intentionally remain on-top UI. Wire AA and
an adaptive infinite grid are not implemented in this pass.

Right-click and Tab open the same cursor-anchored node menu. Empty queries browse
categories; hover/Right opens a submenu, typing searches globally, arrows/Enter
choose, and Escape or an outside click dismisses. No shortcut hints are drawn.
Popup layout clamps to the window. Search currently
accepts ASCII node-name text, not IME composition or clipboard paste.

File has Browse, a path field and explicit Reload. It performs no scaling or
tessellation. STEP produces analytic CAD surfaces; OBJ/FBX produce polygons.
For STEP/STP, File also exposes **STEP tolerance / 0 = file**. Zero selects the
file uncertainty; a positive override (`1e-9` through `1`, source units) governs
boundary agreement and trim projection. The setting is part of the node recipe,
project and undo history; changing it invalidates and recomputes File on the
worker. It is hidden for OBJ/FBX and does not replace Tessellate's density controls.
`File → Transform → Tessellate` changes analytic geometry and then explicitly
creates polygons. Surface divisions belong to Tessellate. Imports enter the
cached DAG with undoable parameters/reloads. No file watching or asynchronous
import yet.

The DAG caches `GeometryData`, currently holding polygon and CAD components,
including mixed results from Merge. Transform preserves analytic control nets;
Null, Switch and bypass preserve the payload. Polygon-only tools reject
CAD with an explicit conversion message. Other families (curves, volumes, etc.)
are not implemented yet. CAD-only output now has a cached display-only mesh and
deduplicated analytic patch boundaries. The DAG and spreadsheet still retain
CAD, not polygons. Preview meshes are batched independently of the whole-model
conversion budget. Failed previews report their count and keep boundary curves.

## Import contracts

All new runtime libraries are **Luce Base**, separate from the Luce editor.

| Package | Working scope | Important exclusions |
| --- | --- | --- |
| luce-obj | Shared positions, polygons, positive/negative indices, corner UVs/N | MTL/textures, curves, vertex-color extensions |
| luce-fbx | ASCII/binary 7.x raw meshes; compressed arrays; 32/64-bit headers | Scene transforms/hierarchy, instances, UV/material layers, animation |
| luce-step | STEP → CAD; shared edges, ellipses, rational splines, colors, unique rigid assemblies | General p-curves, repeated/mapped instances, automatic units |
| luce-cad | Analytic topology, nonperiodic NURBS trims, sphere/torus/cylinder/cone UV trims, per-face previews | General periodic/singular NURBS trims, booleans, disconnected-shell healing |
| luce-tesselator | Rational evaluation, planar trim triangulation, interior edge flips, quad pairing | Adaptive error guarantees, arbitrary curved UV trims, global quad layouts |

FBX imports **mesh-local** definitions: different objects may overlap at their
origins. The UI states this. STEP is not a general CAD importer: unsupported
face/placement topology raises errors. Modeling mesh limits apply to imports.

`Step.load_model` / `decode_model` retain analytic CAD data. The existing mesh
convenience methods delegate to `CadModel.tessellate`; re-tessellation does not
destroy control nets. STEP is no longer responsible for meshing planar faces or
evaluating surfaces. Shared edges stitch the supported B-rep faces without
tolerance welding. See [the real-part audit and remaining coverage](CAD_TESSELLATION.md).
This is not yet a production general-purpose CAD kernel.

The [OBJ format summary](https://www.loc.gov/preservation/digital/formats/fdd/fdd000507.shtml)
explains separate indices and material dependencies. Autodesk's
[importer documentation](https://download.autodesk.com/us/fbx/sdkdocs/fbx_sdk_help/files/fbxsdkprog/WS1a9193826455f5ff-150b16da11960d83164-6a82.htm)
establishes ASCII/binary/version distinctions. Our parser is original Base code.
Downloaded ufbx donor sources are local under `.donors/`, not linked or shipped;
the retained test fixture includes its license.

The [OCCT STEP translator guide](https://github.com/Open-Cascade-SAS/OCCT/blob/master/dox/user_guides/step/step.md)
shows the distinction between geometry, topology, placements and shape
translation. Sampling a support surface alone does not import its trimmed face.
[B-spline schema definitions](https://downloads.steptools.com/docs/cislib/html/t_b_spline_surface.html)
informed the control-net representation. No OCCT dependency is used.

## Blender viewport source study

Blender's [draw manager](https://github.com/blender/blender/blob/main/source/blender/draw/intern/draw_manager.hh)
separates scene synchronization, resource handles, visibility, command generation
and submission. Object matrices/bounds are buffered, and visibility work can be
grouped to reduce transitions. For Luce, the applicable next step is retaining
mesh buffers and updating camera/object uniforms instead of regenerating every
triangle on camera movement.

Its [grid engine](https://github.com/blender/blender/blob/main/source/blender/draw/engines/overlay/overlay_grid.hh)
uses dedicated passes, explicit depth state, procedural lines and view-dependent
grid levels. The [fragment shader](https://github.com/blender/blender/blob/main/source/blender/draw/engines/overlay/shaders/overlay_grid_frag.glsl)
fades with view angle/distance and emits line data for viewport AA. Our depth/
width fix does not reproduce that whole system.

The [GPU state API](https://github.com/blender/blender/blob/main/source/blender/gpu/GPU_state.hh)
and [draw passes](https://github.com/blender/blender/blob/main/source/blender/draw/intern/draw_pass.hh)
make render state explicit. This is a useful portable contract rather than
relying on backend defaults. GPL source was studied, not copied into Luce.

### Proposed luce-gpu work — not applied

1. Separate depth comparison, depth writes and bias from `triangles(depth: bool)`.
   Overlays need testing without writes. Make per-viewport depth scope explicit.
2. Add retained vertex/index buffers and indexed mesh submission, wrapped by
   managed engine objects so Base-only GPU resource types do not break the Luce
   boundary. Then move camera transforms/lighting to shaders.
3. Reuse upload storage: inspected `metal_pass` allocates vertex/coverage buffers
   each frame. The surface also waits for its pending command before drawing.
   Evaluate a bounded in-flight ring with completion tracking; removing waits
   without lifetime tracking is unsafe. Measure latency as well as throughput.
4. Add backend-neutral timestamps and drawable/submission wait counters. CPU
   record time, GPU time, presentation interval and input-to-photon are different
   measurements; vsync alone cannot explain all of them.
5. Add portable wire coverage/AA with Metal/Vulkan tests for depth, near clipping,
   width, display scale and color. Triangle expansion avoids requiring geometry
   shaders and is a useful cross-backend fallback.

Shared UI/GPU sources were not changed. Runtime verification here is on macOS;
Windows/Linux behavior is not claimed tested.

## Verification and release status

Editor tests cover real menu dispatch/bounds, File reload/undo, OBJ attributes,
STEP rational patches, a real binary FBX cube, generated compressed/uncompressed
7.4/7.5 files and malformed input. Assimp independently reported the real cube
as 12 triangles with bounds [-1,1], matching our six quads/12 triangles.
Native captures check the deleted-face view and menu. Engine tests cover Base
and Luce consumers.

Manifests prepare luce-3d 0.1.5 and luced-3d 0.1.1; the engine's UI dependency
range now matches the app's 0.8 minor. Nothing was committed or published.
Before publishing: released-compiler gate, dependency-first publishing, clean
registry install, then platform CI. Local sibling builds do not prove registry
resolution. These follow the project's Claude memory rules read during this task.
