# Planar conic envelopes and the boss end sliver

Tested local checkpoint following [many-coedge charts](CAD_MANY_COEDGES_2026-09-28.md).
The camera still needs density, spacing and remaining constrained-patch work.

## Cause

Planar patch 180 has two trim edges: a circular arc and its chord. Its mirrored
counterpart already clipped, but this end fell back to a triangle fan. Diagnostic
instrumentation identified `trim edge crosses an unsplit grid line`.

The planner bounded the initially sampled arc and added a 1% margin. An odd
sampling missed the arc's outermost point. Later grid intersections introduced
that point outside the original envelope: UV -2.9121346807 versus lower grid
bound -2.9115412008, a gap far larger than the numerical incidence threshold.
Increasing snap tolerance would have hidden the wrong problem.

`layout_bounds.lucb` now includes analytic projected extrema for planar circle
and ellipse arcs, restricted to their actual signed sweeps. These bounds extend
the chart envelope only; canonical trim points and their identities stay fixed.
Other curve/support families still use the previous guarded sampled envelope;
this is not a certified bounding solution for every NURBS chart.

## Evidence

- New standalone regression reproduced the original failure before the fix.
  Its final 64 variants cover circles/ellipses, reflections, rotated conics,
  translated chart origins, positive/negative curve sweeps and 1e-6/0.01 model
  uncertainties. Every case uses grid clipping, preserves source endpoints and
  its arc/chord boundary, has consistent interior edge orientation and positive
  display normals, matches analytic segment area within 1%, and passes inside/
  outside ray tests. Native and C pass.
- Patch 180: 179 quads + 220 triangles becomes 160 quads + 12 triangles + 22
  cut n-gons. Nineteen camera patches change; all 2,710 still have zero
  display-normal flags. No fixture-specific meshing branches were added.
- [Before the envelope fix](preview_camera_boss_clipped.png) and
  [after](preview_camera_boss_conic_bounds.png): matched full-production-cook
  native shaded-wire captures at 4400 × 2604 actual pixels. The end fan is
  replaced by a grid; authored grooves remain visible.

## Complete-model checks

Camera: 620,185 points, 584,088 polygons: 530,600 quads, 18,289 triangles and
35,199 cut/boundary n-gons. Native/C agree on all per-patch counts and normal
flags. Zero open/nonmanifold/inconsistent edges; Euler characteristic 46.
Actual display area 65,662.42632473 and signed volume 74,390.78045376.
Observed native full cook 8.32 s (not a controlled benchmark).

Fixed 4,096 OBJ-to-STEP samples: max 0.0297543, mean-square 5.58665e-6.
STEP-to-OBJ: max 0.0244862, mean-square 5.41829e-6. The latter sample locations
change with the mesh; neither direction is a Hausdorff certificate.

`sign`, `1p5inR` and `33mm_angle` retain their preceding counts and zero topology
flags, with Euler -30, 2 and 0. Complete native opt-2 and C-release application
suites pass; the final negative-sweep expansion additionally passes focused
native/C suites. Released Luce 0.8.18 and pinned Base, no compiler changes.
Main `build/Luced 3D.app` rebuilt in 18 s; native `--smoke` exits 0.

Current tessellation changes remain unpublished. All temporary diagnostics were
removed; `luce-tesselator` is unchanged by this pass.

Records: `/private/tmp/conic-bounds-full-{native,c}.log`,
`/private/tmp/planar-sliver-final-{native,c}.log`,
`/private/tmp/camera-conic-bounds-{quality.txt,c-quality.txt,topology.log,delta.log}`,
`/private/tmp/{sign,1p5inR,33mm_angle}-conic-bounds.log`,
`/private/tmp/luced-conic-bounds-{build,smoke}.log`.
