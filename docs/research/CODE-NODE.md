# Code node: a wrangle for luced-3d

Research and design, 2026-10-08. No code was changed for this document. It answers the
owner's request: "the other node we need to make is Code. This is like a wrangle node that
executes code either once, or in parallel per point, polygons etc. ... all that will be
written in Luce (or luce base whichever is better suited) ... It should be really fast as
well just like Wrangle node in Houdini."

## 1. Decision in one page

**Language.** The Code node runs a small, statically typed subset of Luce syntax (Python-like
indentation, `let`/`var`, `if`/`elif`/`else`, `for`, `and`/`or`/`not`) plus Houdini's `@`
attribute bindings (`@P`, `v@up`, `f@mass`, `i@id`, `@ptnum`, `ch("amount")`). Users who know
Luce read it at once; users who know VEX wrangles recognise every `@` form. It is not full
Luce: no classes, no heap, no imports, no recursion, no calls into Luce or Base code. Those
limits are what make it safe, instantly compiled and vectorizable. §4 argues this.

**Engine.** A column (batch) interpreter written in Luce Base, in a new general package,
`luce-kernel`. The snippet is compiled, in a millisecond, into a register program whose every
instruction runs over a chunk of elements (a few thousand lanes) at a time; chunks run on
geocore's parallel pool. Houdini's VEX works the same way (bytecode, "SIMD" over batches), so
the speed league is the same. A native-compile tier (the Base toolchain emitting a kernel for
a frozen or published network) stays possible later, but it is not needed to hit the bar and
it would force every user's machine to carry a compiler, an assembler and a linker. §5 has
the measurements.

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
4.7 ms). On 10–14 worker threads the column interpreter lands at about 0.5–1 ms for
`@P.y += sin(@P.x * 4) * 0.1` on 1M points, before the cost of reading the mesh's columns
and writing new ones (a few ms, same as every other node). A Houdini Point Wrangle on the
same snippet at 1M points takes on the order of 10–30 ms on comparable hardware (there is no
authoritative SideFX number; this is the common experience and the bar to beat).

Compile latency: the Base toolchain compiles a small module to a native executable in
0.14 s wall (`luce-base build --native --release`), which is fine for a build but a poor
fit for every keystroke in an editor, needs `as` and `ld` (MinGW on Windows) at the user's
machine, and has no in-process loader (`dlopen`) in Base today. The column interpreter
compiles a snippet in well under a millisecond and is the same binary on the three targets.

**Stage 1** (§8) is a working Point/Primitive/Vertex/Detail wrangle with `@P`, `@N`, `@Cd`,
custom float/int/vector attributes created by writing, groups, `ch()` spare parameters, the
math/vector/interpolation/noise/random families, errors at the line, and the 1M-point
benchmark targets. Geometry reads (`point()`, `nearpoints()`), geometry edits (`addpoint()`,
`removeprim()`), strings and arrays follow in stages 2–4.

## 2. What a wrangle is (semantics to match)

