# Script node: Houdini's Python SOP, in Luce Base

Research and design, 2026-10-09. Nothing here is built yet. The owner's request:

> "Once you're done with this we can work on creating Script node. This mode will be
> similar to Python node in Houdini. It more of a general API mode (still luce-base not
> Python) that can create objects and do more high level things than our Wrangle node. [...]
> Our advantage is of course that it's luce-base and is extremely fast. We can probably do
> package import and for example open a Maya file or jpeg and read from it and based on
> that create something."

Measurements were taken on an M4 Max (16 cores) with luce-base 0.39.0, luce 0.14.0 and
luc 0.24.0 from `~/.local/bin`. The probe sources are in Appendix A.

## 1. Decision in one page

**What the node is.** The Code node runs a snippet once per element, in luce-kernel's
column interpreter, with no imports. The Script node is different on every one of those
points:

- It runs one `cook` function once per cook, over the whole geometry, as ordinary
  imperative code.
- It is compiled by the real Luce Base compiler. Pointers, allocation, threads, loops of
  any shape and any Base package are all allowed.
- It builds and edits geometry through a geometry API, and can call any verb the node
  menu has.

Typical uses are reading a JPEG, a CSV or a Maya file and building geometry from it,
recursive or whole-mesh algorithms, and chains of verbs driven by data.

**Recommended execution model: a compiled script host process.**

1. The script, plus a small generated `main`, is built by `luc`/`luce-base` into a native
   executable. Dependencies are the script's own package list plus a pinned luce-geocore.
2. The executable is cached under a content hash of everything that affects the binary:
   the script text, the resolved dependency lock, the toolchain version and the target.
3. luced-3d's compute worker starts it as a child process and keeps it alive between
   cooks.
4. Each cook sends one request line. Geometry goes in and out as `.prism` files in a run
   directory; shared memory comes later.
5. If the script traps, crashes, runs past its time limit or is superseded, the process
   ends. The node fails with the script line the trap names, and the next cook starts a
   new process.
6. On macOS and Linux the host runs inside the same OS sandbox that `luce run --sandbox`
   already uses, with permissions granted per node.

**Why this model and not an in-process native library.**

- The probe in §3.5 confirms that luce-base's object code can be linked into a `.dylib` by
  hand and called through `dlopen`. But a Base trap is "never recoverable" (base.md §11.5):
  the probe's out-of-bounds index ended the host process with exit 1.
- The compute worker is a thread in the app (`compute_bridge.lucb:331`), not a process. A
  script loaded in process can therefore take the whole app down.
- In-process loading has further problems. luce-base has no shared-library output (`--lib`
  makes only `.a`, `main.lucb:858`). The plugin would carry a second copy of the runtime,
  luce-std and luce-geocore, each with its own globals, alongside the app's copy.
- A process boundary fixes all of that, and costs little at the sizes measured.

**Measured numbers that decide it:**

| What | Time |
|---|---|
| Rebuild after editing a script that imports luce-geocore | **0.65 s** |
| Rebuild after editing a script that imports luce-image (JPEG and the rest) | **0.56–0.66 s** |
| Building a new set of dependencies from an empty build directory | 1.2–1.3 s |
| Unchanged rebuild | 0.22 s |
| `luc check`, for diagnostics while typing | **0.14 s** |
| Tiny program with no dependencies | 0.12 s cold, 0.05 s from the object cache |
| Tiny program by hand: emit 0.03 s + `as` 0.04 s + `ld -dylib` 0.02 s | about 0.09 s |
| Process spawn and exit, tiny executable | **1.5 ms** median |
| `.prism` save of a 1M-point, 1M-quad grid (56 MB) | 5.5 ms |
| `.prism` load of the same grid | 11 ms |
| Generating that grid with `MeshPrimitives.grid` | 10 ms |

A cook of a 1M-quad mesh therefore spends about 35 ms crossing the process boundary
(save, load, save, load). Small meshes cross in under 3 ms. The script code itself runs at
native Base speed, on every core if it uses luce-std's parallel loops. Houdini's Python SOP
runs single threaded under the GIL, with a C++ call per element.

**Why not the alternatives:**

- **Compile on every keystroke:** no. A check runs at each pause in typing (0.14 s); a
  build runs when the text is committed (0.65 s). The last good result stays on screen
  while the build runs.
- **Extend luce-kernel's interpreter to call packages (c):** no. Package code uses
  pointers, allocation and loops the column IR cannot express. Running it would need a
  full Base interpreter, and the only one we have (`luce run`) runs Luce only and is about
  2,000× slower (CODE-NODE.md §4.1).
- **A Luce-language script through `luce run --sandbox`, as luced-2d does:** no. It is an
  interpreter and cannot import Base packages.

**The toolchain is already on the machine.** `luc install` builds luced-3d from source, so
every installed luced-3d has `luc`, `luce-base` and the system assembler and linker next
to it: Xcode command line tools, binutils, or MinGW GCC on Windows. CODE-NODE.md §5.2
rejected native compilation because of the toolchain, but that objection does not apply to
an app installed through luc.

## 2. Houdini's side: what to match

Sources: sidefx.com/docs/houdini, now labelled Houdini 22.0. The pages used are
`nodes/sop/python.html`, `hom/pythonsop.html`, `hom/hou/Geometry.html`,
`hom/hou/SopNode.html`, `hom/hou/SopVerb.html`, `model/verbs.html`, `hom/hou/session.html`,
`hom/hou/NodeError.html` and `hom/hou/NodeWarning.html`.

### 2.1 The Python SOP

Houdini has two forms:

- **The "Python" SOP** in the Tab menu, "a quick ad-hoc script". Its parameters are
  **Python Code** and **Maintain State**. With Maintain State off (the recommended
  default), the interpreter is cleared between cooks.
- **A Python-defined SOP type**, an asset with Operator Definition = python. Its code is
  stored in the asset's `PythonCook` section. With zero inputs the node is a source
  (generator).

How a cook works:

- `geo = hou.pwd().geometry()` is the node's output geometry. It is writable, already
  frozen, and starts as a copy of input 0, or empty when nothing is wired.
- Other inputs are `hou.pwd().inputs()[i].geometry()` or `SopNode.inputGeometry(i)`. They
  are read-only; editing one raises `hou.GeometryPermissionError`.
- Parameters are read with `evalParm("name")` or `parm("name").eval()`. A Python-defined
  type gets them from its interface; the plain Python SOP gets them as spare parameters.
  The docs warn: "Do not set node parameters inside a Python SOP."

Time:

- `hou.frame()` gives the frame. A node that reads the frame or animated parameters
  becomes time dependent automatically. The docs do not say this; the forum does.
- `SopVerb.executeAtTime(..., add_time_dep)` passes time dependence on explicitly.

Errors:

- An uncaught exception turns the node red, and the info window shows the traceback with
  line numbers in the code.
- `raise hou.NodeError("msg")` fails the node with only the message.
- `raise hou.NodeWarning("msg")` lets it cook with a warning.
- `node.addWarning` and `addMessage` add badges without raising.
- `hou.updateProgressAndCheckForInterrupt()` inside loops lets the user press Esc.

State between cooks:

- `node.setCachedUserData(name, any_object)` keeps a value, not saved in the .hip file.
- `hou.session` is a module saved in the .hip file.
- Maintain State keeps the interpreter between cooks.
- Data ids are bumped for the user automatically.

### 2.2 `hou.Geometry`

- **Create:**
  - points: `createPoint`, `createPoints(positions)`;
  - polygons and curves: `createPolygon(is_closed)` + `poly.addVertex(pt)`,
    `createPolygons(point_lists)`, `createNURBSCurve`, `createBezierCurve`;
  - surfaces: `createMeshSurface`, `createNURBSSurface`;
  - volumes and solids: `createVolume(xres, yres, zres, bbox)`, `createTetrahedron`;
  - packed primitives: `createPacked(typename)`, then intrinsics such as
    `unexpandedfilename`; `createPackedGeometry(geo)` for embedded geometry;
    `PackedPrim.setTransform(m4)`.
