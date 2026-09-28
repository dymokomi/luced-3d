# Clipped NURBS interior spacing

Local checkpoint after [the frame-grid repair](CAD_FRAME_GRID_2026-09-28.md).
This reduces crowding in the four large camera frame corners while retaining
their exact shared boundaries and complete polygon topology. It does not make
every row uniform or resolve the other remaining camera defects.

## Implementation and safeguards

`clipped_rows.lucb` extracts complete original grid-line chains from a clipped
chart. Holes and trim vertices anchor their ends; ambiguous junctions stop
them. Only interior-to-interior gaps diagnose crowding, so an isolated short
last interval created by a boolean trim does not warp an otherwise regular grid.
Current scope is NURBS charts with stretched quads (edge ratio above 20) and
interior gap ratios above eight, not every ordinary cut cell.

`clipped_spacing.lucb` proposes equal physical chord-length spacing along
those chains, re-evaluating interior points on the exact support. Boundary
coordinates, IDs, normals and polygon corner arrays remain fixed. Up to three
sweeps try both directions, backtracking through factors 1, 1/2, 1/4, 1/8, 1/16.
Rejected candidates leave the accepted mesh unchanged. Non-geometric errors
still propagate rather than being silently swallowed.

Acceptance requires:

- Lower normalized physical gap variance across all chains, without increasing
  the worst gap ratio.
- No increased aggregate quad edge/aspect-and-angle distortion, without exceeding the
  original maximum edge ratio or counts of stretched/skewed quads. Originally
  well-angled charts cannot acquire corner sine below 0.5.
- Unchanged UV triangle orientation and quad corner-turn signs, preventing
  foldovers and newly concave quads.
- Valid actual display triangles against exact support normals and the existing
  sampled deviation budget. No tolerance or density setting is increased.

Frame 2358 rejects full moves on orientation/error grounds; it accepts 1/8,
then 1/16, and stops when further movement violates the error check. This is a
bounded improvement, not a claim that uniform redistribution always preserves
curvature. Global station-phase reconciliation remains a separate task.

## Result and native captures

| Frame patch | Stretched-20 quads before → after | Maximum edge ratio before → after |
|---|---:|---:|
| 2358 | 224 → 42 | 428.84 → 94.29 |
| 2382 | 113 → 10 | 77.17 → 69.02 |
| 2386 | 115 → 10 | 317.49 → 69.02 |
| 2406 | 30 → 4 | 720.64 → 37.65 |

Across these corners the stretched count falls from 482 to 66. No polygon is
added, removed or hidden. Comparison of the complete OBJ dumps shows identical
face arrays; 8,527 interior vertices move (maximum displacement 0.473647 model
units). This displacement is along the support, not surface deviation.

Native shaded-wire images at 4400 × 2604 pixels:

- Patch 2358: [before](preview_camera_frame2358_grid.png),
  [after](preview_camera_frame2358_spacing.png).
- Opposite corner [2386 after](preview_camera_frame2386_spacing.png).
- [Assembled frame and neighbors](preview_camera_frame2358_spacing_assembled.png).

Inspection confirms reduced crowding, but some doubled rows and frozen-boundary
clusters remain. These are real polygon wires, not hidden display diagonals.
The isolated views use neutral inspection lighting; the assembled view retains
normal scene materials. No screenshot editing is used.

## Verification

- Sixteen synthetic combinations cover flat/bilinear curved support, both
  senses, swapped axes, and a central hole. Assertions include exact trim/hole
  preservation, unchanged polygon corner arrays, better spacing, exact analytic
  support positions, positive triangles, projected area, no triangles spanning
  the hole, and unchanged sampled error limits.
- A separate tiny terminal boolean-cut interval regression retains the original
  mesh snapshot and every point exactly. It must not trigger redistribution.
- Complete native opt-2 and C-release application suites both pass all 26 PASS
  groups. This includes the internal Base contracts plus hard/G1 seam tests.
  The standalone Base layout contracts also pass native opt-0/1/3 and C debug.
- Native/C camera quality records agree exactly. Only the four patches above
  change. All 2,710 patches still have zero display-normal flags; method counts
  remain 2,210 local mapped, 456 clipped, 44 constrained.
- Full camera: unchanged 615,219 points / 576,990 polygons, zero boundary,
  nonmanifold or inconsistent edges, Euler 46. Area 65,662.61819901486;
  signed volume 74,393.09598336405. Observed cook 8.35 s, not a controlled
  performance benchmark.
- Fixed 4,096 OBJ-to-STEP samples: maximum remains 0.0259126; mean-square changes
  from 4.65839e-6 to 4.67935e-6 (about 0.45% higher). This checkpoint improves
  spacing, not aggregate OBJ agreement. STEP-to-OBJ max 0.0188468 / mean-square
  4.40099e-6 uses mesh-dependent sample locations and is not a like-for-like
  accuracy comparison or a certified bound.
- `sign`, `1p5inR`, `33mm_angle` vertex and face dumps are unchanged exactly;
  all retain zero topology flags.
- Main release app rebuilt in 19 s, native `--smoke` exit 0.

The new modules and tests are pure Luce Base. No fixture-specific branches,
compiler edits, GPU/UI changes, or luce-tesselator modifications are retained.
Temporary diagnostic prints are removed. Kernel work remains local/unpublished.

Records: `/private/tmp/clipped-spacing-full-{native,c}.log`,
`/private/tmp/camera-clipped-spacing-{guards.txt,c-quality.txt,topology.log,delta.log}`,
`/private/tmp/{sign,1p5inR,33mm_angle}-clipped-spacing.log`,
`/private/tmp/luced-clipped-spacing-{build,smoke}.log`.
The guards record includes temporary diagnostic lines from the same geometry;
the final C record, full suites, app and assembled capture contain none.
