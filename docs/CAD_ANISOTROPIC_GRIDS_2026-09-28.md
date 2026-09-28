# Long, narrow clipped grids

Checkpoint after [band sampling](CAD_BAND_SAMPLING_2026-09-28.md). This removes
the large fans on camera patch 796, a planar rounded-notch ledge. Uneven density
and small cut-cell slivers remain; this is not a finished quad-layout solution.

## Cause and change

Patch 796 has 48 authored coedges. Its clipped plan failed during smooth-row
inheritance at 257 U stations and 36 V stations, reporting a station-budget
overflow. That forced a constrained triangulation even though the chart was
well below the clipper's total grid-point budget. It was not a curvature or
normal failure and did not require changing the hard-edge classifier.

The planner now allows 1,025 stations along either axis, bounded jointly by
131,072 grid points, matching `TrimGrid`. The total is checked during inherited
row planning, after directional refinement, and before every diagonal-error
grid allocation. It does not permit an unchecked 1,025 × 1,025 grid. Existing
shared-edge, boundary, intersection, error, normal and per-cell limits stay in
place. The final ledge chart has 338 U / 40 V stations, including guard lines.

## Result and limits

Patch 796 changes from 188 quads / 1,658 triangles to **6,362 quads / 17 triangles /
175 cut n-gons**. Its rounded-notch outlines and shared topology are preserved.
The camera now uses 2,210 local mapped / 457 clipped / 43 constrained patches.

Native captures at 4400 × 2604 pixels:

- Matching face-on close-ups: [before](preview_camera_ledge796_before.png),
  [after](preview_camera_ledge796_grid.png).
- [Ledge with its shared-edge neighbors](preview_camera_ledge796_neighbors.png).

Inspection shows regular clipped cells in place of large triangle fans. It also
shows dense columns beneath some notches, transitions to sparser columns, and
over-dense adjacent fillets. The new grid publishes additional intersections to
its smooth neighborhood: 95 patch-quality records change, all in IDs 729–880.
The four frame corners and the previous four lens-band improvements are unchanged.

This is a topology-strategy improvement, **not a reduction in mesh size**:
the complete camera grows from 572,198 to 618,384 polygons (46,186 more, about 8%).
Most of that growth is in the connected smooth neighborhood, not the ledge alone.
Total stretched-20 quads decrease from 53,731 to 53,447, but skewed-0.1 quads
increase from 2,083 to 2,104. Patch 796 itself has 24 stretched and 3 skewed quads;
its worst edge ratio is 555,383.7 at a very short cut-cell edge. Zero normal flags
do not make these slivers acceptable final modeling topology.

A trial of existing interior redistribution on analytic planes did not improve
796 and sheared orthogonal grids on other patches. That trial is **not retained**.
The next work must address station families and trim-adjacent cells, not merely
relax planar vertex positions or increase the grid budget again.

## Verification

- New long-strip regression: an irregular planar tab, 500+ longitudinal
  intervals, both parameter-axis orientations, both face windings. It requires
  the clipped strategy, checks unchanged source corners, exact signed area,
  positive support normals and rays through retained/removed tab regions.
- Negative control: restoring the old 257-axis cap makes the new regression
  fail at its clipped-strategy assertion. The final source restores 1,025.
- Base budget contracts accept a 1,025 × 127 strip in both orientations and
  reject excessive products and excessive axis counts.
- Full native opt-2 and C-release application suites pass all 27 PASS groups.
  Standalone Base contracts pass native opt-0/1/3 and C debug.
- Native/C camera quality records agree exactly. All 2,710 source patches remain,
  with zero display-normal flags. Complete topology audit: zero open,
  nonmanifold or inconsistent edges; Euler characteristic 46.
- 657,760 points / 618,384 polygons: 568,725 quads, 13,586 triangles, 36,073 n-gons.
  Actual display area 65,662.58140748247; signed volume 74,393.21168119059.
- Fixed 4,096 OBJ-to-STEP samples: maximum remains 0.0259126; mean-square
  4.68863e-6 versus 4.68847e-6. STEP-to-OBJ max 0.0286789 / mean-square
  4.81635e-6 uses mesh-dependent sample locations, so it is not a like-for-like
  accuracy comparison or a certified bound.
- `sign`, `1p5inR`, `33mm_angle` vertex and face dumps remain identical to the
  previous checkpoint; no topology flags.
- Observed native camera cook 8.68 s, not a controlled benchmark. Main app release
  rebuild 19 s; native `--smoke` exit 0.
- Public release CI rechecked: luced-3d main/v0.1.2 correctness and luce-ui
  main/v0.8.15 correctness/Windows runs are completed and successful. These
  runs verify the published releases, not the unpublished local kernel work.

The capture harness now supports `--patch-neighbors`: it selects the requested
patch and CAD patches sharing actual mesh edges **after the complete cook**.
It preserves global stations and display triangles. It is diagnostic isolation,
not a render mode that hides geometry or wire edges in the application.

Records: `/private/tmp/ledge-grid-{native,c}.log`,
`/private/tmp/camera-ledge-grid-{c-quality.txt,topology.log,delta.log}`,
`/private/tmp/anisotropic-grid-{contract,negative}.log`,
`/private/tmp/luced-ledge-grid-{build,smoke}.log`.
Initial diagnostic records `camera-ledge-budget.txt` and `camera-ledge-rows.txt`
contain temporary prints; final source, C records and app contain none.

Implementation is pure Luce Base in `luce-cad`; no compiler, GPU/UI, renderer or
luce-tesselator modification was needed. Local kernel work is still unpublished.
