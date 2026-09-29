# Modeling capabilities

This is a substantial initial operator set, not Houdini or Blender feature parity.
No placeholder nodes are listed: every registered node evaluates geometry.

![Cube → AttributeRandomize → Bevel → Edit, with an inset and extruded face](preview_modeling.png)

## Geometry nodes

| Family | Nodes |
| --- | --- |
| Sources | Cube, Grid, Sphere, Cylinder, Cone, Torus, File |
| Graph | Edit, Merge, Null, Switch, Tessellate, Group, Blast |
| Transforms/copies | Transform, Mirror, CopyTransform, CopyToPoints, MatchSize |
| Modeling (verbs) | Delete, Reverse, Triangulate, Duplicate, Split, Inset, PolyExtrude, Subdivide, Fuse, Clean, PolyBevel, Loop Cut, Bridge, Fill, Dissolve |
| Deformation (verbs) | Transform Components, Smooth, Mountain, Peak, Flatten, Snap |
| Attributes | AttributeCreate, AttributeRandomize, AttributeDelete, AttributeRename, AttributePromote, Selection Group, Normal, Measure, UVProject, Color |

Modeling and deformation nodes are luce-geocore verbs (after Houdini's SOP
verbs): one Base kernel per operation, shared with the Edit node. The node
catalog is generated from the verb registry, so each has the verb's
parameters plus Houdini's **Group** (text) and **Group Type** (Guess from group,
Points, Edges, Primitives, Vertices). An empty group is every element. Groups
use Houdini's group syntax with our functions (see luce-geocore's API):
`0 2-5`, `0-99:2`, `top ^left`, `@P.y>0`, `@name=piece*`, `p3-4-5`,
`grow(top, 2)`, `loop(p5-6)`. A group of another component type converts
(a face is in a point group when all its points are; Delete removes every face
using a deleted point, like Blast). Numbers naming no element match nothing.

