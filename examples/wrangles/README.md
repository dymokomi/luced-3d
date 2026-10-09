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
