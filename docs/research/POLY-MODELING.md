# Polygon modeling for luced-3d: one tool definition, and the full tool set

Research and design, 2026-10-13. No product code was changed for this document. It answers
the owner's request:

> "Ok once we're somewhat done with CAD I suggest that we switch focus on Poly (Geo). For both
> context we have Edit CAD node and Edit Geo mode that allow us do rapid modeling without making
> nodes, however for every operation we also have a node. We first need to make sure that this
> is universal and that we don't duplicate code and it's somewhat automatic to extend. [...] So
> the same goes for poly editing. Now I suggest that we look closely at Blender since we have the
> source code and Houdini and make sure we have full well organized tool set for polygonal
> modeling. We have all the nodes and all the tools inside Edit Geo for creating, modifying, and
> also selecting. Like we need to be able to select connected islands, edge loops etc. double
> clicking on an edge in selection would select a loop etc. [...] We can also look at Cinema 4D
> and Modo as both have good tools that we may have missed."

"Edit Geo" in the request is the node called **Edit Mesh** today. This document keeps the code's
name and proposes the rename in §9.

Sources and tags:

- **Our code.** luced-3d `origin/main` at `772053b` and luce-geocore at `fbe1118`, read on
  2026-10-13. File names are luced-3d's `src/` unless another repo is named.
- **Blender.** The source at `/Users/sedov/Dev/blender-main`, read for its algorithms and
  keymap: `bmesh/operators/`, `bmesh/tools/`, `editors/mesh/`, the modifiers and the geometry
  nodes. Blender is GPL. We read it and describe what it does in our own words; no code,
  comment or table of it goes into our repos. Claims from it are tagged **[src]** with a path.
- **Houdini, Cinema 4D, Modo and Maya.** Their manuals. Tags as in FUSION-CAD-UX.md:
  **[doc]** official help, **[comm]** a forum or tutorial, **[unverified]** not confirmed.

## 1. Decision in one page

**The kernels are already shared; the wiring is not.** Every Edit Mesh tool is a luce-geocore
verb, and the same verb is the node, so node and step already run one kernel. CAD reached the
same point in stage 7 of FUSION-CAD-UX.md: the Modify feature nodes run Edit CAD's own step
code (`cad_modify.luc` calls `edit_cad_faces.run_face_step`), and the surfacing nodes and steps
share `blend_ops`, `build_ops`, `align_ops` and `fill_ops`. What is duplicated is everything
around the kernel. A CAD tool is named by hand in 7 to 20 source files: the node catalog, the
step dispatch, the pick prompts, the menus, the marking menus, the right-click menu, the handles,
the icons and the inspector. A mesh tool is cheap to add (3 files) but gets little: no handle,
no right-click entry, one starting value, no Repeat.

