# Repeated-seam band sampling

Local checkpoint after [clipped interior spacing](CAD_CLIPPED_SPACING_2026-09-28.md).
Four lens bands have fewer excess cross-filleting rows. This is not a global
station-phase solution, and the rest of the camera is not yet pristine.

## Cause and retained change

The lens cross-section splines already requested 32 intervals before any seam
propagation. The sampler doubled 1, 2, 4, … and returned the first passing count;
it never checked whether an intermediate count met the same criteria.

`edge_sampling.lucb` now uses a bounded bracket search for eligible seams. Every
returned count passes the original chord-distance and angular-turn checks in
its own sample phase. The distance budget, angle target, exact curves, normals,
G0/G1 classification and capped C0 fallback are unchanged. The sampled predicate
is not monotonic in general; the search keeps a passing upper bound and does not
claim a global minimum or certified deflection bound.

Eligibility is deliberately conservative: exactly two opposite, oppositely
oriented uses of an edge within one single-loop four-coedge face, with no use
by another face. Other edges retain their established dyadic family. This is a
topological condition, not a camera name, patch ID, or coordinate special case.

### Rejected broader experiment

Compacting all spline counts reduced the camera to 448,429 polygons, but changed
shared-edge phases and damaged some previously improved frame corners. Their
maximum edge ratios rose from roughly 69 to 1,228. Aggregate counts and zero
normal flags had hidden this regression. That broad change is **not retained**.

An intermediate experiment allowed all single-face repeated seams; its irregular
trimmed patch 710 changed cut-cell shapes. The final policy excludes those
irregular bands too. Global shared-edge compaction needs coherent station-family
planning and downstream quality acceptance, not independent curve optimization.

## Camera result

Only patches 273, 717, 719 and 725 change in the complete per-patch quality
comparison. All four previously repaired frame-corner records are identical.

| Patch | Quads before → after | Stretched-20 quads before → after | Maximum edge ratio before → after |
|---|---:|---:|---:|
| 273 | 3,504 → 2,272 | 0 → 0 | 6.65 → 4.37 |
| 717 | 5,410 → 3,690 | 5,400 → 85 | 46.51 → 31.96 |
| 719 | 3,108 → 2,108 | 3,108 → 2,108 | 59.43 → 40.88 |
| 725 | 2,628 → 1,788 | 2,628 → 1,788 | 33.86 → 23.28 |

Patch 273 uses 21 cross-section intervals, the other three 22 instead of 32.
Their circumferential counts and boundary n-gon counts are unchanged. Whole
camera polygon count falls by 4,792, from 576,990 to 572,198 (0.83%), **not** the
22% of the rejected experiment. Stretched-20 count falls from 60,886 to 53,731.

Native shaded-wire captures, 4400 × 2604 actual pixels:

- Patch 717 [before](preview_camera_lens717_before.png) and
  [after](preview_camera_lens717_bracket.png), matching target, zoom and orbit.
- [Assembled lens and neighboring surfaces](preview_camera_lens_bracket_assembled.png).

The close-up shows fewer longitudinal rows; the assembled view still shows very
thin fillet strips and unresolved neighboring phase crowding. These are actual
polygon wires, not hidden triangulation. No screenshot editing is used. This
checkpoint does not claim that the four bands are optimally isotropic quads.

## Verification

- Twenty-four rational quarter-circle variants cover two radii, two tolerances,
  three orientations and both directions. Each tests the unchanged shared-edge
  count, compact count, original angular predicate, exact support, and 63
  independent distance probes per interval. A C0 kink keeps its capped fallback.
- Synthetic ownership cases distinguish opposite repeated seams from external
  sharing, an irregular loop, adjacent repeats, same-direction repeats and an
  unused edge.
- Full native opt-2 and C-release application suites: all 26 PASS groups.
  Standalone Base layout contracts also pass native opt-0/1/3 and C debug.
- Native/C per-patch quality records agree exactly; all 2,710 patches have zero
  display-normal flags. Methods remain 2,210 local mapped / 456 clipped /
  44 constrained. Skewed-0.1 count remains 2,083.
- Whole camera: 610,427 points / 572,198 polygons, including 521,535 quads,
  15,211 triangles and 35,452 n-gons. Zero open, nonmanifold or inconsistent edges;
  Euler 46. Area 65,662.58249957001; signed volume 74,393.21181312569.
- Fixed 4,096 OBJ-to-STEP samples retain maximum 0.0259126. Mean-square changes
  from 4.67935e-6 to 4.68847e-6 (about 0.19% higher). This is a spacing/density
  improvement, not improved reference agreement. STEP-to-OBJ max 0.0206751 /
  mean-square 4.74741e-6 uses mesh-dependent sample locations; these numbers
  are neither like-for-like accuracy measurements nor certified bounds.
- `sign`, `1p5inR`, `33mm_angle`: vertex and face dumps match the previous
  checkpoint exactly; zero topology flags.
- Observed camera cook 8.38 s; this is not a controlled speed benchmark.
  The main release app rebuild took 19 s and its native `--smoke` test exited 0.

The implementation and regressions are pure Luce Base. No compiler, UI, GPU,
renderer, or luce-tesselator changes were needed. Kernel work remains local and
unpublished. Useful records: `/private/tmp/camera-band-bracket-{quality.txt,c-quality.txt,topology.log,delta.log}`,
`/private/tmp/seam-bracket-final-{native,c}.log`, and
`/private/tmp/luced-band-bracket-{build,smoke}.log`.
