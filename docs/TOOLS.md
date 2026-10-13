# Tools

Generated from the tool registry (`src/tool_registry.luc`) by `tools/tool_docs.py`; do not edit
by hand. A test fails when this page is stale.

Every tool is declared once. Its node, its Edit step, the tool bar, the Create, Modify and Select
menus, the A/S/D marking menus, the right-click menu, Repeat, its prompt, its icon and this page
all come from that declaration (docs/research/POLY-MODELING.md §3). The mesh tools are
luce-geocore's verbs; each CAD tool is a `src/tool_<name>.luc` listed in `src/cad_tools.luc`.

## Geo

Edit Mesh and the Geo context's nodes.

### Create

#### Draw

##### PolyDraw

Add a polygon through drawn positions, or through the group's points.

- Node `PolyDraw` in Geo; a step of Edit Mesh.
- Works on points.
- With nothing selected: "Select three or more points, or click to place corners".
- Gesture: clicks place its corners when nothing is selected; Enter finishes.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Snap distance | 0.0 | yes | Drawn corners this close to an existing point use it (0: only where they coincide). |
| Corners | 0 | no | How many drawn positions follow (x, y, z each); 0 makes the face through the group's points. |

### Modify

#### Extrude

##### Extrude

Extrude faces (as regions or one by one), edges or points.

