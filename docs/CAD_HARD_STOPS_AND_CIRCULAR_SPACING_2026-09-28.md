# Hard-edge row stops and circular spacing

Tested local checkpoint, not a claim that the camera is pristine. This follows
[retained display triangles and analytic grids](CAD_DISPLAY_AND_ANALYTIC_GRIDS_2026-09-28.md).
The tessellation changes remain unpublished while the ongoing patch audit runs.

## Changes

- Removed the curved-hard-edge `support_rows` override. It transported canonical
  boundary samples into the interior even when seam classification stopped flow.
  Exact shared boundary vertices remain; extra vertices terminate in boundary
  polygons instead of forcing the same rows through the neighboring surface.
- Conformed mapped polygons first validate their projected display triangles.
  If those ears oppose the support normals, they may retry support-chart
  triangulation, bounded diagonal repair and the sampled support-error gate.
  The resulting display indices survive face workers and assembly. This is a
  fallback for display diagonals, not hidden wire edges or deleted topology.
- Fully mapped coaxial circular families agree on one angular distribution
  before canonical edge sampling. Every CAD endpoint is mandatory; intervals
  between them are divided evenly at the strongest required density, including
  a circular-sagitta floor. Optional quadrant anchors are omitted when too close
  to a required endpoint. Original CAD vertices never move or merge.
- A family with an aligned connection to an independently clipped/noncircular
  chart is deliberately excluded from phase replacement. Replacing only half
  of that island recreates the competing phases during UV intersection planning.
  Such islands still need a coordinated mixed-chart solution.

Rejected experiments are not included: unconditional UV retriangulation rejected
valid very thin toroidal charts; deleting the hard-edge guard before providing
the display fallback reintroduced thousands of normal violations. An unrestricted
circular-family change worsened patch 715 beside clipped NURBS patch 710. The
conservative final policy leaves that already-known crowded ring unchanged.

## Full camera audit

Read-only `Desktop/camera.step`, divisions 16, edge size 0; all 2,710 patches.

| Measurement | Previous checkpoint | This checkpoint |
| --- | ---: | ---: |
| Points | 651,110 | 610,544 |
| Polygons | 624,493 | 580,005 |
| Quads | 569,415 | 519,872 |
| Triangles | 28,137 | 25,770 |
| Boundary/cut n-gons | 26,941 | 34,363 |
| Display-normal flags | 0 | 0 |
| Open / nonmanifold / inconsistent edges | 0 / 0 / 0 | 0 / 0 / 0 |
| Euler characteristic | 46 | 46 |

Fewer quads here primarily means removal of unnecessary interior rows, not a
quad-percentage goal. The actual display area is 65,662.5999122 and signed volume
74,391.0470963. Native and C-backend audits agree on polygon counts and zero
display-normal flags. A flag compares an actual rendered triangle with all three
analytic corner normals; zero is not a global quality or surface-error certificate.

Observed native full cook: 8.06 s; C stats cook: 7.92 s. These are local timings,
not controlled benchmarks or GPU/input-to-photon measurements.

Fixed 4,096 OBJ-to-STEP samples retain max distance 0.0297543; mean-square changes
from 5.92199e-6 to 5.57760e-6. The worst fixed sample remains frame patch 2358.
STEP-to-OBJ is max 0.0272994, mean-square 5.64025e-6; those mesh-dependent sample
locations changed, so the maximum cannot be treated as a point-for-point
regression comparison. Neither direction is a Hausdorff certificate.

Examples: patch 719 changes from 5,888 quads to 3,108 quads + 92 boundary n-gons;
patch 273 from 5,808 quads + 80 n-gons to 3,504 quads + 80 n-gons. Patch 597's
maximum quad edge ratio drops from 38.79 to 28.08, but remains high. Patch 715
still has 210 quads, 93 stretched cells and maximum edge ratio 5,384.15.

## Visual checks and remaining defects

- [Previous assembled lens/frame](preview_camera_display_final_lens.png)
- [Current assembled lens/frame](preview_camera_hard_stops_lens.png)
- [Large frame/boss close-up](preview_camera_hard_stops_frame.png)

All are native shaded-wire captures at 4400 × 2604 actual pixels, from the full
production cook. The frame has visibly less hard-edge-induced row crowding. The
close-up deliberately exposes the small boss's remaining fan artifacts; it is
not presented as solved. The frame close-up predates only the final optional
quadrant-anchor exclusion; the final assembled capture includes it.

Open priorities: mixed clipped/mapped ring 710/715/717; boss rim fans; narrow
ledge diamond fans; underside flow; first-interior-row spacing. The small boss
also contains many genuine source CAD strips—distinguish those from mesher-added
fans rather than erasing actual authored boundaries.

## Verification

- Complete luced-3d native opt-2 and C-release suites pass using released Luce
  0.8.18 and its pinned Base compiler. No compiler changes.
- Circular fillet regressions cover unsplit, arbitrary split and a split almost
  coincident with an optional quadrant. They preserve shared topology, exact
  support, matching radial rows, interior quads and bounded angular gap ratio.
- Curved hard-strip regression covers both a single transverse span and an
  edge-size-refined interior; extra boundary corners do not become interior
  rows, and all display triangles face all their support normals.
- The Blast regression now compares a polygon deletion against its source
  partition. Meshing a CAD cap alone can legitimately use fewer boundary samples
  than meshing it beside a curved wall; exact standalone/global face-count
  equality was not the correct deletion invariant.
- Secondary full-topology audits: `sign` 8,604 points / 10,765 polygons,
  `1p5inR` 3,031 / 2,645, `33mm_angle` 4,672 / 3,888. All have zero open,
  nonmanifold or inconsistent edges; Euler -30, 2 and 0 respectively.
- Main `build/Luced 3D.app` rebuilt after the final regression gates (18 s),
  with native `--smoke` exiting 0. Records:
  `/private/tmp/luced-circular-checkpoint-{build,smoke}.log`.

Records: `/private/tmp/circular-spacing-{native,c}.log`,
`/private/tmp/camera-circular-spacing-final-*`, and
`/private/tmp/{sign,1p5inR,33mm_angle}-circular-spacing.log`.
