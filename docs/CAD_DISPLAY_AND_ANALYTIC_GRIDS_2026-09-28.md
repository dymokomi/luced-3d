# Retained display triangles and analytic trim grids

Local, tested checkpoint. The camera is **not pristine**: uneven stations,
high-aspect cells, some remaining fallback fans and other Desktop fixtures still
need work. No tessellation release has been published from this checkpoint.

## Causes fixed

1. A curved cut polygon was retriangulated in an average plane during assembly,
   detached worker copies and transforms, discarding its support-chart triangles.
   Some resulting ears lay across a curved boundary and opposed its CAD normals.
   `luce-3d` now owns validated per-face display indices independently of polygon
   edges. Rendering, picking and surface-distance queries use the same indices.
   Copies, attributes, affine/reflected placement, merges and unchanged subsets
   retain them; arbitrary point edits invalidate them. Builder rewinds clear old
   display slots. No wire edges are suppressed and display diagonals are not
   promoted to modeling edges.
2. UV ears can also become poor 3D ears after lifting exact canonical boundary
   vertices. CAD now performs bounded local diagonal flips inside convex UV
   quadrilaterals, accepting only a strict decrease in support-normal violations.
   It can compare an ordinary projected candidate too. A still-folded clipped
   cell rejects that patch strategy transactionally. Real display triangles also
   pass the existing sampled support-deviation check.
3. The grid planner skipped analytic cylinders and cones. Camera lens-body
   patches 247 and 251 are thin cylindrical fillets with five coedges and an
   irregular end trim. They therefore used legacy constrained fans. Analytic
   charts now participate in the same grid-first clipping path, with exact
   analytic normals. Nearly closed isocurves use sampled extent rather than
   their misleadingly short endpoint chord when selecting deflection scale.

All implementation remains Luce Base. No camera IDs, substituted OBJ geometry,
relaxed topology assertions or hidden wireframe edges enter the mesher.

## Complete camera audit

Source: read-only Desktop `camera.step`; divisions 16, edge size 0.

| Measurement | Compound-side checkpoint | Current |
| --- | ---: | ---: |
| CAD patches | 2,710 | 2,710 |
| Points | 662,060 | 651,110 |
| Polygons | 651,073 | 624,493 |
| Quads | 575,882 | 569,415 |
| Triangles | 51,065 | 28,137 |
| Cut n-gons | 24,126 | 26,941 |
| Display-normal flags | 1,629 | 0 |
| Open / nonmanifold / inconsistent edges | 0 / 0 / 0 | 0 / 0 / 0 |
| Euler characteristic | 46 | 46 |

Native and C-backend camera audits agree on polygon counts and zero display-normal
flags across all 2,710 patches. This flag tests each actual display triangle
against all three analytic corner normals; zero flags is **not** a global
injectivity, approximation-error or element-quality certificate.

Native rendered area is 65,664.0660474 and signed volume 74,392.3111312. A stats
cook took 8.23 s locally; C took 8.71 s. These are observations, not controlled
performance claims or viewport/input-latency measurements.

A separate 300-callback native orbit observation in shaded-wire mode, at
4400 × 2604 actual pixels, recorded 2.44539 ms mean / 3.07 ms worst after 35
warm-up frames. This measures callback intervals, **not** GPU completion,
presentation rate or input-to-photon latency. Record:
`/private/tmp/camera-display-final-orbit.log`.

Patch 247 changes from 8 quads + 3,434 triangles to 470 quads + 1 triangle + 15
cut n-gons. Patch 251 changes from 4 quads + 3,335 triangles to the same new
counts. Both retain exact shared boundaries and have zero normal flags. The
resulting long narrow quads still have high aspect ratios; this is not described
as an isotropic remesh. Patch 710 retains its clipped ring and holes, with 3,452
quads, 1 triangle and 304 cut n-gons, now with zero display-normal flags.

Fixed 4,096 OBJ-to-STEP samples: max 0.0297543, mean-square 5.92199e-6. The earlier
compound checkpoint was max 0.0305709, mean-square 8.43064e-6. Worst fixed sample
remains frame patch 2358. STEP-to-OBJ: max 0.0199004, mean-square 5.81363e-6; those
samples depend on the generated mesh and are not a point-for-point comparison.
Neither sampled comparison is a Hausdorff certificate.

## Native visual evidence

All captures are 4400 × 2604 actual pixels. Patch isolation happens **after** the
complete global cook, retaining stations, CAD ownership and display triangles;
there is no OBJ export/reimport in the capture path.

- [Matched thin-ledge before](preview_camera_patch247_before.png)
- [Matched thin-ledge grid clipping](preview_camera_patch247_grid.png)
- [Assembled camera lens after this pass](preview_camera_display_final_lens.png)

The ledge's repeated fans are replaced by strips. The assembled capture still
shows a dense small circular feature, crowded ring stations and uneven regions
around the frame. Those remain explicit follow-up work.

## Regression gates

- Released Luce 0.8.18 with its pinned Base compiler; no compiler modifications.
- `luce-3d` Base plus both Luce consumers: native optimizations 0–3 and C
  debug/release, all PASS. Display topology, reflection/copy/merge/subset retention,
  invalid-input rejection and 256 allocation-failure stages are covered.
- Complete luced-3d native opt-2 and C release suites PASS. Existing degree-four
  smooth-seam assertions remain intact.
- New closed rational-NURBS and analytic-cylinder cases: both seam starts, a
  trimmed hole, stitched seam vertices, exact support points, positive display
  normals and a ray through the hole to the opposite shell.
- New oblique elliptical cylinder/plane trim: both face senses, a split trim
  coedge, size-refined quad interiors, unchanged angular/axial rows, shared
  hard-cap trim edges and positive display normals.
- Direct analytic-normal checks compare all analytic chart derivatives with
  their exact normals, including a rotated coordinate frame.
- Desktop `sign`, `1p5inR` and `33mm_angle` retain their previous point/polygon
  counts and zero open/nonmanifold/inconsistent edges; Euler -30, 2 and 0.
- Main `build/Luced 3D.app` rebuilt with `luc build --release` after those gates
  (17 s); native `--smoke` exits 0. Build/smoke records are
  `/private/tmp/luced-analytic-checkpoint-{build,smoke}.log`.

Raw local diagnostics use `/private/tmp/camera-display-final-*` and
`/private/tmp/display-final-{native,c}.log`. The earlier `display-strict-*` and
`analytic-grid-*` records are intermediate experiments, not final counts.

## Next checks

Investigate crowded circular station pairs (e.g. patch 715 has clean topology
but a maximum quad edge ratio over 5,000), then first-interior-row spacing,
underside flow, the small boss and remaining constrained patches. Distinguish
mandatory CAD vertices from optional curvature/flow stations before redistributing
them. Hard edges must retain their canonical boundary without transporting
unnecessary rows. Continue native large-detail captures and surface/topology
audits rather than treating zero normal flags as completion.