- **Attributes:**
  - `addAttrib(hou.attribType.Point|Prim|Vertex|Global, name, default)`: the default fixes
    the type and tuple size;
  - `addArrayAttrib`;
  - `setAttribValue` and `attribValue` on Point, Prim and Vertex;
  - `setGlobalAttribValue`.
- **Bulk access, the fast path:**
  - `pointFloatAttribValues(name)` returns a flat tuple;
  - `pointFloatAttribValuesAsString` returns bytes for numpy;
  - `setPointFloatAttribValues` and `setPointFloatAttribValuesFromString` (any buffer);
  - the same in Int and String forms, and for prims and vertices.
  The docs call these "much faster than looping over all the points".
- **Groups:** `createPointGroup(name)`, `createPrimGroup`, `createEdgeGroup`,
  `createVertexGroup`; `group.add(...)`; `globPoints(pattern)`.
- **Whole-geometry operations:**
  - `loadFromFile(path)` reads any File SOP format; `saveToFile(path)` picks the format by
    extension;
  - `merge(geo)`, `copy(geo)`, `clear()`;
  - `transform(hou.Matrix4)`, `transformPrims`;
  - `deletePoints`, `deletePrims(prims, keep_points)`;
  - `intrinsicValue` and `setIntrinsicValue`;
  - `freeze()`.
- **Verbs:**
  - `hou.sopNodeTypeCategory().nodeVerb("box")`, `verb.setParms({...})`,
    `verb.execute(dest_geo, [inputs])`;
  - `hou.Geometry.execute(verb, inputs)` returns a new geometry, so calls chain:
    `geo.execute(subdivide).execute(subdivide)`;
  - only compilable SOPs have verbs.

### 2.3 What people use it for, and what they complain about

Uses:

- CSV and JSON to points and attributes (Table Import is the native CSV node);
- images through PIL or OpenCV driving points or Cd;
- parsing their own file formats;
- recursive and procedural loops;
- calling outside libraries or services;
- exporters (Labs' CSV Exporter).

Complaints:

- per-element HOM calls are slow;
- the GIL makes it effectively single threaded;
- Python SOPs cannot be compiled, so they are left out of compiled blocks and
  multithreaded For-Each loops;
- the advice is to move hot code to VEX, verbs or inline C++.

Our version keeps the convenience (imports, an imperative API, verbs, file I/O) and removes
the cost: the code is native, multithreaded where it chooses, and can touch columns
directly instead of through tuples.

## 3. Our side: what exists

### 3.1 The Code node and luce-kernel

- `luced-3d/src/code_cook.luc` passes the node's texts (body, header, spares, ramps), the
  value slots and the clock to `Code.cook` (luce-geocore `src/code/cook.lucb`, `run_code`).
- `code_node.luc` turns literal `k.f32("name", 0.2)` calls into spare-parameter rows. It
  uses `Code.check`, which reports parameter names, components, defaults and
  `reads_time()`. Rows keep their slots by name while the code changes.
- `failure_place` parses "line N, column M" from a cook failure, so the editor can
  underline the line.
- `code_editor.luc` is luce-ui's `TextEditor` with Luce highlighting and
  completion/hover from `Code.complete` and `Code.hover`. Text is committed after a
  400 ms pause.

luce-kernel's `lower.compile` checks the snippet with luce-base's embedded checker
(`embed.Library`, about 11 ms once, then about 0.1 ms per check) and lowers the typed tree
to a column SSA IR. The column interpreter runs that IR in parallel chunks and never
traps.

**Why the Code node has no imports:**

- `embed.check_root` resolves imports under a fixed root and nowhere else
  (luce-base `docs/EMBEDDING.md`). The root holds only luce-kernel's `lib`, luce-std's
  `math`/`math32` and the host's stubs.
- The lowering accepts a subset of Base: no pointers, allocation, `extern`, threads, files,
  failure or generics. It refuses standard modules by name.
- A package function's body uses exactly those things, so the column IR could not run it.

The Script node keeps the Code node's conventions (`k`, spare parameters from literal
calls, `printf`-style console, line-mapped errors) and drops the subset.

### 3.2 luce-geocore surfaces a script would call

- **`GeometrySet`** (`geometry_set/api.lucb`):
  - `of_mesh`, `mesh`, `with_mesh`, `merged`, `transformed(translation, rotation, scale)`,
    `with_instance(child, t, r, s)` (the packed-primitive equivalent), `realized`,
    `blasted(expression, keep)`;
  - point clouds: `with_cloud_of`, `cloud_point`;
  - `bounds`, `paths`, `description`.
- **`Mesh`** (`geometries/polygon/access.lucb`):
  - counts, `point(i)`, `face_size`, `face_point`, `face_normal`, `face_center`,
    `closest_face`, `ray_face`;
  - bulk spans `point_span() -> const Float3[]`, `offset_span`, `corner_span`, and more.
- **`MeshBuilder`** (`point`, `face`, `corner`, `copy_points`, `finish`) and
  **`MeshPrimitives`** (`grid`, `sphere`, `cylinder`, `torus`, `Mesh.cube`).
- **Verbs.** There are 30 mesh verbs in `verbs/api.lucb`, from Transform and PolyExtrude
  to Bevel, Bridge, Mirror and PolyDraw. There are 25 set verbs in `set_verbs/` for curves,
  SDFs, volumes and conversions.
  - All of them run through `GeometryVerbs.run(name, input, second, group, group_type,
    numbers: const f64[])`.
  - `VerbCatalog` describes each parameter: label, kind, default, components and choices.
  - That catalog is what turns verb names and parameter labels into the flat number array.
- **`GeometryFile.save(set, path)` / `load(path)`** (`geometry_files/api.lucb`) write and
  read a whole set as a `.prism` crate.
- **Format readers** are Base packages with a Base-facing `kernel` module next to their
  Luce face: `luce-fbx` (7.1k lines), `luce-usd` (12.8k), `luce-obj`, `luce-ply`,
  `luce-step` and `luce-cad`.
- **Images:** `luce-image`'s `image.Image.open(path)`, Pillow-like:
  `width`, `height`, `channel_count`, `get_sample(x, y, c)`, `getpixel`.
  `luce-exif` reads photo metadata. `luce-json` reads and writes JSON. There is no CSV
  package; `strings.split` and `parse_f64` in luce-std are enough (§7.3).

### 3.3 The compute worker

`compute_worker.luc` is the worker's DAG mirror and result store, keyed by node stamp.
`compute_bridge.lucb` runs it on **a thread** ("luced-3d compute") inside the app's
process. Requests are text deltas, and only the newest is cooked; `superseded()` lets a
cook stop early. A cook failure is stored under the node's stamp and shown on the node.

So "running the script in the worker" means running it on that thread in the app's
process, where a trap ends the app. A script can run *from* the worker, which starts the
child and waits on it, but not *in* it.

### 3.4 luce-base: compile, embed, load

**Pipeline** (`luce-base/src/main.lucb`):

- check, lower to IR, optimize, emit assembly text (arm64 or x86-64);
- the system `as` (`assemble_one`);
- the link: Apple's `ld` with the SDK from `xcrun` (`assemble_and_link`, :628), or the C
  driver on Linux and Windows (`link_with_driver`, :717; `gcc` from MinGW on Windows);
- object caching per build key and per content-addressed piece (`-n.o`, `-p.o`).

**No JIT and no in-process code generation.** Nothing emits machine code into memory, and
nothing uses `MAP_JIT` or `PROT_EXEC`.

**No shared-library output.**

- `--lib` makes `NAME.a` plus a header (`build_library`, :858).
- base.md §17.6 says "`luce build --lib` produces a static or shared library", but the
  shared form is not implemented.
