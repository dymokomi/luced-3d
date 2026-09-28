# Large-file engine audit — September 27, 2026

**Follow-up:** [mapped CAD patches and analytic normals](CAD_MAPPED_PATCHES_2026-09-27.md)
supersedes this report's camera mesh counts, distance samples and CAD-normal
limitations. GPU performance numbers below belong to the earlier measured mesh.

This is a measured improvement, **not full CAD support or Blender performance
parity**. Desktop reference files are read-only test inputs, never substituted
for STEP geometry. Low-level runtime changes are original Luce Base; the editor and
test orchestration remain Luce/Python. No luced-2d, luce-ui or compiler changes.

## Reproduced causes and implemented changes

- The recorded OBJ crash was an out-of-bounds write into a fixed 65,536-corner
  attribute buffer. A bounded preflight now counts positions, faces, corners,
  UVs and normals before allocating. Imported attributes attach during mesh
  construction, without rebuilding the topology/BVH for each one.
- Shaded-wire camera redraws transformed/expanded/copied the entire mesh on
  the CPU. `luce-gpu.Geometry` now retains immutable vertex/endpoint buffers.
  Camera changes send a 112-byte parameter block per batch. A shared GLSL vertex
  shader projects geometry and clips/expands constant-pixel-width lines. Metal
  and Vulkan implementations retain resources through submission completion.
  Large batches split below Vulkan's guaranteed 128 MiB storage-buffer range.
- Flat/smooth buffers are independent cached views; toggling wire visibility
  does not evaluate the DAG. First use still compiles/uploads that view's cache.
- Polygon attribute-only edits now share immutable topology and BVH on the same
  thread. Worker hand-off still makes an independently owned native copy.
  BVH node storage grows on demand instead of reserving two nodes per triangle.
  Construction now gathers triangle bounds once, avoiding repeated indirect
  corner/point reads at every recursive tree level.
- Polygon overlay preparation runs in bulk Base calls on the compute worker,
  avoiding millions of Luce vector objects and per-corner interop calls.
- No-op display placements reuse their source mesh. When the selected mesh is
  also displayed, one native transfer supplies both scene and inspector owners.
- NURBS sampling evaluates only the active `(degree+1)^2` controls, using binary
  knot-span lookup and local basis functions. Immutable CAD nets validate once.
- Trimmed spline-edge intervals are recovered from topology endpoints. STEP
  entity and topology lookups have input-sized/hash-based allocation. Error
  messages identify failing CAD faces and STEP spline-edge entity IDs.
- NURBS interiors refine against geometric surface-to-polygon deviation, with
  one shared split point per internal edge. Boundary IDs remain unchanged.
  This is bounded sampling (eight passes), not a certified Hausdorff bound.

## Local measurements

Optimized native builds (`--opt 2`), one local run unless stated otherwise.
Simultaneous compilation and desktop activity make these diagnostic numbers,
not a controlled benchmark. Time units do not imply nanosecond accuracy.

| Check | Result |
| --- | --- |
| Camera shaded-wire CPU full UI recording, old path | 171.505 ms/frame |
| Same fixture, retained GPU recording path | 0.452 ms/frame before refinement; 0.477 ms with the final refined mesh |
| Final camera STEP tessellation | 8.17 s; 352,972 points, 548,310 faces (157,542 quads) |
| Final camera topology audit | 0 open, non-manifold or inconsistently oriented edges |
| Camera OBJ import | 106,015 points / 211,938 triangles, about 1.05 s |
| Camera_2 OBJ import | 75,483 points / 150,958 triangles, about 0.68 s |
| Car1 OBJ import | 2,083,174 points / 4,171,276 triangles, 22.4 s |
| Car2 OBJ import | 2,789,315 points / 5,578,454 triangles, 28.6 s → 22.24 s after BVH bounds gathering |
| Car2 shaded-wire native orbit, 300 callbacks after 35 warm-up callbacks | 8.27 ms mean / 9.12 ms worst, timer-driven camera input |

These last two rows are importer-only timings. The first full car2 application
capture timed out at 180 seconds. After removing redundant copies, a real
shaded-wire capture succeeded. Native sampling during its transform found the
worker inside BVH construction (2.6 GiB sampled footprint, 2.9 GiB peak), while
the UI continued drawing/waiting for events. After bounds gathering and no-op
Transform reuse, the original-orientation car reached viewport preparation at
22.57 s and completed background computation at 40.92 s; the final orbit run
completed background work in 33.52 s. Initial GPU preparation and upload are
additional costs. This is still slow startup, not a claim of instant loading.
Camera OBJ also passed the complete DAG/viewport capture. At this car's high
edge density, shaded-wire becomes visually dark at the overview scale; these
timings do not establish wire-overlay readability or large-mesh editing speed.

The record benchmark does **not** submit GPU work or measure input-to-photon
latency. Native orbit runs observed approximately 16.7 ms frame callbacks in an
earlier run and 1.93 ms (worst 2.83 ms) in a later run; presentation/window state
was not controlled sufficiently to interpret that difference as a speedup.
The car orbit test uses a 1 ms repeating input timer and excludes the capture
transition from its measured callbacks. An earlier harness produced a one-second
outlier; that harness did not isolate idle scheduling/capture costs and is not a
valid rendering-stall measurement. The corrected test has no such outlier.
These remain event-loop intervals, not measured display refresh or input latency.
Native Metal image captures separately verify that geometry is actually drawn.
After the final BVH change, the combined camera STEP import/tessellation plus
reference OBJ import measured 7.44 s, with unchanged counts and distance samples.