Sources: SideFX "Attribute Wrangle" node reference
(https://www.sidefx.com/docs/houdini/nodes/sop/attribwrangle.html), "Using VEX expressions"
(https://www.sidefx.com/docs/houdini/vex/snippets.html), the VEX function index
(https://www.sidefx.com/docs/houdini/vex/functions/index.html) and the VEX language
reference (https://www.sidefx.com/docs/houdini/vex/lang.html).

### 2.1 Run Over

The snippet is one function body. The node runs it once per element of the chosen domain:

| Run Over | Houdini meaning | geocore domain (`core/attributes.lucb`) |
| --- | --- | --- |
| Detail (only once) | one run; `@ptnum` etc. are 0; detail attributes bind | `Domain.detail` |
| Points | once per point, in parallel | `Domain.point` |
| Vertices | once per vertex (a polygon corner) | `Domain.corner` |
| Primitives | once per primitive (face) | `Domain.face` |
| Numbers | N runs with only detail attributes bound; `@elemnum` is the index | no domain; N lanes |

geocore has one domain Houdini lacks, `Domain.edge`, and calls Houdini's vertex a corner.
The Code node's menu uses Houdini's words (Points, Vertices, Primitives) for people coming
from Houdini and maps them to geocore's domains. Edge run-over is cheap to add later since
groups already support edges.

### 2.2 Attribute bindings

From the snippets page: `@name` reads or writes the attribute `name` on the current element.
A type prefix fixes the type: `f@` float, `i@` int, `v@` vector (3), `u@` vector2, `p@`
vector4, `s@` string, `2@`/`3@`/`4@` matrix2/3/4, `d@` dict, and array forms `f[]@`, `v[]@`
and so on. Well-known names need no prefix: `@P`, `@N`, `@Cd`, `@uv`, `@v`, `@orient`,
`@rot`, `@id`, `@name`, `@ptnum`, `@numpt`, `@primnum`, `@numprim`, `@vtxnum`, `@elemnum`,
`@Frame`, `@Time`, `@TimeInc`. "Other attributes are assumed to be float unless you specify
a type." Writing to an attribute that does not exist creates it on the run-over domain
("If you write to a @attribute in the VEX code and the attribute does not exist, Houdini
will create it"). A second input's attribute at the same element index is
`v@opinput1_P`; arbitrary elements of any input go through `point(1, "P", index)`.

A special binding `@group_name` reads 1/0 membership and writes it to add or remove the
element from the group.

Read/write rule ("three geometries: input, current, output"): bound reads see the input
geometry; bound writes are queued and land in the output after the snippet finishes;
`point()` reads never see what the snippet wrote with `@foo =`; `setpointattrib()` writes
override `@foo =` writes. We keep exactly this rule because it is what makes per-element
parallelism trivially race-free: within one cook, every lane reads the same immutable input
columns and writes its own slot of the output column.

### 2.3 Groups and parameters

The node's Group and Group Type parameters restrict which elements run; everything else
passes through untouched. luced-3d already has this pair (text slot 0, value slot 15) and
geocore evaluates the expression into a bitmask (`luce-geocore/src/groups/evaluate.lucb`).

`ch("name")`, `chf`, `chi`, `chv`, `chs` read a parameter of the node. In Houdini a button
"Creates spare parameters for each unique call of ch()" scans the snippet and adds a
parameter per unique channel name; the owner's "remove repeated typing" principle says do
that automatically on every edit (§7.1).

### 2.4 Editing geometry from parallel code

From the snippets page: "The geometry creation functions can run in parallel. All changes
are queued and applied after your VEX code has iterated over all existing geometry."
`addpoint()` returns the new point number at once (so a snippet can `addvertex` to it) but
the point does not exist to other lanes; `removepoint()`/`removeprim()` are queued deletes;
`setpointattrib(0, "Cd", pt, value)` sets an attribute on any element, queued, and wins
over `@Cd =`. Houdini's own description of the batching (SideFX forum, "VEX SIMD GPU
Implementation", https://www.sidefx.com/forum/topic/43672): reads together, creation
together, attribute sets on new geometry together, deletes together; reads multi-threaded,
writes single-threaded.

### 2.5 Errors

Houdini reports compile errors with the line and column of the snippet and marks the node
red; runtime failures do not exist for most functions (they return defaults: reading a
missing attribute gives 0, out-of-range indices are ignored). We follow that: compile errors
are precise and shown at the line in the editor; runtime operations never trap, and the few
that can fail (division by zero, bad index) produce the IEEE or default value and, at most, a
warning on the node.

## 3. The VEX function catalog against geocore

Status column: **have** (exists in geocore or luce-std and can be bound directly), **easy**
(a few lines over something that exists), **missing** (new code), and the stage that needs
it (S1–S4 from §8; "–" means not planned). Sources for what exists:
`luce-std/src/math.lucb`, `math32.lucb`, `random.lucb`; `luce-geocore/src/math/vector.lucb`
(`Vector3`, f64), `math/matrix.lucb` (`Matrix4`, affine), `core/hash.lucb` (`mix`),
`geometries/attribute_kernels.lucb:85` and `verbs/point_verbs.lucb:224` (sin-hash white
noise only), `geometries/triangle_index.lucb` (BVH: ray, nearest face, distance; no hit
position or uv), `geometries/point_hash.lucb` (uniform grid; `nearest` only),
`geometries/topology/connectivity.lucb` (`Topology`: next/previous/twin corner, valence;
point→faces, point→edges CSR tables), `fields/grid.lucb` (`GridSampler.sample`, trilinear),
`groups/*.lucb`, `verbs/builder.lucb` (`TopologyBuilder`), `geometries/polygon/subset.lucb`
(`kept_faces`, `compacted`).

### 3.1 Math, vectors, matrices, quaternions

| Functions (VEX names) | Status | Stage |
| --- | --- | --- |
| `abs sign floor ceil rint trunc frac sqrt cbrt exp log log10 pow sin cos tan asin acos atan atan2 sinh cosh tanh isnan isinf isfinite min max avg sum product` | have (luce-std `math32`), bind as column ops | S1 |
| `length length2 distance distance2 normalize dot cross` | have (`Vector3`, f64) → re-implement as f32 column kernels | S1 |
| `vector2/3/4` constructors, swizzles `.x .y .z .w`, `set()` | missing (trivial in the compiler) | S1 |
| `ident transpose determinant invert` for `matrix3`/`matrix` | partly (`Matrix4.inverse`, `determinant`); need mat3 | S2 |
| `maketransform(trs) lookat dihedral rotate translate scale prerotate polardecomp` | missing; `Matrix4.compose` covers trs | S2 |
| `quaternion qmultiply qrotate qinvert slerp eulertoquaternion quaterniontoeuler` | missing (geocore has no quaternion type) | S2 |
| `outerproduct diag makebasis solvecubic solvequadratic eigenvalues svddecomp` | missing | – |

### 3.2 Interpolation and fit

| Functions | Status | Stage |
| --- | --- | --- |
| `clamp lerp fit fit01 fit10 fit11 invlerp smooth efit` | easy (one column op each) | S1 |
| `slerp slerpv` | with quaternions | S2 |
| `spline cspline lspline kspline ckspline` | missing | S3 |

### 3.3 Noise and random

| Functions | Status | Stage |
| --- | --- | --- |
| `rand(seed) random(ix) random_ihash random_fhash nrandom` | easy: hash-based, per-lane seeded (`core/hash.lucb` `mix`, luce-std `Random` for the detail case) | S1 |
| `noise snoise` (Perlin, signed/unsigned, 1D–4D in, float/vector out) | missing; implement improved Perlin (Ken Perlin 2002 gradients) in f32 columns | S1 |
| `xnoise` (simplex), `onoise`/`anoise` (fractal sums), `vnoise` (Voronoi/cell), `wnoise`/`mwnoise` (Worley), `curlnoise`/`curlxnoise` (curl of a noise vector field), `flownoise` | missing; fractal sums and curl are compositions of the base noises | S2 (fractal, simplex, curl), S3 (worley/voronoi, flow) |
| `noised xnoised` (noise with derivatives) | missing | S3 |
| `random_sobol random_brj sample_*` | missing | – |

Note: Houdini's `noise()` returns 0.5-centered unsigned noise in [0,1] and `snoise` the
signed form; `rand()` is a per-element hash of its seed; results must be bit-identical run
to run and across thread counts (§7.8). geocore's Mountain verb should move onto the same
noise once it exists (currently white noise, `verbs/point_verbs.lucb:224`).

### 3.4 Geometry reads

| Functions | Status | Stage |
| --- | --- | --- |
| `@attr` bound reads, `@opinput1_attr` | have (columns in `AttributeStore`; positions `point_span()` + origin) | S1 |
| `npoints nprimitives nvertices` (`@numpt @numprim @numvtx`) | have (`access.lucb` counts) | S1 |
| `point(input, "attr", ptnum) prim(...) vertex(...) detail(...)`, `attrib()`, `hasattrib`, `attribtype`, `attribsize` | have (typed column access `typed[T]`, `find_attribute`) → gather ops in the VM | S2 |
| `primpoints primpoint primvertexcount primvertex pointprims pointvertices vertexpoint vertexprim vertexnext vertexprev` | have (`offsets`, `corners`, `corner_faces`, `point_face_span`) | S2 |
| `neighbours neighbour neighbourcount` | easy (walk `point_edge_span` + `edge_span`, as `cook_smooth` does) | S2 |
| `polyneighbours`, `hedge_*` half-edge family, `pointedge pointhedge` | have (`Topology.next/previous/twin`) → thin wrappers | S3 |
| `nearpoint nearpoints(input, P, radius[, maxpoints])`, `pcopen/pcfind/pcfilter/pcimport/pciterate` | **missing**: geocore has only a grid `nearest`; needs a k-nearest / radius query (grid is fine: iterate cells, sort by distance) | S2 (nearpoints, pcfind-style), S3 (pcfilter) |
| `xyzdist(input, P, &prim, &uv)`, `minpos`, `primuv(input, "attr", prim, uv)`, `primduv`, `pointprimuv` | partly: BVH gives face+distance, not the closest point or uv; `fields/mesh_distance.lucb` `closest_feature` has the triangle maths. Need: closest point with barycentric uv, and attribute interpolation at (face, uv) | S2 |
| `intersect(input, orig, dir, &pos, &uv)`, `intersect_all` | partly: `TriangleIndex.ray` returns face and distance; add hit position and uv | S2 |
| `getbbox getbbox_center getbbox_size relbbox getpointbbox` | have (`Bounds`) | S1 (detail-only) |
| `volumesample volumegradient volumeindex` | have for sampling (`GridSampler.sample`); gradient easy | S3 |
| `inpointgroup inprimgroup invertexgroup`, `@group_x` reads | have (group bits) | S1 |
| `idtopoint nametopoint findattribval uniqueval nuniqueval` | easy (hash index built once per cook) | S3 |
| `windingnumber surfacedist uvdist planepointdistance` | missing | – |

### 3.5 Geometry writes

| Functions | Status | Stage |
| --- | --- | --- |
| `@attr = v` bound writes (create if missing) | have the storage (`with_attribute_entry`, `typed_mut`); the VM writes output columns | S1 |
| `setpointgroup setprimgroup setvertexgroup`, `@group_x = 1` | have (`with_group_bits`) | S1 |
| `setpointattrib setprimattrib setvertexattrib setdetailattrib setattrib` (any element, queued) | easy over output columns with a per-thread write queue (§7.6) | S2 |
| `addpoint addprim addvertex removepoint removeprim removevertex` | have the bulk tools (`TopologyBuilder`, `MeshBuilder`, `kept_faces`, `compacted`); need the queue and the two-phase apply (§7.6) | S3 |
| `setprimvertex setvertexpoint`, `primintrinsic`/`setprimintrinsic` | missing | – |
| `addattrib addpointattrib ...` (explicit create with defaults) | easy | S2 |
| `removeattrib removepointattrib ...` | easy (`without_attribute`) | S3 |

### 3.6 Strings, arrays, color, measure, conversion

| Functions | Status | Stage |
| --- | --- | --- |
| `s@name` reads/writes, `sprintf`, `concat`, `strlen`, `startswith`, `find`, `tolower/toupper`, `itoa`, `atoi/atof`, `split`, `join`, `re_match`... | geocore stores strings as an index into a shared table (`DataType.text`), so string columns are int columns plus a table: equality and group tests are cheap; building new strings needs per-lane allocation and interning (`luce-regex` exists for `re_*`) | S4 |
| arrays `f[]@`, `len append push pop sort reverse slice argsort find` | geocore has no per-element arrays ("no arrays-per-element", `attributes.lucb`); needs a ragged column type (offsets + values) in geocore first | S4 |
| `luminance hsvtorgb rgbtohsv blackbody ctransform` | partly in `luce-color` (all color maths lives there; see memory "luce-color science home"); `luce-kernel` must not depend on luce-color for a 3-line `luminance`; HSV is small enough to inline, `ctransform` binds luce-color from the app side | S2 |
| `degrees radians` | easy | S1 |
| `getbbox*`, `distance`, `primarclen` | S1/S3 as above | |
| `Du Dv area perimeter` (shading only), `printf` (debug) | `printf` → the node's console, detail or first N lanes | S1 (`printf`) |

### 3.7 What a first version needs (S1)

Math, vector constructors and swizzles, interpolation/fit, `rand`, Perlin `noise`/`snoise`
(1–4D in, float or vector out), bound reads/writes of float/int/vec2/vec3/vec4 attributes and
groups, `@ptnum @numpt @primnum @numprim @vtxnum @elemnum @Frame @Time`, `ch*()`, `printf`,
bounding box of the input, Run Over Detail/Points/Vertices/Primitives/Numbers. Everything in
3.4–3.6 beyond that is stage 2+.

## 4. The language

### 4.1 Options weighed

1. **Full Luce, run by `luce run`.** The interpreter is a tree walker
   (`luce/src/hir/interp/interp.lucb`, "the semantic oracle"), refuses Base imports, runs
   workers sequentially (`luce/docs/luce.md:1045`) and measured 1.25 s for one pass of a
   7-op expression over 1M floats: 2,000× off the bar. Out of process (luced-2d's
   `script_host.luc`) adds a process, files and a line protocol per cook. Right for luced-2d's
   document-level scripts; wrong for per-element code.
2. **Full Luce or Base, compiled natively per cook.** Near-C speed (fused loop 0.45 ms) but:
   every cook that changes the code pays 0.14 s plus `as` and `ld`; `luce build` itself shells
   out to `luce-base` (`luce/src/back/package.lucb:155–190`) which shells out to `as` and the
   system linker (`luce-base/src/main.lucb:614–747`); Base has no `dlopen`
   (`luce-js/src/host/native_modules.lucb:3–10`) and `--lib` makes only a static archive
   (`main.lucb:855–906`); user code with a bug would trap and a Base trap ends the process
   (`luce-std/src/parallel.lucb` header: "A trap in any item stops the whole program"). It
   would also have to ship a compiler toolchain inside the luced-3d install on all three OSes.
   Full Luce also has no vector/matrix types or the `@` binding grammar; users would write
   per-element loops themselves, against the owner's "no per-element loops in .luc" rule.
3. **A Luce-syntax expression subset with `@` bindings, compiled by us to a column program.**
   What VEX is to C: same surface, restricted so the compiler can lay every value out as a
   column and prove it cannot crash. This is the pick.

### 4.2 The subset, concretely

Lexically Luce: indentation blocks, `#` comments, `let`/`var`, `if`/`elif`/`else`, `for i in
a..<b` and `for x in array` (bounded loops), `while` with a per-cook iteration cap, `and`/
`or`/`not`, `//` integer division, `**`? (no: Luce has `math.pow`; the subset offers `pow()`),
f-strings only inside `printf`. Statically typed with inference from the bindings and
literals; the user never writes a type except through the `@` prefixes and constructors.

Types: `float` (f32 in columns; Luce's `float` is f64 but geometry attributes are f32 and so
are Houdini's; a `--precise` cook option can switch columns to f64 later), `int` (i32),
`vec2`/`vec3`/`vec4` (f32 lanes), `mat3`/`mat4` (S2), `bool` (mask), `str` (S4), arrays (S4).
Operators as in Luce; `*` between a vector and a scalar scales, between two vectors is
component-wise (as VEX), `@` is not an operator. Swizzle fields `.x .y .z .w` and index `[0]`.

Bindings: `@P`, `@N`, `@Cd`, `@uv`, `@v`, `@id`, `@ptnum`, `@numpt`, `@primnum`, `@numprim`,
`@vtxnum`, `@numvtx`, `@elemnum`, `@Frame`, `@Time`, `@TimeInc`, `@group_name`, typed
`f@ i@ v@ u@ p@ s@ 2@ 3@ 4@` and `@opinput1_name`. Attribute names allow `_` and digits.
Writing to an unbound name creates a float attribute on the run-over domain, or the type the
prefix says, or the type of the first assigned value when that is unambiguous (a vector
literal makes a vec3); mixing prefixes for one name is a compile error.

Functions: the catalog of §3; user-defined `func` inside a snippet is S3 (inlined; no
recursion). `return` ends the lane's run.

What is deliberately not there: classes, closures, heap allocation, imports, string
formatting outside `printf`, calling Luce or Base code, unbounded loops. Anything in that
list that users turn out to want becomes a builtin or a stage, not a hole in the sandbox.

### 4.3 Why this maps to columns

Every expression has one value per lane. The compiler turns `let x = @P.x * 4.0` into
"column x = column P.x times scalar 4.0". An `if` on a per-lane condition becomes a mask:
both branches run over the chunk and the assigned variables are selected by the mask (VEX and
every SIMD language do this; cost is the sum of both branches, fine for snippets). A uniform
condition (depends only on `ch()`, detail attributes or constants) is a real branch. A loop
with a uniform trip count runs as nested chunk passes; one with a per-lane trip count runs
masked until all lanes have exited, with a cap (1M iterations per lane) that makes it an error
instead of a hang. A gather (`point(0, "P", i)` with per-lane `i`) is one column op that
reads a column at per-lane indices with bounds masking. Scalars that are the same on every
lane (parameters, detail attributes, uniform `let`s) are kept as scalars and broadcast only
when an op needs them.

## 5. The execution engine

### 5.1 What exists

- `luce` (0.14.0) and `luce-base` (0.39.0) are both tools written in Base, not libraries;
  `luce run` is a tree-walking interpreter, there is no bytecode VM and no JIT
  (`luce/src/main.lucb:517–531`, `luce/docs/DESIGN.md:35–45`); `luce build` writes Base source
  and runs `luce-base` as a subprocess; `luce-base` produces assembly text and runs the system
  `as` and `ld`/`cc` (`luce-base/src/main.lucb:614–747`). Native targets: arm64-macos,
  x86_64-linux, x86_64-windows only (`luce-base/src/back/target.lucb:94–110`). No encoder that
  could emit machine code into memory, no `MAP_JIT`/`PROT_EXEC` use anywhere.
- Base's native backend is near C on array kernels (`luce-base/docs/NATIVE-PERFORMANCE.md`:
  float array transformation 1.51× Clang `-O3`, integer sum 1.26×), auto-vectorizes counted
  loops over contiguous slices (`luce-base/src/back/opt/vectorize.lucb`) and has 128-bit
  vector types (`f32[4]`, `base.md` §5.12: lane-wise `+ - * /`, `mul_add`, `sum/min/max`; no
  lane-wise compare yet).
- `luce-js` (QuickJS in Base, 70k lines) proves an interpreter in Base: `match` over a dense
  `u8` opcode is a jump table since Luce 0.8.12; `memory.frame` gives bounded alloca; it runs
  at 1.1–8× C QuickJS, geometric mean 2.86 (`luce-js/docs/PERFORMANCE.md:75–76`).
- geocore has a persistent pool (`luce-geocore/src/core/parallel.lucb`: `parallel_for(count,
  grain, body, context)`, workers = CPUs−1, grain 65536 for points in current verbs) and
  columnar attributes that are already the layout a column interpreter wants (one contiguous
  64-byte-aligned `Column[u8]` per attribute, `core/attributes.lucb`, `core/shared.lucb`).

### 5.2 Options compared

| | (a) Native compile per cook | (b) Column interpreter in Base | (c) JIT | (d) Hybrid |
| --- | --- | --- | --- | --- |
| Per-point speed, 1M pts, 1 thread | 0.45 ms (measured) | 5–6 ms (measured, unoptimized prototype; ~3.5 ms once constants are scalar operands and copies are avoided) | ~0.5 ms (expected) | b now, a later |
| Same on 12 threads | ~0.05 ms | ~0.5 ms | ~0.05 ms | |
| Compile latency per code edit | 0.14 s + `as` + `ld` (measured); 0.16 s via `luce build` | < 1 ms | ~1–5 ms | |
| Runtime dependencies on the user's machine | `luce-base`, `as`, `ld` (MinGW on Windows), SDK path via `xcrun` on macOS | none | none | |
| Loading the result | needs a `dlopen` story (none in Base) or a worker process with shared-memory columns | in process | needs `MAP_JIT`/`PROT_EXEC`, code signing on macOS (hardened runtime), W^X | |
| Safety of user bugs | a trap kills the app unless out of process | every op is checked; cannot trap | same as b if the JIT is correct | |
| Work | compiler driver, library/dylib emission in luce-base, loader, worker protocol or shared memory, 3-OS toolchain packaging | lexer, parser, type checker, column IR, ~150 column ops, scheduler; all Base | all of b plus an arm64 and x86-64 encoder and a register allocator for the column IR | b + a |
| Determinism across thread counts | yes if written so | yes by construction | yes | |

(a) is where the raw speed is, but it buys 10× on a part of the cook that is already below
the cost of reading and writing the columns, and it costs a compiler on every user's machine.
(c) is the most work for the least gain over (b) at these sizes. (b) hits the bar on its own:
Houdini's VEX is itself a bytecode interpreter batched over elements
(https://www.sidefx.com/forum/topic/43672), so matching its architecture with Base's near-C
inner loops puts us in the same league. (d) keeps (a) as an option for the day a network is
frozen or published as a tool, where a 0.2 s compile and a shipped kernel are fine.

**Pick: (b), designed so (d) stays open** — the column IR is the contract; a later native
emitter can consume the same IR.

### 5.3 How the column interpreter is built

- **Front end** (Base): lexer, parser, binder (resolves `@` names against the input's
  attribute store and the node's parameters), type checker, lowering to a column IR: SSA
  registers typed `f32/i32/mask`, with vectors as 2–4 registers (struct-of-arrays stays
  struct-of-arrays all the way; no per-lane vec3 structs).
- **Program**: a flat instruction array `op, dst, a, b, c` (u16 fields), constants in a
  scalar table, uniforms (parameters, detail attributes, `@Frame`) in a scalar table filled
  per cook, and a column plan: which input columns to bind, which output columns to allocate,
  with their element types and widths.
- **Execution**: `parallel_for(element_count, chunk)` over geocore's pool; each work item
  takes a chunk of `chunk` lanes (4096 measured best; tune 1024–8192 so registers × chunk ×
  4 bytes fits L2), owns a per-thread register file (`registers × chunk` f32s, allocated once
  per cook per worker), copies or views the bound input columns for that chunk, runs every
  instruction as a tight slice loop (`for i in 0..<n: d[i] = a[i] * b[i]`, the shape the Base
  backend vectorizes), and writes its slice of the output columns. No locks: lanes write
  disjoint slots. Group-restricted runs compact the element indices of the group into a
  lane list first (or run masked when the group is dense).
- **Dispatch**: `match op` over a dense `u8`/`u16` opcode (jump table). At 4096 lanes a
  dispatch costs under 1% of the op; the per-element VM at 16 ms versus column at 5.4 ms shows
  why Houdini batches.
- **Ops**: about 150. Arithmetic per type, compares to masks, select, conversions, swizzles,
  math (`sinf` etc. through luce-std `math32` externs, with a note that an in-house
  vectorized `sin`/`cos`/`exp` in `f32[4]` lanes is the biggest later speed-up: libm `sinf` is
  ~2.5 ns per call and dominates the measured kernel), noise, hash random, gather/scatter
  with masks, group bit read/write, reductions for Detail. Each op is a small Base function
  over slices; adding one is one function plus a table row.
- **Never traps**: every slice index is proven by the chunk bound; gathers mask out-of-range
  indices; integer division by zero yields 0; float ops follow IEEE; loops are capped.
  Allocation failures surface as errors. The engine is fuzzed with random programs (the
  luce-js approach, `tests/`) so that the "cannot crash the app" promise is tested, not hoped.

### 5.4 What the numbers say about the bar

For `@P.y += sin(@P.x * 4) * 0.1` on 1M points: 2 arithmetic passes plus one `sinf` pass per
chunk, plus reading P (12 MB) and writing P (12 MB). Single thread about 4 ms (sin pass 2.5
ms dominates); on the pool under 1 ms for the kernel and about 2–3 ms for the column copy and
the new mesh (positions copy-on-write, `geometries/polygon/edits.lucb` `with_positions`).
Target: whole cook under 10 ms on the M4 Max; under 40 ms on a 4-core laptop.
For a noise displacement (`@P += @N * snoise(@P * 3.0) * 0.2`), Perlin 3D is ~40 flops plus 8
gathers of a 512-entry table: about 15–20 ms single thread, 2–3 ms on the pool. Target:
whole cook under 25 ms.

## 6. Packaging

Package boundaries rule: packages only for general technology; formats and apps own their
specifics.

- **`luce-kernel`** (new, Base, depends on luce-std only): the snippet language and the
  column interpreter: lexer, parser, checker, IR, scheduler, the builtin families that are
  not about geometry (math, vector, matrix, quaternion, interpolation, noise, random, color
  basics, strings and arrays later), the builtin registry so a host adds its own ops, and the
  column binding interface (a host hands it named typed columns and gets named typed columns
  back). It knows nothing about meshes. luced-2d can drive it for per-pixel expressions
  (a "pixel wrangle" over image tiles) and luce-image or luce-canvas for parameterized
  filters; luced-3d's parameter expressions (`$F`-style, which do not exist yet,
  `node_catalog.luc`) can use its scalar mode. The name says what it is: a kernel language
  run over columns. (`luce-expr` undersells the statement language; `luce-wrangle` is
  Houdini's word.)
- **`luce-geocore`** gains `src/code/`: the geometry bindings. It depends on luce-kernel:
  binding `@P` (positions are f32 relative to an f64 origin, not an attribute: `mesh.lucb`),
  attributes, groups, the geometry read ops (`point`, `primpoints`, `neighbours`,
  `nearpoints`, `xyzdist`, `intersect`, `volumesample`), the queued edit ops
  (`setpointattrib`, `addpoint`, `removeprim`), Run Over, and the cook entry
  `code.run(set, second, program, uniforms) -> GeometrySet!`. The noise used by Mountain and
  Scatter later comes from luce-kernel's noise module through this dependency, so there is
  one noise implementation.
- **`luced-3d`**: the node (parameters, stamps, worker plumbing, spare parameters), the
  editor UI, undo. All in Luce, calling `code.run` as it calls every verb.

Dependency direction: luced-3d → luce-geocore → luce-kernel → luce-std. luce-kernel never
imports geocore.

## 7. Integration in luced-3d

File references are to `/Users/sedov/Dev/luce_dev/luced-3d/src`.

### 7.1 Parameters

Today `Node.values` is 32 floats and `Node.texts` is exactly 3 strings set per kind in
`Node.init` (`network.luc:96–107`); the parameter panel has a one-line `text` row and no
multi-line kind (`parameter_rows.luc`, luce-ui `widgets/parameters`); project loading only
accepts single-line texts except Sketch's slot 0 (`project_graph.luc:151–155`). The Code node
needs:

- text slot 0: Group (as every node), value slot 15: Group Type (`node_catalog.luc:226–231`);
- a new value row: Run Over (menu Detail/Points/Vertices/Primitives/Numbers), and Count for
  Numbers;
- text slot 1: the code. Multi-line, so `project_graph.luc` must learn to save and load a
  multi-line text for this kind (the Sketch exception generalized to "kinds whose slot 1 is
  code"), and `compute_request.luc` must send it like any text (it already sends texts whose
  stamp changed; the body is Prism text, which handles multi-line strings);
- spare parameters from `ch()`: on every code change the UI thread parses the snippet (the
  luce-kernel parser is callable from Luce like any Base module) and collects `ch("name")`,
  `chv("name")`, `chi`, `chs` calls. Each unique name becomes a parameter row with the type
  the call implies: floats go into free `values` slots above the fixed ones (a small map
  `name → slot` kept on the node, e.g. in text slot 2 as `name=slot;...` or a new
  `list[str]` field), vectors take 3 slots, strings take a text slot (so the string case is S3
  and may need `Node.texts` to grow). Rows appear in the inspector below the code, in order of
  first use, with defaults 0 (a `ch("amp", 0.5)` default form is a cheap extension). Removing
  a `ch()` from the code hides the row but keeps the value until the node is saved, so a typo
  does not lose a tuned value.

### 7.2 Stamps

`stamp_of` hashes `(kind, enabled, values, texts, input stamps, sources, ...)`
(`stamps.luc:48`). The code is in `texts`, so it is stamped for free; spare parameter values
are in `values`. `@Frame`/`@Time` do not exist in luced-3d yet (no timeline; FBX/USD nodes
have private frame slots, `node_catalog.luc:265–283`): until there is a timeline, `@Frame`
binds to 0 and `@Time` to 0, and when a timeline arrives the frame must enter the stamp of
any node whose snippet references it (the parser reports which bindings a snippet uses, so
only those nodes become frame-dependent).

### 7.3 Worker and result store

Nothing new: `Node.compute` (`network.luc:155–236`) gets one more arm that calls
`code.run(...)`; the worker's `Computation.cook` (`compute_worker.luc:126–171`) mirrors it;
results go into the store by stamp as every other node's do. The kernel calls
`channel.progress()` between chunk batches so "Computation superseded" cancels a long run
(`compute_bridge.lucb:129–137`): `code.run` takes a progress callback and the pool loop polls
a cancel flag between chunks (geocore's `parallel_for` has no cancellation; adding an atomic
"stop" checked per work item is small).

### 7.4 Caching compiled programs

Compiling a snippet costs well under a millisecond, so a cache is about not re-binding
columns and keeping chunk scratch warm, not about compile time. A small LRU on the worker
keyed by `(code text hash, attribute signature of the input: names, domains, types, widths,
run-over)` → compiled program, like `groups/cache.lucb` keys group programs by `FullKey`.
Cache the parse (for the spare-parameter scan and error markers on the UI thread) by code
hash as well; the UI parse must not touch geometry.

### 7.5 Editor UI

luce-ui's `TextEditor` (`luce-ui/src/widgets/text_editor/module.lucb:46–136`) is a
multi-line code editor with highlights, folds, change bars, its own undo, and
`update_highlights(start, end, [Highlight], version)`; luced-2d's `script_editor.luc` wires
it to a TextMate grammar through luce-textmate. The Code node's inspector shows the editor
in place of the one-line text row (a new `code` parameter kind that opens
`TextEditor`; height grows with the panel, with a "Detach" into a floating Dialog as the
2D parameter dialogs do). Errors: on every edit the UI thread compiles the snippet against
the last known attribute signature of the input and shows errors as a gutter mark plus a
red underline on the span; `TextEditor` has no diagnostic API yet (decorations.lucb has
AI-lines, highlights, swatches, folds, change bars), so add one `set_diagnostics([Diagnostic
(line, start, end, message)])` decoration that draws a wavy underline and a hover message.
The node's `failure` string gets the same `line:column: message` text so it appears on the
node and in the notice (`network.luc:590–618`). Autocomplete (bindings from the input's
attributes, builtins with signatures) is a later stage over the same parser.

### 7.6 Geometry edits from parallel code (S3 design)

Each worker thread owns an edit queue: new points (position, parent for attribute
inheritance), new vertices, new prims (lists of point refs), removals (bit sets), and
scattered attribute sets (element, attribute, value). `addpoint()` returns a provisional
number `numpt + thread_base + local_index` so later `addvertex` calls in the same lane can
refer to it; after the parallel phase the queues are concatenated in thread order (thread
order is fixed by the chunk index, not by who finished first, which keeps results
deterministic), provisional numbers are renumbered, removals are applied last with
`kept_faces`/`compacted` (`geometries/polygon/subset.lucb`), and the attributes of new
elements are filled through `TopologyBuilder` parents (`verbs/builder.lucb`). This is the
Houdini batching (reads, then creates, then sets on new geometry, then deletes).

### 7.7 Undo

Parameter and text edits are whole-graph snapshots through `perform` (`workspace.luc:473`,
`node_commands.luc:256–268` `set_text`). A code editor commits on every keystroke would make
one undo step per character and a recook per keystroke. Policy: the editor keeps its own
keystroke undo (`TextEditor` has it); the node text commits (one `perform("Change Code")`,
one recook) on focus loss, on Cmd/Ctrl-Enter, and after a 400 ms pause in typing when the
snippet compiles clean. A snippet that does not compile never recooks; the previous result
stays with the error shown.

### 7.8 Determinism and threading

Results must not depend on the number of workers or on scheduling. The engine guarantees it
by: lanes map to element indices, not to threads; `rand(seed)` and noise are pure hashes of
their arguments (a per-element random is `rand(@ptnum + seed)`, as in VEX; never a shared
PRNG); reductions for Detail (`sum`, `min`, `max` over a column) use a fixed tree order;
edit queues concatenate in chunk order (§7.6). `printf` output is collected per chunk and
emitted in element order, capped at some KB.

### 7.9 Freeze

`toggle_freeze` cooks synchronously and writes the result file; the frozen stamp replaces
the input-dependent stamp (`cache_node.luc:49–59`, `stamps.luc`). A frozen Code node
therefore stops recompiling and running; editing its code while frozen is the same as editing
any frozen node's parameters (the stamp ignores them until unfrozen). Nothing special beyond
one thing: the "native compile later" tier of §5.2 (d) is exactly the frozen/published case,
so if it is ever built, Freeze is where it plugs in.

### 7.10 Edit node step

The owner mentioned a Code step in Edit nodes. `EditStep` (`edit_operations.luc:14–47`) has
one free text (`group`) and a numbers list, keyed by hash; the worker replays steps from
checkpoints. A Code step fits as a verb name `"Code"` whose code text travels in a new
`text` field of the step (changing `key`, serialization in `project_graph.luc:108–124` and
the list sharing in `compute_request.luc`). Stage 2+; the node comes first.

## 8. Staged build plan

Each stage ends with `luc test` green in every touched package, the benchmarks below run
with `tools/` scripts kept in the package, and a release batch (owner rule: batch releases).

### Stage 1: minimal useful wrangle

Scope: luce-kernel package with the front end, column IR and interpreter; float/int/vec2/3/4
types; bindings `@P @N @Cd @uv` and custom attributes created by writing; groups read/write
(`@group_x`); `@ptnum @numpt @primnum @numprim @vtxnum @elemnum`; `ch* ()` with auto spare
parameters; math, vector, interpolation, `rand`, Perlin `noise`/`snoise`, `printf`, `getbbox`;
Run Over Detail/Points/Vertices/Primitives/Numbers; `if`/`elif`/`else`, uniform `for`, masked
per-lane `for` with cap; errors at line:column; geocore `src/code/` bindings for meshes and
point clouds; luced-3d node, inspector code editor with diagnostics, undo policy, stamps,
project save/load of multi-line text.
Deliverables: `luce-kernel` 0.1 (docs: language reference with the Python/VEX framing,
builtin table generated from the registry), geocore `code` module, luced-3d Code node, a
`docs/CODE.md` user page in luced-3d.
Tests: luce-kernel unit tests per op against scalar references; a conformance suite of
snippets with expected columns (including VEX-compatibility cases: `noise` range, `fit`,
`rand` distribution); fuzzing of random programs (must never trap); geocore tests for
binding every attribute type/domain and for group restriction; luced-3d headless test that
builds a 1M-point grid and runs the two benchmark snippets.
Benchmarks (M4 Max, 1M points, whole cook on the worker): `@P.y += sin(@P.x*4)*0.1` ≤ 10 ms;
`@P += @N * snoise(@P*3)*0.2` ≤ 25 ms; `@Cd = vec3(rand(@ptnum))` ≤ 8 ms; empty snippet over
1M points ≤ 3 ms (measures binding and copy overhead); compile+bind of a 50-line snippet
≤ 2 ms. Also on the Windows and Linux test machines (memory: WINDOWS/LINUX test sessions).

### Stage 2: reading geometry and the second input

Scope: `point/prim/vertex/detail()` gathers with per-lane indices, `@opinput1_x`, topology
reads (`primpoints`, `pointprims`, `neighbours`, `vertexpoint`...), `nearpoints`/`nearpoint`
(a k-nearest and radius query in geocore built on `PointHash` cells or a new kd-tree),
`xyzdist`+`primuv` (closest point with uv from the BVH, attribute interpolation),
`intersect` with hit position and uv, `setpointattrib`-family scattered writes (queued),
`addattrib`; matrices (mat3/mat4), quaternions, `maketransform/lookat/dihedral`, fractal
and simplex noises, curl noise, color basics; `volumesample`.
Tests: gathers against masks and out-of-range; nearpoints against brute force; xyzdist
against `surface_distance`; scattered writes ordering (last writer per element is the
highest lane index, documented).
Benchmarks: `nearpoints` radius query with ~10 neighbours over 1M points ≤ 80 ms; `xyzdist`
of 1M points against a 100k-triangle mesh ≤ 120 ms.

### Stage 3: editing geometry

Scope: `addpoint/addprim/addvertex/removepoint/removeprim/removevertex` with per-thread
queues and the deterministic apply of §7.6; user `func` in snippets; `while`; `uniqueval`,
`findattribval`, `idtopoint`; half-edge functions; noise derivatives, Worley/Voronoi; Code
as an Edit step.
Tests: a snippet that scatters N points per source point reproduces a Copy/Scatter result
bit for bit at any worker count; removal + creation in one snippet; attribute inheritance of
new elements.
Benchmarks: 1M `addpoint` calls ≤ 60 ms; `removepoint` of half of 1M ≤ 20 ms.

### Stage 4: strings and arrays

Scope: ragged per-element arrays in geocore (`f[]@`, `v[]@`), array builtins, string
columns with interning, `sprintf`, `re_*` via luce-regex, `s@name` writes, `chs`.
Tests: VEX-compatible string and array cases.
Benchmarks: 1M `s@name = sprintf("piece_%d", @primnum // 100)` ≤ 60 ms.

### Later (not scheduled)

Autocomplete and hover docs in the editor; a pixel mode for luced-2d; vectorized
`sin/cos/exp` in `f32[4]` lanes (expected to double the speed of trig-heavy snippets);
the native-compile tier for frozen or published networks; `@Frame` once a timeline exists.

## 9. Risks and open questions for the owner

1. **Syntax: Luce-like, with `@` bindings.** The doc assumes Luce indentation syntax plus
   Houdini's `@name`, `f@`, `v@` prefixes and `ch()`. A VEX user gets the `@` forms but not
   braces and semicolons; a Luce user gets everything except `@`. Confirm this is the mix
   you want, or whether the Code node should accept VEX's C syntax too (a second parser over
   the same IR, maybe 1,500 lines; cheap to add later if users ask).
2. **Precision: f32 columns.** Geometry attributes are f32 (positions f32 around an f64
   origin). The engine computes in f32; literals are f32. A `--precise` f64 mode is possible
   but doubles memory and halves SIMD width. Default f32 unless you say otherwise.
3. **A new package, `luce-kernel`.** It is general (any columnar data; luced-2d pixels), and
   geocore would depend on it for noise. The alternative, putting the interpreter inside
   geocore, makes luced-2d import geometry for pixel expressions. Confirm the package and its
   name (memory: package creation is authorized; this is a confirmation of the boundary).
4. **Growing `Node.texts` beyond 3 strings** and allowing multi-line text in project files
   touches `project_graph.luc`, `compute_request.luc` and the inspector. Other sessions edit
   these files; this work should land in one small patch early, before the node itself, with
   a heads-up to peers (memory: new rules land last / warn peers).
5. **`@Frame`/`@Time` have nothing to bind to** until luced-3d has a timeline. Stage 1 binds
   them to 0 and documents it. Say if a timeline should come first.
6. **Edit step vs node.** The node first; the Edit step in stage 3. Say if the order should
   flip.

## Appendix A: benchmark details

Scratch directory (not in any repo):
`/private/tmp/claude-501/-Users-sedov-Dev-luce-dev/26944722-c0bc-4a1f-9a03-297d52283e2a/scratchpad/code-node/`.
Host: Apple M4 Max, 16 cores, macOS 24.6.0, dev toolchain `~/.local/bin` (luce 0.14.0,
luce-base 0.39.0). All times are wall clock; one thread unless said.

- `hello.luc`, `luce run`: under 10 ms per run (the `time` resolution floor), three runs.
- `loop.luc`: 1M-element `list[float]` setup then one pass of `py[i] += (x - x*x*x*0.1666)*0.1`
  with `x = px[i]*4`. `luce run`: 1.00 s setup only, 2.25 s with the pass → 1.25 s per
  1M-element pass. `luce build --native --release`: 0.16 s compile; the binary runs the pass
  in about 10 ms (0.18 s vs 0.03 s process totals are dominated by process start and list
  setup, so the pass itself is below the resolution; the Base kernels below are the real
  native number).
- `kernel.lucb` (with `sinf`), `luce-base build --native --release` compile 0.14 s wall,
  `--backend=c --release` 0.44 s: per round, 1M points: fused 2.5–2.7 ms; op-at-a-time over
  whole columns 5.2–5.5 ms; chunked 1024 4.7 ms; per-element switch VM 4.8–5.6 ms (libm
  `sinf` dominates all four). Through the C backend (clang): 1.7–2.0 ms for all four.
- `kernel2.lucb` (no libm, 7 ops): fused 0.45–0.5 ms; whole-column passes 3.4–4.3 ms;
  chunked 3.9–4.5 ms; per-element generic register VM 16–17.5 ms; column VM with computed
  indices (not vectorized by the backend) 15.3–15.5 ms.
- `kernel3.lucb` (same program, column VM with slice-typed op functions): chunk 256 →
  5.9–11 ms, 1024 → 5.5–8.9 ms, 4096 → 5.4–7.8 ms over three rounds (first round cold); the
  12 passes per chunk include 5 setup copies/fills the real engine will not do (constants as
  scalar operands, views instead of copies), so about 3.5 ms is the expected single-thread
  figure for 7 ops.

## Appendix B: code references used

- luced-3d: `src/network.luc` (`Node`, `compute`, `cook`, errors), `src/compute_worker.luc`,
  `src/compute_bridge.lucb`, `src/compute_request.luc`, `src/result_store.luc`,
  `src/stamps.luc`, `src/node_catalog.luc`, `src/parameter_rows.luc`, `src/inspector.luc`,
  `src/geometry_nodes.luc`, `src/node_evaluation.luc`, `src/cache_node.luc`,
  `src/edit_operations.luc`, `src/edit_steps.luc`, `src/project_graph.luc`,
  `src/node_commands.luc`, `src/workspace.luc`, `src/history.luc`.
- luce-geocore: `src/core/attributes.lucb`, `core/attribute_ops.lucb`, `core/shared.lucb`,
  `core/parallel.lucb`, `core/hash.lucb`, `core/bits.lucb`, `math/vector.lucb`,
  `math/matrix.lucb`, `geometries/polygon/mesh.lucb`, `access.lucb`, `attributes.lucb`,
  `edits.lucb`, `subset.lucb`, `groups.lucb`, `geometries/topology/connectivity.lucb`,
  `geometries/triangle_index.lucb`, `geometries/point_hash.lucb`, `fields/grid.lucb`,
  `fields/mesh_distance.lucb`, `groups/program.lucb`, `groups/evaluate.lucb`,
  `groups/cache.lucb`, `verbs/builder.lucb`, `verbs/point_verbs.lucb`,
  `geometries/attribute_kernels.lucb`, `set_verbs/attributes.lucb`.
- luce: `src/main.lucb`, `src/hir/interp/interp.lucb`, `src/back/package.lucb`,
  `src/support/sandbox.lucb`, `docs/DESIGN.md`, `docs/luce.md`, `docs/guide/topics/17-tools.md`.
- luce-base: `src/main.lucb`, `src/back/backend.lucb`, `src/back/target.lucb`,
  `src/back/opt/vectorize.lucb`, `docs/language/base.md` (§5.12 vectors, §12 memory.frame),
  `docs/NATIVE-PERFORMANCE.md`, `benchmarks/native_vs_c/`.
- luce-std: `src/math.lucb`, `src/math32.lucb`, `src/random.lucb`, `src/parallel.lucb`.
- luce-js: `src/engine/interpreter.lucb`, `src/host/native_modules.lucb`,
  `docs/PERFORMANCE.md`, `docs/COMPILER-REQUESTS.md`, `README.md`.
- luced-2d: `src/script_host.luc`, `src/script_editor.luc`, `scripting/luced.luc`,
  `docs/SCRIPTING.md`.
- luce-ui: `src/widgets/text_editor/module.lucb`, `decorations.lucb`; luce-textmate
  `src/textmate.lucb`.