- Base programs do call `dlopen`/`LoadLibraryW` through `extern`
  (`luce-gpu/src/gpu/vulkan/entry.lucb` loads Vulkan that way), so loading is possible;
  producing the library is the missing part.

**Embedding (`docs/EMBEDDING.md`):**

- `embed.check_root(root, entry)` and `embed.Library` check source in process and return
  the typed tree and diagnostics. That is all the embedding offers: no codegen, no
  linking.
- Two checks may not run at the same time in one process.

**Runtime start-up.**

- `memory.startup()` sets `memory.heap` and the thread's allocator (`std/memory.lucb:379`).
  The startup shim runs it before `main`, and `thread.spawn` runs it in each new thread.
- A function called from outside, as in a dylib, must call it first. Otherwise `new`
  traps with `memory.unset`, which the probe hit.

**Traps.**

- A trap prints `trap: file:line:column: message` and exits with status 1; it is "never
  recoverable; `defer` does not run" (base.md §11.5).
- luce-std's `crash` module can run hooks and write a report, but the process still ends.

### 3.5 What the probes showed

| Probe | Result |
|---|---|
| `luce-base build` of a 12-line program, release | 0.12 s cold; 0.05 s with the object cache |
| `--emit=asm` of the same | 0.03 s, 9,717 lines (the runtime included) |
| `as` + `ld -dylib` of that assembly | 0.04 s + 0.02 s |
| `dlopen` of that dylib from a host (Python `ctypes`), calling an `export func` | works: `script_cook(1000000)` returns the right sum |
| The same, in a function that allocates with `new` | traps `memory.unset` unless the entry calls `memory.startup()` first; then works |
| The same, in a function that indexes out of bounds | `trap: main.lucb:19:5: index out of bounds`, and **the host process exits with status 1** |
| `luc build --release`, tool importing luce-geocore: empty build dir / no change / edited | 1.20 s / 0.22 s / 0.65 s |
| `luc build --release`, tool importing luce-image: empty build dir / no change / edited | 1.31 s / 0.22 s / 0.56–0.66 s |
| `luc build` (debug), edited | 0.65 s (no faster than release) |
| `luc check` with luce-geocore or luce-image | 0.14 s |
| Running the luce-image tool on a 700×600 JPEG, summing every sample with `get_sample` | 0.10 s for the whole process |
| Spawn and exit of the tiny executable, median of 20 | 1.5 ms |
| `MeshPrimitives.grid(2.0, 1000)` (1,002,001 points, 1M quads) | 10 ms |
| `GeometryFile.save` of it (56 MB `.prism`) / `load` | 5.5 ms / 11 ms |

**Where an edit's 0.65 s goes.** luce-base generates the whole program again on every edit
and reuses only unchanged assembled pieces (memory note "build speed plan", C). A
per-function generation cache, or a resident compiler that keeps the checked dependency
modules, would bring an edit closer to the 0.05–0.1 s a dependency-free program takes.
That is compiler work, the language session's to schedule (§10, Q5).

Windows and Linux were not measured in this pass. Windows builds of luced-3d run about 3×
slower than macOS (memory: 24 s fresh against 7 s), and x86-64 code generation trails
arm64. Expect about 1.5–2 s per edit on the Windows laptop until those land.

### 3.6 Prior art: luced-2d scripting

`luced-2d/src/script_host.luc` and `docs/SCRIPTING.md` work like this:

- The script is a **Luce** program that imports `luced`.
- The editor writes it into `~/.luced-2d/run`, next to `luced.luc` (the API) and
  `document.luc` (a snapshot).
- It runs **`luce run --sandbox ROOT script.luc`** as a subprocess, using the tree-walking
  interpreter.
- The script asks the editor to do things by printing `@l2d` lines, one action per line,
  and the editor performs them as they arrive. Everything else printed goes to the
  console, and the whole run is one undo step.

The sandbox (`luce/src/support/sandbox.lucb`):

- On macOS it uses Seatbelt; on Linux, Landlock plus `no_new_privs` and a seccomp deny list.
- On hosts it does not support, it "fails closed". luced-2d then reruns the script
  unfenced and says so in the console (`script_host.luc:94–99`).
- Policy `luce-sandbox/1`: 30 s wall time, 10 s CPU, a 256 MiB arena, 1 MiB of output,
  16 MiB files, no network and no child processes.

What carries over to the Script node:

- the subprocess;
- a line protocol on stdout;
- the run folder;
- the sandbox and its fallback.

What does not carry over:

- The interpreter: it cannot import Base packages and is slow.
- The design where the host does the work and the script only sends commands. In
  luced-3d the script itself makes the geometry, natively.

## 4. Script node versus Code node

| | Code node (Wrangle) | Script node (Python SOP) |
|---|---|---|
| Runs | once per element, in parallel, no element sees another's writes | `cook(k)` once per cook, over the whole geometry |
| Language | a safe subset of Base, lowered to columns | all of Base: pointers, `new`, structs, generics, `thread`, recursion |
| Imports | none (lib and math are built in) | any Base package, listed on the node |
| Engine | luce-kernel's column interpreter, in the worker thread | a native executable, in a child process |
| Edit to result | ~0.1 ms check, ~1 ms lowering | 0.14 s check, 0.65 s build (cached by hash afterward) |
| Failure | a fault on a lane, reported as line + element | a trap ends the child: line + message; `k.error` fails cleanly |
| Geometry access | bound columns, `p.P`, `k.input(1)` reads | a mutable geometry, builders, bulk spans, verbs, files |
| Good for | per-point math on millions of elements, every frame | file-driven geometry, algorithms that need the whole mesh, verb chains, anything needing a package |

The two complement each other. A Script node reads a JPEG and builds a grid; a Code node
after it displaces the grid every frame at column speed.

## 5. Execution models

Criteria: compile latency while typing, cook speed, crash isolation (a trap must fail the
node, not the app), security (file and network access), platforms, and hot reload.

### (a) A native shared library loaded into the worker

The script is compiled with the real compiler into a `.dylib`, `.so` or `.dll`, cached by
content hash, `dlopen`ed by the worker, and its `export func script_cook(...)` is called.

- **Latency:** the same build as (d), 0.65 s per edit, plus loading.
- **Cook speed:** the best. There is no copy: the plugin gets the input's
  `GeometrySet*`.
- **Crash isolation: none.** A trap exits the app (measured). Stack overflow, a wild
  pointer or a double free does the same; with pointers allowed, those are the script's
  to make.
- **Security:** none beyond the app's own; a process cannot sandbox a library inside
  itself.
- **Platforms:**
  - luce-base cannot emit a shared library today. The hand link worked on macOS arm64,
    but Linux needs `-fPIC`-style code (the x86-64 emitter's relocation model was not
    checked), and Windows needs a DLL with an export table and its own TLS.
  - The plugin would link its own runtime, luce-std and luce-geocore. Their globals
    (`memory.heap`, interop type tables, the geocore thread pool, crash hooks) would exist
    twice. Objects crossing with `interop.Reference` carry type identities from the other
    copy.
  - Making the plugin bind to the app's copy instead needs `-bundle_loader` on macOS,
    `-rdynamic` exports on Linux and an import library on Windows. Base's `pub` symbols
    are hidden unless exported (§17.6), so the compiler would need a new mode.
- **Hot reload:**
  - Unloading is unsafe while any thread the script started still runs, or any callback
    it registered is still held. Loading each new build instead leaks the old code.
  - macOS caches a dylib by path, so every build needs a fresh path.
- **Verdict:** rejected as the default. It might return later as an opt-in "trusted,
  frozen" tier, once Base has a recoverable trap or a guarded-call primitive (Q6).

### (b) A child process per cook, geometry through `.prism` files

