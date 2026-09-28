# Camera audit: compound circular sides

This is an intermediate result, not a clean-camera completion claim. Desktop
STEP/OBJ inputs are read-only. All measurements below use the full production
camera cook at divisions 16, edge size 0, before extracting individual patches.

## Cause and change

`layout_phase.align_sides` only accepted a single circular coedge on each
logical side. If STEP split one circle into several arcs, count matching could
connect different angles across the same cylinder/fillet. Adaptive refinement
then generated thousands of triangles around the mismatched strips.

The existing geometric checks and angular transfer now cover compound sides:
the arcs must share an axis/center and cover the opposite side. Split endpoints
are real angular stations on the opposite side. No input boundary is moved,
no fixture IDs are special-cased, and no wire edges are hidden.

The split-circle fillet regression now requires the same radial correspondence,
quad interior and boundary-only n-gons as the unsplit case. Previously its
split branch only checked that vertices lay on the torus.

## Evidence

| Full camera | Before | After |
| --- | ---: | ---: |
| Points | 674,929 | 662,060 |
| Polygons | 681,714 | 651,073 |
| Quads | 571,476 | 575,882 |
| Triangles | 86,198 | 51,065 |
| Open / nonmanifold / inconsistent edges | 0 / 0 / 0 | 0 / 0 / 0 |
| Euler characteristic | 46 | 46 |
| Rendered area | 65,681.9541147 | 65,683.9934329 |
| Rendered signed volume | 74,391.2082887 | 74,390.8958918 |

Patch 715 (`Lens:1/Body14`): 37 quads + 4,734 triangles became 210 quads.
Patch 21 and its repeated glass-lens counterparts: 73 quads + 2,270 triangles
became 184 quads. These patches have no flagged display-normal inversions.
Physical station bunching still exists in parts of patch 715: its worst edge
ratio is 5,384, so the quad count alone does **not** prove good distribution.

Native shaded-wire captures, 4,400 × 2,604 actual pixels:

- [Patch 715 before](preview_camera_patch715_before.png)
- [Patch 715 after](preview_camera_patch715_after.png)
- [Assembled camera lens](preview_camera_compound_lens.png)

The isolated patches are extracted **after global tessellation**; they are not
independently retessellated previews. OBJ is only a lossless geometry carrier
for these inspection captures. The assembled capture uses the actual STEP cook
and CAD normals. The wireframe visibly confirms removal of the diagonal fans;
it also exposes remaining close pairs of stations and crowded neighboring rims.

Fixed 4,096-sample OBJ-to-STEP comparison: maximum distance 0.0305709, RMS
0.00290356 (previous maximum 0.0305139, RMS 0.00288183). This direction uses the
same reference samples; the small increase is recorded, not claimed as an
accuracy improvement. Reverse sampling depends on generated mesh topology:
maximum 0.035569, RMS 0.00257824, and is not a fixed-point comparison.

Native and C editor suites pass with the strengthened fillet test. `sign`,
`1p5inR` and `33mm_angle` retain their prior polygon counts, Euler values and
zero open/nonmanifold/inconsistent edges. Full camera cooks measured about
9–9.5 seconds in these runs; they were not controlled performance benchmarks.
The local `build/Luced 3D.app` checkpoint was rebuilt with released Luce 0.8.18.
This intermediate CAD work is not a new registry release; the public install
checkpoint remains luced-3d 0.1.2. Its corrected macOS/Linux CI and luce-ui
0.8.15's macOS/Linux/Windows CI are now all green.

## New audit tools and unresolved evidence

`tools/cad_probe.py --stats` now reports every patch's bounds, quads/triangles/
n-gons, cut-grid use, edge ratio, opposite-edge ratio, corner sine and display
triangle alignment with analytic corner normals. `--patch N` extracts that
patch from the complete cook. `--backend c` permits comparison builds.
The `cad_mesher` primitive attribute records which strategy actually succeeded
(1 local rows, 2 clipping, 3 canonical rows, 4 constrained fallback, 5 baseline
fallback plus conformity), including native parallel face jobs.

The new normal audit flags 1,583 baseline display triangles across 53 patches.
This change yields 1,629 across the same patches: **all 46 additional flags are
on patch 710**, a constrained fallback. This is a known regression to investigate
before calling the lens solved. The other 52 flagged patches remain unresolved.
The audit tests all three analytic corner normals with a scale-relative dot
threshold; investigate flags geometrically rather than treating the counter as
proof of a visible defect in every case.

Rejected experiment: suppressing hard-edge support phases and choosing the
best-shaped polygon ear improved the narrow corner 2396 but broke the split
fillet's display-normal regression, increased triangles elsewhere, and raised
camera cook time. Both behavioral changes were reverted. Merely preferring a
better projected ear does not ensure compatibility with the curved support.
The original conservative support-row guard remains; it is not the desired
final hard-edge policy.

Next: inspect patch 710's constrained UV refinement/display triangles, then
return to the hard-edge support guard and uneven canonical phases. Patch 2396
still has 78 severely skewed quads out of 214; patch 609 has 495 out of 2,604.
The main housing ledge, corner transition and first-interior-row issues remain
on the larger audit checklist.

## Research context

[Lyon et al., SIGGRAPH 2019](https://www.graphics.rwth-aachen.de/publication/03300/)
supports allowing partial elements at non-aligned boundaries instead of forcing
all grid directions to follow every trim. This agrees with the requested
hard-edge/boolean-trim policy, but does not implement it for us.

[Reberol et al., 2021](https://arxiv.org/html/2103.04652v1) emphasizes preserving
CAD constraints and checking geometric validity during local quad improvements.
That motivates rejecting the first experiment when its display triangles fail,
even though some wireframes looked simpler. A full cross-field remesher is not
implemented here.
