# Mixed mapped/clipped circular rails

Local tested checkpoint following [hard-edge stops](CAD_HARD_STOPS_AND_CIRCULAR_SPACING_2026-09-28.md).
The ongoing tessellation work remains unpublished. The camera is not pristine.

## Cause and change

Camera patch 715 is an analytic cylinder between clipped NURBS patch 710 and
mapped NURBS fillet 717. One shared circle consists of two STEP coedges. The
clipped layout used only its longest selected coedge to seed a direction, then
independently refined the uncovered interval. Later reconciliation united those
competing phases. In addition, fitted support inversion put the longer coedge
just beyond a fixed UV straightness threshold (1.1395e-7 versus 1e-7), despite
its physical rail displacement fitting the file's declared 0.01 uncertainty.

- Seed every coedge on the selected dominant rail before refining curvature.
  Do not combine unrelated opposite rails merely because their axes agree.
- Classify nearly constant rails using physical support displacement at every
  station, with an additional relative UV straightness guard. Even a sub-epsilon
  UV wobble must pass this check on a strongly stretched support.
- Exact canonical 3D trim points remain unchanged. No UV snapping, tolerance
  increase, proximity welding, hard-edge row override or fixture-specific branch.
- Circular-family phase planning now also operates next to clipped smooth
  charts; their complete initial rails and subsequent reconciliation retain the
  curvature requirement. The previous conservative mixed-family exclusion is
  no longer needed for these admitted layouts.

## Measurements and captures

All 2,710 patches, divisions 16, edge size 0. Native/C agree on every patch's
polygon counts and display-normal flags. Full assembled topology has zero open,
nonmanifold or inconsistent edges; Euler characteristic remains 46.

| Measurement | Previous checkpoint | Current |
| --- | ---: | ---: |
| Points | 610,544 | 620,541 |
| Polygons | 580,005 | 589,370 |
| Quads | 519,872 | 531,186 |
| Triangles | 25,770 | 24,016 |
| Cut/boundary n-gons | 34,363 | 34,168 |
| Display-normal flags | 0 | 0 |
| Patch 715 quads | 210 | 172 |
| Patch 715 edge-ratio > 20 cells | 93 | 0 |
| Patch 715 worst edge ratio | 5,384.15 | 13.21 |

Observed full native cook 8.42 s; C stats cook 8.12 s. These are local timings,
not controlled performance benchmarks. Actual display area 65,662.5264064;
signed volume 74,390.7948379.

The fixed 4,096 OBJ-to-STEP samples retain max 0.0297543 at patch 2358;
mean-square is 5.58709e-6 (previous 5.57760e-6). STEP-to-OBJ max 0.0244812,
mean-square 4.79437e-6. That direction uses mesh-dependent locations and is not
a point-for-point comparison. Neither direction certifies Hausdorff error.

Native shaded-wire images, 4400 × 2604 actual pixels, with no hidden wire edges:

- [Ring isolated after the complete cook](preview_camera_mixed_ring.png)
- [Assembled lens and surrounding frame](preview_camera_mixed_lens.png)

The assembled view still exposes dense fillets, small-boss rim fans and the
remaining ledge artifacts. Patch 717 has 5,410 quads, including 5,400 with edge
ratio above 20: density and physical spacing there need separate investigation.
Zero normal flags alone do not certify accuracy, injectivity or clean topology.

## Verification

- Complete native opt-2 and C-release application suites pass with released
  Luce 0.8.18 and pinned Base compiler. No compiler changes.
- New mixed-chart synthetic regressions join a clipped rational NURBS cylinder
  with a hole to an analytic cylinder via split circle coedges. Arbitrary and
  near-quadrant splits plus fitted-support noise preserve shared seam degree,
  exact radius, interior quads and positive triangle/corner-normal agreement.
  All three have 120 stations with gap ratios below 1.04 (test bound 2.5).
- Base rail tests accept physically negligible fitted noise, reject the same
  UV noise on a million-fold stretched support even below UV epsilon, and reject
  genuinely oblique rails even under a loose physical tolerance.
- `sign`, `1p5inR` and `33mm_angle` retain their previous counts, zero topology
  defects, and Euler characteristics -30, 2 and 0.
- Main `build/Luced 3D.app` rebuilt (20 s); native `--smoke` exits 0.

Records: `/private/tmp/metric-rails-full-{native,c}.log`,
`/private/tmp/camera-metric-rails-{checked-quality.txt,c-quality.txt,final-topology.log,final-delta.log}`,
`/private/tmp/{sign,1p5inR,33mm_angle}-metric-rails.log`,
`/private/tmp/luced-metric-rails-{build,smoke}.log`.