The worker writes the inputs to `.prism` files and spawns the cached executable with the
request. The child loads the inputs, runs `cook`, writes the output `.prism` and exits; the
worker loads the result.

- **Latency:** the same build as (d).
- **Cook speed:**
  - 1.5 ms spawn, plus runtime start, plus geometry I/O: about 35 ms for 1M quads round
    trip, under 3 ms for small meshes.
  - Each cook starts cold: files the script opens are read again, and nothing stays warm.
- **Crash isolation: complete.** The worker sees the exit status, reads the
  `trap: file:line:col: message` line on stderr and fails the node at that line.
- **Security:** the child can enter the Seatbelt or Landlock sandbox before it runs any
  script code.
- **Platforms:** an executable is what luce-base already builds on all three targets.
  Nothing new is needed.
- **Hot reload:** trivial. A new hash means a new executable.
- **Verdict:** the right first stage. (d) is the same thing, made persistent.

### (c) Extend luce-kernel's interpreter to call package code

- The column IR has no pointers, heap, failure or general loops, and package bodies use
  all of them. "Calling into packages" would mean either
  - an interpreter for all of Base (pointers into a byte heap, `extern` calls through a
    foreign-function shim, threads), which amounts to a second compiler backend plus a VM;
    or
  - a host binding by hand for every package function a script may use.
- The speed claim would be lost. A Base interpreter would land near luce-js's QuickJS
  numbers (1–8× C QuickJS), not native speed.
- **Verdict:** rejected. The Code node's subset exists because the interpreter is
  columnar; the Script node exists because it is not.

### (d) Recommended: a persistent compiled script host

(b) with three changes:

1. **One process per (node, build hash), kept alive between cooks.** A cook is one request
   line and one reply.
   - It saves the spawn and runtime start (about 2 ms).
   - Module-level state lives across cooks: an opened image, a parsed file, a
     spatial index. That is Houdini's Maintain State, and `k.keep()` makes it explicit
     (§7.6).
   - The process exits after 60 s idle, when its node is deleted, or when a new build
     replaces it. It is killed by PID when a cook is superseded or runs past its limit.
2. **Geometry through the run directory, then through shared memory.**
   - Stage 1 uses `.prism` files in `~/.luce/scripts/run/<pid>/`.
   - A later stage maps the files (luce-std has `files/mapping.lucb`), so a column is
     mapped instead of copied. Unchanged input columns already keep their `points_id` /
     `corners_id`, so a request can say "same input as last cook" and skip the transfer.
3. **A warm build service.**
   - The worker keeps one build in flight per node. A newer commit cancels the older
     build (kill by PID).
   - Builds of other nodes run in parallel up to the core count.
   - Later, a resident `luce-base` keeps the dependency closure checked, as
     `embed.Library` keeps the standard modules (Q5).

Against the criteria:

- **Latency:**
  - Each pause in typing runs a check: 0.14 s through `luc check` in the script's project
    today, and in process later (§9).
  - A commit (400 ms pause, blur, or Cmd-Enter, as the Code node does) runs a build:
    0.65 s, or 1.2–1.3 s for a new dependency set.
  - The node shows "Building…". Until the build finishes, the node keeps its last result,
    which is drawn as stale.
- **Cook speed:** native Base. The node's overhead is about 2 × (save + load) of the
  geometry that crosses.
- **Crash isolation:** complete, as in (b). Runaway loops hit the wall-time limit; the
  default is 30 s, set per node.
- **Security:** §5.1.
- **Platforms:** the three targets luce-base builds for, with the same toolchain luc
  already uses there.
- **Hot reload:** each build has its own executable path, and a new hash starts a new
  process.

### (e) Other options looked at

- **An in-process JIT.** None exists. One would need arm64 and x86-64 encoders, a
  register allocator for code in memory, W^X and `MAP_JIT` with code signing on macOS.
  Even then a trap still ends the process. It is weeks of compiler work for nothing (d)
  lacks.
- **Luce (full) scripts via `luce run`, like luced-2d.** Rejected: an interpreter, and no
  Base packages.
- **A thread with a trap hook.** The trap path has no hook that returns; the crash module
  can only run hooks and then exit. A Base feature to recover from a trap on a thread
  (`thread.guarded(func)`) would make (a) safe from traps, but not from memory errors in
  code that uses pointers. That is a language decision (Q6).

### 5.1 Security

A script is code the user, or whoever sent them the project file, wrote. It gets the
user's rights unless it is fenced.

- **Fencing.** macOS uses Seatbelt and Linux uses Landlock + seccomp, applied by the child
  itself before `cook` runs, as `luce run --sandbox` does. The confinement code lives in
  `luce/src/support/sandbox.lucb` + `sandbox_abi.c`. It should move to a luce-std module
  (`process.sandbox`) so the generated `main` can call it (Q3).
- **Grants per node.** The Script node lists what it may reach:
  - read: the paths its `k.file(...)` parameters name (an image, a CSV), the project
    directory, and the folders the user adds;
  - write: the run directory only, unless the user adds a folder;
  - network: off unless the user turns it on.
  A path parameter's file picker adds that file to the grants. The grants are saved in
  the project.
- **Opening a project.** A project from somewhere else whose Script nodes have never been
  built on this machine asks once: "This project runs 3 scripts. Build and run them?"
  Like Houdini's HDA trust, but explicit.
- **Windows.** The luce sandbox fails closed on Windows, so Script nodes there run
  unfenced, with the console saying so, as luced-2d does. A Job object still gives memory,
  CPU-time and child-process limits. AppContainer is the real fence and is open (Q3).
- **Resources, on every target:** wall time (default 30 s), memory (default the larger of
  8 GiB and half of RAM), output size, and no child processes.

## 6. How a cook runs

### 6.1 The script project

Each Script node's code becomes a small Luce Base package the app writes and luc builds:

```
~/.luce/scripts/build/<hash>/
    package.prisma        # kind "tool", entry src/main.lucb, the node's dependencies
    luc.lock              # written by luc lock; copied from the project when present
    src/main.lucb         # generated: the request loop, then calls script.cook
    src/script.lucb       # the node's code, byte for byte, so lines match
```

- `<hash>` is a SHA-256 of:
  - the script text;
  - the node's dependency list;
  - the resolved lock (the versions and content hashes luc resolved);
  - the luce-base version and the target;
  - the luce-geocore version the app was built with.
- The executable is `build/<hash>/build/script`.
- An LRU trims `~/.luce/scripts/build` at 2 GB (Q8).

Pinning luce-geocore to the app's own version keeps the `.prism` exchange and the verb
catalog identical on both sides. The app embeds that version at build time.

### 6.2 The request loop (generated `main`)

The protocol is lines on stdin and stdout, as luced-2d's `@l2d` is. Anything else the
script prints is console text.

```
-> @l3d cook 7 in0=/…/run/7-0.prism in1= out=/…/run/7-out.prism frame=24 time=1.0 fps=24
   params=/…/run/7-params.txt
<- (anything the script prints: console)
<- @l3d warning 7 12 5 "fewer than 3 columns on row 18"
<- @l3d progress 7 0.4
<- @l3d read 7 /Users/me/data/points.csv 1696830000 4812
<- @l3d done 7 ok
   (or: @l3d done 7 error 14 9 "the image has no alpha channel")
```

- Parameters travel as a small text file, one per line: name, components, values. The
  same names go into the Code node's value slots.
- A `read` line records every file the script opened through `k` (path, modification
  time, size). The node's stamp includes them, so editing the CSV recooks the node
  (§6.4).
- A trap writes `trap: script.lucb:L:C: message` to stderr and the process exits. The
  worker maps it to the node, then deletes the run files.

### 6.3 In the worker

`compute_worker.luc`'s `cook` handles a Script node like this:

1. Find the executable for the node's hash. If it is missing, ask the build service and
   fail this cook with "Building…" (see below).
