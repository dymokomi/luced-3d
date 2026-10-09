# Code node: a wrangle for luced-3d

Research and design, 2026-10-08, revised twice the same day after the owner's answers (§9).
No code was changed for this document. It answers the owner's request: "the other node we
need to make is Code. This is like a wrangle node that executes code either once, or in
parallel per point, polygons etc. ... all that will be written in Luce (or luce base
whichever is better suited) ... It should be really fast as well just like Wrangle node in
Houdini", and the owner's later call: "luce-base is probably the right language as it's fast
and system language. Perfect for high speed geometry processing language."

## 1. Decision in one page

**Language.** It looks and works like VEX, but it is Luce Base: what `luce-base check`
accepts, restricted to a safe subset (§4.4). As in a Wrangle, the user writes only the body.
The node wraps it in generated code for its Run Over menu, and that code defines the element
and the node (§4.2). The one-liner from the request, as typed in a Code node running over
Points:

```luce
p.P[1] += math32.sin(p.P[0] * 4.0) * 0.1
```

What the node compiles (generated, never shown or edited):

```luce
import math32
from luce_kernel.lib import *
from luce_geocore.code import Point, Kernel

pub func point(p: Point*, k: const Kernel*):
    p.P[1] += math32.sin(p.P[0] * 4.0) * 0.1    # the user's text, line for line
```

Run Over picks the wrapper:
- Points: `p: Point*`.
- Primitives: `f: Prim*`.
- Vertices: `v: Vertex*`.
- Detail: `k: Kernel*` alone.
- Numbers: `n: i64` and `k`.

Errors point at the user's lines, not the wrapper's. Positions, normals and colors are `f32[4]` vectors, which Base
computes lane by lane with the ordinary operators (`p.P = p.P + p.N * 0.1`); other
attributes go through accessors named after their storage type (`p.f32("mass")`,
`p.set_f32("mass", 1.0)`); node parameters come from the `Kernel` value
(`k.f32("amount", 0.2)`) and are created as spare parameters automatically; `k.frame` and
`k.time` come from the timeline. Base's explicit `f32`/`f64`/`i32`/`i64` types are the
precision rule the owner asked for: every attribute computes as what it is stored as, and a
width change is a cast the user writes. Because the text is Base, the Luce TextMate grammar
luced already ships (`fileTypes: ["luc", "lucb"]`) highlights it, and the Base compiler's
own checker produces the diagnostics.

**Front end.** No second parser. `luce-kernel` imports the Base compiler's lexer, parser
and checker as library modules (the compiler is written in Base; its `front` and `sema`
modules become public modules of the `luce-base` package) and lowers the checker's typed
tree (`type_id` and `resolved` on every node) into a column program. §4.3 has the cost and
the request to the language session.

