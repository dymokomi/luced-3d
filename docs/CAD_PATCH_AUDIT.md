# Next patch audit

Current work: [even physical rows on mapped affine strips](CAD_MAPPED_EXTRUSIONS_2026-09-28.md).
Previous checkpoint: [canonical seams and preserved diagnostic normals](CAD_CANONICAL_SEAMS_2026-09-28.md).
Previous checkpoint: [small-scale diagonals and ear remainders](CAD_EAR_REMAINDERS_2026-09-28.md).
Latest verified repair: [collapsed physical cut ribbons](CAD_COLLAPSED_RIBBONS_2026-09-28.md).
Preceding investigation: [trim predicates and the now-repaired regression](CAD_TRIM_PREDICATES_2026-09-28.md).
Previous app checkpoint: [continuous analytic charts and physical cut-cell cleanup](CAD_ANALYTIC_BRANCHES_2026-09-28.md).
Previous checkpoint: [button rims and geometric polygon deviation](CAD_CELL_DEVIATION_2026-09-28.md).
Earlier morning checkpoint: [STEP import tolerance and broader-model robustness](CAD_IMPORT_ROBUSTNESS_2026-09-28.md).
The notes below retain the earlier overnight patch work; that newer report
records current loading blockers and does not claim the remaining flow defects
are resolved.

This is a work list, **not a claim that these defects are fixed**. Complete the
project/UI/icon and installation release queue before starting the requested
ongoing tessellation goal. Begin with the user's `camera.step`, then expand to
the other Desktop STEP/OBJ pairs. Desktop models remain read-only and untracked.

The prerequisite release queue is now complete and the ongoing goal is active.
First audit/results: [compound circular sides](CAD_COMPOUND_ARCS_2026-09-27.md).
Follow-ups: [periodic charts](CAD_PERIODIC_CHARTS_2026-09-27.md), then
[retained display triangles and analytic trim grids](CAD_DISPLAY_AND_ANALYTIC_GRIDS_2026-09-28.md).
Previous checkpoint: [hard-edge row stops and circular spacing](CAD_HARD_STOPS_AND_CIRCULAR_SPACING_2026-09-28.md).
Then [mixed-chart circular rails](CAD_MIXED_CHART_RAILS_2026-09-28.md).
Then [many-coedge clipped charts](CAD_MANY_COEDGES_2026-09-28.md).
Then [planar conic envelopes](CAD_CONIC_ENVELOPES_2026-09-28.md).
Then [grazing cut cells](CAD_GRAZING_CELLS_2026-09-28.md).
Then [frame grid and polygon area scaling](CAD_FRAME_GRID_2026-09-28.md).
Then [clipped interior spacing](CAD_CLIPPED_SPACING_2026-09-28.md).
Then [repeated-seam band sampling](CAD_BAND_SAMPLING_2026-09-28.md).
Then [long, narrow clipped grids](CAD_ANISOTROPIC_GRIDS_2026-09-28.md).
Then [shallow crossings and independent planar strips](CAD_SHALLOW_CROSSINGS_2026-09-28.md).
Then [endpoint-only smooth joins](CAD_ENDPOINT_FLOW_2026-09-28.md).
Then [late seam cuts versus interior rows](CAD_FLOW_ADMISSION_2026-09-28.md).
Then [trim incidence and boundary-adjacent gaps](CAD_ALIGNMENT_AND_END_GAPS_2026-09-28.md).
Then [stopped endpoints on affine extrusions](CAD_EXTRUSION_ENDPOINTS_2026-09-28.md).
Then [physical pitch and competing row phases](CAD_PHYSICAL_PITCH_2026-09-28.md).
Current checkpoint: [planar map preflight and cut ribbons](CAD_PLANAR_PREFLIGHT_2026-09-28.md).
The earlier display-normal failures are resolved on the current camera audit.
That does **not** resolve the separate spacing, aspect-ratio and remaining
fallback-fan work below; zero normal flags are not a mesh-quality certificate.

