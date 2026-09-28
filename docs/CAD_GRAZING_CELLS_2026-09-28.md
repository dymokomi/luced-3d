# Grazing cut cells and constrained cylinder strips

Local checkpoint after [conic envelopes](CAD_CONIC_ENVELOPES_2026-09-28.md).
This improves another family of camera patches; it does not certify the whole
camera's quad spacing or resolve the remaining 45 constrained patches.

## Two causes, two bounded repairs

Patch 2537 is a six-coedge cylinder strip, not a NURBS projection failure.
A grid line grazing its fitted trim creates a tiny UV triangle with only about
1e-9 axial width. Canonical 3D trim points differ slightly from the aligned UV
rail. Lifting this cell gives a triangle opposing its support normals, so the
entire patch previously fell back to a dense constrained mesh. The adjacent
mirror strips also had cut polygons whose local diagonal flips stalled.

- `clipped_merge.lucb` merges a failed sliver into a neighbor across exactly one
  internal manifold edge. The small cell must occupy at most 1% of the neighbor's
  UV area. Additional touching vertices are rejected, as are unions over 256
  corners. Boundary vertices, positions, identities and trim segments remain
  unchanged. A linear topology scan finds neighbors; work stops after 32 merges.
- `clipped_triangulation.lucb` solves the remaining small-polygon triangulation
  globally when local flips and projected triangulation fail. Its dynamic
  program permits only visible UV diagonals and triangles positively oriented
  against every support normal. Its shape cost favors less elongated display
  triangles. The O(n³) search is limited to 256 corners and the exceptional
  failed cells, not every ordinary quad.
- The actual final display triangles still pass the existing sampled surface
  deviation check. No CAD tolerance, seam welding rule or normal test was relaxed.
  Failure still rolls back to the next meshing strategy.

Small-cell agglomeration is an established approach in embedded Cartesian
meshing; this independently written surface-polygon implementation uses much
stricter trim-preservation constraints than a flow-discretization merge.
Background: [Toprak, Rieckmann and Kummer, 2024](https://arxiv.org/abs/2404.15285).
That paper is not evidence that our CAD surface error is certified.

## Native visual checks

Matched full-production-cook captures, isolated only **after** tessellation:
4400 × 2604 actual pixels. Inspection uses neutral material and balanced lights
to reveal these dark underside strips; actual mesh, normals, depth testing and
wire edges are unchanged. The preview tool now offers `--neutral` for this.

| Patch | Before (quads / triangles / n-gons) | After | Captures |
|---|---:|---:|---|
| 2537 | 346 / 180 / 0 | 27 / 0 / 10 | [before](preview_camera_strip2537_baseline.png), [after](preview_camera_strip2537_repaired.png) |
| 2533 | 461 / 231 / 0 | 59 / 0 / 10 | [before](preview_camera_strip2533_baseline.png), [after](preview_camera_strip2533_repaired.png) |

Thirteen previously constrained cylinder strips now clip. Three other patches
(2382, 2386, 2406) now accept the earlier clipped-grid candidate instead of local
mapping. Sixteen camera patches change overall. This is local improvement, not
an assertion that every constrained patch should become a rectangle.

## Verification

- Synthetic grazing-cylinder tests cover three angular phases, both windings,
  exact preservation of all five UV/3D boundary vertices, removal only of the
  internal sliver chord, and rejection when no safe neighboring cell exists.
- Global triangulation tests cover a concave U-shaped polygon, both windings,
  positive normals, exact area, no triangle centroid in the notch, retained
  directed display topology, and rejection of fully opposing normals.
- Complete native opt-2 and C-release application suites pass. Final focused
  native/C runs also check the explicit canonical-position assertions.
- Full camera: 613,497 points; 575,777 polygons (524,479 quads, 15,950 triangles,
  35,348 n-gons). All 2,710 patches have zero display-normal flags. Native/C
  agree on every per-patch polygon count, method and normal flag.
- Zero open, nonmanifold or inconsistently oriented edges; Euler 46. Actual
  display area 65,662.40306185; signed volume 74,390.63068830. Observed native
  full cook 8.05 s, not a controlled performance comparison.
- Fixed 4,096 OBJ-to-STEP samples: maximum remains 0.0297543; mean-square
  5.55978e-6. STEP-to-OBJ: max 0.0285106, mean-square 5.32755e-6. The latter
  sample locations change with the mesh; its maximum is not a like-for-like
  comparison with the previous mesh or a Hausdorff certificate. Worst fixed
  reference sample still belongs to frame patch 2358.
- `sign`, `1p5inR` and `33mm_angle` retain their preceding counts and zero
  topology flags (Euler -30, 2 and 0 respectively).
- Main `build/Luced 3D.app` rebuilt in 18 seconds; native `--smoke` exits 0.

Temporary diagnostics and the before-capture code switches are removed. Current
kernel changes remain local/unpublished. No compiler or luce-tesselator changes.

Records: `/private/tmp/cutcell-{full,final}-{native,c}.log`,
`/private/tmp/camera-cutcell-{quality.txt,c-quality.txt,topology.log,delta.log}`,
`/private/tmp/{sign,1p5inR,33mm_angle}-cutcell.log`,
`/private/tmp/camera-strip{2533,2537}-{baseline,repaired}-preview.log`,
`/private/tmp/luced-cutcell-{build,smoke}.log`.