A verb carries every attribute and group through its provenance: an element
with one parent copies it; an interpolated one (a subdivision edge point, a
new corner inside a face) averages floats, renormalizes normals, takes the
heaviest parent's integer or text, and keeps group membership only when every
parent is a member. New elements are zero, empty and in no group. Each verb
also returns an output selection (Extrude's front faces, Inset's inner faces,
Fuse's merged points), which the tool flow adopts.

## Selection and tools

Components (points, edges, faces or vertices, keys 1–4) can be selected on
whichever node the viewport displays; the selection is a luce-geocore
`Selection` (bits plus the connectivity they index), so select all, invert,
grow, shrink, border, flood, loop and ring are word-parallel Base passes.
Switching the component type carries the selection over (a face stays when
all its points were selected).

Pressing a tool, as with Houdini's shelf tools:

- on the active **Edit node**, appends a step to its recipe (see below);
- on any other displayed node, creates the tool's verb node after it (between
  it and whatever it fed), with **Group** set to the selection's expression
  (runs such as `0-5 12`, a group's name, or chained edge pairs `p3-4-5`),
  **Group Type** set to the component type, and a **guard**: the connectivity
  hash the group was selected on. Display and the node selection move to it,
  and when it cooks its output selection (Extrude's front faces, Inset's inner
  faces) becomes the viewport selection, switching the component type. The
  Move gizmo on a plain node makes a Transform Components node the same way.
- with nothing selected, the new node waits (Tool → Select): the viewport shows
  its input, Enter takes the selection as the group, Esc removes the node.

If the input's topology later changes, a guarded node fails with "Group was
selected on different topology. Reselect, or Keep IDs." **Reselect** shows the
input with the group selected for a new pick; **Keep IDs** clears the guard and
applies the numbers as they are (Houdini's behaviour). Typed groups are never
guarded. Very large selections show as a summary in the Group field.

## Edit tools and important limits

- PolyExtrude moves face regions (or each face, with Individual faces) along
  their averaged normals, with an inset across the region's boundary and
  divisions along the walls; each run of faces around a boundary point gets
  its own front point, and a whole closed surface simply moves out. An edge
  group extrudes its edges into quads (outward in the face plane on a mesh
  boundary) and selects the front edges. There is no twist, taper or spine.
- Inset moves the rim of each region (or face) inward by a distance, with an
  optional depth; inner corners blend their face's corners so UVs follow.
  Clamp keeps each move within half of the boundary edges beside it.
- Loop Cut cuts 1–64 loops across the quads of each group edge's ring (or
  only between the group's edges), slid together toward one side; other faces
  on the ring take the new points, and a quad already cut by one ring stops a
  crossing ring. The new loop edges are selected.
- Bridge joins pairs of boundary loops or runs among the group's edges (each
  with the nearest one of its kind) with rows of quads when they have as many
  edges, else with triangles zipped by distance along them. Loops are paired
  facing each other; coplanar holes twist. Twist turns where a loop starts.
- PolyBevel bevels the group's interior edges by a constant offset measured in
  the faces beside them, with 1–64 segments along a profile (0.5 round, 0
  flat) and overlap clamping. Where three or more beveled edges meet, the hole
  becomes one patch face (no grid patch); a lone beveled edge's end vertex
  stays and its strip fans around it. Edges at non-manifold points are skipped
  with a warning.
- Subdivide operates on the whole mesh, Catmull–Clark or linear, with edges used
  by more than two faces kept as creases. There are no crease weights yet.
- Fill caps one boundary loop of the group's edges. Dissolve joins faces across
  up to 128 edges.
- Fuse merges the group's points within a distance into the first of them,
  dropping faces that collapse.
- CopyToPoints realizes copies at target positions, with a 256-copy limit. It
  does not yet interpret orientation/scale attributes or retain instances.

## The Edit node

The Edit node is a modeling engine in one node: while it is displayed and
selected, every tool appends a step to its recipe instead of creating a node,
and each tool (or each drag) is one undo. There is no operation list to edit.

- A step is one verb run: the verb, the group expression and its type, the
  parameter values, the connectivity hash the group was selected on, and the
  node's Symmetry and Keep selection settings at the time.
- The recipe is the truth: undo restores a shorter recipe. The worker keeps
  the results after the last eight steps and every sixteenth (D18), so undo
  and redo inside that window cook nothing, and a deeper undo replays at most
  fifteen steps. Consecutive moves of the same components merge into one step
  (D19); each drag remains its own undo.
- After a topology tool the selection becomes what the tool made (Extrude's
  front faces); with **Keep selection** it is instead the selection carried
  through the tool (a new element is selected when all its parents were).
- **Soft radius** and **Falloff** (linear, quadratic, cubic, smooth) make
  moves, rotations and scales pull the points near the selection, by the
  distance to the nearest selected point.
- **Symmetry** (X, Y or Z) mirrors every tool: the group gains the mirror of
  each member (points, faces, edges and vertices matched by position within a
  ten-thousandth of the model's size), and moved points' mirrors move to the
  mirrored places; points on the plane stay on it.
- An upstream change that alters the input's topology fails the node: "Edit
  input topology changed. Undo the upstream change or clear this node's edits."
  Position-only upstream changes flow through the recipe.

## Attribute contracts

Domains are point=0, vertex/corner=1, primitive/face=2, detail=3 and edge=4.
Numeric tuples have 1–4 components, float or integral values; text attributes
index a shared string table; groups are flagged boolean attributes. Names are
unique within a domain; `P` is reserved for built-in positions. Matrices and
arbitrary field sockets are not implemented.

Topology builders carry output-to-input parent maps (see the verbs above).
Extrusion walls inherit the originating face. Merge unions
schemas and zero-fills absent attributes; conflicting types fail and the left
detail value wins. Promotion averages contributing floating values; integer
promotion chooses the first contributor. Original-domain attributes are retained.

`Cd` and `uv` are consumed by rendering with corner > point > primitive > detail
precedence. Shaded display consumes corner `N` when present (CAD tessellation
writes analytic normals); Flat uses face normals. Generic numeric vector attributes are not automatically transformed
as directions/normals. UVProject is planar XZ projection, not UV unwrapping.

The Geometry Spreadsheet is virtualized, horizontally/vertically scrollable,
sortable, filterable and pinnable. It displays selected-node geometry separately
from the display flag. It is an inspector/selection surface, not a direct cell
editor; modify attributes with nodes.

## Operator fidelity

Houdini's [Subdivide](https://www.sidefx.com/docs/houdini/nodes/sop/subdivide.html),
[Fuse](https://www.sidefx.com/docs/houdini/nodes/sop/fuse.html),
[PolyBevel](https://www.sidefx.com/docs/houdini/nodes/sop/polybevel.html) and
[Smooth](https://www.sidefx.com/docs/houdini/nodes/sop/smooth.html) are the
references for these operators, and each is broader than ours: Subdivide
motivated separate topology/position handling and linear attribute interpolation;
Fuse shows that merging points needs explicit attribute ownership (ours keeps the
first representative, and Clean is separate); PolyBevel also offers point
bevels, per-edge offsets and patterned corner patches, where ours makes one
patch face per corner; Smooth has more controls than our one-step neighbor relaxation. The
limits above document these differences rather than claiming SOP equivalence.
Fields should arrive as a deliberate type-system addition, not ad-hoc
expressions inside widgets.

## Remaining modeling milestones

Selected-edge bevel and fillets, knife/loop cuts, multi-edge dissolve, bridge
loops, robust booleans, remeshing, UV unwrap, instancing, general fields, multi-node
selection, wire insertion and subnets remain future work.
