# Boundary stitching versus quad flow — September 27, 2026

This follow-up implements the distinction in the three supplied screenshots:
**share a boundary, without necessarily sharing an interior grid**. It updates
the previous [trim-grid pass](CAD_TRIM_GRID_2026-09-27.md).
Runtime changes are original Luce Base in `luce-cad`. No compiler, GPU, UI,
polygon-engine or luced-2d changes are part of this follow-up. Nothing published.

## Seam policy

G0-only creases retain common positions but do not require tangent continuity.
The classifier tests tangent planes separately from parameter directions; a
smooth circular fillet meeting a Cartesian plane is not automatically a valid
row-transport boundary. Continuity and derivative equality are distinct concepts
in [Open CASCADE's continuity definitions](https://occt3d.com/dev/doc/refman/html/_geom_abs___shape_8hxx.html).

Allowing partial boundary cells instead of forcing every boundary into grid
directions is consistent with the motivation of
[Lyon et al., Free Boundaries for Trimmed Quad Meshing](https://www.graphics.rwth-aachen.de/publication/03300/).
The implementation here is a bounded seam classifier and existing-UV planner,
not their global quantization algorithm or a reproduction of MoI's mesher.

| Seam | Interior layout | Shared topology |
| --- | --- | --- |
| G0-only crease | Stop transported rows; retain boundary n-gons where valid | All canonical edge samples retained |
| Smooth, aligned U/V | Continue compatible rows | Same shared point IDs |
| Smooth, swapped/reversed U/V | Continue with compatible directors | Same shared point IDs |
| Smooth, incompatible directors | Stop and clip; no forced cross-seam phase | Same shared point IDs |
| Singular, uncertain or non-manifold adjacency | Conservative flow stop | No tolerance welding or dropped vertices |

Seven interior seam samples test placed tangent planes within 0.5 degrees and
U/V directors within 5 degrees. One consistent direct or swapped permutation
must pass along the sampled seam. These are planning heuristics, **not certified
G1 continuity tests**; narrow features between samples can be missed.

## Architecture and safeguards

- `seam_flow` owns adjacency, classification and deterministic compatible-flow
  islands. `cad_flow_island` records the minimum local CAD face ID per island as
  a primitive integer attribute. Object paths and hierarchy are unchanged.
- `layout_rows` establishes each face's own curvature-sized rows before any
  propagation. `layout_balance` transports them only through eligible seams.
  `trim_layout` likewise restricts inherited UV rows, while still intersecting
  its grid with every trim boundary.
- Global edge cuts and face-local rows are distinct sorted station sets. All
  published cuts receive canonical point IDs. A stopped neighbor inserts extra
  IDs into boundary polygon edges, rather than making interior fans merely to
  match its neighbor's count. Storage grows on demand within unchanged budgets.
- A curved n-gon can pass ordinary polygon validation yet produce a display
  triangle perpendicular to the support. Conformed mapped polygons now test
  actual renderer triangles against all three corner support normals, inside
  the transactional rollback boundary.
- Analytic bands and NURBS strips with one transverse span retain extra curved
  hard-boundary support rows locally. Their flat neighbors still stop flow.
  Applying that guard indiscriminately to doubly-curved NURBS recreated camera
  corner fans during testing; that broader version was rejected. Other warped
  cases can retry the full mapped/constrained strategies and still have fans.
- Planning remains a serial prepass on the background compute worker; the
  existing four native face workers consume frozen plans. No UI-thread work or
  new platform-specific runtime was introduced.

This is trim-cell polygon clipping, not a new general-purpose polygon/CAD
Boolean engine. It does not promise all-quads, uniform aspect ratios, certified
deviation, general trim healing or successful tessellation of every STEP file.

## Final measurements

Optimized local macOS runs, divisions 16, edge-size control off. Timings are
individual runs during development, not controlled cross-platform benchmarks.

| STEP file | Points | Polygons | Quads | Triangles | Other polygons | Tessellation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| camera | 786,922 | 818,587 | 662,882 | 132,952 | 22,753 | 8.54 s |
| sign | 8,993 | 11,224 | 6,798 | 4,418 | 8 | 0.312 s |
| 1p5inR | 2,978 | 2,625 | 2,526 | 2 | 97 | 0.026 s |
| 33mm_angle | 4,797 | 4,140 | 3,826 | 8 | 306 | 0.038 s |

All four audits have zero open, non-manifold and inconsistently oriented edges.
Euler characteristics remain 46, -30, 2 and 0. This does not certify absence of
all geometric self-intersections or inverted triangles in every legacy fallback.

Camera polygons dropped 30.9% from 1,184,236. Measured tessellation changed from
9.54 to 8.54 seconds. Quad share fell from 88.5% to 81.0%, and triangle count
increased: removing excessive row propagation is **not** a universal improvement
to every curved fallback patch. The elbow and angle remain quad-dominant.

Using the same 4,096 OBJ-to-STEP sample positions, the maximum remains 0.0305139
source units. Mean squared distance changed from 8.15336e-6 to 8.50899e-6
(RMS approximately 0.002855 to 0.002917). In the reverse direction, maximum is
0.0273912 and mean squared distance 1.03524e-5; those STEP sample positions change
with the mesh. These are global nearest-surface samples, not part-paired
Hausdorff certificates or evidence that geometric error improved everywhere.

## Visual and regression verification

Actual native Metal shaded-wireframe captures, inspected after the final code:

- [Camera corner](preview_corner_seam_flow.png): the broad fan transitions at the
  checked bend are gone. Dense curved rows terminate on the coarse adjoining
  region; the shared boundary remains connected.
- [LensBody](preview_lens_seam_flow.png): retained curved detail and a coarser
  planar interior, but fallback fans around openings and some rim transitions
  remain. This is not a claim that the lens tessellation is fully clean.

The full camera corner background run reached viewport preparation at 8.99 s
and captured at 11.47 s; the LensBody subset captured at 0.668 s. These include
application computation/preparation and are not GPU frame-time measurements.
The retained-GPU probe recorded the full UI in 0.484 ms per frame with 1,605,475
wire segments (previous report: 0.511 ms). Camera update was 0.00050 ms. This
probe records commands without GPU submission, so it makes no input-latency or
GPU-throughput claim.

All 19 regression groups pass with optimized native and C backends on macOS.
New cases assert a single multi-vertex planar neighbor at a hard crease, a smooth
45-degree frame mismatch, smooth 90-degree/direct transport, canonical seam
edge incidence, circular G1 flow stops and a quad-only curved strip with planar
caps. Existing curvature, normal, reversed winding, parallel determinism, trim
clipping, import, DAG and editor tests also pass. The dome-cap regression now
expects coarse boundary n-gons on the hard planar cap, rather than inheriting
the dome's entire grid.

`luc build --release` and the built application's three-frame `--smoke` pass.
Tests use sibling path dependencies and the installed toolchain; this is not a
registry-install or publishing gate. Windows/Linux GPU execution was not tested.

Remaining work includes phase-aware layouts for compound/incompatible curved
patches, tolerance-aware trim arrangements and local density grading. The
alternate-camera/car limitations recorded in the preceding report were not
resolved by this change; they were not re-audited in this focused seam pass.
