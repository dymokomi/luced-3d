# Continuous analytic charts and physical cut-cell cleanup

Verified incremental checkpoint after the button-rim correction. The camera is
not pristine, and broader STEP import/tessellation failures remain open. All
geometry comes from STEP; Desktop files and reference OBJs remain unchanged.

## Two distinct causes

Six cylindrical frame transitions were falling back because neighboring coedges
used different angular branches. Examples in the actual clipping input were
`0 -> 6.25557` and `pi -> -3.09251`: these were fictitious long chords across the
chart, not real edges around the cylinder. Chart initialization previously ran
only when a face explicitly reused a seam edge. Ordinary partial cylinders and
cones need continuous branch selection too.

`trim_chains.initialize` now carries the projection seed between cylinder/cone
coedges whether or not an edge is repeated. Holes start in the outer loop's
angular chart. Refreshing a shared chain preserves the established branch.
No canonical position, tolerance, edge identity or support surface changes.
Nonperiodic NURBS initialization is unchanged; this does not pretend arbitrary
multi-chart trims have been solved.

Separately, tiny boundary ribbons survived on curved charts because optional
sliver cleanup was restricted to planar UV distances. Curved cells now use their
lifted physical area/longest-side measure. Only boundary-adjacent ribbons below
five percent of model tolerance qualify. The existing one-eighth neighboring
UV-area, single-shared-edge and simple-union guards remain. Dissolve preserves
all point IDs and display triangles. Normal and sampled support-error checks
still validate the lifted result. The optional pass is bounded to 128 dissolves
instead of stopping after the first 32 cells of a dense boundary strip.

This is actual polygon-edge removal across a valid cell union, not a wireframe
visibility trick. It does not guarantee an ideal aspect ratio for every cut
polygon. No fixture IDs or coordinates are in either production rule.

## Full assembled camera

Same File tolerance (0.01), divisions 16 and edge size 0 as the prior checkpoint.
Captures isolate patches only after the full production cook.

| Metric | Previous checkpoint | Current |
|---|---:|---:|
| Points | 674,425 | 671,178 |
| Polygons | 629,153 | 624,869 |
| Quads / triangles / other polygons | 588,961 / 4,752 / 35,440 | 585,608 / 3,456 / 35,805 |
| Mapped / clipped / constrained patches | 2,200 / 489 / 21 | 2,200 / 495 / 15 |
| Open / nonmanifold / inconsistent edges | 0 / 0 / 0 | 0 / 0 / 0 |
| Folded-display flags | 0 | 0 |

The chart correction changes eight quality records: six cylinder transitions
and two immediate neighbors. The preceding physical cleanup changes another
46 records. All 2,710 current quality records match native versus C at printed
precision. Euler characteristic remains 46. Retained-display area is
65,662.53548709703; signed volume is 74,393.22694268434.

The six transitions 2278, 2282, 2351, 2353, 2705 and 2708 now have 92–93 cut
polygons each instead of 627–863 mostly quads/triangles. For example, 2351 changes
from 380 quads + 254 triangles to 30 four-corner cells, 1 triangle and 62 cut
n-gons. The neighboring patch's dense boundary stations terminate at the trim;
they no longer require a triangle fan across this cylindrical patch.

The physical cleanup removes both newly observed sliver flags on 1102/1127:
their effective widths were 0.00027918 and 0.00033282, below the 0.0005 cleanup
threshold. They now have no stretched-20 or skewed-0.1 quads; maximum edge ratios
are 4.40021 and 1.71658, and minimum corner sines are 0.97836 and 0.97779.

Raw quality totals are **not uniformly better**: stretched-20 counts are
49,987 versus 49,981, and skewed-0.1 counts are 2,115 versus 2,099. Each of the
six new cylinder grids has two flagged boundary cut quads. Patch 276 now has
20 flagged four-corner cut polygons, formed by merging thin boundary triangles;
none of these flags is on a non-boundary quad. Its polygon count falls 367 to
294, but its very thin segmented border is still visibly crowded and unfinished.
Those flags are retained, not concealed through polygon reclassification.

## Native shaded-wire inspection

Actual 4,400 × 2,604 native captures with the same cameras before/after:

- [2351 and stitched neighbors, before](preview_camera2351_chart_before.png)
- [2351 and stitched neighbors, after](preview_camera2351_chart_after.png)
- [276 narrow boundary detail, before](preview_camera276_sliver_before.png)
- [276 narrow boundary detail, after](preview_camera276_sliver_after.png)

The rim transition loses its fallback fan. The narrow 276 comparison is a
limited cleanup, not a pristine result. Missing distant faces in these images
are the explicit diagnostic patch subset, not dropped model geometry.

Fixed 4,096 OBJ-to-STEP samples give max 0.0259126 (unchanged), mean squared
4.63e-6 versus 4.62886e-6. Reverse STEP-to-OBJ gives max 0.020835 and mean squared
4.176e-6; those sample locations change with mesh indexing. Neither direction
is a certified error bound. These small differences are not claimed as an
accuracy improvement. Individual full cooks measured 9.7–10.4 seconds with
other checks running, not a controlled speed benchmark or GPU latency result.

## Regression coverage and remaining files

- 160 analytic chart cases: cylinders/cones, two scales, five angular phases,
  all four loop starts, both windings, an internal hole, and shared-chain refresh.
  Check continuous closed charts, trim area and unchanged exact curve positions.
  Disabling the new non-seam initialization fails the branch assertion. Omitting
  outer-relative hole seeding also failed the new hole assertion before correction.
- Ten application-facing oblique cylinder/cap cases rotate only the support
  chart, not geometry. Check clipped strategy, shared edge ownership, support
  positions and every rendered triangle normal.
- 64 physical-sliver checks distinguish UV scale from physical width and require
  canonical positions/topology to survive. A 64-ribbon strip checks that cleanup
  completes past the former 32-operation limit without losing collinear corners.
- Full application suite: **31 PASS groups each on native opt-2 and C release**.
  The standalone Base layout contracts also pass native opt-0 and opt-3.
- `sign`, `1p5inR` and `33mm_angle` still load and tessellate in the corpus probe:
  6,841 / 2,645 / 3,888 polygons. This probe is not an exhaustive visual audit.
- `camera_2` still fails face 81 at source tolerance 0.01 (residual 0.0102655).
  At explicit File tolerance 0.02 it still fails face 95 triangulation.
- `car1` still rejects endpoint residual 1.58559e-5 against source tolerance
  1e-5. Its known repeated-occurrence issue is unchanged by this chart work.
- `car2` still fails the assembled trim on face 720 with crossing/touching loops.

The main `build/Luced 3D.app` was rebuilt at **08:57:06 PDT** using released
Luce 0.8.18 and the pinned Base toolchain; native `--smoke` exited zero. This is
local work, not a new registry release. Temporary tracing and negative-control
switches have been removed.

Evidence: `/private/tmp/camera-trim-chart{.obj,-topology.log,-c.txt,-delta.log}`,
`trim-chart-final-{native,c}.log`, `trim-chart-corpus.log`,
`camera2-trim-chart.log`, `trim-chart-app-{build,smoke}.log`,
`chart-contract-{fixed,negative}.log`, `camera-physical-slivers128-trial.txt`.

Next: the 15 constrained camera patches, remaining mapped-patch crowding and
cut-cell defects, then the assembled camera_2/car2 trim failures and actual CAD
instance support for car1. Do not infer completion from fewer fallback patches.
