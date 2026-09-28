# Cross-patch grids and trim-cell clipping — September 27, 2026

This implements the proposed **continue compatible rows, clip irregular trims**
approach. It builds on [mapped patches](CAD_MAPPED_PATCHES_2026-09-27.md), rather
than replacing already-good Coons grids with a second, competing grid.
It is original Luce Base code in `luce-cad` and `luce-tesselator`. No compiler,
luce-ui, luce-gpu or luced-2d changes are part of this follow-up.

## Research and scope

MoI is a useful output reference, not a source-code donor. Its public mesh
documentation describes shared-edge welding, curvature/length/aspect controls,
and n-gon versus quad/triangle output. Those controls do not establish that
MoI solves arbitrary cross-patch all-quad parameterization, and this work does
not claim to reproduce its private algorithm.
[MoI mesh documentation](https://moi3d.com/4.0/docs/moi_command_reference11.htm).

Free-boundary trimmed quad meshing explicitly permits partially aligned
boundaries and cut elements. This supports keeping a good interior layout
instead of forcing every irregular trim into the grid directions.
[Lyon et al., Parametrization Quantization with Free Boundaries for Trimmed
Quad Meshing](https://www.graphics.rwth-aachen.de/publication/03300/).

Quasi-structured CAD meshing combines sizing, curve discretization constraints
and compatible patch layouts; opposite-side counts alone are not a universal
solution for junctions or mismatched parameterizations.
[Gmsh quasi-structured meshing research](https://arxiv.org/html/2103.04652v1).
The larger cross-field/quantization solver described in this literature is
**not implemented here**. The current transfer uses existing compatible UV
directions, not a global reparameterization of every CAD surface.

## Pipeline and package boundaries

1. Existing curve and interior-curvature sampling establish baseline shared
   edge stations and four-logical-side Coons layouts.
2. Irregular planar/nonperiodic NURBS patches seed directional U/V rows. The
   planner preserves a dominant coedge's phase, adds curvature/size support,
   and transfers compatible isoparametric stations across shared edges. Swapped
   and reversed UV directions are covered by regression tests.
3. Exact CAD-curve/grid intersections register canonical curve parameters.
   Both incident faces consume the same 3D point IDs. Old projection values
   are cached as the station set grows, avoiding seed-dependent UV drift.
4. Logical opposite-side counts are reconciled before meshing. Compatible
   single-circle sides also transfer angular positions, not merely counts.
   Compound circular sides keep count matching plus geometric refinement.
5. `TrimGrid.clip` intersects the supplied grid with pre-split UV trim polygons.
   Whole cells stay quads; boundary cells remain small polygons. Holes wholly
   inside a cell and cells over the 256-corner limit triangulate locally.
6. CAD lifts the result onto exact support surfaces, preserving boundary IDs.
   Actual rendered triangles are checked at midpoint/centroid samples.
   Clipped-grid normals are evaluated at known UVs, avoiding a second inverse
   projection pass. CAD paths, primitive colors and `cad_face` survive.
7. Four existing native face workers prepare independent patches; assembly is
   deterministic. Planning remains a serial prepass on the background compute
   worker, not the UI thread. No new application threading abstraction was added.

`luce-tesselator` owns UV cell clipping, without STEP, CAD topology or UI policy.
`luce-cad` owns curve intersections, station propagation, support evaluation,
tolerances and shared seam identity. `brep_mesh` now orchestrates assembly;
`patch_dispatch` contains transactional strategy selection. Planning, circular
phase transfer, deviation refinement and output validation are separate modules.

The integer primitive attribute `cad_trim_grid` identifies polygons produced by
the clipped-grid path. It is diagnostic provenance, not a second geometry type.

## Safety and fallbacks

- Every clipped input trim segment must appear exactly once in the output;
  every interior edge must appear twice. An omitted boundary or open interior
  rejects that strategy. No near-point welding hides a failed cell arrangement.
- A rejected strategy rewinds scratch before mapped/constrained alternatives.
  Final triangulation validation occurs inside this transaction, not only after
  a worker has returned an unusable mesh.
- If full-sample constrained meshing fails, the original baseline can be meshed
  and extra seam samples inserted into real polygon boundaries. This result is
  also validated; warped/self-intersecting n-gons are not silently accepted.
- Analytic fallback surfaces now receive bounded interior deviation refinement,
  as NURBS already did. Compound analytic mapped patches also receive that
  check, because equal counts with different phases can otherwise make long
  skewed quads miss curvature.
- Work is bounded: 257 stations per UV axis, 1,025 per shared edge, eight trim
  reconciliation passes and 32 mapped-side balancing passes. Guard bounds and
  sampled deviation tests are not certified error bounds.

An experiment transferring all compound-circle stations exposed crossing/touching
trims on camera detail face 564. That broad transfer is **not enabled**. Correct
generalization needs topology-aware trim healing/arrangement, not a larger
tolerance or deletion of troublesome seam vertices.

## Final measured meshes

Optimized local native runs, 16 divisions, edge-size control off. Inputs on the
Desktop were read only. Timings are individual diagnostic runs, not controlled
cross-platform benchmarks.

| STEP file | Points | Quads | Triangles | Other polygons | Tessellation |
| --- | ---: | ---: | ---: | ---: | ---: |
| camera | 1,151,246 | 1,048,551 | 118,549 | 17,136 | 9.54 s |
| sign | 8,993 | 6,814 | 4,418 | 0 | 0.305 s |
| 1p5inR | 3,327 | 2,789 | 3 | 229 | 0.026 s |
| 33mm_angle | 5,584 | 4,548 | 16 | 447 | 0.038 s |

All four have **zero open, non-manifold and inconsistently oriented edges**.
Euler characteristics remain 46, -30, 2 and 0 respectively. These connectivity
checks do not prove absence of all geometric self-intersections or every
possible CAD deviation.

Camera quads are 88.5% of polygons, versus 82.3% in the previous mapped-patch
report. Density grew from 652,429 to 1,184,236 polygons; tessellation grew from
6.65 to 9.54 seconds. This is a quality/continuity improvement with a real memory
and preparation cost, **not an overall tessellation speedup**. Early experiments
exceeded two million polygons and were not retained.

Using the same 4,096 OBJ-to-STEP sample locations:

- Maximum distance: 0.0329782 → **0.0305139** source units.
- RMS distance: approximately 0.00303 → **0.0028554**.
- Final STEP-to-OBJ sampled maximum: 0.0261422; RMS 0.0030335.

These use the native triangle BVH and actual renderer triangulation. They are
global nearest-surface samples, not a Hausdorff certificate or a fully part-paired
comparison. STEP sample locations change with the mesh. The audit tool now also
measures area/volume using actual renderer triangles instead of incorrectly
fanning concave or nonplanar n-gons in Python.

## Visual and runtime verification

Actual Metal readbacks, inspected after the final changes:

- [Camera corner](preview_corner_trim_grid.png): rows continue around the bend
  and into the adjoining front surface. The former large repeated fan band there
  is gone; other rim transitions remain visible.
- [LensBody](preview_lens_trim_grid.png): retained curved detail and interior
  support; fan transitions around openings and excessively dense regions are
  still visible. This is not a uniformly clean all-quad lens result.
- [Full camera](preview_camera_trim_grid.png): rendered from the STEP pipeline,
  not the supplied OBJ. The capture also exercised native orbit callbacks.

The close-up full-camera background run reached viewport preparation at 10.08 s
and completed the capture at 13.52 s. The isolated LensBody run reached viewport
preparation at 0.713 s and captured at 0.849 s. Native orbit measured 5.81 ms mean
and 24.87 ms worst callback interval over 300 samples; it ran during other local
development activity and is **not GPU time or input-to-photon latency**.

The retained-GPU command-recording probe measured 0.511 ms per full UI frame
with this 1,184,236-polygon mesh and 2,335,448 wire segments (previous report:
0.488 ms with 652,429 polygons). It records commands without submitting GPU
work. This confirms the CPU recording path remains retained; it does not prove
unchanged GPU throughput, latency or cross-platform frame pacing.

Both optimized native and C-backend test suites pass all 18 regression groups.
New cases cover oblique cut cells, contained and crossing holes, oversized cells,
unsplit-crossing rejection, seam valence across swapped/reversed UV patches,
reversed-frame circular fillets and compound-ring manifold/support preservation.
`luc build --release` and the built app's three-frame `--smoke` run passed.
The C backend was tested on macOS; Windows/Linux GPU execution was not tested
in this follow-up.

## Remaining work

The next substantial steps are tolerance-aware trim arrangements/healing,
compatible compound-edge phase constraints, density grading, and general
cross-field layouts for incompatible parameterizations. Some fallback fans and
thin cells remain. There is no claim of complete STEP support or MoI-quality
meshing across all supplied models. The large alternate camera/car fixtures
still have explicit unsupported cases:

- `camera_2.step`: face 81 projection residual 0.010088 exceeds tolerance 0.01.
- `car1.step`: edge #93693 / curve #61161 endpoint residual 1.58559e-5 exceeds
  the file tolerance of 1e-5.
- `car2.step`: face 6 exceeds the adaptive patch face budget. It is still not
  a successful whole-model tessellation.

These errors remain explicit; model tolerances were not inflated to hide them.

No packages were published. Release-compiler and clean registry-install gates
from the workspace's publishing rules still apply before publication.

## Reproduction

From `luced-3d`, with `LUCE_BASE` pointing to the intended local Base compiler:

```sh
python3 tests/run.py --opt 2
python3 tests/run.py --opt 2 --backend c
python3 tools/cad_probe.py /Users/sedov/Desktop/camera.step --opt 2
python3 tools/surface_delta.py /Users/sedov/Desktop/camera.step /Users/sedov/Desktop/camera.obj
python3 tools/preview.py --scene cad_wire --file /Users/sedov/Desktop/camera.step --background --opt 2 --rotation-x 0 --pitch 0.2 --yaw 0.35 --zoom 0.14 --target 45 29 0 --output docs/preview_corner_trim_grid.png
luc build --release
```
