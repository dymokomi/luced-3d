# Collapsed cut ribbons — camera regression repaired

The goal remains active. This checkpoint repairs the patch-276 regression from
the [trim-predicate investigation](CAD_TRIM_PREDICATES_2026-09-28.md); it does not
claim that the camera's remaining spacing/fan defects or other STEP files are
fixed. The exact trim predicates and the File node's STEP tolerance setting
remain in place.

## Cause and change

A microscopic UV triangle lifted to three collinear physical vertices. Its
longest side bordered another collapsed ribbon, while a shorter side bordered
a healthy triangle. The cleanup's small-to-large area rule rejected the thin
neighbor and merged sideways into the healthy triangle. The resulting polygon
retraced part of its own physical boundary, so no consistently oriented display
triangulation could exist. This forced the entire patch into a fan-producing
fallback.

The pure Base CAD cleanup now detects collapsed physical ribbons and removes
only the internal chord spanning the entire ribbon. It can cross a chain of
collapsed cells before reaching a real cell. The ordinary one-eighth area rule
still applies to noncollapsed cells. No canonical point, trim segment, or point
identity is removed or moved. The numerical collinearity bound accounts for
binary64 coordinate subtraction, is capped relative to cell length, and is not
a replacement for the File node's geometric fitting tolerance. Final support
normals, display conditioning, and deviation checks remain mandatory.

Lifted display repair now recognizes ill-conditioned triangles as well as
reversed triangles, using the same per-triangle criterion as PolygonMesh. A
tiny positive normal dot product alone must not admit a degenerate display ear.

## Evidence

- All **32 test groups pass** with native opt-2 and C release.
- Internal CAD layout contracts also pass native opt-0 and opt-3.
- New synthetic cases exercise collapsed-cell chains with a smaller spanning
  neighbor across physical/chart scales, reversed winding, rotated/translated
  placement, and one-ULP physical perturbations. They preserve all six boundary
  vertices, keep the healthy triangle intact, and validate the final display.
- An isolated negative-control copy with spanning-chord selection disabled
  fails: `collapsed ribbon removed a healthy triangle`.
- All **2,710 camera quality records are identical between native and C**,
  with zero fold flags. Only patch 276 differs from the preceding 08:57 app.
- Patch 276 is back on the clipped-grid path: **23 quads, 249 triangles,
  18 cut n-gons** (290 polygons), versus the regressed fallback's 499 polygons.
  The earlier verified patch had 294 clipped polygons.
- Full camera: **671,178 points; 624,865 polygons** (585,611 quads, 3,453
  triangles, 35,801 other polygons). Zero open, nonmanifold, or inconsistently
  oriented edges; Euler characteristic 46. Retained-display area
  65,662.53548709619; volume 74,393.22694267749. These agree with the preceding
  clipped-grid checkpoint to numerical roundoff.
- One full cook took 9.90 seconds; this is not a controlled speed comparison.

The [large native shaded-wire close-up](preview_camera276_collapsed_ribbon.png)
uses the same camera as the [regressed view](preview_camera276_predicate_regression.png).
It isolates patch 276 **after full assembly cooking**, not before. The large
fan wedges across the strip are gone. Narrow boundary cells remain; the image
is not evidence that every trim on the model is pristine. The final exported
geometry is byte-identical to the captured version, excluding the timing header.

Local evidence:

- `/private/tmp/collapsed-ribbon-{native,c}.log`
- `/private/tmp/camera-ribbon-final-{native,c}.txt`
- `/private/tmp/camera-ribbon-final.obj`
- `/private/tmp/camera-ribbon-final-topology.log`
- `/private/tmp/camera276-spanmerge-preview.log`
- `/private/tmp/cad-ribbon-negative.hK8eAU/` (isolated negative control)

## Application checkpoint and remaining corpus work

`build/Luced 3D.app` was rebuilt at **09:59:05 PDT** with released Luce 0.8.18
and passed the native `--smoke` check (exit 0). Build/smoke logs are
`/private/tmp/ribbon-app-{build,smoke}.log`. This replaces the earlier hold on
the 08:57 application. No new package release has been published for this change.

The fresh corpus run still meshes `sign`, `1p5inR`, and `33mm_angle` with
6,841 / 2,645 / 3,888 polygons. `camera_2` still fails face 81 at the file's
0.01 tolerance (projection residual 0.0102655). `car1` still rejects endpoint
residual 1.58559e-5 at its file tolerance 1e-5. These are not silently relaxed;
the per-File STEP override remains available. Its separate repeated-assembly
limitation also remains unresolved. The current run is recorded in
`/private/tmp/collapsed-ribbon-corpus.log`. `car2` imports all 5,015 faces but
still fails assembled face 720 with `polygon has degenerate area`. The next
construction/refinement investigation must retain the new exact predicates
and their close-boundary tests, not revert to false trim-contact rejection.