- Node `PolyExtrude` in Geo; a step of Edit Mesh.
- Works on faces or edges or points.
- After it runs, moving the pointer sets Distance (along the selection's average normal); a click keeps it, the wheel steps Divisions, X, Y or Z locks Vector to that axis.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Distance | 0.2 | yes | How far the fronts move. |
| Inset | 0.0 | yes | How far the fronts' boundaries move inward across the faces; for points, how far along each edge a spike's base sits (0: a quarter of the edge). |
| Divisions | 1 | yes | Rows of faces along each wall. |
| Individual faces | off | yes | Extrude each face on its own, along its own normal, instead of each connected region. |
| Direction | Region normal | yes | Which way the fronts move: along each region's average normal, along each point's normal, or along Vector. |
| Clamp inset | on | yes | Keep each inset within half of the boundary edges beside it. |
| Vector | 0.0, 0.0, 0.0 | yes | The way the fronts move when Direction is Vector (its length does not matter; zero moves along the region's normal). |
| Twist | 0.0 | yes | Degrees each front turns about its region's center, the wall rows turning with it. |
| Taper | 1.0 | yes | How each front scales about its region's center (1 keeps its size), the wall rows following. |
| Manifold | off | yes | Merge each wall that would lie in the plane of the face beside it into that face, so faces pushed into a solid cut it cleanly. |

##### Inset

Inset faces by a distance, as regions or one by one.

- Node `Inset` in Geo; a step of Edit Mesh.
- Works on faces.
- After it runs, a drag in the viewport sets Thickness (hauled away from the selection's center); a click keeps it.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Thickness | 0.1 | yes | How far the inner faces' boundaries move inward. |
| Depth | 0.0 | yes | How far the inner faces move along their normals. |
| Individual faces | off | yes | Inset each face on its own instead of each connected region. |
| Outset | off | yes | Move the rim outward into the faces around the group, which keeps its size and stays selected. |
| Even | on | yes | Keep the rim's width at corners: a point goes further where the boundary turns. |
| Clamp | on | yes | Keep each inset within half of the boundary edges beside it. |
| Relative | off | yes | Scale the thickness at each point by the mean length of the boundary edges there. |
| Edge rail | off | yes | Slide each boundary point along the edge between the two group faces beside it, where there is one. |
| Boundary | on | yes | Inset along the mesh's open edges too; off, the rim slides along them. |

##### Duplicate

Copy the group's faces, offset along their normals.

- Node `Duplicate` in Geo; a step of Edit Mesh.
- Works on objects or faces.
- After it runs, a drag in the viewport sets Offset (along the selection's average normal); a click keeps it.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Offset | 0.2 | yes | Distance of the copies along their face normals. |

#### Bevel

##### Bevel

Bevel the group's edges into strips with corner patches, or cut off its points.

- Node `PolyBevel` in Geo; a step of Edit Mesh.
- Works on edges or points.
- After it runs, a drag in the viewport sets Width (hauled away from the selection's center); a click keeps it, the wheel steps Segments.
- While its drag lasts: A drags Width, P drags Shape, S drags Segments, M cycles Width Type, V cycles Affect, O cycles Miter Outer, I cycles Miter Inner, Z cycles Profile Type, N cycles Intersection, C flips Clamp overlap, H flips Harden normals, U flips Mark seams, K flips Mark sharp, L flips Loop slide.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Width | 0.1 | yes | How far the bevel reaches; Width Type says how it is measured (Percent reads it as a percentage). |
| Segments | 1 | yes | Faces across each strip. |
| Shape | 0.5 | yes | The profile across a strip: 0.5 round, 0.25 a straight chamfer, 1 the square corner, 0 hollowed in to the opposite corner. |
| Width Type | Offset | yes | Offset: from the edge to the strip's sides across the faces. Width: the strip's own width. Depth: from the edge straight in to the strip. Percent: a share of the edges beside. Absolute: along the edges beside. |
| Affect | Auto | yes | Bevel edges, or cut off points; Auto cuts off points for a group of points and bevels edges otherwise. |
| Clamp overlap | on | yes | Keep the width below where strips and patches would cross. |
| Loop slide | on | yes | Slide the strip's sides along an unbeveled edge between two beveled ones, keeping edge loops straight. |
| Profile Type | Superellipse | yes | The profile's shape: the superellipse Shape sets, or the Custom profile ramp. |
| Miter Outer | Sharp | yes | Where three or more beveled edges meet round an outside corner over 180°: a sharp miter, a patch, or an arc. |
| Miter Inner | Sharp | yes | Where beveled edges meet inside a corner under 180°: a sharp miter or an arc, spread apart by Spread. |
| Spread | 0.1 | yes | How far an inner arc miter's points spread along their edges. |
| Intersection | Grid Fill | yes | How a corner where three or more beveled edges meet fills: a grid of faces following the profiles, or a face cutting off each strip's end. |
| Harden normals | off | yes | Give the bevel's corners normals that blend into the faces beside it (writes N on corners). |
| Mark seams | off | yes | Carry a beveled edge's seam across the corner patches to the next beveled seam. |
| Mark sharp | off | yes | Carry a beveled edge's sharp mark across the corner patches to the next sharp one. |
| Face strength | None | yes | Write face_strength for weighted normals: 1 weak on corner patches, 2 medium on strips, 3 strong on the faces kept; New the bevel's faces, Affected also the rebuilt faces, All every face. |
| Material | -1 | yes | The new faces' material: -1 keeps the material of the faces beside them, 0 and up the mesh's material of that number (in order of first use). |
| Limit | None | yes | Bevel only the group's edges whose faces meet at more than Angle, or whose bevel_weight is above 0 (the weight also scales the width). |
| Angle | 30.0 | yes | With Limit Angle: the least angle between an edge's face normals, in degrees. |
| Custom profile | a ramp | yes | With Profile Type Custom: the profile across a strip, its depth from the straight chamfer (0) to the square corner (1) at each place across (0 to 1). |

##### Bevel Weight

Set the bevel_weight of the group's edges or points for Bevel's Limit Weight.

- Node `Bevel Weight` in Geo; a step of Edit Mesh.
- Works on edges or points.
- After it runs, a drag in the viewport sets Weight (rightward, its range over 300 points); a click keeps it.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Weight | 1.0 | yes | The weight the group's edges (or points) get: Bevel with Limit Weight scales its width by it, and leaves those of weight 0. |
| Mode | Set | yes | Give the group this weight, or clear it to 0. |

#### Cut

##### Loop Cut

Cut edge loops across the rings of the group's edges.

- Node `Loop Cut` in Geo; a step of Edit Mesh.
- Works on edges.
- Gesture: the edge under the pointer shows what it makes, the wheel sets the count; a click makes it there.
- After it runs, moving the pointer sets Slide (along the rails of the element under the pointer); a click keeps it, the wheel steps Cuts.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Cuts | 1 | yes | New loops across each ring. |
| Slide | 0.0 | yes | Move the loops toward one side of the ring (-1..1). |
| Even | off | yes | Slide every cut the same distance, so each loop keeps its shape. |
| Flip | off | yes | With Even: keep each loop the same distance from the next loop on the slide's side, taking its shape. |
| Whole ring | on | yes | Cut the whole ring through each of the group's edges; off: only across the group's edges. |

##### Offset Edge Loops

Add two edge loops either side of the group's loops.

- Node `Offset Edge Loops` in Geo; a step of Edit Mesh.
- Works on edges.
- After it runs, moving the pointer sets Amount (along the rails of the element under the pointer); a click keeps it.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Amount | 0.25 | yes | How far along the edges beside the loops the new loops sit, as a share of each (of their mean length with Even). |
| Even | off | yes | Put every new point the same distance from its loop. |
| Cap ends | off | yes | Take the new loops round the ends of open runs instead of meeting there. |

##### Knife

Cut the group's faces with a plane; keep one side, or both.

- Node `Clip` in Geo; a step of Edit Mesh.
- Works on components.
- Gesture: a stroke dragged across the model.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Axis | Y | yes | The axis the cutting plane faces, or the plane below (Custom). |
| Offset | 0.0 | yes | Where the plane crosses its axis (Custom: how far it moves along its normal). |
| Through centroid | off | yes | Put the plane through the group's centroid (Offset then moves it from there). |
| Keep | Above | yes | The side of the plane kept; Both cuts and keeps everything. |
| Plane point | 0.0, 0.0, 0.0 | no | Custom: a point on the plane. |
| Plane normal | 0.0, 0.0, 0.0 | no | Custom: the plane's normal; above is the side it points to. |

##### Connect

Connect the group's points or edge middles across their faces.

- Node `Connect` in Geo; a step of Edit Mesh.
- Works on points or edges.
- With nothing selected: "Select points (or edges) across faces".
- After it runs, a drag in the viewport sets Position (rightward, its range over 300 points); a click keeps it.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Position | 0.5 | yes | Where along each of the group's edges the new point sits. |

##### Edge Slide

Slide the group's edges along the faces beside them.

- Node `Edge Slide` in Geo; a step of Edit Mesh.
- Works on edges.
- After it runs, moving the pointer sets Amount (along the rails of the element under the pointer); a click keeps it.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Amount | 0.0 | yes | How far along the rails, as a share of each rail (of their mean length with Even); the sign picks the side. |
| Even | off | yes | Move every point the same distance, so the loop keeps its shape. |
| Flip | off | yes | With Even: keep every point the same distance from its rail's end, so the loop takes the shape of the loop beyond. |
| Clamp | on | yes | Keep the amount within -1..1 and every point on its rail. |

##### Vertex Slide

Slide the group's points along their edges.

- Node `Vertex Slide` in Geo; a step of Edit Mesh.
- Works on points.
- After it runs, moving the pointer sets Amount (along the rails of the element under the pointer); a click keeps it, X, Y or Z locks Direction to that axis.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Amount | 0.0 | yes | How far along each point's edge, as a share of it (of the edges' mean length with Even). |
| Direction | 0.0, 0.0, 0.0 | yes | Each point slides along its edge that runs most this way (a drag picks it). |
| Even | off | yes | Move every point the same distance. |
| Flip | off | yes | With Even: keep every point the same distance from its edge's far end. |
| Clamp | on | yes | Keep the amount within 0..1 and every point on its edge. |

#### Fill

##### Fill

Cap each closed loop of the group's boundary edges.

- Node `Fill` in Geo; a step of Edit Mesh.
- Works on edges.
- With nothing selected: "Select the boundary edges around each hole".

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Mode | Single face | yes | One face per loop, or triangles around a new point at its center. |

##### Bridge

Join pairs of boundary loops or runs among the group's edges with faces.

- Node `Bridge` in Geo; a step of Edit Mesh.
- Works on edges.
- With nothing selected: "Select two boundary loops or runs of edges".

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Divisions | 1 | yes | Rows of faces across each bridge (chains with as many edges). |
| Twist | 0 | yes | Turn where a closed pair's second loop starts, by this many points. |

#### Merge

##### Fuse

Merge nearby points of the group.

- Node `Fuse` in Geo; a step of Edit Mesh.
- Works on objects or points.
- After it runs, a drag in the viewport sets Distance (hauled away from the selection's center); a click keeps it.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Distance | 0.001 | yes | Points of the group closer than this merge into the first of them. |

##### Merge Points

Merge the group's points: at their center, first, last, per island or by distance.

- Node `Merge Points` in Geo; a step of Edit Mesh.
- Works on points or edges or faces.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Mode | At center | yes | Where the group's points merge: all at their center, the first or the last point; each connected island at its center; or those within the distance. |
| Distance | 0.001 | yes | By distance: points of the group closer than this merge. |

#### Delete

##### Delete

Remove the group's faces (points delete every face using them) and the points left unused.

- Node `Delete` in Geo; a step of Edit Mesh.
- Works on components.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Keep group | off | yes | On: keep only the group. Off: delete it. |

##### Clean

Remove points no face uses.

- Node `Clean` in Geo; a step of Edit Mesh.
- Works on components, or everything when nothing is selected.

##### Dissolve

Join the faces across the group's interior edges (or around its points), one face per region.

- Node `Dissolve` in Geo; a step of Edit Mesh.
- Works on points or edges or faces.

#### Split

##### Split

Detach the group's faces: they get their own points.

- Node `Split` in Geo; a step of Edit Mesh.
- Works on faces.

#### Sweep

##### PolyMirror

Reflect the group's faces across a plane, joined along it.

- Node `PolyMirror` in Geo; a step of Edit Mesh.
- Works on objects or faces.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Axis | X | yes | The axis the mirror plane faces. |
| Offset | 0.0 | yes | Where the plane crosses its axis. |
| Through centroid | off | yes | Put the plane through the group's centroid (Offset then moves it from there). |
| Keep original | on | yes | Keep the group beside its reflection. |
| Weld | on | yes | Join the reflection to the original at points on the plane. |

##### Spin

Sweep the group's edges around an axis into a surface of revolution.

- Node `Spin` in Geo; a step of Edit Mesh.
- Works on edges.
- After it runs, a drag in the viewport sets Angle (turned about the selection's center); a click keeps it, the wheel steps Steps.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Axis | Y | yes | The axis the profile turns about. |
| Center | 0.0, 0.0, 0.0 | yes | A point on the axis. |
| Angle | 360.0 | yes | How far the profile turns, in degrees; 360 closes it. |
| Steps | 12 | yes | Copies of the profile along the turn. |

#### Subdivide

##### Triangulate

Split the group's faces into their triangles.

- Node `Triangulate` in Geo; a step of Edit Mesh.
- Works on objects or faces.

##### Subdivide

Split faces into quads, optionally with Catmull-Clark smoothing.

- Node `Subdivide` in Geo; a step of Edit Mesh.
- Works on objects or faces, or everything when nothing is selected.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Levels | 1 | yes | Each level splits every face into quads. |
| Method | Catmull-Clark | yes | Catmull-Clark smooths as it splits; Linear keeps the shape. |

##### Crease

Set the crease sharpness of the group's edges for subdivision.

- Node `Crease` in Geo; a step of Edit Mesh.
- Works on edges.
- After it runs, a drag in the viewport sets Sharpness (rightward, its range over 300 points); a click keeps it.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Sharpness | 10.0 | yes | USD crease sharpness: 0 smooth, 10 infinitely sharp; s stays sharp for s levels. |
| Mode | Set | yes | Give the group's edges this sharpness, or make them smooth. |

#### Shape

##### Smooth

Laplacian relaxation of the group's points.

- Node `Smooth` in Geo; a step of Edit Mesh.
- Works on components.
- After it runs, a drag in the viewport sets Amount (rightward, its range over 300 points); a click keeps it, the wheel steps Iterations.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Amount | 0.5 | yes | How far each point moves toward the average of its neighbors. |
| Iterations | 1 | yes | Rounds of smoothing. |

##### Noise

Deterministic noise displacement.

- Node `Mountain` in Geo; a step of Edit Mesh.
- Works on components.
- After it runs, a drag in the viewport sets Height (hauled away from the selection's center); a click keeps it.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Height | 0.2 | yes | Largest displacement of the noise. |
| Seed | 0 | yes | Another seed gives other noise. |

##### Peak

Move points along their normals.

- Node `Peak` in Geo; a step of Edit Mesh.
- Works on components.
- After it runs, a drag in the viewport sets Distance (along the selection's average normal); a click keeps it.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Distance | 0.2 | yes | Distance along the averaged normals. |

##### Flatten

Flatten the group onto a plane through its centroid.

- Node `Flatten` in Geo; a step of Edit Mesh.
- Works on components.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Axis | Y | yes | The axis flattened to the group's centroid. |

##### Snap

Snap points to a grid.

- Node `Snap` in Geo; a step of Edit Mesh.
- Works on components.
- After it runs, a drag in the viewport sets Spacing (hauled away from the selection's center); a click keeps it.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Spacing | 0.1 | yes | Grid spacing points snap to. |

#### Normals

##### Reverse

Flip the winding of the group's faces.

- Node `Reverse` in Geo; a step of Edit Mesh.
- Works on objects or faces.

### Select

A Select tool changes the selection only: from D, the right-click Select submenu or Modify ›
Selection it runs on what is selected (a tool that looks at everything runs on everything when
nothing is), its rows stay on the tool bar while its selection does, and a change runs it again.
As a node it is a Select node whose output selection the viewport adopts. Its group function is
the same rule in a node's Group, run on every cook: `sharp(*, 30)`, `loop(p6-7)`.

Click gestures on a mesh's components:

| Gesture | Edge | Face or point |
| --- | --- | --- |
| Double-click | Its loop; again on a boundary edge, the whole boundary | Its island |
| Shift + double-click | Add the loop; on the loop of the edge picked last, only the run between | Add the island; beside the face picked last, the face loop through both |
| Cmd/Ctrl + double-click | Add its ring | Remove the island |
| Shift + Cmd/Ctrl + double-click | Remove the loop | Remove the island |
| Shift + Cmd/Ctrl + click | The shortest path from the element picked last, added | The same |

Hovering an edge shows the loop a double-click would take (its ring with Cmd/Ctrl held).

#### Loops

##### Loop

Edge loops through the selected edges, face loops through faces side by side, point loops through points along an edge.

- Node `Select Loop` in Geo; a step of Edit Mesh.
- Works on edges or faces or points.
- With nothing selected: "Select edges, two faces side by side, or two points on a loop".
- Group function: `loop(group, only_between)`.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Only between | off | yes | With two edges on one loop selected: only the run between them, the shorter way round. |

##### Ring

Edge rings through the selected edges: across each quad to its opposite edge.

- Node `Select Ring` in Geo; a step of Edit Mesh.
- Works on edges.
- With nothing selected: "Select edges for Ring".
- Group function: `ring(group)`.

##### Boundary Loop

Each selected boundary edge's whole boundary; selected faces' outline as edges.

- Node `Select Boundary Loop` in Geo; a step of Edit Mesh.
- Works on edges or faces.
- With nothing selected: "Select boundary edges, or faces for their outline".
- Group function: `boundary(group)`.

##### Loop to Region

The faces a closed loop of selected edges encloses (its smaller side, or bigger).

- Node `Select Loop to Region` in Geo; a step of Edit Mesh.
- Works on edges.
- With nothing selected: "Select a closed edge loop".
- Group function: `region(group, side)`.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Side | Smaller | yes | Which side of each closed loop: the one with fewer faces, or more. |

#### Region

##### Grow Selection

The selection and its neighbors, a ring at a time.

- Node `Select Grow` in Geo; a step of Edit Mesh.
- Works on points or edges or faces.
- Group function: `grow(group, steps, face_step)`.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Steps | 1 | yes | How many rings of neighbors to add or take away. |
| Face step | off | yes | Faces reach faces that share a point, points and edges reach across faces; off: faces across edges, points and edges along edges. |

##### Shrink Selection

The selection without its outer ring, a ring at a time.

- Node `Select Shrink` in Geo; a step of Edit Mesh.
- Works on points or edges or faces.
- Group function: `shrink(group, steps, face_step)`.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Steps | 1 | yes | How many rings of neighbors to add or take away. |
| Face step | off | yes | Faces reach faces that share a point, points and edges reach across faces; off: faces across edges, points and edges along edges. |

##### Border

The selected elements next to an unselected one.

- Node `Select Border` in Geo; a step of Edit Mesh.
- Works on points or edges or faces.
- Group function: `border(group)`.

##### Connected

Whole islands touching the selection, optionally kept inside seams, sharp edges, materials, UV islands or face angles.

- Node `Select Connected` in Geo; a step of Edit Mesh.
- Works on points or edges or faces.
- Group function: `connected(group, seams, sharp, materials, uv_seams, normals, angle)`.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Seams | off | yes | Stop at seam edges (the edge group or attribute `seam`). |
| Sharp | off | yes | Stop at edges marked sharp (the edge group or attribute `sharp`). |
| Materials | off | yes | Stop between faces of different materials (the face attribute `material`). |
| UV seams | off | yes | Stop where the faces' `uv` values part along an edge. |
| Normals | off | yes | Stop at edges whose faces meet at more than Angle. |
| Angle | 30.0 | yes | The face angle Normals stops at, in degrees. |

##### Linked Flat

Faces reached from the selection across edges flatter than an angle.

- Node `Select Linked Flat` in Geo; a step of Edit Mesh.
- Works on faces.
- Group function: `flat(group, angle)`.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Angle | 1.0 | yes | The largest angle between two faces still counted flat, in degrees. |

##### Shortest Path

The shortest path between the selected elements, taken in order; with Fill region every element on a shortest path.

- Node `Select Shortest Path` in Geo; a step of Edit Mesh.
- Works on points or edges or faces.
- With nothing selected: "Select two components to join".
- Group function: `path(group, distance, fill_region, face_step)`.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Distance | Length | yes | What a path measures: its length, or its steps. |
| Fill region | off | yes | Every element on any shortest path in steps between the two, not one path. |
| Face step | off | yes | Points and faces step across faces (diagonals), edges around their faces. |

#### Similar

##### Similar

Every element like a selected one by normal, area, perimeter, sides, plane, material, group, length, direction, face angle, crease, seam, sharpness or valence.

- Node `Select Similar` in Geo; a step of Edit Mesh.
- Works on points or edges or faces.
- Group function: `similar(group, by, compare, threshold)`.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| By | Normal | yes | What is compared. Faces: Normal, Area, Perimeter, Sides, Coplanar, Material, Group. Edges: Length, Direction, Face angle, Crease, Seam, Sharp, Faces, Group. Points: Normal, Edges, Faces, Group. |
| Compare | Equal | yes | Equal within the threshold, or at least, or at most, a selected element's value. |
| Threshold | 0.01 | yes | How far apart values still count as equal: in the value's units, degrees for Normal, Direction and Face angle. |

#### Find

##### Sharp Edges

Edges whose faces meet at more than an angle.

- Node `Select Sharp Edges` in Geo; a step of Edit Mesh.
- Works on edges, or everything when nothing is selected.
- Group function: `sharp(group, angle)`.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Angle | 30.0 | yes | Edges whose two faces meet at more than this, in degrees. |

##### By Sides

Faces by their number of sides: triangles, quads, n-gons.

- Node `Select By Sides` in Geo; a step of Edit Mesh.
- Works on faces, or everything when nothing is selected.
- Group function: `sides(group, sides, compare)`.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Sides | 4 | yes | The number of sides compared with. |
| Compare | Equal | yes | How a face's sides compare with Sides. |

##### By Area

Faces smaller or larger than an area.

- Node `Select By Area` in Geo; a step of Edit Mesh.
- Works on faces, or everything when nothing is selected.
- Group function: `area(group, area, compare)`.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Area | 0.01 | yes | The area compared with, in square units. |
| Compare | Less | yes | Faces smaller than Area, or larger. |

##### By Normal

Faces facing a direction within a spread.

- Node `Select By Normal` in Geo; a step of Edit Mesh.
- Works on faces, or everything when nothing is selected.
- Group function: `facing(group, direction_x, direction_y, direction_z, spread)`.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Direction | 0.0, 0.0, 0.0 | yes | The direction faces should face (a zero vector takes +Y). |
| Spread | 30.0 | yes | How far a face's normal may lean from Direction, in degrees. |

##### Non-manifold

Boundary edges, edges of three faces or more, flipped neighbors and pinched points.

- Node `Select Non-manifold` in Geo; a step of Edit Mesh.
- Works on edges or points, or everything when nothing is selected.
- Group function: `nonmanifold(group, boundary, multiple_faces, non_contiguous, pinched_points)`.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Boundary | on | yes | Edges with one face. |
| Multiple faces | on | yes | Edges with three faces or more (a T-junction). |
| Non contiguous | on | yes | Edges whose two faces wind opposite ways (a flipped neighbor). |
| Pinched points | on | yes | Points where faces meet only at the point (at the Points level). |

##### Loose

Points no face uses.

- Node `Select Loose` in Geo; a step of Edit Mesh.
- Works on points, or everything when nothing is selected.
- Group function: `loose(group)`.

##### Interior Faces

Faces all of whose edges have more than two faces (walls inside a solid).

- Node `Select Interior Faces` in Geo; a step of Edit Mesh.
- Works on faces, or everything when nothing is selected.
- Group function: `interior(group)`.

#### Pattern

##### Checker

Keep a checker pattern of the group: runs of selected and deselected elements across each island.

- Node `Select Checker` in Geo; a step of Edit Mesh.
- Works on points or edges or faces.
- With nothing selected: "Select the region to thin out".
- Group function: `checker(group, selected, deselected, offset)`.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Selected | 1 | yes | Elements kept selected in a row. |
| Deselected | 1 | yes | Elements deselected in a row, after each selected run. |
| Offset | 0 | yes | Shift the pattern along by this many elements. |

##### Random

A random share of the group: each element kept with the Ratio's chance, the same for the same seed.

- Node `Select Random` in Geo; a step of Edit Mesh.
- Works on points or edges or faces.
- With nothing selected: "Select the region to thin out".
- Group function: `random(group, ratio, seed)`.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Ratio | 0.5 | yes | The share of the group kept selected. |
| Seed | 0 | yes | Another seed, another pattern. |

#### Symmetry

##### Mirror Selection

The selection's mirror across X, Y or Z (elements with nothing at their mirror drop out).

- Node `Select Mirror` in Geo; a step of Edit Mesh.
- Works on points or edges or faces.
- Group function: `mirror(group, axis, extend)`.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Axis | X | yes | The plane through the origin the selection is mirrored across. |
| Extend | off | yes | Keep the selection and add its mirror; off: only the mirror. |

#### Convert

##### Convert

The selection as points, edges or faces: those it touches, or only those it contains (Maya's Convert Selection).

- Node `Select Convert` in Geo; a step of Edit Mesh.
- Works on points or edges or faces.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| To | Faces | yes | The component type the selection becomes. |
| Rule | Touching | yes | Touching: every element the selection touches. Contained: only those all of whose points, edges or faces are selected. |

## CAD

Edit CAD's steps and the CAD context's nodes. A node keeps what it picks by name (faces, edges by
the faces they lie between, curves), so it holds as the chain upstream changes; a step keeps the
selection it ran on.

### Create

#### Sketch

##### Sketch

Curves on a plane or a flat face, constrained and dimensioned.

- Node `Sketch` in CAD.
- Works on faces.
- With nothing selected: "Click the flat face to sketch on; Esc cancels".
- Gesture: sketch.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Plane | XZ | yes | The plane the sketch is drawn on: XY (front), XZ (the ground), YZ (side), or a flat face of the input body (Pick face). |
| Offset | 0.0 | yes | How far the plane is moved along its normal. |

##### Redefine Sketch Plane

Put a sketch onto another flat face or an origin plane.

- A step of Edit CAD.
- Works on faces.
- With nothing selected: "Click the flat face to put the sketch on (or choose an origin plane in the tool bar, then Enter); Esc cancels".
- Gesture: sketch.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Plane | XZ | yes | The plane the sketch is drawn on: XY (front), XZ (the ground), YZ (side), or a flat face of the input body (Pick face). |
| Offset | 0.0 | yes | How far the plane is moved along its normal. |

#### Features

##### Extrude

Sweep a sketch's profiles or a face along the sketch plane's normal into a body, joined, cut or intersected by Auto.

- Node `Extrude` in CAD; a step of Edit CAD.
- Works on curves.
- Also picks object: The face the extrusion runs to (To object), kept by its name so it stays that face as the body changes.
- Also picks side 2 object: The face the second side runs to (To object).
- Also picks start object: The face the extrusion starts from (Start: Object), kept by its name.
- Also picks objects to cut: The bodies Join, Cut and Intersect act on, kept by their faces' names. Auto-select: every body, as it is when the node cooks.
- Gesture: profiles.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Type | Extrude | yes | Extrude: the whole area inside the profiles. Thin extrude: a wall along the profiles' curves (open ones too), Wall thickness wide. |
| Start | Profile plane | yes | Where the extrusion starts: on the sketch's plane; that plane moved Start offset along its normal; or a face of the body (Pick start object), Start offset further on. |
| Start offset | 0.0 | yes | Offset: how far along the normal the extrusion starts (negative: the other way). Object: how far past the face. |
| Direction | One side | yes | One side: along the normal (a negative distance goes the other way). Two sides: an extent and taper each way. Symmetric: the same each way. |
| Measurement | Half length | yes | Symmetric: Half length extrudes the distance to each side, Whole length half of it to each side. |
| Extent | Distance | yes | Distance: as far as Distance says. To object: until the face picked (Pick object), Offset further. All: through the whole body. |
| Distance | 10.0 | yes | How far the profiles sweep along the sketch plane's normal; negative goes the other way. |
| Extend | To selected face | yes | To object, as Fusion's: To selected face, its surface extended past the face; To adjacent faces, the face and the faces next to it; To body, the body the face is on; Through body, out of its far side. |
| Offset | 0.0 | yes | To object: how far past the face the extrusion stops (negative: short of it). |
| Flip | off | yes | All, one side: through the body against the normal instead. |
| Taper angle | 0.0 | yes | Leans the sides: positive out, the profile growing along the extrusion; negative in. Fusion's sign. |
| Side 2 extent | Distance | yes | Two sides: the second side's extent, against the normal. |
| Side 2 distance | 10.0 | yes | Two sides: how far the second side goes against the normal. |
| Side 2 extend | To selected face | yes | To object, second side: as Extend. |
| Side 2 offset | 0.0 | yes | To object, second side: how far past its face it stops. |
| Side 2 taper | 0.0 | yes | Two sides: the second side's taper, positive out. |
| Wall thickness | 1.0 | yes | Thin extrude: how thick the wall is. |
| Wall location | Side 1 | yes | Thin extrude: Side 1 inside a closed profile (left of an open curve as it was drawn), Side 2 outside it (right), Center half each way. |
| Operation | Auto | yes | Auto: cuts where it goes into the body, else joins it (a new body without one), as Fusion does. Join, Cut, Intersect: combined with the body flowing down the chain, or the second input's when one is wired. |

##### Revolve

Turn a sketch's profiles about an axis into a body, joined, cut or intersected by Auto.

- Node `Revolve` in CAD; a step of Edit CAD.
- Works on curves.
- Also picks object: The face the revolve turns to (Type: To), kept by its name.
- Also picks axis: The sketch line or body edge the profiles turn about (projected onto the sketch's plane).
- Gesture: profiles.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Axis | Picked | yes | Picked: the sketch line or body edge picked (Pick axis), projected onto the sketch's plane. X, Y, Z: an origin axis. |
| Type | Angle | yes | Angle: as far as Angle says. Full: all the way round. To: until the face picked (Pick object), its surface extended past it. |
| Direction | One side | yes | One side: from the sketch's plane toward its normal (a negative angle the other way). Two sides: an angle each way. Symmetric: Angle each way. |
| Angle | 360.0 | yes | How far the profiles turn about the axis. |
| Side 2 angle | 90.0 | yes | Two sides: how far the second side turns, the other way. |
| Flip | off | yes | To: turn against the sketch plane's normal instead. |
| Operation | Auto | yes | Auto: cuts where it turns into the body, else joins it (a new body without one). Join, Cut, Intersect: combined with the body flowing down the chain, or the second input's when one is wired. |

#### Solids

##### Solid Box

A box centered on the origin.

- Node `Solid Box` in CAD.
- Works on components.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Size | 20.0, 20.0, 20.0 | yes | Width (X), height (Y) and depth (Z), centered on the origin. |

##### Solid Cylinder

A cylinder along +Y, centered on the origin.

- Node `Solid Cylinder` in CAD.
- Works on components.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Radius | 10.0 | yes | The base's radius. |
| Height | 20.0 | yes | Along +Y, centered on the origin. |

##### Solid Cone

A cone or frustum along +Y, centered on the origin.

- Node `Solid Cone` in CAD.
- Works on components.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Radius | 10.0 | yes | The base's radius. |
| Height | 20.0 | yes | Along +Y, centered on the origin. |
| Top radius | 0.0 | yes | 0 is a pointed cone; otherwise a frustum. |

##### Solid Sphere

A sphere centered on the origin.

- Node `Solid Sphere` in CAD.
- Works on components.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Radius | 10.0 | yes | Centered on the origin. |

##### Solid Torus

A torus about +Y, centered on the origin.

- Node `Solid Torus` in CAD.
- Works on components.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Radius | 10.0 | yes | The ring's radius, about +Y. |
| Tube | 2.5 | yes | The tube's radius; less than the ring's. |

#### Curves

##### Curve

A free curve: through points, by control points, from an edge, an isoparm, or on a face.

- Node `Curve` in CAD.
- Works on edges.
- Also picks face: Isoparm and On face: the face, kept by its name.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Type | Through points | yes | How the curve is made: through points (Alias's EP curve), with points as its control points (CV curve), from a body's edge or a face's isoparm (Duplicate Curve), or on a face. |
| Degree | 5 | yes | The curve's degree (lowered to what its points allow). |
| Direction | U | yes | Isoparm: along v at a u (U), or along u at a v (V). |
| Parameter | 0.5 | yes | Isoparm: where along the face's surface, 0 to 1. |

##### CV Curve

A curve through clicked control points, degree 5 by default.

- A step of Edit CAD.
- Works on curves.
- Gesture: clicks place its corners when nothing is selected; Enter finishes.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Degree | 5 | yes | The curve's degree (lowered to what its points allow): 5 by default, Alias's 3 or 7 on request. |

##### EP Curve

A curve passing through clicked points, degree 5 by default.

- A step of Edit CAD.
- Works on curves.
- Gesture: clicks place its corners when nothing is selected; Enter finishes.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Degree | 5 | yes | The curve's degree (lowered to what its points allow): 5 by default, Alias's 3 or 7 on request. |

##### Curve on Surface

A curve lying on a face, through points clicked on it.

- A step of Edit CAD.
- Works on curves.
- Gesture: clicks place its corners when nothing is selected; Enter finishes.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Degree | 5 | yes | The curve's degree (lowered to what its points allow): 5 by default, Alias's 3 or 7 on request. |

##### Isoparm

The isoparm through a point double-clicked on a surface, as a curve.

- A step of Edit CAD.
- Works on curves.
- Gesture: isoparm.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Direction | U | yes | The isoparm along v through the point clicked (U), or along u (V). |
| Point | 0.0, 0.0, 0.0 | yes | Where the surface was clicked. |

### Modify

#### Blends

##### Fillet

Round edges with a rolling ball: constant, chord length or variable radius, G1 to G3, rule fillets, full rounds and selection sets.

- Node `Fillet` in CAD; a step of Edit CAD.
- Works on edges.
- Also picks center face: Full round: the face rounded away, kept by its name; the faces on each side are found across its longest parallel edges.
- Also picks faces: Rule fillet, Between faces: the first set of faces, kept by their names.
- Also picks other faces: Rule fillet, Between faces: the second set (none: any face next to the first set).
- Also picks set 2 edges: Selection set 2's edges, filleted at Set 2 radius (with Variable radius, set 2: the constant edges the law runs into).
- Also picks set 3 edges: Selection set 3's edges, filleted at Set 3 radius (with Variable radius, set 2: the constant edges the law runs into).
- Also picks set 4 edges: Selection set 4's edges, filleted at Set 4 radius (with Variable radius, set 2: the constant edges the law runs into).
- Also picks set 5 edges: Selection set 5's edges, filleted at Set 5 radius (with Variable radius, set 2: the constant edges the law runs into).
- Also picks set 6 edges: Selection set 6's edges, filleted at Set 6 radius (with Variable radius, set 2: the constant edges the law runs into).
- Also picks set 7 edges: Selection set 7's edges, filleted at Set 7 radius (with Variable radius, set 2: the constant edges the law runs into).
- Also picks set 8 edges: Selection set 8's edges, filleted at Set 8 radius (with Variable radius, set 2: the constant edges the law runs into).
- Also picks set 9 edges: Selection set 9's edges, filleted at Set 9 radius (with Variable radius, set 2: the constant edges the law runs into).
- After it runs, a drag in the viewport sets Radius (hauled away from the selection's center); a click keeps it.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Type | Fillet | no | Fillet: the edges picked. Rule fillet: the edges a rule takes (All edges, or Between faces), found again as the body changes. Full round: a center face (Pick center face) rounded away whole, tangent to it and to the faces on each side. |
| Rule | All edges | no | All edges: every edge of the kinds below. Between faces: those between the faces picked (Pick faces) and, when picked, the other faces (Pick other faces). |
| Rounds | on | no | Rule fillet: outside edges (convex), material taken away. |
| Fillets | on | no | Rule fillet: inside edges (concave), material added. |
| Radius type | Constant | no | Constant: the fillet's radius. Chord length: the distance between where the fillet leaves the two faces. Variable: Radius at the start of the edge (or its tangent chain), End radius at its end and points between, G1, G2 or G3. |
| Radius | 1.0 | yes | The rolling ball's radius. |
| Chord length | 1.0 | no | Chord length: how far apart the fillet's edges on the two faces are. |
| End radius | 2.0 | no | Variable: the radius at the end of the edge or chain (Radius is at its start). |
| Smooth transition | off | no | Variable: the radius held a moment at each point and eased between them; off (Fusion's): straight between two radii, a smooth spline through more. |
| Selection sets | 1 | yes | Fusion's selection sets: the edges picked are set 1 at Radius; sets 2 and on each take their own edges (Pick set 2 edges…) and radius, meeting at setback corners where radii differ. With Variable radius, set 2 is the constant edges the law runs into at corners (a straight law runs in as Fusion's, a cone; any other must end at their radius). |
| Set 2 radius | 2.0 | yes | Selection set 2's radius. |
| Set 3 radius | 2.0 | yes | Selection set 3's radius. |
| Set 4 radius | 2.0 | yes | Selection set 4's radius. |
| Set 5 radius | 2.0 | yes | Selection set 5's radius. |
| Set 6 radius | 2.0 | yes | Selection set 6's radius. |
| Set 7 radius | 2.0 | yes | Selection set 7's radius. |
| Set 8 radius | 2.0 | yes | Selection set 8's radius. |
| Set 9 radius | 2.0 | yes | Selection set 9's radius. |
| Tangent chain | on | yes | Each picked edge brings the edges continuing it smoothly: a rounded slot's rim, the edges around an earlier fillet. |
| Continuity | G1 | yes | G1: a circular fillet (Fusion's Tangent). G2: curvature flows into the faces (Fusion's Curvature; no jump in reflections). G3: its change too, smoother still. Where three meet at a corner they stop short of it, and a patch as smooth as they are rounds it. |
| Tangency weight | 1.0 | yes | How far the continuity reaches into the fillet (Fusion's Tangency weight): 1 the plain fillet; more hugs the faces longer and turns tighter in the middle, less is flatter. A G1 fillet with a weight is a conic, its corners setbacks. |
| Conic | Off | yes | G1 (Parasolid's conic section): Rho, the conic's own (0.5 a parabola, less an ellipse, more a hyperbola); Rho relative, against the circle's (0.5 the circle); Middle radius, the radius of curvature at the section's middle as a share of the fillet's radius (1 the circle). |
| Rho | 0.5 | yes | The conic's rho (0 to 1), or Middle radius's share of the radius. |
| G2 shape | Fusion | yes | G2 (Parasolid's G2 section): Fusion's own; by Depth (0 at the chord between the contacts to 1 at the faces' corner) and Skew (0 toward the first face to 1 toward the second, 0.5 even); or by Softness (more is flatter and deeper, less like a chamfer with rounded edges). |
| Depth | 0.5 | yes | How far the section's middle lies from the chord toward the corner. |
| Skew | 0.5 | yes | Where the section leans: toward the first face below 0.5, the second above. |
| Softness | 0.5 | yes | The section's arms along the faces: more is flatter and deeper. |
| Corner type | Rolling ball | no | Where three fillets meet at a corner: Rolling ball, a ball rounds it (G2 and G3: they stop where the ball's would and a three-sided patch joins their ends; where inside and outside fillets meet, the pair's section rolls round the lone one), Fusion's; Setback, the fillets stop short of the corner (2 radii, Fusion's) and a patch blends them into the faces, a vertex blend where both kinds meet. |
| More options | off | yes | Show the rows that bound the fillet: Limits along its edge, a corner's Setback and shape, and what it does when it runs off its faces (Overflow: Smooth, Cliff, Notch). |
| Limits | off | yes | Parasolid's limits: the fillet runs only from Limit from to Limit to along its one straight edge (fractions of its length), capped by planes square to the edge. |
| Limit from | 0.0 | yes | Where along the edge the fillet starts (0 its start). |
| Limit to | 1.0 | yes | Where along the edge the fillet ends (1 its end). |
| At overlap | off | yes | Parasolid's overlap limit: within Limit from and Limit to, the fillet runs only along the longest stretch where it fits its faces, capped square there, rather than overflowing. |
| Setback | 0.0 | yes | Parasolid's setbacks: where fillets meet at a Setback corner, each stops at least this many radii from it, the corner's patch filling the gap; 0 as far as the corner needs (Fusion's). |
| Corner edge shape | 0.5 | yes | Alias's Corner Blend Edge Shape: a G1 Setback corner's curves on the faces, as conics (0.5 the circle, Fusion's; more runs nearer the faces' corner, keeping more of it; less is flatter). |
| Corner fullness | 0.0 | yes | Alias's Pivot Curve Length Ratio: a Setback or G2 corner's patch bulges this much from its edges against the fairest fill (1); 0, the default, as Fusion's corners (Setback 1.27 at G1 and 1.1 at G2 and G3, three-sided 1.143). |
| Overflow | on | yes | Parasolid's overflow: a fillet running off its face does what Smooth, Cliff and Notch allow, tried in that order; off, it must fit its faces. |
| Smooth | on | yes | Overflow: the ball rolls on over a line splitting the face, or onto a round tangent to it beyond. |
| Cliff | on | yes | Overflow: a cliff-edge blend, tangent to the other face and running along the edge where the face ends (G1). |
| Notch | on | yes | Overflow: the fillet unchanged, the next face trimming it, or a ledge's plane covering its end. |

##### Chamfer

Cut edges flat: an equal distance, two distances, or a distance and an angle.

- Node `Chamfer` in CAD; a step of Edit CAD.
- Works on edges.
- After it runs, a drag in the viewport sets Distance (hauled away from the selection's center); a click keeps it.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Type | Equal distance | yes | Equal distance: as far along each face. Two distances: Distance along the first face (the one more of the picked edges lie on), Distance 2 along the other. Distance and angle: Distance along the first face, leaving it at Angle. |
| Distance | 1.0 | yes | How far the chamfer reaches along each face. |
| Distance 2 | 1.0 | yes | Two distances: how far the chamfer reaches along the other face. |
| Angle | 45.0 | yes | Distance and angle: the angle the chamfer leaves the first face at. |
| Flip | off | yes | Measure the first distance on the other face. |
| Corner type | Chamfer | yes | Where three chamfers meet at a corner: Chamfer joins them with a flat face; Miter runs them on to a point; Blend sets them back and closes the corner with one flat face, as Fusion's. |
| Tangent chain | on | yes | Each picked edge brings the edges continuing it smoothly: a rounded slot's rim, the edges around an earlier fillet. |

##### Reblend

Give fillet faces another radius.

- A step of Edit CAD.
- Works on faces or patches.
- Gesture: reblend.
- After it runs, a drag in the viewport sets Radius (hauled away from the selection's center); a click keeps it.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Radius | 1.0 | yes | The blends' new radius: they are deleted, the faces healed, and filleted again; blends meeting them keep their own. |

#### Faces

##### Offset Face

Move faces along their normals, tangent faces following.

- Node `Offset Face` in CAD; a step of Edit CAD.
- Works on faces or patches.
- After it runs, a drag in the viewport sets Distance (hauled away from the selection's center); a click keeps it.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Distance | 1.0 | yes | How far the faces move along their outward normals (negative: in); the faces around stretch or shrink to meet them, tangent ones following. |

##### Shell

Hollow a body to a wall Inside, Outside or Both, the faces picked opened.

- Node `Shell` in CAD; a step of Edit CAD.
- Works on objects or faces or patches.
- Also picks bodies: Bodies hollowed closed, with nothing opened.
- After it runs, a drag in the viewport sets Inside thickness (hauled away from the selection's center); a click keeps it.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Tangent chain | on | yes | Each face removed brings the faces meeting it smoothly: a rounded rim opens whole. |
| Inside thickness | 1.0 | yes | The wall's thickness inside the body's faces. |
| Outside thickness | 1.0 | yes | The wall's thickness outside the body's faces. |
| Direction | Inside | yes | Inside: the wall inside the body's faces. Outside: outside them. Both: Inside thickness in, Outside thickness out. |

##### Split Face

Split faces where a face's surface or an origin plane crosses them.

- Node `Split Face` in CAD; a step of Edit CAD.
- Works on faces or patches.
- Also picks splitting face: The face whose surface, extended, splits them.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Splitting tool | Picked face | yes | The face picked (its surface extended), or an origin plane. |
| Extend splitting tool | on | yes | On: the picked face's surface, extended past the face, splits the faces. Off: the face cuts only where it reaches, and must cut right across each face it meets. |
| Offset | 0.0 | yes | An origin plane moved along its normal. |

##### Replace Face

Move faces onto the surface of target faces.

- Node `Replace Face` in CAD; a step of Edit CAD.
- Works on faces or patches.
- Also picks target faces: The faces (one surface, or a solid's faces) the faces are moved onto.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Tangent chain | on | yes | Each face replaced brings the faces meeting it smoothly. |

##### Delete

Delete faces and heal the body over them; a whole body picked goes.

- Node `Delete Face` in CAD; a step of Edit CAD (`Delete`).
- Works on objects or faces or patches.

##### Remove Faces

Take faces away and leave the model open.

- A step of Edit CAD.
- Works on faces or patches.

#### Bodies

##### Move/Copy

Move or copy bodies, or faces with the faces around following: free, along a direction, turned, or point to point.

- Node `Move` in CAD; a step of Edit CAD (`Transform Components`).
- Works on objects or faces or patches.
- Also picks rotate axis: Rotate: the edge whose line it turns about.
- Also picks from point: The point that moves: a corner or an edge's end, a round edge's middle.
- Also picks to point: Point to point: where it goes.
- Also picks pivot: Set pivot: the point Free move and Rotate turn about.
- Gesture: move.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Move object | Bodies | no | Bodies: whole bodies move. Faces: the faces move, the faces round them following. |
| Move type | Free move | yes | Free move: the gizmo's moves and turns. Translate: along X, Y and Z. Rotate: an angle about an axis. Point to point: from a picked point to another. Point to position: from a picked point to the coordinates typed. |
| Translate | 0.0, 0.0, 0.0 | yes | How far along X, Y and Z. |
| Rotate | 0.0, 0.0, 0.0 | yes | Free move: the turn about X, then Y, then Z, in degrees, about the pivot. |
| Axis | Y axis | yes | Rotate: about the X, Y or Z axis through the pivot, or the line of an edge picked (Pick axis). |
| Angle | 0.0 | yes | Rotate: how far it turns. |
| Pivot | Selection middle | yes | What Free move and Rotate turn about: the middle of what moves, the origin, or a point (Set pivot picks one). |
| Pivot point | 0.0, 0.0, 0.0 | yes | The point turned about. |
| From point | 0.0, 0.0, 0.0 | yes | The point that moves (Pick from point: a corner or an edge's end; a round edge's middle). |
| To point | 0.0, 0.0, 0.0 | yes | Point to point: where it goes (Pick to point). Point to position: the coordinates it goes to. |
| Create copy | off | yes | Leave what is picked where it is and move a copy: of a body, or of faces as a surface body. |

##### Combine

Join tool bodies to a target body, cut them from it, or keep what they share.

- Node `Combine` in CAD; a step of Edit CAD.
- Works on objects.
- Also picks tool bodies: The bodies joined to, cut from or intersected with the target (the second input's bodies are tools too).

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Operation | Join | yes | Join: the tool bodies added to the target. Cut: taken out of it. Intersect: only what the target shares with them. |
| Keep tools | off | yes | Keep the tool bodies after combining. |

##### Split Body

Split bodies by a face's surface or an origin plane, each piece a body.

- Node `Split Body` in CAD; a step of Edit CAD.
- Works on objects.
- Also picks splitting face: The face whose surface, extended, splits the bodies.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Splitting tool | Picked face | yes | The face picked (its surface extended), or an origin plane. |
| Extend splitting tool | on | yes | On: the picked face's surface, extended past the face, splits the body. Off: the face cuts only where it reaches, and must cut a piece off. |
| Offset | 0.0 | yes | An origin plane moved along its normal. |

##### Remove

Take whole bodies away.

- Node `Remove` in CAD; a step of Edit CAD.
- Works on objects.

##### Mirror Body

Reflect the bodies across an origin plane, joined or apart.

- Node `Mirror Body` in CAD.
- Works on components.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Plane | YZ (across X) | yes | The plane through the origin the body is mirrored across. |
| Separate bodies | off | yes | Keep the mirror image a body of its own instead of joining it. |

##### Pattern

Copy the bodies along an axis or around it.

- Node `Pattern` in CAD.
- Works on components.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Type | Linear | yes | Linear: copies along an axis, Spacing apart. Circular: copies around an axis through the origin, over Angle. |
| Count | 3 | yes | How many bodies, the original among them. |
| Axis | X | yes | The axis the copies go along or around. |
| Spacing | 20.0 | yes | Linear: the distance between copies. |
| Angle | 360.0 | yes | Circular: the angle the copies spread over (360: evenly around). |
| Separate bodies | off | yes | Keep the copies bodies of their own instead of joining them. |

##### Scale Body

Scale bodies by one factor, about the origin or about each body's middle.

- Node `Scale Body` in CAD; a step of Edit CAD.
- Works on objects.
- After it runs, a drag in the viewport sets Scale (hauled away from the selection's center); a click keeps it.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Scale | 2.0 | yes | How much larger the bodies become (less than 1: smaller). |
| About | Origin | yes | Origin: every body scaled about the origin. Body middle: each about the middle of its bounds. |

#### Curves

##### Duplicate Curve

Free curves from the edges picked, or a face's isoparm.

- A step of Edit CAD.
- Works on edges or faces or patches.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Direction | U | yes | At a face: the isoparm along v at a u (U) or along u at a v. |
| Parameter | 0.5 | yes | At a face: where along it, 0 to 1. |

##### Blend Curve

A curve blending two curves or edges, G0 to G4 at each end.

- Node `Blend Curve` in CAD; a step of Edit CAD.
- Works on curves.
- Also picks from curve: The curve or edge the blend leaves, at its end nearest the other (an edge when the input has no curves).
- Also picks to curve: The curve or edge the blend meets.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Start | G2 Curvature | yes | The continuity with the first curve or edge where the blend leaves it (G4: blend curves only, as Alias and Rhino). |
| End | G2 Curvature | yes | The continuity with the second curve or edge where the blend meets it. |
| Degree | 5 | yes | The blend's degree: 5 by default on as many spans as its ends need (G1 and G2 one, G3 three, G4 five); 7 gives a single span up to G3 (Explicit Control). |
| Extra spans | 0 | yes | Spans beyond what the ends need: free control points that bend as little as they can. |
| Start tangent | 1.0 | yes | How long the blend's tangent is at its start, in chords (Alias's tangent handle; 1 is Relax, less is Tight). |
| End tangent | 1.0 | yes | How long the tangent is at its end, in chords. |
| Start curvature | 0.0 | yes | The start's curvature shape (Alias's curvature handle): how far its second control points lean along the tangent, in chords. |
| End curvature | 0.0 | yes | The end's curvature shape. |
| Start rate | 0.0 | yes | G3 at the start: the third control points' lean. |
| End rate | 0.0 | yes | G3 at the end. |
| Start G4 shape | 0.0 | yes | G4 at the start: the fourth control points' lean. |
| End G4 shape | 0.0 | yes | G4 at the end. |
| Other start end | off | yes | Leave the first curve at its other end (by default the ends nearest each other). |
| Other end end | off | yes | Meet the second curve at its other end. |

##### Blend Curve

A curve blending two edges, G0 to G4 at each end.

- A step of Edit CAD.
- Works on edges.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Start | G2 Curvature | yes | The continuity with the first curve or edge where the blend leaves it (G4: blend curves only, as Alias and Rhino). |
| End | G2 Curvature | yes | The continuity with the second curve or edge where the blend meets it. |
| Degree | 5 | yes | The blend's degree: 5 by default on as many spans as its ends need (G1 and G2 one, G3 three, G4 five); 7 gives a single span up to G3 (Explicit Control). |
| Extra spans | 0 | yes | Spans beyond what the ends need: free control points that bend as little as they can. |
| Start tangent | 1.0 | yes | How long the blend's tangent is at its start, in chords (Alias's tangent handle; 1 is Relax, less is Tight). |
| End tangent | 1.0 | yes | How long the tangent is at its end, in chords. |
| Start curvature | 0.0 | yes | The start's curvature shape (Alias's curvature handle): how far its second control points lean along the tangent, in chords. |
| End curvature | 0.0 | yes | The end's curvature shape. |
| Start rate | 0.0 | yes | G3 at the start: the third control points' lean. |
| End rate | 0.0 | yes | G3 at the end. |
| Start G4 shape | 0.0 | yes | G4 at the start: the fourth control points' lean. |
| End G4 shape | 0.0 | yes | G4 at the end. |
| Other start end | off | yes | Leave the first curve at its other end (by default the ends nearest each other). |
| Other end end | off | yes | Meet the second curve at its other end. |

##### Attach

Join two curves end to end, by a blend or a straight connection.

- A step of Edit CAD.
- Works on curves.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Method | Blend | yes | Blend moves both ends to meet at Blend Bias, continuous there; Connect keeps them and bridges a gap with a straight span. |
| Blend bias | 0.5 | yes | Blend: where the ends meet, 0 at the first curve's end, 1 at the second's start. |
| Continuity | G1 | yes | Blend: the continuity at the joint. |

##### Detach

Cut a curve in two at a parameter.

- A step of Edit CAD.
- Works on curves.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Parameter | 0.5 | yes | Where the curve is cut, 0 at its start to 1 at its end. |

##### Close

Close a curve, keeping its shape with a blend span or meeting its ends halfway.

- A step of Edit CAD.
- Works on curves.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Preserve shape | on | yes | On: a G2 blend span closes the gap and the curve keeps its shape. Off: its ends move to meet halfway (G1). |

##### Stretch

Reshape a curve by dragging handles along it.

- A step of Edit CAD.
- Works on curves.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Floating | off | yes | Off (Locked): the handles stay at their parameters. On: each finds the point of the new curve nearest it. Drag the handles in the viewport; Shift-click on the curve adds one (up to degree + 1), on a handle takes it away. |

##### Reverse

Reverse a curve's direction.

- A step of Edit CAD.
- Works on curves.

##### Delete

Delete the curves picked.

- A step of Edit CAD.
- Works on curves.

#### Surface Edit

##### Project

Cast curves onto a face along a vector, the view or its normals.

- Node `Project` in CAD; a step of Edit CAD.
- Works on curves.
- Also picks projection face: The face the curves are cast onto, kept by its name.
- Gesture: view.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Along | Vector | yes | Alias's Project options: along a vector, along the view, or along the face's normals (Rhino's Pull). |
| Vector | 0.0, -1.0, 0.0 | yes | The direction the curves are cast along (View: the view's direction when the step was made). |
| Both ways | on | yes | Cast both ways along the direction (Plasticity's Bidirectional), the nearest hit winning; off: only ahead along it. |
| Match original | off | yes | Alias's Match original: keep each curve's degree and spans; off: degree 5 on as many spans as the tolerance needs. |

##### Intersect

Curves where two faces meet, or a face and a plane.

- Node `Intersect` in CAD; a step of Edit CAD.
- Works on faces or patches.
- Also picks second face: The face it meets.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| With | Faces | yes | Intersect two faces, or a face with a plane. |
| Plane origin | 0.0, 0.0, 0.0 | yes | With a plane: a point of the plane. |
| Plane normal | 0.0, 1.0, 0.0 | yes | With a plane: its normal. |
| Curves on both | off | yes | Alias's Create curves on both surfaces: the meeting curve on the second face too. |

##### Trim

Cut a face by its curves, keeping or discarding the regions clicked, or dividing it.

- Node `Trim` in CAD; a step of Edit CAD.
- Works on faces or patches.
- Also picks cutting faces: 3D Trimming by Intersect: the faces that cut it where they meet it.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Mode | Keep | yes | Alias's Trim: keep the regions clicked (their markers), discard them, or make every region a face of its own. |
| Show intersections | on | yes | Mark where the curves cross the face's edges and each other (green) and the ends of curves that cut nothing (red), as Alias's Show Intersections. |
| Curves | On face | yes | Alias's 3D Trimming: only the curves on the face, or every curve of the model cast onto it as the trim runs (along a vector, or along its normals). |
| Cast direction | 0.0, -1.0, 0.0 | yes | 3D Trimming along a vector: the direction curves off the face are cast along. |
| Intersect faces | off | yes | 3D Trimming by Intersect: the faces picked after the first (the node's Cutting faces) cut it where they meet it. |
| Extend curves | off | yes | Carry curve ends that stop short of the face's edge on along the face, to its edge or the next curve (Alias's Extend). |

##### Untrim

Undo a face's last trim, or every one.

- Node `Untrim` in CAD; a step of Edit CAD.
- Works on faces or patches.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Stages | Last | yes | Alias's Untrim Stages: undo the last trim, or every one (a face with none goes back to its natural surface). |

##### Trim Convert

Make a trimmed face a surface of its own, untrimmed.

- Node `Trim Convert` in CAD; a step of Edit CAD.
- Works on faces or patches.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Degree U | 5 | yes | The new surface's degree across its first pair of sides. |
| Degree V | 5 | yes | Its degree across the other pair. |
| Spans U | 4 | yes | Its spans along u. |
| Spans V | 4 | yes | Its spans along v. |
| Switch U/V | off | yes | Exchange the new surface's u and v. |
| Keep originals | off | yes | Keep the trimmed face as a body of its own beside the converted one. |

##### Shrink

Cut a trimmed face's surface down to its trimmed region.

- Node `Shrink` in CAD; a step of Edit CAD.
- Works on faces or patches.

##### Stitch

Join bodies along edges that lie within a gap.

- Node `Stitch` in CAD; a step of Edit CAD.
- Works on objects.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Gap | 0.001 | yes | Edges whose ends and middles lie this close join (Alias's Stitch tolerance, 0.0001 to 1); the joined edges keep the gap as their precision. |
| Detach periodic | off | yes | Alias's Detach periodic surfaces (for export): a face wrapping round its surface split in two, each meeting its seam once. |
| Detach single-curve boundaries | off | yes | Alias's Detach single curve boundaries (for export): a loop of one closed edge split into two edges. |

##### Unstitch

Make each face of a body a body of its own.

- Node `Unstitch` in CAD; a step of Edit CAD.
- Works on objects.

#### Align

##### Align

Make a surface's edge or a curve's end meet a master G0 to G3.

- Node `Align` in CAD; a step of Edit CAD.
- Works on edges or curves.
- Also picks master: What it aligns to: an edge, a curve, a face (Project, U/V), or a double-click on a surface for an isoparm.
- Also picks second master: A second master for another side of the input (optional).
- With nothing selected: "Align: select the input first: a surface's edge (Edges level) or a curve near its end (Curves level)".

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Continuity | G1 Tangent | yes | What the input's edge meets the master with: G0 its position, G1 its tangent plane, G2 its curvature, G3 the curvature's rate. |
| Type | Edge | yes | Alias's Alignment Type: Edge (onto the master's edge or curve), Project (cast onto a face along the vector), U/V (a curve to a surface's direction), Vector (rows move only along the vector). |
| Vector | 0.0, -1.0, 0.0 | yes | Project: the direction the input's edge is cast onto the master along (zero: the master's normals). Vector: the only way the tangent and curvature rows move. |
| U/V direction | U | yes | U/V: the master surface's direction the curve's end is matched to. |
| Position influence | 0.0 | yes | 0: the input keeps its own parameterization and its CVs move least; 1: it takes the master's (its ends on the master's ends, its knots). |
| Tangent balance | off | yes | Make the rows' start and end lengths follow the master's ratio (its inner hull). |
| Tangent scale | 1.0 | yes | Alias's Starting Tangent Scale: how far behind the edge the tangent row lies, against the input's own (1; the arrows in the viewport drag it). |
| Tangent scale end | 1.0 | yes | Ending Tangent Scale. |
| Curvature scale | 1.0 | yes | Alias's Starting Curvature Scale: how far behind the tangent row the curvature row lies, against the input's own (1). |
| Curvature scale end | 1.0 | yes | Ending Curvature Scale: at the edge's end (the scale runs between). |
| G3 scale | 1.0 | yes | Alias's Starting G3 Scale: how far behind the curvature row the G3 row lies, against the input's own. |
| G3 scale end | 1.0 | yes | Ending G3 Scale. |
| AutoScale G2 | off | yes | Alias's AutoScale G2: the curvature row follows the tangent scale, keeping the rows' lengths in proportion. |
| AutoScale G3 | off | yes | AutoScale G3: the G3 row follows the tangent (and curvature) scale. |
| Extra CV rows | 0 | yes | Carry the change further into the surface over this many more rows (the continuity rows stay as set). |
| Blend factor | 0.0 | yes | Alias's Blend Factor: positive, the extra rows' change dies out faster; 0 evenly; negative, it lasts. |
| Partial | off | yes | Align only a range of the input's edge; outside it, and a span beyond, the edge stays. |
| Start | 0.0 | yes | Partial: where along the input's edge the aligned range starts. |
| End | 1.0 | yes | Partial: where it ends. |
| Modify both | off | yes | Move the master too: both to the middle of their edges and cross curves (Align 2008's Both). |
| Explicit control | off | yes | On: the input's degree and spans as given (refused when the rows are too few). Off: quintic across at least, spans added for the rows the order needs. |
| Degree U | 0 | yes | Explicit Control: the input's degree across the edge (0: its own). |
| Spans U | 0 | yes | Its spans across (0: its own). |
| Degree V | 0 | yes | Its degree along the edge (0: its own). |
| Spans V | 0 | yes | Its spans along (0: its own). |
| Refine | off | yes | Insert knots along the edge where the match misses the limits, up to Max new spans. |
| Max new spans | 10 | yes | Refine: how many spans it may add along the edge. |
| Position limit | 0.001 | yes | Refine and the feedback: the largest gap (G0) that passes. |
| Tangent limit | 0.1 | yes | The largest angle (degrees, G1) that passes. |
| Curvature limit | 0.5 | yes | The largest curvature and G3 difference (percent) that passes. |
| Outer edge | Edge align | yes | Alias's Outer Edge: the input leaves along the master's own direction across (Edge align), or turned by the skew angles. |
| Start skew | 0.0 | yes | Alias's Outer Edge Skew: the angle (degrees) the input leaves the edge at, turned from the master's own direction across, at the start. |
| End skew | 0.0 | yes | The skew at the edge's end (Edge Align at both: 0). |
| Attach point | off | yes | Curves: attach the end at a place along the master curve (Alias's Attach Point); off, at its nearest point. |
| Attach at | 0.0 | yes | Curves: where on the master curve the end attaches, 0 to 1. |
| Curve on surface | on | yes | Project: leave a curve on the master face where the input meets it (off: Alias's NoCOS). |
| Shrink to fit | on | yes | Project: the input's edge as cast must land on the face. |
| Proxy display | off | yes | Alias's Enable Proxy Display: the input's hull as it was, a ghost. |
| Diagnostic feedback | on | yes | Alias's Diagnostic Feedback: the gaps, angles and curvature differences along the edge in the viewport. |

##### Symmetry Align

Make an edge meeting a symmetry plane continuous with its mirror image.

- Node `Symmetry Align` in CAD; a step of Edit CAD.
- Works on edges or curves.
- With nothing selected: "Symmetry Align: select the input first: a surface's edge (Edges level) or a curve near its end (Curves level)".

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Continuity | G1 Tangent | yes | What the input meets its mirror half with. |
| Plane | YZ | yes | The symmetry plane, square to X, Y or Z. |
| Offset | 0.0 | yes | Where the plane crosses its axis. |
| Project for position | on | yes | Alias's Project For Position: the edge moved onto the plane (off: it stays, only its tangent set). |

#### Surface Build

##### Square

A surface from four boundaries, each Free, G0, G1, G2, implied or at a tangent angle.

- Node `Square` in CAD; a step of Edit CAD.
- Works on curves or edges.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Boundary 1 | G0 | yes | Alias's Square continuity at the boundary picked first: Free, G0 (position), G1 (tangent to the surface it lies on), G2 (curvature too), Implied tangent or curvature (the mirror across the plane the boundary lies in), or a Tangent angle to its surface. Its label on the model cycles it too. |
| Boundary 2 | G0 | yes | Alias's Square continuity at the boundary picked second: Free, G0 (position), G1 (tangent to the surface it lies on), G2 (curvature too), Implied tangent or curvature (the mirror across the plane the boundary lies in), or a Tangent angle to its surface. Its label on the model cycles it too. |
| Boundary 3 | G0 | yes | Alias's Square continuity at the boundary picked third: Free, G0 (position), G1 (tangent to the surface it lies on), G2 (curvature too), Implied tangent or curvature (the mirror across the plane the boundary lies in), or a Tangent angle to its surface. Its label on the model cycles it too. |
| Boundary 4 | G0 | yes | Alias's Square continuity at the boundary picked fourth: Free, G0 (position), G1 (tangent to the surface it lies on), G2 (curvature too), Implied tangent or curvature (the mirror across the plane the boundary lies in), or a Tangent angle to its surface. Its label on the model cycles it too. |
| Angle 1 | 0.0 | yes | Tangent angle: the boundary's surface's tangent plane turned this far about the edge (positive lifts toward its normal side). |
| Angle 2 | 0.0 | yes | Tangent angle: the boundary's surface's tangent plane turned this far about the edge (positive lifts toward its normal side). |
| Angle 3 | 0.0 | yes | Tangent angle: the boundary's surface's tangent plane turned this far about the edge (positive lifts toward its normal side). |
| Angle 4 | 0.0 | yes | Tangent angle: the boundary's surface's tangent plane turned this far about the edge (positive lifts toward its normal side). |
| Blend | Linear | yes | Alias's Blend type: Linear (a G0 boundary's influence falls straight off; four lines make the bilinear patch) or Cubic (it keeps the G0 patch's slope). |
| 1-3 boundary blend | 0.5 | yes | Alias's 1-3 Boundary Blend: where the influence of boundaries 1 and 3 meets across the surface (0.5 halfway; toward 3 above it). Acts on boundaries with a slope across (G1, G2, Implied, Cubic). |
| 1-3 influence | 1.0 | yes | Alias's 1-3 Influence: how far boundaries 1 and 3 shape the surface (1 as built; more reaches further in). Their continuity stays. |
| 2-4 boundary blend | 0.5 | yes | Alias's 2-4 Boundary Blend: where the influence of boundaries 2 and 4 meets across the surface (0.5 halfway; toward 4 above it). Acts on boundaries with a slope across (G1, G2, Implied, Cubic). |
| 2-4 influence | 1.0 | yes | Alias's 2-4 Influence: how far boundaries 2 and 4 shape the surface (1 as built; more reaches further in). Their continuity stays. |
| Rebuild 1 | off | yes | Alias's Rebuild: boundary 1 rebuilt to fewer spans, evenly parameterized by its length, before the surface is made (within a ten-millionth). |
| Rebuild 2 | off | yes | Alias's Rebuild: boundary 2 rebuilt to fewer spans, evenly parameterized by its length, before the surface is made (within a ten-millionth). |
| Rebuild 3 | off | yes | Alias's Rebuild: boundary 3 rebuilt to fewer spans, evenly parameterized by its length, before the surface is made (within a ten-millionth). |
| Rebuild 4 | off | yes | Alias's Rebuild: boundary 4 rebuilt to fewer spans, evenly parameterized by its length, before the surface is made (within a ten-millionth). |
| Colinear 1 | off | yes | Alias's Colinear Options: across boundary 1 the surface's isoparms line up with the neighbor's (as Align without skew); the corners keep their own lines. |
| Colinear 2 | off | yes | Alias's Colinear Options: across boundary 2 the surface's isoparms line up with the neighbor's (as Align without skew); the corners keep their own lines. |
| Colinear 3 | off | yes | Alias's Colinear Options: across boundary 3 the surface's isoparms line up with the neighbor's (as Align without skew); the corners keep their own lines. |
| Colinear 4 | off | yes | Alias's Colinear Options: across boundary 4 the surface's isoparms line up with the neighbor's (as Align without skew); the corners keep their own lines. |
| Explicit control | off | yes | Off: the multi-span quintic the continuity needs. On: the degrees and spans given (refitted, its sides held). |
| Degree U | 5 | yes | Explicit Control's structure. |
| Spans U | 4 | yes | Explicit Control's structure. |
| Degree V | 5 | yes | Explicit Control's structure. |
| Spans V | 4 | yes | Explicit Control's structure. |
| Boundary labels | on | yes | Alias's Boundary Labels: each boundary's continuity at its middle; a click cycles it. |
| Continuity check | on | yes | Alias's Continuity Check: the new surface's edges against the surfaces they meet, drawn as the Check node's. |

##### Skin

A loft through sections in order, its ends matched to the surfaces they lie on.

- Node `Skin` in CAD; a step of Edit CAD.
- Works on curves or edges.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Degree | 5 | yes | Alias's V degree: across the sections (lowered to one less than their count). |
| Closed | off | yes | Skin round: the last section back to the first, smoothly. |
| Start continuity | G0 | yes | The first section's side matched to the surface it lies on (an edge, a curve on a face): G0 to G3. |
| End continuity | G0 | yes | The last section's side, likewise. |
| Boundary labels | on | yes | The start and end continuity at their sections; a click cycles them. |
| Curves a section | 1 | yes | Alias's curve sets: the picks taken this many at a time as one section (curves end to end). |
| Surface type | Single surface | yes | Alias's Surface Type: one surface through the sets (each joined), or one surface for each curve of the sets. |
| Proportional crown | 0.0 | yes | Alias's Proportional Crown (two sections): the middle between them raised (or lowered) along the surface's normal by this much of the gap. |
| Flow control | Connect ends | yes | Alias's Flow Control: the sections matched by their own parameters, ends joined (Connect ends), or by their lengths, the isoparms spread evenly along each (Free). |
| Modify range | off | yes | Alias's Modify Range: skin only a stretch of every section. |
| Range from | 0.0 | yes | The stretch's end, a fraction of every section (of its length with Flow Control Free). |
| Range to | 1.0 | yes | The stretch's end, a fraction of every section (of its length with Flow Control Free). |
| Explicit control | off | yes | Off: the multi-span quintic the continuity needs. On: the degrees and spans given (refitted, its sides held). |
| Degree U | 5 | yes | Explicit Control's structure. |
| Spans U | 4 | yes | Explicit Control's structure. |
| Degree V | 5 | yes | Explicit Control's structure. |
| Spans V | 4 | yes | Explicit Control's structure. |

##### Rail

Generation curves swept along one or two rails.

- Node `Rail` in CAD; a step of Edit CAD.
- Works on curves or edges.
- Also picks rails: One rail, or two.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Sweep mode | Natural | yes | How the sections turn along the rail: Natural (rotation minimizing, Alias's Proportional with one generation curve), Parallel (not at all), Vector (keeping a direction up), Spine (square to a spine curve: the rail's last pick). |
| Vector | 0.0, 1.0, 0.0 | yes | Sweep mode Vector (Alias's View): the direction the sections keep up. |
| Two rails | Scale | yes | Alias's Transform Control with two rails: each section scaled to reach both rails, stretched along the chord only, or only turned. |
| Blend bias | 1.0 | yes | Alias's Gen. Blend Value: how the generation curves blend along the rail (1 evenly; above 1 the first lasts longer). |
| Rail 1 continuity | G0 | yes | The first rail's side matched to the surface it lies on (an edge, a curve on a face). |
| Rail 2 continuity | G0 | yes | The second rail's side, likewise. |
| First continuity | G0 | yes | The first generation curve's side (at the rail's start). |
| Last continuity | G0 | yes | The last generation curve's side (at the rail's end). |
| Boundary labels | on | yes | Each side's continuity at its middle; a click cycles it. |
| Sweep pivot | Closest | yes | Alias's Sweep Pivot: where the first generation curve meets the rail: their closest points, fractions along both, or a fraction along the rail and a point in space. |
| Pivot on rail | 0.0 | yes | The pivot's fraction along the rail. |
| Pivot on curve | 0.0 | yes | The pivot's fraction along the first generation curve. |
| Pivot point | 0.0, 0.0, 0.0 | yes | Off Curve: the generation curve's pivot, a point in space. |
| Fixed curve | Rail | yes | Alias's Fixed Curve: which stays when the pivots are made to meet: the rail (the generation curve moves onto it) or the generation curve (the rail moves). |
| Curve segments | off | yes | Alias's Curve Segments: sweep only a stretch of each rail and of the generation curves. |
| Rail 1 from | 0.0 | yes | The stretch's end, a fraction along the curve. |
| Rail 1 to | 1.0 | yes | The stretch's end, a fraction along the curve. |
| Rail 2 from | 0.0 | yes | The stretch's end, a fraction along the curve. |
| Rail 2 to | 1.0 | yes | The stretch's end, a fraction along the curve. |
| Curves from | 0.0 | yes | The stretch's end, a fraction along the curve. |
| Curves to | 1.0 | yes | The stretch's end, a fraction along the curve. |
| Rebuild rail 1 | off | yes | Alias's Rebuild per curve: rail 1 rebuilt by its length to the fewest spans (within a ten-millionth) before the sweep. |
| Rebuild rail 2 | off | yes | Alias's Rebuild per curve: rail 2 rebuilt by its length to the fewest spans (within a ten-millionth) before the sweep. |
| Rebuild generation curves | off | yes | Alias's Rebuild per curve: generation curves rebuilt by its length to the fewest spans (within a ten-millionth) before the sweep. |
| Colinear rail 1 | off | yes | Alias's Colinear Options: the sections placed along rail 1 by its own parameter, so the isoparms line up with the surface it is an edge of. |
| Colinear rail 2 | off | yes | Alias's Colinear Options: the sections placed along rail 2 by its own parameter, so the isoparms line up with the surface it is an edge of. |
| Explicit control | off | yes | Off: the multi-span quintic the continuity needs. On: the degrees and spans given (refitted, its sides held). |
| Degree U | 5 | yes | Explicit Control's structure. |
| Spans U | 4 | yes | Explicit Control's structure. |
| Degree V | 5 | yes | Explicit Control's structure. |
| Spans V | 4 | yes | Explicit Control's structure. |

##### Profile

Profiles placed along a rail, oriented Parallel, Radial or by the surface normal.

- Node `Profile` in CAD; a step of Edit CAD.
- Works on curves or edges.
- Also picks rail: The rail the profiles are placed on.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Orientation | Radial | yes | Alias's Profile orientation: the profiles carried without turning, turning with the rail, or kept up the normal of the face the rail lies on. |
| Transition | Linear | yes | Between profiles: Linear (straight), Local (eased between neighbors), Global (a smooth spline through all), Limited (smooth, never past a profile). |
| Explicit control | off | yes | Off: the multi-span quintic the continuity needs. On: the degrees and spans given (refitted, its sides held). |
| Degree U | 5 | yes | Explicit Control's structure. |
| Spans U | 4 | yes | Explicit Control's structure. |
| Degree V | 5 | yes | Explicit Control's structure. |
| Spans V | 4 | yes | Explicit Control's structure. |

##### Set Planar

Closed curves lying in a plane filled as a planar sheet.

- Node `Set Planar` in CAD; a step of Edit CAD.
- Works on curves or edges.

##### Sheet Extrude

Free curves swept along a direction to a sheet.

- Node `Sheet Extrude` in CAD; a step of Edit CAD.
- Works on curves or edges.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Direction | 0.0, 1.0, 0.0 | yes | The direction the curves are carried along. |
| Distance | 1.0 | yes | How far the curves are carried. |
| Both sides | off | yes | Carry them the distance both ways. |

##### Sheet Revolve

Free curves turned about an axis to a sheet.

- Node `Sheet Revolve` in CAD; a step of Edit CAD.
- Works on curves or edges.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Axis point | 0.0, 0.0, 0.0 | yes | A point of the axis. |
| Axis | 0.0, 1.0, 0.0 | yes | The axis's direction. |
| From | 0.0 | yes | The angle the sheet starts at. |
| To | 360.0 | yes | The angle it ends at (a whole turn: 360 more than From). |

##### Extend

Carry a surface's edge or a curve's end on, by a distance or a percentage.

- Node `Extend` in CAD; a step of Edit CAD.
- Works on edges or curves.
- With nothing selected: "Extend: select a surface's edge (Edges level) or a curve near its end (Curves level) first".

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Type | Linear | yes | Alias's and Parasolid's Extend: Linear (straight on, tangent), Natural (the same surface carried on, Alias's Extrapolate), Soft (curvature continuous, easing to straight), Reflective (curvature continuous, its change mirrored). |
| Distance | 1.0 | yes | How far the edge is carried on (a length, or a percentage of the surface's length across). |
| Distance is | Length | yes | The distance as a length, or a percentage of the surface's length across the edge (of the curve's length). |
| Merge | on | yes | Alias's Merge: the extension part of the surface; off, a sheet of its own beside it. |
| Chain select | off | yes | Alias's Chain Select: the edges running on tangent from the picked one (other surfaces' edges meeting it end to end) extended too. |

#### Surface Blends

##### Blend Surface

A surface between two sides of edges or curves, G0 to G3 at each.

- Node `Blend Surface` in CAD; a step of Edit CAD.
- Works on edges or curves.
- Also picks second side: Side 2, likewise.
- Also picks profiles: Alias's Profile Blend: curves across the blend it passes through (none: a Freeform Blend).

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Side 1 continuity | G1 | yes | Alias's Side 1: G0 (position), G1 (tangent), G2 (curvature) or G3 to the surface side 1 lies on; a free curve's side is G0. Its label on the model cycles it. |
| Side 2 continuity | G1 | yes | Alias's Side 2: G0 (position), G1 (tangent), G2 (curvature) or G3 to the surface side 2 lies on; a free curve's side is G0. Its label on the model cycles it. |
| Side 1 shape | 1.0 | yes | Alias's Side 1 Shape: above 1 the blend hugs the corner (longer tangents), below 1 it is rounder. |
| Side 2 shape | 1.0 | yes | Alias's Side 2 Shape: above 1 the blend hugs the corner (longer tangents), below 1 it is rounder. |
| Lock shapes | on | yes | Alias's Lock Shape Controls: side 2's Shape follows side 1's. |
| Proportional crown | 0.0 | yes | Alias's Proportional Crown: the middle raised (or lowered) by this much of the gap between the sides, along the normal of the gap and side 1. |
| Flow control | Connect ends | yes | Alias's Flow Control: the sides' ends joined to each other (Connect ends), each section square to side 1 (Free), or the sides matched by their own parameters so the isoparms leave them as their surfaces' do (Edge align). |
| Modify range | off | yes | Alias's Modify Range: blend only a stretch of each side. |
| Side 1 from | 0.0 | yes | The stretch's end, a fraction of the side's length. |
| Side 1 to | 1.0 | yes | The stretch's end, a fraction of the side's length. |
| Side 2 from | 0.0 | yes | The stretch's end, a fraction of the side's length. |
| Side 2 to | 1.0 | yes | The stretch's end, a fraction of the side's length. |
| Boundary labels | on | yes | Each side's continuity at its middle; a click cycles it. |
| Continuity check | on | yes | Alias's Continuity Check: the blend's edges against the surfaces its sides lie on, drawn as the Check node's. |
| Interior edge align | off | yes | Alias's Interior Edge Align (Profile Blend): the blend's isoparms run along each profile from side to side (side 2 matched through the profiles' ends). |
| Explicit control | off | yes | Off: the multi-span quintic the continuity needs. On: the degrees and spans given (refitted, its sides held). |
| Degree U | 5 | yes | Explicit Control's structure. |
| Spans U | 4 | yes | Explicit Control's structure. |
| Degree V | 5 | yes | Explicit Control's structure. |
| Spans V | 4 | yes | Explicit Control's structure. |

##### Surface Fillet

A rolling-ball blend between two sets of faces.

- Node `Surface Fillet` in CAD; a step of Edit CAD.
- Works on faces or patches.
- Also picks second faces: The second set.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Section | G1 circular | yes | Alias's Section Type: a chamfer between the contacts, the ball's circle, a curvature-continuous section (G2, or G3 also matching the curvature's rate), Bias (the peak pushed toward a set) or Lead (a conic by its Knee Ratio). |
| Construction | Radius | yes | Alias's Construction: the ball's radius, or the chord between the contacts held constant. |
| Radius | 1.0 | yes | The rolling ball's radius (Chord: the distance between the contacts). |
| Flip set 1 | off | yes | The ball rolls on the other side of the first set's faces (Alias's arrow). |
| Flip set 2 | off | yes | The other side of the second set's faces. |
| Trim | Automatic | yes | Alias's Trim Type: the faces trimmed back to the contacts, the contacts left on them as curves, or the faces as they are. |
| Form factor | 1.0 | yes | Alias's Form Factor (G2 and G3): the section's arms, below 1 sharper, above rounder. |
| Bias factor | 0.0 | yes | Alias's Bias Factor: the peak radius pushed toward set 1 (negative) or set 2 (positive). |
| Knee ratio | 0.0 | yes | Alias's Knee Ratio (Lead): the peak radius over the tangent offset (0: the ball's circle). |
| Curvature | Both | yes | Alias's Curvature: the sets whose curvature the section matches (G2, G3, Bias); the other it meets tangent only. |
| Variable | off | yes | Alias's Variable Fillets: the radius (or chord) from its size at the start through a middle size to an end size, eased between. |
| Middle size | 0.0 | yes | The radius (or chord) halfway along (0: none, straight from start to end). |
| End size | 1.0 | yes | The radius (or chord) at the end. |
| Continuity check | on | yes | The fillet's edges against the faces it rolls on, drawn as the Check node's. |

##### Tube

A round tube along a curve, its radius constant or varying.

- Node `Tube` in CAD; a step of Edit CAD.
- Works on edges or curves.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Radius | 0.25 | yes | The tube's radius. |
| Normal offset | 0.0 | yes | Alias's Normal offset: the tube's axis moved off the curve along the face's normal (off a face: the curve's frame's up). |
| Tangent offset | 0.0 | yes | Alias's Tangent offset: the axis moved across the curve, in the face. |
| Flip | off | yes | Alias's Flip: the normal offset the other way (a groove for a bump). |
| Variable | off | yes | Alias's variable radius: from the radius at the start through a middle radius to an end radius, eased between. |
| Middle radius | 0.0 | yes | The radius halfway along (0: none). |
| End radius | 0.25 | yes | The radius at the curve's end. |
| Trim | Off | yes | Alias's Tubular Offset trims (a curve on a face): where the tube meets the face as curves on it, or the face's strip under the tube taken away. |

##### Fill Surface

A hole's boundaries filled with one surface, G0 to G2 at each, through guides.

- Node `Fill Surface` in CAD; a step of Edit CAD.
- Works on edges or curves.
- Also picks guides: Curves the fill runs through, and points (a double-click on a surface); none as well.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Continuity | G1 | yes | Each boundary's continuity to the surface beside it (xNURBS's, Alias's N-sided): Free keeps its position, G0 position, G1 tangent, G2 curvature. A boundary's label on the model sets its own (a click cycles it). |
| Quad | off | yes | xNURBS's Quad sided: four boundaries make an untrimmed four-sided face (else one trimmed face over any number). |
| Tension | 0.0 | yes | Plasticity's Tension: 0 the smoothest bend, toward 1 tighter (shorter between the boundaries). |
| Flatness | 0.0 | yes | xNURBS's Flatness: a pull toward the boundaries' best plane. |
| Domain | Auto | yes | Alias's N-sided domain: the boundaries projected onto their best plane (Projected), laid round a polygon (Molded, for holes whose neighbors stand square to that plane: a lid on walls), or N quads round a center (Quads: fillets' and walls' corners, G2 in a second). Auto fills a ball's hole with its ball, fillets' corners with quads, projects the rest unless a neighbor stands square. |
| Boundary flow | Natural | yes | Plasticity's Boundary (Quad): the isoparms leaving each side as they fall (Natural), square to it (Normal), along the next sides (Next) or along the neighbor's own (Adjacent). |
| Guide continuity | G0 | yes | Guide curves the fill passes through (G0), or tangent to the face a guide lies on (G1). |
| Explicit control | off | yes | Alias's Explicit Control: the degrees and spans as set here, no refining (else multi-span quintic, refined). |
| Degree U | 5.0 | yes | Explicit Control's degree or span count that way. |
| Spans U | 4.0 | yes | Explicit Control's degree or span count that way. |
| Degree V | 5.0 | yes | Explicit Control's degree or span count that way. |
| Spans V | 4.0 | yes | Explicit Control's degree or span count that way. |
| Refine | on | yes | Rhino's Refine, xNURBS's Quality: spans are halved while a boundary misses its tolerance. |
| Most spans | 32.0 | yes | The most spans refining reaches each way. |
| Position tolerance | 0.0 | yes | The gap a boundary may keep (0: a millionth of the hole's size). |
| Angle tolerance | 0.05 | yes | The angle between normals a G1 or G2 boundary may keep, in degrees. |
| Curvature tolerance | 0.5 | yes | The normal curvatures' difference a G2 boundary may keep, in percent of the larger. |
| Boundary labels | on | yes | Each boundary's continuity at its middle; a click cycles it. |
| Continuity check | on | yes | Alias's Continuity Check: the fill's edges against the surfaces beside them, drawn as the Check node's. |
| Show conflicts | on | yes | Where the neighbors' demands disagree (xNURBS 7): the corners and stretches no surface meets, drawn red with their amounts. |
| Boundary 1 | Continuity row | yes | This boundary's own continuity (its label sets it). |
| Boundary 2 | Continuity row | yes | This boundary's own continuity (its label sets it). |
| Boundary 3 | Continuity row | yes | This boundary's own continuity (its label sets it). |
| Boundary 4 | Continuity row | yes | This boundary's own continuity (its label sets it). |
| Boundary 5 | Continuity row | yes | This boundary's own continuity (its label sets it). |
| Boundary 6 | Continuity row | yes | This boundary's own continuity (its label sets it). |
| Boundary 7 | Continuity row | yes | This boundary's own continuity (its label sets it). |
| Boundary 8 | Continuity row | yes | This boundary's own continuity (its label sets it). |
| Boundary 9 | Continuity row | yes | This boundary's own continuity (its label sets it). |
| Boundary 10 | Continuity row | yes | This boundary's own continuity (its label sets it). |
| Boundary 11 | Continuity row | yes | This boundary's own continuity (its label sets it). |
| Boundary 12 | Continuity row | yes | This boundary's own continuity (its label sets it). |
| Boundary 13 | Continuity row | yes | This boundary's own continuity (its label sets it). |
| Boundary 14 | Continuity row | yes | This boundary's own continuity (its label sets it). |
| Boundary 15 | Continuity row | yes | This boundary's own continuity (its label sets it). |
| Boundary 16 | Continuity row | yes | This boundary's own continuity (its label sets it). |

##### Bridge Fillet

A fillet bridging two side sets across a center set it consumes.

- Node `Bridge Fillet` in CAD; a step of Edit CAD.
- Works on faces or patches.
- Also picks second faces: The second side set.
- Also picks center faces: The center set the bridge also touches, and consumes.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Radius estimate | 0.5 | yes | Where the ball starts: the bridge's radius is the one touching all three sets, found from this. |
| Flip set 1 | off | yes | The ball rolls on the other side of the first set's faces. |
| Flip set 2 | off | yes | The other side of the second set's faces. |
| Trim | Automatic | yes | Automatic: the side sets trimmed back to the contacts and the center set consumed (Parasolid's three-face blend); Curves on surface: the contacts left as curves; Off: the faces as they are. |
| Continuity check | on | yes | The bridge's edges against the side sets, drawn as the Check node's. |

##### Corner

A patch closing the corner where three or four blends meet.

- Node `Corner` in CAD; a step of Edit CAD.
- Works on faces or patches.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Type | Ball corner | yes | Alias's Ball Corner (one trimmed patch over the corner's hole) or Corner Blend (four sides as one untrimmed patch, Quad), each G1 to the blends meeting there. |
| Continuity | Type's | yes | The patch's continuity to every blend (Type's: G1). |
| Continuity check | on | yes | The patch's edges against the blends, drawn as the Check node's. |
| Show conflicts | on | yes | Where the blends' demands disagree, drawn red (Fill's). |
| Center adjust | 0.0 | yes | Alias's Center Adjust: the patch's middle moved out (more) or in (less) along its normal, a share of the hole's size; 0 as the fill makes it. |

#### Surface Structure

##### Insert Knot

Add a knot to a surface where it is, the shape kept.

- A step of Edit CAD.
- Works on cvs or faces or patches.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Direction | U | yes | Across U (a new row of CVs along V) or across V. |
| Parameter | 0.5 | yes | Where along the surface, from 0 at its start to 1 at its end. |
| Times | 1 | yes | How many times: up to the degree. |

##### Remove Knot

Take a knot out of a surface, within a tolerance.

- A step of Edit CAD.
- Works on cvs or faces or patches.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Direction | U | yes | Across U or across V. |
| Parameter | 0.5 | yes | The inner knot nearest this parameter goes. |
| Times | 1 | yes | How many times, as far as the tolerance allows. |
| Tolerance | 0.01 | yes | How far the surface may move. |

##### Raise Degree

Raise a surface's degree along U and V, the shape kept.

- A step of Edit CAD.
- Works on cvs or faces or patches.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Raise U | 1 | yes | Degrees added along U (to 11 at most). |
| Raise V | 1 | yes | Degrees added along V. |

##### Rebuild

Rebuild a surface: explicit degrees and spans, within a tolerance, fewer spans, Bezier.

- A step of Edit CAD.
- Works on cvs or faces or patches.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Kind | Explicit | yes | Alias's Rebuild Surface types. |
| Explicit Control | Multi-span quintic | yes | The structure: quintic spans (the default), one span of degree 7 (a Bezier patch, G3 at both edges), or degrees and spans of one's own. |
| Degree U | 5 | yes | The degree along U. |
| Degree V | 5 | yes | The degree along V. |
| Spans U | 4 | yes | Spans along U (Within tolerance: to start with). |
| Spans V | 4 | yes | Spans along V. |
| Keep U ends | G2 | yes | The continuity its edges at the U ends keep with what they meet. |
| Keep V ends | G2 | yes | The continuity its edges at the V ends keep. |
| Tolerance | 0.01 | yes | How far the surface may move (Within tolerance, Reduce spans, Del multi knots). |
| Max spans | 32 | yes | Within tolerance: the most spans a direction gets. |

##### Convert to B-spline

Make a face's analytic surface a B-spline surface.

- A step of Edit CAD.
- Works on faces or patches.

#### Inspect

##### Check

Draw edges' continuity, curvature combs and the deviation from a reference over the body.

- Node `Check` in CAD.
- Works on edges.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Continuity | G2 Curvature | yes | The continuity each edge should have. Edges meeting it draw green, one order short yellow, further short red; the label at an edge's middle reads the order it reached and the measure that decided it. |
| Sharp edges | off | yes | Check creases too: edges whose faces meet at more than 10° all along them. Off, they are left out (their combs stay). |
| Stations | 12 | yes | Where along each edge the faces are compared, evenly spaced. |
| Distance | 0.001 | yes | G0: the largest gap between the two faces that still counts as touching. |
| Angle | 0.1 | yes | G1: the largest angle between the faces' normals that still counts as tangent. |
| Curvature | 0.5 | yes | G2: the largest difference of the faces' curvatures across the edge, relative to the larger. |
| Curvature rate | 1.0 | yes | G3: the largest difference of how fast those curvatures change across the edge, relative to the larger. |
| Combs | on | yes | Curvature combs on curved edges: quills away from the center of curvature, as long as the curvature. |
| Comb samples | 48 | yes | Quills along each curved edge. |
| Cross quills | on | yes | Each face's curvature across the edge as a quill at every station: equal quills are G2, a jump shows as two lengths. |
| Comb scale | 1.0 | yes | How long quills draw: at 1 the longest is a tenth of the body. |
| Deviation | off | yes | Color the body by how far it lies from the second input's surfaces (green within Acceptable, red outside the reference, blue inside). |
| Acceptable | 0.01 | yes | Deviation: within this distance of the reference the map is green. |
| Ramp | 0.1 | yes | Deviation: the distance at which the colors saturate (red outside the reference, blue inside). |