**Safety.** The subset excludes everything that can corrupt memory (pointers beyond the
API's parameter types, allocation, `---`, `extern`, `asm`, the `c` module, threads) at
check time, and turns every remaining trap the Base compiler would insert (bounds,
overflow, division by zero, failed `T(x)`, `assert`, `trap`) into an error that stops
the cook: the node errors out with the line and the element. The engine
itself cannot trap. §4.5.

**Engine.** A column (batch) interpreter written in Base in the new general package
`luce-kernel` (approved name). The lowered program is a flat instruction list whose every
instruction runs over a chunk of elements (a few thousand lanes) at a time; chunks run on
geocore's parallel pool. Houdini's VEX works the same way (bytecode, batched over elements),
so the speed league is the same. Native compilation per cook stays ruled out (§5.2): it
would put `luce-base`, `as` and `ld` on every user's machine, Base has no `dlopen`, and a
native trap ends the process. A native tier for frozen or published networks stays possible
later over the same column IR.

The deciding numbers, measured in this session on an Apple M4 Max (16 cores), 1M points, a
7-operation polynomial per point, one thread (scratch programs in
`/private/tmp/claude-501/-Users-sedov-Dev-luce-dev/26944722-c0bc-4a1f-9a03-297d52283e2a/scratchpad/code-node/`):

| Way of running the per-point program | Time, 1M points, 1 thread |
| --- | ---: |
| Native Base, fused loop (`luce-base build --native --release`) | 0.45–0.6 ms |
| Native Base, one pass per operation over whole 1M columns | 3.9 ms |
| **Column interpreter in Base, chunks of 4096 lanes, generic bytecode** | **5.4–6.0 ms** |
| Per-element bytecode interpreter in Base (one dispatch per op per point) | 16 ms |
| `luce run` (the Luce tree-walking interpreter) | 1,250 ms |

With `sinf` in the program the gap narrows (libm dominates: fused 2.5 ms, column passes
4.7 ms). On 10–14 worker threads the column interpreter lands at about 0.5–1 ms for the
snippet above on 1M points, before the cost of reading the mesh's columns and writing new
ones (a few ms, the same as every other node). A Houdini Point Wrangle on the same snippet
at 1M points takes on the order of 10–30 ms on comparable hardware (no authoritative SideFX
number exists; this is the common experience and the bar to beat). Compile latency: the
Base toolchain compiles a small module to a native executable in 0.14 s wall (plus `as` and
`ld`); the column interpreter lowers a checked snippet in well under a millisecond and is
the same binary on the three targets.

**Stages** (§8): 0 the Base front end as a library; 1 the node with points/prims/vertices/
detail, P/N/Cd and custom attributes, groups, parameters, math/vector/noise/random, errors
at the line, benchmarks; 2 the timeline; 3 geometry reads and the second input; 4 geometry
edits and the Edit step; 5 strings and arrays.

## 2. What a wrangle is (semantics to match)

Sources: SideFX "Attribute Wrangle" node reference
(https://www.sidefx.com/docs/houdini/nodes/sop/attribwrangle.html), "Using VEX expressions"
(https://www.sidefx.com/docs/houdini/vex/snippets.html), the VEX function index
(https://www.sidefx.com/docs/houdini/vex/functions/index.html) and the VEX language
reference (https://www.sidefx.com/docs/houdini/vex/lang.html).

### 2.1 Run Over

The snippet runs once per element of one domain:

| Houdini Run Over | Meaning | Base entry point | geocore domain (`core/attributes.lucb`) |
| --- | --- | --- | --- |
| Detail (only once) | one run; detail attributes bind | `detail(k: Kernel*)` | `Domain.detail` |
| Points | once per point, in parallel | `point(p: Point*, k: const Kernel*)` | `Domain.point` |
| Vertices | once per vertex (a polygon corner) | `vertex(v: Vertex*, k: const Kernel*)` | `Domain.corner` |
| Primitives | once per primitive (face) | `prim(f: Prim*, k: const Kernel*)` | `Domain.face` |
| Numbers | N runs, only detail attributes; the index is the element | `number(i: usize, k: const Kernel*)` | none; N lanes |

As in Houdini, a Run Over menu on the node chooses it, and the node generates the entry
function around the user's text (§1). The column above is the generated signature; the
user never types it. geocore has a domain Houdini lacks,
`Domain.edge`, and calls Houdini's vertex a corner; the API keeps Houdini's word `vertex`
because that is what users know, and an `edge` entry point is cheap later since groups
already support edges. `detail` takes a mutable `Kernel*` because detail attributes and
queued edits are written through it; the parallel entry points take it `const`.

**One element's code, every element in parallel.** In Points mode, the code is written for
a single point: `p` is "this point", exactly as `@P` is in a Point Wrangle. The node runs it
for every point (in the group) in parallel, Houdini's model. Each run sees the same input
geometry and writes only its own point's outputs, so the order and the thread count never
change the result (§2.2's read/write rule). The engine does not run one point at a time. It
runs each instruction of the snippet over a chunk of 4,096 points at once, on geocore's
thread pool, one chunk per worker (§4.7, §5.3). That is how Houdini runs VEX too, and it is
where the speed comes from. The user cannot tell the difference: for them, the code is one
point's.

### 2.2 Attribute bindings

Houdini binds attributes to variables with `@name` and type prefixes (`f@`, `v@`, `i@`,
`s@`, `3@`, `f[]@`); well-known names (`@P @N @Cd @uv @v @ptnum @numpt @primnum @numprim
@vtxnum @elemnum @Frame @Time`) need no prefix; writing an unknown name creates the
attribute ("If you write to a @attribute in the VEX code and the attribute does not exist,
Houdini will create it"); a second input's attribute is `@opinput1_P` or
`point(1, "P", index)`; `@group_name` reads and writes group membership.

The same facts in Base: the well-known names are typed fields of the element value (`p.P`,
`p.N`, `p.Cd`, `p.uv`, `p.v`, `p.ptnum`, `p.numpt`); other attributes go through accessors
named after their storage type (`p.f32("mass")`, `p.set_f32("mass", 1.0)`), which is what
Houdini's prefix does and what Base's explicit types need; the first `set_*` of a name that
does not exist creates the attribute with that storage type on the run-over domain;
`k.input(1).point(p.ptnum)` is `@opinput1_`; `p.in_group("left")` and
`p.set_group("left", true)` are `@group_left`.

Read/write rule ("three geometries: input, current, output"): bound reads see the input
geometry; bound writes are queued and land in the output after the snippet finishes;
`point()` reads never see what the snippet wrote; `setpointattrib()` writes override
`@foo =` writes. We keep exactly this rule, because it is what makes per-element parallelism
race-free: within one cook every lane reads the same immutable input columns and writes its
own slot of the output column. A read after a write in the same lane returns the written
value (that is a register, not geometry), which matches what a VEX user sees.

### 2.3 Groups and parameters

The node's Group and Group Type parameters restrict which elements run; the rest pass
through untouched. luced-3d already has this pair (text slot 0, value slot 15) and geocore
evaluates the expression into a bitmask (`luce-geocore/src/groups/evaluate.lucb`).

`ch("name")`, `chf`, `chi`, `chv`, `chs` read a parameter of the node; Houdini has a button
"Creates spare parameters for each unique call of ch()". Here `k.f32("amount", 0.2)`,
`k.i32("count", 4)`, `k.vec3("direction")`, `k.text("name")` are the same thing and the
parameters appear on every edit without a button (§7.1).

### 2.4 Editing geometry from parallel code

From the snippets page: "The geometry creation functions can run in parallel. All changes
are queued and applied after your VEX code has iterated over all existing geometry."
`addpoint()` returns the new point number at once so the snippet can `addvertex` to it, but
the point does not exist to other lanes; `removepoint()`/`removeprim()` are queued deletes;
`setpointattrib(0, "Cd", pt, value)` sets an attribute on any element, queued, and wins
over `@Cd =`. Houdini's own description of the batching (SideFX forum, "VEX SIMD GPU
Implementation", https://www.sidefx.com/forum/topic/43672): reads together, creation
together, attribute sets on new geometry together, deletes together; reads multi-threaded,
writes single-threaded. The Base spelling is `k.add_point(P)`, `k.remove_prim(f)`,
`k.set_point_f32(i, "mass", v)` on the `Kernel` value (§7.6).

### 2.5 Errors

Houdini reports compile errors with the line and column of the snippet and marks the node
red; runtime failures mostly do not exist (reading a missing attribute gives 0; bad indices
are ignored). We follow that for reads and go one step further for arithmetic: compile
errors are precise and shown at the line in the editor; a would-be trap at run time is a
an error on the node with its line and element (§4.5); the engine never traps.

## 3. The VEX function catalog against geocore

Status column: **have** (exists in geocore or luce-std and can be bound directly), **easy**
(a few lines over something that exists), **missing** (new code), and the stage that needs
it (S1–S5 from §8; "–" means not planned). Sources for what exists:
`luce-std/src/math.lucb`, `math32.lucb`, `random.lucb`; `luce-geocore/src/math/vector.lucb`
(`Vector3`, f64), `math/matrix.lucb` (`Matrix4`, affine), `core/hash.lucb` (`mix`),
`geometries/attribute_kernels.lucb:85` and `verbs/point_verbs.lucb:224` (sin-hash white
noise only), `geometries/triangle_index.lucb` (BVH: ray, nearest face, distance; no hit
position or uv), `geometries/point_hash.lucb` (uniform grid; `nearest` only),
`geometries/topology/connectivity.lucb` (`Topology`: next/previous/twin corner, valence;
point→faces, point→edges CSR tables), `fields/grid.lucb` (`GridSampler.sample`, trilinear),
`groups/*.lucb`, `verbs/builder.lucb` (`TopologyBuilder`), `geometries/polygon/subset.lucb`
(`kept_faces`, `compacted`). In the snippet these are functions of `luce_kernel.lib` (math
over vectors, noise, random, interpolation: general) and methods of `luce_geocore.code`
values (anything that reads or writes geometry); scalar math is luce-std's `math` (f64) and
`math32` (f32), imported as in any Base module.

### 3.1 Math, vectors, matrices, quaternions

| Functions (VEX names) | Status | Stage |
| --- | --- | --- |
| `abs sign floor ceil rint trunc frac sqrt cbrt exp log log10 pow sin cos tan asin acos atan atan2 sinh cosh tanh isnan isinf isfinite min max` | have (`math`, `math32`), bound as column ops in the operand's width | S1 |
| `+ - * /` on vectors, vector × scalar | have in the language (`f32[4]`, `f64[2]`, base.md §5.12) | S1 |
| `length length2 distance distance2 normalize dot cross avg sum` | have (`Vector3`, f64) → `lib.dot(a, b)`, `lib.cross`, `lib.length`, `lib.normalized` over `f32[4]` and `f64[4]` (two f64 vectors as registers) | S1 |
| `ident transpose determinant invert` for `Mat3`/`Mat4` | partly (`Matrix4.inverse`, `determinant`); need mat3 | S3 |
| `maketransform lookat dihedral rotate translate scale prerotate polardecomp` | missing; `Matrix4.compose` covers trs | S3 |
| `quaternion qmultiply qrotate qinvert slerp eulertoquaternion quaterniontoeuler` | missing (geocore has no quaternion type); `Quat` as `f32[4]` | S3 |
| `outerproduct diag makebasis solvecubic solvequadratic eigenvalues svddecomp` | missing | – |

### 3.2 Interpolation and fit

| Functions | Status | Stage |
| --- | --- | --- |
| `clamp lerp fit fit01 fit10 fit11 invlerp smooth efit` | easy (one column op each, scalar and vector) | S1 |
| `slerp slerpv` | with quaternions | S3 |
| `spline cspline lspline kspline ckspline` | missing | S4 |

### 3.3 Noise and random

| Functions | Status | Stage |
| --- | --- | --- |
| `rand(seed) random(ix) random_ihash random_fhash nrandom` | easy: hash-based, per-lane seeded (`core/hash.lucb` `mix`; luce-std `Random` for the detail case) | S1 |
| `noise snoise` (Perlin, signed/unsigned, 1D–4D in, float/vector out) | missing; improved Perlin (2002 gradients) in f32 and f64 columns | S1 |
| `xnoise` (simplex), `onoise`/`anoise` (fractal sums), `vnoise` (Voronoi/cell), `wnoise`/`mwnoise` (Worley), `curlnoise`/`curlxnoise`, `flownoise` | missing; fractal sums and curl are compositions of the base noises | S3 (fractal, simplex, curl), S4 (worley/voronoi, flow) |
| `noised xnoised` (noise with derivatives) | missing | S4 |
| `random_sobol random_brj sample_*` | missing | – |

Houdini's `noise()` returns unsigned noise centered on 0.5 and `snoise` the signed form;
`rand()` is a per-element hash of its seed; results must be bit-identical run to run and
across thread counts (§7.8). geocore's Mountain verb should move onto the same noise once it
exists (today white noise, `verbs/point_verbs.lucb:224`).

### 3.4 Geometry reads

| Functions | Base spelling | Status | Stage |
| --- | --- | --- | --- |
| `@attr` reads, `@opinput1_attr` | `p.P`, `p.f32("x")`, `k.input(1).point(p.ptnum).P` | have (columns in `AttributeStore`; positions `point_span()` + origin) | S1 (S3 for input 1) |
| `npoints nprimitives nvertices` | `p.numpt`, `k.input(0).numpt` | have (`access.lucb` counts) | S1 |
| `point(input, "attr", i) prim() vertex() detail()`, `hasattrib`, `attribtype` | `k.input(0).point(i).f32("x")`, `k.detail_f32("x")`, `p.has("x")` | have (typed column access, `find_attribute`) → gather ops | S3 (detail: S1) |
| `primpoints primpoint primvertexcount pointprims pointvertices vertexpoint vertexprim vertexnext vertexprev` | `f.points() -> const i32[]`, `p.prims()`, `v.point`, `v.prim`, `v.next()` | have (`offsets`, `corners`, `corner_faces`, `point_face_span`) | S3 |
| `neighbours neighbour neighbourcount` | `p.neighbours() -> const i32[]` | easy (walk `point_edge_span` + `edge_span`, as `cook_smooth` does) | S3 |
| `polyneighbours`, `hedge_*`, `pointedge pointhedge` | `k.input(0).hedge(...)` | have (`Topology.next/previous/twin`) → thin wrappers | S4 |
| `nearpoint nearpoints(input, P, radius[, max])`, `pcopen/pcfind/pcfilter/pcimport/pciterate` | `k.input(1).nearpoints(p.P, 0.5, 8) -> const i32[]` | **missing**: geocore has only a grid `nearest`; needs a k-nearest / radius query (the grid is fine: iterate cells, sort by distance) | S3 (nearpoints), S4 (pcfilter) |
| `xyzdist(input, P, &prim, &uv)`, `minpos`, `primuv`, `primduv`, `pointprimuv` | `let hit = k.input(1).closest(p.P)`; `hit.prim`, `hit.uv`, `hit.P`, `k.input(1).prim_vec3(hit.prim, hit.uv, "N")` | partly: BVH gives face+distance, not the closest point or uv; `fields/mesh_distance.lucb` `closest_feature` has the triangle maths | S3 |
| `intersect(input, orig, dir, &pos, &uv)`, `intersect_all` | `k.input(1).intersect(o, d)` | partly: `TriangleIndex.ray` returns face and distance; add hit position and uv | S3 |
| `getbbox getbbox_center getbbox_size relbbox getpointbbox` | `k.input(0).bounds()` | have (`Bounds`) | S1 |
| `volumesample volumegradient` | `k.input(1).sample(p.P)` | have (`GridSampler.sample`); gradient easy | S4 |
| `inpointgroup inprimgroup invertexgroup`, `@group_x` | `p.in_group("x")` | have (group bits) | S1 |
| `idtopoint nametopoint findattribval uniqueval nuniqueval` | `k.input(0).find_i32("id", 7)` | easy (hash index built once per cook) | S4 |
| `windingnumber surfacedist uvdist planepointdistance` | | missing | – |

### 3.5 Geometry writes

| Functions | Base spelling | Status | Stage |
| --- | --- | --- | --- |
| `@attr = v` (create if missing) | `p.P = v`, `p.set_f32("mass", 1.0)` | have the storage (`with_attribute_entry`, `typed_mut`); the engine writes output columns | S1 |
| `setpointgroup setprimgroup setvertexgroup`, `@group_x = 1` | `p.set_group("x", true)` | have (`with_group_bits`) | S1 |
| `setpointattrib setprimattrib setvertexattrib setdetailattrib` (any element, queued) | `k.set_point_f32(i, "mass", v)`, `k.set_detail_f32(...)` | easy over output columns with a per-thread write queue (§7.6) | S3 |
| `addpoint addprim addvertex removepoint removeprim removevertex` | `k.add_point(P) -> i32`, `k.add_prim(points: const i32[])`, `k.remove_point(i)` | have the bulk tools (`TopologyBuilder`, `MeshBuilder`, `kept_faces`, `compacted`); need the queue and the two-phase apply (§7.6) | S4 |
| `addattrib addpointattrib ...` (explicit create with defaults) | `k.add_point_f32("mass", 0.0)` | easy | S3 |
| `removeattrib removepointattrib ...` | `k.remove_point_attribute("x")` | easy (`without_attribute`) | S4 |
| `setprimvertex setvertexpoint`, `primintrinsic` | | missing | – |

### 3.6 Strings, arrays, color, measure, conversion

| Functions | Status | Stage |
| --- | --- | --- |
| `s@name` reads/writes, `sprintf`, `concat`, `strlen`, `startswith`, `find`, `tolower/toupper`, `itoa`, `atoi/atof`, `split`, `join`, `re_match`... | geocore stores strings as an index into a shared table (`DataType.text`): equality and group tests are cheap; building new strings needs per-lane buffers and interning (`luce-regex` exists for `re_*`); Base's `str` is a view, so the lowering gives each lane a bounded scratch buffer and `format` | S5 |
| arrays `f[]@`, `len append push pop sort reverse slice argsort find` | geocore has no per-element arrays (`attributes.lucb`); needs a ragged column type (offsets + values) in geocore first; Base spelling is a span `const f32[]` | S5 |
| `luminance hsvtorgb rgbtohsv blackbody ctransform` | partly in `luce-color` (all color maths lives there); `luce-kernel` must not depend on luce-color for a 3-line `luminance`; HSV is small enough to inline; `ctransform` binds luce-color from the app side | S3 |
| `degrees radians` | easy | S1 |
| `printf` (debug) | Base `print` and `format` → the node's console, detail or the first N lanes | S1 |

### 3.7 What a first version needs (S1)

Vector operators, `lib` vector functions, interpolation/fit, `rand`, Perlin
`noise`/`snoise`, `print`, bounds of the input, bound reads/writes of
f32/f64/i32/i64/vec2/vec3/vec4 attributes and groups, `ptnum numpt primnum numprim vtxnum`,
`k.frame`/`k.time` (0 until stage 2), `k.f32/i32/vec3("name", default)` parameters,
run-over by entry point. Everything in 3.4–3.6 beyond that is stage 3+.

## 4. The language

### 4.1 Options weighed

1. **Full Luce run by `luce run`.** The interpreter is a tree walker
   (`luce/src/hir/interp/interp.lucb`, "the semantic oracle"), refuses Base imports, runs
   workers sequentially (`luce/docs/luce.md:1045`) and measured 1.25 s for one pass of a
   7-op expression over 1M floats: 2,000× off the bar. Out of process (luced-2d's
   `script_host.luc`) adds a process, files and a line protocol per cook. Right for
   document-level scripts; wrong for per-element code.
2. **Luce or Base compiled natively per cook.** Near-C speed (fused loop 0.45 ms) but every
   cook that changes the code pays 0.14 s plus `as` and `ld`; `luce-base` produces assembly
   text and runs the system assembler and linker (`luce-base/src/main.lucb:614–747`); Base
   has no `dlopen` (`luce-js/src/host/native_modules.lucb:3–10`) and `--lib` makes only a
   static archive (`main.lucb:855–906`); a bug in user code would trap and a Base trap ends
   the process (`luce-std/src/parallel.lucb` header). It would also ship a compiler
   toolchain inside the luced-3d install on all three OSes.
3. **A Luce-syntax subset.** Luce has one `int` and one `float` (f64), no vector types and
   no operator overloading (`luce/docs/luce.md:467`), so vectors would be method calls
   (`p.P.add(p.N.scale(0.1))`) and widths would need an inference rule outside the language.
4. **A Base-syntax subset, checked by the Base compiler, lowered by us to a column
   program.** Base has `f32`/`f64`/`i32`/`i64`, spans and structs, and 8- and 16-byte
   vectors with lane-wise operators (`f32[4]`, base.md §5.12), so a snippet names storage
   types exactly and writes vector math with `+ - *`. Its unsafe half (pointers, allocation,
   `---`, `extern`, `asm`, threads) is a short, exhaustive list (§12.6 of base.md names both
   lists) that the lowering refuses at check time. What remains is the C-like core Houdini
   users already write in VEX. This is the pick (owner: "luce-base is probably the right
   language").

### 4.2 The API, in Base

Two API modules, written as ordinary `.lucb` files whose bodies are never executed (the
lowering recognizes their names; the stubs exist so the Base checker can type a snippet and
so hover docs come from the real declarations):

- `luce_kernel.lib` (general, shipped by luce-kernel): `dot cross length length2 normalized
  distance lerp fit fit01 clamp smooth` over `f32[4]`/`f32[2]`/`f64[2]` and scalars (Base
  has no overloading, so the f64 vector forms carry a `64` suffix: `dot64`);
  `rand(seed: i64) -> f32`, `rand3(seed: i64) -> f32[4]`; `noise(p: f32[4]) -> f32`,
  `snoise`, `noise2(p: f32[2])`, `vnoise3(p: f32[4]) -> f32[4]`, `noise64(p: f64[4])`
  (S1); `Mat3`, `Mat4`, `Quat` (S3); `degrees radians`.
- `luce_geocore.code` (geometry, shipped by luce-geocore): `Point`, `Vertex`, `Prim`,
  `Kernel`, `Geometry` (an input), `Hit`, `Bounds`.

```luce
## luce_geocore/code.lucb (excerpt of the stubs; bodies are never run)
pub struct Point:
    pub var P: f32[4]          # position, f32 storage, relative to the mesh origin; lane 3 is 0
    pub var N: f32[4]          # normal (0 when absent); writing creates it
    pub var Cd: f32[4]         # color; writing creates it
    pub var uv: f32[2]
    pub var v: f32[4]
    pub let ptnum: i32
    pub let numpt: i32
    pub func has(name: str) -> bool
    pub func f32(name: str) -> f32          # a compile error if the attribute is stored otherwise
    pub func f64(name: str) -> f64
    pub func i32(name: str) -> i32
    pub func i64(name: str) -> i64
    pub func vec2(name: str) -> f32[2]
    pub func vec3(name: str) -> f32[4]
    pub func vec4(name: str) -> f32[4]
    pub func text(name: str) -> str                         # S5
    pub func set_f32(name: str, value: f32)                 # creates a float32 attribute on first use
    pub func set_f64(name: str, value: f64)
    pub func set_i32(name: str, value: i32)
    pub func set_i64(name: str, value: i64)
    pub func set_vec2(name: str, value: f32[2])
    pub func set_vec3(name: str, value: f32[4])
    pub func set_vec4(name: str, value: f32[4])
    pub func in_group(name: str) -> bool
    pub func set_group(name: str, member: bool)
    pub func prims() -> const i32[]                         # S3
    pub func neighbours() -> const i32[]                    # S3

pub struct Kernel:
    pub let frame: f64         # timeline frame (stage 2); 0 before that
    pub let time: f64          # seconds
    pub let fps: f64
    pub func f32(name: str, default: f32 = 0.0) -> f32      # a spare parameter
    pub func f64(name: str, default: f64 = 0.0) -> f64
    pub func i32(name: str, default: i32 = 0) -> i32
    pub func vec3(name: str) -> f32[4]
    pub func text(name: str) -> str                         # S5
    pub func detail_f32(name: str) -> f32
    pub func set_detail_f32(name: str, value: f32)          # detail entry point only
    pub func input(index: usize) -> const Geometry*         # 0 is the node's own input
    pub func add_point(P: f32[4]) -> i32                    # S4, queued
    pub func remove_point(index: i32)                       # S4, queued
    pub func set_point_f32(index: i32, name: str, value: f32)   # S3, queued
```

Three snippets as users type them (bodies only; the wrapper of §1 defines `p`, `f` and `k`):

```luce
# Run Over Points: noise displacement along the normal, animated, two spare parameters.
let amount = k.f32("amount", 0.2)
let scale = k.f32("scale", 3.0)
let n = snoise(p.P * scale + [0.0, 0.0, (f32)k.time, 0.0])
p.P = p.P + p.N * (n * amount)
```

```luce
# Run Over Primitives: color by area and put the big ones in a group.
let big = f.area() > k.f32("threshold", 0.01)
f.Cd = [1.0, 0.2, 0.2, 0.0] if big else [0.2, 0.2, 1.0, 0.0]
f.set_group("big", big)
```

```luce
# Run Over Detail: one run; a reduction over the input, stored in float64.
let bounds = k.input(0).bounds()
k.set_detail_f64("height", (f64)bounds.size()[1])
```

The generated wrapper imports `math32` and all of `luce_kernel.lib` (VEX's functions are
there without imports), so the body calls `snoise`, `fit`, `rand` and the rest directly.
Helper functions, if the user wants them, go in the node's second text area (a "Header"
tab), which the wrapper places above the entry function.

Why `f32[4]` for three-component attributes: Base's vectors are 8 or 16 bytes, so `f32[3]`
is an array without lane operators while `f32[4]` has them (base.md §5.12: "`+`, `-`, `*`
... a vector and a scalar of its element type in either position"). Storage stays
`Float3` (12 bytes, `core/float3.lucb`); the engine binds lane 3 to a zero register and
drops it on store. In the column engine a vector is four column registers either way, so the
padding costs nothing at run time; it only shapes what the user types (`p.P[1]` is y; a
literal `[x, y, z, 0.0]`). `f32[2]` for `uv` is a vector already.

### 4.3 Reusing the Base front end

The Base compiler is written in Base (`luce-base/package.prisma`: `kind = "tool"`, no
`public` list): `src/front/` (lexer, parser, layout, AST, source; 5,284 lines),
`src/sema/` (types, standard modules, describe; 2,236 lines) and `src/sema/check/`
(declarations, bodies, expressions, operators, conversions, allocation, escape, ...; 8,366
lines, `extend Checker` blocks per concern). The checker writes what it learns onto the tree
(`src/front/ast.lucb:198–201`: `type_id` "and the declaration a name, call, or member
resolved to", `resolved`); the backends consume that tree. `luce-kernel` is a Base package,
so it imports those modules once `luce-base` names them public (`str[] public =
["front.ast", "front.parser", "front.source", "sema.types", "sema.check.module", ...]`;
`luce-pkg/src/package.lucb:80` defines `public` for every kind and nothing refuses a
dependency on a tool). What that costs and needs:

- A `public` list on `luce-base` and an embedding entry: `Checker.create`, `load`, the
  diagnostics sink and `check FILE` exist (`src/main.lucb`, `luce-base check FILE [--target
  NAME]`); what is missing is checking a module whose imports resolve against a root the
  host supplies. The snippet root is a scratch directory shipped with luced-3d: the two stub
  modules, luce-std's `math.lucb` and `math32.lucb` (small, MIT) or their `luce-base
  interface` outputs, and the snippet file; Base's standard modules (`memory`, `thread`,
  `c`, ...) are built into the checker and the lowering refuses them by name (§4.4). No
  toolchain beyond the embedded checker is involved; a later in-memory source provider
  removes the files.
- A documented walk over the typed tree for the lowering (node kinds, `type_id` meaning,
  `resolved` targets, how `extend` methods and implicit `self` appear). The C and native
  backends' lowering (`src/back/ir/`) is the model: the kernel's lowering is a third backend
  whose target is the column IR.
- Version coupling: `luce-kernel` follows the luce-base release it imports; snippets are
  Base of that version. That is the point: kernel syntax never drifts from the language.
- The language session owns `luce-base` (memory: route luce-base requests to LUCE_LANG).
  The request is small: the `public` list, a `check_root(root, entry) -> typed tree` entry,
  and the walk documented. Days, not weeks; the alternative (a second parser and checker for
  a Base subset) is 5,000+ lines that would drift.

Fallback if the library route stalls: run `luce-base check` as a subprocess for diagnostics
(available today) and parse the subset in `luce-kernel` for lowering. That ships but
duplicates and puts `luce-base` on the user's machine, so it is a fallback, not the plan.

### 4.4 The safe subset

The lowering walks the typed tree and accepts exactly these Base constructs; anything else
is a diagnostic at its line, "not available in a kernel", through the same channel as the
checker's own errors.

Accepted (lowered to columns):

- module-level `pub func` entry points (§2.1) and helper `func`s (inlined; recursion is a
  compile error), `import math32`, `import math`, `from luce_kernel.lib import ...`,
  `from luce_geocore.code import ...`, module-level `let` constants;
- `let`/`var` of `f32 f64 i32 i64 u32 u64 usize bool`, the vectors `f32[2] f32[4] f64[2]
  i32[4]`, fixed arrays of those up to 16 elements, the API structs by value (`Hit`,
  `Bounds`), spans the API returns (`const i32[]`, S3), `str` (S5);
- arithmetic (`+ - * / // %` and the `%`, `|`, `?` forms), comparisons, `and`/`or`/`not`,
  bit operators and shifts, casts `(T)x` and checked `T(x)`, `x if c else y`;
- `if`/`elif`/`else`, `while` with a per-lane iteration cap (1M) that makes a runaway loop
  a node error, `for i in a..<b`, `for x in span`, `match` on integers and enums with `_`,
  `break`/`continue`, `return`;
- method calls on API values; field reads and writes through the entry point's `Point*`,
  `Prim*`, `Vertex*`, `Kernel*` parameters and `const Geometry*` results, which are the
  only pointer-typed values a kernel ever holds (they are the API's parameter and result
  types, never formed by the snippet);
- `print` and `format` into a per-lane bounded buffer (the console);
- `assert` and `trap(message)` (node errors with the message, §4.5).

Excluded (compile error at the line):

- raw pointers in any form the snippet writes: `T*`, `const T*`, `void*`, `T*?` in a
  declaration, `&x`, `*p`, `(T*)` casts, pointer arithmetic (base.md §5.3, §6.6, §7.7);
- allocation and frames: `new`, `free`, `alloc`, `memory.*`, `with ... as allocator`,
  `memory.frame`, `---` uninitialised storage (§6.2, §12);
- the foreign world: `extern`, `export`, `asm`, the `c` module, `c.str`, handles (§8.9,
  §17);
- concurrency and effects: `thread`, atomic `@T`, `volatile`, `os`, `io`, `time`, files;
  `main`, `test`, `defer`/`errdefer`;
- types the columns cannot hold: `union`, interface views, closures, function values,
  generics, `str` building before S5, arrays over 16 elements, structs the snippet declares
  (S4 for plain-scalar structs);
- failure: `!` results, `try`, `catch`, `recover`, `error` (the API never fails; what could
  fail is a node error).

The list is checked against base.md §12.6's two lists: everything in the "undefined, as in
C" list needs a construct from the excluded set, so a kernel cannot reach undefined
behaviour; everything in the "defined and checked" list is a trap the engine turns into a
fault (§4.5).

### 4.5 Traps are errors on the node

The Base compiler inserts traps (base.md §11.5) for:
- out-of-bounds indexing;
- checked overflow;
- division by zero;
- shifting by the type's width or more;
- a failed `T(x)` conversion;
- `else trap`, `assert`, and `trap(...)` itself.

In the column engine each of these is an instruction with a mask result: the op computes
the condition for every lane (`index < length`, the overflow flag, `divisor != 0`, ...).
The first lane that fails stops the cook. As the owner decided, the node errors out and
shows why: "line 7: index out of bounds (point 1204)". That message is the node's failure,
red in the network as any cook error is, and a diagnostic at the line in the editor.
Nothing partial escapes: the output columns are written only when every chunk finished.
Chunks run in parallel, so when several fail the error reported is the lowest element's.
That keeps the message the same whatever the thread count.

The engine's own code never indexes outside a proven chunk bound and never allocates inside
a chunk, so the engine itself cannot trap; that promise is fuzzed (§5.3). Stack exhaustion
cannot happen: helper functions are inlined and recursion is refused.

Deviations from Base's own semantics, stated in the kernel reference: a trap is the node's
error, not the end of the program; `print` goes to the node's console, in element order,
capped. Everything else (literal typing: "context chooses the float type; absent context
the default is `f64`", base.md §4.3; strict storage; C's `//` and `%`; IEEE floats) is
Base's, because it is Base's checker that decides.

### 4.6 Precision: whatever the attribute is

Owner: "for speed they should be whatever they actually are." In Base this is not a rule
the kernel adds; it is the type system. A read carries its storage type: `p.P` is `f32[4]`
(positions, `Float3` storage), `p.f64("x")` is `f64`, `p.i32("id")` is `i32`, an `int8`
attribute reads as `i8`, a `boolean` as `bool`; asking for the wrong width
(`p.f32("x")` on a float64 attribute) is a lowering error naming the stored type, because
the lowering binds names against the input's attribute store (`find_attribute`,
`attribute_type`). Mixing widths needs the cast Base needs (`(f64)p.P[0] * k.f64("big")`);
literals take the width of their context; a store is exact because the setter's type is
the storage type. `k.frame` and `k.time` are `f64` (frames stay exact); `rand` and noise
come in f32 and f64 forms. Math runs in the operand width (`math32.sin` for f32, `math.sin`
for f64). Reductions for `detail` accumulate in f64. The mesh origin (f64,
`geometries/polygon/mesh.lucb`) is `k.input(0).origin() -> f64[4]` for the rare snippet
that needs world coordinates at full precision; most meshes have origin 0.

### 4.7 Why this maps to columns

Every value has one instance per lane. The lowering turns `let x = p.P[0] * 4.0` into
"column x = column P.x times scalar 4.0". A condition that depends on the element becomes a
mask: both branches run over the chunk and assigned variables are selected by the mask
(VEX and every SIMD language do this; the cost is the sum of both branches, fine for
snippets). A uniform condition (parameters, detail values, constants) is a real branch. A
loop with a uniform trip count is nested chunk passes; a per-lane trip count runs masked
until every lane has exited. A gather (`k.input(0).point(i).P` with per-lane `i`) is one
column op that reads a column at per-lane indices with bounds masking. Values that are the
same on every lane are scalars, broadcast only when an op needs them. A `f32[4]` is four
column registers; `v.sum()` is three adds.

## 5. The execution engine

### 5.1 What exists

- `luce` (0.14.0) and `luce-base` (0.39.0) are both tools written in Base, not libraries;
  `luce run` is a tree-walking interpreter, there is no bytecode VM and no JIT
  (`luce/src/main.lucb:517–531`, `luce/docs/DESIGN.md:35–45`); `luce-base` produces
  assembly text and runs the system `as` and `ld`/`cc` (`luce-base/src/main.lucb:614–747`).
  Native targets: arm64-macos, x86_64-linux, x86_64-windows only
  (`luce-base/src/back/target.lucb:94–110`). No encoder that could emit machine code into
  memory; no `MAP_JIT`/`PROT_EXEC` use.
- Base's native backend is near C on array kernels (`luce-base/docs/NATIVE-PERFORMANCE.md`:
  float array transformation 1.51× Clang `-O3`, integer sum 1.26×), auto-vectorizes counted
  loops over contiguous slices (`luce-base/src/back/opt/vectorize.lucb`) and has 128-bit
  vector types (`f32[4]`, base.md §5.12: lane-wise `+ - * /`, `mul_add`, `sum/min/max`;
  no lane-wise compare yet).
- `luce-js` (QuickJS in Base, 70k lines) proves an interpreter in Base: `match` over a dense
  `u8` opcode is a jump table since Luce 0.8.12; `memory.frame` gives bounded alloca; it
  runs at 1.1–8× C QuickJS, geometric mean 2.86 (`luce-js/docs/PERFORMANCE.md:75–76`).
- geocore has a persistent pool (`luce-geocore/src/core/parallel.lucb`: `parallel_for(count,
  grain, body, context)`, workers = CPUs−1, grain 65536 for points in current verbs) and
  columnar attributes that are already the layout a column interpreter wants (one
  contiguous 64-byte-aligned `Column[u8]` per attribute, `core/attributes.lucb`,
  `core/shared.lucb`).

### 5.2 Options compared

| | (a) Native compile per cook | (b) Column interpreter in Base | (c) JIT | (d) Hybrid |
| --- | --- | --- | --- | --- |
| Per-point speed, 1M pts, 1 thread | 0.45 ms (measured) | 5–6 ms (measured prototype; ~3.5 ms once constants are scalar operands and copies are views) | ~0.5 ms (expected) | b now, a later |
| Same on 12 threads | ~0.05 ms | ~0.5 ms | ~0.05 ms | |
| Latency per code edit | 0.14 s + `as` + `ld` (measured) | < 1 ms lowering (+ the checker, ~ms) | ~1–5 ms | |
| Runtime dependencies on the user's machine | `luce-base`, `as`, `ld` (MinGW on Windows), SDK via `xcrun` on macOS | none | none | |
| Loading the result | needs a `dlopen` story (none in Base) or a worker process with shared-memory columns | in process | needs `MAP_JIT`/`PROT_EXEC`, code signing on macOS, W^X | |
| Safety of user bugs | a trap kills the app unless out of process; the subset of §4.4 removes memory bugs but not traps | every op is checked; errors stop the cook; cannot trap | same as b if the JIT is correct | |
| Work | compiler driver, dylib emission in luce-base, loader, worker protocol, 3-OS toolchain packaging | lowering from the typed tree, column IR, ~150 column ops, scheduler; all Base | all of b plus an arm64 and x86-64 encoder and a register allocator | b + a |
| Determinism across thread counts | yes if written so | yes by construction | yes | |

Is a native tier more viable now that the snippet is Base? Slightly: no translation step,
and the §4.4 subset already removes undefined behaviour, so the generated code is as safe
as Base's checks make it. The blockers are unchanged and are not about the language: the
toolchain (`luce-base`, `as`, `ld`) on every user's machine, no `dlopen` or shared-library
output in Base, and a trap (bounds, overflow) ending the process, which the subset cannot
remove without the engine's masking. The numbers also do not ask for it: (a) buys 10× on a
part of the cook that is already below the cost of reading and writing the columns. (c) is
the most work for the least gain at these sizes. (b) hits the bar on its own: Houdini's VEX
is itself a bytecode interpreter batched over elements
(https://www.sidefx.com/forum/topic/43672), so matching its architecture with Base's near-C
inner loops puts us in the same league. (d) keeps (a) for the day a network is frozen or
published as a tool, where a 0.2 s compile and a shipped kernel are fine and the lane-fault
semantics can be relaxed to Base's own traps in a worker process.

**Pick: (b), designed so (d) stays open.** The column IR is the contract; a later native
emitter consumes the same IR.

### 5.3 How the column interpreter is built

- **Front end**: the Base checker (§4.3) produces the typed tree; the lowering in
  `luce-kernel` binds API names (`Point.P`, `Kernel.f32`, `lib.snoise`) to column ops,
  resolves attribute reads against the input's attribute store at cook time (names and
  storage types), applies the subset rules of §4.4, and emits a column IR: SSA registers
  typed `f32/f64/i32/i64/mask`, with vectors as 2–4 registers (struct-of-arrays stays
  struct-of-arrays all the way; no per-lane `f32[4]` structs in memory).
- **Program**: a flat instruction array `op, dst, a, b, c` (u16 fields), constants in a
  scalar table, uniforms (parameters, detail attributes, frame, time) in a scalar table
  filled per cook, a fault table (instruction → source position), and a column plan: which
  input columns to bind, which output columns to allocate, with their element types.
- **Execution**: `parallel_for(element_count, chunk)` over geocore's pool; each work item
  takes a chunk of `chunk` lanes (4096 measured best; tune 1024–8192 so registers × chunk
  × width fits L2), owns a per-thread register file allocated once per cook per worker,
  views the bound input columns for that chunk, runs every instruction as a tight slice loop
  (`for i in 0..<n: d[i] = a[i] * b[i]`, the shape the Base backend vectorizes), and writes
  its slice of the output columns under the fault mask. No locks: lanes write disjoint
  slots. Group-restricted runs compact the group's element indices into a lane list first
  (or run masked when the group is dense).
- **Dispatch**: `match op` over a dense opcode (jump table). At 4096 lanes a dispatch costs
  under 1% of the op; the per-element VM at 16 ms versus column at 5.4 ms shows why Houdini
  batches.
- **Ops**: about 150, each in the widths it supports: arithmetic per type with overflow
  masks, compares to masks, select, width conversions, swizzles, math (`sinf`/`sin` etc.
  through luce-std externs; an in-house vectorized `sin`/`cos`/`exp` in `f32[4]` lanes is
  the biggest later speed-up, since libm `sinf` at ~2.5 ns per call dominated the measured
  kernel), noise, hash random, gather/scatter with masks, group bit read/write, reductions
  for `detail`, print into per-lane buffers. Each op is a small Base function over slices;
  adding one is one function plus a table row.
- **Never traps**: every slice index is proven by the chunk bound; gathers mask
  out-of-range indices; integer ops use the `?` and `%` forms internally and set fault
  bits; float ops follow IEEE; loops are capped; nothing allocates inside a chunk.
  Allocation failures before the run surface as errors. The engine is fuzzed with random
  programs (the luce-js approach) so that "cannot crash the app" is tested, not hoped.

### 5.4 What the numbers say about the bar

For the §1 snippet on 1M points: 2 arithmetic passes plus one `sinf` pass per chunk, plus
reading P (12 MB) and writing P (12 MB). Single thread about 4 ms (the sin pass, 2.5 ms,
dominates); on the pool under 1 ms for the kernel and about 2–3 ms for the column copy and
the new mesh (positions copy-on-write, `geometries/polygon/edits.lucb` `with_positions`).
Target: whole cook under 10 ms on the M4 Max; under 40 ms on a 4-core laptop. For the noise
displacement of §4.2 (Perlin 3D: ~40 flops plus 8 gathers of a 512-entry table) about
15–20 ms single thread, 2–3 ms on the pool. Target: whole cook under 25 ms.

## 6. Packaging

Package boundaries rule: packages only for general technology; formats and apps own their
specifics. The owner approved `luce-kernel` under that name.

- **`luce-kernel`** (Base; depends on luce-std and on the `luce-base` compiler's public
  front-end modules): the subset rules and the lowering from Base's typed tree to the column
  IR, the column interpreter and scheduler, the builtin registry so a host adds its own ops,
  the column binding interface (a host hands it named typed columns and gets named typed
  columns back), and the general library `lib` (vector functions, matrices, quaternions,
  interpolation, noise, random, color basics) with its `.lucb` stubs. It knows nothing
  about meshes. luced-2d can drive it for per-pixel expressions over image tiles; luce-image
  or luce-canvas for parameterized filters; a future parameter-expression system in
  luced-3d can use its scalar mode.
- **`luce-geocore`** gains `src/code/`: the geometry bindings and the `luce_geocore.code`
  stubs. It depends on luce-kernel: binding `P` (positions are f32 relative to an f64 origin,
  not an attribute: `mesh.lucb`), attributes, groups, the geometry read ops (`point`,
  `prims`, `neighbours`, `nearpoints`, `closest`, `intersect`, `sample`), the queued edit ops
  (`set_point_*`, `add_point`, `remove_prim`), run-over, and the cook entry
  `code.run(set, inputs, program, uniforms, progress) -> GeometrySet!`. The noise used by
  Mountain and Scatter later comes from luce-kernel through this dependency, so there is one
  noise implementation.
- **`luced-3d`**: the node (parameters, stamps, worker plumbing, spare parameters), the
  editor UI, undo, the timeline. All in Luce, calling `code.run` as it calls every verb.

Dependency direction: luced-3d → luce-geocore → luce-kernel → luce-base (front end) +
luce-std. luce-kernel never imports geocore.

## 7. Integration in luced-3d

File references are to `/Users/sedov/Dev/luce_dev/luced-3d/src`.

### 7.1 Parameters

Today `Node.values` is 32 floats and `Node.texts` is exactly 3 strings set per kind in
`Node.init` (`network.luc:96–107`); the parameter panel has a one-line `text` row and no
multi-line kind (`parameter_rows.luc`, luce-ui `widgets/parameters`); project loading only
accepts single-line texts except Sketch's slot 0 (`project_graph.luc:151–155`). The owner
approved multi-line text. The Code node needs:

- text slot 0: Group (as every node), value slot 15: Group Type (`node_catalog.luc:226–231`);
- text slot 1: the code. Multi-line: `project_graph.luc` saves and loads it (the Sketch
  exception generalized to "kinds whose slot 1 is code"); `compute_request.luc` already sends
  texts whose stamp changed as Prism text, which carries multi-line strings;
- Run Over is not a parameter: it follows from the entry point (§2.1); Numbers takes its
  count from a value row that appears only when `number` is defined;
- spare parameters: on every code change the UI thread checks the snippet (the kernel's
  checker, callable from Luce like any Base module) and collects `k.f32("name", default)`,
  `k.f64`, `k.i32`, `k.vec3`, `k.text` calls with literal names from the typed tree. Each
  unique name becomes a parameter row with that type: floats go into free `values` slots
  above the fixed ones (a `name → slot` map kept on the node), vectors take 3 slots, strings
  take a text slot (S5; `Node.texts` grows then). Rows appear in the inspector below the
  code, in order of first use, with the literal default. Removing a call hides the row but
  keeps the value until the node is saved, so a typo does not lose a tuned value. A name
  computed at run time (`k.f32(name)`) is a compile error: parameters must be literal.

### 7.2 Stamps

`stamp_of` hashes `(kind, enabled, values, texts, input stamps, sources, ...)`
(`stamps.luc:48`). The code is in `texts`, so it is stamped for free; spare parameter values
are in `values`. The timeline (§7.11) adds the frame to the stamp only for nodes whose
snippet reads `k.frame` or `k.time`, which the checker reports.

### 7.3 Worker and result store

Nothing new: `Node.compute` (`network.luc:155–236`) gets one more arm that calls
`code.run(...)`; the worker's `Computation.cook` (`compute_worker.luc:126–171`) mirrors it;
results go into the store by stamp as every other node's do. `code.run` takes a progress
callback; the pool loop polls a cancel flag between chunks so "Computation superseded"
(`compute_bridge.lucb:129–137`) stops a long run (geocore's `parallel_for` has no
cancellation; an atomic "stop" checked per work item is small). Lane faults travel back as
the node's `warning` with their line and count.

### 7.4 Caching compiled programs

Lowering costs under a millisecond and checking a few, so the cache is about not re-binding
columns and keeping chunk scratch warm. A small LRU on the worker keyed by `(code text hash,
attribute signature of the input: names, domains, types)` → lowered program, like
`groups/cache.lucb` keys group programs by `FullKey`. The UI thread caches the checked tree
by code hash for the spare-parameter scan and the error markers; the UI check never touches
geometry.

### 7.5 Editor UI

What exists: luce-ui's `TextEditor` (`luce-ui/src/widgets/text_editor/module.lucb:46–136`)
is a multi-line code editor with highlights, folds, change bars, its own undo and
`update_highlights(start, end, [Highlight], version)`. luced builds its editor on it:
`luced/src/editor/panel.luc` (`EditorPanel`: a `TextEditor` with a status bar and a syntax
menu), `luced/src/workspace/document.luc` (text, history, language analysis),
`luced/src/language/` (`GrammarSet` over luce-textmate, `SyntaxTheme`, folding, swatches)
and the Luce TextMate grammar written out by `luced/src/language/default_grammars.luc:13`
(`luce.tmLanguage.json`, scope `source.luce`, `fileTypes: ["luc", "lucb"]`, so Base is
covered); luced-2d does the same with a smaller `ScriptHighlighter`
(`luced-2d/src/script_editor.luc:130–175`). Diagnostics: neither luced nor luce-ui has them
today; `decorations.lucb` offers AI lines, highlights, swatches, folds and change bars, and
luced runs no compiler check (its subprocesses are `luc info`, `luc new`, git). So:

- luced-3d embeds a `TextEditor` in the inspector for the code slot (a new `code` parameter
  kind; height grows with the panel; "Detach" opens it in a floating Dialog as the 2D
  parameter dialogs do), highlighted by luce-textmate with the same `luce.tmLanguage.json`
  text luced writes (shared by moving the grammar string into luce-textmate as the default
  Luce grammar, so all three editors load one source), with luced's `SyntaxTheme` colors.
- luce-ui gains one decoration, `set_diagnostics(spans: [Diagnostic(start, end, severity,
  message)], version)`, that draws a wavy underline, a gutter mark and a hover message, with
  the same version guard `update_highlights` has. luced and luced-2d get it for free.
- On every edit (debounced), the UI thread checks the snippet against the last known
  attribute signature of the input and publishes diagnostics (checker errors, subset errors,
  and the last cook's error); the node's `failure` string gets the same
  `line:column: message` text so it shows on the node and in the notice
  (`network.luc:590–618`).
- Later: the `EditorPanel`/`Document`/`GrammarSet` glue moves from luced into luce-ui as a
  `CodeEditor` widget so the three apps share it; autocomplete from the API stubs and the
  input's attribute names over the same checker.

### 7.6 Geometry edits from parallel code (S4 design)

Each worker thread owns an edit queue: new points (position, parent for attribute
inheritance), new vertices, new prims (lists of point refs), removals (bit sets), and
scattered attribute sets (element, attribute, value). `k.add_point()` returns a provisional
number `numpt + thread_base + local_index` so later calls in the same lane can refer to it;
after the parallel phase the queues are concatenated in chunk order (fixed by the chunk
index, not by who finished first, which keeps results deterministic), provisional numbers
are renumbered, removals are applied last with `kept_faces`/`compacted`
(`geometries/polygon/subset.lucb`), and attributes of new elements are filled through
`TopologyBuilder` parents (`verbs/builder.lucb`). This is Houdini's batching (reads, then
creates, then sets on new geometry, then deletes). The queues are bounded per chunk
(a lane may add at most 1,024 elements per run; more is an error), so no allocation
happens inside a chunk.

### 7.7 Undo

Parameter and text edits are whole-graph snapshots through `perform` (`workspace.luc:473`,
`node_commands.luc:256–268` `set_text`). Committing on every keystroke would make one undo
step per character and a recook per keystroke. Policy: the editor keeps its own keystroke
undo (`TextEditor` has it); the node text commits (one `perform("Change Code")`, one
recook) on focus loss, on Cmd/Ctrl-Enter, and after a 400 ms pause in typing when the
snippet checks clean. A snippet that does not check never recooks; the previous result stays
with the error shown.

### 7.8 Determinism and threading

Results must not depend on the number of workers or on scheduling. The engine guarantees it
by: lanes map to element indices, not to threads; `rand(seed)` and noise are pure hashes of
their arguments (a per-element random is `rand(p.ptnum + seed)`, as in VEX; never a shared
PRNG); reductions for `detail` use a fixed tree order; edit queues concatenate in chunk
order (§7.6); fault counts are summed per line, order-free. `print` output is collected per
chunk and emitted in element order, capped.

### 7.9 Freeze

`toggle_freeze` cooks synchronously and writes the result file; the frozen stamp replaces
the input-dependent stamp (`cache_node.luc:49–59`, `stamps.luc`). A frozen Code node stops
checking and running; editing its code while frozen is the same as editing any frozen
node's parameters (the stamp ignores them until unfrozen). The "native compile later" tier
of §5.2 (d) is exactly the frozen/published case, so if it is ever built, Freeze is where it
plugs in.

### 7.10 Node first, Edit step later

The owner left the order open. The node comes first, the Edit step in stage 4, because:
the node is the general tool and everything (engine, API, editor, stamps, timeline) is
needed for it anyway; an Edit step (`edit_operations.luc:14–47`) is a verb over a mesh
replayed from checkpoints, keyed by hash, with one free text (`group`) and a numbers list,
so a Code step means a new text field in `EditStep`, its key, `project_graph.luc:108–124`
serialization and the list sharing in `compute_request.luc`; once `code.run` exists, that
wrapper is small and can wait for the first modeling session that wants code between
extrudes. Stage 4 also brings the queued geometry edits, which is what a Code step inside a
modeling session would mostly be for.

### 7.11 Timeline

The owner: "Lets create a timeline of course as well." luced-3d has no time today (no
`$F`, no frame; FBX/USD nodes carry private frame slots, `node_catalog.luc:265–283`). The
design:

- **State on the network**: `frame: float` (current), `start`, `end`, `fps` (default 24),
  `playing: bool` (not saved). Saved with the project (`project_file.luc`) next to the
  graph; a project without them opens at frame 1, range 1–240, 24 fps.
- **Bindings**: `k.frame`, `k.time = (frame - 1) / fps` (Houdini's convention: frame 1 is
  time 0), `k.fps`, all `f64`. The checker reports whether a snippet reads any of them; the
  node keeps a `time_dependent` flag from that report.
- **Stamps**: `stamp_of` includes the frame for time-dependent nodes only, so a frame change
  re-stamps and recooks exactly the time-dependent nodes and what is downstream of them;
  everything else keeps its store entry. The result store's LRU already keeps recent stamps,
  so scrubbing back and forth replays from the store when memory allows (it keeps a quarter
  of physical memory, `compute_bridge.lucb:287`).
- **Playback**: a `Timeline` panel at the bottom of the workspace: play/pause, step back and
  forward, a scrub bar over the range with the current frame, start/end fields, fps field,
  a loop toggle. Playing advances the frame on the UI clock at `fps` and submits a cook; if
  the worker is behind, frames are dropped rather than queued (the request carries the
  wanted stamps, so superseded frames cancel). Scrubbing submits on every change the same
  way. Keys: space to play, left/right to step.
- **Other time-dependent nodes**: FBX and USD readers with their private frame slots can
  later follow the timeline through a toggle; not part of this stage.
- **Undo**: frame changes are not undo steps (they are navigation); range and fps edits are.

## 8. Staged build plan

Each stage ends with `luc test` green in every touched package, the benchmarks below run
from scripts kept in the package, and a release batch (owner rule: batch releases).

### Stage 0: the Base front end as a library (language session)

Scope: `public` modules on the `luce-base` package; a `check_root(root, entry)` entry that
checks a module against a host-supplied root and returns the typed tree plus diagnostics;
the typed-tree walk documented (node kinds, `type_id`, `resolved`, methods and `self`);
the standard-module set the checker builds in listed so the lowering can refuse them by
name. Owner of this work: LUCE_LANG.
Tests: the luce-base suite unchanged; a test that checks a snippet root with the stubs and
a deliberate error and gets `line:column`; a test that the walk sees every node kind the
subset accepts.

### Stage 1: the node

Scope: `luce-kernel` with the subset rules, the lowering, column IR and interpreter; widths
f32/f64/i32/i64/u32/u64 and masks; traps as node errors with line and element; `lib` stubs and ops:
vector functions, `fit/lerp/clamp/smooth`, `rand`, Perlin `noise`/`snoise` in f32 and f64;
`luce_geocore.code` with `Point`, `Vertex`, `Prim`, `Kernel`, `Geometry.bounds()`,
attribute fields and typed accessors, groups, `print`; run-over by entry point;
`if`/`elif`/`else`, `match`, uniform and masked loops with cap, inlined helpers; the
luced-3d node, multi-line text in projects and requests, inspector code editor with the
Luce grammar and the new diagnostics decoration, spare parameters, undo policy, stamps,
cancellation.
Deliverables: `luce-kernel` 0.1 (docs: the accepted subset, the exclusion list, errors,
with the C/VEX framing; the `lib` reference generated from the stubs), geocore `code`
module, luced-3d Code node, `docs/CODE.md` user page in luced-3d, the luce-ui decoration.
Tests: luce-kernel unit tests per op against scalar references in every width; a
conformance suite of snippets with expected columns (VEX-compatibility cases: `noise`
range, `fit`, `rand` distribution); an exclusion suite (every construct of §4.4's excluded
list is refused at the right line); a fault suite (every trap of §4.5 becomes a counted
fault and leaves input values intact); fuzzing of random accepted programs (must never
trap); geocore tests for binding every attribute type and domain and for group
restriction; luced-3d headless test that builds a 1M-point grid and runs the benchmark
snippets; a test that the same snippet gives identical bits at 1, 2 and 16 workers.
Benchmarks (M4 Max, 1M points, whole cook on the worker): `p.P[1] += math32.sin(p.P[0] *
4.0) * 0.1` ≤ 10 ms; the noise displacement ≤ 25 ms; `p.Cd = rand3(p.ptnum)` ≤ 8 ms; empty
`point` over 1M points ≤ 3 ms (binding and copy overhead); check + lower of a 50-line
snippet ≤ 5 ms. Also on the Windows and Linux test machines.

### Stage 2: the timeline

Scope: §7.11 in full: network state, project save/load, `k.frame/time/fps`, time-dependent
flag and stamps, the Timeline panel, playback and scrubbing, superseded-frame cancellation.
Tests: a time-dependent Code node downstream of a static one recooks alone on a frame
change (stamp test); project round trip of range and fps; playback drops frames rather than
queueing when the worker is slow (headless test with an artificially slow cook).
Benchmark: scrubbing a 100k-point noise snippet holds 24 fps on the M4 Max.

### Stage 3: reading geometry and the second input

Scope: `k.input(i)` with `point(i)`, `prim(i)`, `vertex(i)` reads and per-lane gathers;
topology reads (`f.points()`, `p.prims()`, `p.neighbours()`, `v.point`, `v.prim`) as
spans; `nearpoints` (a k-nearest and radius query in geocore built on `PointHash` cells or
a kd-tree); `closest` with uv and `prim_*` interpolation (closest point with uv from the
BVH); `intersect` with hit position and uv; queued `set_point_*`/`set_prim_*` scattered
writes; `add_point_f32`-style explicit creation; `Mat3/Mat4/Quat`, transforms,
fractal/simplex/curl noises, color basics; `for x in span` over API spans.
Tests: gathers against masks and out-of-range (faults); nearpoints against brute force;
closest against `surface_distance`; scattered write ordering (last writer per element is
the highest lane index, documented).
Benchmarks: `nearpoints` radius query with ~10 neighbours over 1M points ≤ 80 ms; `closest`
of 1M points against a 100k-triangle mesh ≤ 120 ms.

### Stage 4: editing geometry, Code as an Edit step

Scope: `add_point/add_prim/add_vertex/remove_point/remove_prim/remove_vertex` with
per-thread bounded queues and the deterministic apply of §7.6; snippet-declared structs of
plain scalars; `find_*`, `uniqueval`-style lookups; half-edge functions; noise derivatives,
Worley/Voronoi; volume sampling; the Code Edit step (§7.10).
Tests: a snippet that scatters N points per source point reproduces a Copy/Scatter result
bit for bit at any worker count; removal + creation in one snippet; attribute inheritance
of new elements; an Edit node with a Code step replays from a checkpoint.
Benchmarks: 1M `add_point` calls ≤ 60 ms; `remove_point` of half of 1M ≤ 20 ms.

### Stage 5: strings and arrays

Scope: ragged per-element arrays in geocore (`const f32[]`, `const f32[4][]` attributes),
span methods, string columns with interning, `format` into per-lane buffers and `str`
methods, `re_*` via luce-regex, `set_text`, `k.text`.
Tests: VEX-compatible string and array cases.
Benchmarks: 1M `p.set_text("name", f"piece_{p.primnum // 100}")` ≤ 60 ms.

### Later (not scheduled)

Autocomplete and hover docs from the stubs; a pixel mode for luced-2d; vectorized
`sin/cos/exp` in `f32[4]` lanes (expected to double trig-heavy snippets); the
native-compile tier for frozen or published networks (§5.2 d); the shared `CodeEditor`
widget in luce-ui; keyframes on parameters over the timeline.

### Beyond stage 5: the rest of VEX, in order

From the VEX function index (https://www.sidefx.com/docs/houdini/vex/functions/index.html,
read 2026-10-08), in the order geometry work needs it. Shading, lights, BSDFs, crowds,
CHOP, channel primitives, OCIO, USD and texture families are left out: luced-3d does those
with nodes, or doesn't do them yet.

1. **Math and transforms.**
   - Matrices: `ident transpose invert determinant maketransform cracktransform lookat dihedral rotate scale translate prerotate polardecomp`.
   - Quaternions: `quaternion qmultiply qrotate qinvert slerp eulertoquaternion quaterniontoeuler qconvert`.
   - Math: `abs sign frac rint trunc min max avg sum product pow exp log log10 cbrt` and the `*pi` trig forms; `solvequadratic solvecubic`; `distance_pointline distance_pointsegment distance_pointray planepointdistance`.
   - Interpolation: `efit fit10 fit11 invlerp lspline cspline kspline spline`.

   `Mat3`, `Mat4` and `Quat` are Base structs with methods, since Base has no operator
   overloading; the vector ops stay lane operators.
2. **Ramps.**
   - `chramp`/`ramp_lookup` with a ramp parameter row (a luce-ui ramp widget: points, interpolation, color or float), saved on the node.
   - Wranglers use this constantly for falloffs and color maps.
3. **Noise and sampling.**
   - Noise: `curlnoise curlnoise2d` (divergence-free, for flow), `flownoise`, `wnoise`/`mx_worley`/`mx_cellnoise` (cellular), `anoise`/`onoise`/`xnoise`/`pnoise` (periodic), `noised`/`xnoised` (with derivatives).
   - Random: `nrandom random_sobol random_poisson`.
   - Sampling: `sample_sphere_uniform sample_hemisphere sample_direction_cone sample_circle_uniform sample_normal`.
4. **Topology.**
   - Vertices: `vertexprim vertexpoint vertexnext vertexprev primvertex primvertexcount pointvertices`.
   - Half-edges: `hedge_*`, `pointhedge primhedge`.
   - Neighbors: `polyneighbours`.
   - Groups: `expandpointgroup expandprimgroup`, `npointsgroup`.
5. **Measure.**
   - `getbbox_*`, `relbbox`, `relpointbbox`, `minpos`, `surfacedist`, `windingnumber`, `computenormal`, `primarclen`, `curvearclen`.
   - Sampling a surface: `uvsample`, `primuv` already in S3.
6. **Point clouds.**
   - `pcopen pcfilter pcfind pcfind_radius pciterate pcimport pcnumfound`, over the same point grid as `nearpoints`, plus `pcfilter`'s weighted average as one call (the common smoothing idiom).
7. **Volumes.**
   - `volumesample volumesamplev volumegradient volumeindex volumepostoindex volumeres` over luce-geocore's fields.
   - Then SDF-driven wrangles: snapping to a surface, coloring by distance.
8. **Strings, arrays, dicts.**
   - Strings: `sprintf split join replace startswith re_match re_replace atoi atof itoa`.
   - Arrays: `append insert pop push removeindex resize reverse slice sort argsort find len foreach`.
   - Dicts: `keys json_dumps`, last.
   - Needs per-element ragged storage; S5 starts it.
9. **Utility.**
   - `printf` to the node's console (in element order, capped); `warning` and `error` from code (an error fails the node with its line).
   - `getcomp`/`setcomp` are Base indexing already.

Each item ships as `lib` functions (or geocore `Host` builtins when they read geometry),
with stubs, a scalar reference, conformance cases against VEX's documented values, and a
benchmark at 1M elements.

## 9. Decisions taken and open questions

Decided by the owner on 2026-10-08:

1. **Syntax: pure Luce Base.** No `@` bindings, no `ch()`; a snippet is a Base module with
   entry points and typed API values (§4.2); the safe subset and node errors are §4.4–4.5.
   The Base compiler's front end is reused as a library (§4.3) rather than writing a second
   parser. (An earlier revision chose Luce syntax; Base replaced it because it names storage
   widths and has vector operators, which Luce lacks.)
2. **Precision: whatever the attribute is.** In Base that is the type system; widths are
   explicit and casts are written (§4.6).
3. **Package: `luce-kernel`**, approved under that name (§6).
4. **Multi-line text** in nodes and projects, with the editor stack luced already uses on
   luce-ui's `TextEditor`, plus a diagnostics decoration that does not exist yet (§7.5).
5. **Timeline**: designed in §7.11, built as stage 2, right after the node and before the
   geometry reads, because animated snippets are the first thing users try.
6. **Node before Edit step** (§7.10).
7. **Engine**: the column interpreter; native compilation per cook stays ruled out (§5.2).

Also decided on 2026-10-08:

8. **It looks and works like VEX, with Base syntax.**
   - The user writes only the body, as in a Wrangle.
   - The node generates the wrapper for its Run Over mode; the wrapper defines `p`, `f`, `v`, `n` and `k` and imports the kernel library (§1, §4.2).
   - The entry points' pointer types live in generated code, never in the user's text.
9. **A fault fails the node.**
   - The first failing element stops the cook.
   - The node errors out with the line and the element (§4.5).
   - There are no partial results and no warnings with counts.
10. **`f32[4]` for three-component attributes**, for Base's lane operators.

Nothing is open now. Stage 0 (the Base front end as a library) was sent to the language
session.

## Appendix A: benchmark details

Scratch directory (not in any repo):
`/private/tmp/claude-501/-Users-sedov-Dev-luce-dev/26944722-c0bc-4a1f-9a03-297d52283e2a/scratchpad/code-node/`.
Host: Apple M4 Max, 16 cores, macOS 24.6.0, dev toolchain `~/.local/bin` (luce 0.14.0,
luce-base 0.39.0). Wall clock; one thread unless said.

- `hello.luc`, `luce run`: under 10 ms per run (the `time` resolution floor), three runs.
- `loop.luc`: 1M-element `list[float]` setup then one pass of `py[i] += (x - x*x*x*0.1666)*0.1`
  with `x = px[i]*4`. `luce run`: 1.00 s setup only, 2.25 s with the pass → 1.25 s per
  1M-element pass. `luce build --native --release`: 0.16 s compile; the native binary's pass
  is below the resolution of whole-process timing (0.18 s vs 0.03 s totals are process start
  and list setup); the Base kernels below are the real native number.
- `kernel.lucb` (with `sinf`), `luce-base build --native --release` compile 0.14 s wall,
  `--backend=c --release` 0.44 s: per round, 1M points: fused 2.5–2.7 ms; op-at-a-time over
  whole columns 5.2–5.5 ms; chunked 1024 4.7 ms; per-element switch VM 4.8–5.6 ms (libm
  `sinf` dominates all four). Through the C backend (clang): 1.7–2.0 ms for all four.
- `kernel2.lucb` (no libm, 7 ops): fused 0.45–0.5 ms; whole-column passes 3.4–4.3 ms;
  chunked 3.9–4.5 ms; per-element generic register VM 16–17.5 ms; column VM with computed
  indices (not vectorized by the backend) 15.3–15.5 ms.
- `kernel3.lucb` (same program, column VM with slice-typed op functions): chunk 256 →
  5.9–11 ms, 1024 → 5.5–8.9 ms, 4096 → 5.4–7.8 ms over three rounds (first round cold); the
  12 passes per chunk include 5 setup copies/fills the real engine will not do (constants
  as scalar operands, views instead of copies), so about 3.5 ms is the expected
  single-thread figure for 7 ops.

## Appendix B: code references used

- luced-3d: `src/network.luc` (`Node`, `compute`, `cook`, errors), `src/compute_worker.luc`,
  `src/compute_bridge.lucb`, `src/compute_request.luc`, `src/result_store.luc`,
  `src/stamps.luc`, `src/node_catalog.luc`, `src/parameter_rows.luc`, `src/inspector.luc`,
  `src/geometry_nodes.luc`, `src/node_evaluation.luc`, `src/cache_node.luc`,
  `src/edit_operations.luc`, `src/edit_steps.luc`, `src/project_graph.luc`,
  `src/project_file.luc`, `src/node_commands.luc`, `src/workspace.luc`, `src/history.luc`.
- luce-geocore: `src/core/attributes.lucb`, `core/attribute_ops.lucb`, `core/shared.lucb`,
  `core/float3.lucb`, `core/parallel.lucb`, `core/hash.lucb`, `core/bits.lucb`,
  `math/vector.lucb`, `math/matrix.lucb`, `geometries/polygon/mesh.lucb`, `access.lucb`,
  `attributes.lucb`, `edits.lucb`, `subset.lucb`, `groups.lucb`,
  `geometries/topology/connectivity.lucb`, `geometries/triangle_index.lucb`,
  `geometries/point_hash.lucb`, `fields/grid.lucb`, `fields/mesh_distance.lucb`,
  `groups/program.lucb`, `groups/evaluate.lucb`, `groups/cache.lucb`, `verbs/builder.lucb`,
  `verbs/point_verbs.lucb`, `geometries/attribute_kernels.lucb`,
  `set_verbs/attributes.lucb`.
- luce-base: `package.prisma`, `src/main.lucb` (`check`, `build`, assembler and linker
  calls at 614–747, `build_library` at 855–906), `src/front/*.lucb` (`ast.lucb:198–201`
  `type_id`/`resolved`), `src/sema/*.lucb`, `src/sema/check/*.lucb`, `src/back/backend.lucb`,
  `src/back/target.lucb`, `src/back/opt/vectorize.lucb`, `docs/language/base.md` (§4.3
  literals, §5.3 pointers, §5.12 vectors, §6.2 `---`, §7.2 arithmetic, §7.4 "No user type
  overloads an operator", §8.9 asm, §11.5 traps, §12 memory, §12.6 the safety statement,
  §12.7 memory.frame, §17 C), `docs/NATIVE-PERFORMANCE.md`, `benchmarks/native_vs_c/`.
- luce: `src/main.lucb`, `src/hir/interp/interp.lucb`, `src/back/package.lucb`,
  `src/support/sandbox.lucb`, `docs/DESIGN.md`, `docs/luce.md` (line 467 "There is no
  overloading"; line 1204 `float` ↔ `f64`/`f32`), `docs/guide/topics/16-base.md`.
- luce-pkg: `src/package.lucb` (`public`, kinds).
- luce-std: `src/math.lucb`, `src/math32.lucb`, `src/random.lucb`, `src/parallel.lucb`.
- luce-js: `src/engine/interpreter.lucb`, `src/host/native_modules.lucb`,
  `docs/PERFORMANCE.md`, `docs/COMPILER-REQUESTS.md`, `README.md`.
- luced: `src/editor/panel.luc`, `src/workspace/editors.luc`, `src/workspace/document.luc`,
  `src/language/default_grammars.luc`, `grammars.luc`, `appearance.luc`.
- luced-2d: `src/script_host.luc`, `src/script_editor.luc`, `scripting/luced.luc`,
  `docs/SCRIPTING.md`.
- luce-ui: `src/widgets/text_editor/module.lucb`, `decorations.lucb`; luce-textmate
  `src/textmate.lucb`.
