# CAD tessellation: current implementation and next stages

**Latest:** [quad flow, normals and reviewed captures](CAD_MAPPED_PATCHES_2026-09-27.md)
supersedes the tessellation/normal results below. The
[large-file engine audit](ENGINE_AUDIT_2026-09-27.md) supersedes the
camera counts/performance below and records the new camera/car failures. It
includes measured surface deltas, bounded adaptive refinement and GPU retention.

## Verified external parts

### Hierarchy, narrow patches and display-cache follow-up

The current 16-division camera audit produces 343,055 points and 527,473 faces
(158,545 quads), with zero boundary, non-manifold or inconsistently oriented
edges. A local optimized CPU probe took 12.39 seconds for tessellation alone. This
supersedes the earlier counts below: narrow NURBS/analytic UV axes now have
independent sample spacing instead of inheriting the long axis's spacing.
The additional geometry is a quality tradeoff, not a claimed speedup. This is
still not certified chord-error control or a finished all-quad mesher; dense
boundary-to-interior transitions and planar triangle fans need further work.

Models with at least 16 faces dispatch face meshing to four native workers.
Each owns scratch/ARC temporaries; shared edge samples are immutable, and
results merge in source-face order. Progress/cancellation callbacks stay on
the calling compute thread. This preserves shared edge IDs and deterministic
primitive attributes while leaving the UI thread free.

CAD patch boundaries have their own display batch and remain visible in flat
and shaded preview. Display-mode changes no longer submit the DAG or clone
meshes to remove normals. Smooth/flat colors and line endpoints are cached
independently of the mode. Regression tests assert unchanged compute generation
when cycling through all five display modes.

