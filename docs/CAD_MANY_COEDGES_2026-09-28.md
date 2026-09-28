# Grooved and many-coedge clipped charts

Local tested checkpoint after [mixed-chart rails](CAD_MIXED_CHART_RAILS_2026-09-28.md).
The main app is rebuilt, but the current tessellation changes are not published.
Remaining density and fallback defects mean the camera is not yet pristine.

## Cause and bounded change

The camera's small boss rim, patch 243, is a cone with 172 authored coedges and
a repeated periodic seam. A 128-coedge cutoff excluded it from the clipped-grid
planner regardless of how simple its support was. Its numerous actual grooves
then acquired additional constrained triangle fans.

Clipped-chart construction now permits 1,024 coedges, with an initial 16,384
sampled-boundary budget. Existing grid station/cell limits, final boundary limits,
support-error checks and transactional fallback remain. The mapped four-sided
recognizer is unchanged. No CAD endpoints, hard boundaries or real wire edges
are removed, and no camera IDs enter the implementation.

| Camera patch | Old quads / triangles / n-gons | New quads / triangles / n-gons |
| --- | ---: | ---: |
| 243, grooved boss cone | 158 / 1,448 / 0 | 40 / 8 / 104 |
| 551, lens-body trim | 117 / 2,144 / 0 | 83 / 4 / 169 |
| 2154, underside face | 897 / 2,024 / 0 | 824 / 20 / 332 |

The jagged trim cuts regular cells into boundary polygons; it does not require
each groove's hard edge to continue into the support's interior. Some clipped
boundary cells are necessarily narrow. This is not an all-quad or equal-aspect
remesh claim.

## Native visual checks

Matched full-production-cook shaded-wire captures, 4400 × 2604 actual pixels:

- [Boss before](preview_camera_boss_audit.png)
- [Boss with clipped rim](preview_camera_boss_clipped.png)
- [Separate sign fixture](preview_sign_many_coedges.png)

The fan band around the boss is largely gone while the authored grooves remain.
A fan region at its extreme right persists: planar sliver patch 180 still uses
the constrained fallback. It has just two trim edges, so that is a different
problem; mirror sliver 187 already clips. Large fillet density and underside
spacing also remain on the audit list.

## Full validation

Camera: 620,380 points, 584,374 polygons (530,635 quads, 18,564 triangles,
35,175 n-gons). All 2,710 patches have zero display-normal flags. Native and C
agree on each patch's counts and flags. Topology remains zero open/nonmanifold/
inconsistent edges with Euler characteristic 46. Actual display area is
65,662.42599997 and signed volume 74,390.78001102. Observed native full cook
7.92 s, not a controlled benchmark.

Fixed 4,096 OBJ-to-STEP samples retain max 0.0297543, mean-square 5.58667e-6.
STEP-to-OBJ is max 0.0263119, mean-square 5.42897e-6; those mesh-dependent sample
locations change, so this direction is not a point-for-point regression measure.
Neither measurement certifies Hausdorff distance or all-patch accuracy.

Secondary fixtures:

- `sign`: 9,437 points / 6,841 polygons, down from 10,765 polygons. Five triangles
  remain, compared with 4,461 previously. Zero normal/topology flags, Euler -30.
  Fixed OBJ-to-STEP max 0.0106321, mean-square 5.43049e-6; STEP-to-OBJ max
  0.015847, mean-square 4.98193e-6. These are current measurements, not claimed
  improvements against an unmeasured previous deviation baseline.
- `1p5inR`: unchanged 3,031 / 2,645, zero topology flags, Euler 2.
- `33mm_angle`: unchanged 4,672 / 3,888, zero topology flags, Euler 0.

Complete native opt-2 and C-release application suites pass. A new synthetic
147-coedge grooved cone covers both boundary orientations, a repeated seam,
exact source vertices and conical support, clipped-grid provenance, positive
display/corner normals and bounded face count. Additional native/C ray checks
miss removed tooth intervals and hit their tall neighbors. The existing
hard-boundary and compatible-seam continuity regressions remain intact.

Released Luce 0.8.18 and pinned Base compiler; no compiler changes. Main
`build/Luced 3D.app` rebuilt in 18 s; native `--smoke` exits 0.

Records: `/private/tmp/many-coedges-full-{native,c}.log`,
`/private/tmp/grooved-grid-ray-{native,c}.log`,
`/private/tmp/camera-many-coedges-{quality.txt,c-quality.txt,topology.log,delta.log}`,
`/private/tmp/sign-many-coedges-{quality.txt,delta.log}`,
`/private/tmp/{sign,1p5inR,33mm_angle}-many-coedges.log`,
`/private/tmp/luced-many-coedges-{build,smoke}.log`.