2. Make sure a host process for the hash is running. Start it if not, recording its PID.
3. Write `in0` and `in1` with `GeometryFile.save` (skip when unchanged since the last
   request to the same process), write the parameters, send the request line.
4. Read lines until `done`, checking `channel.superseded()` between reads. When the cook
   is superseded, kill the PID and fail the cook with "Computation superseded", as other
   cooks do.
5. On `done ok`, `GeometryFile.load(out)` becomes the node's `GeometryData`; the console
   and the warnings go on it as `code_cook.luc` does. On error or exit, fail the node
   with the mapped line.

When the build finishes, the node is invalidated, so the cook runs again. The
`ResultStore` keeps the last good result under the old stamp, so the viewport keeps
showing it.

### 6.4 Stamps and time

The node's stamp combines:

- the build hash;
- the parameter values;
- the input stamps;
- the frame, when the script is time dependent;
- the files it read, when it read any.

The Script node is **time dependent** when its text calls `k.frame()`, `k.time()` or
`k.fps()`. The parse in §9.2 finds those calls. A "Time Dependent" toggle forces it either
way, because a script can reach time in ways a parse cannot see.

Houdini only marks a node time dependent when the code reads the frame. Recording the
files a script read is our addition: Houdini does not recook a Python SOP when its CSV
changes.

### 6.5 Threads inside a script

The script is a normal Base program. luce-std's `parallel` and geocore's pool are there,
and verbs run on every core as they do in the app.

- A script that loops over a million points can split the loop.
- The API's bulk spans (§7.2) let it write columns directly.

Houdini's GIL has no counterpart here.

## 7. The API

The API lives in luce-geocore as `src/script/`, public module `script`. It is general
technology, geometry scripting on top of geocore, so it belongs there and not in the app,
following the package-boundaries rule.

Unlike the Code node's stubs, it is real code: the script links it. Its `##` docs are what
completion shows.

Vectors are `f32[4]` with the fourth lane ignored, as in the Code node, so `+ - *` work on
whole vectors and code moves between the two nodes. `f64` forms exist where precision
matters (`origin`, `bounds`).

### 7.1 The cook and `k`

```luce
## The node during one cook: inputs, parameters, time, messages. The entry is
##     pub func cook(k: Cook*) -> !
## in the node's code; returning an error fails the node at the line it came from.
pub struct Cook:
    ## The output, which starts as a copy of input 0 (empty when nothing is wired):
    ## Houdini's hou.pwd().geometry().
    pub func geometry() -> Geometry*
    ## Replace the output wholesale (a verb's result, a loaded file).
    pub func set_geometry(geometry: Geometry) -> !
    ## Input `index`, read-only, empty when unconnected; `connected(index)` tells which.
    pub func input(index: i64) -> const Geometry*
    pub func connected(index: i64) -> bool

    ## Spare parameters: a literal call makes a row, as in the Code node.
    pub func f32(name: str, default: f32) -> f32
    pub func f64(name: str, default: f64) -> f64
    pub func i32(name: str, default: i32) -> i32
    pub func toggle(name: str, default: bool) -> bool
    pub func vec3(name: str, default: f32[4]) -> f32[4]
    pub func color(name: str, default: f32[4]) -> f32[4]
    pub func text(name: str, default: str) -> str
    ## A file row with a picker; the file joins the node's read grants, and the node
    ## recooks when it changes.
    pub func file(name: str, default: str) -> str
    ## A menu row: the chosen index of "a|b|c".
    pub func menu(name: str, choices: str, default: i32) -> i32
    pub func ramp(name: str, t: f32) -> f32
    pub func ramp_color(name: str, t: f32) -> f32[4]

    ## The timeline; reading these makes the node time dependent.
    pub func frame() -> f64
    pub func time() -> f64
    pub func fps() -> f64

    ## Messages. print() and f-strings go to the console as well.
    pub func warning(message: str)                  # Houdini's NodeWarning: cooks on
    pub func error(message: str) -> !               # NodeError: fails at this line
    pub func progress(fraction: f64) -> !           # also the interrupt check: fails
                                                     # "superseded" when the cook was
    ## Open a file the node may read (path parameters and the grants), and record it.
    pub func read_file(path: str) -> interop.Owned[const u8[]]!
    ## The project's directory, for relative paths.
    pub func project() -> str

    ## State that lives across cooks while the host process does: Houdini's
    ## setCachedUserData. Never saved; may be empty on any cook.
    pub func keep(name: str, geometry: const Geometry*) -> !
    pub func kept(name: str) -> const Geometry*?
```

### 7.2 Geometry: build, edit, read

```luce
pub struct Geometry:
    pub static func empty() -> Geometry!
    pub static func grid(size: f64 = 2.0, divisions: i64 = 10) -> Geometry!
    pub static func sphere(radius: f64 = 1.0, segments: i64 = 16) -> Geometry!
    ## Any format the File node reads: .prism, .obj, .ply, .fbx, .usd(a/c/z), .step.
    pub static func load(path: str) -> Geometry!
    pub func save(path: str) -> !

    # Counts and bounds
    pub func point_count() -> i64
    pub func prim_count() -> i64
    pub func vertex_count() -> i64
    pub func bounds() -> Bounds

    # Creating (Houdini's createPoint(s), createPolygon(s))
    pub func add_point(position: f32[4]) -> i64!
    pub func add_points(positions: const f32[4][]) -> i64!     # first new number
    pub func add_polygon(points: const i64[]) -> i64!
    pub func add_polyline(points: const i64[], closed: bool = false) -> i64!
    pub func remove_points(points: const i64[]) -> !           # their polygons go too
    pub func remove_prims(prims: const i64[], keep_points: bool = false) -> !

    # Positions and topology
    pub func position(point: i64) -> f32[4]
    pub func set_position(point: i64, position: f32[4])
    pub func prim_points(prim: i64) -> const i32[]             # a view into the corners
    ## The bulk paths (Houdini's pointFloatAttribValues, with no copy): writable
    ## spans over the columns, valid until the next topology change.
    pub func positions() -> Float3[]!
    pub func point_f32s(name: str) -> f32[]!
    pub func point_vec3s(name: str) -> Float3[]!
    pub func prim_f32s(name: str) -> f32[]!

    # Attributes (Houdini's addAttrib + setAttribValue); writing creates them
    pub func add_attribute(name: str, domain: Domain, kind: AttributeKind, components: i64) -> !
    pub func has_attribute(name: str, domain: Domain) -> bool
    pub func point_f32(point: i64, name: str) -> f32
    pub func set_point_f32(point: i64, name: str, value: f32) -> !
    pub func point_vec3(point: i64, name: str) -> f32[4]
    pub func set_point_vec3(point: i64, name: str, value: f32[4]) -> !
    pub func set_point_i32(point: i64, name: str, value: i32) -> !
    pub func set_point_text(point: i64, name: str, value: str) -> !
    # ... the same for prim_, vertex_ and detail_ (Houdini's global)

    # Groups
    pub func point_group(name: str) -> Group!                 # created when missing
    pub func prim_group(name: str) -> Group!
    pub func in_point_group(point: i64, name: str) -> bool

    # Whole-geometry operations
    pub func merge(other: const Geometry*) -> !
    pub func transform(matrix: Mat4) -> !
    pub func copy() -> Geometry!
    ## Packed-primitive equivalent: a reference to `child` placed at a transform.
    pub func add_instance(child: const Geometry*, translate: f32[4], rotate: f32[4], scale: f32[4]) -> !
    ## Curves and volumes, through geocore's families
    pub func add_curve(points: const f32[4][], degree: i64 = 5, closed: bool = false) -> i64!
    pub func add_volume(name: str, resolution: i32[4], min: f32[4], max: f32[4]) -> Volume!

    # Queries (the Code node's reads, here as plain calls)
    pub func nearest_point(position: f32[4], max_distance: f32) -> i64
    pub func closest_prim(position: f32[4]) -> i64
    pub func intersect(origin: f32[4], direction: f32[4]) -> Hit
```

