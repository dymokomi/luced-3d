# The Script node

The Script node is luced-3d's Python SOP. You write one function, `cook`,
that runs **once per cook over the whole geometry**: read files, loop over
anything, keep structs and lists, call verbs, and build or edit points,
polygons, curves and attributes. The code is [Luce Base](https://luce-base.luciaos.com),
compiled by the real compiler into a native program, so loops run at the
speed of C, and it may import any Luce package as it is.

![An L-system tree from a Script node](preview_script_tree.png)

```luce
## Lift the input (input 0) by a parameter.
from luce_geocore.script import Cook

pub func cook(k: Cook*) -> !:
    let lift = k.f32("lift", 0.5)
    let positions = try k.geometry().positions()
    for i in 0..<positions.length:
        positions[i].y += lift
```

Add one with Tab (Utility). Example scenes are in `examples/scripts/`
(File > Open).

## Script or Code?

| | Code node (Wrangle) | Script node (Python SOP) |
|---|---|---|
| Runs | once per element, all in parallel | `cook(k)` once, over everything |
| Language | a safe subset of Base | all of Base: structs, pointers, recursion, threads |
| Imports | none | any Luce package |
| After an edit | about a millisecond | a build: about a second the first time, then cached |

Use a Code node for per-point math every frame; use a Script node to read a
file, run an algorithm that needs the whole mesh, or chain verbs. A Script
node that reads a JPEG and a Code node after it that animates the result
work well together.

## How a cook runs

The node's code is the module `script.lucb` of a small tool that luc builds.
The build is kept under a key of the code, the packages and the toolchain, so
an unchanged script never builds twice, and an undo finds its build. While a
build runs the node shows *Building script*; a build error underlines its line
in the editor.

The tool runs in a child process: a script that crashes, traps on an index
out of range or loops forever fails the node, never the editor. Each cook
starts fresh, as Houdini's Python SOP does with Maintain State off: module
`var`s start at their initial values every time. (The editor keeps the next
process started, so a cook does not wait for one.)

The geometry crosses to the child and back as `.prism` files: about 35 ms
for a million quads, under 3 ms for small meshes. The console starts with a
status line, for example `[built in 0.55 s · cooked in 3.5 ms (load 0.1 ms,
save 0.3 ms)]`.

On macOS the first start of a newly built tool can take a second or more
while the system checks it; allowing the editor (or the Terminal you start it
from) under System Settings > Privacy & Security > Developer Tools avoids it.

## The cook: `k`

`k.geometry()` is the output, which starts as a copy of input 0 (empty when
nothing is wired). Replace it whole with `k.set_geometry(g)`.

| Call | Is |
|---|---|
| `k.input(i)`, `k.connected(i)` | input 0 or 1, read-only (`copy()` one to change it) |
| `k.f32("name", 0.5)`, `k.f64`, `k.i32` | a number parameter |
| `k.toggle("name", true)` | an on/off parameter |
| `k.vec3("name", [x, y, z, 0.0])`, `k.color(...)` | a vector or color parameter |
| `k.menu("name", "Low\|High", 1)` | a menu: the chosen index |
| `k.text("name", "hi")`, `k.file("name", "image.jpg")` | text; a file with a picker, relative to the project's folder |
| `k.ramp("name", t)`, `k.ramp_color("name", t)` | a ramp parameter at `t` |
| `k.frame()`, `k.time()`, `k.fps()` | the timeline; reading one makes the node follow it |
| `k.warning(f"...")` | a warning on the node; the cook goes on |
| `try k.error(f"...")` | fails the node at this line |
| `k.progress(0.4)` | how far the cook is, on the node |
| `print(...)` | the console under the code |

As in the Code node, a literal call such as `k.f32("height", 0.3)` makes a
row on the node, starting at 0.3. A tuned value survives edits to the code.

## Geometry

`Geometry` is a geometry set opened for editing (luce-geocore's `script`
module). Making one: `Geometry.empty()`, `grid(size, divisions)`,
`sphere(radius, segments)`, `cube(size)`, `load("file.prism")`.

| Call | Is |
|---|---|
| `add_point(p)`, `add_points(list)` | new points; their number |
| `add_polygon(points)` | a polygon through point numbers |
| `remove_points(list)`, `remove_prims(list, remove_points)` | removal; numbers after them move down |
| `position(i)`, `set_position(i, p)`, `prim_size(f)`, `prim_point(f, n)` | one element |
| `positions()` | every position as a writable `Float3[]` (`.x`, `.y`, `.z`): the fast path |
| `point_count()`, `prim_count()`, `vertex_count()`, `bounds()` | sizes |
| `set_f32(Domain3.point, i, "mass", v)`, `value_f32(...)` | attributes, one element (also `vec3`, `i32`, `text`); writing makes them |
| `set_point_f32`, `point_vec3`, ... | point shorthands |
| `f32s(domain, name)`, `vec3s(...)`, `i32s(...)`, `point_vec3s("Cd")` | a whole attribute as a writable span |
| `set_detail_f64`, `set_detail_vec3`, `set_detail_text` | detail (global) attributes |
| `add_to_group(Domain3.prim, "top", f)`, `in_group(...)`, `group_flags(...)` | groups, named as group expressions name them |
| `add_polyline(points, closed)`, `add_curve(points, degree, closed)` | curves (degree 5 by default) |
| `make_cloud()`, `cloud_count()`, `cloud_position(i)`, `cloud_value(i, name)` | the point cloud |
| `merge(&other)`, `transform(t, r, s)`, `add_instance(&child, t, r, s)` | whole sets; instances are packed copies |
| `copy()`, `save(path)` | a copy; a `.prism` file |

Positions in spans are relative to `origin()`, which is zero unless the
input set one. A span stays valid until points or polygons are added or
removed.

## Verbs

Every node of the menu that luce-geocore runs is a verb, as in Houdini's
`hou.Geometry.execute`:

```luce
var subdivide = try Verb.named("Subdivide")
try subdivide.parm("Levels", 2.0)
var smooth = try subdivide.run(k.geometry())
try smooth.apply("Subdivide")   # in place, with defaults
```

`parm` takes the label the node's row shows (case, spaces and underscores do
not matter); a wrong label fails with the verb's labels. `group("@P.y>1",
GroupKind.prims)` sets the Group and Group Type rows.

## Packages

The **Packages** row names what the script imports, apart by spaces:
`luce-image`, `owner/name@^1.2`, or a folder (`../my-reader`). luce-geocore
and luce-std are always there. A registry package is locked when it is added,
and the lock is kept in the project, so the script builds the same anywhere;
a build needs the packages downloaded once, then works offline.

## Errors

A build error, a trap (`index out of bounds`), `k.error` and an error the
script raises itself (`error(code, "...")`) name the line and column of the
script, and the editor underlines it. An error a package raised and `try`
passed up names where it was raised instead: *returned from cook: the file
could not be opened (raised at luce_geocore/src/...)*.

## Not yet

- Completion and hover: the editor's help reads the Code node's API; it
  cannot see a script's imports until luce-base's `embed.Library` checks
  package modules.
- Volumes from code (`add_volume`), array attributes, and editing a
  polygon's own vertex list.
