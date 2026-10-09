# Code node examples

Scenes after classic Houdini wrangle tutorials, each built with Code nodes
(Luce Base code written for one element and run for all of them in
parallel). Open one with File > Open. Select a Code node to see its code
and the parameters its `k.f32(...)` calls made. Press Play (or ↑) on the
timeline for the animated ones.

`tests/examples/main.luc` builds them; every Code node must cook without
an error, and the program writes these files again.

| Scene | What it shows |
|---|---|
| `sine_wave` | A grid rolling as a sine wave along X, moving with time (`k.time`), with frequency, speed and amplitude parameters. |
| `ripple` | Rings spreading from the center and fading with distance, animated. |
| `noise_sphere` | A sphere pushed in and out by `snoise` that drifts with time. |
| `color_by_height` | Noise hills, then a second Code node coloring them with `fit` and `lerp` from blue valleys to white peaks. |
| `twist` | One Code node wraps a grid into a tube; a second twists it about Y, more with height, and bulges it. |
| `random_prim_colors` | Running over Primitives: each face colored `rand3` by its number and a seed parameter. |
| `jitter` | Points moved by a random offset each, seeded by `p.ptnum`. |
| `attractor` | Points pulled up toward a target (a vector parameter), the pull fading with distance in the ground plane; the color shows the pull. |
| `checker` | Running over Primitives: a checkerboard from each face's `f.center()`. |
| `terrain` | Fractal terrain: the header defines `fbm`, a loop of noise octaves; the body raises the grid by it; a second node colors by height; a Detail node writes the octave count as a detail attribute. |
| `million_points` | A 1000 × 1000 grid (a million points) moved by animated noise and colored by height. Press Play to watch it run every frame. |
| `spiral` | Geometry from nothing: Numbers mode with no input, each `n` adding two points (`k.add_point`) and the quad to the previous pair (`k.add_prim`). Count, turn and rise are parameters. |
| `holes` | Faces deleted at random (`k.remove_prim`), Houdini's delete-by-condition. |
| `distance_color` | A grid colored and dipped by its distance to a sphere in the **second input** (`k.input(1).xyzdist`). |
| `projection` | A flat sheet dropped onto noise terrain in the second input by a ray down from each point (`k.input(1).intersect`). |
| `smoothing` | A rough noise blob smoothed by three Code nodes, each averaging every point with its nearest neighbors in the input (`k.input(0).nearpoints`, `point_P`): a point-cloud blur. |
| `ramps` | Houdini's `chramp`: a float ramp (`k.ramp`) shapes a volcano's profile by distance from the center and a color ramp (`k.ramp_color`) paints it by height. Edit the ramps in the node's parameters. |
| `matrix_twist` | A tube squared off and twisted by a rotation matrix per point (`Mat3.rotation(...).transform(...)`). |
| `cells` | Worley cells (`wnoise`): each region a random color, darkened and dipped toward the borders (`f2 - f1`). |
| `curl_flow` | A grid carried through a divergence-free flow (`curlnoise`) in a loop of small steps; the color shows how far each point traveled. |
| `inside_outside` | A grid lifted and colored where it lies inside a sphere in the second input (`windingnumber`). |
| `surface_distance` | Bands of color by distance along the surface from two seed points (`surfacedist` over a group the first node marks). |
| `pc_smooth` | Point-cloud smoothing in one call: `k.input(0).pcopen(p.P, radius, 20).filter_vec3("P")`, VEX's pcfilter, two passes. |
| `shrink_wrap` | A grid wrapped onto a signed distance field in the second input, stepping each point back along the field's gradient by its distance (`volume_gradient`, `volume_sample`). |
| `console` | A Detail run printing the input's size to the node's console (`k.printf`) and warning when it is large (`k.warning`). Select the Code node to read it. |
| `names` | Texts: faces named by quadrant (`k.sprintf`, `f.set_text`), colored by the number read back from the name (`slice`, `to_i32`), and one quadrant deleted downstream by a Blast of `@name=quad_2`. |
| `median` | Arrays: spiky terrain cleaned by the median height of each point's neighborhood across the grid's edges (`k.floats`, `append`, `sort`), which drops spikes a mean would only smear. |
| `neighbor_lists` | Array attributes, Houdini's `i[]@nbrs` idiom: one node stores each point's neighbors as an i32 array (`p.set_i32_array`), three later nodes read the lists back (`p.i32_array`) to average heights. The lists show in the Geometry Spreadsheet. |
| `gyroid` | Volume Wrangle (Run Over Voxels): a Volume node makes an empty level set, the Code node writes a gyroid shell cut to a ball (`math32.max` of two distances, an intersection), Convert to Mesh shows its surface. |
| `metaballs` | Five spheres orbiting with time, joined by a smooth minimum the header defines (`smin`), written per voxel and meshed. Press Play. |
| `noise_cloud` | A fog volume: density from noise octaves, fading toward the edge, drifting with time (the classic Volume Wrangle cloud). The viewport draws fog as smoke. |
| `eroded_points` | Volume from Points makes a level set of a sphere's points; a Voxels Code node adds noise to each voxel's distance (`x.value`), and Convert to Mesh shows the eroded rock. |
