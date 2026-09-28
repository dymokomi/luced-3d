# Modeling capabilities

This is a substantial initial operator set, not Houdini or Blender feature parity.
No placeholder nodes are listed: every registered node evaluates geometry.

## Forty-two geometry nodes

| Family | Nodes |
| --- | --- |
| Sources | Cube, Grid, Sphere, Cylinder, Cone, Torus, File |
| Graph | Edit, Merge, Null, Switch, Tessellate, Group |
| Transforms/copies | Transform, Mirror, CopyTransform, CopyToPoints, MatchSize |
| Topology | Reverse, Triangulate, Subdivide, Fuse, Inset, Bevel, PolyExtrude, Duplicate, Split, Delete, Clean |
| Deformation | Smooth, Mountain, Peak |
| Attributes | AttributeCreate, AttributeRandomize, AttributeDelete, AttributeRename, AttributePromote, Selection Group, Normal, Measure, UVProject, Color |

Groups accept `*`, space/comma-separated IDs, inclusive ranges (`2-5`), or
`@name` for nonzero values of an attribute in the applicable domain. This is not
an expression language. Invalid IDs and incompatible attribute schemas fail
atomically and appear as node errors.

## Edit tools and important limits

- XYZ movement uses the translation gizmo. Rotate currently rotates around Y
  in degrees; Scale is uniform about the selection center. Flatten targets Y.
- Extrude operates on selected face regions with boundary walls. It does not
  extrude isolated edges/points or an entire closed surface.
- Inset is an individual-face centroid fraction, not an exact-distance offset.
- Bevel chamfers all edges of a closed oriented manifold, using a fractional
  width. It is not a selected-edge, constant-width, multi-segment fillet.
- Subdivide operates on the whole mesh, with Catmull–Clark positioning or linear
  quads in the procedural node. There are no crease weights yet.
- Fill accepts one selected boundary loop. Dissolve accepts one internal edge.
- Delete handles points, faces, or the faces incident to selected edges. Clean
  removes unused points; deleting faces alone deliberately preserves points.
- Duplicate offsets selected faces along their normals; Split unshares them.
- Fuse uses spatial hashing and deterministic first-point attribute ownership.
- Smooth, Noise, Peak, Snap, Reverse and Triangulate are selection-aware.
- CopyToPoints realizes copies at target positions, with a 256-copy limit. It
  does not yet interpret orientation/scale attributes or retain instances.

Each Edit operation stores its selection and exact input topology signature.
Topology-incompatible upstream edits fail rather than silently moving wrong IDs.
Undo/redo includes modeling, groups, attribute parameters and graph changes.

## Attribute contracts

Domains are point=0, vertex/corner=1, primitive/face=2 and detail=3. Numeric tuples
have 1–4 components, float or integral values. Names are unique within a domain;
`P` is reserved for built-in positions. Limits: 32 named attributes per mesh and
262,144 numeric values per attribute. Strings, matrices and arbitrary field
sockets are not implemented.

Topology builders carry output-to-input parent maps. Retained/duplicated elements
inherit values; newly created elements without parents receive zero. Extrusion
walls inherit the originating face. Subdivision interpolates floating point
point/corner values; integer values retain deterministic parents. Merge unions
schemas and zero-fills absent attributes; conflicting types fail and the left
detail value wins. Promotion averages contributing floating values; integer
promotion chooses the first contributor. Original-domain attributes are retained.

`Cd` and `uv` are consumed by rendering with corner > point > primitive > detail
precedence. Stored `N` is inspectable metadata; shading currently uses geometric
face normals. Generic numeric vector attributes are not automatically transformed
as directions/normals. UVProject is planar XZ projection, not UV unwrapping.

The Geometry Spreadsheet is virtualized, horizontally/vertically scrollable,
sortable, filterable and pinnable. It displays selected-node geometry separately
from the display flag. It is an inspector/selection surface, not a direct cell
editor; modify attributes with nodes.

## Remaining modeling milestones

Selected-edge bevel and fillets, knife/loop cuts, multi-edge dissolve, bridge
loops, robust booleans, remeshing, UV unwrap, instancing, general fields, multi-node
selection, wire insertion and subnets remain future work. Project persistence is
also not implemented: this is still an experimental session-based editor.