`Geometry` wraps a `GeometrySet` and keeps a `MeshBuilder` open while points and
primitives are being added. The builder is finished, which assembles the mesh, when a read
needs the mesh, when a verb runs, or when the cook returns. A script that only adds points
and polygons pays for one assembly.

### 7.3 Verbs: Houdini's `hou.Geometry.execute`

```luce
## A verb from the node menu by its name ("PolyExtrude", "Subdivide", "Boolean"...),
## with every parameter at its default. set() takes the parameter's label as the
## node's row shows it; a vector takes its components.
pub struct Verb:
    pub static func named(name: str) -> Verb!
    pub func set(label: str, value: f64) -> !
    pub func set_vec3(label: str, value: f32[4]) -> !
    pub func set_group(group: str, group_type: GroupType = .guess) -> !
    ## Run on `input` (and `second` for two-input verbs); a new geometry.
    pub func run(input: const Geometry*, second: const Geometry*? = none) -> Geometry!
    pub func close()

extend Geometry:
    ## In place: geometry.apply("Subdivide") with defaults, for chains.
    pub func apply(name: str) -> !
```

`Verb.set` turns a label into a slot through `VerbCatalog.parm_label`,
`parm_components` and `number_count`, then `run` calls `GeometryVerbs.run`. A bad label is
an error that lists the verb's labels.

### 7.4 Example: a JPEG to a colored height field (luce-image)

```luce
from luce_std import math32
from luce_geocore.script import Cook, Geometry, Float3
from luce_image.image import Image

pub func cook(k: Cook*) -> !:
    let path = k.file("image", "height.jpg")
    let divisions = k.i32("divisions", 256)
    let height = k.f32("height", 0.3)

    let opened = try Image.open(path)
    defer opened.release()
    let image = opened.value()
    try image.load()
    let w = try image.width()
    let h = try image.height()

    var grid = try Geometry.grid(size = 2.0, divisions = (i64)divisions)
    let positions = try grid.positions()            # Float3[], written in place
    let colors = try grid.point_vec3s("Cd")         # created by the call
    for i in 0..<positions.length:
        let p = positions[i]
        # The grid spans -1..1 in X and Z; sample the pixel under the point.
        let u = (usize)(math32.clamp((p.x + 1.0) * 0.5, 0.0, 1.0) * (f32)(w - 1))
        let v = (usize)(math32.clamp((p.z + 1.0) * 0.5, 0.0, 1.0) * (f32)(h - 1))
        let r = (f32)(try image.get_sample(u, v, 0)) / 255.0
        let g = (f32)(try image.get_sample(u, v, 1)) / 255.0
        let b = (f32)(try image.get_sample(u, v, 2)) / 255.0
        positions[i].y = (0.2126 * r + 0.7152 * g + 0.0722 * b) * height
        colors[i] = Float3(x = r, y = g, z = b)
    try k.set_geometry(grid)
```

At 256 divisions there are 66k points and 200k `get_sample` calls. The probe summed 420k
samples, including starting its process and decoding the JPEG, in 0.10 s. A direct pixel
span on `Image` would make this one pass with no per-call checks; luce-image can add one
(Q9).

### 7.5 Example: a CSV to points

This parsing code was compiled and run in the probe (Appendix A); only the geometry calls
are the proposed API.

```luce
import strings
from luce_geocore.script import Cook, Geometry, Domain, AttributeKind

## x,y,z,mass per row after a header.
pub func cook(k: Cook*) -> !:
    let data = try k.read_file(k.file("table", "points.csv"))
    defer data.release()
    let lines = try strings.split((str)data.value, '\n')
    defer free(lines)
    var geo = try Geometry.empty()
    try geo.add_attribute("mass", .point, .f32, 1)
    for (row, line) in lines[1..].indexed():
        if line.length == 0:
            continue
        let cells = try strings.split(line, ',')
        defer free(cells)
        if cells.length < 4:
            k.warning(f"row {row + 2} has {cells.length} columns")
            continue
        let p: f32[4] = [try strings.parse_f32(cells[0]), try strings.parse_f32(cells[1]), try strings.parse_f32(cells[2]), 0.0]
        let point = try geo.add_point(p)
        try geo.set_point_f32(point, "mass", try strings.parse_f32(cells[3]))
    print(f"{geo.point_count()} points")
    try k.set_geometry(geo)
```

A malformed number fails the node at the `parse_f32` line, with luce-std's message.

### 7.6 Example: a Maya file

**There is no Maya reader** in the workspace. A search for "maya" in every package's
sources and manifests finds only luced-2d's Photoshop-style UI strings. What one would
take:

- **`.ma` (Maya ASCII)** is a MEL script: `requires`, `createNode <type> -n <name> -p
  <parent>;`, `setAttr ".attr" -type "..." values;`, `connectAttr "a.out" "b.in";`.
  - Reading geometry means executing a small subset of MEL: those four commands,
    statements, quoted strings and the `-type` value forms.
  - Then interpret the node types that matter: `transform` (t, r, s, rotate order, pivots,
    parenting); `mesh`; `nurbsCurve` / `nurbsSurface`; `camera`; `shadingEngine` sets for
    materials.
  - `mesh` stores vertices in `.vt`, edges in `.ed` (vertex pairs + a smooth flag) and
    faces in `.fc` as `-type polyFaces` with `f` (signed edge indices, negative =
    reversed), `mu` (uv indices per uv set), `mc` (colors) and `h`/`fc` (holes). Faces
    are given as **edge loops**, so vertices are rebuilt from the edge list.
  - Construction history (`polyCube` → `polyExtrudeFace` → mesh) is not evaluated. A file
    saved with history keeps the final mesh in the shape's `.vt`/`.fc` only when the shape
    was cached; otherwise the geometry exists only as the history to replay. Readers
    outside Autodesk read the cached shape and report the rest.
  - Estimate: a `luce-maya` package of 2–3k lines of Base for MEL tokenizing, the
    command subset, the node graph, and mesh, transform, curve and UV conversion to
    geocore. That is about luce-obj plus luce-ply in size, tested against Maya-exported
    samples.
- **`.mb` (Maya binary)** is an IFF-style chunked format (`FOR4`/`FOR8` groups, `MAYA`,
  `HEAD`, `CREA`, `ATTR` chunks). It carries the same node and attribute data as `.ma`,
  binary-encoded and undocumented.
  - The open readers are reverse-engineered and partial; Blender has none, and the usual
    advice is "export FBX or USD".
  - Estimate: `.ma` first, then `.mb` as a second front end onto the same node graph
    (+1.5–2k lines). Its risk is the format's undocumented corners, not code volume.
- **Today, without a reader,** a script reads what Maya exports. We already have FBX and
  USD readers, with geocore conversion, through their `kernel` modules:

```luce
from luce_geocore.script import Cook, Geometry

pub func cook(k: Cook*) -> !:
    # Maya: File > Export All > FBX (or USD); luce-fbx reads it.
    var scene = try Geometry.load(k.file("scene", "set_dressing.fbx"))
    let spacing = k.f32("spacing", 3.0)
    var out = try Geometry.empty()
    for i in 0..<10:
        try out.add_instance(&scene, [(f32)i * spacing, 0.0, 0.0, 0.0], [0.0, (f32)i * 36.0, 0.0, 0.0], [1.0, 1.0, 1.0, 0.0])
    try k.set_geometry(out)
```

  Once `luce-maya` exists, the same script names a `.ma` and adds `luce-maya` to the
  node's dependencies; `Geometry.load` picks the reader by extension.

### 7.7 Errors in the API

- Every API call that can fail is `!`. The script's `try` sends the error up to `cook`,
  and the node fails with the message and the line of the `try` that raised it. The
  generated `main` reads the position the runtime records for an error in flight; Q7
  covers how.
