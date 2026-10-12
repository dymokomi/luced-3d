# Node paths: parameters that name other nodes

A parameter that names another node holds a **node path**, Houdini's
operator path, and every such parameter goes through one module,
`src/node_paths.luc`. It parses and normalizes paths, resolves them,
writes the path from one node to another, lists what the picker offers,
keeps paths on their nodes when nodes are renamed or regrouped, and says
what a node reaches by path, for invalidation, stamps and the worker. No
node kind has path code of its own.

## The parameters

Every node path row is declared in `node_catalog.node_path_rows`, built
with `parameter_rows.node_path` (row kind `node`):

| Node | Row | Text slot | Names | Wildcards | Takes record it |
| --- | --- | --- | --- | --- | --- |
| Import | **Object** | 0 | a node with a result (`geometry`) | yes | no |
| Import | **Transform Object** | 1 | a node with a result (`geometry`); blank: the world, `.`: the source's own frame | no | no |
| Render | **Camera** | 0 | a Camera node (`camera`); blank: the first camera | no | yes |

A row's `targets` says which nodes it may name (`node_paths.fits`):
`geometry` is any node with a result, so not a Camera, Light, Render or
shader node; `camera` is a Camera. The picker lists only those, and a
wildcard matches only those.

These text rows are not node paths, though they hold paths or names. They
name things inside geometry, files or scenes, not nodes, so renaming a node
does not touch them:

- Camera, Light and Material **Path**: the object's or material's own path
  in the scene (`cameras/hero`, `materials/red`), which the node writes.
- Assign Material's **Material**: a material path in the library on its
  second input.
- Group rows and Blast's paths: elements and object paths inside the input.
- File, Cache, Export, Image Texture, a Light's Environment, a Render's
  Output and a Script's file rows: files on disk.
- Export's **Root prim** and a USD File's **Variants** and **Load
  payloads**: USD prim paths.
- A Code or Script node's text spare rows: strings the code reads.
- What takes record by node: visibility, transforms and lights are kept by
  node id, and hidden objects by their path inside the node's result. Only
  the Render camera is a node path.

The Code and Script nodes have no way to name another node; when they
gain one, it will be a node path row like these.

## Paths

An absolute path starts at the root and names each container down to the
node: `/Geo 2`, `/Group 1/CAD 3`, `/Geo 2/Sphere 4`. A relative path starts
at the node holding the row: `..` is the network it sits in, so
`../Sphere 4` is a sibling, `../..` the container above, and `../../Geo 2`
an object beside the holder's own. `.` is the holder itself.

`node_paths.normalize` keeps a typed path tidy: blank space around it, empty
and `.` steps, and a name followed by `..` go (`/Geo 2//./Box/../Cube 1/`
is `/Geo 2/Cube 1`); a relative path that ends where it starts is `.`.
`node_commands.set_text` stores node path rows normalized.

In a row that allows wildcards (Import's Object), `*` (any run of
characters) and `?` (one) in a name match every node there, in authoring
order: `/Geo*`, `/Geo 2/Sphere ?`. A wildcard never matches the holder or
the containers it sits in (they read it), nor what the row's targets
leave out.

Since a name is one step of a path, `Network.rename` refuses a name that is
blank, holds `/`, `*` or `?`, is `.` or `..` (`node_paths.name_problem`), or
is already a sibling's. New nodes never take a sibling's name. Should two
siblings share a name anyway, a path reads the first.

## The picker

A node path row shows the path and a button. The button opens the node
path picker (`node_path_picker.luc`): the nodes the row may name
(`node_paths.choices`), each level in authoring order and depth first into
containers, the one it names now checked. As in Houdini's operator
chooser, a toggle at the top, **Relative paths**, writes each choice from
the holder (`../../Geo 2/Sphere 4`) instead of from the root
(`/Geo 2/Sphere 4`); it starts off and is kept while the editor runs.
Choosing an entry sets the row in that form. Paths typed by hand may be
either form, as before.

The Takes pane's camera list sets every Render node's Camera to the chosen
camera's absolute path.

## Following renames and regrouping

Renaming a node, or a container on a path, and grouping (which moves nodes
into a new Group: a target, a container above it, or the holder itself)
run inside `Network.keeping_paths`:

1. `node_paths.references` takes every exact path, in the nodes' rows and
   in the takes other than the active one, with the node it reaches now.
2. The edit runs.
3. `node_paths.retarget` points each path at its node again where it no
   longer reaches it: an absolute path stays absolute; a relative one stays
   relative, recomputed from the holder (grouping the holder adds a `..`).

All of it is one undo step: undo brings back the names and every path.
Wildcard paths are left as typed, as Houdini leaves them, and so are blank
and `.`. Deleting a target leaves the path and the holder's error ("Nothing
at /Geo 2/Cube 1", "No camera at /Camera 3"); undo brings both back.

The active take's state is the nodes', so its paths are rewritten there; an
inactive take keeps its own copy of the Render camera, which is rewritten
in the take.

Nodes move between containers only by grouping today; there is no ungroup.
Copy and paste and Duplicate (`node_clipboard.luc`) follow Houdini: an
absolute path still names the original, and so does a relative path that
reaches a node left behind (it is kept as written); a relative path from a
copied node to another copied node names the copy, rewritten from the copy's
place and name (pasting renames copies whose names are taken, and the
copied nodes may land at another level).

## Cooking and invalidation

What a node reaches by path is part of what it reads:

- `node_paths.dependencies` lists the nodes a holder's rows reach.
  `Network.invalidate` recooks a holder when one of them changes (an Import
  also when a container above a source, above itself or at or above its
  Transform Object changes, since their placements place what it reads).
- A stamp leaves a node path row's text out and puts what it reaches in
  (`node_paths.resolution`, the ids row by row), so a rename that the paths
  followed recooks nothing, while a path that comes to name another node
  (a path to nothing that a rename makes good) recooks the holder. An
  Import's stamp also lists each source's stamp and placement steps.
- The worker is sent the body of every node holding paths with each
  request, since a rename changes the texts without changing a stamp, and
  it resolves the paths against the names in the request. Its kept results
  include what each holder reaches.

A Render node's Camera resolves in its network (`Network.render_camera`):
blank is the first camera in the scene, otherwise it must name a Camera
node, and the render looks through that node's camera, by its Path.
`Network.render_result` checks the scene for both the local cook and the
worker, and the Render panel starts from the same camera.

## Tests

`tests/editor/node_path_tests.luc` checks the module itself (normalizing,
refused names, wildcards, absolute and relative paths, targets, choices,
dependencies and resolutions, references kept through renames in the nodes
and in takes), Render's Camera through renames and grouping with undo and
redo, an inactive take's camera following a rename, the picker's toggle
writing relative and absolute paths for Import and Render rows, Import's
Transform starting at Into this object, the worker rendering after a rename
and regroup, and Modify › Rename… (F2). `tests/editor/import_path_tests.luc`
checks the Import's rows through renames, grouping, undo, deletion and the
worker. `tests/editor/node_clipboard_tests.luc` checks paths between copies,
within a network and across containers pasted together.
