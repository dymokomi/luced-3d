# Hard trims, underside flow, and first interior rows

Local implementation and verification, September 27, 2026. Nothing published.

Historical snapshot: the [endpoint/layout correction](CAD_ENDPOINT_LAYOUT_2026-09-27.md)
supersedes the phase-mismatch diagnosis and workaround below. Its root cause
was floating-point spline endpoint wrapping; use the newer captures and metrics
to evaluate the current implementation.

## Changes

The camera underside had equal *counts* on opposing sides, but substantially
different sample positions. Pairing those samples by index bent complete rows
across the band. Four topological sides were also being treated as sufficient
reason to map a grid onto hard oblique trims.

`luce-cad` now prefers support-grid clipping for hard oblique boundaries and
strongly mismatched rectangular NURBS row phases. Exact CAD endpoints and shared
boundary IDs are retained. Periodic/repeated-edge domains remain on the existing
periodic paths. Clipping is tried before the shared-sample mapped fallback.

For compatible mapped patches, `mapped_spacing.lucb` redistributes **interior**
rows by physical length, including the intervals next to both boundaries. It
does not move trim vertices. Candidates must improve the worst spacing ratio,
preserve UV orientation, and pass a sampled display-deviation comparison. There
are at most three passes. Reversed winding uses the corresponding display
diagonal. This is a bounded heuristic, not a certified NURBS error bound.

`clipped_cells.lucb` confines display fallback to an individual warped cut cell:
its validated UV triangulation replaces that cell only. Previously, one failed
n-gon could throw away a good grid for the entire patch. Surrounding regular
quads and valid cut n-gons remain intact.

`luce-3d` polygon triangulation now uses a polygon-scale area threshold and avoids
choosing a final ear that leaves three collinear seam corners. It does not weld
or remove those corners. No changes to luce-ui, luce-gpu, or luced-2d.

The distinction between boundary interpolation and physical interior spacing is
also discussed in [NASA's grid-generation documentation](https://www.grc.nasa.gov/www/winddocs/gman/gridgen.html).
The implementation here is bounded row redistribution, **not** an implementation
of its elliptic PDE solver.

## Verification

21 test groups passed on both native and C backends on this Mac. Added tests
cover fixed boundary vertices with oversized first/last interior gaps, a
four-sided curved surface meeting a hard oblique cap (including shared-edge
multiplicity and unbent grid rows), and collinear-corner polygons at two scales.
The release app build and native `--smoke` passed. Windows/Linux execution was
not performed.

At divisions 16 / edge size 0, all four complete STEP meshes have zero open,
nonmanifold, and inconsistently oriented edges:

| Model | Points | Polygons | Quads | Triangles | Euler |
| --- | ---: | ---: | ---: | ---: | ---: |
| camera | 681,623 | 665,535 | 547,824 | 83,284 | 46 |
| sign | 9,673 | 11,899 | 7,286 | 4,510 | -30 |
| 1p5inR | 2,978 | 2,625 | 2,528 | 0 | 2 |
| 33mm_angle | 4,797 | 4,140 | 3,824 | 12 | 0 |

Other polygons are cut-cell/boundary n-gons. Camera polygons fell from 776,711
to 665,535 (14.3%). Its three underside bands now use 129/32/32 polygons instead
of 4,096/2,048/512. Three formerly fan-producing crease strips use eight cells
each instead of approximately 340 polygons each.

The fixed 4,096 OBJ-to-STEP samples have maximum distance 0.0305139 source units
and RMS 0.002934 (previous RMS 0.002868). This is a small increase in sampled RMS,
not an accuracy improvement or a global error certificate. Camera renderer area
is 65,681.4667 and volume 74,395.3690; topology and shape checks must accompany
visual checks, not be inferred from the lower polygon count.

Camera tessellation measured about 10.2–10.7 seconds versus the earlier 8.1-second
run. The extra planning/quality checks currently cost compute time. CPU viewport
command recording measured 0.4723 ms for the full UI and 0.00046 ms for the camera
callback, with 1,347,124 wire segments. This benchmark does **not** measure GPU
submission/completion or prove a frame-rate improvement.

## Native shaded-wireframe inspection

These are actual Metal captures, not generated illustrations:

- [Underside](preview_bottom_hard_trims.png): diagonal bunching replaced by straight rows.
- [Corner](preview_corner_hard_trims.png): redistributed mapped interior next to retained trims.
- [Lens](preview_lens_hard_trims.png): retained for an honest view of remaining limitations.

Compound/periodic lens bands and some fallback transitions still contain dense
rows and fans. This is **not** a completed universal quad/trim solver. The
underside improvement and first-row contract are verified; the remaining lens
transitions need further work. Save work, relaunch the local app, and retessellate
to see the updated geometry.
