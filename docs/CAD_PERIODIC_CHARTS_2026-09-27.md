# Periodic trim charts — historical investigation

This records the investigation before separate display triangles were implemented.
The previously failing regression below is now resolved; see the
[display/analytic-grid follow-up](CAD_DISPLAY_AND_ANALYTIC_GRIDS_2026-09-28.md)
for current validation and remaining defects. This is not a pristine-camera claim.

## Isolated cause and result

Camera patch 710 (`Camera - 6/Lens:1/Body14`) is a closed NURBS fillet with 13
coedge uses, a repeated seam, and four small holes. Independent coedge projection
can put both uses of the seam on the same UV rail. Even after projecting the
connected loop correctly, the grid clipper rejected it with “one trim identity
has inconsistent UV positions”: a canonical **3D** vertex can have two valid
images on opposite sides of a cut **2D** chart.

`trim_chains.lucb` now projects repeated-seam loops in topological order, retries
the chart's endpoint branches if necessary, rejects jumps across a closed axis,
retains the chosen chart when canonical stations are added, and separates only
verified periodic chart images. Pinched vertices in the same image retain their
explicit identity; nearby unrelated vertices are never welded. Lifting still
uses the original shared 3D IDs. No camera IDs enter the meshing code.

Compared with the compound-side checkpoint at divisions 16 / edge size 0:

| Patch 710 | Before | Periodic chart candidate |
|---|---:|---:|
| Quads | 110 | 3,453 |
| Triangles | 5,516 | 1 |
| Cut n-gons | 0 | 303 |
| Display-normal flags | 237 | 1 |

The full camera has 663,265 points and 649,204 polygons. Its topology audit has
zero open, nonmanifold, or inconsistently oriented edges; Euler characteristic
remains 46. The fixed 4,096 OBJ-to-STEP samples improve from maximum 0.0305709 /
mean-square 8.43064e-6 to maximum 0.0297543 / mean-square 5.83108e-6. The new worst
fixed sample belongs to patch 2358, not 710. Reverse samples depend on the new
mesh and are not a point-for-point comparison. Typical local cooks remain about
8.6 seconds; this is not a viewport frame-time measurement.

Matched native viewport captures, both 4400 × 2604 actual pixels:

- [Before](preview_camera_patch710_before.png)
- [Periodic chart](preview_camera_patch710_chart.png)

The ring now has regular bands and trimmed holes rather than the old fans.
Other camera regions, and the one remaining display-normal flag, still need work.

## Additional regression findings

The new synthetic `periodic_grid_tests.luc` uses a rational closed cylinder with
a rectangular hole, including a reversed seam-start case. It exposed two more
independent issues:

1. A closed isocurve's endpoint chord is zero. Curvature planning must use a
   sampled extent for that case, not exhaust the row budget against a zero scale.
2. Intersection precision must fit the **physical** boundary snap budget. A
   fixed UV residual can exceed that budget on a tight-tolerance curved support,
   leaving a missing cell-side segment. The root target now also uses the local
   edge chord / UV span. Making all roots uniformly ultra-tight was tested and
   rejected: it caused widespread fallback on the camera. The metric-scaled
   target preserves the candidate camera's counts and patch 710 result.

Base contracts also check that same-image IDs alias, unrelated coincident
vertices stay distinct, and an open NURBS support cannot pretend its opposite
rails are periodic.

## Required next step: preserve display triangulation separately

The new regression is intentionally still failing its strict display-normal
assertion. A generic n-gon ear can consist of three points on a curved boundary
run. It is a legal triangle in an averaged projection but points perpendicular
to the actual cylinder support. Example from the regression:

```
(0.929788, 0.368095, 0)
(0.923880, 0.382683, 0)
(0.910273, 0.414008, 0)
cross = (0, 0, 1.34085e-5)  # cylinder normals are radial, not axial
```

Experimentally replacing only affected n-gons with their valid UV triangles
reduced the camera's flags from 1,629 to 256 (53 to 10 patches), including patch
710 to zero. **That experiment was reverted**: promoting display diagonals to
real polygon edges breaks the existing smooth-seam degree-four contract in
`quad_flow_tests.luc:50`. Do not weaken that test or the new normal assertions.

The correct architectural follow-up is an explicit, validated per-face display
triangulation in the low-level polygon engine. CAD already has a valid UV
triangulation for clipped cells; the polygon must retain its real boundary while
using those triangle indices for rendering/picking/deviation. This data must
survive worker assembly, affine/reflected transforms, immutable/worker copies,
merges, subsets and attribute-only snapshots. Geometry/topology edits need a
clear invalidation/retriangulation rule. Do not merely rotate polygon starts,
hide wire edges, or globally tune an ear heuristic against this fixture.

Relevant engine files: `geometries/polygon.lucb`, `builder.lucb`, and
`polygon_triangulation.lucb`; CAD integration: `clipped_cells.lucb`,
`clipped_patch.lucb`, `face_jobs.lucb`, `brep_mesh.lucb`. Existing assembly rebuilds
generic triangulation in `mesh.finish()` and later copies/transforms, so fixing
only the temporary UV mesh is insufficient.

Local diagnostic records (not committed fixture data):

- `/private/tmp/camera-chart-metric-quality.txt`: accepted periodic/metric candidate
- `/private/tmp/camera-chart-full.log`: full topology/area/volume audit
- `/private/tmp/camera-chart-orientation-quality.txt`: **reverted** explicit-triangle experiment
- `/private/tmp/camera-chart-native.log`: latest failing regression run

No new tessellation package has been published and no new app checkpoint has
been promoted from this work-in-progress state. Complete native/C regressions,
full topology and distance audits, and assembled plus isolated native captures
before doing so.
