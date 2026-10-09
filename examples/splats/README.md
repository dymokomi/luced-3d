# Gaussian splat examples

Code node scenes for Gaussian splat clouds. Open one with File > Open and
select a Code node to see its code and the parameters its `k.f32(...)`
calls made.

Each scene starts from the same synthetic capture, built in the scene so no
file is needed: a Sphere's points are jittered and colored warm to cool by
a Code node, baked into splats by **Bake GSplats** (Source: Points), given
SH degree 1 by **GSplats SH Degree**, and given a view-dependent sheen by a
Code node writing the first band with `p.set_sh`. Run Over Points runs over
a point cloud when the input has no mesh, so `p` is a splat. Replace the
first nodes with a File node on a `.ply` capture to edit a real one.

`tests/examples/main.luc` builds these; every Code node must cook without
an error, and the program writes these files again.

| Scene | What it shows |
|---|---|
| `fade_by_height` | Splats fading out above a height: `p.opacity` scaled down along a smooth ramp between the Start and End parameters. |
| `recolor` | The view-independent color desaturated (`p.Cd`, the DC term) while the SH bands, the view-dependent part, stay as they are. Amount blends toward gray. |
| `squash` | Every splat flattened along world Y through its covariance: `gsplat.set_covariance(p, S · gsplat.covariance(p) · S)` with `S = Mat3.scaling([1, squash, 1])`, decomposed back into `orient` and `scale`. |

The splat members of `p` are `orient` (x, y, z, w), `scale` (σ per axis),
`opacity` (linear), `sh(i)`, `set_sh(i, v)` and `sh_count()`. The `gsplat`
module adds `sigmoid` and `logit`, `rotation` and `rest` (the SH frame),
`covariance` and `set_covariance`, `color(p, direction)` (the color the
splat shows along a view direction), `rotate_sh` and `rotate`.
