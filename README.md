# luced-3d

A native procedural 3D editor built with `luce-ui`, `luce-3d` and `luce-gpu`.
The neutral greys and `#E7A03F` orange match `luced-2d`.

```sh
luc install dymokomi/luced-3d
# Or, from a development checkout:
luc run --release
```

Use the current installed Luce toolchain and sibling checkouts. `luc build --release`
creates `build/Luced 3D.app` on macOS. `luc run -- --smoke` renders three frames
and exits. Runtime code is Luce for the editor and Luce Base for its libraries.

For large files, use the optimized build above. Current timings and the
caching design are in [PERFORMANCE.md](docs/PERFORMANCE.md).

## Documentation

- [DESIGN.md](docs/DESIGN.md): module boundaries, background computation and
  result caching, Edit recipes and undo, gizmos, viewport rendering, imports.
- [MODELING.md](docs/MODELING.md): the node set, Edit tools, attribute contracts
  and limits.
- [CAD_TESSELLATION.md](docs/CAD_TESSELLATION.md): STEP to polygons: pipeline,
  invariants, heuristics, tolerances, probing tools and known limitations.
- [PERFORMANCE.md](docs/PERFORMANCE.md): current numbers, what makes them fast,
  how to measure and open work.
- [GROUPS.md](docs/GROUPS.md): imported STEP hierarchy and Blast.
- [OUTLINER.md](docs/OUTLINER.md): output rules, Groups and nested networks.
- [PROJECTS.md](docs/PROJECTS.md): the project schema and UI persistence.

