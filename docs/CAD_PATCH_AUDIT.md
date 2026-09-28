# Next patch audit

This is a work list, **not a claim that these defects are fixed**. Complete the
project/UI/icon and installation release queue before starting the requested
ongoing tessellation goal. Begin with the user's `camera.step`, then expand to
the other Desktop STEP/OBJ pairs. Desktop models remain read-only and untracked.

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
  Identify which support-row or post-stitch fallback creates them.
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