The hard-edge `support_rows` override is now removed. Camera totals are 632,814
polygons with zero topology/normal flags. Patch 715's mixed-chart row crowding
is improved: all coedges on its clipped NURBS neighbor's dominant rail now seed
the same initial family. Physical rail classification accommodates fitted
support noise without loosening trim tolerance. The ring has 172 quads, no
stretched-20 cells, and maximum edge ratio 13.21 (previously 5,384.15).
Adjacent patch 717 remains dense, but refining its self-seam count from 32 to 22
under the same sampled error/angle tests reduces stretched-20 quads from 5,400
to 85. Bands 273, 719 and 725 also improve, without changing any other camera
patch's quality record. A broader experiment compacting externally shared edges
was rejected because it worsened frame-corner phases, despite lower global
polygon counts. Those shared-edge counts remain unchanged until a global
phase/quality solution is available. The small boss's conical rim (patch 243)
now clips its 172 authored coedges instead of using the constrained fallback:
1,448 triangles become 8. Its planar end sliver 180 now also clips: analytic
conic extrema replace the incomplete sampled envelope that caused the fallback.
It first changed from 179 quads + 220 triangles to 160 quads + 12 triangles + 22
cut n-gons. Physical spacing for independent narrow planes now reduces it to
12 quads + 2 triangles + 14 cut n-gons, with two skewed cut quads still present.
Both ends of the grooved boss now show grids rather than fan clusters.
Patch 551 and underside patch 2154 also benefit from admitting many-coedge charts.

Current strategy distribution: 2,208 local mapped patches, 475 clipped patches,
27 constrained patches. Four additional planar strips stopped failing clipping
after separating shallow-crossing incidence from the coarser row-spacing
epsilon. Independent strips 427/435 now have 13 quads + 3 trim n-gons each,
with no fans and maximum quad edge ratio 1.48415. Strips 421/422 now clip too.
Their initial excess density was not actual inherited rows: the mere presence
of endpoint-only smooth rails blocked physical pitch. Checking real interior
stations instead first reduced each to 32 quads + 2 trim n-gons. A later shared
cut introduced a row only 0.01 units from the trim. A quality gate for late flow
on initially independent planar charts now retains that exact seam cut without
extending its poor phase across the strip: each first had 14 quads + 3 trim n-gons,
zero stretched-20 quads and maximum quad edge ratio 6.2516. The gate is not
applied broadly to curved or initially coupled charts.
Affine-extrusion endpoint ownership then removed one redundant quad from each.
Fillets 606/607 no longer extend two unequal stopped-trim endpoint coordinates
across their straight support direction. Each changes from 1,026 quads + 62 cut
polygons to 961 quads + 63 cut polygons; the wedge disappears, and minimum quad
corner sine improves to approximately 1. Bounded physical pitch now splits the
straight direction without moving curved stations: each has 18,004 quads,
1 triangle and 75 cut n-gons. Maximum aspect improves from about 295 to 16.88,
while minimum corner sine remains approximately 1. Competing late row phases
remain boundary cuts rather than crowding this already adequate interior grid.
Adjacent 605/608 improve from maximum aspect 53.35 to 3.06. Their planar
neighbors 421/422 become denser too: 553 quads, 1 triangle and 13 cut n-gons each.
Their worst cut-cell aspect rises from 6.25 to 18.96, with no stretched-20 or
skewed-0.1 flags; do not describe every neighboring cut polygon as improved.
This adds 43,730 polygons (7.4%) to the assembled camera. Other
curved camera patches retain the prior station policy, after broad endpoint
omission was measured to worsen several frame patches.
Neighbors 403/418 have fewer total quads but more stretched-20 cells, so this is
not a complete coupled-spacing solution.
Planar notched ledge 796 now uses a clipped grid after
replacing a square axis-count limit with an anisotropic joint grid budget.
Its 1,658 triangles become 17, but it and its smooth neighbors remain too dense;
that checkpoint grew total camera polygons by 46,186 and some cut-cell slivers have extreme edge
ratios. The matched captures are visibly better than the old fans, not pristine.
Do not mistake a strategy change or green topology for good spacing everywhere.
Planar four-logical-side ledges 334/336/361/363 now receive a clipped alternative
before their fitted grids fail: 712/607/737/454 triangles become zero, with
20/16/20/16 real polygons. Twelve planar patches move out of the constrained
fallback, including frame planes 2287 and 2320–2337 (see checkpoint for IDs).
The latter exposed almost coincident trim/grid ribbons. Bounded planar cell
unions retain every trim point and remove only internal grid edges; planes
2287/2323 now have maximum quad edge ratio 2.36 rather than the rejected
intermediate result's 7.1 million. The retained full camera has fewer polygons
than the preceding checkpoint and no patch gains stretched/skewed quad flags.
Thirteen cylinder strips in 2533–2559 now use clean
clipped grids: grazing slivers merge into adjacent cells without moving the
trim, and a bounded global display triangulation resolves stalled local flips.
Patch 2537 changes from 346 quads + 180 triangles to 27 quads + 10 cut polygons;
matched native captures show the removed fans and regular interior. Other
constrained strips and the dense mapped fillets need further audit; method provenance is not proof
of quality. Frame patch 2358 now clips after fixing an absolute polygon-normal
area cutoff and allowing bounded cut-cell merges up to one eighth of a neighbor.
It changes from 42 quads / 742 triangles to 1,890 quads / 3 triangles / 104 cut
polygons. The fixed OBJ-reference maximum decreases from 0.0297543 to 0.0259126.
Bounded physical redistribution now improves its crowded interior without
moving shared boundaries: stretched-20 quads fall from 224 to 42. The other
three frame corners (2382, 2386, 2406) change from 113/115/30 stretched quads to
10/10/4. Overlapping incoming smooth-seam station sets still leave visible
double/triple rows, especially at the frozen boundary; this is not a finished
global spacing solution. Temporary intersection diagnostics exposed additional NURBS
near-grid crossings; unlike the planar envelope bug these need investigation
of exact root insertion versus the proximity/snap guards. Raw diagnostic:
`/private/tmp/camera-planar-unsplit-debug.txt` (instrumentation removed).