Related packages: CAD modeling and tessellation live in
[luce-cad](https://github.com/dymokomi/luce-cad) (its `tessellation` modules
hold NURBS evaluation and trim/grid meshing, formerly luce-tesselator), geometry
and rendering in [luce-3d](https://github.com/dymokomi/luce-3d), and the formats
in [luce-step](https://github.com/dymokomi/luce-step),
[luce-obj](https://github.com/dymokomi/luce-obj),
[luce-fbx](https://github.com/dymokomi/luce-fbx) and
[luce-usd](https://github.com/dymokomi/luce-usd). Each format owns its read and
write; the OBJ writer is `Obj.write` in luce-obj, the USD one `Usd.save` in
luce-usd.

![Procedural modeling with shared LuciaOS SVG icons](docs/preview_shared_icons.png)

## Projects and workspace

File → New/Open/Save/Save As uses `.prisma` documents through `luce-prism`.
Cmd/Ctrl-N, O, S and Shift-S are supported. Projects retain the authored node DAG,
nested Groups, output/enabled/visibility flags, parameters, Edit recipes, camera,
and network pan/zoom. External geometry paths are relative to the project when
possible; geometry is referenced, not embedded. Save changes before moving files.
New/Open/Quit protects unsaved changes with Save/Don't Save/Cancel.

Window size, dock splits, tab order/selection, floating panels, shading, grid and
normal display persist in `~/.luced-3d/ui.prisma`. Window → Reset Panel Layout
restores the default arrangement. Tests and captures do not read or write this
user preference file. See [project schema and persistence](docs/PROJECTS.md).

## Try modeling

1. Focus the Network pane. Press **Tab**, type `Transform`, and press Enter.
   The new node connects to the selected node and becomes the viewport output.
2. Change its Translation, Rotation or Scale in Parameters, or drag an XYZ
   handle in the viewport to translate it.
3. In Network, **Tab**, type `Edit Mesh`, Enter. The viewport gains the
   Object/Polygons/Edges/Vertices/Corners level buttons and a tool strip at the
   left, ending with primitives to create.
4. Choose Polygons (**2**), then click a face. Shift-click adds/removes components.
   At Object (**1**) a click selects a whole piece.
   Press **E** or click Extrude. Repeat to keep extending the selected cap.
5. Set **Next distance** before extrusion; **Last distance** changes the most
   recent extrusion. The Edit node lists the operations it owns.
6. Choose Move (**M**) and drag an XYZ handle to move selected points, edges or
   faces. **Q** returns to selection; **1–5** change the selection level.
7. **Cmd/Ctrl-Z** undoes; **Cmd/Ctrl-Shift-Z** redoes. A scrub or handle drag is
   one step; Escape cancels a handle or node drag.

## Network

- Drag empty space, middle-drag, or Space-drag to pan. Touchpad scrolling
  pans; the mouse wheel, Cmd/Ctrl-scroll and pinch zoom around the pointer.
- Drag node bodies to move them. Home or **Frame nodes** fits the network.
- Nodes use compact Houdini-inspired bodies, top inputs and bottom outputs.
- Drag or click-click from a geometry output to an input (or the reverse) to connect or replace
  a wire. Alt-click an input disconnects it. Outputs can feed multiple nodes.
- Node types are available in Tab/right-click search: primitives, modeling,
  transforms, copies, groups and attributes. Merge has two geometry inputs for
  joining branches. Cycles are rejected. See [capabilities](docs/MODELING.md).
- Tab or right-click opens a menu at the pointer, kept inside the window.
  Browse categories/submenus or type to filter; arrows and Enter choose.
- File imports OBJ, FBX (scene hierarchy, transforms, layers and instances; see
  [FBX files](docs/MODELING.md#fbx-files)), USD (.usd, .usda, .usdc, .usdz; see
  [USD files](docs/MODELING.md#usd-files)), PLY (meshes, point clouds and
  Gaussian splats, through luce-ply) and a bounded STEP subset. Export
  writes a node's result to USD, FBX, OBJ, PLY or prism. Browse or enter
  a path, then Reload for disk changes. STEP remains analytic: use Transform for
  scale and Tessellate for explicit polygon conversion. CAD surfaces appear
  automatically with patch boundaries using cached, disposable viewport meshes;
  no Tessellate node is needed just to see them. The File inspector contains only
  name, path, Browse/Reload, geometry summary and actual import errors. STEP/STP
  adds **STEP tolerance / 0 = file**: zero uses the source uncertainty; a positive
  value overrides it in source units. This per-node setting is saved in projects,
  supports undo, and reloads the analytic model off-main when changed. OBJ, FBX
  and PLY do not show this setting. It is separate from tessellation density. See the
  [import contracts](docs/DESIGN.md#imports) and the
  [CAD tessellation reference](docs/CAD_TESSELLATION.md).
- Tessellate's **Target edge length / 0 = off** refines boundaries and inserts
  interior grids. Smaller positive values give denser geometry; quads are used
  where suitable. Meshes include corner normals and STEP face colors as `Cd`.
- STEP product/occurrence and solid names become primitive group paths such as
  `Camera - 6/Lens:1/Phone Camera Lens v3:1/LensShell`. File, Transform, Merge,
  Tessellate and Blast preserve these paths. The Outliner shows their hierarchy
  beneath exposed nodes, with collapsible assembly branches.
- **Blast** deletes named groups; enable **Delete non-selected / isolate** to
  keep them instead. Exact parent paths include descendants. Use `*`/`?` globs,
  quotes around paths with spaces, and `^pattern` to subtract from a preceding
  selection (for example `* ^*/LensShell`). Empty selection means all geometry.
  CAD remains analytic when blasted before Tessellate. This is named primitive
  selection, not Houdini's complete expression/attribute-selection language.
- Click or hold the top-right grouped viewport square for Wireframe, Flat +
  Wireframe, Flat, Shaded, and Shaded + Wireframe. **Show normals** adds face-center
  normal guides. Rendered is visibly unavailable until a render engine exists.
- Clicking a node selects its properties. **O** and the right-hand strip toggle
  Out; multiple results can be exposed. **D** toggles isolated preview without
  changing outputs. The left-hand strip toggles bypass (**B**).
- The **Outliner** shows exposed results and nested Groups. Double-click a Group
  to enter its local network; Up returns to the parent. Groups have hierarchical
  transforms and visibility. See [output rules and limits](docs/OUTLINER.md).
- Disabling Transform, an Edit node or Merge passes its first input through.
  Disabling Cube produces empty geometry. Delete/Backspace in Network deletes
  the selected node and disconnects its consumers.
- Edit tools appear when the selected Edit node (Edit Mesh, Edit CAD, Edit SDF) is enabled and displayed; a selected and displayed Sketch node (inside a CAD node) is drawn and constrained in the viewport.
  Display it with D before modeling. Incomplete nodes show an error instead of
  stale geometry; connect their inputs or undo the change.

## Viewport

Maya-style: **Alt-left-drag** orbits, **Alt-middle-drag** pans, and
**Alt-right-drag** dollies (Option on macOS). Scroll/pinch also zooms.
Ordinary left-click is reserved for tools and selection.
**F** frames the displayed geometry; **G** toggles the grid. Component picking
ignores occluded points, edges and faces, with orange hover previews before
selection. Viewport tools use shared LuciaOS SVG icons with hover labels,
rendered by luce-ui's cached luce-svg pipeline.
Grid spacing is one unit; +Y is up.

## Implementation and limits

The lower dock also contains **Geometry Spreadsheet**. It follows the selected
node, independently of the viewport output, or can be pinned. Switch between
points, vertices (polygon corners), primitives (faces), and detail (the mesh's
counts and detail attributes, and the geometry's own detail attributes, such
as a sketch plane, even without a mesh).
Filter attributes or rows, click headers to sort, and click rows to select
components on the displayed Edit node. Numeric scalar/vector attributes survive
topology operations; `Cd` affects rendering and corner `uv` supports seams.

Each Edit kind (Edit Mesh, Edit CAD, Edit SDF) has its own
selection levels, tool strip and primitives, generated from its registry
entry. Edit Mesh's strip holds the luce-geocore modeling verbs (extrude, inset,
bevel, loop cut, bridge, fill, dissolve, knife, connect, edge slide, mirror,
spin, crease, PolyDraw and the point and face operators), each offered on the
levels it applies to; Edit CAD moves and deletes models and faces and edits
control vertices. Set **Tool amount** in Parameters before applying a tool;
hover icons for names. **Soft radius** and **Falloff** let nearby points
follow a move (the viewport tints the points they reach by weight),
**Symmetry** mirrors every tool across an axis plane, and **Keep selection**
carries the selection through topology tools. See [MODELING.md](docs/MODELING.md).

The graph has stable node IDs, geometry ports, shared cached results, downstream
invalidation and demand-driven evaluation of exposed outputs or preview. Edit nodes
store ordered operations against immutable mesh snapshots. A 64-bit topology
hash guard rejects incompatible upstream changes instead of applying edits to
wrong IDs. Results are cached by content stamp ([design](docs/DESIGN.md#background-computation)).
Undo covers graph changes, nested deletion, parameters, Out/visibility/preview/bypass, selections and modeling;
history retains 64 transactions.

Geometry storage, groups, modeling verbs, ray queries and the geometry codec
live in luce-geocore; CAD models and their tessellation in luce-cad; the
renderer and Edit overlays in luce-3d, drawing through luce-gpu from retained
GPU arrays. None of them depends on UI. Editor state, graph evaluation,
commands and tools stay in this project; the viewport is `luce-ui`'s
`SceneView` widget.

This is an experimental modeling foundation. Transform/Group gizmos support Move, Rotate, Scale and compensated Pivot;
Cube supports corner resizing. Shift snaps and +/- changes gizmo size.
Limits include 128 nodes, 8,388,608 points/faces and 33,554,432 corners per mesh;
individual operators and importers can have tighter safety budgets. General
typed attribute sockets and a path tracer are not implemented. CAD tessellation
still has known difficult trims and poorly distributed regions under active work.

## Verification

```sh
luc test
python3 tools/preview.py --scene edit  # macOS desktop / Metal capture
python3 tools/profile.py             # CPU phase timings
python3 tools/profile.py native      # native orbit frame intervals
```

Tests cover topology and concave triangulation, region extrusion, ray picking,
branching DAGs, invalid links, caching, bypass, topology guards, transactions,
Tab search, actual wire and parameter gestures, face picking, extrusion,
translation handles, File/Tessellate and background cooking, and resized UI
rendering, in the test program `tests/editor`. CAD-only tessellation regressions
live in luce-cad (`luc test` there); format tests live in luce-step, luce-obj and
luce-fbx.

See [DESIGN.md](docs/DESIGN.md) for module boundaries and architectural references.
See [PERFORMANCE.md](docs/PERFORMANCE.md) for measured timings and how to reproduce them.

## Licenses

Code: MIT OR Apache-2.0. Rounded icons by
[Dy Mokomi / luciaos-assets](https://github.com/dymokomi/luciaos-assets),
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), including new modeling
and shading glyphs contributed in the same style. The test fixtures are original
(`tests/fixtures/README.md`); Desktop CAD models are not included.
