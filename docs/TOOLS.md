# Tools

Generated from the tool registry (`src/tool_registry.luc`) by `tools/tool_docs.py`; do not edit
by hand. A test fails when this page is stale.

Every tool is declared once. Its node, its Edit step, the tool bar, the Create, Modify and Select
menus, the A/S/D marking menus, the right-click menu, Repeat, its prompt, its icon and this page
all come from that declaration (docs/research/POLY-MODELING.md §3). The mesh tools are
luce-geocore's verbs.

## Create

### Draw

#### PolyDraw

Add a polygon through drawn positions, or through the group's points.

- Node `PolyDraw` in Geo; a step of Edit Mesh.
- Works on points.
- With nothing selected: "Select three or more points, or click to place corners".
- Gesture: clicks place its corners when nothing is selected; Enter finishes.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Snap distance | 0.0 | yes | Drawn corners this close to an existing point use it (0: only where they coincide). |
| Corners | 0 | no | How many drawn positions follow (x, y, z each); 0 makes the face through the group's points. |

## Modify

### Extrude

#### Extrude

Extrude faces (as regions or one by one) or edges.

- Node `PolyExtrude` in Geo; a step of Edit Mesh.
- Works on faces or edges.
- A drag in the viewport after it runs sets Distance.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Distance | 0.2 | yes | How far the fronts move along their faces' normals. |
| Inset | 0.0 | yes | How far the fronts' boundaries move inward across the faces. |
| Divisions | 1 | yes | Rows of faces along each wall. |
| Individual faces | off | yes | Extrude each face on its own instead of each connected region. |
| Clamp inset | on | yes | Keep each inset within half of the boundary edges beside it. |

#### Inset

Inset faces by a distance, as regions or one by one.

- Node `Inset` in Geo; a step of Edit Mesh.
- Works on faces.
- A drag in the viewport after it runs sets Thickness.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Thickness | 0.1 | yes | How far the inner faces' boundaries move inward. |
| Depth | 0.0 | yes | How far the inner faces move along their normals. |
| Individual faces | off | yes | Inset each face on its own instead of each connected region. |
| Clamp | on | yes | Keep each inset within half of the boundary edges beside it. |

#### Duplicate

Copy the group's faces, offset along their normals.

- Node `Duplicate` in Geo; a step of Edit Mesh.
- Works on objects or faces.
- A drag in the viewport after it runs sets Offset.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Offset | 0.2 | yes | Distance of the copies along their face normals. |

### Bevel

#### Bevel

Bevel the group's edges into strips of faces.

- Node `PolyBevel` in Geo; a step of Edit Mesh.
- Works on edges.
- A drag in the viewport after it runs sets Offset.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Offset | 0.1 | yes | Distance from each beveled edge to the sides of its strip, measured in the faces beside it. |
| Segments | 1 | yes | Faces across each strip. |
| Profile | 0.5 | yes | Shape across the strip: 0.5 round, toward 1 the original corner, 0 flat. |
| Clamp overlap | on | yes | Keep each offset within half of the edges it slides along, so strips cannot cross. |

### Cut

#### Loop Cut

Cut edge loops across the rings of the group's edges.

- Node `Loop Cut` in Geo; a step of Edit Mesh.
- Works on edges.
- A drag in the viewport after it runs sets Slide.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Cuts | 1 | yes | New loops across each ring. |
| Slide | 0.0 | yes | Move the loops toward one side of the ring (-1..1). |
| Whole ring | on | yes | Cut the whole ring through each of the group's edges; off: only across the group's edges. |

#### Knife

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

#### Connect

Connect the group's points or edge middles across their faces.

- Node `Connect` in Geo; a step of Edit Mesh.
- Works on points or edges.
- With nothing selected: "Select points (or edges) across faces".
- A drag in the viewport after it runs sets Position.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Position | 0.5 | yes | Where along each of the group's edges the new point sits. |

#### Edge Slide

Slide the group's edges along the faces beside them.

