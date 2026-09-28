# CAD quad flow and shading follow-up — September 27, 2026

The later [trim-grid follow-up](CAD_TRIM_GRID_2026-09-27.md) supersedes the
tessellation measurements below and includes new wireframe captures.

This follow-up addresses the lens fillet, shaded streaks and curved-corner fans
in the supplied screenshots. It supersedes the tessellation/normal results in
[the earlier engine audit](ENGINE_AUDIT_2026-09-27.md), not its GPU measurements.
Runtime geometry work is original, platform-independent Luce Base. No compiler,
luce-ui, luce-gpu or luced-2d files were changed in this follow-up.

## Implementation

- Match opposite **logical side** sample counts globally before discretizing
  shared B-rep edges. A side may contain several STEP edges; smooth UV joins no
  longer force an otherwise four-sided patch through general triangulation.
- Use a Coons/transfinite UV grid for suitable planar, NURBS and analytic
  patches. Lift interior samples onto the exact support; reuse boundary IDs.
  Denser samples on either side propagate across the whole patch instead of
  collapsing into a boundary fan. This does not weld unrelated nearby surfaces.
- Sample interior curvature as well as edge curvature. A bulging NURBS patch
  with four straight trims cannot collapse to one flat quad. Simple/straight
  splines use fewer samples within the requested quality budget.
- Check UV Jacobian orientation and every lifted display diagonal. Reject
  folded/collapsed grids and rewind scratch before the constrained fallback.
- Add bounded interior support to complex flat trims. The automatic lattice
  cap is 32 per axis, or the requested divisions if higher. A 64-per-axis
  experiment increased camera tessellation to 14.9 seconds, so it was not kept.
- Generate B-rep corner normals from rational first derivatives or the exact
  analytic surface normal. No averaging across triangles of unequal density.
  Normals are prepared in the native face workers and transformed with the face.
- Raise ordinary File preview quality to 16 divisions (8 for faces with more
  than 32 edge uses), with the existing bounded fallback policy. Curved patch
  outlines now use 64 samples rather than 16, avoiding visibly coarse chords
  cutting behind the displayed surface. Preview meshes remain disposable caches;
  File still outputs analytic CAD, not polygons.

Quality tests are sampled and work-budgeted, not certified chord-error bounds.
Opposite-side count propagation is bounded to 64 passes and 256 intervals per
edge. Incompatible or non-four-sided domains retain the constrained fallback.

## Measured results

Optimized local native runs; these are diagnostic timings, not controlled
cross-platform benchmarks. Desktop STEP/OBJ files are read-only inputs.

| Fixture, 16 divisions | Points | Quads | Triangles | Tessellation |
| --- | ---: | ---: | ---: | ---: |
| camera.step | 594,911 | 537,301 | 115,128 | 6.65 s |
| sign.step | 8,993 | 6,806 | 4,434 | 0.293 s |
| 1p5inR.step | 2,690 | 2,370 | 636 | 0.081 s |
| 33mm_angle.step | 4,065 | 3,562 | 1,006 | 0.084 s |

All four have **zero open, non-manifold and inconsistently oriented edges**.
Their Euler characteristics are respectively 46, -30, 2 and 0. Camera at eight
divisions also passes: 207,183 points, 182,322 quads and 49,630 triangles.

The previous camera had 157,542 quads / 390,768 triangles. Its quad fraction is
now approximately 82%, up from 29%. The whole camera's final background
viewport preparation completed in 9.15 seconds in one native capture run;
GPU upload is additional. The isolated analytic LensBody preview completed
background preparation in 0.82 seconds.

The final 652,429-face mesh still records a full shaded-wire UI frame in
0.488 ms on the retained-GPU path. This benchmark records commands without
submitting GPU work; it is not input-to-display latency or GPU frame time.

All 2,710 isolated camera patches completed at both 8 and 16 divisions, with
zero failures. The full 16-division isolated-patch audit took 15.42 seconds:
higher preview quality has a real startup cost and does not imply instant load.

