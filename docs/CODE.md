# The Code node

The Code node is luced-3d's Wrangle. You write code for **one element**
(one point, one primitive, one vertex), and the node runs it for every
element in parallel. If you know Houdini's Attribute Wrangle, it works the
same way. The code is [Luce Base](https://luce-base.luciaos.com), so it reads
much like VEX with Python's indentation.

![A terrain built from three Code nodes](preview_code_terrain.png)

```luce
# Run Over: Points. p is this point.
p.P[1] += math32.sin(p.P[0] * 4.0) * 0.1
```

Add one with Tab or by holding A in the viewport. Example scenes are in
`examples/wrangles/` (File > Open).

## Run Over

The **Run Over** menu says what one run of the code is, and which names the
code gets:

| Run Over | One run is | Names |
|---|---|---|
| Points | one point | `p`, `k` |
| Vertices | one corner of a polygon | `v`, `k` |
| Primitives | one face | `f`, `k` |
| Detail (only once) | the whole geometry, once | `k` |
| Numbers | each number `n` from 0 to Count - 1 | `n`, `k` |

The runs are independent. Each one reads the **input** geometry and writes
only its own element. It never sees what other runs wrote, so neither the
order nor the number of threads changes the result. (Houdini works the same
way.) A **Group** limits which elements run; the rest pass through
unchanged.

## Elements

`p` (Point), `f` (Prim) and `v` (Vertex) have their common attributes as
fields. Three-component values are `f32[4]` vectors whose fourth lane is
ignored, so `+`, `-` and `*` work on whole vectors:

| Field | Point | Prim | Vertex |
|---|---|---|---|
| `P` position | ✓ | | |
| `N` normal | ✓ | | ✓ |
| `Cd` color | ✓ | ✓ | |
| `uv` (`f32[2]`) | ✓ | | ✓ |
| numbers | `ptnum`, `numpt` | `primnum`, `numprim` | `vtxnum`, `numvtx`, `ptnum` |
| measures | | `area()`, `center()`, `normal()` | |

Any other attribute is read and written through accessors named after its
type, as Houdini's `f@`, `v@`, `i@` prefixes do:

```luce
let m = p.f32("mass")            # 0 when the attribute does not exist
p.set_f32("mass", m * 2.0)       # writing creates it
p.set_vec3("velocity", [0.0, 1.0, 0.0, 0.0])
p.set_group("top", p.P[1] > 1.0)
```

The types are `f32`, `f64`, `i32`, `i64`, `vec2`, `vec3`, `vec4`. An
attribute that exists must be read as the type it has.

## Parameters, time and the detail

`k` is the node. A literal call makes a parameter row on the node, Houdini's
spare parameters from `ch()`. The row keeps its value while you edit the
code:

```luce
let amount = k.f32("amount", 0.25)          # a slider, 0.25 to start
let count = k.i32("count", 4)
let target = k.vec3("target", [0.0, 1.0, 0.0, 0.0])
```

A ramp (Houdini's `chramp`) is a curve or gradient you edit in the node's
parameters. Code reads it at any `t` from 0 to 1:

```luce
let falloff = k.ramp("falloff", d / radius)      # a float ramp
p.Cd = k.ramp_color("colors", p.P[1] / 2.0)       # a color ramp
```

`k.frame`, `k.time` and `k.fps` come from the timeline (`f64`). A node that
reads them recooks when the frame changes; other nodes don't. Detail
attributes are `k.detail_f32("name")` and the like. In Detail and Numbers
mode, write them with `k.set_detail_f32("name", v)`.

## Reading geometry

`k.input(0)` is the node's input as it was before the run; `k.input(1)` is
its second input (empty when nothing is connected). Both are read-only:

```luce
let g = k.input(0)
let near = g.nearpoints(p.P, 0.3, 8)          # up to 16 nearest, nearest first
var sum: f32[4] = [0.0, 0.0, 0.0, 0.0]
for i in 0..<near.count:
    sum = sum + g.point_P(near.points[i])
```

| Kind | Functions |
|---|---|
| Counts | `point_count()`, `prim_count()`, `bounds()` (`min`, `max`, `center`, `size`) |
| Attributes | `point_P(i)`, `point_f32(i, "name")` … `point_vec4`, `prim_f32(i, "name")` … `prim_vec4` |
| Topology | `prim_point_count(f)`, `prim_point(f, j)`, `point_prim_count(i)`, `point_prim(i, j)`, `neighbor_count(i)`, `neighbor(i, j)` |
| Nearest points | `nearpoint(P, maxdist)` (-1 when none), `nearpoints(P, maxdist, count)` |
| Surfaces | `xyzdist(P)`, `closest_prim(P)`, `closest_uv(P)`, `primuv_f32(f, uv, "name")`, `primuv_vec3(f, uv, "name")` (`"P"` gives the position) |
| Rays | `intersect(origin, direction)`: `prim` (-1 for a miss), `uv`, `position`, `distance` |
| Vertices | `vertex_prim`, `vertex_point`, `vertex_next`, `vertex_prev`, `prim_vertex_count`, `prim_vertex`, `point_vertex_count`, `point_vertex` |
| Half-edges | `hedge_next`, `hedge_prev`, `hedge_src_point`, `hedge_dst_point`, `hedge_prim`, `hedge_equiv_count`, `point_hedge(src, dst)`, `prim_hedge` |
| Neighbors and groups | `poly_neighbor_count`, `poly_neighbor`; `npointsgroup`, `nprimsgroup`, `expandpointgroup_count`/`expandpointgroup`, `expandprimgroup_count`/`expandprimgroup` |
| Measure | `getbbox_min`/`max`/`center`/`size`, `relbbox(P)`, `minpos(P)`, `computenormal(point)`, `primarclen`, `curvearclen`, `surfacedist(group, point)` (along edges), `windingnumber(P)` (about 1 inside a closed mesh, 0 outside) |

An index out of range fails the node, naming the element.

**Point clouds** (VEX's `pcopen`): `g.pcopen(P, radius, count)` finds up to
64 points, nearest first. `pc.count()`, `pc.point(i)`, `pc.distance(i)`,
`pc.f32(i, "name")` and `pc.vec3(i, "name")` read them, and
`pc.filter_f32("name")` / `pc.filter_vec3("name")` average them weighted by
distance (VEX's `pcfilter`). Smoothing is one line:

```luce
p.P = k.input(0).pcopen(p.P, 0.2, 20).filter_vec3("P")
```

`pcfind` is the same search; `pcfind_radius` keeps points whose own radius
attribute reaches.

**Volumes**: from an input made by SDF nodes, `volume_sample(name, P)`
(trilinear; an SDF itself is sampled exactly), `volume_sample_vec3`,
`volume_gradient(name, P)`, `volume_index(name, i, j, k)`,
`volume_pos_to_index`, `volume_index_to_pos`, `volume_res`,
`volume_voxel_size`. `""` names the first grid, or the SDF.

## Making and removing geometry

As in VEX, the changes queue up and apply after every run has finished, in
element order, so the result doesn't depend on threads:

```luce
let a = k.add_point([0.0, 1.0, 0.0, 0.0])     # its number, usable at once
k.remove_prim(f.primnum)
k.set_point_vec3(a, "Cd", [1.0, 0.0, 0.0, 0.0])
```

- `add_point(P) -> i32`, `add_prim(points: i32[16], count)` (a polygon of
  `count` of the points).
- `remove_point(i)` (its polygons go too), `remove_prim(i)` (its points
  stay).
- `set_point_f32(i, "name", v)` … `set_prim_vec4`: set any element's
  attribute. This wins over writes through `p`.
- One run may add at most 1024 elements.

Numbers mode with no input builds geometry from nothing; see the `spiral`
example. A new point's number is the run's number × 1024 plus its order
within the run, so run `n` can name the points run `n - 1` made.

## Functions

`math32` (`sin`, `cos`, `sqrt`, `floor`, `pi`, ...) and `math` (the same in
`f64`) are imported, and so is the kernel library:

| Family | Functions |
|---|---|
| Vectors | `dot`, `cross`, `length`, `length2`, `distance`, `distance2`, `normalized`; `dot2d`, `length2d`, `distance2d`, `normalized2d`; `f64` forms end in `64` |
| Ranges | `lerp`, `clamp`, `fit`, `fit01`, `smooth`, `degrees`, `radians` |
| Noise | `noise` (0 to 1, around 0.5) and `snoise` (-1 to 1), Perlin, in 1D (`noise1`), 2D, 3D and 4D, `f32` and `f64`; `pnoise` (periodic), `flownoise`, `noised`/`xnoised` (with the gradient), `curlnoise`/`curlnoise2d` (divergence-free), `onoise`/`anoise` (fractal), `wnoise` (Worley: `f1`, `f2`, `seed`), `mx_cellnoise` |
| Sampling | `nrandom`, `random_sobol`, `random_poisson`, `sample_circle_uniform`, `sample_direction_uniform`, `sample_sphere_uniform`, `sample_hemisphere`, `sample_direction_cone`, `sample_normal` |
| Random | `rand(seed)`, `rand3(seed)` (a vector), `rand_stream(seed, stream)`, all repeatable for the same seed |
| Math | `abs`, `sign`, `frac`, `rint`, `trunc`, `min`, `max`, `avg`, `sum`, `product`, `pow`, `exp`, `log`, `log10`, `cbrt`, `sinpi`/`cospi`/`tanpi`, `solvequadratic`, `solvecubic`, `distance_pointline`, `distance_pointsegment`, `distance_pointray`, `planepointdistance` |
| Matrices | `Mat3`, `Mat4`: `identity`, `rotation(angle, axis)`, `scaling`, `translation`, `multiply`, `transposed`, `determinant`, `inverted`, `transform`/`transform_point`/`transform_vector`, `rotate`, `scale`, `translate`; `maketransform`, `cracktransform`, `lookat`, `dihedral`, `polardecomp`. Row vectors as in VEX: `a.multiply(b)` applies `a` first |
| Quaternions | `Quat`, `quaternion(angle, axis)`, `qmultiply`, `qrotate`, `qinvert`, `slerp`, `eulertoquaternion`, `quaterniontoeuler` |
| Splines | `efit`, `fit10`, `fit11`, `invlerp`, `lspline`, `cspline`, `kspline`, `spline` (keys in an `f32[16]` with a count) |

Helper functions go in the **Header** below the code:

```luce
func fbm(at: f32[4], octaves: i32) -> f32:
    var sum: f32 = 0.0
    var scale: f32 = 1.0
    var weight: f32 = 0.5
    for i in 0..<octaves:
        sum += snoise(at * scale) * weight
        scale *= 2.0
        weight *= 0.5
    return sum
```

## What the language allows

The whole of Base's arithmetic, `if`/`elif`/`else`, `while` and `for` loops,
`match`, `let`/`var`, and casts like `(f32)k.time`. Left out are pointers,
memory allocation, threads, files and calling native code: anything that
could crash the editor. Code that uses them gets an error at its line.

## Texts and arrays

Texts are values of up to 256 bytes: `k.text("literal")`, `k.sprintf("quad_%d",
(f32)n)`, `k.itoa(n)`, or a text attribute (`p.text("name")`,
`g.point_text(i, "name")`). Their methods are `length`, `equals`, `startswith`,
`endswith`, `find`, `concat`, `replace`, `slice(start, end)` (negative counts
from the end), `split_count`/`split(sep, index)`, `join`, `to_i32`, and `to_f32`.
Write one with `p.set_text("name", t)` or `k.set_point_text(i, "name", t)`;
a face text named `name` drives groups downstream (`@name=quad_2`).

Arrays hold up to 64 numbers or vectors: `k.floats()`, `k.ints()`, `k.vectors()`,
then `append`, `insert`, `pop`, `remove`, `resize`, `reverse`, `slice`, `sort`,
`argsort`, `find`, `len`, `at` and `set`. They are values: a changed array is a new
one (`a = a.append(x)`). They live for one element's run; array attributes
(Houdini's `f[]@`) are not stored yet.

## Messages

`k.printf("point %d at %.2f\n", (f32)p.ptnum, p.P[0])` writes to the node's
console, shown under the code (the first 200 lines, in element order).
Up to four numbers are filled into `%d`, `%f`, `%e` and `%g`.
`k.warning("text")` gives the node a warning and lets it cook.
`k.error("text")` fails it at that line, naming the element.

## Errors

A typo or a type mismatch fails the node. The line is underlined in the
editor, and hovering it shows the message. So does an error while running,
such as an index out of range, a division by zero or an `assert`:
`line 7, column 3: index out of bounds (point 1204)` names the line and the
first element where it happened. Nothing partial gets through.

## Speed

The code is checked when you pause typing (about 0.1 ms) and turned into a
column program: each operation runs over thousands of elements at once, on
every core. On a million points, `p.P[1] += math32.sin(p.P[0] * 4.0) * 0.1`
runs in about 0.7 ms on an M4 Max. New parameter values and frames reuse
the program.