- A trap (index out of range, overflow, `assert`) ends the process with
  `trap: script.lucb:L:C: message`. The node shows "line L, column C: message", and the
  editor underlines it.
- `k.error(msg)` is the clean failure: it returns an error, so `defer`s run.
- Messages that point into the API (a failed verb) name the verb and the script line
  that called it.

## 8. Dependencies

Houdini's Python SOP imports anything on `sys.path`, so a hip file does not say what it
needs. We can do better, and must, because the script is compiled.

**Where dependencies are declared.** Two forms were considered:

- **A node-level list** (recommended): a "Packages" row on the node, entries like
  `luce-image ^0.45`, edited as a list with registry search.
  - The list is written into the script project's `package.prisma`.
  - The `luc.lock` that `luc lock` produces is saved **in the project file** next to the
    node, so the project rebuilds the same everywhere.
  - luce-geocore and luce-std are always present, at the app's versions; they cannot be
    removed.
- **From the import lines:**
  - `from luce_image.image import Image` names a module path whose first segment is the
    package's import name.
  - The editor can offer "add luce-image to this node's packages?" when an import does not
    resolve, using the registry's package search (pkg.luciaos.com).
  - This is only an assist: imports alone do not say which owner or version.

**Version pinning.** The lock pins exact versions and content hashes. "Update packages" on
the node runs `luc lock` again and shows what changed. All packages are public, and
anonymous installs work, so a project that names registry packages builds on any machine
with network access.

**Offline.**

- Building needs the package sources once; luc keeps them in its cache under `~/.luce`.
- A project whose lock is satisfied by the cache builds offline. If not, the node fails
  with "luce-image 0.45.0 is not downloaded; connect to build this script", and the
  Script node's last cooked result, if the project saved it frozen, still shows.
- **Freeze** works as for other nodes: the output is stored in the project, so a scene
  opens and renders without building anything.

**Local packages.** A dependency can be a path (`../my-reader`), as luc allows. The
project then records the path, and the node shows it as local, not portable.

## 9. Errors, diagnostics and the editor

### 9.1 The editor

`CodeEditor` (`code_editor.luc`) is reused as it is: luce-ui's `TextEditor`, Luce
highlighting, a 400 ms commit pause, Cmd/Ctrl-Enter, diagnostics as underlines with hover
messages.

The differences:

- One text, the whole module, with no Body/Header split. `cook` is written by the user,
  and helpers sit around it.
- A starter text with `pub func cook(k: Cook*) -> !:` and a comment saying what `k` holds.
- Under the code: the console (print output and warnings, first 200 lines), then a status
  line: "Built in 0.6 s · cooked in 14 ms (I/O 4 ms)".

### 9.2 Checking while typing (stage 2)

At each pause, `luc check` runs in the script's project. It takes 0.14 s with
luce-geocore or luce-image, and its diagnostics come back with lines and columns.

- They map straight onto the editor, because `src/script.lucb` *is* the node's text.
- The check runs in the build service, never on the UI thread.
- A newer pause kills an older check by PID.

Parameter rows come from a parse, not a check:

- luce-base's `front.parser` is public through `embed`. luced-3d parses the text in
  process, which needs no imports resolved.
- It collects calls of the form `k.<f32|i32|vec3|text|file|menu|ramp|...>("literal", literal)`,
  where `k` is `cook`'s first parameter. Those become rows, and they keep their slots by
  name, as `code_node.refresh` does.
- The same parse finds `k.frame()`, `k.time()` and `k.fps()` for time dependence.
- A call whose name is not a literal makes no row, and the editor warns at it, as the Code
  node does.

### 9.3 Completion and hover (stage 4)

luce-kernel's `lower.complete` and `hover` work on stub texts the host provides. For the
Script node, completion must cover any package's API.

- **The plan:** generalize luce-kernel's assist (`assist*.lucb`) so it works over any
  checked tree. Then run `embed.Library.check` on a root that holds the script plus the
  dependency closure's sources, which `luc sync` already places under the project's
  `.luc/deps`.
- **The unknown is cost.** A `Library` caches only the standard modules, so each check
  would re-check luce-geocore and luce-image. That needs a measurement, and probably a
  Library that also caches a fixed set of package modules, a small extension of what
  `Library` already does for the standard ones (Q5).
- **Until then,** completion covers `k.`, `Geometry`, `Verb` and the locals, from the
  script API's own source, with luce-kernel's assist pointed at the `script` module's
  text.

## 10. Staged build order

Every stage ends with `luc test` green in each touched package. The new tests are listed
for each stage.

**Stage 0: Script API in luce-geocore (no app).**

- Work:
  - `src/script/`: `Cook` (backed by plain structs, so tests can drive it), `Geometry`
    over `GeometrySet` + `MeshBuilder`, attribute access, groups, bulk spans, `Verb` over
    `GeometryVerbs`/`VerbCatalog`, `Geometry.load/save` for `.prism`;
  - the request loop `script.serve(cook_fn)` that the generated `main` calls (the protocol
    in §6.2).
- Tests:
  - geocore unit tests for each API group: add 10k points and polygons and compare with
    `MeshBuilder`; attributes round-trip through `.prism`; `Verb.named("PolyExtrude")`
    with labels matches the node's cook; a bad label lists the labels;
  - a `tests/script_serve/` program that runs `serve` over a canned request and checks
    the reply lines and the output file;
  - a trap test: the child exits 1 and stderr carries `trap: script.lucb:L:C:`.

**Stage 1: The node, with builds and the process (b, then d).**

- Work:
  - luced-3d: node kind `Script`, its texts (code, packages, grants, lock), the project
    writer, the build service (`luc build --release` in `~/.luce/scripts/build/<hash>`,
    with PID tracking, cancellation and parallel builds), the host process manager
    (start, request, read, kill, idle exit);
  - the worker hook in `compute_worker.cook`; the console and warnings on
    `GeometryData`; error mapping;
  - use (b), a process per cook, first; switch to persistent processes once (b) passes.
- Tests:
  - `tests/script_node/`, headless and with no GUI: a network of Grid → Script (move
    points up) → output, cooked through `Computation` with stamps checked;
  - a second cook with the same hash starts no build;
  - a trap fails the node with the right line, and the app process lives;
  - a 60 s busy loop is killed at the limit;
  - a superseded cook kills the PID;
  - timing assertions logged, not enforced: build under 1.5 s and cook overhead under
    50 ms for 1M quads on the M4 Max.

**Stage 2: Editing.**

- Work:
  - the editor (CodeEditor reuse), check-on-pause through `luc check`, the parse for
    parameter rows and time dependence, spare-parameter rows (the `code_node.luc`
    machinery shared, not copied: one `spares` helper used by both nodes);
  - "Building…" and stale-result display; the status line.
- Tests:
  - parameter rows keep values across edits;
  - a type error underlines the right line;
  - editing the code while a build runs cancels it;
  - a changed `k.f32` default does not overwrite a tuned value.

**Stage 3: Packages, files and the sandbox.**

- Work:
  - the Packages row and registry search, `luc lock` into the project, offline messages;
  - `k.file`, `k.read_file` and the `read` lines, with file stamps in the node's stamp;
  - grants, with the sandbox entry moved from luce to luce-std (`process.sandbox`) and
    applied by `serve` before `cook`;
  - the trust prompt on project open;
  - Windows: unfenced with a console notice, plus a Job object for limits.
- Tests:
  - the JPEG and CSV examples of §7 as `examples/scripts/` with checked outputs;
  - editing the CSV recooks the node;
  - reading a file outside the grants fails with the sandbox's error on macOS and Linux;
  - a clean `LUC_HOME` build of an example project from the registry (the
    verify-registry-install rule);
  - an offline build with a warm cache succeeds, and with a cold cache fails with the
    message.