The acceptance rule is not simply “more quads”: preserve exact trim boundaries,
surface error and watertight topology, then improve physical spacing and element
shape. Canonical boundary samples are shared even where interior row flow stops.
G0 creases must not transport rows merely to equalize counts. Compatible smooth
UV directions (including axis swaps) can transport flow; oblique/incompatible
trims should clip the grid. Keep boundary polygons where geometrically safe;
don't hide missing curvature support in a large warped n-gon.

Explicit user examples to locate by CAD face/edge IDs and capture before/after:

- Circular raised cap: dense upper/lower rim, sparse central wall and mismatched
  stations. Check cap-to-rim continuity and physical sampling independently.
- Small boss on curved housing: radiating triangle fans and coarse triangular
  housing cells. Check clipping path and local curvature budget.
- Rounded housing transition: multiple rows bunch near an incompatible trim;
  distant cap edges skew toward those stations. Audit hard/G1 flow decisions.
- Narrow recessed ledge: repeated dense diamond/triangle fans across the strip.
  Planar strips 427/435 are corrected and captured; 421/422 now also stop the poor
  late inherited row while retaining the seam vertex. Affine fillets 606/607 now
  have bounded physical pitch; dense adjacent NURBS 403/418 and other ledges
  remain under audit. Planes 334/336/361/363 now have matched before/after
  captures without their fans. Remaining constrained candidates include
  269/252, 2351/2353 and planar 722 (an unsplit-grid crossing).
- Underside long sweep and straight/corner junctions from earlier screenshots.
- First interior row on both sides of a trim is too far from the boundary;
  keep the trim fixed, improve interior spacing instead of shifting the seam.

For each region, record patch IDs, seam classification, baseline/adaptive/
inherited row counts, trim support, min/max physical gaps, surface deviation,
polygon valence/aspect distribution and native shaded-wire captures. Inspect the
assembled result as well as isolated patches. Use larger viewport-only captures
and report actual dimensions. Re-run native/C regression suites and topology
audits, then periodically rebuild the main app after passing checks.

Known broader fixtures: `camera_2.step` has a singular-direction failure,
`car1.step` an endpoint tolerance failure, and `car2.step` crossing/touching trims.
Do not silently inflate tolerances or substitute their OBJ meshes for STEP.
