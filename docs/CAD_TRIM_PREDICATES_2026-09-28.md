# Trim predicate investigation — not an app release

Historical investigation: its patch-276 regression is repaired by the later
[collapsed-ribbon checkpoint](CAD_COLLAPSED_RIBBONS_2026-09-28.md). The text below
records the evidence and hold decision at the time of this investigation.

The ongoing goal remains active. This is a tested local numerical-robustness
change with an unresolved camera mesh-quality regression. **Do not replace the
08:57:06 PDT app checkpoint or publish these experiments as a quality release.**
The remaining files are not fixed, and the camera is not pristine.

## Established causes and retained changes

The assembled `car2.step` face 720 initially failed a false trim contact.
Two distinct nearby boundary samples were classified as touching by a
whole-domain epsilon. Replacing only that intersection test exposed another
epsilon-dependent failure in ear membership; replacing that reached adaptive
refinement, which then rejected an ill-conditioned triangle.

`luce-tesselator/trim_predicates.lucb` now separates topological decisions from
geometric fitting tolerance. Dominant-plane segment intersection, ear
membership, orientation and ray crossing use filtered binary64 signs, with
bounded TwoDiff/TwoSum/FMA expansion arithmetic for ambiguous orientations.
All bounding boxes use the same projection as their predicates. Close points
remain distinct; true crossings and touches remain invalid. Ears still have to
meet the polygon engine's local conditioning contract. This is not arbitrary
precision for unbounded/subnormal inputs and is not a new surface-deviation
certificate.

The numerical design follows the predicate-versus-construction distinction
described by [Shewchuk](https://www.cs.cmu.edu/~quake/robust.html) and
[CGAL's kernel documentation](https://doc.cgal.org/latest/Kernel_23/index.html).
The implementation is pure Luce Base, not a wrapper or imported C parser.
The File node's existing STEP import-tolerance override is unchanged: numerical
topology signs must not be controlled by a user-selected fitting distance.

`luce-3d` now conditions each supplied display triangle against its own extent,
not the extent of its containing polygon. A valid small triangle must not become
invalid merely because an adjacent polygon is dissolved into the same face.
Zero-area, repeated-index and invalid-boundary checks remain mandatory.

A bounded edge-only triangle subdivision alternative is retained in CAD for
cases where a centre fan would fail the conditioning check. All proposed lifted
children must agree with support normals. Ordinary valid centre refinement is
unchanged. Pure support-normal evaluation is separated from inverse projection
to avoid a module dependency cycle.

## Experiments rejected, not hidden

Applying edge-only subdivision generally got the full car past face 720 to
face 1019, and removed some refinement-budget failures. However, both native
and C tests found folded triangles in a synthetic spherical fillet. That broad
policy is **not retained**. The narrower retained policy passes that regression
but the current assembled car still fails face 720 with `polygon has degenerate
area`. Getting to face 1019 in the rejected experiment is not a car2 fix.

Area-prioritized ear orders and optional cut-cell cleanup rollback did not
restore the affected camera patch. A mean-area ear policy even produced 33
fold flags on that patch. Those experiments and all temporary tracing were
removed. No tolerance was increased, boundary point dropped, OBJ substituted,
or wire edge hidden to make a model appear to pass.

## Validation and camera regression

The retained code passes **32 application groups on native opt-2 and C release**.
The additional private tests cover exact-rational orientation oracles, cyclic
permutations, three projection axes, reversed normals, three binary scales,
near-but-disjoint segments, real intersections, ear membership and ray parity.
End-to-end coverage includes 144 close-boundary domains, 18 close disjoint
holes and 36 crossing/touching rejections. An isolated copy using the old trim
implementation fails these tests with `trim loops cross or touch`.

There are 84 triangle split-mask tests across scale, winding and aspect ratio,
plus three cases where a centre fan is invalid but shared-edge subdivision is
conditioned. Six small-triangle polygon-union tests preserve exact display
indices; the full 3D Base tests pass native opt-2 and C release, including
allocation-failure cleanup.
The internal CAD layout contracts also pass native opt-0 and opt-3.

The full 2,710-face camera still meshes with zero open, nonmanifold or
inconsistently oriented edges and Euler characteristic 46. It has 671,201 points
and 625,074 polygons: 585,629 quads, 3,662 triangles and 35,783 other polygons.
Retained-display area is 65,662.5220538525 and volume 74,393.03906684446.
One measured cook took 9.49 seconds; this is not a controlled performance claim.
All 2,710 printed quality records agree between native and C, with zero fold
flags. Compared with the previous app checkpoint, only record 276 changes.

Patch 276 regresses from 294 clipped polygons to 499 constrained polygons
(41 quads and 458 triangles). Its quad-only shape metrics improve, but that
does **not** mean the mesh is cleaner: the large native shaded-wire
[diagnostic close-up](preview_camera276_predicate_regression.png) clearly shows
fans. The image is taken after the full cook, with only this patch isolated.
The old and new diagnostic camera views are not an exact matched-view pair.
This quality regression is why the installed app and registry were not updated.

The changed ear choices also expose how sensitive clipped-cell repair is to
its initial triangulation. Restore a robust boundary-terminating solution for
276 without reintroducing false-contact predicates, then revisit car2's
ill-conditioned constraints/refinement. Valid synthetic predicates alone do
not certify the full CAD construction pipeline.

## Other files and evidence

`sign`, `1p5inR` and `33mm_angle` still import and mesh with 6,841 / 2,645 / 3,888
polygons. `camera_2` still fails face 81 at source tolerance 0.01 with residual
0.0102655. `car1` still rejects endpoint residual 1.58559e-5 at source tolerance
1e-5; its separate repeated-instance limitation is not addressed here.

Local evidence:

- `/private/tmp/predicate-conditioned-final-{native,c}.log`
- `/private/tmp/camera-predicate-conditioned{.obj,-topology.log}`
- `/private/tmp/camera-predicate-final-c.txt`
- `/private/tmp/camera-predicate-conditioned-native.txt`
- `/private/tmp/car2-conditioned-refinement.log` (current failure)
- `/private/tmp/car2-red-green-trial.log` (rejected broad-policy experiment)
- `/private/tmp/predicate-refinement-corpus.log` (broad-policy corpus trial;
  its car2 face-1019 result is superseded by the current failure above)
- `/private/tmp/camera276-predicates-detail{.png,.log}`

The last rebuilt application remains the 08:57:06 PDT checkpoint documented in
[the preceding report](CAD_ANALYTIC_BRANCHES_2026-09-28.md). No publication or
claim of camera completion was made for this investigation.