Using the same 4,096 OBJ-to-STEP samples as before:

- Maximum distance: **0.0548802 → 0.0329782** source units.
- RMS distance: **0.00597 → 0.00303** source units.
- Final STEP-to-OBJ sampled maximum: 0.033951; RMS 0.00289.

STEP sample locations change with the mesh; only the OBJ-to-STEP sample set is
identical across versions. These are global nearest-surface samples, not a
certified Hausdorff metric or a fully part-paired comparison.

## Visually reviewed native Metal captures

These are actual application readbacks, not mockups or reference OBJ renders.

- [Curved corner close-up](preview_corner_mapped.png): continuous quad rows over
  the bend. Remaining triangular transitions on the adjoining plane are visible.
- [Lens shaded wire](preview_lens_mapped.png): mapped fillet rows, with the
  planar trim around its openings also visible.
- [Analytic File lens preview](preview_lens_analytic_normals.png): smooth surface
  normals and denser patch outlines before a Tessellate node.
- [Full camera](preview_camera_mapped.png) and [isolated frame](preview_frame_mapped.png).
- [Sign](preview_sign_mapped.png), [1p5inR](preview_elbow_mapped.png),
  [33mm angle](preview_angle_mapped.png).

The captures are not uniformly all-quad meshes: flat trim transitions, holes,
singular caps and unsupported mapped domains still use triangles/fans. Further
boundary-aware quad decomposition and quality-controlled unstructured meshing
are needed there. This follow-up does not claim those remaining patterns are
clean enough for production retopology.

## Verification and remaining corpus failures

All 16 application behavior groups passed in native builds (unoptimized and
optimized) and the optimized C backend. New tests check a curved-interior patch
with straight boundaries, a curved four-sided patch, valence-four interior
vertices, exact analytic positions/normals, reversed winding, split logical
sides stitched to a cap, and rational normals at repeated endpoint knots in
non-unit parameter domains. Optimized app build and native bundle smoke passed.
The mapped plane path also explicitly rejects boundaries outside the support
plane's tolerance; faster grid construction does not bypass that validation.

`camera_2.step` still fails face 81's boundary/support tolerance check
(0.010088 versus 0.01). `car2.step` now reports face 6's adaptive-face budget
failure. Neither is silently exported with missing faces. This is not a repair
of all earlier corpus failures; no healing tolerance was inflated.

No packages were published. Vulkan was not runtime-tested on this Mac; these
changes contain no new backend-specific drawing code.

## Reproduction

```sh
python3 tests/run.py --opt 2
python3 tests/run.py --opt 2 --backend c
python3 tools/cad_probe.py /path/to/camera.step --opt 2
python3 tools/cad_probe.py /path/to/camera.step --opt 2 --stats
python3 tools/cad_probe.py /path/to/camera.step --opt 2 --preview --divisions 16
python3 tools/surface_delta.py /path/to/camera.step /path/to/camera.obj
python3 tools/preview.py --scene cad_wire --file /path/to/camera.step --background --opt 2 --rotation-x 0 --zoom 0.14 --yaw 0.35 --pitch 0.2 --target 45 29 0
python3 tools/preview.py --scene cad_wire --file /path/to/camera.step --group '*LensBody*' --background --opt 2 --rotation-x 0 --zoom 0.5 --pitch 0.3
```

Group expressions containing spaces must be quoted **inside** the expression,
or use an unambiguous wildcard such as `*/Frame`. The capture harness rejects
an empty polygon output instead of accepting a blank screenshot.

## Source study

The matched-opposite-side approach is described by the
[Gmsh transfinite tutorial](https://gmsh.info/doc/texinfo/#t6).
Its [transfinite mesher source](https://raw.githubusercontent.com/live-clones/gmsh/master/src/mesh/meshGFaceTransfinite.cpp)
was inspected for logical-side and parameter-space handling. The Luce Base
implementation is original; no GPL implementation was copied.