- Node `Edge Slide` in Geo; a step of Edit Mesh.
- Works on edges.
- A drag in the viewport after it runs sets Amount.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Amount | 0.5 | yes | How far along the rails, as a fraction of each rail; the sign picks the side. |

### Fill

#### Fill

Cap each closed loop of the group's boundary edges.

- Node `Fill` in Geo; a step of Edit Mesh.
- Works on edges.
- With nothing selected: "Select the boundary edges around each hole".

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Mode | Single face | yes | One face per loop, or triangles around a new point at its center. |

#### Bridge

Join pairs of boundary loops or runs among the group's edges with faces.

- Node `Bridge` in Geo; a step of Edit Mesh.
- Works on edges.
- With nothing selected: "Select two boundary loops or runs of edges".

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Divisions | 1 | yes | Rows of faces across each bridge (chains with as many edges). |
| Twist | 0 | yes | Turn where a closed pair's second loop starts, by this many points. |

### Merge

#### Fuse

Merge nearby points of the group.

- Node `Fuse` in Geo; a step of Edit Mesh.
- Works on objects or points.
- A drag in the viewport after it runs sets Distance.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Distance | 0.001 | yes | Points of the group closer than this merge into the first of them. |

#### Merge Points

Merge the group's points: at their center, first, last, per island or by distance.

- Node `Merge Points` in Geo; a step of Edit Mesh.
- Works on points or edges or faces.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Mode | At center | yes | Where the group's points merge: all at their center, the first or the last point; each connected island at its center; or those within the distance. |
| Distance | 0.001 | yes | By distance: points of the group closer than this merge. |

### Delete

#### Delete

Remove the group's faces (points delete every face using them) and the points left unused.

- Node `Delete` in Geo; a step of Edit Mesh.
- Works on components.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Keep group | off | yes | On: keep only the group. Off: delete it. |

#### Clean

Remove points no face uses.

- Node `Clean` in Geo; a step of Edit Mesh.
- Works on components, or everything when nothing is selected.

#### Dissolve

Join the faces across the group's interior edges (or around its points), one face per region.

- Node `Dissolve` in Geo; a step of Edit Mesh.
- Works on points or edges or faces.

### Split

#### Split

Detach the group's faces: they get their own points.

- Node `Split` in Geo; a step of Edit Mesh.
- Works on faces.

### Sweep

#### PolyMirror

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

#### Spin

Sweep the group's edges around an axis into a surface of revolution.

- Node `Spin` in Geo; a step of Edit Mesh.
- Works on edges.
- A drag in the viewport after it runs sets Angle.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Axis | Y | yes | The axis the profile turns about. |
| Center | 0.0, 0.0, 0.0 | yes | A point on the axis. |
| Angle | 360.0 | yes | How far the profile turns, in degrees; 360 closes it. |
| Steps | 12 | yes | Copies of the profile along the turn. |

### Subdivide

#### Triangulate

Split the group's faces into their triangles.

- Node `Triangulate` in Geo; a step of Edit Mesh.
- Works on objects or faces.

#### Subdivide

Split faces into quads, optionally with Catmull-Clark smoothing.

- Node `Subdivide` in Geo; a step of Edit Mesh.
- Works on objects or faces, or everything when nothing is selected.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Levels | 1 | yes | Each level splits every face into quads. |
| Method | Catmull-Clark | yes | Catmull-Clark smooths as it splits; Linear keeps the shape. |

#### Crease

Set the crease sharpness of the group's edges for subdivision.

- Node `Crease` in Geo; a step of Edit Mesh.
- Works on edges.
- A drag in the viewport after it runs sets Sharpness.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Sharpness | 10.0 | yes | USD crease sharpness: 0 smooth, 10 infinitely sharp; s stays sharp for s levels. |
| Mode | Set | yes | Give the group's edges this sharpness, or make them smooth. |

### Shape

#### Smooth

Laplacian relaxation of the group's points.

- Node `Smooth` in Geo; a step of Edit Mesh.
- Works on components.
- A drag in the viewport after it runs sets Amount.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Amount | 0.5 | yes | How far each point moves toward the average of its neighbors. |
| Iterations | 1 | yes | Rounds of smoothing. |

