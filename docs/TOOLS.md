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

### Pattern

#### Select Checker

Keep a checker pattern of the group: runs of selected and deselected elements across each island.

- Node `Select Checker` in Geo; a step of Edit Mesh.
- Works on points or edges or faces.
- With nothing selected: "Select the region to thin out".

| Row | Starts at | On the tool bar | What it does |
| --- | --- | --- | --- |
| Selected | 1 | yes | Elements kept selected in a row. |
| Deselected | 1 | yes | Elements deselected in a row, after each selected run. |
| Offset | 0 | yes | Shift the pattern along by this many elements. |
