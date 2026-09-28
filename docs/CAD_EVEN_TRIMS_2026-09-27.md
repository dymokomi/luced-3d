# Physical row spacing and trim-cell robustness — September 27, 2026

Follow-up to the four screenshots showing bunched rows and circular/rounded
trims falling back to fans. Runtime changes are entirely Luce Base in `luce-cad`
and `luce-tesselator`. No luced-2d, UI, GPU, compiler or polygon-engine changes.
The local application was rebuilt; nothing was published.

## Spacing changes

- `curve_spacing` measures physical arc length once per shared edge. Extra
  intervals on a compound logical side go to its largest physical pitch, not
  almost equally to every STEP coedge regardless of length.
- `layout_counts` agrees on counts across compatible flow seams before placing
  rows. This avoids interleaving independently phased sample families simply
  because two neighboring patches initially requested different counts. Hard
  seams still keep independent interior layouts.
- Spline rows use approximately equal arc-length spacing when the sampled
  chord/turn tests accept it. Curves that cannot pass within the existing budget
  retain parameter spacing. At the cap, an alternative distribution is allowed
  only if its sampled maximum chord error and turn are no worse than the old
  distribution. These checks are sampled, not certified deflection bounds.
- Late count balancing measures physical gaps and splits at arc midpoints.
  `row_redistribution` also redistributes uneven late-added row families on
  rails classified as straight. Old trim intersections remain shared boundary
  corners; they are not deleted or welded to make the wireframe look cleaner.
- Output points still evaluate the exact retained CAD curves/surfaces. Original
  CAD vertices and trim geometry do not move. Generated sample positions may
  change between tessellations, as intended by physical redistribution.

The distinction between index-based and arc-length-based grid distributions is
also described in [NASA's GMAN grid generation documentation](https://www.grc.nasa.gov/www/winddocs/gman/gridgen.html).
This implementation is a bounded original planner, not a global optimal quad
layout solver or a reproduction of MoI's mesher.

## Why Boolean-style clipping was still becoming fans

Three separate correctness problems were found in the existing clipping path:

1. The lens panel's outer loop visits the same CAD vertex twice. The old clipper
   treated those occurrences as unrelated points and rejected their common grid
   corner. `TrimGrid.clip_identified` now accepts explicit vertex identities;
   `cut_topology` validates their projections and audits boundary multiplicity.
   Equal coordinates alone never authorize merging two vertices.
2. Frame trim curves approach a straight grid line tangentially. Snapping several
   nearby samples to that line flattened a thin region, despite each individual
   move being inside CAD tolerance. Alignment is now restricted to actual
   crossings or roundoff-sized corrections, using an unmodified neighborhood.
3. CAD fitting tolerance was also being used to decide whether vertices belong
   to grid sides. This confused close parallel/tangent boundaries with coincident
   boundaries. Grid incidence now uses a separate, much smaller tolerance;
   grid-side ownership is selected explicitly rather than by a large positional
   offset. Interior classification uses a representable inward displacement,
   including in very thin cells. Planar curve/grid roots are refined more tightly.

Consequently, the checked lens panel and frame patches retain their grid cells
and clipped boundary n-gons instead of rejecting the arrangement and invoking
the constrained fan fallback. Shared boundary identities, surface normals,
colors and source group paths are retained. This is trim-cell clipping, not a
new general CAD Boolean engine.

On the full camera, the lens panel (CAD face 271) has 412 quads and 136 other
polygons, versus 533 and 378 before this pass. Frame faces 2285 and 2317 now have
779/103 and 790/92 respectively (quads/other polygons). Other includes legitimate
cut-cell n-gons; a lower non-quad count is not itself a correctness proof.

## Verification

All 20 regression groups pass with optimized native and C backends on macOS.
New assertions cover tiny/long compound coedges, physically even spacing on a
nonuniformly parameterized straight spline, preservation of exact support,
pinched loops with explicit identities, rejection of unowned coincident
vertices, a 3e-8-wide strip beside a grid line, and a near-tangent CAD curve that
must remain in the clipped-grid path. Existing seam, hole, normal, winding,
parallel determinism, import, DAG and editor regressions remain green.

`luc build --release` and the built application's `--smoke` pass. Tests use
sibling path dependencies and the configured local toolchain. They are not a
registry-install/publishing gate or Windows/Linux execution tests.

Divisions 16, edge-size control off; individual development runs:

| STEP | Points | Polygons | Quads | Triangles | Other polygons | Tessellation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| camera | 775,566 | 776,711 | 659,595 | 85,808 | 31,308 | 8.11 s |
| sign | 9,526 | 11,752 | 7,331 | 4,412 | 9 | 0.315 s |
| 1p5inR | 2,978 | 2,625 | 2,528 | 0 | 97 | 0.027 s |
| 33mm_angle | 4,797 | 4,140 | 3,824 | 12 | 304 | 0.034 s |

All four have zero open, non-manifold and inconsistently oriented edges. Euler
characteristics remain 46, -30, 2 and 0. These audits do not certify absence of
every geometric self-intersection in legacy fallbacks.

Compared with the preceding seam-flow pass, camera polygons decreased from
818,587 to 776,711 (5.1%), triangles from 132,952 to 85,808, and tessellation from
8.54 to 8.11 seconds in these runs. This is not a controlled benchmark.

The fixed 4,096 OBJ-to-STEP samples retain maximum distance 0.0305139 source
units. Mean squared distance is 8.22577e-6 versus 8.50899e-6 before; RMS is
approximately 0.002868 versus 0.002917. Reverse STEP-to-OBJ samples have maximum
0.0371147 and mean squared distance 1.00686e-5. Reverse sample locations change
with the mesh, so these are not paired per-part/Hausdorff certificates or proof
that every local patch improved.

The retained-GPU probe records the full UI in 0.475 ms with 1,552,243 wire
segments (previously 0.484 ms / 1,605,475 segments). Camera update is 0.00053 ms.
This measures CPU command recording without GPU submission, not GPU frame time
or input-to-photon latency. Background computation remains off the UI thread;
the existing parallel face workers consume the frozen plans.

## Inspected native shaded-wireframe captures

- [Lens close-up](preview_lens_even_trims.png): the planar grid terminates cleanly
  at the circular opening. Some adjacent curved rims/side transitions still
  contain dense rows and fallback fans.
- [Frame](preview_frame_even_trims.png): clipped planar grids retained around
  the rounded trim regions; this is an overview, not a complete microfeature audit.
- [Lower camera corner](preview_corner_even_trims.png): quad layout retained and
  physical spacing improved in accepted families, but the entire bend is not
  uniformly graded. Dense transitions remain visible.

A knot-based redistribution experiment was rejected after its native capture
introduced new underside fans; that experiment is not in the final code.

The remaining work is joint layout optimization across compound curved sides
and better handling of constrained/singular curved fallback patches. This pass
does not claim that every span in screenshots 1–2 is now evenly spaced, that
every trim uses clipping, or that all four screenshots' artifacts are solved.
Other camera/car import limitations from earlier reports were not re-audited.