**Proposal: one `Tool` record per operation, and every surface reads the registry.** A tool
declares its name, section, icon, the levels and selection it works on, its pick slots, its
parameter rows (which of them show on the step's tool bar), the parameter a viewport drag sets,
its gesture (click, stroke, placing, hover, slide), its handles and one `cook` function. The
node, the Edit step, the tool bar, the Create/Modify/Select menus, the A/S/D marking menus, the
right-click menu, Repeat, the pick prompts and the docs are all generated from it. For mesh
tools the record is built from the luce-geocore verb itself, so adding a mesh tool is one Base
file (the verb's declaration and kernel) and one line in the verb list. For CAD, each tool is
one small Luce declaration file beside its luce-cad kernel until those declarations move into a
luce-cad registry (§9, question 2).

**The poly tool set is about half there.** luced-3d has 30 mesh verbs and 28 Edit Mesh tools.
Against Blender, Houdini, Cinema 4D and Modo, the main gaps are:

- **Selection by click.** Loop, ring, connected, path and similar exist as functions or not at
  all, but no click gesture reaches them. Double-click for loops is missing.
- **Select tools.** Select Similar, shortest path, by angle and sharp edges, non-manifold,
  checker, by sides and selection sets are missing.
- **Interactive tools.** Bevel, Inset, Extrude and Loop Cut take a number on the tool bar instead
  of a drag in the viewport. Loop Cut has no hover preview.
- **Modify tools.** Solidify, Bridge options, Grid Fill, Rip, Edge Split, Collapse,
  Un-subdivide, PolyReduce, Quadrangulate, Rotate Edge, Poke, Offset Edge Loops, Circularize,
  Straighten, vertex bevel, bevel profiles and normals tools are missing.
- **Deformers.** Bend, Twist, Taper, Lattice and sculpt-lite brushes are missing.
- **Analysis.** A mesh check for non-manifold geometry, n-gons, poles and zero-area faces is
  missing.

**Order** (§8): the tool definition and the migration of every existing CAD and mesh tool first,
then selection, then the interactive Modify tools by priority, then the rest.

## 2. How a tool exists today

### 2.1 The two halves

**Mesh tools** are luce-geocore verbs (`luce-geocore/src/verbs/`). A verb is a Base record:

- its name, which is also the node kind and the recipe's step name;
- its category and description;
- the domain it works on and the second domain it accepts;
- its parameters as `ParmSpec` rows (label, kind, initial value, range, menu items, doc,
  soft maximum);
- whether it changes topology;
- its `cook` function.

The registry is the `makers` array in `verbs/api.lucb`: 30 verbs. luced-3d's node catalog
generates the node from it (parameters, Group, Group Type), so a verb is a node with no Luce code.
`Verbs.run` resolves the group and returns the output selection, which the viewport adopts. The
Edit Mesh step runs the same `Verbs.run` (`edit_operations.EditStep.evaluate`). This half is
already one definition.

**CAD tools** have their kernels in luce-cad Base (`CadModeling.shelled`, `CadSurfaceFill`,
`CadSurfacing.aligned`, …), but there is no registry. Each tool is wired by hand in Luce: rows in
`node_catalog.cad_fields`, a node wrapper (`cad_modify`, `cad_surface_nodes`,
`cad_curve_nodes`), an Edit CAD step branch (`edit_cad.ran` dispatches on the verb name through
eight families), pick prompts for the node (`modify_picks`) and for the step (`edit_cad_picks`),
commands (`modify_commands`, `surface_commands`, `cad_commands`, `edit_cad_actions`), and handles
(`feature_handles`). The kernel call itself is shared, as stage 7 intended: the Modify nodes run
`edit_cad_faces.run_face_step`, Edit CAD's Fillet runs the node's `cad_nodes.evaluate_cad`, and
the surfacing families share their `*_ops.luc`.

### 2.2 Where a tool is named

One row per surface. "Generated" means the tool needs no code there.

| Surface | Mesh tool (e.g. PolyBevel) | CAD tool (e.g. Shell, Fillet, Fill Surface) |
| --- | --- | --- |
| Node definition and catalog | Generated from `VerbCatalog` (`node_catalog.verb_fields`) | By hand: `cad_nodes.cad_only_kinds`, `cad_category`, the family's `kinds()`, `node_catalog.cad_fields` / `blend_fields` |
| Kernel call | `Verbs.run` | Shared Luce op (`edit_cad_faces`, `blend_ops`, `build_ops`, `align_ops`, `fill_ops`) |
| Edit step executor | `EditStep.evaluate`, generic | `edit_cad.ran`: a chain of `if step.verb in family.verbs()` |
| Edit tool list | `edit_mesh.tool_names` + `tool_levels` (by hand) | `edit_cad.tool_list` and each family's `tools()` (by hand) |
| Starting numbers | `tools.tool_run` (a table by name, by hand) | `EditTool.numbers`, or the node's starting values |
| Step tool bar | Generated (`node_catalog.tool_rows`) | Generated from the node's rows, or the tool's `rows` |
| Viewport handles | None | `feature_handles`: two hand lists of kinds; the cook encodes `HandleLine`s |
| Pick prompts | One generic Group (Tool → Select) | `modify_picks` (node rows and prompts), `edit_cad_picks` (step waits), `tool_prompts` |
| Create/Modify menus | Generated from the Edit kind | `top_menus`: a hand list of CAD commands |
| A/S marking menus | Generated from the kind; S lists every tool, disabled when the level does not fit | `marking_items`: hand lists of node kinds per context; Repeat's kind map |
| Right-click menu | **None** in Edit Mesh (only Create) | `viewport_menu`: per selection type; CAD entries picked by index (`modify[0]`, `modify[4]`…) |
| Tool bar strip | Generated | Generated |
| Repeat | **None** | `last_cad_tool` and a hand map of command ids to kinds |
| Icons | `tool_icons.asset_name` (a 131-branch `if` chain) | The same chain |
| Inspector | Generic | Special cases for Extrude, Revolve, Offset Face, Fillet, Chamfer, Check |
| Outliner, worker, report | Generic | Generic |
| Docs | MODELING.md by hand | MODELING.md by hand |
| Tests | `operators_tests`, `edit_mesh_tests` | One test file per tool family |

### 2.3 Measured

Counted on `772053b`. "Mentions" are lines naming the tool or its constants.

| Tool | src files | src mentions | test files | preview tools |
| --- | --- | --- | --- | --- |
| Fillet (CAD) | 20 | 60 | 18 | 10 |
| PolyExtrude / Extrude (both) | 21 | 53 | 20 | 6 |
| Align (CAD) | 12 | 39 | 5 | 3 |
| Shell (CAD) | 9 | 26 | 3 | 3 |
| Fill Surface (CAD) | 7 | 32 | 1 | 1 |
| PolyBevel (mesh) | 3 | 5 | 3 | 1 |
| Loop Cut, Edge Slide, Bridge, Spin (mesh) | 3 each | 3–4 each | 0–1 | 0 |

What adding a tool took, from the commits that did it:

- **Fill Surface** (`a916366`): 16 files, 727 lines. 223 of them are its op (`fill_ops.luc`), 217
  its tests and 111 its preview. The rest is wiring in 8 source files: `blend_ops`,
  `build_labels`, `edit_cad_build`, `edit_cad_picks`, `modify_picks`, `surface_commands`,
  `tool_icons` and the docs.
- **Bridge Fillet and Corner** (`e2149ec`): 17 files; wiring in 7 source files.
- **PolyMirror, Spin, Crease, PolyDraw** (`6a31450`): 8 files, 94 lines in luced-3d (the
  kernels are in luce-geocore). Each tool took a line in `edit_mesh.luc`, a branch in `tools.luc`
  and an icon.

The layers by size:

- **Wiring** (commands, picks, prompts, menus, handles, icons, tool bar, steps): 21 files, 5,206
  lines.
- **CAD step and op code**: 17 files, 5,661 lines.
- **Edit Mesh's kind**: 134 lines.
- **String dispatch**: `if kind == "Name"` and `in ["Name", …]` tests occur 707 times in `src/`.
  The most are in `tool_icons` (131) and `node_catalog` (119).

### 2.4 The duplication, named

1. **The tool list is written per surface.** Edit CAD's tools (`edit_cad.tool_list`), its
   commands (`modify_commands`, `surface_commands`), the CAD network's node kinds
   (`cad_nodes.cad_only_kinds`), the right-click menu (by index into the commands), the marking
   menu (`marking_items.modify_items` names Mirror Body, Pattern, Transform…), Repeat's map and
   `feature_handles`' lists all repeat the same names. Adding a tool and missing one of them
   leaves it absent from that surface, silently.
2. **Two pick systems.** A node keeps picks by name and prompts through `modify_picks`. A step
   keeps a group and prompts through `edit_cad_picks`. Both describe the same inputs: Combine's
   target and tools, Align's master, Fill's boundaries and guides.
3. **Two step shapes.** A node is `kind` + `values[48]` + `texts`. A step is `EditStep` (verb,
   numbers, group, texts, topology, symmetry, keep). `cad_modify.evaluate` translates one into
   the other per kind.
4. **Dispatch by verb name in the executor.** `edit_cad.ran` tests membership in eight families'
   verb lists before reaching the face steps. `edit_cad_faces.run_face_step` tests ten names.
5. **Mesh tools carry a second table.** `tools.tool_run` gives each mesh tool its starting
   numbers by name, apart from the verb's own `ParmSpec.initial`. `edit_mesh.tool_levels` gives
   its levels, apart from the verb's domain.
6. **Icons by an if-chain** keyed on display names.
7. **Inspector special cases** for six CAD kinds' rows, which belong in the rows' own conditions.

What is already right and should be kept:

- one kernel per operation;
- the verb registry's generated node and rows;
- the `Parameter` row model with `hide_when`, `in_steps` and `slider`;
- the cook publishing its handles as `HandleLine`s;
- the Edit kind's levels and `smart` list;
- the recipe as truth.

### 2.5 What a mesh tool lacks today

Mesh tools are cheap to add because they get little:

- **No drag.** A tool runs at its starting numbers and the tool bar changes them. There is no
  viewport drag (Blender's and Modo's), no handle and no hover preview (Loop Cut).
- **No right-click.** The right-click menu in Edit Mesh has no tools.
- **No Repeat.**
- **No selection-type filtering in S.** S lists every tool and disables those the level does not
  take. CAD hides them.
- **No pick slots beyond the one Group.** Bridge cannot be given its two loops apart, and a
  Connect path has no start and end.

## 3. One tool definition

### 3.1 The rule

**An operation is declared once, where its kernel lives. Every surface is generated from the
declaration.** Houdini works the same way: a SOP's parameter template, its viewer state and its
shelf tool all hang off one node type, and its verb is the same code in the node and in the
Edit SOP. The declaration says what the operation *is*. A small set of rules in luced-3d decides
where it *shows*: which menu, which marking menu, which right-click section, from its section
and the selection it takes. No surface keeps a list of tool names.

There are two homes for declarations, both feeding one Luce registry:

- **Mesh tools: the luce-geocore `Verb`, extended.** The verb already holds the name, category,
  domains, parameters and cook. It gains the few fields listed in §3.2. These are facts about the
  operation, not about luced-3d's menus. Adding a mesh tool is one Base file in
  `luce-geocore/src/verbs/` (declaration and kernel) and one line in `makers`. luced-3d needs no
  code.
- **CAD tools: one Luce declaration file each**, in luced-3d (`src/tool_<name>.luc`). Each holds
  a `Tool` built with the same fields and a `cook` that calls the luce-cad kernel, as
  `fill_ops.luc` does today. Moving these declarations into a luce-cad Base registry, shaped
  like `Verb`, is question 2 in §9. The Luce form comes first because the CAD ops' glue (word
  parsing, labels, state lines) is Luce today.

Edit SDF and Edit GSplats tools follow later, in whichever of the two forms their kernels suit.

### 3.2 The record

In luced-3d, `tool.luc`:

```
## One operation: the node of that kind, the step of that verb, and every
## menu, marking menu, right-click entry, prompt and handle that reaches it.
pub class Tool:
    ## The node kind and step verb ("PolyBevel"), and the label menus show
    ## ("Bevel").
    pub let name: str
    pub let label: str
    ## Where it sits: "Create", "Modify" or "Select", then a family
    ## ("Edges", "Faces", "Points", "Objects", "Normals", "Deform",
    ## "Surfaces", "Blends"…). Menus, marking menus and docs group by it.
    pub let section: str
    pub let family: str
    pub let icon: str
    pub let doc: str
    ## The contexts it is a node in ("geometry", "cad") and the Edit kinds
    ## it is a step of ("Edit Mesh", "Edit CAD").
    pub let contexts: list[str]
    pub let kinds: list[str]
    ## What it works on: one or more pick slots. The first is the
    ## selection the tool is run on; the others are asked for after.
    pub let picks: list[Pick]
    ## Its parameter rows (Parameter, with `in_steps` for the tool bar and
    ## `more` for More options).
    pub let rows: list[Parameter]
    ## The row a drag in the viewport sets (-1: none), and how: "haul"
    ## (anywhere, Modo's), "handle" (on the cook's handle lines only).
    pub let drag: int
    pub let drag_mode: str
    ## The viewport input it takes besides clicks: "" none, "stroke"
    ## (Knife, Bisect), "place" (PolyDraw), "hover" (Loop Cut's ring under
    ## the pointer), "slide" (Edge Slide, Vertex Slide).
    pub let gesture: str
    ## Whether it runs with nothing selected (on everything): Subdivide,
    ## Clean, Triangulate.
    pub let whole: bool
    ## The run: the same for a node and a step.
    pub let cook: func(Invocation, GeometryData, str) -> GeometryData!
```

`Pick` is one selection input:

```
pub class Pick:
    pub let label: str          ## "Edges", "Target body", "Master"
    pub let levels: list[int]   ## the levels it is picked at
    pub let many: bool          ## Enter finishes; else one click does
    pub let required: bool
    pub let prompt: str         ## "Pick the second loop"
```

`Invocation` is what both a node and a step hand the cook. It replaces `EditStep`'s fields and
the node's value and text slots as the cook sees them:

```
pub class Invocation:
    pub let verb: str
    pub let numbers: list[float]
    pub let texts: list[str]
    ## One group per pick slot (a mesh group expression, or CAD names).
    pub let picks: list[str]
    pub let group_type: int
    pub let topology: int
    pub let symmetry: int
    pub let keep: bool
```

A node builds its `Invocation` from its value slots and texts; a step stores one. The step's
"Edit CAD keeps names, Edit Mesh keeps groups" difference moves into `Pick`: a CAD pick slot is
stored as names, a mesh slot as a group with a topology guard. The node and the step read the
same slot the same way. That removes `cad_modify.evaluate`'s translation and the two pick
systems.

For mesh verbs, `verb_tools.luc` builds a `Tool` from each `VerbCatalog` entry. The Base `Verb`
gains these fields:

- `label`, `section`, `family` and `icon`, as plain text;
- a `picks` array of `PickSpec` (label, domain, many, required, prompt). The first entry stands
  for today's Group, so a verb with no `picks` keeps one Group;
- `drag` and `drag_mode`;
- `gesture`;
- `whole`;
- on `ParmSpec`, `bar` (shown on the tool bar, default on) and `more` (behind More options).

The cook already returns the output selection. It gains the handle lines, as CAD's cooks return
them now (`VerbOutput.handles`), so Bevel's offset arrow and Extrude's distance arrow come from
the kernel that knows where they stand.

### 3.3 What is generated from it

| Surface | Read from the registry |
| --- | --- |
| Node catalog | `kinds()`, `fields()`, `category_in()`, `allowed()` from `contexts`, `section` and `family`; the pick slots become pick rows (what is picked, Pick again) |
| Edit kinds | `EditKind.tools` = the tools whose `kinds` name it; `edit_mesh.tool_names`, `tool_levels` and `tools.tool_run` go |
| Step executor | `kind.run` looks the verb up and calls `tool.cook`; only primitives, sketches and moves stay with the kind |
| Tool bar | `rows` with `in_steps` (as now), More options from `more` |
| Drag and handles | One generic driver: `drag` + `drag_mode` set that row from the pointer; the cook's handle lines as now |
| Gestures | One module per gesture, not per tool: `stroke` (today's knife), `place` (today's PolyDraw), `hover`, `slide` |
| Prompts | One prompt chain over `picks`, for nodes and steps (replaces `modify_picks`, `edit_cad_picks`, most of `tool_prompts`) |
| Create / Modify / Select menus | By `section`, then `family` as submenus |
| Marking menus | A = Create, S = Modify, D = Select (§6.2); each lists the tools whose first pick takes the current level, grouped by family; Repeat first |
| Right-click | The tools whose first pick takes the selection's level, by family; the Select tools for that level; with nothing selected, Create |
| Repeat | The last `Tool` and its numbers, in any context: a step in an Edit node, else a node |
| Icons | `icon` (the 131-branch chain keeps only non-tool names) |
| Docs | `tools/tool_docs.luc` writes docs/TOOLS.md from `label`, `doc` and the rows' docs; a test fails when it is stale |
| Tests | One conformance test walks the registry (§3.5) |

### 3.4 Fitting Luce

- **No reflection.** Luce cannot find tool files by itself, so the registry is a list, like
  luce-geocore's `makers`: `tool_registry.luc` imports each CAD tool module and calls its
  `tool()`. Adding a CAD tool is its file plus one line there. The conformance test fails when a
  `tool_*.luc` file is not in the list.
- **Callbacks.** `cook` is a plain `func` field. Optional hooks use the Luce form
  `pub var f: func(...) -> T!? = none`, called through `if let`, because field defaults must be
  constants.
- **Names.** A field cannot share a name with a method. `Tool.picks` is a field, so the method
  that resolves a slot is `pick_slot`. `list` and `bytes` are reserved.
- **Unused imports are errors.** The registry imports each tool module, and each module is
  used.
- **No bit operations in Luce.** Selections, loops and paths stay luce-geocore `Selection`
  passes. The Luce side only names them.
- **Luce orchestrates Base.** The registry is a table of what to call. Per-element work stays in
  the kernels and the selection passes.
- **Build cost.** One module per CAD tool adds modules, which builds tolerate (luced-3d already
  has 205). A table built once (`tool_registry.all()` cached by the workspace) avoids rebuilding
  the closures on every menu open. Today `edit_kinds.edit_kind` rebuilds every kind on each call.

### 3.5 Tests the registry gets

One test file, `tool_registry_tests.luc`, checks every tool:

1. **Node and step agree.** On a fixture for its first pick (a cube's top face, a ring of edges,
   a CAD box's edge), the node at its starting values and the Edit step with the same picks give
   the same result. Compared: point count, face count, volume and bounds; for CAD, the face names
   and the volume. This is the parity CAD stage 7 established, enforced for all.
2. **Every surface reaches it.** The node menu offers it in its contexts. The Edit kind lists it.
   S, or A for Create tools, lists it at its pick's level. The right-click menu lists it with that
   level selected.
3. **Every row has a doc** and an initial value in range. The icon exists in luciaos-assets.
4. **docs/TOOLS.md is current.**
5. **Repeat** after the tool runs it again on a new selection.

### 3.6 Migration (no backward compatibility)

The order is set so that every step leaves `luc test` green. Old names and paths are deleted, not
kept.

- **M0. Lock behavior.** Before moving anything, add the node/step parity checks for every
  existing tool. Some will not agree today: for example, Edit CAD's Fillet passes texts the node
  does not. Record those and fix them first.
- **M1. `Tool`, `Invocation`, registry; mesh tools.**
  - Add `tool.luc`, `tool_registry.luc` and `verb_tools.luc`. Extend luce-geocore's `Verb` with
    the fields of §3.2, and fill them for all 30 verbs.
  - Edit Mesh's tools come from the registry. Delete `edit_mesh.tool_names`, `tool_levels`,
    `tools.tool_run` and its table, and `EditTool` for mesh tools.
  - `EditStep` becomes `Invocation` plus the recipe fields.
- **M2. Surfaces read the registry.**
  - Menus, marking menus, the right-click menu, Repeat, icons and the tool bar.
  - Delete the name lists in `marking_items`, `top_menus` (the CAD submenu), `viewport_menu`
    (the `modify[n]` indexing), `repeat_items`' kind map and `feature_handles`' kind lists.
  - Edit Mesh gains right-click and Repeat here.
- **M3. CAD tools, family by family.** Each family becomes `tool_*.luc` files with picks and
  rows, its node wrapper and step branch deleted:
  1. Fillet and Chamfer (`cad_blends`, the inspector's special cases into row conditions);
  2. the Modify features (`cad_modify`, `modify_commands`, `modify_picks`' node rows);
  3. Offset Face and Reblend;
  4. surfacing (`cad_surface_nodes`, `edit_cad_surfaces`, `surface_commands`);
  5. builders and blends;
  6. Align;
  7. curves;
  8. NURBS structure steps.

  At the end `edit_cad.ran` has no family chain, and `edit_cad_picks` and `modify_picks` are one
  prompt module. Extrude, Revolve and Sketch keep their command paths (they start from a sketch's
  profiles) but are `Tool`s for menus and Repeat.
- **M4. Gestures.** Today's knife stroke and PolyDraw placing become the `stroke` and `place`
  gesture modules. `hover` and `slide` arrive with Loop Cut and Edge Slide in stage 3.
- **M5. Docs generated.** docs/TOOLS.md replaces MODELING.md's hand lists of tools; MODELING.md
  keeps the concepts.

Expected size: the wiring layer (5,206 lines) should lose about half; that is an estimate, not
a measurement. Each CAD tool's footprint becomes one declaration file plus its op. Each mesh
tool's becomes its luce-geocore file.

Timing: M0–M5 start after the CAD Stage 8 work in flight lands. The two collide in
`edit_cad.luc`, `blend_ops.luc` and `node_catalog.luc`.

## 4. Nodes and editing: where Houdini differs

The same operation behaves differently as a node and as an interactive edit. The definition in §3
must allow for both.

- **What a node keeps.** A Houdini SOP keeps its group as text: numbers, or a pattern such as
  `@P.y>0`. It is re-evaluated when upstream changes, and numbers break when topology changes.
  Our guard reports that ("Group was selected on different topology"). An Edit step is recorded
  once and never re-resolved. For CAD both keep names, which survive upstream edits.
- **Rule-based groups.** Houdini's PolyBevel, PolyExtrude and Group SOPs take *rules*: "edges
  sharper than 30°", "boundary edges", "faces facing +Y". A rule is re-evaluated each cook, so a
  node stays valid as its input changes. Blender's and Cinema 4D's tools take only the selection.
  We have the rule language already (group expressions). Missing are the functions for angle,
  sharpness, boundary, non-manifold and sides (§5.2), so that a selection tool can also be
  written as a rule in a node's Group.
- **Interactive drags.** Blender's Bevel and Inset, Modo's tools and Cinema 4D's tools set their
  main value by dragging in the viewport. Houdini's PolyBevel and PolyExtrude states drag
  handles. A node only stores the value. Both write the same row, so the drag is a property of
  the tool (`drag`), not of the node or the step.
- **Repeat and Last-operation panels.** Blender's "Adjust Last Operation" panel, Cinema 4D's
  attribute pane for the active tool, and our tool bar are the same idea: after a tool runs, its
  values stay editable until the next tool. Houdini needs no such panel: the node *is* the
  panel.
- **Gestures that are not values.** A knife stroke, PolyDraw's corners and a Loop Cut's hovered
  ring are inputs a node cannot ask for in its parameter pane. Ours record them as numbers after
  the parameters (`Verb.trailing`; the knife's plane point and normal), so a node replays them.
  Keep that rule: a gesture's result is always numbers or picks in the invocation, never camera
  state.
- **Soft selection and symmetry** belong to the Edit node today (its Soft radius, Falloff and
  Symmetry rows). Houdini puts soft radius on each SOP (Edit, PolyExtrude…), Blender in the
  scene's tool settings. Ours fits Edit: they are settings of how you edit, so steps record them.
  A node that wants them uses a Soft Transform-style row. That needs nothing new until Bend and
  Taper (§5.4) take a falloff.

## 4b. Edit nodes hold their result

The owner, 2026-10-13: "the Edit Mesh — sure it needs to support undo, but we're not recording
history of what's happening in the node really — it's a node that as an output holds the new
thing that we've modeled — so inside this single node there is no stack that we need to process.
[…] It's all held inside the Edit Mesh node as an absolute representation of what we did there."

**The model** (`src/edit_held.luc`, `src/held.luc`, `src/held_store.lucb`; the framework's: Edit
Mesh, Edit CAD and Edit SDF take part by setting `EditKind.holds`):

- **An Edit node holds its result.** Every action (a move, a tool, a primitive, a deletion)
  replaces it; the node's cook returns it with no work. The worker replays nothing: it reads
  the held result by its content key from `HeldStore` (Base; Luce objects never cross threads),
  and the request carries the key, not steps.
- **Heavy actions run on the worker** (owner: modeling must be absolutely realtime; the UI never
  blocks). With the compute worker, every Edit CAD action and every Edit Mesh action but a
  gizmo's move and a sculpt stroke (which follow the pointer on the UI thread and cost only what
  moved) run there (`EditKind.background`): the node names the result it will hold (`held_key`,
  the base's key and the step's) and the base it runs on (`held_base`), keeps showing what it
  held, and its node in the network shows the action's progress; the worker runs the step on the
  base, keeps a drag's frames as its own (a CAD result never crosses as a file per frame) and
  puts the released result in `HeldStore`, which the node takes when the report comes
  (`edit_held.adopt`). A drag adjusting such an action sends each frame's step; requests
  coalesce (at most one waits for the worker), so the worker cooks only the newest values and a
  stale result is never shown. Undo is one step per action as before; a result the worker made
  is found again by its key. A project saved while one runs runs it first. Measured
  (`tests/editor/background_action_tests.luc`, headless): a Boolean of two 100k-face spheres
  held the UI thread 124–149 ms; with the worker the command returns in ~6 ms and the UI's
  longest turn while it runs is under 1 ms. Moving an Edit CAD box's top face held it 17 ms;
  with the worker the command returns in 1 ms. In the real window (`tools/preview.py --scene
  held_heavy --background`, two 1M-face spheres, Subtract): frames keep coming every 16.7 ms
  while the worker runs the 0.6 s Boolean; the frame the result first shows takes ~80 ms (the
  new 1M-face mesh's overlay and upload; its edges and shading normals are made on the worker
  before it is published). Captures: `held_heavy_running`, `held_heavy`.
- **Adjust last action** (owner answer 7, Blender's redo panel): the node keeps the result before
  its last action (`Held.base`) and that action as its one step (`Node.edits`), so the tool bar,
  a drag after the tool and Repeat's numbers run it again from the base. The next action bakes it:
  its result becomes the new base. There is no stack beyond that.
- **Undo** keeps the node's earlier results in the app's undo history, one entry per action, a
  whole drag one entry. They are immutable and share their arrays (a move shares everything but
  the positions; a topology tool shares nothing it did not rebuild). **The memory bound**: at
  most 64 changes, and the held results the history keeps take at most 2 GiB beyond the graph's
  own, each shared array counted once from the newest change back (`Workspace.bound_history`,
  `HeldStore.footprint`); older changes go and the newest always stays. Results nothing reaches
  (graph, gesture, history) are released from the store after every rebuild.
- **Input.** A wired Edit Mesh starts from its input's result when it is made (cooked once on the
  UI thread); later changes upstream do not flow in. The inspector then says "Input changed:
  Reload Input takes it", and **Reload Input** (the inspector's button, Modify › Reload Input)
  starts over from the input as it is now, one undo step. The Reference input (retopology) stays
  live: Shrinkwrap and Relax read it when they run.
- **Create inside.** Every Create entry is offered at every level with nothing selected (they were
  pale because a tool with no selection needed `whole`; primitives, Poly Pen and Sculpt need
  none). A primitive adds a piece of its own, selected at the Object level.
- **Saving.** A project keeps each held result beside it as a luce-geocore crate,
  `<name>.held/n<id>.prism` (binary, written only when its key changed), its last action baked
  in; the node's line names the file. Loaded, it is the node's result with nothing to adjust.
  Old step recipes do not load (no backward compatibility).
- **Realtime.** A drag never serializes or replays anything: the move runs on the held mesh in
  Base, and while it lasts the shown Edit node's mesh is drawn as the action made it, in place of
  the cooked one, with no cook here or on the worker until the drag ends
  (`Workspace.show_held`); its GPU arrays update only where points moved. luce-geocore's moves
  became O(what moved): a few faces' points found from their corners
  (`selecting/convert.lucb: sparse_points`), the bounds grown from the last mesh's when no
  moved point stood on them (`position_edit.moved_bounds`), and the degenerate-face check made
  only round the moved points. Transform Components of 1,000 faces of a 1M-face grid went from
  14.1 ms to 1.5 ms (luce-geocore alone). Each frame of a drag is made over the last frame's
  mesh (`Verbs.run`'s `over`, `Workspace.drag_shown`), so its normals, shading layout and GPU
  copies change only where points moved since; a shading cache whose mesh is gone gives its
  column to the next instead of a copy (`ShadingCache.surrender`), and the viewport looks a
  tool's icon up again only when the context changes.

Measured (`tests/editor/held_speed_tests.luc`, M-series Mac, headless; a pointer move from the
request to a result the viewport draws):

| Drag | Before (recipe replay, local cook) | Held |
| --- | ---: | ---: |
| A cube's edge | 3.8 ms | 0.44 ms |
| 1,000 faces of a 1M-face grid | 282 ms | 2.0 ms |
| The same with the compute worker | (worker cook and a deep copy per move) | 1.9 ms |

In the real window (`tools/preview.py --scene held_drag --opt 3`, with the compute worker, 123
moves of the same 1,000 faces): the move takes 2.1 ms on average (2.8 ms worst) and frames come
every 16.5 ms on average (20.6 ms worst): the display's 60 Hz. Before the per-frame work above
(the move from the base each frame, the shading switched to per-corner each frame, the icons
looked up each refresh) frames came every 28.9 ms.

**Mesh Boolean** (luce-geocore `verbs/boolean.lucb` and `booleans/`; label Boolean, Modify ›
Combine; a node and an Edit Mesh action from the one definition). Union, Subtract or Intersect
of closed pieces: with one pick of several pieces (Object level: faces sharing a `path`, else
connected parts) the piece holding the lowest face is A and the rest B; a second pick makes its
pieces B. The result is one piece (A's path) and the output selection. Exact and deterministic:
Shewchuk-filtered orientation predicates with exact fallbacks, cut points kept as exact
homogeneous coordinates named only by input ids, a constrained triangulation per cut triangle,
and patches kept by their exact winding numbers (after Zhou et al. 2016 and Cherchi et al.
2022; no code taken). Results are stored with f64 points (chained Booleans survive ~43 steps
instead of 20), which a move shares rather than copies (luce-geocore: a moved point's f32
position no longer rounds its f64 point, so it reads from f32): 1,000 faces of a 1M-face
result drag in 1.6 ms a move with the worker, as a plain grid's do (3.2 ms when each move
copied the f64 column); an operand that is not closed is
refused, naming the pick, and a result that would not close is an error, never an open mesh.
Two UV spheres of 100,352 faces each: Union 70 ms, Subtract 68 ms, Intersect 62 ms; of 999,698
faces each: 479, 465 and 416 ms (luce-geocore docs/API.md). Inside one Edit Mesh: two boxes, one
moved into the other, both picked, Boolean, and Operation switched on the tool bar
(`tests/editor/held_edit_tests.luc: boolean_inside`; captures `held_boxes`, `held_boolean`,
`held_subtract`).

**Edit CAD and Edit SDF hold theirs too** (owner, 2026-10-13: the same model). `EditKind.holds`
is set for both; the framework above is unchanged. Edit CAD holds its bodies, free curves and
sketches; Edit SDF its SDF program. Case by case for Edit CAD:

- **Sketches** are objects of the held model (luce-cad `CadSketches`). Drawing changes the last
  action while it made the sketch, else is an Edit Sketch action. Editing a sketch later changes
  the sketch, not a body already extruded from it: the extrude was baked when the next action
  came (as in a direct modeler; Fusion's timeline would replay it).
- **CV moves** run on the held surfaces; a drag adjusts its one action.
- **Align** (owner rule: a CV move on rows an Align set runs that Align again) is a relation held
  as data with the bodies (`GeometryData.aligns`), carried from action to action, saved with the
  held result (`held_aligns`) and read back on load.
- **Reblend** works on the held bodies as they are: luce-cad identifies their constant blends by
  shape, so no fillet history is needed.
- **Names**: an action's faces are named `#<node>s<n>`, `n` counted across baked actions
  (`Held.actions`, saved as `held_actions`), so names never repeat within a node.
- **Tolerances** (the kernel agent's project tolerances): held bodies do not cook again when the
  project's tolerances change; each is checked against them instead (luce-cad `rechecked`), edges
  off their faces by more than the new positional tolerance made tolerant, and the node says how
  many (`edit_held.recheck`, one undo step with the setting).
- **The timeline strip** shows only the adjustable last action: there is nothing earlier to roll
  back to (undo goes back instead).
- **The worker** reads held CAD sets from a crate in a per-process temporary folder (a set holding
  luce-cad objects cannot be stored as plain columns); plain sets stay in memory.
- A drag whose values cannot be built fails the node while it lasts and the viewport keeps the
  last good result; let go, the warning names the action (`"Shell could not be built: …"`).

Measured (`held_speed_tests.cad_action_cost`, from the command to the result): moving a box's top
face as an Edit CAD action took 22.5 ms after 1 action and 23.1 ms after 40 with the recipe and
its checkpoints; held, 16.2 ms and 17.2 ms. Captures: `held_cad` (a box and a cylinder made in one
Edit CAD, the cylinder moved), `held_sdf` (a sphere and a box made in one Edit SDF, the box moved
over the sphere and set to Subtract).

Edit GSplats still keeps a recipe; it is recommended to follow (its held result would be the
cloud with its deletions, moves and recolors; the same `holds` flag and a run_over for moves).

## 5. The polygon tool set

### 5.1 Create

Status column, here and below:

- **N**: a node (verb or luced-3d node);
- **E**: an Edit Mesh tool or primitive;
- **~**: partly there (see the note);
- **—**: missing.

| Tool | What it does, options | Best reference | Today |
| --- | --- | --- | --- |
| Box | Size per axis, **divisions per axis**, bevel-free | Houdini Box (divisions), Blender Cube | N E: one size, no divisions |
| Sphere | **UV** (rows, columns) and **ico** (subdivisions); **quad sphere** (a subdivided cube, Houdini's Polygon Mesh type) | Houdini Sphere (primitive types); Blender UV/Ico Sphere | N E: UV, one segment count |
| Cylinder, Cone | Radius top and bottom, height, sides, **height rows**, **cap rings**, cap type (n-gon, fan, none) | Blender, Houdini Tube | N E: sides only; caps n-gon |
| Torus | Rings, sides, major and minor radii | Blender | N E: one count |
| Grid, Plane | Size, rows and columns apart | Houdini Grid | N E: square, one count |
| Disc / Circle | Sides, fill type | Blender Circle | — |
| Tube | Cylinder without caps, with thickness | Houdini Tube | — |
| Capsule, platonic solids, helix | | Houdini Platonic Solids, C4D | — |
| PolyDraw | Clicks place corners (on points, the surface or the ground); Enter makes the face | Blender Poly Build; Houdini TopoBuild | N E |
| Poly Pen / Poly Build | One tool that adds faces from edges (Ctrl-drag an edge extrudes a quad), splits, deletes and moves under the pointer, with no selection first | C4D Polygon Pen [doc S24]; Blender Poly Build (`editmesh_polybuild.cc`); Houdini TopoBuild [doc] | — |
| Retopology | Poly Pen working on a reference mesh's surface: new points stick to it, the reference drawn through | Houdini TopoBuild (reference input); Blender snapping + Poly Build | ~ PolyDraw places on the surface under the cursor |
| Primitive placement | Create on the clicked surface or plane, size by drag | Blender's interactive Add (`add_primitive_tool`), Plasticity | ~ Placing on surfaces exists for PolyDraw and Plane from Face |

Primitives belong in the registry like any tool: Create section, Objects family, no picks. Their
options are their rows. In Edit Mesh a primitive is a step that adds a piece, as today. The A menu
shows them; the tool bar shows the new piece's rows until the next step (FUSION's open idea
"Create steps' sizes on the bar").

### 5.2 Select

Selecting is the gap the owner named. Today's selection is a luce-geocore `Selection` (bits on
a domain) with word-parallel passes: invert, grow, shrink, border, flood (connected), loop and
ring (`Selection.walked`). Group expressions add `grow()`, `shrink()`, `border()`,
`connected()`, `loop()`, `ring()` and attribute tests. These are reached only from Modify ›
Selection. No click reaches loop, ring or connected.

**Click gestures** (proposed; the modifier rules are ours already: Shift adds, Ctrl or Cmd takes
away, Alt is the camera):

| Gesture | At Edge | At Face | At Point | Reference |
| --- | --- | --- | --- | --- |
| Double-click | Edge loop | Connected island | Connected island | Houdini (edges) [doc], Maya (edges) [doc], Modo (faces, points: connected) [doc], C4D (faces: connected groups) [doc] |
| Shift + double-click | Add the loop; on the loop of the edge picked last, only the run between them | Add the island; on a face beside the one picked last, the face loop through both | Add the island | Houdini add [doc]; Maya partial loop [doc] |
| Ctrl/Cmd + double-click | Remove the loop | Remove the island | Remove the island | Houdini remove [doc] |
| Double-click the same edge again | Its ring (again: the loop) | — | — | Blender's click-again cycling [src] |
| Shift + Ctrl/Cmd + click | Shortest path from the last picked element (edges, faces or points) | same | same | Blender Ctrl-click [src]; Maya Shortest Edge Path [doc]; C4D Path Selection [doc] |

A loop on a boundary edge runs along the boundary, and a double-click on it again gives the
whole boundary instead of a ring. The walker follows Blender's rules [src `bmesh_walkers_impl.cc`]:

- through points of four edges, to the opposite edge;
- stopping at poles and non-manifold edges;
- along boundary fans on a boundary;
- across a pole whose biggest face is an n-gon only along that n-gon's side;
- face loops through quads only;
- delimit by seams or sharp edges when asked.

Today's `loop()` is close. Its pole and n-gon rules need checking against these.

**Select tools** (the Select family; each also a group function where it is a rule, so a node's
Group can say it):

| Tool | What it selects, options | Best reference | Today |
| --- | --- | --- | --- |
| All, None, Invert | | | ~ All, Invert; None by clicking empty space |
| Grow / Shrink | One ring of neighbors; across edges only or across points (face step) | Blender `use_face_step` [src]; C4D Grow "Using Edges Only" [doc] | N(group fn) E: edges-only |
| Loop / Ring (of the selection) | Every selected edge's loop or ring; partial between two | Blender multi loop/ring [src] | E (commands, Edges only) |
| Face loop, point loop | | Blender, Maya | — |
| Boundary loop | Each selected boundary edge's whole boundary | Blender `select_boundary_loop` [src]; Houdini Shift+B [doc] | ~ `border()` is the region's border |
| Region ↔ loop | Faces' outline as edges; a closed loop's smaller (or bigger) side as faces | Blender `region_to_loop`, `loop_to_region` [src] | ~ border |
| Connected (linked) | The islands touching the selection; **delimit** by seam, sharp, material, UV island, normal | Blender Select Linked [src] | E (flood), no delimits |
| Shortest path | Between two elements; topology distance or length; across faces (diagonals); **fill region** (every shortest path's elements) | Blender (`bmesh_path.cc`, `bmesh_path_region.cc`) [src]; Houdini Group Find Path | — |
| Select Similar | Like the selected by: points (normal, valence, faces); edges (length, direction, face angle, sharp, seam, crease); faces (area, sides, perimeter, normal, coplanar, material); equal, greater, less, with a threshold | Blender (`editmesh_select_similar.cc`, KD-trees) [src] | — |
| Sharp edges | Face angle above a threshold | Blender [src]; C4D Phong Break Selection [doc] | — |
| Linked flat faces | Flood across edges flatter than an angle | Blender [src] | — |
| By normal | Faces facing a direction within a spread | Houdini Select by Normal [doc] | ~ `@N.y>0.9` rules |
| By sides | Triangles, quads, n-gons; =, ≠, <, > | Blender [src] | — |
| Non-manifold | Wire, boundary, more than two faces, opposite winding, pinch points | Blender [src] | — |
| Loose | Points and edges without faces | Blender | — |
| Interior faces | Faces all of whose edges have more than two faces | Blender | — |
| Checker | Every nth along the selection from the active element: nth, skip, offset | Blender `select_nth` [src] | — |
| Random | Ratio, seed | Blender | — |
| Mirror | The selection's mirror across X, Y or Z | Blender | ~ Symmetry on the Edit node mirrors steps, not the selection |
| Side of active | Everything beyond the active element along an axis | Blender `select_axis` [src] | ~ `@P.x>0` |
| By attribute, group | A boolean attribute, a named group | Houdini, Blender | ~ group expressions |
| Selection sets | Save, recall, add to, remove from a named set; sets are named groups on the mesh | Maya Quick Select Sets, C4D Set Selection, Houdini groups | ~ Selection Group node; no Edit UI |
| Convert | Faces ↔ edges ↔ points (all or any) | Modo Alt [doc] | E (level switch carries over) |
| Hide / Unhide | Hide selected, hide unselected, reveal | Blender H, C4D | — |
| Soft selection | Radius, falloff curve, by surface distance (not only straight-line) | Maya Soft Select (surface mode); Modo falloffs | E: straight-line distance, four falloffs |
| Symmetry | Selection and tools mirrored | Maya, Blender | E (Edit node row) |
| Through the depth | Boxes select hidden elements too | Blender X-ray, our V | E |
| Lasso, paint select | Free shape; brush across the surface | Blender, Maya | Splats only |

**The active element.** Path, checker, partial loop and "side of active" need the element picked
last. Blender keeps a selection history for this. The `Selection` needs an active element
(the last pick) carried with it. That is a small addition to luce-geocore.

### 5.3 Modify

Status as in §5.1. "Drag" is the row a viewport drag sets.

**Extrude family**

| Tool | What it does, options | Best reference | Drag, gesture | Today |
| --- | --- | --- | --- | --- |
| Extrude (region) | Faces moved out as a region with side walls; distance, inset, divisions; **twist and taper along the walls**; along normals or one direction; **Manifold** (an inward push cuts cleanly by dissolving the walls left flat: Blender's Extrude Manifold [src `editmesh_extrude.cc`]) | Houdini PolyExtrude (spine, twist, taper, per-face front transform) for the node; Blender for the drag | Distance; Cmd drag = inset | N E: distance, inset, divisions, individual; no twist, taper, spine or manifold |
| Extrude individual | Each face apart | Blender, C4D (Preserve Groups off) | Distance | ~ a row of Extrude |
| Extrude edges / points | Edges into quads; points into edges | Blender (E on edges/verts) | Distance | Edges: N E; points — |
| Extrude along curve | Faces along a curve with twist and scale ramps | Houdini PolyExtrude Spine; C4D Sweep | Picks a curve | — |
| Extrude to cursor | Ctrl-click makes a vertex/edge/face extruded to the click | Blender (`dupli_extrude_cursor`) | Click (place) | — |
| Matrix extrude | Extrude repeated n times, each step turned and scaled | C4D Matrix Extrude; Blender Extrude Repeat | Steps | — |
| Smooth Shift | Extrude with the walls kept smooth (no wall where faces are flat) | Modo, C4D | Distance | ~ Extrude's region mode |
| Inset | Rim moved in by thickness; depth; individual; **outset**, **even**, **relative**, **edge rail**, **boundary** (open edges inset too) [src `bmo_inset.cc`] | Blender | Thickness; Cmd drag depth | N E: thickness, depth, individual, clamp; no outset/even/relative/rail |
| Poke | Each face fanned around a new center, offset along the normal | Blender; Modo Poly Poke | Offset | — |
| Solidify / Thicken | Shell with thickness; even; rim; flip; offset (−1..1); creases on the rims | Blender Solidify modifier (complex mode for non-manifold); Modo Thicken | Thickness | — |
| Wireframe | Each edge a tube, faces gone | Blender Wireframe | Thickness | — |

**Bevel, chamfer**

| Tool | What it does, options | Best reference | Drag, gesture | Today |
| --- | --- | --- | --- | --- |
| Edge Bevel | Offset types (offset, width, depth, percent, absolute); segments; **profile** (superellipse 0..1) and **custom profile** (a ramp); **miters** outer sharp/patch/arc, inner sharp/arc, spread; corner patch grid vs cutoff; clamp; loop slide; harden normals; mark seams/sharp | Blender (`bmesh_bevel.cc`): the most complete corner handling (grid patches refined by Catmull-Clark at N-sided corners); Houdini PolyBevel for rule groups and per-edge offset attributes | Offset; wheel = segments; P = profile | N E: offset, segments, profile, clamp; one patch face per corner; no miters, no custom profile, no vertex bevel |
| Vertex Bevel | Each point cut off, a face in its place | Blender (Affect: Vertices) | Offset | — |
| Chamfer (C4D-style face) | Faces' borders chamfered with a rounding | C4D Bevel, Polygon mode | Offset | ~ Inset + Bevel |

**Cuts and connections**

| Tool | What it does, options | Best reference | Drag, gesture | Today |
| --- | --- | --- | --- | --- |
| Loop Cut | Cuts across the ring under the pointer, previewed while hovering; number of cuts (wheel), smoothness, **then slides** (even, flip) | Blender Loop Cut and Slide (hover ring preview [src `editmesh_preselect_edgering.cc`]); Maya Multi-Cut Ctrl-click | hover + slide | N E on selected edges' rings; no hover, no slide stage |
| Offset Edge Loops | Two loops either side of the selected loop, slid apart; cap ends | Blender (`bmo_offset_edgeloops.cc`) | Offset | — |
| Knife | Strokes cut across faces; snapping to points and edge middles; angle snap; cut through vs visible only; several segments before Enter | Blender Knife (multi-segment, snapping); C4D Knife Line/Loop/Plane modes | stroke | E: one straight stroke = a plane clip; not multi-segment, no snapping |
| Bisect / Plane cut | A plane cuts; fill the cut; clear one side | Blender Bisect; Houdini Clip | stroke | N (Clip) E (Knife) |
| Connect | Edges between selected points across faces; or between edge middles (the "Connect" ring cut) | Blender J (vertex path); Maya Connect | — | N E |
| PolySplit / Multi-Cut | Click points on edges and faces in order; edges made between them | Maya Multi-Cut; Houdini PolySplit; C4D Polygon Pen | place | — |
| Edge Slide | Edges slid along the faces beside them; even, flip, clamp | Blender (G G) | slide | N E: an amount, no slide gesture |
| Vertex Slide | One point slid along a chosen edge | Blender (Shift V) | slide | — |
| Rotate Edge (spin) | An edge turned within its two faces, CW/CCW | Blender; C4D Spin Edge | — | — |
| Subdivide edges | n cuts on each selected edge, faces patterned | Blender Subdivide (quad corner modes) | — | ~ Subdivide splits the selected faces or edges (Straight Cut around), levels not cuts |

**Delete, dissolve, merge**

| Tool | What it does, options | Best reference | Today |
| --- | --- | --- | --- |
| Delete | Faces, edges and faces, only faces, points | Blender's delete menu | N E (faces; points delete faces using them) |
| Dissolve | Faces joined across edges; points removed between two edges | Blender, C4D Melt | N E |
| Limited Dissolve | Edges whose faces meet flatter than an angle dissolve, flattest first; delimits | Blender (`bmesh_decimate_dissolve.cc`) | — |
| Delete Edge Loop | A loop removed and its faces merged, the ring healed | Blender (`delete_edgeloop`) | — |
| Collapse | Each selected edge island to its center | Blender, C4D | ~ Merge Points per island |
| Merge (at center, first, last, cursor) | Points to one place | Blender M; C4D Weld | N E (Merge Points) |
| Merge by Distance / Fuse | Points within a distance welded; connected-only option | Blender Weld modifier (connected mode) | N E (Fuse) |
| Target Weld | Drag one point onto another to weld | Maya Target Weld; C4D Weld | — |
| Clean / Mesh Cleanup | Unused points; degenerate faces; doubles; flip inconsistent | Houdini PolyDoctor; Blender Clean Up menu | ~ Clean (unused points) |

**Split, rip, separate**

| Tool | What it does | Best reference | Today |
| --- | --- | --- | --- |
| Split | Faces detached | Blender Y | N E |
| Rip | Edges or a point split, the side nearest the pointer dragged away; Rip Fill | Blender V / Alt V (`editmesh_rip.cc`) | — |
| Edge Split | Faces split apart along edges (hard edges) | Blender, Houdini Cusp | — |
| Separate / Extract | Faces become their own piece (`path`) | Blender P; Maya Extract | ~ Split; no new piece |
| Duplicate | Faces copied, optionally moved | Blender Shift D | N E (offset along normals) |

**Fill and bridge**

| Tool | What it does, options | Best reference | Today |
| --- | --- | --- | --- |
| Fill (make face) | Closed boundary loops capped; fan | Blender F (context-aware), Alt F | N E |
| Grid Fill | A hole filled with a quad grid; span, offset; shape carried in from the boundary | Blender Grid Fill (`bmo_fill_grid.cc`) | — |
| Fill Holes by sides | Every hole up to n sides | Blender | — |
| Bridge | Two loops joined; twist, cuts, interpolation (linear, blend path, blend surface), smoothness, profile, merge | Blender Bridge Edge Loops | N E: twist only |
| Close Hole | Click a boundary, it is capped | C4D Close Polygon Hole (hover preview) | — |

**Sweeps, symmetry, arrays**

| Tool | What it does | Best reference | Today |
| --- | --- | --- | --- |
| Spin | Edges/faces swept round an axis; steps, angle, merge seam | Blender Spin | N E: full turn about Y default |
| Screw | Spin with a rise per turn | Blender Screw | — |
| Mirror | Pieces reflected across a plane, welded on it | Blender Mirror modifier (clip, bisect) | N (Mirror, PolyMirror) E (PolyMirror) |
| Symmetrize | One side mirrored over the other, the seam welded | Blender (`bmo_symmetrize.cc`) | — |
| Snap to Symmetry | Mirror pairs moved to their averaged places | Blender | — |
| Array / Copy | Copies by offset, count, fit; merged ends | Blender Array; Houdini Copy and Transform | N (CopyTransform) |

**Subdivision and reduction**

| Tool | What it does | Best reference | Today |
| --- | --- | --- | --- |
| Subdivide | Faces split; Catmull-Clark or linear | Houdini Subdivide | N E |
| Subdivision display | Limit surface shown, cage edited | Houdini, Modo Tab | N |
| Crease | Edge sharpness for subdivision | Houdini, Blender | N E |
| Un-subdivide | Undo one subdivide on a regular grid | Blender (`bmo_unsubdivide.cc`) | — |
| PolyReduce / Decimate | Quadric edge collapse to a ratio; keep boundary, symmetry, weights | Houdini PolyReduce; Blender Decimate (`bmesh_decimate_collapse.cc`) | — |
| Triangulate | Quad method (beauty, fixed, shortest diagonal), n-gon method (beauty, ear clip) | Blender | N E (one method) |
| Quadrangulate (tris to quads) | Triangle pairs joined by quality score; delimits | Blender (`bmo_join_triangles.cc`) | — |
| Remesh | Voxel or quad remesh | Houdini Remesh, Quad Remesher | ~ Mesh to SDF → Convert to Mesh |

**Shaping (point tools)**

| Tool | What it does | Best reference | Today |
| --- | --- | --- | --- |
| Smooth / Relax | Laplacian smoothing; keep volume; boundary held; relax (even spacing only, shape kept) | Blender Laplacian Smooth; Modo Relax | N E (Smooth) |
| Flatten | Onto a best-fit plane | Blender Flatten; Maya | N E |
| Circularize | A loop or face region made a circle | Blender Circularize; Maya Circularize | — |
| Straighten / Space evenly | A path made straight, or its points spaced evenly | Blender Space Evenly; Houdini Edge Straighten, Edge Equalize | — |
| Make planar | Faces made flat in place | Blender | ~ Flatten |
| Noise | Displacement | Houdini Mountain | N E |
| Push along normals | Points moved along normals | Blender Shrink/Fatten; Houdini Peak | N E (Peak) |
| Snap to grid | | | N E (Snap) |

**Normals, edge data, UV seams**

| Tool | What it does | Best reference | Today |
| --- | --- | --- | --- |
| Reverse (flip) | Winding flipped | | N E |
| Recalculate outside | Consistent winding, facing out | Blender Shift N | — |
| Hard / soft edges | Sharp edge marks; by angle | Maya Soften/Harden; Blender Shade Auto Smooth | ~ Normal node (whole mesh) |
| Custom normals | Set from faces, average, point to target, weighted | Blender normals tools | — |
| UV seams | Mark, clear, from islands | Blender | — |
| Bevel weight, crease weight per edge | | Blender | Crease only |

### 5.4 Deform and sculpt-lite

| Tool | What it does, options | Best reference | Today |
| --- | --- | --- | --- |
| Transform components | Move, rotate, scale with soft selection and symmetry | Maya, Blender | N E |
| Bend, Twist, Taper, Squash | About an axis and an origin, limits along it; one node with a mode | Houdini Bend [doc]; Blender Simple Deform [src] | N E |
| Lattice | Points moved by a cage | Houdini Lattice Deform, Blender Lattice | N E |
| Soft Transform node | A transform with a falloff, as a node | Houdini Soft Transform | N E |
| Shrinkwrap / Ray | Points projected onto another mesh | Houdini Ray, Blender Shrinkwrap | N E |
| Corrective smooth | Smooth that keeps the rest shape's detail | Blender Corrective Smooth [src] | N E |
| Sculpt-lite brushes | Grab, smooth, inflate, flatten, pinch; radius and strength by drag; symmetry; on the Edit node as a step per stroke | Houdini Sculpt SOP; Blender sculpt; C4D Brush and Magnet | N E |
| Edge Transport, Edge Relax | Values or positions moved along edges | Houdini | N E (Edge Transport's distance; Relax) |

Sculpt-lite is a stroke gesture whose result is a displacement attribute or a point list stored
in the step. That keeps it a recipe step and keeps strokes undoable one at a time.

### 5.5 Analysis

| Tool | What it shows | Best reference | Today |
| --- | --- | --- | --- |
| Mesh Check | Overlays and counts: non-manifold edges, boundary, n-gons, triangles, poles (3 and 5+), zero-area faces, zero-length edges, flipped neighbors, self-intersections; each a click to select | C4D Mesh Checking; Houdini PolyDoctor; Blender 3D-Print toolbox | — |
| Measure | Area, perimeter, curvature per element | Houdini Measure | N |
| Statistics | Points, edges, faces, tris, selected counts in the viewport | Blender overlay statistics | ~ geometry sheet |
| Face orientation | Front/back tint | Blender overlay | — |
| Edge length, angle readouts | Live while transforming | Blender overlay "Edge length" | — |
| Topology flow overlay | Loop lines across quads | (none standard) | — |

The Mesh Check should share its finding passes with the Select tools: "Select non-manifold" and
the check's overlay are the same pass, shown two ways.

## 6. Interaction model for Geo

### 6.1 One way to run any tool

1. **Pick, then tool.** Select at the tool's level, then run it from S, the right-click menu or
   Modify. The selection is its first pick. With nothing selected the node waits (Tool → Select,
   as now) or, in Edit Mesh, says "Select edges first".
2. **Drag sets the main value.** After a tool with a `drag` row runs, dragging in the viewport
   (anywhere, not on a handle) sets that row until the button is released:
   - Houdini's PolyBevel state does this [doc];
   - Cinema 4D's Extrude and Bevel do it [doc];
   - Blender's modal tools do it [src].

   A click without dragging accepts. The wheel steps a count row (Bevel's segments, Loop Cut's
   cuts), as Houdini and Cinema 4D do [doc]. Shift snaps the value. The drag is one undo step
   with the tool.
3. **The tool bar stays live** for the last step (as now) until another tool runs. That is
   Blender's Adjust Last Operation and Cinema 4D's Realtime Update [doc].
4. **Repeat** is the first entry of S. It runs the last tool with its last values on the new
   selection: Cinema 4D's New Transform [doc], Fusion's Repeat.
5. **Gesture tools** take their input first:
   - Knife: strokes;
   - PolyDraw and Poly Pen: clicks;
   - Loop Cut: hover a ring, wheel for cuts, click, then drag to slide (Cinema 4D's Path/Loop
     Cut keeps the cut editable after [doc], which our tool bar gives).

### 6.2 Marking menus in Geo

- **A: Create.** Primitives, PolyDraw, Poly Pen; in Geo outside an Edit node, the same as nodes.
- **S: Modify.** Repeat first. Then the tools whose first pick takes the current level, grouped
  by family: at Edges, Bevel, Loop Cut, Bridge, Connect, Edge Slide…; at Faces, Extrude, Inset,
  Poke…. Tools that do not apply are left out, as Edit CAD already does.
- **D: Select.** In Geo contexts, holding D opens the Select tools for the level: Loop, Ring,
  Connected, Grow, Shrink, Path, Similar, Sharp, Non-manifold, Checker, Invert. In a sketch D
  stays Constraints. D is the marking menu only (owner, §9 question 3): the display flag keeps D
  in the Network panel alone. Built in Stage 0.

The right-click menu lists the same Modify tools for the selection, then a Select submenu. With
nothing selected it lists Create.

### 6.3 Tool bar rows: what Geo tools show

Every mesh verb's `ParmSpec` gains `bar` and `more`. The rule: the rows a modeler changes while
looking at the result go on the bar (Bevel: Offset, Segments, Profile; Extrude: Distance, Inset,
Divisions). Everything else goes behind More options (Bevel's miters, clamp, harden normals).

## 7. Gaps, ranked

Ranked by how often a modeler reaches for the tool, then by how much other work depends on it.

1. **The tool definition and its surfaces** (§3). Every later stage adds tools, so this pays back
   at once. Edit Mesh gains right-click, Repeat and level-filtered S here.
2. **Selection by click.** Double-click loops and islands, path, the D menu, and the active
   element.
3. **Interactive drag** for Extrude, Inset, Bevel; Loop Cut with hover and slide; Edge Slide as a
   gesture.
4. **Bevel to Blender's level.** Vertex bevel, miters, custom profile, grid corner patches,
   offset types.
5. **The everyday missing tools.** Knife with segments and snapping, Grid Fill, Bridge options,
   Solidify, Rip, Edge Split, Delete Edge Loop, Collapse, Target Weld, Offset Edge Loops, Poke,
   Rotate Edge, Symmetrize.
6. **Select tools.** Similar, sharp, by sides, non-manifold, checker, delimits on Connected,
   selection sets, hide/unhide.
7. **Primitives with full options.** Box divisions, ico and quad spheres, caps and rows.
8. **Shape tools.** Circularize, Straighten, Space Evenly, Relax, Make Planar.
9. **Topology tools.** Quadrangulate, Limited Dissolve, Un-subdivide, PolyReduce, Triangulate
   methods.
10. **Normals and edge data.** Recalculate outside, hard/soft edges by angle, seams, bevel
    weights.
11. **Deformers.** Bend/Twist/Taper, Lattice, Shrinkwrap.
12. **Poly Pen and retopology.**
13. **Mesh Check.**
14. **Sculpt-lite.**

Already there and kept as they are:

- Extrude (regions, edges);
- Inset;
- Loop Cut on a ring;
- Bridge;
- Fill;
- Dissolve;
- Fuse, Merge Points;
- Subdivide, Subdivision, Crease;
- Spin, PolyMirror, Clip/Knife;
- Connect, Edge Slide;
- PolyDraw;
- Smooth, Flatten, Noise, Peak, Snap;
- soft selection, symmetry, Keep selection.

## 8. Staged build plan

Each stage ends with `luc test` green in luced-3d, and in luce-geocore when it changed. Each also
needs a preview capture for the docs and docs/TOOLS.md regenerated. Tests drive the workspace as
`edit_mesh_tests` and `select_tool_tests` do: events into the viewport, then the recipe, the
selection and the result checked. Each kernel is tested in luce-geocore first (its
`tests/mesh/*_checks.lucb`), on small fixtures with known counts.

**Stage 0: the tool definition, mesh tools** (§3.6 M0–M2). **Done 2026-10-13** (see "Stage 0 as
built" below).
- `Tool`, `Pick`, `Invocation`, `tool_registry`, `verb_tools`; luce-geocore `Verb` gains label,
  section, family, icon, picks, drag, gesture, whole, and `ParmSpec.bar`/`more`, filled for all
  30 verbs.
- Edit Mesh tools from the registry. Delete `tools.tool_run`, `edit_mesh.tool_names` and
  `tool_levels`.
- Menus, marking menus, right-click, Repeat and icons from the registry. Delete the hand lists.
- Tests:
  - `tool_registry_tests` (§3.5) passes for every mesh tool;
  - S at Edges lists Bevel and not Inset;
  - right-click with faces selected lists Extrude;
  - Repeat after Bevel bevels a new edge with the same offset;
  - removing a verb from `makers` removes it from every menu (no other edit).

**Stage 0 as built.**
- M0: `tool_parity_tests` landed first. It recorded ten tools whose starting numbers were not
  their node's (`tools.tool_run`'s Extrude 0.5, Bevel 0.5, Crease 0.5, Fuse 0.5…); M1 made the
  verb's initial value the only one, so a tool now starts where its node does (Extrude 0.2,
  Bevel 0.1, Crease 10).
- luce-geocore: `Verb` gained `label`, `section`, `family`, `icon`, `picks` (`PickSpec`: label,
  levels as `objects points edges faces`, prompt), `drag`, `gesture`, `whole` and `native` (the
  group kept on its own domain, for Select verbs); `ParmSpec` gained `bar`. `Verbs` reads them.
  `more` was left out: nothing shows More options yet (Stage 4's Bevel needs it). Every tool
  verb takes one pick for now; Bridge's two loops come with Stage 5.
- luced-3d: `tool_record.luc` (`Tool`, `Pick`, `Invocation`), `tool_registry.luc`,
  `verb_tools.luc`, `verb_rows.luc` (a verb's rows, moved out of `node_catalog` so the registry
  sits below it), `tool_menus.luc` and `tool_docs.luc`. `tools.tool_run`, `verb_defaults`,
  `edit_mesh.tool_names`, `tool_levels`, `EditStep.evaluate` and the "Extrude faces" command are
  gone. `EditStep` hands its tool an `Invocation`; it was not renamed, because Edit CAD's files
  use it throughout and move in Stage 1.
- Every surface reads the registry: Edit Mesh's tools (`EditTool` keeps its `Tool`), the node
  menu (already generated from the verbs), the tool bar (`bar`), Modify › Edit Mesh tools
  (Repeat and a submenu per family), Modify › Selection, A (primitives and placing tools), S
  (Repeat, then the level's Modify tools by family), D (Select), the right-click menu (Repeat,
  the level's tools by family, Select; with nothing selected, Create), Repeat, the prompts
  ("Select edges for Bevel", "Bevel works on edges"), the icons and docs/TOOLS.md
  (`tools/tool_docs.py`; a test fails when it is stale). The knife's stroke is found by its
  gesture, PolyDraw's placing by `gesture = "place"`.
- Menus order families by `tool_registry.family_order()` (family names, not tool names).
- A tool node that does not change topology keeps the selection, as its step does; a Select
  verb's node adopts its cook selection.
- Edit CAD's Noise, Flatten and Snap on CVs take their verbs and numbers from the registry; the
  rest of Edit CAD is untouched until Stage 1.
- Measured on luced-3d `src/` (string mentions of a mesh tool's label or verb name, CAD tools of
  the same name included): 4.5 files and 6.6 lines per mesh tool before; 1.7 files and 3.0
  lines after, every one of them a CAD tool, a family or category name, or the knife's
  Clip-specific stroke step. A mesh-only tool (Inset, Bevel, Loop Cut, Spin…) is named in no
  luced-3d source file.
- Adding a mesh tool is its luce-geocore file and one line in `makers` (and ORDER). Select
  Checker (§5.2) was added that way: `select_verbs.lucb` and one `makers` line; luced-3d
  needed no source change, and it is a node, a D entry, a right-click Select entry, a Modify ›
  Selection entry and a docs/TOOLS.md section. With it taken out of `makers`, luced-3d still
  type-checks: no surface names it.
- Tests: `tool_parity_tests` (node = step = cook for every tool), `tool_registry_tests`
  (declarations, docs/TOOLS.md current, S/D/A/right-click/Modify at every level in an Edit Mesh
  and on a plain node, S at Edges has Bevel not Inset, right-click on faces has Extrude, Repeat
  as a step and as a node, Select Checker, D in the viewport and the network); luce-geocore's
  `select_checks`.
- Not yet: the drag driver (Stage 3; `drag` is declared and documented), More options, multiple
  picks, the stroke and place gesture modules (M4).

**Stage 1: CAD tools onto the definition** (M3–M5). **Done 2026-10-13** (see "Stage 1 as
built" below).
- Family by family, in §3.6's order; `modify_picks` and `edit_cad_picks` become one prompt
  module; docs/TOOLS.md generated.
- Tests:
  - the parity check (node = step) for every CAD tool;
  - the existing CAD test files pass unchanged in what they assert;
  - the wiring-layer line count is reported in the commit.

**Stage 1 as built.**
- One declaration per CAD tool: `src/tool_<name>.luc`, 69 of them (Fusion's features, Modify
  features, blends, the surfacing tools, the builders and blends between surfaces, Align, the
  curves, the NURBS structure steps, the solids, Check, Sketch), each listed by one line in
  `src/cad_tools.luc`. A declaration is a `ToolEntry` (name, label, icon, node menu category,
  contexts, Edit kinds, step verb: what menus and icons read without building it) and the
  `Tool` it makes: section and family, doc, picks, rows, cook, drag row, gesture, inputs,
  starting numbers, handles, whether its value box opens, and what its node waits for.
- `Pick` grew what CAD needs: what a click gives (`pick_kinds.luc`: faces, a face, bodies, a
  body, edges, an edge, a point, curves, curve words, a blend's end, Align's input and master,
  an axis, profiles), where a node keeps it (a text or values) and where a step keeps it (its
  group, a text or numbers), when it is wanted, what taking it sets, its part of a shared text
  (a Fillet's set k), its summary and the inspector's buttons. `Invocation` carries a node's
  second input, memo and sketch, so one cook serves a node and a step (`cad_cook.luc` has what
  cooks share: names found on the pick geometry, a step's pick geometry, edges model by model).
- Generated from the declarations, the hand wiring deleted:
  - the CAD node catalog (kinds, categories, rows, inputs, descriptions) and node evaluation;
    `cad_nodes.evaluate_cad` is the registry's lookup, `cad_modify.luc` and
    `cad_surface_nodes.luc` are gone;
  - Edit CAD's tools and its step executor: `edit_cad.ran` keeps the kind's own steps
    (primitives, sketches, CV moves) and hands the rest to the step's tool; the eight-family
    chain, the families' `tools()` and `verbs()` lists and `edit_cad_surfaces.run` are gone;
  - one pick chain (`tool_picks.luc`) for nodes and steps, replacing `modify_picks.luc`,
    `edit_cad_picks.luc`, the CAD prompts of `tool_prompts.luc` and the builders' prompt
    labels; the prompt carries its tool and pick, which give its level, selection filter and
    hint; the inspector's pick rows come from the picks (its six CAD special cases are gone),
    and a tool bar row that makes a pick wanted (To object, Point to point) asks for it;
  - one command per tool (`tool_run.luc` runs it as a step in Edit CAD, a node in a CAD network,
    a mesh tool elsewhere), replacing `modify_commands.luc`, `surface_commands.luc` and the
    Fillet, Chamfer, Offset Face and Check commands; Press Pull dispatches to the tools;
  - the A, S and right-click menus and Modify › CAD tools by family at the selection's level
    (no `modify[n]` indexing), Repeat for every context (`last_cad_tool` and its map are gone),
    the handles (`Tool.handles`, no kind lists), the icons (the chain lost 60 CAD names) and
    docs/TOOLS.md, which now has a CAD part.
- The drag driver (Stage 3) takes a CAD step's drag row: luce-geocore's `Verbs.frame_at` gives a
  frame from the middle of what the step picked, so after Fillet, Offset Face, Shell, Reblend or
  Scale Body a drag anywhere sets the main row as it does for Bevel.
- Measured against `5546775` (src files naming the tool by its label or the constant holding
  it): Fillet 14 files and 36 lines before, 6 and 12 after (its declaration, Press Pull, the
  fillet-set command, and the sketch's own Fillet); Align 9 and 20, 7 and 10 (its ops and
  constants); Shell 9 and 17, 2 and 3 (its declaration and its kernel's branch); Fill Surface 6
  and 12, 3 and 11 (its declaration and ops). The wiring layer (the 21 files counted then:
  commands, picks, prompts, menus, marking menus, handles, icons, tool bar, Edit CAD's kind and
  the CAD node wrappers) was 5,717 lines; the 15 left are 3,173, and with the new
  `tool_picks`, `tool_run`, `cad_tools`, `cad_cook` and `pick_kinds` 4,331 (-24%). The
  declarations hold 2,416 lines, most of them rows and cooks moved out of `node_catalog`
  (1,029 to 816 lines) and the families' modules. `kind == "…"` and `in […]` tests went from
  459 to 361.
- Added by a declaration alone: **Scale Body** (`tool_scale_body.luc` and its line in
  `cad_tools.luc`): a node, an Edit CAD step, its rows and drag, a Bodies entry in S, the
  right-click menu and Modify, a docs/TOOLS.md section and a parity check, with no other file
  changed.
- Tests: `cad_tool_parity_tests` (node = step for every CAD tool that runs on a box's face,
  edge or body with nothing more to pick: Offset Face, Shell, Delete, Move/Copy, Remove, Scale
  Body, Fillet, Chamfer, Trim, Untrim, Trim Convert, Shrink, Stitch, Unstitch; and, through
  `cad_pick_parity.luc`, the tools that take more picks, clicked as their prompts ask:
  Replace Face, Split Body, Split Face, Combine, Intersect, Square, Skin, Rail, Profile,
  Align, Project, Extrude To object and Revolve about a picked edge); `tool_registry_tests`
  covers every CAD tool's declaration and the CAD network's and Edit CAD's menus; the CAD test
  files pass with only their wiring calls renamed (`tool_run.run`, `tool_picks.accept`, the
  prompts' labels, which are now "Pick " and the pick's label: "Pick sections", "Pick axis").
- Disabled tools draw pale (luce-ui's `Theme.disabled`): marking menu entries, the tool column,
  the level switchers; the icon shelf's buttons keep their tooltips.
- Follow-up round (2026-10-13):
  - Move node parity: a tool's node inserted from the viewport (and a prompt's pick) wrote the
    Group Type into slot 15, which a CAD node uses for its own rows (Move/Copy's Create copy),
    so a Move node of faces made a copy; the Group Type is now written only to nodes that have
    that row (`node_catalog.takes_group_type`).
  - A node keeps asking for more of its first pick while its tool still waits for it (Square's
    other boundaries, Skin's next section), as a step does (`tool_picks.node_next`).
  - Extrude and Revolve run with a flat face selected take that face as the profile, as Fusion
    does (`cad_commands.face_feature`, Edit CAD's sketch on the face and the feature); a
    Revolve's Profiles text can name a face as Extrude's can, and then waits for its axis.
  - A CAD node made from a menu keeps its viewport handles and takes the drag driver as a step
    does: a drag anywhere sets its drag row, in the tool's undo step (`tool_run.as_node`,
    `tool_drag_tests`' Offset Face node). Preview scenes `drag_cad_node` and `revolve_face`.
- Not yet: the CAD declarations live in luced-3d (question 2: luce-cad later).

**Stage 2: selection.** **Done 2026-10-13** (see "Stage 2 as built" below).
- In luce-geocore:
  - a `Selection` active element;
  - loop and ring walkers checked against Blender's rules (§5.2);
  - face and point loops;
  - partial loop between two edges;
  - shortest path (Dijkstra with a turn penalty, topology mode, fill region);
  - Connected with delimits;
  - Similar (by the criteria in §5.2, threshold and compare);
  - sharp edges, linked flat, sides, non-manifold, loose, interior, checker, random, mirror,
    region↔loop, boundary loop.

  Each is also a group function where it is a rule (`sharp(30)`, `sides(=4)`,
  `nonmanifold()`, `path(p3, p40)`).
- In luced-3d:
  - the double-click gestures (§5.2);
  - Shift+Ctrl/Cmd+click path;
  - the D menu;
  - selection sets as named groups in Edit Mesh (save, recall, add, remove);
  - Hide/Unhide.
- Tests:
  - a 4×4 grid torus: double-click an edge selects its loop of 16 edges;
  - again on the same edge gives the ring;
  - Shift+double-click a second edge on the same loop selects only the edges between;
  - at a pole the loop stops (a sphere's pole);
  - on a boundary it runs the boundary;
  - double-click a face selects its island and not a second cube's;
  - path from corner to corner of a 5×5 grid has 8 edges (topology) and is straight with the
    turn penalty;
  - Similar by area on a mixed mesh selects only the equal faces;
  - non-manifold finds a T-junction edge;
  - a saved set recalls after undo and survives a save and load;
  - every Select tool is also reachable as its group function in a node's Group.

**Stage 2 as built.**
- luce-geocore: a `selecting/` module below the group language and the verbs. Each select tool is
  a `SelectRule` (name, label, group function, family, icon, levels, picks, `ParmSpec` rows,
  `whole`, kernel) in a file of its family (`loops`, `regions`, `paths`, `similar`, `traits`,
  `patterns`, `mirror`, `convert`) and one line in `registry.lucb`'s `rule_makers` (plus ORDER for
  a new file). `Verbs` lists the rules after `makers` as the Select verbs (`Verb.rule`;
  `run_verb` runs the rule), and the group parser takes every rule's function name with numeric
  arguments after the group (`sharp(*, 30)`, `path(0 24, 1)`), so one declaration is a node, a
  D/right-click/Modify entry, a docs/TOOLS.md section and a group function. `ParmSpec`, `PickSpec`
  and `filled_parms` moved to `core/verb_specs.lucb`; the conversion kernels and the mirror map
  moved into `selecting/`. `Selection` gained the active element (`active`, `with_active`, set by
  `changed`), `joined` and `ruled` (a rule on a selection, as the gestures run them); `walked` is
  gone.
- Rules (22): Loop (Blender's walker rules: four- or two-edge points crossed past half their
  faces over manifold edges; poles end it; on a boundary along the fan, stopping at outer
  corners and at n-gon sides; the n-gon hub; face loops through quads; point loops; Only between
  for a run), Ring, Boundary Loop (whole boundaries, or faces' outline), Loop to Region (smaller
  or bigger side), Grow and Shrink Selection (Face step), Border, Connected (seam, sharp,
  material, UV, normal-angle delimits), Linked Flat, Shortest Path (Dijkstra on positions with a
  1% turn cost, Topology mode, Face step, Fill region by two breadth-first searches), Similar
  (15 measures, Equal/Greater/Less, sorted references and a direction hash), Sharp Edges, By
  Sides, By Area, By Normal, Non-manifold (boundary, three faces or more, flipped neighbors,
  pinched points), Loose, Interior Faces, Checker, Random, Mirror Selection, Convert.
- Not rules: select all, none and invert stay selection commands (their group syntax is `*`,
  an empty group and `!x`); Convert has no group function (`convert()` is the language's).
- Labels avoid other surfaces' names: Grow/Shrink/Mirror Selection (CAD's Shrink, the Mirror
  node).
- luced-3d: the gestures of §9 in `selection_gestures.luc` (the double-click takes its first
  click back with one undo, so the gesture is one step); hover previews the loop or ring in
  amber (luce-3d `EditOverlay.set_preview`); `select_with` runs the rule on the selection
  (`Selection.ruled`, no mesh rebuilt) and switches level when the rule's output is of another
  type; the last Select tool's rows stay on the tool bar (`SelectRun`) and a change runs it again
  on the same seed. Selection sets are named groups written by an Edit Mesh `Selection Set` step
  (or a Selection Group node on a plain node), named set1, set2, … with Select/Add/Remove/
  Intersect/Add selection/Remove selection per set. Hide, Hide unselected and Unhide keep the
  hidden faces in the workspace (in undo snapshots); luce-3d's renderer collapses their
  triangles and edges in the draw and pick passes, the overlay drops their points' markers, and
  `Workspace.kept` keeps hidden components out of every selection change and, with the Edit
  Mesh's Symmetry, mirrors picks and removals.
- Marking menus show labels for every entry, in columns by family under its name; D follows the
  level (Loops first at Edges, Region first elsewhere), then Selection, Sets and Hide. The
  right-click menu has Select with nothing selected too; Modify › Selection has a submenu per
  family, the sets and Hide.
- Tests: luce-geocore `select_rule_checks` (loops on a grid, cylinder hub, torus and sphere
  poles; boundaries and cycling; partial loops; face and point loops; rings; Loop to Region;
  islands with each delimit; paths and fill; Similar on a box beside a grid; grow and shrink;
  traits; a T-junction, a flipped face, a pinch, a lone point, a walled box; mirror, convert,
  random; group functions and Select verbs); luced-3d `select_gesture_tests` (real viewport
  events: double-click timing, modifiers, undo), `selection_set_tests` (sets through a project
  file, hide, the bar, symmetry, a Bevel node on `sharp(*, 30)`), `marking_label_tests`, and the
  registry and parity tests over every new tool.
- Not yet: renaming or deleting a set (a set is a group: a Group node or Attribute Delete removes
  it), a face loop's partial run, Side of Active, lasso and paint selection, soft selection by
  surface distance.

**Stage 3: drag and the interactive core.** **Done 2026-10-13** (see "Stage 3 as built" below).
- The generic drag driver (haul, wheel for counts, Shift snaps).
- Extrude: twist, taper, manifold mode, individual as a row.
- Inset: outset, even, relative, edge rail, boundary.
- Loop Cut with the `hover` gesture (ring preview, wheel for cuts) and the slide stage.
- Edge Slide and Vertex Slide as the `slide` gesture.
- Offset Edge Loops.
- Tests:
  - a drag of 100 points after Bevel changes Offset by the screen-to-world amount, one undo
    step;
  - the wheel after Loop Cut gives 3 cuts;
  - Loop Cut hovering a cube's side previews its ring, and a click cuts it;
  - Extrude Manifold pushed into a box cuts a pocket with no inner walls (face count checked);
  - Inset Even keeps width at a 30° corner.

**Stage 3 as built.**
- The drag driver (owner answer 7). luce-geocore's `Verb` gained `drag_mode`, `follows`, `wheel`,
  `axis`, `axis_choice` and `rails`, and `ParmSpec` gained `more`; `Verbs.frame` measures, on the
  input a tool ran on, its group's center and average normal and, for a slide, its rails
  (`verbs/drag.lucb`: each moving element's origin, where value 1 puts it, and its side).
  luced-3d's `tool_drag.luc` (events, typing, the box), `tool_drag_measure.luc` (pointer to
  value) and `drag_session.luc` (the session on the workspace) are the whole driver; no tool is
  named in them. After any tool with a drag row runs (S, the right-click menu, Modify, Repeat,
  a node or a step), a drag anywhere in the viewport sets that row and a click keeps it. A tool
  that `follows` (Extrude as Blender's E, Edge Slide, Vertex Slide, Offset Edge Loops, Loop
  Cut's slide) takes the value from the pointer with no button until the click. The modes:
  `length` hauls away from the group's center on screen, a point worth what it covers there
  (Bevel, Inset, Fuse, Noise, Snap); `normal` runs along the average normal as an arrow handle
  does, exact under the pointer in any perspective (Extrude, Duplicate, Peak); `amount` takes
  the row's range over 300 points (Smooth, Crease, Connect); `angle` turns about the center
  (Spin); `slide` runs along the rails of the element nearest the pointer, where the rail
  passes nearest the pointer's ray. While the value moves: the value box by the pointer shows
  it and takes typing (units and arithmetic, as the CAD boxes; Enter keeps), the wheel steps
  the count row (Bevel's Segments, Extrude's Divisions, Loop Cut's Cuts, Smooth's Iterations,
  Spin's Steps), X, Y and Z lock Extrude to a world axis (Direction set to Vector, the guide
  line in the axis color; the same key unlocks), Escape or a right click puts back the numbers
  the tool ran with. Values snap as the CAD handles do, unless Cmd/Ctrl is held: a tenth of
  the grid's step for distances, whole degrees, twentieths of a rail, hundredths of a range.
  Every drag folds into the tool's own undo step (`History.merge_last`). Another tool, a chosen
  tool or a marking menu keeps the value first (`tool_drag.settle`); an undo ends the drag.
- Extrude: Direction (Region normal, Blender's region extrude and now the default; Point
  normals, the old behavior; Vector), Vector, Twist and Taper about each region's center with
  the wall rows following, and Manifold (a wall that would lie in the plane of the face beside
  it merges into that face, and boundary points left on a straight side go: a box's top pushed
  in gives a shorter box of 6 faces). Edges move along the Vector too; points grow spikes
  (Maya's vertex extrude: a ring Inset along each edge, a quarter of it at 0, and a tip). The
  kernel is four files: `extrude.lucb` (settings, regions, edges), `extrude_fronts.lucb`,
  `extrude_walls.lucb` (Manifold) and `extrude_spikes.lucb`.
- Inset: Outset (the faces around inset away from the group, which keeps its size and stays
  selected), Even (the old miter; off, the bisector), Relative, Edge rail (a two-face sector's
  point slides along their shared edge) and Boundary (off, the rim slides along the mesh's open
  edges and no wall rises there).
- Loop Cut: the `hover` gesture (`hover_gesture.luc`, any tool with that gesture): chosen from
  any component level it switches to Edges, the edge under the pointer shows in amber the loops
  the verb would make (the verb run on that edge, its output selection drawn), the wheel sets
  the cuts, a click cuts and the cut slides with the pointer until a click; with edges selected it cuts their rings. Rings run through
  quads only, as Blender's (`BMW_DELIMIT_EDGE_RING_NGONS`); a triangle on a ring edge now fans
  from its far corner to the new points (a UV sphere's pole caps), an n-gon takes them into
  its boundary. Even slides every cut the same distance (the mean spacing's share), Flip keeps
  it as far short of the next loop.
- Edge Slide (Even, Flip, Clamp; Amount 0 at the start, past -1..1 without Clamp) and the new
  Vertex Slide (Direction picks each point's edge; a drag's first move picks it from the
  edges' screen directions; X/Y/Z lock it), both the `slide` drag. Offset Edge Loops: two loops
  either side of the group's loops and runs (Cap ends takes them round open ends), the faces
  beside cut into strips; its Amount slides along the edges the new points sit on.
- More options: a verb's `more` rows sit under a "More options" folder, shut at first, on the
  tool bar and in the node's pane (Extrude's Clamp, Vector, Twist, Taper and Manifold; Inset's
  Clamp, Relative, Edge rail and Boundary; Loop Cut's Whole ring). Extrude's ten rows had
  covered the viewport.
- Not in Stage 3 (as §8 places them): Poly Pen (Stage 6), Bevel's drag beyond Offset (Stage 4),
  a drag on the hovered ring's own handle, Extrude Manifold for individual faces, twist and
  taper on edges and points.
- Tests: luce-geocore `extrude_inset_checks` (volumes of an extruded, tapered and slanted
  box top; twisted fronts' corners; the region normal of a box's top and front; Manifold in
  and out with face counts and volumes; spikes; inset areas; Even at a 30° corner within
  1e-6, Outset, Relative, Edge rail on a sheared strip, Boundary off) and `cut_slide_checks`
  (Loop Cut counts on a grid, a cylinder round and across, a torus and a sphere's fanned
  poles; slide positions; Even and Flip on rings of edges 1, 2 and 3 long; Edge Slide on its
  rails, Even exact, Flip, unclamped; Vertex Slide; Offset Edge Loops open, capped and on a
  torus; drag frames and rails), both under the allocation-failure sweep; luced-3d
  `tool_drag_tests` (real viewport events: Bevel's 100-point drag equals 100 times the point's
  world size at the edge, one undo step, snapped without Cmd, Escape, a click keeps, as a node;
  Extrude following its normal, the wheel, typed 1.25 and Enter, the Y lock, Escape; Loop Cut's
  hover preview, three cuts by the wheel, the click and the slide; Edge Slide; Vertex Slide's
  picked edge), and `tool_parity_tests` over every tool (a hover tool runs on the selection).

**Stage 4: Bevel in full.** **Done 2026-10-13** (see "Stage 4 as built" below).
- Offset types; vertex bevel; profile superellipse and custom ramp; miters outer
  sharp/patch/arc and inner sharp/arc; corner patches as grids (`ADJ`-style refinement) and
  cutoff; loop slide; harden normals; mark sharp.
- Tests:
  - a cube's 12 edges at 3 segments give the rounded cube with grid corners, all quads but the
    corner triangles where segments are odd;
  - vertex bevel of a cube corner adds one triangle;
  - outer arc miter on a 270° corner keeps the strip width;
  - a custom profile of a step makes a stepped strip.

**Stage 4 as built.**
- luce-geocore: PolyBevel rewritten after Blender's bmesh bevel, read for its algorithm and
  written our own way (nothing copied; the files' notes describe it). A run: which edges or
  points bevel (`bevel_setup`: the group, Limit Angle or Weight, `bevel_weight`; an edge of
  three or more faces, or a bevel vertex whose faces are not one fan, refuses with a message;
  boundary edges are left), each bevel vertex's halves counterclockwise from outside with
  their widths by Width Type (Offset, Width = offset·2 sin(a/2), Depth = offset·cos(a/2),
  Percent and Absolute along the legs); Clamp overlap (`bevel_widths`: the widest bevel before
  a strip collapses or a side runs off its edge, all widths scaled to just short of it); the
  rings of boundary points (`bevel_boundary`, `bevel_meet`: offset lines meeting in a face or
  dropped onto one between, Loop slide onto the one unbeveled edge between, terminal edges,
  cut-off points, outer Patch and Arc miters, inner Arc miters spread along their edges); the
  even-widths pass along loop-slid chains (least squares by CGLS); the profiles
  (`bevel_profile`: the unit-square superellipse, Shape s → r = −2 ln 2 / ln s, points by equal
  chords — exact angles for the circle, legs for the square shapes, bisection otherwise; the
  Custom profile a ramp of depth from the chamfer to the square corner, its points on the
  ramp's points first so a step stays a step; the custom profile's side kept along chains); the
  vertex meshes (`bevel_grid`, `bevel_corners`, `bevel_patches`: Grid Fill refined by
  Catmull-Clark with Sabin's center rule and resampled, its starting center placed so the
  refined center lands on the profile's fullness (the refinement is affine, so two refinements
  fix it — no table); the cube corner as an octant of the superellipsoid; pipes snapped to
  the pipe's profile; the square shape's offset-line grid; the hollow corner; Cutoff's faces;
  polygons and fans; two strips welded); the output (`bevel_emit`: rebuilt faces, strips and
  patches, corner values by mean value coordinates in the face each lies in, shared per point
  and face; coincident patch points welded so square and hollow shapes keep no zero-area
  faces); the finishing passes (`bevel_marks`: every edge value of a beveled edge onto its
  strip's sides and of an unbeveled edge onto its remaining piece; Mark seams and sharp along
  the patch boundary to the next marked edge; Harden normals' corner N by Blender's rules;
  face_strength 1/2/3 by Face strength's mode; Material). Rings and vertex meshes are built in
  parallel (each ring's size is known first). `bevel_weights.lucb` is the new **Bevel Weight**
  verb. Thirteen files, none over 520 lines.
- The verb's records: `ParmKind.ramp` (a ramp in a parameter's components, its default in
  `ParmSpec.initials`), `KeySpec` and `Verb.keys` (Blender's modal keys as data:
  `Verbs.key_*`), `Verbs.parm_initial_at`.
- Choices that differ from Blender: Shape follows Blender's mapping (0.25 is the chamfer, 0
  hollows to the opposite corner; 0.5 round, 1 square); Clamp stops 0.01% short of the
  collision so squeezed faces keep an area (our verbs refuse zero-area faces); Affect has an
  Auto choice (points picked cut points off); Material is the mesh's n-th material in order of
  first use (our materials are paths, not slots); the Grid Fill center is solved, not looked up.
- luced-3d: a verb's rows skip the Group Type's slot 15 when it has more numbers (Bevel has
  46; `verb_numbers` takes the slot out again); a ramp parameter is a value ramp row
  (`parameter_rows.ramp_values`) on the node's pane and the tool bar, set as one change
  (`set_parameters`, `set_last_step_values`); `Tool.keys` (`ToolKey`) from the verb's keys, and
  the drag driver acts on them during a live drag before anything is typed: A, P and S switch
  what the pointer sets (Width by length, Shape and Segments by amount; a whole-number row
  drags in whole steps), M, V, O, I, Z and N cycle the menus, C, H, U, K and L flip the
  toggles, the wheel steps Segments, typing sets the row the pointer sets. docs/TOOLS.md lists
  the keys.
- Tests: luce-geocore `bevel_checks` (closed forms, under the allocation-failure sweep): a cube
  edge at 1–16 segments against the polygon's volume and area and their round limit; Shapes 1,
  0.25, 0 and the square's odd corner chord; the five width types; the three-edge corner at 2–5
  segments (Blender's patch counts, every patch point on the sphere of radius w about the inner
  corner) and every edge at 3 segments (all quads but 8 triangles); vertex bevel (8 − w³/6, one
  triangle); bevel_weight and the Bevel Weight verb; Limit Angle; Clamp overlap (the octahedron
  of face centers, 4/3, every face outward; unclamped, faces turn inside out); a stepped custom
  profile (8 − 2·w²/4); Cutoff; the L block's sharp and arc miters (strips ending square at x
  and z = 1 + w with their round end profile, the arc's middle on its circle of radius 2w);
  Loop slide on a sheared grid; a flat pipe; Harden normals, Mark sharp continuity, Face
  strength, Material; a boundary edge and a non-manifold edge refused; a sweep of every option
  over a cube, the L block, a cylinder (n-gon caps), a sphere (pole fans) and a torus, all
  closed and outward; `modeling_checks` and `select_checks` updated. luced-3d
  `bevel_tool_tests` (the rows and slots, a node's custom profile, the tool bar's ramp, and P,
  S, the wheel, M, C, A and typed 0.25 from real viewport events, one undo step), the drag and
  parity tests over every tool (Bevel Weight included).
- Preview scenes (`tools/preview_bevel.luc`, shaded wireframe): every edge of a box at 3
  segments, one corner's grid at 4, top corners cut off, the L block's arc miter, a stepped
  Custom profile with More options open on its ramp, and a drag after P (the box by the pointer
  reading Shape).
- Benchmarks (837 × 837 grid, `tests/bench`): 1k faces' inner edges 31 ms, 100k faces' at 3
  segments 210 ms (2.2M faces out: grid corners), every edge 455 ms. As first built (serial
  output) it took 98 ms, 1.04 s and 1.98 s; the old bevel 63 ms, 454 ms and 1.10 s with one
  patch face per corner and two-corner blends. The speed round: face normals, choosing edges
  (whole bit words per range), the bevel vertices (each one's room of halves known from its
  point's edges, built in parallel; a refusal is reported for the first vertex in order),
  ring sizes and rooms, Clamp overlap, the even-widths pass's re-placing, the grid points'
  numbering and the output all in parallel. The output is built in pieces (4096 input faces,
  8192 edges or 2048 vertices each), every piece into its own `FaceBatch`
  (luce-geocore `verbs/face_batch.lucb`) with its own corner-mix cache, joined in order by
  `append_batches`, so the mesh is the same on any number of threads; edge-value pairs, face
  kinds and corner flags are only collected when a finishing pass reads them (the output's
  edge topology was built on every run before). Every `bevel_checks` result was compared
  byte for byte (all 937 bevels saved as .prism) against the serial build.
- Not yet: Blender's per-corner UV seam snapping (corners interpolate in one face each, which
  keeps UVs continuous unless a seam runs through a corner patch); vertex groups (weights come
  from `bevel_weight`); a square cut-off point at odd segments, and Cutoff with Percent widths
  round the L's inner corner, can fold faces flat and then pass the input through with a
  warning.

**Stage 5: everyday modify tools.** **Done 2026-10-13** (see "Stage 5 as built" below).
- Knife with segments, snapping to points and edge middles, angle snap, cut through.
- Grid Fill; Bridge's cuts, interpolation and merge; Solidify; Rip and Rip Fill; Edge Split;
  Delete Edge Loop; Collapse; Target Weld; Poke; Rotate Edge; Symmetrize; Snap to Symmetry;
  Extract to a new piece.
- Tests per tool on fixtures:
  - Grid Fill of a 16-edge circle hole gives 4×4 quads;
  - Solidify of a grid gives a closed shell of twice the faces plus the rim;
  - Rip of an edge in a grid leaves two boundary edges;
  - Delete Edge Loop on a cylinder's middle loop leaves one row fewer;
  - Symmetrize of a lopsided sphere matches its mirror within 1e-6.

**Stage 5 as built.**
- Every tool is one luce-geocore verb (its file under `src/verbs/`) and one line in `makers`
  (and ORDER); luced-3d took no per-tool wiring. Blender's source was read for the algorithms
  and written our own way. New verbs: **Knife** (`knife`, `knife_faces`), **Grid Fill**,
  **Solidify**, **Poke**, **Rotate Edge**, **Edge Split** and **Rip** (`rip`), **Separate**,
  **Delete Edge Loop** and **Limited Dissolve** (`dissolve`, with Dissolve moved out of
  `fill_dissolve`), **Collapse** and **Target Weld** (`cleanup`), **Screw** (`spin`),
  **Symmetrize** and **Snap to Symmetry**, **Relax** (`smoothing`, with Smooth),
  **Tris to Quads** (`quadrangulate`), **Decimate** (`PolyReduce`: `decimate`,
  `unsubdivide`) and Triangulate's methods (`triangulate`). Clip's tool is now **Bisect**
  (its stroke, `bisect_stroke.luc`); the Knife is the new verb.
- Options, after Blender, Houdini and Modo:
  - Knife: points on the surface (snapping to points, Ctrl to edge middles, Shift none), C holds
    each segment to 15° on screen, Z cuts through (else only faces facing the view that nothing
    hides, by a ray back from each cut's middle), Backspace, the first point again closes, Enter
    cuts. A path ending inside a face is trimmed back to its last edge (Blender leaves a dangling
    edge; our faces have none). Faces split along every path across them, through the stroke's
    corners inside them; crossing paths in one face are left out with a warning.
  - Bridge: Cuts, Twist, Interpolation (Linear, Blend path, Blend surface), Smoothness, Profile
    with six shapes, Merge and Merge factor; faces as the first pick bridge their outlines and
    go; a second pick (`PickSpec` 2, `Verbs.run(..., second)`) pairs its loops with the first's.
  - Grid Fill: Span (0 finds it from the corners), Offset, Simple; Coons-patch inner points.
  - Solidify: Thickness, Offset, Even thickness, Fill rim, Flip.
  - Poke: Offset, Relative, Center (weighted mean, mean, bounds).
  - Rip: Offset, Fill (Rip Fill), Flip, Turn (a point's split); chain ends inside the surface
    cut one edge on, by Blender's rule, so a ripped interior edge opens a hole of six boundary
    edges (its two copies among them), not the two the plan guessed.
  - Merge Points gains At point; Collapse; Target Weld; Separate (Selection, Loose parts; paths
    suffixed .001…); Dissolve's Clean points; Delete Edge Loop; Limited Dissolve (Angle,
    Boundaries, delimits); Decimate (Collapse by quadrics with Lock boundary, Un-subdivide,
    Planar); Tris to Quads (Face and Shape angles, delimits); Triangulate (five quad methods,
    two n-gon methods); Subdivide's Smoothness; Smooth's Keep volume, Keep boundary and Axes;
    Relax; Spin's Flip; Screw (Turns, Steps, Rise); Symmetrize (six directions, Threshold);
    Snap to Symmetry (Direction, Threshold, Factor, Center).
- Two picks: `Verb.wants` says whether the first pick alone wants the second (Bridge with fewer
  than two loops, Target Weld always; `Verbs.wants_second`). A mesh tool's later pick is a
  `Pick` of kind components kept in a node's text 1 (its own row) and a step's text 0; after the
  tool runs, `tool_picks.luc` (now for mesh tools too) asks for it ("Pick second loop"), the
  selection fills it, Enter keeps it.
- Gestures: `knife` (`knife_placing.luc` on the placing prompt, `place_prompt.luc` now carries
  the gesture, the rays clicked along and the toggles; a stroke outside an Edit node makes a
  node); Bridge's second loop through the pick chain; Spin's angle drag is the drag driver's
  `angle` mode.
- Parallel kernels with ordered output: `batched_faces` (face_batch.lucb) runs a verb's faces in
  ranges, each into its own `FaceBatch`, joined in order; `TopologyBuilder.extend_points` and
  `place_point` let threads place points. Poke, Solidify and Triangulate build their faces this
  way; Solidify's points, Snap to Symmetry's pairing, Smooth and Relax's rounds and Tris to
  Quads' pricing run in parallel. Decimate keeps each point's live triangles as a slice
  rewritten on each merge, numbers only the group's points, and breaks ties by edge length (a
  flat grid priced every collapse 0 and piled them on one point: 1.8 s to 80 ms for 100k
  triangles).
- Benchmarks (837 × 837 grid, `tests/bench`; luce-geocore docs/API.md has every row): Poke of 100k faces 54 ms; Solidify of every
  face with Even thickness 70 ms (1.4M faces out); Symmetrize of everything 103 ms; Snap to
  Symmetry of every point 44 ms; Knife cutting through a row of 837 faces 55 ms; Grid Fill of a
  22-edge hole 17 ms; Bridge of two 837-edge loops with 3 cuts, Blend path and Profile 19 ms;
  Edge Split of a 1k-face block's inner edges 58 ms; Separate of 100k faces as loose parts
  26 ms; Limited Dissolve of the whole grid into one face 150 ms; Collapse of 100k faces' edges
  24 ms; Triangulate (Beauty) of everything 71 ms; Tris to Quads of the grid in triangles
  137 ms (518 ms before its pricing ran in parallel); Decimate of 100k triangles to half 88 ms
  (1.86 s before the tie-break and the compact lists), Un-subdivide of 836 × 836 quads 76 ms;
  Subdivide with Smoothness 725 ms (2.8M faces; 599 ms without, 555 before it worked on selections).
- Tests: luce-geocore `face_tool_checks`, `symmetry_checks`, `fill_checks`, `split_checks`,
  `dissolve_tool_checks`, `merge_checks`, `sweep_checks`, `knife_checks`, `reduce_checks`,
  `shape_checks`, all under the allocation-failure sweep (Grid Fill's 4×4 on a 16-gon hole and
  the prism's volume; Solidify's 2F + rim, closed, volume area × thickness, Even on a cube;
  Delete Edge Loop giving the cylinder back; Symmetrize within 1e-6; Spin and Screw counts and
  places; Bridge counts, profile radius 1.5, merge; Decimate halving a sphere and keeping a
  grid's square; Tris to Quads giving the grid back; …). luced-3d `modify_tool_tests` (real
  viewport events: the Knife's stroke, snaps, angle, through, Backspace, closing, Escape, as a
  node; Bridge's and Target Weld's second picks as steps and nodes; Spin's angle drag; every new
  drag row), and `tool_parity_tests` over every tool (the Knife drawn, second picks accepted).
- Preview scenes `tools/preview_modify.luc` (modify_knife, modify_knife_cut, modify_bridge,
  modify_bridge_pick, modify_grid_fill, modify_solidify, modify_poke, modify_rip,
  modify_symmetrize, modify_screw, modify_decimate).
- Fixes after review (screenshots of the first round):
  - Bridge's Blend path had handles twice Blender's length (the whole gap, not half of it, times
    the factor), bunching the cut rows toward the middle, and a straight run's plane normal was
    rounding noise above an absolute threshold, so two straight runs of a flat grid could arch out
    of the plane (the "ridge" between the two grids). Handles now follow Blender's
    `bezier_handle_calc_length_v3` (half the gap across the normals' plane), a nearly straight
    run counts as straight against its size and takes Blender's aligned normal (square to the
    run, toward the other), loop centers are weighed by edge length, and each loop's shape is
    carried along the curve with the turn that keeps it from twisting (Blender's
    `bm_edgering_pair_interpolate`). Linear's Profile swells about the straight line. Profile
    on open runs still widens them along the run (the earlier "wings"): Blender does the same.
    Checks: two parallel square loops bridge into a straight tube, rows at y = 2 B(t) (Blend
    path) or evenly (Linear), swelled by the profile; straight runs of a turned grid bridge
    flat with the middle row halfway.
  - Solidify's kernel was right for reasonable input; the crumpled preview came from the scene
    (white Noise near the cell size folds the grid's own quads, and Even thickness then
    multiplies the move up to ten times at the folds; the grid also lay in the floor plane, whose
    lines showed through). The scene is now a roughened bowl. Solidify gains Blender's
    modifier Clamp and Angle clamp (off by default, as in Blender). Checks: the preview's noisy
    grid and a smoothly raised grid give closed shells, every inner point within 1.2× (1.6×)
    the thickness and no inner face turned; Clamp and Angle clamp limits by closed form.
  - Subdivide works on the selection as Blender's does: the group's faces (or an edge group's
    edges and the faces they close) split; other faces keep the mesh joined with Straight Cut
    (a split edge's point becomes a corner, two split edges are joined across, a quad with three
    is cut as `quad_3edge`); Catmull-Clark moves only points every face of which splits. The
    editor ran every `whole` tool on everything even with a selection; now only with nothing
    selected. Checks: `subdivide_select_checks` (one face, an L, a smoothed block, an edge group,
    two levels) and `modify_tool_tests`.
  - New preview scenes modify_bridge_runs (the two grid runs bridged flat) and modify_subdivide
    (an L of faces subdivided).
- Not yet: Knife's crossing paths in one face and holes inside a face; Decimate's symmetry and
  weights; Bridge's loop pairs mode; Grid Fill between two open runs; Extrude to cursor, Matrix
  extrude, Offset Edge Loops' slide (as before).

**Stage 6: primitives in full, and Poly Pen.** **Done 2026-10-13** (see "Stage 6 as built"
below).
- Box divisions; ico and quad spheres; caps and rows; Disc; Tube; Capsule; platonic solids;
  interactive placement on surfaces.
- Poly Pen: extrude an edge by dragging, split, delete under the pointer.
- Retopology on a reference mesh.
- Tests: counts per primitive option; Poly Pen dragging a boundary edge adds one quad; a
  retopology quad's points lie on the reference within tolerance.

**Stage 6 as built.**
- Primitives are luce-geocore verbs like every tool (one `verbs/create_*.lucb` declaration each
  and a `makers` line; their kernels in a new `primitives/` module, built in place on the pool:
  `arrays`, `placement`, `boxes`, `lathe`, `round`, `torus`, `polyhedra`). The hand-written
  Cube, Grid, Sphere, Cylinder, Cone and Torus nodes and Edit Mesh's `Create …` steps are gone:
  the verbs are the nodes (`Verb.inputs` 0: no input, no group), the Edit Mesh steps and the
  registry's Create › Primitives tools.
  - **Box**: size and divisions per axis; Bevel and Bevel segments round every outer edge with
    PolyBevel (its grid corners); one division each way is `Mesh.cube` point for point.
  - **Grid** (width, depth, columns, rows) and **Plane**.
  - **Sphere** (UV: columns, rows), **Icosphere** (0–9 subdivisions, Blender's counts),
    **Quad Sphere** (a box lattice mapped onto the sphere, no poles), **Capsule** (cap rows,
    body rows; a sphere at twice its radius).
  - **Cylinder** and **Cone** (top radius 0: an apex; else a frustum), rows, caps None, N-gon,
    Fan or Grid (the Coons patch of the circle's four quarters, sides in fours) in Cap rings
    bands; **Pipe** (Houdini's thick tube: "Tube" is CAD's sweep) and **Disc**.
  - **Torus** (major and minor segments, Twist by whole points), **Platonic Solid** (the five,
    the dodecahedron as the icosahedron's dual, resting on a face), **Helix** (a spring).
  - Every primitive stands on its base at Position along Up, turned by Turn; Name piece (on in
    Edit Mesh's steps, off for a node) names its faces' path /box1, /box2, …. Text was not in
    the plan and is not built.
- Interactive creation: the `create` gesture (`create_gesture.luc`), Modo's and Maya's. A
  primitive chosen (A, Create, the shelf) waits for a press on the ground or a surface (the
  surface's normal is Up); a drag draws the base (corner to corner, or out from the center), the
  release keeps it, and a primitive with a rise takes it from the pointer (`height` along Up,
  exact under the pointer, or `radius` off the base's circle for a torus's tube) until a click.
  A click without a drag lets the base follow the pointer. The value box by the pointer shows
  the value and takes typing (units, arithmetic, "w, d"; Enter keeps it and goes on), the wheel
  steps the tool's count row, sizes snap to a tenth of the grid's step (Cmd/Ctrl frees them,
  Shift squares a rectangle), Escape or a right click takes it back. The primitive shows live
  and is one undo step: a step of the edited Edit Mesh (a piece selected at Object), else a node
  of its own, shown; the tool stays chosen; Enter before a press makes one at the origin. The
  verb's `PlaceSpec` names the rows; nothing in the gesture names a primitive.
- Poly Pen: the `pen` gesture (`pen_gesture.luc`) inside an Edit Mesh (one is added after the
  displayed node when none is edited), Blender's Poly Build and Maya's Quad Draw. Clicks place
  corners on the mesh's points, the snap target or any surface, else the grid; every four make a
  quad, three a triangle, N-gon closes on Enter or the first corner, Strip makes a quad of the
  first four and another of each next pair (M steps the modes: no shortcut takes M). Ctrl+click
  extends the boundary edge nearest the click into a quad reaching it, Ctrl+drag an edge drags
  its quad out and Ctrl+drag a corner point fills the corner (Blender's quad from an edge pair);
  a drag on a point moves it; Shift+click deletes the face (dissolves the point or edge) under
  the pointer; Ctrl+Shift+click splits the edge under it, there. Free faces face the viewer.
  Each action is one step: PolyDraw, the new **Poly Pen** verb (Extend, Fill corner, Split:
  positions after its parameters, so a node replays it), Delete, Dissolve or Transform
  Components; a refused action says why and adds nothing.
- Retopology: Snap Target… (Modify, the right-click menu in an Edit Mesh) waits for a click on an
  object, the rest of the scene included; placing (the create gesture, Poly Pen, PolyDraw) then
  lands on it alone (`Workspace.landing_at`), and the edited Edit Mesh gets it as its
  **Reference**, a second input (an Import of the object into this object's frame). Steps of a
  reference verb read it: **Shrinkwrap** (Nearest, Along normals, Along vector; Offset, Strength;
  points whose line misses stay, with a warning) and **Relax**, which then keeps its points on
  it. As nodes they take the reference as their second input (Shrinkwrap requires it). Clear
  Snap Target lets every surface count again.
- Not built: Text; a relax brush in Poly Pen; Poly Pen's edge-loop insertion; turning the base
  by the pointer while it is drawn (Turn is a row); a choice of drawing a base from its corner or
  its center.
- Tests: luce-geocore `primitive_checks` (closed forms: every count per option, every sphere's
  points on its sphere, Box (1, 1, 1) = Mesh.cube, divided and rounded boxes, caps of each kind
  and rings by the polygon volume, cone and frustum volumes, pipe walls, disc areas, tori on
  their tube with twist, closed capsules within their radius of the axis, Platonic counts and
  resting faces, the helix closed, placement by Position, Up and Turn, pieces) and
  `retopology_checks` (Shrinkwrap nearest, offset, strength, along a vector with misses, along
  normals; refused without a reference; Relax on a reference; Poly Pen's quad and triangle, an
  inner edge refused, a corner filled back, an edge split), both under the allocation-failure
  sweep; luced-3d `create_gesture_tests`, `poly_pen_tests` and `retopology_tests` from real
  viewport events, and `tool_parity_tests` (every primitive as a step on nothing, as a node and
  through its cook; Poly Pen's actions as nodes in `poly_pen_tests`; the Shrinkwrap node with
  its second input in `retopology_tests`).
- Benchmarks (luce-geocore docs/API.md): about a million faces of each primitive in 24–32 ms.
- Preview scenes `tools/preview_create.luc`: create_gallery, create_box, create_surface,
  pen_strip, retopo_sphere, retopo_shrinkwrap.

**Stage 7: shape, topology and normals tools.** **Done 2026-10-13** (see "Stage 7 as built"
below).
- Circularize, Straighten, Space Evenly, Relax, Make Planar.
- Quadrangulate (quality-scored joining), Limited Dissolve, Un-subdivide, PolyReduce (quadric
  collapse), Triangulate methods.
- Recalculate outside, hard/soft by angle, seams, bevel weights.
- Tests:
  - Circularize of a cube's top makes a circle (radius spread < 1e-6);
  - Quadrangulate of a triangulated grid gives the grid back;
  - PolyReduce to 50% halves the face count and keeps the boundary;
  - Recalculate fixes a sphere with flipped faces.

**Stage 7 as built.**
- Every tool is one luce-geocore verb and a line in `makers`, as in Stages 5 and 6; luced-3d
  took no per-tool wiring (one family name, UV, in `tool_registry.family_order`). Blender's
  LoopTools and bmesh operators, Maya's and Houdini's manuals were read for what the tools do;
  nothing was copied.
- Shape (`circularize.lucb`, `straighten.lucb`, `planar.lucb`):
  - **Circularize** (edges, faces, points): loops become circles round their edge-weighted
    centers in their Newell planes, open runs arcs of their Kåsa circle fits; faces give their
    regions' outlines and carry the inner points along their rays when the outline is
    star-shaped, or between two concentric circles for a ring of faces (a round rim round a
    round hole). Radius (0 fits), Even, Flatten, Twist, Influence (the drag row).
  - **Straighten** (edges, points): runs onto the line between their ends, Even or by length
    shares; Influence. **Space Evenly**: runs and loops to equal lengths along the polyline
    (Linear) or a centripetal Catmull-Rom spline (Smooth); Influence. Chains run in parallel.
  - **Make Planar** (faces): Blender's Make Planar Faces, Factor and Iterations (10), both
    passes of a round in parallel. Relax was built in Stage 5.
- Topology: Quadrangulate (Tris to Quads), Limited Dissolve, Un-subdivide and PolyReduce
  (Decimate) and the Triangulate methods were built in Stage 5; their Stage 7 tests (a
  triangulated grid joined back, a sphere halved, a grid's boundary kept) are Stage 5's
  `reduce_checks`.
- Normals (`recalculate.lucb`, `edge_marks.lucb`):
  - **Recalculate Normals** (faces, everything with none; Inside): islands wound one way by
    a breadth-first walk over corner links found in parallel, then turned to face out by
    their signed volume about their centers (summed in parallel pieces), a sheet too flat to
    tell keeping its majority's winding; faces that cannot agree are reported. It selects the
    faces it turned.
  - **Hard Edges**, **Soft Edges** (Mode Set/Clear) and **Smooth by Angle** (Angle 30°, Keep
    hard edges; edges, faces or everything) write the edge mark `sharp` (1 hard, -1 soft, 0
    by the cusp). The shading follows it: luce-geocore's smooth normals, given `sharp`,
    split each point's faces into fans at hard edges, join them across soft ones and across
    unmarked edges within 60° (`smooth_normals.lucb`: `EdgeMarks`, `fan_normal`), so the
    marks survive every later edit on the edges' provenance and a Move refreshes them
    around the moved points; a mesh whose `sharp` changes takes a fresh shading cache.
    Blender's rule holds: one hard edge at a point splits nothing there.
  - **Mark Seam** (Mode) and **Seams from Islands** (Mark hard) write `seam`; the latter reads
    corner UVs and refuses a mesh without them (the Edit Mesh says why, the mesh stays).
  - Bevel weights: **Bevel Weight** (Stage 4).
- The viewport draws the marks in an Edit node (luce-3d `EditOverlay`, `seam` and `sharp`
  colors): hard edges cyan, seams red, 2 points wide over the 1-point wireframe, writing no
  depth so the selection's orange draws over them; the selection and the marks stand 0.2% of
  the view distance toward the eye, so the surface no longer speckles them.
- Poly Pen: the floating panel is titled Poly Pen (the tool chosen) for the PolyDraw, Delete
  and Poly Pen steps it makes (`tool_bar.luc`), as its menus name it.
- Icons: Circularize `circle-center`, Straighten `constraint-collinear`, Space Evenly
  `resample-curve`, Make Planar `set-planar`, Recalculate Normals `reverse-normals`, Hard
  Edges `select-sharp`, Soft Edges `shaded-view`, Smooth by Angle `surface-normal`, Mark Seam
  `sketch-break`, Seams from Islands `uv-project`: stand-ins until luciaos-assets has
  circularize, straighten, space-evenly, make-planar, recalculate-normals, hard-edges,
  soft-edges, smooth-by-angle, mark-seam and seams-from-islands. The Stage 6 tools now draw
  their own icons (icosphere, quad-sphere, disc, platonic-solid, helix, poly-pen,
  shrinkwrap, snap-target).
- Tests: luce-geocore `shape_loop_checks` (a divided box's top outline on a circle within
  1e-6 at equal angles, inner points inside, Radius, Flatten off and Twist, Influence 0; arcs
  through a bent run and a straight run refused; Straighten even and by length, half
  Influence; Space Evenly on a squeezed row, a square outline and, Smooth, a circle's chords
  within 1%; Make Planar exact on one face, a noisy grid flattened) and
  `normals_tool_checks` (a sphere with 62 faces reversed turned back, closed and of its
  volume, Inside, a group alone, a sheet's majority; a box's corner shading by the cusp,
  all soft, one hard edge, two, cleared, Smooth by Angle 30 and 100, Keep hard edges, a
  sphere's equator hard before and after a Move; seams set and cleared, found from corner UV
  islands, refused without UVs), both under the allocation-failure sweep. luced-3d
  `shape_tool_tests` (real viewport events: Circularize from the right-click menu on four
  clicked faces and its Influence drag in one undo step; a double-clicked row straightened
  and spaced; Make Planar on a bent grid; Recalculate after Reverse; Hard, Soft and Seam
  marks drawn by the overlay and cleared from the bar; Smooth by Angle's drag; Seams from
  Islands' refusal; every Stage 7 tool's node equal to its step in every point, face normal
  and mark), `poly_pen_tests` (the panel's title), `tool_parity_tests` (a tool the grid
  cannot take must be refused alike by node and step).
- Benchmarks (luce-geocore docs/API.md: the 1024² grid and a 1448 × 724 sphere, about a
  million faces): Circularize of the whole grid (its outline a circle, 1M inner points mapped)
  90 ms, of a 512² block 35 ms, of every row as an arc 80 ms (113 ms before the chains were
  fitted in parallel); Straighten of every row 40 ms; Space Evenly 57 ms linear, 125 ms smooth
  (154 ms before each span's knots were found once); Make Planar of every face, 10 rounds,
  43 ms; Recalculate Normals of the half-reversed sphere 40–50 ms and of the grid 28 ms (148 ms
  and 117 ms before the links and the island sums went parallel); Hard Edges on 2.1M edges
  3 ms; Smooth by Angle of the sphere 18 ms; Seams from Islands 20 ms; the sphere's shading
  normals 27 ms by the cusp, 23 ms by its edge marks.
- Preview scenes `tools/preview_shape.luc`: shape_circularize, shape_hole, shape_straighten,
  shape_space, shape_planar, normals_recalculated, normals_hard, normals_angle,
  normals_seams.
- Not built: custom normals (Blender's set from faces, average, point to target, weighted
  normal) and a face-orientation display (the viewport lights both sides of a face alike, so
  a reversed face shows only when turned); Circularize's mapping of the inner points of a
  region whose outline is not star-shaped or that has more than two outlines (the outlines
  become circles, the inner points stay, with a warning); Straighten on loops.

**Stage 8: deformers, Mesh Check, sculpt-lite.** **Done 2026-10-14** (see "Stage 8 as built" below).
- Bend/Twist/Taper/Squash as one node; Lattice; Shrinkwrap.
- Mesh Check overlay sharing the Select passes.
- Sculpt-lite brushes as stroke steps.
- Tests:
  - Twist 90° of a box column turns the top 90°;
  - Mesh Check counts on a fixture with each defect;
  - one brush stroke is one undo step.

**Stage 8 as built** (paused 2026-10-13 for the held-mesh Edit Mesh, finished after it).
- Every tool is a luce-geocore verb and a line in `makers` (or a select rule), as in Stages 5–7.
  Blender's Simple Deform, Lattice and sculpt brushes and Houdini's Bend, Lattice and
  PolyDoctor were read for behavior; nothing was copied.
- **Bend** (`bend.lucb`, Modify › Deform): one node with a Mode (Bend, Twist, Taper, Squash),
  Amount (degrees, or percent for Taper and Squash), Axis, Direction (the way a bend curls),
  Origin (the group's start, its center, Custom), Length (0: the group's extent) and Limits
  (the span that deforms; points past it follow rigidly). Its drag turns Amount; M steps the
  mode and A the axis while it lasts.
- **Lattice** (`lattice.lucb`, Modify › Deform): a cage of Points along X, Y and Z round the
  group's bounds (Padding), Smooth (Bernstein, Sederberg–Parry) or Linear (trilinear). The
  moved cage points follow the parameters (count, then index and offset each), so a node
  and a step replay them. The run leaves its cage's box on the mesh (`.lattice_low`,
  `.lattice_size`, `.lattice_points`), so `Verbs.lattice` gives the cage over the result.
  luced-3d's `lattice_gesture.luc` draws it and drags its points (Shift adds), one undo
  step per drag, for the edited node's last step or a shown Lattice node.
- **Sculpt** (`sculpt.lucb`, `sculpt_brush.lucb`, Modify › Sculpt): Draw, Grab, Smooth,
  Inflate, Flatten, Pinch; Radius, Strength, Falloff (Smooth, Sphere, Linear, Constant,
  Sharp), Invert; the group alone moves; the Edit node's symmetry mirrors each dab. A stroke's
  dabs (center, direction and pressure each) follow the parameters. luce-geocore remembers the last
  stroke cooked, so a stroke sent again with more dabs runs only the new ones and makes its
  mesh over the last one (normals and GPU copies refreshed around what moved): 3 ms per
  pointer move on 1M faces. `sculpt_gesture.luc`: the brush circle (and its half-strength
  ring) on the surface, a drag strokes, Ctrl inverts, Shift smooths, [ and ] size it (it
  keeps its size on screen), Escape drops a stroke; one stroke, one undo step.
- **Mesh Check**: the select rules **Poles**, **Degenerate**, **Intersecting** and the
  **Mesh Check** rule (every finding turned on, at the selection's level) are Select › Find
  tools; luce-geocore's `MeshReport` (`Verbs.mesh_check`) runs the same passes for the
  overlay: non-manifold edges, pinched points, boundary edges, flipped neighbors, loose
  points, n-gons, triangles, poles, zero-area faces, zero-length edges, intersecting faces.
  `mesh_check_view.luc`: the shading menu's Mesh Check draws each finding in its color over
  the shown mesh (luce-3d `EditOverlay.add_finding`) and lists them at the lower left; a row's
  click selects that finding, one undo step.
- Edge marks draw 3.5 points wide and the selection's lines 2, so a selected hard edge or seam
  shows its mark's color at both sides (Stage 7's carry-over).
- Nodes of a verb taking numbers after its parameters keep them past the Group Type's slot
  (`edit_operations.node_numbers`, `insert_numbers`), so a Sculpt or Lattice node with many
  dabs or moved points replays them.
- Tests: luce-geocore `deform_checks`, `sculpt_checks`, `mesh_check_checks` under the
  allocation-failure sweep; luced-3d `deform_tool_tests` from real viewport events.
  Benchmarks: luce-geocore docs/API.md.
- **Sculpt in the real window** (`tools/preview.py --scene sculpt_drag --opt 3 --background`):
  a Draw stroke over a 1M-face grid in an Edit Mesh, 123 pointer moves: the move takes 4.8 ms
  on average (13.8 ms worst) and frames come every 16.6 ms (the display's 60 Hz). Getting
  there: a whole-mesh group ("*") on another domain is the cached group of that domain, not a
  conversion of the whole mesh on every move (luce-geocore `resolve_group`; 9.2 to 4.8 ms); a
  holding Edit node's steps no longer go to the worker with every request (its result goes
  by key; a long stroke's numbers also overran the 64-number cap on a step, now 1M).
- **Dense wires**: in Edit mode a mesh's wires are left out where they would cover its faces
  (more than one edge per two pixels of its footprint on screen; luce-3d
  `mesh_batch.too_dense`). A 1M-face grid in part of the view was drawn as solid wire grey,
  hiding a sculpted surface's shading; nearer, the wires come back.
- Mesh Check's panel stands above the snapping and tool shelf buttons.
- Captures (`tools/preview_deform.luc`): `deform_bend`, `deform_twist`, `deform_lattice` (the
  cage drawn over the result), `sculpt_draw` (a sphere, one Draw stroke mirrored by X
  symmetry, the brush hovering), `sculpt_drag` (the 1M grid), `mesh_check` (an open
  boundary, two triangles, poles, the panel), `hard_marks` (marked edges, two of them
  selected: the mark shows round the selection).
- **Soft Transform** (`point_verbs.lucb`, Modify › Deform; Houdini's Soft Transform):
  Transform Components with its falloff on (Soft radius 1 to start), a node and a tool of
  its own; the Edit node's soft radius stays for gizmo moves.
- **Corrective Smooth** (`corrective_smooth.lucb`, Modify › Deform; Blender's Corrective
  Smooth): the group smoothed (Factor, Iterations), then given back the detail the rest
  shape (its second input; an Edit Mesh's Reference) has over its own smoothing, measured
  in the frame of the smoothed rest surface (normal and first edge) and put back in the
  smoothed deformed one's (Scale). An undeformed shape comes back exactly; a rigid move or
  turn comes back as that move or turn.
- **Edge Transport** (`edge_transport.lucb`, Modify › Shape; Houdini's Edge Transport):
  each point's distance from the group along the edges (Distance: Dijkstra over edge
  lengths; Hops: breadth first), in the point attribute `dist`, -1 where unreached;
  Normalize gives 0..1. Relax (Stage 6) is the edge relax.
- **Pen pressure**: each sculpt dab carries the pen's pressure (a seventh number; 1 from a
  mouse), which scales its strength; Grab's dabs carry points by the move alone. luce-ui's
  `Application.dispatch` (the path tests and synthetic input take) drops the pen's fields,
  so the pressure test hands its events to the gesture as the viewport does; native events
  keep them.
- Benchmarks (1M faces, docs/API.md): Soft Transform of 1,000 points, radius 40: 23.6 ms;
  Corrective Smooth, 5 rounds: 73.4 ms; Edge Transport from one point: 117 ms (Distance),
  17 ms (Hops).
- Icons: stand-ins (Bend `stretch-curve`, Lattice `grid`, Mesh Check `surface-analysis`,
  Poles `vertex-select`, Degenerate `select-by-area`, Intersecting `boolean-intersect`, Soft
  Transform `transform-gizmo`, Corrective Smooth `smooth-tool`, Edge Transport
  `edge-select`).

## 9. Open questions for the owner

The owner's answers (2026-10-13), and how they were applied:

1. **Keep Edit Mesh.** No rename to Edit Geo.
2. **CAD tools are declared in Luce now** and move into luce-cad later, family by family.
3. **D is the marking menu only.** In the viewport D opens Select (a sketch keeps
   Constraints). The display flag lost its window-wide D shortcut. The Network panel takes D
   itself, so D on a focused network still flips the selected node's display flag; the
   viewport, the outliner and the parameters no longer do. The status line reads "A / S / D:
   create, modify, select   D in the network: display flag", and the README says the same.
4. **Ring is Cmd/Ctrl+double-click on an edge.** Cmd/Ctrl alone still removes, so the
   gestures are, for Stage 2:
   - Cmd/Ctrl+click removes one element (as now);
   - Cmd/Ctrl+double-click on an edge adds its ring (the double-click replaces its first
     click's removal, one undo step); on a face or point, where there is no ring, it removes
     the island;
   - Shift+Cmd/Ctrl+double-click removes the loop (on an edge) or the island;
   - Shift+Cmd/Ctrl+click is the shortest path (answer 6); a path needs one click, so the
     double-click forms do not clash with it.
5. **Double-click a face or point selects its island.**
6. **Shift+Cmd/Ctrl+click selects the shortest path.**
7. **Dragging right after a tool runs sets its main value; a click keeps it.** Every tool
   declares its `drag` row (docs/TOOLS.md lists it); Stage 3 built the driver (`tool_drag.luc`).
8. **Selection (Stage 2) comes before the interactive tools (Stage 3).**

The questions as asked:

1. **Rename Edit Mesh to Edit Geo?** The request calls it Edit Geo, the context is Geo, and
   "Mesh" will also hold curves and points later. Recommend: yes, Edit Geo, in Stage 0. Without
   backward compatibility it is a plain rename; projects saved with the old name stop loading.
2. **Where CAD tools are declared.** Luce files in luced-3d now (§3.1), or a luce-cad Base
   registry like luce-geocore's verbs from the start? Recommend: Luce now, and move a
   declaration into luce-cad when its op's glue moves to Base, family by family. Moving it first
   would hold up Stage 0.
3. **D for Select in Geo.** Hold D opens Select in Geo contexts, tap D stays the display flag.
   Recommend: yes. It follows A and S and needs no new key.
4. **Ring gesture.** Double-click the same edge again for its ring, as proposed, or Maya's Shift +
   double-click on a parallel edge? Recommend: double-click again. Shift + double-click is taken
   by "add a loop", which Houdini also uses.
5. **Double-click a face or point: island or loop?** Recommend: island (Modo, Cinema 4D), with
   face loops from Shift + double-click beside the last face, and from D › Loop.
6. **Path modifier.** Shift+Ctrl/Cmd+click for the shortest path (Ctrl/Cmd alone already removes)?
   Recommend: yes.
7. **Drag anywhere** sets a tool's main value right after it runs (Houdini's PolyBevel state,
   Cinema 4D). Recommend: yes, for every tool with a `drag` row. A click without moving keeps the
   value.
8. **Order.** Recommend: selection (Stage 2) before the interactive tools (Stage 3), because
   every modeling session starts with selecting.

## 10. Algorithms to study before building

Read in Blender's source for what they do, then written our own way in luce-geocore:

- **Bevel** (`bmesh/tools/bmesh_bevel.cc`).
  - Each corner point is placed where the offset lines meet in each face.
  - Profiles are superellipses whose points are spaced by equal chords.
  - An N-sided corner starts as a coarse patch and is refined by Catmull-Clark (with Sabin's
    correction), then resampled to the segment count.
  - Loop slide evens the offsets along chains.
  - Clamp computes the largest safe offset.
- **Loop and ring walkers** (`bmesh/intern/bmesh_walkers_impl.cc`): the opposite-edge rule at
  four-edge points, the n-gon pole case, boundary fans, delimits.
- **Shortest path** (`bmesh/tools/bmesh_path.cc`, `bmesh_path_region.cc`).
  - Dijkstra on points, edges or faces. A step's cost is its length times a factor that grows as
    the turn sharpens, so ties prefer straight paths.
  - Topology mode costs every step 1.
  - Fill region runs a breadth-first search from both ends and keeps the elements on any
    shortest path.
- **Select Similar** (`editors/mesh/editmesh_select_similar.cc`): the selected elements' values in
  KD-trees (1D for scalars, 3D for normals, 4D for planes), candidates tested by range query.
- **Grid Fill** (`bmesh/operators/bmo_fill_grid.cc`).
  - Corners are found by angle.
  - Span and offset choose the sides.
  - Interior points carry each boundary row's shape inward through a triangle frame, then the
    two directions are blended.
- **Join triangles** (`bmo_join_triangles.cc`): candidates scored for flatness and square
  corners, merged greedily, each new quad lowering its aligned neighbors' cost so grids grow
  consistently.
- **Decimate** (`bmesh/tools/bmesh_decimate_collapse.cc`): Garland–Heckbert quadrics, boundary
  planes weighted heavily, collapses that flip a face rejected, symmetry by paired edges.
- **Inset** (`bmo_inset.cc`): per-edge in-face normals averaged at each point, even
  (angle-corrected) and relative (length-scaled) offsets, edge rail.
- **Knife** (`editors/mesh/editmesh_knife.cc`): the cut network is built over the faces first,
  then each face is split by its net, with holes bridged to the boundary.
- **Region match** (`bmesh/tools/bmesh_region_match.cc`): order-independent topology hashes
  refined by re-hashing, for "select similar region".