**Stage 4: Speed and help.**

- Work:
  - mapped `.prism` exchange and "same input" requests;
  - completion and hover over packages (§9.3) after measuring a package-caching `Library`;
  - ask the language session for the compile items in Q5.
- Tests:
  - 1M-quad cook overhead under 10 ms with mapping;
  - completion lists `Image.open` after `from luce_image.image import Image`.

**Later.**

- `luce-maya` (`.ma`, then `.mb`) as its own package (§7.6);
- a Script mode for Edit steps;
- a "Python Module" equivalent: shared helper modules in the project that several Script
  nodes import, like `hou.session` (one more file in each script project, part of the
  hash).

## 11. Open questions for the owner

1. **A persistent process, or Houdini's fresh state per cook?** The recommendation is
   persistent, which is faster and keeps opened files warm, with `k.keep()` as the only
   documented state. Module globals would then survive by accident unless the host
   restarts the process every cook, which costs about 2 ms.
2. **Where should the API live?** The proposal is luce-geocore `src/script/` as public
   `script`. The other choice is a small `luce-geocore-script` package. The
   package-boundaries rule points to geocore.
3. **Sandbox.**
   - Is moving `luce/src/support/sandbox.lucb` into luce-std acceptable (language-session
     work)?
   - On Windows: unfenced with a notice, as luced-2d does, or invest in AppContainer?
   - Is network off by default right?
4. **Trust on open.** Should a project's Script nodes ask before their first build on a
   new machine, and should the answer be stored per project?
5. **Compiler asks to the language session** (`luce-base-ownership`):
   - (i) a per-function generation cache, or a resident build mode that keeps the
     dependency closure checked, so an edit builds in about 0.1–0.2 s instead of 0.65 s;
   - (ii) `embed.Library` caching a fixed set of package modules, for completion;
   - (iii) the shared-library output that base.md §17.6 promises, if tier (a) is ever
     wanted.
6. **Recoverable traps?** A `thread.guarded` that turns a trap on a thread into an error
   would allow an in-process "trusted" tier. It is a language decision. The recommendation
   does not need it.
7. **Errors from `try` carry no source position today.** The `trap:` line has one; an
   error returned from `cook` has only its message. The options are to have the generated
   `main` report "returned from cook" with no line, or to ask for error positions (an
   `ErrorCode` plus the `try` site), which also helps every Base program.
8. **Disk budget** for `~/.luce/scripts` (proposed 2 GB, LRU) and the idle timeout
   (proposed 60 s).
9. **luce-image pixel spans:** add `Image.channel_span(c) -> const f32[]` or similar, so
   image-driven scripts do not pay a checked call per sample?
10. **`luce-maya`:** worth scheduling now, or wait until a project needs it? The FBX and
    USD route works today.

## Appendix A: probe sources and commands

All under `/private/tmp/claude-501/-Users-sedov-Dev-luce-dev/26944722-c0bc-4a1f-9a03-297d52283e2a/scratchpad/script-probe/`.

**`tiny/main.lucb`:** an `export func script_cook(count: i64) -> f64` loop.

- `luce-base build main.lucb -o tiny --release`: 0.12 s cold, 0.05 s cached.
- `--emit=asm -o tiny.s`: 0.03 s, 9,717 lines.
- `as -o tiny.o tiny.s`: 0.04 s.
- `ld -dylib -arch arm64 -platform_version macos 15.0 15.0 -syslibroot $(xcrun --show-sdk-path) -o tiny.dylib tiny.o -lSystem`: 0.02 s.
- `ctypes.CDLL("tiny.dylib").script_cook(1000000)` = 249999750000.0.

**`alloc/main.lucb`:**

- `script_alloc` allocates with `new f64[n]`. It trapped `memory.unset` until the entry
  called `memory.startup()`; then it returned 499500.0 for n = 1000.
- `script_trap(9)` indexes an `f64[4]`. Output: `trap: main.lucb:19:5: index out of
  bounds`; the Python host exited with status 1 and its next line never ran.

**`jpegprobe/`:** a tool package depending on luce-image (path) and luce-std. `main` opens
a JPEG with `Image.open`, sums every `get_sample(x, y, 0)` and prints the mean.

- `luc build --release`: 1.31 s from an empty `build/`, 0.22 s unchanged, 0.56–0.66 s
  after an edit.
- `luc check`: 0.14 s.
- Running on `luce-image/build/background-open.jpg` (700×600): 0.10 s.

**`geoprobe/`:** a tool package depending on luce-geocore. `MeshPrimitives.grid(2.0,
1000)`, then `GeometrySet.of_mesh`, `GeometryFile.save`, `GeometryFile.load`, timed with
`time.now()`.

- Grid 10.2–10.4 ms; save 5.4–5.7 ms; load 11.2–11.3 ms; file 56,024,367 bytes.
- `luc build --release`: 1.20 s fresh, 0.65 s after an edit; debug build 0.65 s.

**`csvprobe/`:** the CSV parsing of §7.5 (`files.read`, `strings.split`, `parse_f32`,
`parse_f64`), built with `luc build` and run on a three-line CSV: "2 points, mass 3.5".

**Process spawn:** median of 20 runs of `tiny` through `subprocess.run`: 1.53 ms.

## Appendix B: code references

- luced-3d: `src/code_cook.luc`, `src/code_node.luc`, `src/code_editor.luc`,
  `src/compute_worker.luc`, `src/compute_bridge.lucb:331` (the worker thread),
  `docs/CODE.md`, `docs/research/CODE-NODE.md` §4–5.
- luce-kernel: `README.md`, `src/lower/root.lucb` (the snippet root), `src/lower/scan.lucb`,
  `src/lower/assist*.lucb`, `src/lower/lowerer.lucb:138` ("not available in a kernel").
- luce-geocore:
  - `src/code/cook.lucb` (`run_code`);
  - `src/geometry_set/api.lucb`;
  - `src/geometries/polygon/access.lucb`, `src/geometries/builder.lucb`,
    `src/geometries/primitives.lucb`;
  - `src/verbs/api.lucb` (30 mesh verbs), `src/set_verbs/verb.lucb` and `api.lucb`
    (`GeometryVerbs`, `VerbCatalog`);
  - `src/geometry_files/api.lucb`.
- luce-base:
  - `docs/EMBEDDING.md`;
  - `src/main.lucb:628` (`assemble_and_link`), `:717` (`link_with_driver`), `:858`
    (`build_library`, static only);
  - `src/std/memory.lucb:379` (`startup`);
  - `docs/language/base.md` §11.5 (traps), §17.6 (export, "static or shared library");
  - `luce-gpu/src/gpu/vulkan/entry.lucb` (dlopen from Base).
- luce: `src/support/sandbox.lucb`, `src/support/sandbox_abi.c`, `docs/luce.md` (`luce run
  --sandbox`, policy `luce-sandbox/1`).
- luced-2d: `src/script_host.luc` (subprocess, `@l2d` lines, unfenced fallback),
  `docs/SCRIPTING.md`.
- luce-image: `src/image/module.lucb` (`Image.open`, `get_sample`). luce-fbx and luce-usd:
  `src/kernel.lucb`.

## Owner decisions (2026-10-09)

1. **Execution:** a native tool built by the real compiler, run in a long-lived child process. A trap fails the node, not the app. About 0.65 s per edit on the Mac is acceptable for now.
2. **State:** the process stays alive between cooks, but each cook starts with fresh state, as Houdini's Python SOP does.
3. **Access:** everything, with no sandbox, like Houdini's Python. Drop the sandbox stage and the per-node file and network grants.
4. **Packages:** "There should not be extra work. We should be able to use existing packages without modifying them." A script imports any existing Luce package as it is: no adapters, no wrappers and no changes to the package. No luce-maya now. Maya data comes through whatever packages exist (FBX, USD).
