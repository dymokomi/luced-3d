# Button rims: geometric deviation and retained dissolve triangles

Incremental camera checkpoint after the File-tolerance/import work. No source
STEP/OBJ was modified. This is not a declaration that the camera is pristine or
that the broader Desktop files now load.

## Root causes

The rounded end of Body28 (patch 1463, with the opposite end at 1467) already
had a hard-trim clipped layout. Two later failures unnecessarily sent it back
to constrained triangulation:

1. Agglomerating a grazing cell discarded valid display triangles and ear-clipped
   the polygon union again. That ear order stranded a near-collinear boundary
   fragment. `TopologyTools.dissolve` now preserves the source triangles, checks
   the simple union, and removes only the shared *polygon* edge. No positions or
   boundary vertices change. This also preserves nonplanar polygon surfaces.
2. The CAD deviation validator treated UV barycentric correspondence as geometric
   distance to one particular triangle. A non-affine NURBS parameterization can
   place an exact surface sample across that triangle's display diagonal, even
   on a completely flat support. The observed button sample was 0.0117458 from
   its assigned triangle but **0.00209722 from the same polygon's surface**, against
   the unchanged File tolerance of 0.01. Boundary projection residuals were at
   most 9.23e-7 for that triangle, so increasing import tolerance was not the fix.

The fast triangle check remains. When it misses, the validator checks the other
retained display triangles in that same polygon only. It cannot borrow nearby
faces or a different CAD patch to hide an error. Normal/orientation checks and
the tolerance setting remain unchanged. These are finite sample checks, not a
certified Hausdorff bound.

An experiment preflighting all four-sided NURBS maps did not change the camera
and was removed. No fixture IDs or fixture-specific geometry rules are in the
production changes. Temporary tracing was removed.

## Observed result

Matched native 4400 × 2604 shaded-wire captures, isolated **after the full cook**:

- [Before: button end and immediate neighbors](preview_camera_button1463_before.png)
- [After: button end and immediate neighbors](preview_camera_button1463_cell_error.png)
- [Newly admitted rounded corner patch 1102](preview_camera1102_cell_error.png)

The button's diamond fans are replaced with regular longitudinal strips and
true cut n-gons carrying the unchanged dense shared boundary corners.

| Camera metric | Before | After |
|---|---:|---:|
| Total polygons | 631,302 | 629,153 |
| Quads | 590,565 | 588,961 |
| Triangles | 5,265 | 4,752 |
| Cut n-gons | 35,472 | 35,440 |
| Constrained fallback patches | 24 | 21 |
| Patch 1463 | 259 quads + 217 triangles | 32 cut n-gons |
| Patch 1467 | 259 quads + 217 triangles | 32 cut n-gons |
| Patch 1468 | 3 quads + 107 triangles | 8 cut n-gons |

Only 13 of the 2,710 printed patch quality records changed. Eight other patches
now use their previously rejected clipped grids; two existing clipped patches
accept an additional spacing improvement. Global stretched-20 quad count falls
49,996 → 49,981, while skewed-0.1 count rises **2,097 → 2,099**: newly clipped
1102 and 1127 each have a tiny boundary sliver to inspect/clean up. These raw
metrics include cut cells. They must not be concealed by the global improvement.

Full topology audit: 674,425 points, zero open/nonmanifold/inconsistent edges,
Euler 46, zero folded-display flags. Actual retained-display area is
65,662.51514265097 and signed volume is 74,393.23054639812.

Deterministic reference sampling (4,096 samples each way): fixed OBJ-to-STEP
maximum stays 0.0259126; mean squared distance improves 4.68832e-6 → 4.62886e-6.
STEP-to-OBJ reports max 0.0201382 and mean squared 4.06814e-6, but those source
samples change with the mesh, so this is not a fixed-sample improvement claim.
Reference agreement is not a substitute for support-tolerance checks.

One full camera cook measured 9.77 seconds versus 9.96 for the earlier checkpoint;
these single runs are not a controlled speed benchmark.

## Validation and remaining work

- Full app suite: 31 PASS groups each, native opt-2 and C release.
- All 2,710 current camera patch/quality records match between native and C at
  printed precision, excluding the elapsed-time header.
- 32 synthetic deviation cases: model scale, UV swap, winding and rational
  weights. Nonlinear-parameter planes pass; genuinely under-resolved bulges fail.
- Eight dissolve combinations retain every original triangle's ordered point
  IDs, all positions, and the expected polygon topology; pinched union rejected.
  Direct Base tests pass native opt-2 and C release; native Luce consumers pass.

`camera_2.step` with explicit File tolerance 0.02 still fails at face 95 with
the collapsed/self-intersecting polygon error. It was rechecked, not assumed
fixed by the dissolve change. Other known import/assembly blockers remain in
[the morning report](CAD_IMPORT_ROBUSTNESS_2026-09-28.md).

The remaining camera rim transitions, hard-trim ownership and spacing defects
stay in the active goal. In particular, the two new boundary sliver flags and
the other 21 constrained patches require individual diagnosis. Local work has
not been published to the registry.

Artifacts: `/private/tmp/camera-cell-error-*`, `/private/tmp/cell-error-full-*`,
`/private/tmp/dissolve-3d-final-*`, `/private/tmp/camera2-cell-error-stats.log`.

The main `build/Luced 3D.app` was rebuilt at **08:33:19 PDT** with released Luce
0.8.18 and passed native `--smoke` (exit 0). Build/smoke logs are
`/private/tmp/cell-error-app-build.log` and `/private/tmp/cell-error-app-smoke.log`.