#### Noise

Deterministic noise displacement.

- Node `Mountain` in Geo; a step of Edit Mesh.
- Works on components.
- A drag in the viewport after it runs sets Height.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Height | 0.2 | yes | Largest displacement of the noise. |
| Seed | 0 | yes | Another seed gives other noise. |

#### Peak

Move points along their normals.

- Node `Peak` in Geo; a step of Edit Mesh.
- Works on components.
- A drag in the viewport after it runs sets Distance.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Distance | 0.2 | yes | Distance along the averaged normals. |

#### Flatten

Flatten the group onto a plane through its centroid.

- Node `Flatten` in Geo; a step of Edit Mesh.
- Works on components.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Axis | Y | yes | The axis flattened to the group's centroid. |

#### Snap

Snap points to a grid.

- Node `Snap` in Geo; a step of Edit Mesh.
- Works on components.
- A drag in the viewport after it runs sets Spacing.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Spacing | 0.1 | yes | Grid spacing points snap to. |

### Normals

#### Reverse

Flip the winding of the group's faces.

- Node `Reverse` in Geo; a step of Edit Mesh.
- Works on objects or faces.

## Select

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

### Loops

#### Loop

Edge loops through the selected edges, face loops through faces side by side, point loops through points along an edge.

- Node `Select Loop` in Geo; a step of Edit Mesh.
- Works on edges or faces or points.
- With nothing selected: "Select edges, two faces side by side, or two points on a loop".
- Group function: `loop(group, only_between)`.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Only between | off | yes | With two edges on one loop selected: only the run between them, the shorter way round. |

#### Ring

Edge rings through the selected edges: across each quad to its opposite edge.

- Node `Select Ring` in Geo; a step of Edit Mesh.
- Works on edges.
- With nothing selected: "Select edges for Ring".
- Group function: `ring(group)`.

#### Boundary Loop

Each selected boundary edge's whole boundary; selected faces' outline as edges.

- Node `Select Boundary Loop` in Geo; a step of Edit Mesh.
- Works on edges or faces.
- With nothing selected: "Select boundary edges, or faces for their outline".
- Group function: `boundary(group)`.

#### Loop to Region

The faces a closed loop of selected edges encloses (its smaller side, or bigger).

- Node `Select Loop to Region` in Geo; a step of Edit Mesh.
- Works on edges.
- With nothing selected: "Select a closed edge loop".
- Group function: `region(group, side)`.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Side | Smaller | yes | Which side of each closed loop: the one with fewer faces, or more. |

### Region

#### Grow Selection

The selection and its neighbors, a ring at a time.

- Node `Select Grow` in Geo; a step of Edit Mesh.
- Works on points or edges or faces.
- Group function: `grow(group, steps, face_step)`.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Steps | 1 | yes | How many rings of neighbors to add or take away. |
| Face step | off | yes | Faces reach faces that share a point, points and edges reach across faces; off: faces across edges, points and edges along edges. |

#### Shrink Selection

The selection without its outer ring, a ring at a time.

- Node `Select Shrink` in Geo; a step of Edit Mesh.
- Works on points or edges or faces.
- Group function: `shrink(group, steps, face_step)`.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Steps | 1 | yes | How many rings of neighbors to add or take away. |
| Face step | off | yes | Faces reach faces that share a point, points and edges reach across faces; off: faces across edges, points and edges along edges. |

#### Border

The selected elements next to an unselected one.

- Node `Select Border` in Geo; a step of Edit Mesh.
- Works on points or edges or faces.
- Group function: `border(group)`.

#### Connected

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

#### Linked Flat

Faces reached from the selection across edges flatter than an angle.

- Node `Select Linked Flat` in Geo; a step of Edit Mesh.
- Works on faces.
- Group function: `flat(group, angle)`.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Angle | 1.0 | yes | The largest angle between two faces still counted flat, in degrees. |

#### Shortest Path

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

### Similar

