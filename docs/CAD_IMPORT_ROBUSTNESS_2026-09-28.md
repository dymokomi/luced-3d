# Morning import/tessellation checkpoint

This is a verified incremental checkpoint, not completion of the camera's
remaining quad-flow work or a claim of general STEP support. Desktop inputs
remain read-only; no reference OBJ supplies generated geometry.

## Per-File STEP tolerance

The File inspector shows `STEP tolerance / 0 = file` only for `.step`/`.stp`
(case-insensitive). Zero uses declared length uncertainty, with `1e-6` only as
the undeclared fallback. A positive value replaces it, including when stricter
than the file. Supported override range is `1e-9..1`, in source coordinate units.
Multiple declared contexts still use their maximum; context-scoped units and
automatic unit conversion remain unsupported.

The option flows through `Step.load_model`/`decode_model` into the CAD model's
boundary-agreement and projection tolerance. It is separate from Tessellate's
divisions and target edge length. Projects, undo/redo, cache recipes and the
actual background worker retain it. Changing file extension hides irrelevant
controls without losing the saved STEP value. Numerical fields support nine
decimal places so small tolerances are not rounded to zero.

[Native File inspector capture](preview_file_step_tolerance.png), 4400 × 2604
actual pixels. API and probe documentation describe the same source-unit rule.

## Engine fixes

1. Rational surface normals no longer depend on model, knot or homogeneous
   weight scale. Derivatives accumulate relative to a local control point;
   tangent magnitudes are normalized before their cross product. Genuine
   singular derivatives return zero for the CAD pole handler. This removes
   `camera_2`'s face-48 direction-normalization failure without changing the
   original camera's reported patch statistics.
2. Failed four-sided, repeated-seam NURBS maps now get a seam-aware cut-chart
   fallback before shared cuts freeze. A real-mesher preflight preserves
   successful maps and their row phases. An earlier unrestricted fallback
   experiment changed original-camera patches 715/717; it was not retained.
   `car2`'s tire patch 153 now meshes (isolated: 16,702 points, 16,384 polygons).
3. Small spherical trims can use a rotated local chart around an authored
   longitude pole. Boundary positions and IDs stay unchanged. The chart must
   fit a single hemisphere; genuinely unsupported multi-chart regions fail.
   Rotation is selected before meshing trims that touch a pole, not only after
   ear clipping fails: a numerically simple UV polygon can otherwise lift to
   inverted triangles. Successful non-polar charts keep their original path.

The sphere fix makes isolated `car2` face 720 mesh (381 points, 688 polygons),
but **its full assembled cook still fails at face 720** with crossing/touching
trims. Dense shared-edge cuts expose an additional issue; the isolated result
does not establish full-model correctness.

## Validation

- Full editor suite: 31 PASS groups on native opt-2 and C release, including
  real background computation and existing CAD/project/UI behavior.
- Normal contracts: 1,080 regular rational evaluations across model/knot/weight
  scales and translations, plus 36 collapsed-edge/near-pole evaluations.
- Closed-band contracts: 64 rational-quadratic/polynomial-cubic variants,
  both parameter orders, four loop starts, winding reversals and two sizes.
  Tests check open rails versus stitched meridians and every display normal.
- Spherical trim contracts: 12 rotated, scaled, reversed octants/all loop
  starts; support radius, area, boundary ownership and every display normal.
- NumberField module: two tests on native and C, now included in its CI runner.
- CAD internal contracts also pass native opt-0 and opt-3.
- Original camera: all 2,710 patch/quality records match the 06:50 checkpoint
  at printed precision; 631,302 polygons. This comparison does not certify
  that its known crowded trims and skewed quads are aesthetically resolved.
  Current native and C-release records also match each other exactly at that
  precision (excluding elapsed time).

[Tire seam and adjacent patches](preview_car2_tire_seam.png) is an actual
4400 × 2604 neutral shaded-wireframe capture. The tire now loads and renders,
but is too dense to call finished. The background capture prepared it in
16.4 seconds with 926 live UI frames; that is preparation time, **not FPS or a
whole-car benchmark**. The synchronous capture timed out at 180 seconds while
repeatedly preparing intermediate graphs; that diagnostic is not hidden.

## Unresolved work, in addition to camera quad distribution

| Model | Current failure |
|---|---|
| `camera_2.step`, source tolerance 0.01 | Face 81 projection residual 0.0102655 exceeds tolerance |
| `camera_2.step`, explicit tolerance 0.02 | Full cook reaches face 95, collapsed/self-intersecting polygon; isolated preview succeeds |
| `car1.step`, source tolerance 1e-5 | Edge #93693 spline endpoint residual 1.58559e-5 |
| `car1.step`, explicit tolerance 1e-4 | Repeated assembly occurrences need instanced CAD support |
| `car2.step`, source tolerance 1e-5 | Full cook advances from face 153 to face 720 trim crossing/touching |

Do not silently inflate tolerance, discard failing faces, flatten repeated
occurrences into one placement, or label partial previews full-file support.
Next diagnostics should compare assembled versus isolated boundary station
lists around face 720 and camera_2 face 95, then preserve the actual shared trim
while correcting chart/predicate/conformity failures. Original-camera hard
trim termination, button rims, first interior gaps and flow density remain open.

The design separation is consistent with OCCT's documented boundary model,
per-surface range splitters and independent face-meshing stages. These Luce
Base fixes are original implementations, not a port of OCCT's triangulator.
See [OCCT meshing architecture](https://github.com/Open-Cascade-SAS/OCCT/wiki/mesh)
and [STEP tolerance management](https://github.com/Open-Cascade-SAS/OCCT/blob/master/dox/user_guides/step/step.md).

Local changes are not yet a registry release. Rebuild/smoke and final probe
artifacts are in `/private/tmp/import-robustness-*`,
`/private/tmp/camera-import-robustness-*` and `/private/tmp/car2-pole-guard-final.log`.
The main `build/Luced 3D.app` was rebuilt at 07:55:23 PDT and passed native
`--smoke` (exit 0). The final native/C full suites each report 31 PASS groups,
including the source-uncertainty-below-default regression.
