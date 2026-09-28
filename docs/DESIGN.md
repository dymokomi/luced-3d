# Editor and engine boundaries

`luced-2d` is the application reference: workspace state is separate from the
viewport, `luce-ui` provides dock panels and controls, and shared `Command`
instances drive keyboard and button actions. Signal connections are retained
and disconnected at shutdown. The theme reproduces its default grey/orange
palette using the same linear-light conversion in `luce-color`.

    luced-3d → luce-ui
             → luce-3d → luce-gpu

The application does not implement native graphics backends. `luce-gpu` owns GPU
resources and submission; `luce-3d` owns topology, geometry operations, cameras,
materials, picking and rendering. `luced-3d` owns the graph, evaluation policy,
operation recipes, selection, interaction and history. The Metal observer under
`tools/` is only for test capture, following `luced-2d`'s preview workflow.

## Graph and evaluation

`network.luc` defines stable-ID nodes and ordered geometry input ports. Outputs
can fan out; Merge combines two inputs. A proposed connection traverses upstream
dependencies before committing, rejecting self-links and cycles. Evaluation
also detects cycles defensively. Missing inputs remain explicit and yield a
visible node error. Deletion disconnects consumers, so no dangling IDs remain.

Parameter and connection changes dirty only the changed node and its downstream
consumers. Evaluation starts at the displayed node and caches immutable
`PolygonMesh` results; a shared ancestor cooks once. Camera movement, node layout,
renaming and component selection do not cook geometry. Errors are cached until
the relevant dependencies change. An invalid displayed branch clears the old
mesh rather than pretending it is the current output.

Selected and displayed node IDs are independent. Disabled operators pass through
their first input (including Merge); disabled generators return empty geometry.
Grid and lights are viewport helpers, outside the user's graph.

## Edit recipes and undo

An Edit node stores ordered immutable `EditOperation`s. Moves retain selected
point IDs and a displacement; extrusions retain face IDs and distance. Each
operation checks the exact ordered input topology before replay. Changing an
upstream transform or cube dimensions preserves topology and replays edits;
changing connectivity to incompatible topology yields an error with guidance.
The latest extrusion distance can be changed without adding another operation.

`history.luc` retains before/after snapshots for up to 64 transactions. Graph
records and selection arrays are copied; immutable mesh results and operation
objects are shared. `Workspace.perform` is the mutation boundary. Rejected
operations restore the before snapshot and leave history intact. New commands
after undo discard the redo branch. Parameter scrubs and gizmo/node drags bracket
one transaction; gizmos preview against the gesture's original state, so a long
drag does not accumulate hundreds of mesh operations. Escape or lost capture
cancels a gizmo/node drag.

## Interaction

- `actions.luc`: shared `luce-ui.Command` objects and state-dependent enabling.
- `network_view.luc`: graph coordinates, pointer-centred zoom, pan, port hit
  testing, wiring, flags, node movement and drawing. It explicitly accepts Tab
  so the UI focus traversal does not consume node search.
- `inspector.luc`: selected-node properties and Edit operation information. It
  avoids replacing an active number field's unchanged value while typing.
- `viewport_tools.luc`: component controls, selection overlays, projected
  translation handles and ray-based occlusion tests. These are editor tools,
  enabled by the selected/displayed node's capabilities.
- `view.luc`: navigation and composition with `three_ui.SceneView`.
- `panels.luc` / `app.luc`: composition, search palette, refresh and lifecycle.

## Mesh representation

`luce-3d.PolygonMesh` separates shared points, polygon corner lists, per-face
normals and unique edges. A hashed edge table is built once per immutable result.
Ear-clipped triangles support concave polygons; draw/pick/overlay use the same
triangulation. Transform regenerates normals from geometry and reverses winding
under reflection. Region extrusion duplicates selected points once, keeps cap
face IDs, and emits walls only on the selected region's boundary. It does not
create internal walls between adjacent selected faces. Offset directions use
averaged selected-face normals. It does not perform collision resolution or
self-intersection cleanup across separate faces.

The initial limits are 128 graph nodes, 16,384 points/faces, 65,536 corners and
256 corners per face. All mesh operators validate inputs and create new results;
failure leaves their input mesh unchanged. Face-local UVs are provisional; a
numeric attributes now have explicit point/face/corner provenance through
topology changes. New elements inherit, interpolate, or receive zero according
to the operator contract in MODELING.md. An immutable triangle BVH accelerates
picking and visibility queries.

## Architectural references and direction

Blender's [geometry evaluation graph](https://github.com/blender/blender/blob/main/source/blender/nodes/NOD_geometry_nodes_lazy_function.hh)
is a reference for cached, demand-driven evaluation and treating groups as graph
units. Its [Transform Geometry node](https://github.com/blender/blender/blob/main/source/blender/nodes/geometry/nodes/node_geo_transform_geometry.cc)
illustrates a geometry-input/output operator with translation, rotation and
scale. Its [region extrusion implementation](https://github.com/blender/blender/blob/main/source/blender/bmesh/operators/bmo_extrude.cc)
was studied for the distinction between region boundaries and interior edges.
The Luce implementation is original; no Blender source was copied or linked.

Houdini's [network editor](https://www.sidefx.com/docs/houdini/network/nodes.html),
[wiring](https://www.sidefx.com/docs/houdini/network/wire.html) and
[flags](https://www.sidefx.com/docs/houdini/network/flags.html) informed the compact
top-to-bottom graph, click-click/drag wiring, hover hints, and independent selected,
displayed and bypassed states. Our flags remain orange, not Houdini's multicolor
scheme. Fixed-screen-size hover controls provide bypass, display and spreadsheet
inspection. Wire insertion, multiselection and subnet navigation are not
implemented. The user's ResearchGate image URL returned 403, so its precise
appearance could not be inspected.

Blender's [mesh toolbar](https://docs.blender.org/manual/en/latest/modeling/meshes/tools/toolbar.html)
informed the component buttons and left icon strip. `tool_icons.luc` contains
original native vector glyphs; no raster dependencies or copied Blender artwork.
Camera navigation follows [Maya's Alt-button mapping](https://help.autodesk.com/cloudhelp/2026/ENU/Maya-Basics/files/GUID-941480C1-9BDA-4DB3-8EA8-113A0D6FAF1F.htm).
See PERFORMANCE.md for the current shared-UI secondary-button modifier/capture
limitation and local workaround.

There is one editor graph context. Future subnetworks should package this same
kind of graph with exposed inputs/outputs; entering a subnetwork changes visible
scope, not operator categories. General attribute sockets, subgraphs,
serialization and more modeling operators build on this foundation. GPU geometry
processing, shader materials, texture support and acceleration structures belong
in the engine. No path tracer is included, and current CPU preparation must not
be described as GPU geometry acceleration.

## Expanded module boundaries

`node_catalog.luc` is the shared source of node kinds, input arity, parameter
defaults/ranges and inspector metadata. `network.luc` owns graph validity and
caching; `node_evaluation.luc` dispatches operators; `component_groups.luc`
resolves component groups. `edit_operations.luc` owns replayable modeling
recipes. `geometry_sheet.luc` virtualizes tabular geometry inspection.
Inspector controls have stable parents even when changing node type.

The engine separates attributes, topology builders, primitive generators,
general operators, boundary/manifold tools and triangle acceleration into
individual modules. Topology operators use explicit parent maps rather than
editor-specific selection state. Attribute data belongs to immutable meshes,
not spreadsheet widgets. See MODELING.md for current contracts and RESEARCH.md
for the research-driven direction.
