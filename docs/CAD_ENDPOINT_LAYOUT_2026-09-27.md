# Camera spline endpoints and patch-layout correction

Local implementation and verification, September 27, 2026. Not published.
This supersedes the phase-mismatch workaround in the hard-trim report.

## Root causes and changes

1. **False spline-end wrapping.** Reconstructing a trimmed parameter as
   `angle + sweep * fraction` could exceed the last knot by a few ulps. The
   evaluator treated this as a genuine periodic seam crossing and returned the
   opposite end of an open edge. Topological endpoints were correct, but the
   arc-length and density planners measured a large fictitious final jump.
   Camera edge 6013, for example, jumped from approximately z=-3.871 near its
   end to z=+3.924 at fraction 1, instead of ending at z=-3.924. Clamping
   arithmetic roundoff **before** wrapping fixes the underlying geometry
   evaluation. Genuine seam-crossing intervals still wrap.
2. **Stale shared rows.** A final mapped-side balance could introduce rows
   after a neighboring clipped grid had stopped reconciling. The two planners
   now reconcile together before freezing shared samples. Compatible smooth
   stations are mandatory. Late straight-rail redistribution skips flow seams.
   Hard/incompatible boundaries still share vertices without requiring a row
   through the neighboring interior. The arbitrary opposite-phase clipping
   heuristic has been removed; hard oblique trims still select clipping.
3. **Missed diagonal curvature.** Straight or adequately sampled U/V isocurves
   do not guarantee adequate display triangles. The planner now checks both
   quad diagonals and adds complete support rows before registering trim
   intersections. This prevents some camera corner grids from being rejected
   later in favor of stretched boundary-fitted layouts.
4. **First/last interior spacing.** Physical row redistribution includes the
   gaps immediately inside both fixed trims. Acceptance checks normalized gap
   variance as well as the worst gap ratio: improving one axis is no longer
   blocked solely by an unchanged worst row in the other. Sampled display error
   uses the tessellation quality budget, not the much smaller CAD boundary
   tolerance. Original trim vertices, support evaluation, and UV orientation
   remain constrained. This is a bounded heuristic, not an error certificate.

Runtime changes are confined to Luce Base in `luce-cad`. No compiler, luce-ui,
luce-gpu, or luced-2d source changes were needed.

## Visual verification

Actual Metal shaded-wireframe captures of the complete STEP tessellation:

- [Underside/shared seam](preview_camera_endpoint_bottom.png): straight rows;
  the large cross-band diagonal sweep is gone in this view.
- [Straight side](preview_camera_endpoint_straight.png): inspect row continuity
  and spacing near the retained patch boundaries.
- [Lower rounded corner](preview_camera_endpoint_corner.png): inspect the
  interior gap distribution and transition from the straight band.
- [Upper rounded corner](preview_camera_endpoint_upper.png): the opposite
  corner, including its dense outer trim region.

These are not a claim of uniformly ideal quads throughout the model. Dense
periodic/compound transitions, some fallback triangles, and dashed/aliased
wire rendering remain visible. No edges were hidden to make the captures look
cleaner, and the trim tolerance was not relaxed.

## Validation

All 21 test groups passed with both native and C backends on macOS. Internal
regressions cover positive/negative endpoint roundoff, real periodic crossings,
mixed curvature on a bilinear saddle, and fixed trims with uneven first/last
interior gaps in one or both axes. Existing regressions cover hard-edge
n-gons, rotated smooth-frame stops, swapped-axis smooth continuation, curved
strip support, holes, topology, and the application's DAG/background workflow.
The optimized local app build and native `--smoke` also passed. No Windows or
Linux execution was performed.

Full meshes at divisions 16, edge size 0:

| Model | Points | Polygons | Quads | Triangles | Open / nonmanifold / winding conflicts |
| --- | ---: | ---: | ---: | ---: | --- |
| camera | 674,929 | 681,714 | 571,476 | 86,198 | 0 / 0 / 0 |
| sign | 8,653 | 10,864 | 6,249 | 4,512 | 0 / 0 / 0 |
| 1p5inR | 3,059 | 2,706 | 2,605 | 0 | 0 / 0 / 0 |
| 33mm_angle | 4,797 | 4,140 | 3,824 | 12 | 0 / 0 / 0 |

Other polygons are boundary/cut-cell n-gons. Camera Euler characteristic is
46, renderer area 65,681.9541, and signed volume 74,391.2083. Compared with the
previous report, camera polygon count increases 2.4%; this is not a blanket
polygon-reduction claim. One optimized tessellation run measured 9.098 seconds;
concurrent activity and differing geometry prevent a controlled speedup claim.

The fixed 4,096 OBJ-to-STEP samples have RMS 0.00288183 and maximum 0.0305139
source units (previous RMS 0.002934). STEP-to-OBJ has RMS 0.00289352 and maximum
0.0276449. Reverse samples depend on the generated mesh, so they are not an
identical before/after sample set. Neither direction is a Hausdorff certificate.

### Broader corpus limitations

The other STEP files were already unsupported in earlier reports and still
fail; current failure locations differ after the corrected planning:

- `camera_2.step`: imports 618 faces; tessellation reports a zero/nonfinite
  direction on face 48 (previously stopped at face 81's projection tolerance).
- `car1.step`: edge 93693 / curve 61161 endpoint residual 1.58559e-5 exceeds
  the source tolerance 1e-5, unchanged. No tolerance inflation was added.
- `car2.step`: imports 5,015 faces; face 153 reports touching/crossing trims
  (previously stopped earlier at adaptive-face budget checks).

The production OBJ importer loaded camera, camera_2, car1 and car2 successfully,
including car2's 5,578,454 polygons. Import success does not validate their STEP
counterparts or establish viewport performance for those larger models.

## Reproduction

From `luced-3d`, with the compatible local `LUCE_BASE` selected:

```sh
python3 tests/run.py --opt 2
python3 tests/run.py --opt 2 --backend c
python3 tools/cad_probe.py /Users/sedov/Desktop/camera.step --opt 2 --output /tmp/camera-check.obj
python3 tools/surface_delta.py /Users/sedov/Desktop/camera.step /Users/sedov/Desktop/camera.obj
python3 tools/preview.py --scene cad_wire --file /Users/sedov/Desktop/camera.step --background --opt 2 --rotation-x 0 --pitch -1.45 --yaw 0 --zoom .065 --target 20 -34 0 --output /tmp/camera-bottom.png
python3 tools/preview.py --scene cad_wire --file /Users/sedov/Desktop/camera.step --background --opt 2 --rotation-x 0 --pitch -.15 --yaw .3 --zoom .04 --target 47 -18 4 --output /tmp/camera-straight.png
python3 tools/preview.py --scene cad_wire --file /Users/sedov/Desktop/camera.step --background --opt 2 --rotation-x 0 --pitch -.2 --yaw .35 --zoom .075 --target 46 -27 0 --output /tmp/camera-lower.png
python3 tools/preview.py --scene cad_wire --file /Users/sedov/Desktop/camera.step --background --opt 2 --rotation-x 0 --pitch .2 --yaw .35 --zoom .08 --target 46 27 0 --output /tmp/camera-upper.png
luc build --release
```

Save work, relaunch the rebuilt local app, and force a fresh Tessellate cook
(for example, change divisions and restore it). A running process retains its
old executable and cached geometry. Nothing was published or automatically
closed/relaunched in the user's session.
