# Small-scale diagonals, ear remainders, and planned-face diagnostics

This is ongoing robustness work, not a claim that the camera or car corpus is
pristine. The File node's STEP fitting tolerance remains unchanged. Numerical
conditioning guards below are not user tolerance overrides.

## Changes

- Interior triangle improvement formerly used an absolute area floor of 1e-12.
  That suppressed useful diagonal flips on small CAD details, leaving slivers
  that subsequent surface refinement could collapse. It now uses a relative
  squared-length guard with a 1e-30 floor. Existing canonical seam exclusions
  remain. This is a conservative floating-point flip test, **not** an exact
  incircle predicate or a certified Delaunay mesher.
- Ear clipping could consume the usable interior and strand dozens of sampled
  straight-edge vertices as a microscopic residual polygon. The last-four-ear
  check did not cover this. It now tracks usable convex corners and rejects a
  removal that would leave none. Only the two neighboring corners need updates.
  This is a necessary feasibility check, not a complete backtracking algorithm.
  No constrained vertex is discarded, merged, moved, or snapped.
- If a single-loop greedy ear path still stalls, one area-centroid interior
  seed is permitted only if it lies on the positive side of **every** original
  segment, every wedge is numerically conditioned, and the area agrees. This
  explicitly verifies visibility rather than drawing arbitrary fan spokes.
  Holes cannot take this fallback. It seeds the existing lattice/flip/pairing
  pipeline; it is not a new quad mesher. A bounded backtracking experiment did
  not resolve the reproduced case and was removed rather than retained.
- Parallel face jobs stop assigning new work after a failure, join the earlier
  in-flight jobs, then report the first failing face in source order before
  assembling any partial output. Failed models no longer cook every later face.
- Very close views of small offset parts could project a Transform axis label
  outside the GPU image-region limit and abort the viewport frame. Labels are
  now culled outside the viewport; potentially visible axis lines remain drawn
  and GPU-clipped. Move/Rotate/Scale/Pivot close-up rendering is covered by a test.

## Diagnostic workflow

`CadModel.planned_face` / `BrepModel.planned_face` compute the complete shared
edge/layout plan, then run only the chosen final face job. They preserve source
face attributes, planned boundary stations, retained display triangles, and
analytic normals. Unused points are compacted. Independent non-B-rep patches
are intentionally unsupported. This lets a failing assembly be inspected
without substituting a differently planned isolated preview.

```
python3 tools/cad_probe.py /path/model.step --planned --patch 720 --stats --opt 2
python3 tools/cad_probe.py /path/model.step --planned --patch 720 --output /tmp/patch.obj --opt 2
```

Success only validates the selected final face, **not** the whole assembly.
The output header records `planned_face`; full cooks record -1. OBJ export at
this checkpoint did not serialize analytic corner N. The subsequent
[canonical-seam audit](CAD_CANONICAL_SEAMS_2026-09-28.md) also found that compaction
discarded N. Thus the original planned/full comparison did not actually establish
preservation of authored normals; both extracted meshes had lost them. The newer
contract compares directly with the original full cook and fixes compaction
before exporting N.

## Evidence so far

- New diagonal regressions cover 36 scale/plane/winding/seam combinations.
- New noisy-straight-boundary regressions cover 1,296 scale/plane/winding/start/
  roundoff-amplitude combinations, preserving every input point and boundary
  edge, triangle orientation, expected polygon counts and area. The 432-case
  pre-fix executable fails with the original stall. An isolated negative control
  disabling the kernel fallback also fails the expanded suite. Both final
  native opt-2 and C release runs pass all **32 test groups**.
- The worker test repeats an intentionally out-of-order failure 16 times; only
  4–7 of 64 jobs may begin, the earlier face wins, and no partial mesh is emitted.
- Planned faces exactly match extracted full-cook corner positions, display
  triangles, normals and strategy/flow attributes on parallel planes, G0 stops,
  incompatible smooth joins, swapped/aligned flow, and curved strips.
- The diagonal fix gets car2 past assembled face 720. Its planned mesh has
  827 points, 25 quads, 1,104 triangles, no nonmanifold/inconsistent edges, and
  zero support-normal fold flags. Native/C quality records agree. This small
  spherical patch is still triangle-heavy and needs a later quality pass.
- A 4400 × 2604 native shaded-wire OBJ capture now completes after fixing the
  remote-pivot label error. It is not a substitute for an analytic-normal capture
  or a full-car success check: [planned face 720](preview_car2_planned720.png).
- Before the ear-remainder fix, car2 next failed face 1019. Its trace stranded
  58 (then 14 in fallback) boundary samples within a roughly 8e-17-wide chart
  strip. The repaired planned face has **57 quads and 3,919 triangles**, zero
  folded display triangles, and no poor-quad flags at the reported thresholds.
  Native and C quality records agree. The exported patch has 2,539 points,
  all 1,043 expected open boundary segments, no nonmanifold/inconsistent edges,
  and Euler characteristic 1. Its triangle-heavy strategy still needs a separate
  quality/performance pass. The [large native shaded-wire view](preview_car2_planned1019.png)
  visibly confirms dense triangles and uneven boundary transitions; this is
  **not** a pristine-quad result. The OBJ-based view uses regenerated normals.
- A fresh full car2 cook now passes faces 720 and 1019, then stops at **face
  1290: trim loops cross or touch**. No tolerance was silently increased.
  This is a spherical face in `Car/ShellFrontLeftWing` with six coedge uses;
  edge 2864 appears twice in opposite directions. Its periodic/singular chart
  needs investigation, not removal of the seam. Full car2 is not yet a
  successful tessellation.
- All 2,710 full-camera quality records agree between native and C and remain
  exactly unchanged from the
  preceding collapsed-ribbon checkpoint, including zero fold flags. This work
  does not resolve the camera's separate remaining quad-spacing defects.

Relevant local logs: `/private/tmp/car2-face1019-trim-trace.log`,
`/private/tmp/car2-planned720{,-c}-stats.txt`,
`/private/tmp/planned-face-final-{native,c}.log`, and
`/private/tmp/offscreen-gizmo-tests.log`. Temporary trace printing is removed
from production sources.

Final logs: `/private/tmp/ear-kernel-{native,c}.log`,
`/private/tmp/car2-face1019-kernel.txt`, `/private/tmp/car2-ear-kernel-full.log`,
`/private/tmp/car2-face1019-kernel-c.txt`, `/private/tmp/car2-face1290-topology.txt`,
and `/private/tmp/camera-ear-kernel-{native,c}.txt`. The negative-control package is
`/private/tmp/ear-kernel-negative.nOFJm4/`. The temporary extracted source-data
reproducer was removed; Desktop files remain read-only and untracked.

## Application checkpoint

`build/Luced 3D.app` was rebuilt at **10:40:58 PDT** using released Luce 0.8.18.
The native `--smoke` run exited 0. Logs:
`/private/tmp/ear-kernel-app-{build,smoke}.log`. This replaces the 09:59 build.
No package release was published for this checkpoint. The goal remains active;
remaining camera spacing/flow work, car2 face 1290, camera_2's tolerance failure,
and car1's tolerance/repeated-assembly limitations are not marked resolved.