The relevant Blender mechanisms are its
[mesh batch cache](https://github.com/blender/blender/blob/main/source/blender/draw/intern/draw_cache_impl_mesh.cc)
and separate
[wireframe overlay pass](https://github.com/blender/blender/blob/main/source/blender/draw/engines/overlay/overlay_wireframe.hh):
retain geometry buffers, request surface/line batches independently, and
invalidate only their dependencies. No Blender implementation was copied.
Our renderer still projects expanded vertices and uploads them per frame;
retained GPU vertex/index buffers plus camera uniforms and GPU-expanded lines
remain necessary work before claiming Blender-like performance. No shared
luce-ui or luce-gpu API changes were made in this follow-up.

STEP assembly paths and Blast are documented in [GROUPS.md](GROUPS.md).

### Camera import and analytic viewport preview

`camera.step` now opens through File: all 111,374 entities, 2,710 analytic
faces and 6,811 shared edges are read, with its six RGB styles and composed rigid
assembly placements. All patches complete the viewport's preview policy with
zero failed patches. The native Metal result and simplified File inspector are
shown in `preview_camera.png`. No OBJ data was used for import or preview.

CAD output is now visible without a Tessellate node. `CadModel.preview_face`
produces disposable per-patch display meshes; `GeometryData` caches them in a
separate `CadPreview`. It batches polygons for submission and draws each shared
analytic boundary once. Camera motion does not remesh; analytic Transform can
reuse a transformed preview cache. Normals guides show one sample per CAD patch
instead of flooding the viewport with internal display-mesh normals.

Preview uses 8 divisions, 4 for faces with many edge uses, with bounded 4/16
fallbacks when a particular discretization fails. This is display approximation,
not an export-quality or watertight conversion contract. The explicit Tessellate
node remains the only CAD-to-polygon DAG conversion. The complete camera now
converts at 16 divisions: 197,774 points, 282,169 faces (113,287 quads), with zero
boundary, non-manifold or inconsistently oriented edges in the topology audit.
The unoptimized CPU probe took 18.72 seconds; application computation runs on a
worker and publishes an immutable result. Native viewport capture is verified in
`preview_camera_tessellated.png`. This audit is not a CAD chord-error guarantee.

The camera exposed and now tests: 76-control-point curves, a 39-loop face,
elliptical arcs, spherical caps, toroidal patches, analytic periodic UV trims,
coincident loop junctions, and hole-order-independent bridging. Only exact
coincident junctions are canonicalized; unrelated nearby vertices are not welded.
Planar trimming projects tolerance-accepted samples onto the support plane for
triangulation while preserving original shared boundary positions in the mesh.

Runtime algorithms remain original Luce Base. Rigid assembly placement follows
target-frame × inverse(source-frame), composed through parent representations.
The unique-occurrence subset rejects repeated occurrences and mapped instances.
[OCCT STEP assembly mapping](https://github.com/Open-Cascade-SAS/OCCT/blob/master/dox/user_guides/step/step.md)
Analytic torus evaluation follows its standard two-angle parameterization.
[OCCT toroidal surface reference](https://dev.opencascade.org/doc/occt-7.9.0/refman/html/class_geom___toroidal_surface.html)

The File inspector now keeps name, path, Browse/Reload, geometry counts and actual
import errors. Redundant instructions and node-state controls were removed from
that inspector; graph flags/shortcuts remain available.

### September 27 follow-up: size refinement, normals and color

`sign.step` now completes at 16 divisions: 390 analytic faces, 986 shared edges,
8,353 mesh points, 4,583 quads and 7,600 triangles. There are zero open,
nonmanifold or inconsistently oriented edges; Euler characteristic -30 matches
the supplied OBJ. Relative volume difference is 0.002718%, area 0.000389%.
256-sample comparisons measured maximum distances 0.01463 (STEP mesh → OBJ)
and 0.02954 (OBJ → STEP mesh), not certified error bounds.

At target edge length 10, sign has 9,437 points, 5,341 quads and 8,252 triangles,
still watertight and consistently oriented. Native unoptimized tessellation
took about 0.89 seconds without size refinement and 1.12 seconds with it in
single local runs. See `preview_sign.png`.

At target edge length 5, `1p5inR.step` has 1,953 points, 1,515 quads and 876
triangles, with zero open/nonmanifold/inconsistent edges (about 116 ms).
Zero disables target-size refinement. Positive values specify desired source-unit
spacing, **not a minimum edge-length constraint** or guaranteed maximum. Small
trim features remain small; this is not a field-aligned all-quad mesher.

New support includes partial circular bands, U- or V-ruled patches, tolerance-
checked nonperiodic NURBS UV projection and metric-scaled interior UV grids.
Hole bridging checks the local visibility cone at repeated boundary vertices.
Opposing structured edges agree on counts; all adjacent faces reuse edge IDs.
STEP length uncertainty controls boundary agreement; automatic unit conversion
and mixed-unit assembly interpretation are still unsupported.

Tessellation emits primitive `cad_face`, optional primitive RGB `Cd`, and corner
`N`. STEP surface-fill styles can target solids/shells or individual faces;
explicit face styles override inherited colors. Normals average incident
polygon normals within each CAD face, preserving boundaries between CAD faces;
they are not exact analytic derivatives. Mesh transforms inverse-transpose `N`.
Geometry-changing edits invalidate stale normals and fall back to face normals.

`camera.step` contains 111,374 entities, 2,710 faces, 55 solids and six RGB styles
(also present in its MTL). The color chain is supported and covered by a portable
colored-cylinder fixture, including a face override and reflected transform.
At that earlier milestone the complete camera did not import; the follow-up
above resolves those import and preview failures. Its OBJ is
never silently substituted; OBJ MTL loading is not implemented in this change.
Sign at 4 divisions still exposes a trim triangulation failure; 16 is verified.

The viewport grouped square exposes five working display modes and normal
guides, with Rendered disabled. Wireframe is transparent line-only display;
wire overlays on filled modes use depth-tested constant-pixel lines. Flat
ignores `N`; Shaded consumes it. These modeling views are informed by Blender's
Wireframe/Solid workflow, not claims of Material Preview or path tracing.
[Blender viewport shading](https://docs.blender.org/manual/en/5.1/editors/3dview/display/shading.html)

Camera clip planes follow orbit distance to retain depth precision for large
CAD parts; zoom no longer snaps to the old 150-unit cap after framing a part.

STEP geometry and presentation are separate data paths; OCCT similarly exposes
shape-associated colors through its extended STEP translator. Our reader is
an original Base implementation, not an OCCT binding.
[OCCT STEP guide](https://github.com/Open-Cascade-SAS/OCCT/blob/master/dox/user_guides/step/step.md)

### Original part baseline

Tested against the user-provided `1p5inR.step`, with `1p5inR.obj` used only
as an independent comparison mesh. Neither Desktop file was modified.
Geometry is generated from STEP entities, not from the OBJ.

The STEP contains 22 faces: 14 planes, six ruled B-spline surfaces, one cylinder
and one cone, with 59 shared edges. Two planar faces contain holes.

| Divisions | Points | Quads | Triangles | Open / nonmanifold / inconsistent edges |
| --- | ---: | ---: | ---: | --- |
| 16 | 984 | 566 | 836 | 0 / 0 / 0 |
| 64 | 3,864 | 2,063 | 3,602 | 0 / 0 / 0 |

Both meshes have Euler characteristic zero, consistent with the part's
through-hole. Bounds match the OBJ within its decimal precision.
At 64 divisions the volume differs from the OBJ by 0.00815%, and surface area
by 0.00258%. A deterministic 256-sample test in each direction (vertices and
triangle interiors) measured maximum distances of 0.00476 and 0.00707 source
units. This is **not a Hausdorff bound**, a certified chord-error bound, or proof
that every STEP file works. The reference OBJ is itself a tessellation.

The actual File → Tessellate → Transform pipeline was rendered in the native
Metal viewport; see `preview_cad.png` and `preview_cad_wire.png`.
File continues to retain analytic CAD. Transform remains separate.

## Ownership and algorithms

- `luce-step/document.lucb`: bounded Part 21 scanner and entity lookup.
- `luce-step/brep_reader.lucb`: placements, rational curve/surface data,
  vertex/edge identity, oriented uses and face bounds.
- `luce-cad/brep*.lucb`: format-independent owned topology, support validation,
  one discretization per shared edge, and surface-specific face meshing.
- `luce-tesselator`: rational evaluation, planar trim triangulation and
  conservative quad recombination.
- `luce-3d`: indexed polygon mesh and rendering; quads remain polygons even
  though rasterization uses triangles.

All runtime implementation is original Luce Base. Python files are development
inspection/audit tools only. No OpenCASCADE, Gmsh, Blender or other donor runtime
was linked or copied into the product.

Shared boundaries use **identical point IDs**, not independent point samples
followed by approximate welding. Closed periodic seams also share IDs. This
automatically stitches already-connected CAD topology, but does not heal
disconnected or defective source shells.

Structured ruled NURBS are accepted only after checking the control net is affine in U or V and
the sampled boundary agrees with the support surface. Circular bands likewise
validate the analytic radius, axial location and angular correspondence.
Planes use validated, non-touching loops; visible bridges and ear clipping
preserve every boundary sample. Up to 128 sweeps of interior edge flips improve
the diagonals using a floating-point incircle test; this bounded optimizer does
not claim exact predicates or guaranteed Delaunay convergence. Quad recombination uses greedy quality-ranked
matching: convexity, corner angles 20–160 degrees, edge ratio at most 10.
It does not claim to implement Blossom or field-aligned quadrangulation.

## Performance investigation

Dense, unoptimized native probes initially took roughly 2.4–3.5 seconds. Per-face
and per-stage instrumentation identified planar intersection checks and hole
bridge searches as the dominant work, not rendering or NURBS evaluation.
Conservative bounding-box rejection, avoiding duplicate intersection checks,
nearest-first visible-bridge candidates, and a persistent ear-search cursor
reduced an observed 64-division run to **133 ms**; 16 divisions took **18 ms**.
With the subsequent interior-diagonal quality pass enabled, final measurements
were **263 ms** at 64 divisions and **49 ms** at 16 divisions.
These are single local measurements, not hardware-independent guarantees.
Temporary instrumentation was removed. No shared UI/GPU changes were needed.

## Research and design consequences

CGAL distinguishes constrained Delaunay triangulation from unconstrained
Delaunay and documents the role of visibility and exact/filtered predicates.
Our interior edge flips never exchange boundary edges; production-strength
predicate robustness and adaptive interior point insertion are still needed.
[CGAL triangulation manual](https://doc.cgal.org/latest/Triangulation_2/index.html)

OCCT's meshing design separates shared-edge discretization, consistency repair,
face meshing and postprocessing. Its face algorithms consume the previously
computed boundary polygons; deflection and angle are distinct controls. This
supports making edge sampling a CAD-wide responsibility instead of having
every surface independently invent its boundary.
[OCCT meshing documentation](https://github.com/Open-Cascade-SAS/OCCT/wiki/mesh)

Gmsh's quadrilateral tutorial describes Blossom matching and notes that
recombination can leave triangles to avoid poor quads. Our conservative local
pairing is a smaller algorithm, not an implementation of that paper.
The relevant next step is better constrained triangulation and quality
optimization, not forcing a four-corner label onto invalid polygons.
[Gmsh tutorial 11](https://gmsh.info/doc/texinfo/#t11)

Wei and Wei's trimmed-NURBS reconstruction pipeline starts from tessellation and
repair, then uses boundary-constrained quad meshing, patch extraction and spline
fitting. Their plate-with-a-hole example highlights boundary drift when
constraints are omitted. Reparameterizing a CAD model into an all-quad patch
layout is substantially different from faithfully displaying its existing
trimmed faces. A future remesh node should expose that approximation explicitly.
[Scalable Field-Aligned Reparameterization for Trimmed NURBS](https://arxiv.org/html/2410.14318v1)

The quasi-structured Gmsh work is also relevant to a later global quad layout
pipeline; its abstract was reviewed, not its full algorithm implementation.
[Reberol, Georgiadis and Remacle](https://arxiv.org/abs/2103.04652)

## Explicit remaining coverage

The two earlier whole-mesh fixtures and the camera conversion above are verified; this is
**not full STEP/CAD support**.
Current hard limits include 16 MiB / 262,144 STEP entities, 32,768 topological
vertices/edges, 8,192 B-rep surfaces/faces, 64 trim loops, 16,384 planar boundary samples,
and dynamically grown polygon storage capped at 2,097,152 points/faces and
8,388,608 corners. GPU frame budgets remain separate from modeling budgets.

Priority next stages:

1. Adaptive, knot-aware edge subdivision with measured chord/angular error,
   compatible counts for structured patches, and per-model tolerance/units.
2. Analytic surface derivatives and more robust UV inversion, STEP p-curves/surface curves,
   periodic UV unwrapping, constrained UV triangulation and interior refinement.
   Extend current trimmed NURBS, sphere and torus coverage to arbitrary periodic
   trims and singular configurations.
3. Explicit shell/solid topology, repeated assembly instances, units, oriented shells,
   and spline subintervals. Unsupported types must continue to fail, not vanish.
4. Tolerance-aware sewing of disconnected boundary edges with diagnostics,
   protected feature boundaries and ambiguity handling. Never indiscriminately
   weld every nearby vertex, which can destroy thin features.
5. Quality-driven quad layouts with sharp-feature constraints, singularity
   handling and projection/error checks, as a distinct optional remeshing stage.

## Reproduce

From `luced-3d`:

```sh
python3 tests/run.py
python3 tools/inspect_step.py /Users/sedov/Desktop/1p5inR.step
python3 tools/cad_probe.py /Users/sedov/Desktop/1p5inR.step --reference /Users/sedov/Desktop/1p5inR.obj --divisions 64
python3 tools/preview.py --scene cad_wire --file /Users/sedov/Desktop/1p5inR.step
luc build
```

The external probe is opt-in: the portable regression suite does not depend on
the user's Desktop. Portable tests cover holes, invalid crossing loops, quad
pairing, rational curves, periodic seams, shared-edge manifoldness, analytic
reflection and a synthetic STEP cylinder.
