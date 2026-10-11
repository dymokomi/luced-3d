# Network levels: what renders, what a container yields, what the viewport shows

luced-3d's networks follow Houdini's split between the object level (`/obj`)
and the data networks inside objects (SOPs). This note says what each level
produces, how the flags work, why objects are not wired and how one reads
another (the Import node), and what the viewport, the Outliner and Render show.

## Two kinds of level

- **Object levels** are the root (Scene) and every Group whose context is
  Scene (a Group made at the root). They hold context containers (Geo, CAD,
  SDF, Volumes, GSplats, Materials, Group), cameras, lights and Render nodes,
  like Houdini's `/obj` and an object subnet.
- **Data levels** are the inside of Geo, CAD, SDF, Volumes and GSplats, and of
  Groups made inside them. They hold operators wired into chains, like a SOP
  network.

Materials and Material are special containers (below).

## The display flag

Every node has one flag, the **display flag** (`Node.visible`; the orange strip on
the node's right, `D`, and the eye in the Outliner). Bypass and Freeze stay as
they were. The Out flag (Auto / On / Off) and the island-terminal rule are
gone, and so are the isolated preview and its `/ PREVIEW` label: `D` sets the
display flag.

- **At an object level** the flag is per node, as in Houdini's `/obj`: every
  node with its flag on is active and renders, and any number can be on.
  Render nodes never render as objects; they are render settings (below).
- **In a data level** the flag is a radio button, as in a SOP network: one
  node holds it. Setting it on a node clears it on that node's siblings. A new
  node takes it. Deleting the node that holds it passes it to that node's
  first input, as Houdini does.

## What a container yields

A container's result, the one its parent level reads and draws, is:

| Container | Yields |
| --- | --- |
| Group at an object level | every child with its display flag on, each placed by the Group's transform |
| Geo, CAD, SDF, Volumes, GSplats, a Group inside them | its single output node's result, placed by its transform |
| Materials (and a Group inside it) | every material inside: the end of each chain (a node nothing inside reads) |
| Material | its shader, resolved from its shader nodes (unchanged) |

A data container's **output node** is chosen as Houdini chooses a SOP
network's:

1. An **Output** node inside it, if there is one. Output is a new
   pass-through node, offered in every data context. With several Output
   nodes the first one made is used, and the container warns: "Several
   Output nodes; Output 12 is used".
2. Otherwise the node with the display flag (there is at most one; a
   project with two in one data network does not load).
3. With neither, the container yields nothing and warns: "No Output node or
   display flag inside".

**Set Output** on the Network panel's bottom toolbar makes the selected
node feed the level's Output node, adding one after it when there is none.

The display flag and the Output node can differ, as in Houdini: while you work
upstream the viewport shows the flagged node, while the parent still reads the
Output node.

Hidden children no longer leave a container's aggregate: a data container
yields exactly one node, and an object-level Group yields its flagged
children.

## Objects are not wired

In Houdini, wires at `/obj` make a parenting hierarchy. luced-3d has no
object parenting (a Group places what it holds), so a wire between two
objects would mean nothing: a Geo feeding a Light, or a Geo feeding another
Geo. Nothing is wired at an object level:

- Object-level nodes have **no inputs** (a project that gives one inputs does
  not load), and the Network panel draws no ports there. Connecting two is
  refused: "Objects are not wired together; bring one into another with an
  Import node".
- Camera and Light have no input anywhere: each makes just its object.
- An object's network has no Input node (there is nothing for it to read);
  the node menu leaves it out there.
- Containers nested in a data network (a Geo inside a Geo, a Group inside an
  SDF) keep their two inputs and Input nodes, as Houdini's subnets do: that
  is wiring within one object.

When you edit inside a Geo, you see that Geo as the context: nothing at the
object level reads it, so it is never drawn as part of another object.

What could make sense later is an object-level node that acts on another
object (a deformer over a Geo). None exists; when one does, it is designed
then, not wired through generic object inputs.

## The Import node

**Import** (Houdini's Object Merge) is how one object reads another. It sits
in any data network (Geo, CAD, SDF, Volumes, GSplats, and Groups in them) and
has no inputs. Its rows are Object Merge's, for one object line:

| Object Merge | Import | Notes |
| --- | --- | --- |
| Object 1 | **Object** | A path, absolute or relative, with wildcards |
| Transform | **Transform** | None, Into This Object (the default here; Houdini's is None), Into Specified Object |
| Transform Object | **Transform Object** | Shown with Into Specified Object |
| Invert Transform | **Invert Transform** | Off with None |

### Paths

Object and Transform Object are node paths, as every parameter that names
another node is ([NODE-PATHS.md](NODE-PATHS.md)): absolute from the root
(`/Geo 2`, what the Geo yields; `/Geo 2/Sphere 4`, a node inside an
object) or relative from the Import itself (`../Sphere 4` a sibling,
`../../Geo 2` an object beside the Import's own). Each row's button opens
the node path picker, with its Relative paths toggle.

A name in the Object path may hold `*` (any run of characters) and `?` (one),
like Houdini's `/obj/ball*`: the Import reads every match, each placed by
the Transform menu, merged in authoring order. A wildcard never matches the
Import, the containers it sits in (so `/Geo*` from inside Geo 4 reads the
other Geos), cameras, lights, Render nodes or shader nodes.

### Transform

Houdini's object is a container here: Geo, CAD, SDF, Volumes, GSplats or a
Group, each placing what it yields by its Translate, Rotate, Scale and
Pivot. A source's **own frame** is that of its object: for a container, its
own placement and those of the containers above it; for a node inside one,
the containers it sits in. Its geometry starts there (a container's result
has its own placement undone first, as Houdini leaves out the object
transform). Then:

- **None**: it stays in its own frame. A Geo moved 5 along X imports at the
  origin.
- **Into This Object**: it is carried into the Import's frame (the placements
  of the containers it sits in): it lands where it sits in the scene, seen
  from this object. The source's placements apply, then the Import's
  containers' are undone; containers both share cancel.
- **Into Specified Object**: it is carried into the **Transform Object**'s
  frame, a path like Object's (a container: its own frame; a node inside
  one: that container's). Blank is the world, so the geometry arrives in
  world coordinates; `.` is the source's own frame, the same as None.
- **Invert Transform** carries it the other way, from the destination frame
  into the source's: with Into This Object, the geometry placed as if it
  sat in this object, seen from the source. With None it changes nothing.

`Network.import_steps` chooses the frames and `import_node.carry` writes the
carry as placement steps (each a translation, an XYZ rotation and a scale, so
uneven scale under rotation stays exact); an Euler rotation is undone axis by
axis, X then Y then Z.

### Paths follow their nodes

Renaming a node, or a container on a path, and grouping a source, a
container above it or the Import itself rewrite every exact Object and
Transform Object path in the same undo step, absolute as absolute and
relative as relative; wildcard paths stay as typed, and a deleted source
leaves the path and the Import's error ("Nothing at /Geo 2/Cube 1"). The
node path system does this for every node path row alike
([NODE-PATHS.md](NODE-PATHS.md#following-renames-and-regrouping)).

### Cooking

It recooks when a source changes, or a container's placement above a source,
above the Import or at or above its Transform Object changes
(`Network.invalidate`); its stamp lists each source's stamp and placement
steps and what its paths reach, not the paths, so a rename recooks nothing.
A rename that makes a path reach a different node (a path to nothing that
now finds one) recooks it. The worker is sent an Import's paths with every
request, since its stamp does not carry them ([NODE-PATHS.md](NODE-PATHS.md#cooking-and-invalidation)). Both the local cook and the worker read through
`Network.import_read`, which refuses an empty path, a path to nothing, and a
source that reads the Import ("An Import can't read what it is part of"):
importing the container the Import feeds.

A Materials library reaches a Geo this way (Import `/Materials 3` into Assign
Material's second input). A future mesh light would name its geometry the
same way, by an object path parameter, not a wire.

### Not carried over from Object Merge

Object Merge's Number of Objects (a list of Object, Group and Enable lines)
is not offered: a node's parameter rows are fixed by its kind, so a variable
list of path rows has no place yet; wildcards cover reading several objects,
and several Import nodes into a Merge cover the rest. Its Group, Expand
Group, per-object groups and path attributes, packing, bundles (`@props`),
`__display_sop__` and `__render_sop__`, and DOP paths are not offered either:
a container's result is already what its display flag or Output node yields.

## What changes in evaluation

`Network.outputs(parent)` applies the table above, and every reader of a
level uses it: the local cook and the worker's cook of containers, stamps
(a container's stamp lists the stamps of what it yields), pinned results in
the worker's store, invalidation, the Outliner and grouping. An Import node's
source joins the same readers (`Network.import_source`). A container's
instance is always visible: whether it is drawn is decided by its own flag at
its parent level, not by a visibility bit inside its result.

**Render** has no geometry input and no output to wire. It renders the root:
its cook is the merge of every flagged object at the root, checked for a
camera and lights as before. Its stamp lists the stamps of those objects. The
Render panel and the viewport's Render mode both render the root.

## What the viewport shows

The viewport always shows the root scene, however deep the network view is.

- **At the root** it draws every flagged object, as rendered.
- **Inside a container** it draws two things:
  - **The context**: what you are editing, drawn normally. In a data level,
    that is the node with the display flag. In an object-level Group, it is
    the Group's flagged children.
  - **Everything else**: what each level above yields, except the branch
    you are in: the flagged objects of each object level, and the output of
    each data container you are nested in. Inside a Group in a Geo, the
    Geo's output draws around the Group's flagged node, as the root's other
    objects do (unless the Group is that output: then it is the branch). A
    Materials library draws nothing. All of it draws as the **context
    display mode** says.
- **Coordinates.** The viewport works in the context's local frame (the
  transforms of the containers you are inside), as before, so modeling tools,
  picking and gizmos are unchanged. The rest of the scene is placed by the
  inverse of that frame, so it sits where it belongs around the context.
- **Context display mode.** A button at the top right, left of the shading
  button. A long press (or a right click) opens a menu of three modes; a click
  steps to the next one.
  - **All**: everything else draws normally.
  - **Greyed** (the default): everything else draws ghosted. Meshes and CAD
    previews draw desaturated and see-through after the context, depth
    tested without writing depth (luce-3d's `Material.fade`, luce-gpu's
    `mesh_fade`), so the grid and what lies behind still show; splats fade
    the same way (`GaussianSplats.set_faded`); their lines draw dim. Ghosts
    hide nothing from Visible only.
  - **Hidden**: only the context draws.
- **Edit tools and selection** act on the context only: the rest of the
  scene can't be picked, in any mode.

The mode is a view setting, like the shading mode: it is not undone and not
saved with the project. Switching it redraws without recooking.

## The Outliner

The Outliner lists the root's objects: each object-level node, under each
container what it yields (its output node, or each material), and under an
object-level Group its flagged children.

- While the network view is inside a container, every row outside that
  container is greyed. The container and the rows below it stay as they are.
- Clicking any row, greyed or not, takes the network view to that node's
  network and selects it. Double-clicking a container enters it.
- The search field at the top lists only the rows whose name holds what is
  typed (any case), with the rows above them; collapsed branches are searched.
- The eye toggles an object-level node's display flag. Rows inside data
  containers have no eye: a data container's output is chosen in its network.

## Tests

`tests/editor/level_tests.luc` covers each rule: the root renders every
flagged object, a container yields only its output node (and warns with
several or none), a Materials container yields every material, the viewport
keeps showing the root while the network view is deep, All, Greyed and Hidden
change what is drawn, the Outliner's greying and navigation, and Render
rendering the root. `tests/editor/object_import_tests.luc` covers the
object level (no inputs, no Input nodes, refused wires and projects), the
Import node (absolute and relative paths, placement with rotated and scaled
containers, invalidation and stamps, refusals, the worker) and nested
containers in All, Greyed and Hidden. `tests/editor/import_transform_tests.luc`
checks each Transform mode and Invert Transform against the world with
containers turned about several axes and scaled unevenly, nested
containers, wildcards and the worker; `tests/editor/import_path_tests.luc`
renames sources and their containers, groups a source, an ancestor and the
Import, undoes and redoes each, and checks patterns, deleted sources,
refused names and the worker; `tests/editor/node_path_tests.luc` checks the
node path system every such row shares ([NODE-PATHS.md](NODE-PATHS.md#tests)).
