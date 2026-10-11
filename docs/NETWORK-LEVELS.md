# Network levels: what renders, what a container yields, what the viewport shows

luced-3d's networks follow Houdini's split between the object level (`/obj`)
and the data networks inside objects (SOPs). This note says what each level
produces, how the flags work, what the viewport, the Outliner and Render show,
and how scenes from before this change were converted.

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
  Wiring one object-level node into another turns the source's flag off, so
  its result is not drawn twice, once alone and once inside its reader. Turn
  it back on if you want both.
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
2. Otherwise the node with the display flag. A project from before the radio
   rule can have several flagged nodes; the first one is used, with a warning.
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

## What changes in evaluation

`Network.outputs(parent)` applies the table above, and every reader of a
level uses it: the local cook and the worker's cook of containers, stamps
(a container's stamp lists the stamps of what it yields), pinned results in
the worker's store, invalidation, the Outliner and grouping. A container's
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
  - **Everything else**: the flagged objects of each object level above,
    except the branch you are in. They draw as the **context display mode**
    says.
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

## Conversion

There are no users, so there is no migration code. The example projects under
`examples/` are written by the tests (`tests/examples`), which build them with
the editor's own commands; they were regenerated under these rules. Projects
written before this change still open, but the `output` property is no longer
read or written, so a container whose output was chosen by the old rules
yields its flagged node instead.

## Tests

`tests/editor/level_tests.luc` covers each rule: the root renders every
flagged object, a container yields only its output node (and warns with
several or none), a Materials container yields every material, the viewport
keeps showing the root while the network view is deep, All, Greyed and Hidden
change what is drawn, the Outliner's greying and navigation, and Render
rendering the root.