#### Similar

Every element like a selected one by normal, area, perimeter, sides, plane, material, group, length, direction, face angle, crease, seam, sharpness or valence.

- Node `Select Similar` in Geo; a step of Edit Mesh.
- Works on points or edges or faces.
- Group function: `similar(group, by, compare, threshold)`.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| By | Normal | yes | What is compared. Faces: Normal, Area, Perimeter, Sides, Coplanar, Material, Group. Edges: Length, Direction, Face angle, Crease, Seam, Sharp, Faces, Group. Points: Normal, Edges, Faces, Group. |
| Compare | Equal | yes | Equal within the threshold, or at least, or at most, a selected element's value. |
| Threshold | 0.01 | yes | How far apart values still count as equal: in the value's units, degrees for Normal, Direction and Face angle. |

### Find

#### Sharp Edges

Edges whose faces meet at more than an angle.

- Node `Select Sharp Edges` in Geo; a step of Edit Mesh.
- Works on edges, or everything when nothing is selected.
- Group function: `sharp(group, angle)`.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Angle | 30.0 | yes | Edges whose two faces meet at more than this, in degrees. |

#### By Sides

Faces by their number of sides: triangles, quads, n-gons.

- Node `Select By Sides` in Geo; a step of Edit Mesh.
- Works on faces, or everything when nothing is selected.
- Group function: `sides(group, sides, compare)`.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Sides | 4 | yes | The number of sides compared with. |
| Compare | Equal | yes | How a face's sides compare with Sides. |

#### By Area

Faces smaller or larger than an area.

- Node `Select By Area` in Geo; a step of Edit Mesh.
- Works on faces, or everything when nothing is selected.
- Group function: `area(group, area, compare)`.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Area | 0.01 | yes | The area compared with, in square units. |
| Compare | Less | yes | Faces smaller than Area, or larger. |

#### By Normal

Faces facing a direction within a spread.

- Node `Select By Normal` in Geo; a step of Edit Mesh.
- Works on faces, or everything when nothing is selected.
- Group function: `facing(group, direction_x, direction_y, direction_z, spread)`.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Direction | 0.0, 0.0, 0.0 | yes | The direction faces should face (a zero vector takes +Y). |
| Spread | 30.0 | yes | How far a face's normal may lean from Direction, in degrees. |

#### Non-manifold

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

#### Loose

Points no face uses.

- Node `Select Loose` in Geo; a step of Edit Mesh.
- Works on points, or everything when nothing is selected.
- Group function: `loose(group)`.

#### Interior Faces

Faces all of whose edges have more than two faces (walls inside a solid).

- Node `Select Interior Faces` in Geo; a step of Edit Mesh.
- Works on faces, or everything when nothing is selected.
- Group function: `interior(group)`.

### Pattern

#### Checker

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

#### Random

A random share of the group: each element kept with the Ratio's chance, the same for the same seed.

- Node `Select Random` in Geo; a step of Edit Mesh.
- Works on points or edges or faces.
- With nothing selected: "Select the region to thin out".
- Group function: `random(group, ratio, seed)`.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Ratio | 0.5 | yes | The share of the group kept selected. |
| Seed | 0 | yes | Another seed, another pattern. |

### Symmetry

#### Mirror Selection

The selection's mirror across X, Y or Z (elements with nothing at their mirror drop out).

- Node `Select Mirror` in Geo; a step of Edit Mesh.
- Works on points or edges or faces.
- Group function: `mirror(group, axis, extend)`.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Axis | X | yes | The plane through the origin the selection is mirrored across. |
| Extend | off | yes | Keep the selection and add its mirror; off: only the mirror. |

### Convert

#### Convert

The selection as points, edges or faces: those it touches, or only those it contains (Maya's Convert Selection).

- Node `Select Convert` in Geo; a step of Edit Mesh.
- Works on points or edges or faces.

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| To | Faces | yes | The component type the selection becomes. |
| Rule | Touching | yes | Touching: every element the selection touches. Contained: only those all of whose points, edges or faces are selected. |