`surface_delta.py` uses the production BVH for 4,096 deterministic samples in
each direction (vertices and triangle centroids). For the same OBJ samples,
maximum OBJ-to-STEP distance improved **0.587493 → 0.0548802 source units**;
RMS improved approximately **0.02935 → 0.00597**. The old worst point was on
LensBody; the final worst sample is on Body15. Final STEP-to-OBJ maximum is
0.0747378. Those samples change with tessellation, so that direction is not an
identical-point before/after comparison. These are global nearest-surface
samples with CAD-part attribution, not a certified or fully part-paired metric.

## Known corpus failures and next engine work

- `camera_2.step`: imports 618 faces / 1,371 edges, but face 81 has a projected
  boundary residual 0.010088 against file tolerance 0.01. No tolerance inflation
  or dropped face is hidden behind a successful result.
- `car1.step`: edge #93693 / spline #61161 has endpoint residual 1.58559e-5
  against declared tolerance 1e-5. The previously unsupported subinterval case
  now has an implementation and synthetic regression, but this file still fails.
- `car2.step`: imports 5,015 faces / 11,278 edges. Face 44 stalls trim
  triangulation. Face 4 also needs excessive refinement (113,280 polygons in
  isolation). This is not a production-quality conversion of the car.
- Planar boundary-to-interior fans and irregular transition triangles remain.
  Next: robust constrained triangulation predicates, p-curves/per-edge UV
  parameter correspondence, explicit bounded healing with diagnostics, shared
  curvature/angle-driven edge sampling, then quality-controlled remeshing.
- CAD normals are still averaged polygon normals within each analytic face;
  exact analytic derivative normals remain work to do.
- Import is whole-file, not streaming. Large-mesh copies, initial world/light
  preparation, normal-guide storage and first GPU upload remain sizable costs.
  Indexed device buffers, lazy guides, transform uniforms and staged uploads
  are the next polygon/display steps. Dense component-mode picking/overlays
  need their own benchmark; object-mode timings do not cover them.
- Vulkan has cross-target compilation/link validation here, **not runtime
  verification**. Test the retained path on actual Windows/Linux GPU hardware.
  No vsync or shared event-loop policy was changed.

## Source studies

Blender's [mesh batch cache](https://github.com/blender/blender/blob/main/source/blender/draw/intern/draw_cache_impl_mesh.cc)
and [wire overlay](https://github.com/blender/blender/blob/main/source/blender/draw/engines/overlay/overlay_wireframe.hh)
informed retaining geometry separately from view state. Its
[OBJ reader](https://github.com/blender/blender/blob/main/source/blender/io/wavefront_obj/importer/obj_import_file_reader.cc)
and [mesh importer](https://github.com/blender/blender/blob/main/source/blender/io/wavefront_obj/importer/obj_import_mesh.cc)
informed validation and staging; no GPL code was copied.

OCCT's [face discretization](https://github.com/Open-Cascade-SAS/OCCT/blob/master/src/ModelingAlgorithms/TKMesh/BRepMesh/BRepMesh_FaceDiscret.cxx)
and [STEP tolerance management](https://github.com/Open-Cascade-SAS/OCCT/blob/master/dox/user_guides/step/step.md)
reinforce that independent geometry may require healing beyond the declared
file precision. That needs a bounded, inspectable policy, not arbitrary epsilon
changes or silently omitting inconvenient patches.

## Reproduction

```sh
python3 tests/run.py
python3 tools/corpus_probe.py /path/to/camera.obj /path/to/car1.obj /path/to/car2.obj
python3 tools/cad_probe.py /path/to/camera.step --opt 2
python3 tools/surface_delta.py /path/to/camera.step /path/to/camera.obj
LUCE_PROFILE_OPT=2 python3 tools/profile.py mesh /path/to/camera.step wire gpu
LUCE_PROFILE_OPT=2 python3 tools/profile.py mesh /path/to/camera.step wire native
python3 tools/preview.py --scene cad_wire --file /path/to/camera.obj --background --opt 2
python3 tools/preview.py --scene cad_wire --file /path/to/car2.obj --background --opt 2 --orbit
luc build --release
```

Use the sibling GPU/3D package test gates as well. GPU tests cover retained-only
frames, depth, viewport pixels, owner destruction before submission, allocator
cleanup, native optimization levels, C comparison modes and optional-platform
linkage. Polygon tests inject allocation failure through 96 stages and verify
that attribute snapshots survive closing their original mesh.

Final local gates passed: all 15 editor behavior groups; optimized app build
and native bundle smoke; 3D native optimization/C backend suites and Metal pixel
tests with API/GPU validation; GPU ownership/allocation/pixel and cross-target
link gates. No packages were published. Released-compiler/registry-install gates
are still required before publishing, and Vulkan needs hardware verification.
