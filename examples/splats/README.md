# Gaussian splat examples

Scenes for Gaussian splat clouds: Code node edits, and the conversions
between splats and meshes. Open one with File > Open and
select a Code node to see its code and the parameters its `k.f32(...)`
calls made.

Each scene starts from the same synthetic capture, built in the scene so no
file is needed: a Sphere's points are jittered and colored warm to cool by
a Code node, baked into splats by **Bake GSplats** (Source: Points), given
SH degree 1 by **GSplats SH Degree**, and given a view-dependent sheen by a
Code node writing the first band with `p.set_sh`. Run Over Points runs over
a point cloud when the input has no mesh, so `p` is a splat. Replace the
first nodes with a File node on a `.ply` capture to edit a real one.

`tests/examples/main.luc` builds every scene here; every Code node must cook without
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

## Conversions

The conversion scenes start from a sphere bumped by noise along its normals,
concave in places,
and colored warm to cool by height (a Code node), instead of the synthetic
capture.

| Scene | What it shows |
|---|---|
| `from_polygons` | **GSplats from Polygons**: splats with no training. Flat discs are scattered over the mesh at 3000 per unit of area, each in its triangle's plane, sized to overlap its neighbors (σ = 0.6/√density across, a tenth of that through) and colored by the mesh's `Cd`. |
| `splats_to_mesh` | Splats back to a mesh. **GSplats to Volume** sums the splats' Gaussians into a fog volume (voxel 0.02) whose integral is the splats' mass, and **Convert to Mesh** surfaces it where the density is 0.3. The discs are made half as thick as wide, so the density across the surface is smooth. |
| `splat_normals` | **Normals from GSplats** with Visualize Normals on: each splat's shortest axis, its side voted by its neighbors' centroid and agreed over a spanning tree of the neighbor graph, so the concave dents face out too, then refined. The colors show `N`. |

On a real capture, replace the first nodes with a File node on a `.ply`,
`.spz` or `.splat` file. Clean GSplats first (Max Scale) keeps the huge
background splats out of GSplats to Volume, and its Voxel Size of 0 uses the
splats' median size.

## Lighting and rendering

| Scene | What it shows |
|---|---|
| `splat_relight` | The ball's splats (their `Cd` standing in for a capture's lit colors) get normals (**Normals from GSplats**), lose their light into `albedo` (**Delight GSplats**), and are lit again by a low sun from the side (**Relight GSplats**): diffuse and a highlight baked into `Cd` and the SH, shadowed through the splats' density. |
| `splat_shadows` | Splats and meshes in one render: the ball's splats on a floor beside a sphere, under an area light, through a camera into a **Render** node (press Render). luce-render traces the splats as 3D Gaussian Ray Tracing does: they emit their colors (the floor takes on their glow), shadow the floor and the sphere, and let what is behind show through their thin edges. |
