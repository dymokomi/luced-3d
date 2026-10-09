# Script node examples

Scenes built with the Script node: Luce Base code that runs once per cook
over the whole geometry, as Houdini's Python SOP runs Python. Open one with
File > Open and select the Script node to see its code, the parameters its
`k.f32(...)` calls made, and its console.

The first cook of a scene builds each script into a small native tool, which
takes about a second; later cooks reuse it. `docs/SCRIPT.md` describes the
node and its API.

`tests/examples/scripts.luc` builds these scenes: every Script node must
build and cook without an error, and the program writes these files again.

| Scene | What it shows |
|---|---|
| `jpeg_heightfield` | An image as a colored height field. The `luce-image` package (named in the node's Packages row) reads `heightfield.jpg`, given by a file parameter relative to the project; a grid's points rise with each pixel's brightness and take its color, written through the bulk spans `positions()` and `point_vec3s("Cd")`. |
| `csv_points` | `points.csv` (x, y, z and mass after a header) as a point cloud: luce-std reads the file, Base's `strings` splits it, each row adds a point with `mass`, `pscale` and `Cd`, and `make_cloud()` turns the points into the cloud the viewport draws. A short row is a warning, not a failure. |
| `lsystem_tree` | Procedural modeling with loops over the whole geometry: an L-system string rewritten a few generations, then walked by a 3D turtle (a struct and a stack) that leaves a six-sided tube for every step, thinner on deeper branches, colored by height. |
| `verb_chain` | Verbs from code (Houdini's `hou.Geometry.execute`): a sphere, then Subdivide and PolyExtrude run by name with parameters set by their labels and a group expression, then colored by height. |
