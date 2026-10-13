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
| Subdivide edges | n cuts on each selected edge, faces patterned | Blender Subdivide (quad corner modes) | — | ~ Subdivide works on faces |

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
| Bend, Twist, Taper, Squash | About an axis and an origin, limits along it; one node with a mode | Houdini Bend [doc]; Blender Simple Deform [src] | — |
| Lattice | Points moved by a cage | Houdini Lattice Deform, Blender Lattice | — |
| Soft Transform node | A transform with a falloff, as a node | Houdini Soft Transform | ~ Edit node's soft radius |
| Shrinkwrap / Ray | Points projected onto another mesh | Houdini Ray, Blender Shrinkwrap | — |
| Corrective smooth | Smooth that keeps the rest shape's detail | Blender Corrective Smooth [src] | — |
| Sculpt-lite brushes | Grab, smooth, inflate, flatten, pinch; radius and strength by drag; symmetry; on the Edit node as a step per stroke | Houdini Sculpt SOP; Blender sculpt; C4D Brush and Magnet | — |
| Edge Transport, Edge Relax | Values or positions moved along edges | Houdini | — |

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

**Stage 1: CAD tools onto the definition** (M3–M5).
- Family by family, in §3.6's order; `modify_picks` and `edit_cad_picks` become one prompt
  module; docs/TOOLS.md generated.
- Tests:
  - the parity check (node = step) for every CAD tool;
  - the existing CAD test files pass unchanged in what they assert;
  - the wiring-layer line count is reported in the commit.

**Stage 2: selection.**
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

**Stage 3: drag and the interactive core.**
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

**Stage 4: Bevel in full.**
- Offset types; vertex bevel; profile superellipse and custom ramp; miters outer
  sharp/patch/arc and inner sharp/arc; corner patches as grids (`ADJ`-style refinement) and
  cutoff; loop slide; harden normals; mark sharp.
- Tests:
  - a cube's 12 edges at 3 segments give the rounded cube with grid corners, all quads but the
    corner triangles where segments are odd;
  - vertex bevel of a cube corner adds one triangle;
  - outer arc miter on a 270° corner keeps the strip width;
  - a custom profile of a step makes a stepped strip.

**Stage 5: everyday modify tools.**
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

**Stage 6: primitives in full, and Poly Pen.**
- Box divisions; ico and quad spheres; caps and rows; Disc; Tube; Capsule; platonic solids;
  interactive placement on surfaces.
- Poly Pen: extrude an edge by dragging, split, delete under the pointer.
- Retopology on a reference mesh.
- Tests: counts per primitive option; Poly Pen dragging a boundary edge adds one quad; a
  retopology quad's points lie on the reference within tolerance.

**Stage 7: shape, topology and normals tools.**
- Circularize, Straighten, Space Evenly, Relax, Make Planar.
- Quadrangulate (quality-scored joining), Limited Dissolve, Un-subdivide, PolyReduce (quadric
  collapse), Triangulate methods.
- Recalculate outside, hard/soft by angle, seams, bevel weights.
- Tests:
  - Circularize of a cube's top makes a circle (radius spread < 1e-6);
  - Quadrangulate of a triangulated grid gives the grid back;
  - PolyReduce to 50% halves the face count and keeps the boundary;
  - Recalculate fixes a sphere with flipped faces.

**Stage 8: deformers, Mesh Check, sculpt-lite.**
- Bend/Twist/Taper/Squash as one node; Lattice; Shrinkwrap.
- Mesh Check overlay sharing the Select passes.
- Sculpt-lite brushes as stroke steps.
- Tests:
  - Twist 90° of a box column turns the top 90°;
  - Mesh Check counts on a fixture with each defect;
  - one brush stroke is one undo step.

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
   declares its `drag` row now (docs/TOOLS.md lists it); the driver is Stage 3.
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
