# Gaussian splats in luced-3d

Research and design, 2026-10-09. No code was changed for this document. It answers the
owner's request to add a Gaussian splats context to luced-3d and to follow Houdini, where
splats became a first-class procedural citizen (Houdini 21 preview, Houdini 22 general
availability).

## 1. Decision in one page

**Representation.** Like Houdini, a splat cloud is the existing **points** component of a
GeometrySet with conventional point attributes. It is not a new component family. A cloud
is drawn as splats when it has `orient`, `scale` and `opacity`:

| Attribute | Type | Meaning |
|---|---|---|
| `P` | positions (f32 over f64 origin) | center |
| `orient` | f32 × 4, xyzw, unit | rotation (Houdini's order; PLY stores wxyz) |
| `scale` | f32 × 3 | standard deviations along the local axes, linear (PLY stores log) |
| `opacity` | f32 | linear 0..1 (PLY stores the logit) |
| `Cd` | f32 × 3 | color from the DC term, `0.5 + C0 · f_dc` |
| `sh` | ragged f32 × 3 (vec3 array) | SH bands 1..d, coefficient-major, RGB per item: 0, 3, 8 or 15 items |
| `restorient` | f32 × 4, optional | the orient the `sh` were authored in (Houdini's) |
| detail `gsplat_color_space` | text | `srgb` (trained captures, the default) or `linear` |

**Nodes.** Houdini's node names are mirrored where Houdini has a node. GSOPs (CG Nomads'
toolset) is the reference where Houdini has none. Every node is a luce-geocore set verb in
a new **GSplats** category:
- Bake GSplats
- Crop GSplats
- Clean GSplats
- Reduce GSplats
- GSplats SH Degree
- GSplats from Polygons
- GSplats to Volume
- Normals from GSplats

The existing File, Export, Transform, Merge, Blast and Code nodes learn splats.

**Formats.**
- **luce-ply** (new; PLY is general tech, used for meshes and scans too) reads and writes 3DGS PLY and PlayCanvas compressed PLY.
- **luce-spz** (new) reads and writes Niantic SPZ v2–v4 and the headerless `.splat`. It needs a zstd codec in luce-compress.
- **luce-usd** gains `ParticleField3DGaussianSplat`; its schema table already lists it.

**Viewport.** The renderer is luce-3d's `GaussianSplats`, modeled on FogVolume. It runs in three steps:
1. A compute pass projects, culls and evaluates SH for every splat.
2. A GPU LSD radix sort orders the splats by depth.
3. A hardware-rasterized draw renders one instanced quad per splat, back to front. It is depth tested against meshes but writes no depth, and blends with `Blend.over`.

The draw needs one new luce-gpu primitive: instanced quads pulled from a GPU buffer, with an indirect count.

The target is 3M splats at 60 fps and 6M at 30 fps or better, in a 2800×1800 viewport on the M4 Max.

**Code node.**
- Run Over Points learns point clouds; today it reads the mesh component only.
- `Point` gains the `orient`, `scale` and `opacity` fields.
- New accessors: `p.sh(i)` and `p.set_sh(i, v)`.
- New helper module `gsplat`: covariance, SH evaluation and rotation, sigmoid and logit.

## 2. What Houdini does

### 2.1 Version facts

| Version | What arrived | Source |
|---|---|---|
| 21.0 | **Bake GSplats SOP**: converts PLY attributes to "Houdini's GSplat Attributes" for Karma XPU. Its Karma notes say "this technique is currently a technical preview and not production-ready". SideFX's VP of Product called H21 "testing the waters": basic display, basic rendering, read only. | [bakegsplat](https://www.sidefx.com/docs/houdini/nodes/sop/bakegsplat.html), [H21 Karma](https://www.sidefx.com/docs/houdini/news/21/karma.html), [radiancefields H22](https://radiancefields.com/houdini-22-makes-gaussian-splats-a-first-class-citizen-—-rigging-relighting-and-reconstruction) |
| 22.0 (GA July 2026; no 21.5) | **ML Preprocess GSplats TOP** and **ML Train GSplats TOP**. **Rasterize GSplats COP** and the Camera COP. The **ML Train GSplats from Karma** recipe. SOP Import LOP writes USD `ParticleField3DGaussianSplat`. A noise-free Karma XPU algorithm. The viewport is over 40% faster, has initial shadow casting and receiving, adds a **GSplats Alpha Culling** display option and supports the USD GSplat schema. Splats deform with Bone Deform and Surface Deform. Animated splats play back in real time. | [H22 Karma](https://www.sidefx.com/docs/houdini/news/22/karma.html), [H22 ML](https://www.sidefx.com/docs/houdini/news/22/ml.html), [H22 Copernicus](https://www.sidefx.com/docs/houdini/news/22/copernicus.html), [H22 Solaris](https://www.sidefx.com/docs/houdini/news/22/solaris.html), [H22 viewport](https://www.sidefx.com/docs/houdini/news/22/viewport.html), [H22 product page](https://www.sidefx.com/products/whats-new-in-h22/gaussian-splats/) |
| 22.0 Labs (Aug 2026 update) | **Labs Delight GSplats SOP**, **Labs Normals from GSplats SOP**, **Labs Relight GSplats LOP** (1.0, 1.1) | [delight](https://www.sidefx.com/docs/houdini/nodes/sop/labs--delight_gsplats.html), [normals](https://www.sidefx.com/docs/houdini/nodes/sop/labs--normals_from_gsplats.html), [relight 1.1](https://www.sidefx.com/docs/houdini/nodes/lop/labs--relight_gsplats-1.1.html), [radiancefields platform page](https://radiancefields.com/platforms/sidefx) |

**Verified** in SideFX's documentation:
- every node named above, with its parameters (§2.3);
- the Bake GSplats attribute names;
- the alpha-culling option and its HOM calls (`hou.GeometryViewportSettings.gsplatsAlphaCulling()` and `setGsplatsAlphaCulling()`);
- the Karma environment variable `KARMA_XPU_GSPLATS_RENDER_MODE`, which reverts to the old mode.

**Not verifiable:**
- **The Houdini 21 release date.**
- **What "procedural cleanup nodes" means.** The H22 product page and press mention them, but no core SOP of that name is in the H22 SOP index. The cleanup appears to be Labs nodes, third-party HDAs (Nodeconnector's free cleanup HDA) and ordinary SOPs.
- **How the viewport sorts and rasterizes.** It is undocumented.
- **Whether `GS_SPH_*` include the DC term.** Sixteen floats for degree 3 suggests they do.
- **The SH color space after Linearize Color.**
- **Native `.spz` or `.splat` import.** Press coverage says GSOPs carries what the native toolset lacks, including `.splat` and `.spz` import. Native Houdini appears to read PLY only, through the File SOP.
- **VEX functions for splats.** The H22 VEX notes list none; the alpha-culling HOM calls are the only splat API.

### 2.2 Representation and attributes

> "GSplats are point clouds. When rendering, use the **Wireframe** mode to see the point
> clouds and use any shaded modes (like **Flat Shaded**) to see GSplats."
> ([Display Options](https://www.sidefx.com/docs/houdini/ref/windows/displayopts_3d.html))

The File SOP reads a PLY's properties as point attributes. **Bake GSplats** (H21) then
converts them, "BEFORE attempting to transform or otherwise manipulate them".

| Bake reads | | Bake writes | |
|---|---|---|---|
| `f_dc` | 3 floats | `Cd` | 3 floats (optionally linearized from sRGB) |
| `rot` | 4 floats, wxyz | `orient` | 4 floats, normalized (Houdini order xyzw) |
| `opacity` | logit, needs sigmoid | `GS_Alpha` | 1 float |
| `scale` | log, needs exp | `scale` | 3 floats |
| `f_rest` | 45 floats | `GS_SPH_R`, `GS_SPH_G`, `GS_SPH_B` | 16-float arrays per channel |
| | | `restorient` | 4 floats: "the original orientation for tracking successive transforms" |

Bake's inputs come in "vector or expanded form": either `f_dc[3]` or `f_dc_0`…`f_dc_2`. Its parameters are:
- Linearize Color;
- Compute GSplats;
- Compute SPH Coefficients;
- Delete Original Attributes;
- Disable Shadow Casting in Karma, which adds a detail attribute.

`restorient` is the key idea we adopt. Deformers (Transform, Bone Deform, Surface Deform)
rotate `orient` as they rotate any orient attribute and never touch the SH. The renderer
evaluates SH in the rest frame, rotating the view direction by
`orient · restorient⁻¹`. This is how Houdini rigs splats with stock deformers.

The COP rasterizer also reads `pscale` as a size multiplier, and accepts `Alpha` in place
of `GS_Alpha`.

### 2.3 Every Houdini splat node

| Node (context, version) | What it does | Main parameters |
|---|---|---|
| **Bake GSplats** (SOP, 21.0) | PLY attributes to Houdini's conventions (above) | Linearize Color, Compute GSplats, Compute SPH Coefficients, Delete Original Attributes, Disable Shadow Casting in Karma |
| **Rasterize GSplats** (COP, 22.0) | "Rasterizes point-based Gaussian Splats onto one or more layers": color and depth for compositing. Inputs: `camera_ref`, `gsplats` (from SOP Import COP), `mindepth`, `maxdepth`. Reads `P`, `Cd`, `GS_Alpha`/`Alpha`, `orient`, `scale`, `pscale`, `GS_SPH_R/G/B`. | Quick setups (Add Cd, Add Depth from Eye, Add Depth NDC, Move to Origin), Depth Conversion (Distance/Depth/Height), Border. Outputs `Cd`, `intrinsic:depth_eye`, `intrinsic:depth_ndc`. |
| **ML Preprocess GSplats** (TOP, 22.0) | Rendered EXRs, cameras and a point cloud into a COLMAP-like dataset (`images/`, `sparse/0/*.bin`, `pointcloud/points3d.ply`); one shared PINHOLE camera | camera source (metadata, file, SOP, LOP), point cloud from depth back-projection or a file, depth AOV, extra AOV features, smoothing, Python venv |
| **ML Train GSplats** (TOP, 22.0) | "Trains a 3D Gaussian Splatting model from a set of posed images" | Total Steps, Steps Scaler, SPH Degree Interval (raise the active SH degree every N steps), SPH and Color learning rates, densification Strategy **Default** (clone/split/prune) or **MCMC** with Cap Max GS, Refine Start/Stop/Every, position, opacity, scale, rotation and feature learning rates, SSIM Lambda (loss `(1-λ)·L1 + λ·SSIM`), opacity and scale L1 regularization, PLY/USD output and checkpoints |
| **ML Train GSplats from Karma** (LOP recipe, 22.0) | Camera array (Dome or Sphere) → Karma EXRs with depth/albedo/N AOVs → Preprocess → Train → Bake GSplats | camera distribution, render settings, training hyperparameters |
| **SOP Import** (LOP, 22.0 change) | Translates splats to USD `ParticleField3DGaussianSplat` | — |
| **Labs Delight GSplats** (SOP, 22.0) | Removes baked lighting and writes `albedo`, using bilateral illumination estimation over splat neighborhoods, with AO | Delight Amount, Light Blur Radius, Max Blur Points, Spatial Falloff Sigma, Edge Preservation Sigma, Chroma Influence, AO Amount/Radius, Crevice Shadow Lift, White Balance, Exposure, Gamma, Saturation |
| **Labs Normals from GSplats** (SOP, 22.0) | Reconstructs a VDB surface, transfers `N` back, optional KNN bilateral refinement. Second output: the surface mesh. | Point Separation, Surface Separation, Voxel Scale, Visualize Normals, Refine Normals, Search Radius, Smooth/Sharpen Amount |
| **Labs Relight GSplats** (LOP, 1.0/1.1) | PBR relighting with USD lights. Reads `albedo`, `metalness`, `specular`, `roughness`, `emission`, `emission_color`, `ao`; ray-traced shadows against an SDF; writes `Cd` and SH. | Camera, Enable Shadows, Auto Compute Self Shadows, Shadow Bias, base/specular/emission lobes, SPH Roughness/Specular Influence, SPH Env Spec Blend, Normal Softness, Diffuse Wrap |
| **Bone Deform, Surface Deform** (SOP) | Rig and deform splats as points, rotating `orient` | — |

Houdini has **no** native node for crop, filter, decimate, merge or SH rotation; these are
ordinary SOPs or third-party tools. **GSOPs** ([GitHub](https://github.com/cgnomads/GSOPs),
[node list](https://github.com/cgnomads/GSOPs/wiki/GSOPs-Nodes)) is the third-party set
that fills the gap: 30 nodes, Houdini 20.5–22. Its nodes include:
- `gaussian_splats_import`, which reads `.ply`, `.splat` and `.spz`;
- `gaussian_splats_export`;
- `gaussian_splats_transform`, which rotates the SH;
- `gaussian_splats_crop`;
- `gaussian_splats_dbscan`, for outlier removal;
- `gaussian_splats_reduce`, a decimator modeled on NanoGS;
- `gaussian_splats_mirror`, which keeps the SH valid;
- `gaussian_splats_deform`;
- `gaussian_splats_from_polygons`, which makes splats with no training;
- `gaussian_splats_bake`, which converts splats to points, mesh and density volumes;
- `gaussian_splats_histogram`;
- `gaussian_splats_hald_clut`;
- `gaussian_splats_relight_ibl`;
- `gaussian_splats_convert`, which converts between GSOPs' conventions and Houdini 21's native ones;
- `vdb_from_gaussian_splats`;
- `gaussian_splats_visualize_boxes`.

GSOPs cannot train.

### 2.4 Display and rendering

- **Viewport (Vulkan only since H22).** Shaded modes draw splats; wireframe draws centers.
  - GSplats Alpha Culling (Optimize tab) culls splats under a threshold "to improve performance". An over-high default culled real detail, as a [forum thread](https://www.sidefx.com/forum/topic/102417/) shows; it was fixed in a daily build.
  - H22 adds initial shadows and claims 23M-splat scenes.
  - The sort and raster method is not documented.
- **Karma XPU** renders splats; Storm and Karma CPU show colored points.
  - H21's renders were noisy and slow to resolve.
  - H22 uses "a noise-free algorithm", with SH support and relighting.
- **USD.** OpenUSD 26.03 added `UsdVolParticleField3DGaussianSplat` ([schema](https://openusd.org/dev/user_guides/schemas/usdVol/ParticleField3DGaussianSplat.html), [SH API](https://openusd.org/dev/user_guides/schemas/usdVol/ParticleFieldSphericalHarmonicsAttributeAPI.html)):
  - `positions` (point3f/h), `orientations` (quatf/h), `scales` (float3/half3) and `opacities` (float/half);
  - `radiance:sphericalHarmonicsDegree` and `radiance:sphericalHarmonicsCoefficients` (float3[], (d+1)² per particle, DC included; missing data means DC (0.5, 0.5, 0.5));
  - the hints `projectionModeHint` (perspective or tangential) and `sortingModeHint` (zDepth or cameraDistance).

  The schema page does not state whether opacity is linear and scale is not log. Check that against the `hdParticleField` reference renderer before writing USD.

## 3. Technical core (references)

### 3.1 The model (Kerbl et al. 2023)

Kerbl, Kopanas, Leimkühler, Drettakis, *3D Gaussian Splatting for Real-Time Radiance
Field Rendering*, ACM TOG 42(4), SIGGRAPH 2023.

**Each splat** has a center μ, covariance Σ = R S Sᵀ Rᵀ (R from a unit quaternion, S =
diag(scale)), opacity α and view-dependent color c(d) from real SH of degree ≤ 3.

**Projection (EWA, Zwicker et al. 2002).**
- Σ′ = J W Σ Wᵀ Jᵀ, where W is the view rotation and J the perspective Jacobian at the center: `[[fx/z, 0, −fx·x/z²], [0, fy/z, −fy·y/z²]]`.
- The reference code clamps x/z and y/z to 1.3 × tan(fov/2) before J.
- It adds a 0.3 px² low-pass to Σ′'s diagonal.
- The screen radius is ⌈3·√λmax⌉.
- Mip-Splatting (Yu et al., CVPR 2024) instead multiplies α by √(det Σ′ / det(Σ′ + 0.3 I)). This is gsplat's and SPZ's "antialiased" flag.

**Blending.** Splats are sorted by view depth and blended front to back: C = Σ cᵢ αᵢ Πⱼ<ᵢ(1 − αⱼ), where αᵢ = min(0.99, o·exp(−½ dᵀ Σ′⁻¹ d)). A splat is skipped when αᵢ < 1/255, and a pixel stops when transmittance falls below 10⁻⁴.

**SH (degree 0–3; constants from the reference code).** With d = normalize(μ − camera) in the frame the SH were trained in:

```
C0 = 0.28209479177387814
C1 = 0.4886025119029199
C2 = [1.0925484305920792, -1.0925484305920792, 0.31539156525252005, -1.0925484305920792, 0.5462742152960396]
C3 = [-0.5900435899266435, 2.890611442640554, -0.4570457994644658, 0.3731763325901154,
      -0.4570457994644658, 1.445305721320277, -0.5900435899266435]
c  = C0*k0
   - C1*y*k1 + C1*z*k2 - C1*x*k3
   + C2[0]*x*y*k4 + C2[1]*y*z*k5 + C2[2]*(2zz-xx-yy)*k6 + C2[3]*x*z*k7 + C2[4]*(xx-yy)*k8
   + C3[0]*y*(3xx-yy)*k9 + C3[1]*x*y*z*k10 + C3[2]*y*(4zz-xx-yy)*k11
   + C3[3]*z*(2zz-3xx-3yy)*k12 + C3[4]*x*(4zz-xx-yy)*k13 + C3[5]*z*(xx-yy)*k14
   + C3[6]*x*(xx-3yy)*k15
color = max(c + 0.5, 0)
```

The color is in the space the training images were in: sRGB-encoded for captures. Our
`Cd` stores `0.5 + C0·k0`, so the shader adds bands 1..3 to `Cd`.

**Rotating SH** (Transform, Mirror, export after a deform): band l transforms by a
(2l+1)×(2l+1) real Wigner D-matrix. Band 1 is a permuted 3×3 rotation, and bands 2 and 3
follow from Ivanic–Ruedenberg recurrences. A reflection negates the coefficients that are
odd under it. SPZ's coordinate conversions and GSOPs' Transform and Mirror do exactly this.

**Related work for later stages.**

| Work | What it adds |
|---|---|
| StopThePop (Radl et al., SIGGRAPH 2024) | per-pixel sorting that removes popping |
| 3DGRT (Moenne-Loccoz et al., SIGGRAPH Asia 2024) | ray tracing splats through proxy BVHs |
| 3DGUT (Wu et al., CVPR 2025) | unscented-transform rasterization, for distorted cameras and secondary rays |
| MCMC densification (Kheradmand et al. 2024) | Houdini's MCMC training strategy |

### 3.2 Formats

**3DGS PLY** (INRIA reference; `binary_little_endian 1.0`, one `vertex` element, float32):

```
x y z  nx ny nz (usually zero)  f_dc_0..2  f_rest_0..44  opacity  scale_0..2  rot_0..3
```

- `opacity` is a logit, so α = sigmoid.
- `scale_*` is the log of σ.
- `rot_*` is a quaternion **w, x, y, z**, not necessarily normalized.
- `f_rest` is **channel-major**: `f_rest[c·15 + i]` is coefficient i + 1 of channel c (the reference transposes (N, 15, 3) to (N, 3, 15) before flattening).
- Lower degrees have 0, 9 or 24 `f_rest` properties.
- A full degree-3 splat is 62 floats, 248 bytes.

**PlayCanvas compressed PLY** (SuperSplat): a `chunk` element per 256 splats holds min/max
bounds. The `vertex` element packs into u32s: position 11/10/11 bits, rotation
smallest-three 2+10/10/10, scale 11/10/11 and color RGBA 8 each. An optional `sh` element
holds u8 `f_rest`. That is about 16 bytes per splat without SH.

**`.splat`** (antimatter15/splat; no header): 32 bytes per splat.

| Bytes | Field |
|---|---|
| 0..11 | position, f32 × 3 |
| 12..23 | scale, f32 × 3, linear |
| 24..27 | RGBA, u8: RGB = clamp((0.5 + C0·f_dc)·255), A = sigmoid(opacity)·255 |
| 28..31 | rotation, u8 × 4: w, x, y, z as q·128 + 128 |

There is no SH. Converters order splats by size × opacity, largest first.

**SPZ** (Niantic, [spec](https://github.com/nianticlabs/spz)):
- **Header.** Versions 1–3 are a gzip stream starting with a 16-byte header: magic `NGSP` (0x5053474e), version, numPoints, shDegree, fractionalBits, flags (bit 0: antialiased) and a reserved byte.
- **v4 container.**
  - A 32-byte plaintext header adds numStreams and tocByteOffset.
  - Extension records follow when flag 0x2 is set.
  - Then come a table of contents of (compressed, uncompressed) u64 sizes and **independently zstd-compressed attribute streams**.
- **Encodings.**
  - Positions are 24-bit signed fixed point with `fractionalBits` fractional bits.
  - Alpha is a u8 sigmoid.
  - Color is u8 per channel, f_dc scaled by 0.15·255 around 127.5.
  - Scale is u8 log, as (ln σ + 10)·16.
  - Rotation in v3–v4 is the smallest three components as 10-bit signed integers plus a 2-bit index; v2 used 8-bit x, y, z with w derived.
  - SH are u8, coefficient-major with RGB interleaved, quantized to `sh1Bits` (default 5) and `shRestBits` (default 4).
- **Coordinates.** Files are in RUB (OpenGL and three.js). Sixteen named systems convert by 90° turns, which include SH rotation.
- **Size.** A splat takes about 10× less than in PLY.

### 3.3 Sorting and rasterization

**Tile rasterization** (the 3DGS reference; gsplat, Ye et al. 2024, JMLR 2025):
1. Preprocess each splat: project, cull, take the radius and evaluate SH.
2. Duplicate each splat once per 16×16 tile it touches, with a 64-bit key (tile id << 32 | depth).
3. Run one global GPU radix sort (CUB).
4. Each tile's thread block walks its range front to back, with early termination.

This gives exact per-tile order and suits training, which needs gradients. It costs
duplicated keys (often 5–10× the splat count) and a full compute rasterizer.

**Global depth sort + hardware quads** (antimatter15, SuperSplat/PlayCanvas, Spark, most engines):
1. Sort splat indices once per view by center depth.
2. Draw an instanced quad per splat, back to front, with premultiplied over-blending.

- **The vertex stage** takes the 2D covariance's eigenvectors and spans ±k·√λ along them.
- **The fragment stage** evaluates the Gaussian.

Hardware blending does the compositing, and depth testing against meshes is free.

**Sorting in those viewers.**
- antimatter15 sorts on a CPU worker with a 16-bit counting sort: about 150 ms per 1M splats, so sorting runs about 4×/s, behind the frames.
- Spark ([system design](https://sparkjs.dev/docs/system-design/)) reads distances back from the GPU and bucket-sorts them on a worker. Its splats pack to 16 bytes, and splat edits run on the GPU through its `dyno` shader graphs.
- SuperSplat sorts on a CPU worker too.

On desktop GPUs a full GPU radix sort of 32-bit keys is cheap.

**Radix sort portability.** Onesweep (Adinets & Merrill 2022) needs forward-progress
guarantees that Metal does not give. A reduce-then-scan LSD sort (FidelityFX Parallel Sort
style: count, scan, scatter per pass) is portable. Of the speed tricks:
- quantizing the view depth of visible splats to 16 bits needs two 8-bit passes instead of four;
- re-sorting only when the view changes saves work at rest;
- a tight quad bound `√(2·ln(255·α))·σ` in place of 3σ cuts fill;
- culling by α < 1/255 removes splats outright;
- level of detail is used past about 10M splats.

## 4. Our codebase today (what the design builds on)

**luce-geocore**:
- `geometry_set/set.lucb`: a GeometrySet holds at most one component per family, through `ComponentType` function tables (share, close, size, bounds, placed, joined, filtered, describe…). At most 64 families.
- `points.lucb`: `PointCloud` has f32 positions over an f64 origin and an `AttributeStore`. **`place_cloud` moves positions only**: it shares every attribute untransformed, unlike `detail.lucb`, which honors roles.
- **Attributes** (`core/attributes.lucb`) are 1–4-wide tuples of bool, i8, i32, i64, f32, f64 or text. Storage is array, single or **ragged**, Houdini's `f[]@` and `v[]@`. Roles are generic, position, vector, normal, color, uv and index; **there is no quaternion role and no f16 type**.
- **Set verbs** (`set_verbs/`): 24 verbs in `set_makers`. Each has a `SetVerb` with ParmSpec rows and a cook over `SetVerbInput`. The node catalog is generated from `VerbCatalog` (mesh verbs, then set verbs), so a new set verb is a new node with no luced-3d code.
- **Codec** (`geometry_files/`): `.prism` crates hold every component and attribute, ragged ones included. Other packages register codecs per family.
- **Code node** (`src/code/`): Run Over Points, Vertices, Primitives, Detail, Numbers, Voxels. `run_code` binds `set_mesh(set)`. **A set with only a point cloud passes through untouched**: point clouds are not yet a Run Over target. Array attributes are bound with at most 64 items.

**luce-gpu**:
- **Compute** (`Kernel`, `Compute` passes): storage buffers, 32-bit int atomics, float atomics on Metal 3, subgroup ops (32 wide on Apple), `dispatch_indirect`, storage images and timestamps. Every command sees what earlier ones wrote, and a frame submitted after a pass sees its results.
- **Client fragment shaders** run through `shade`, `shade_instances` (up to 1,048,576 instance rects, data copied from the CPU) and `shade_triangles` (CPU clip-space vertices). **The vertex stage is always luce-gpu's.**
- `draw_mesh` already does vertex pulling from up to seven buffers, but with built-in shaders.
- `Pipeline.create(..., depth_test = true)` tests without writing depth (added for fog, luce-gpu d785d33).
- `Blend.over` is premultiplied.
- **There is no indirect draw.**
- Ray queries use triangle BLASes only.

**luce-3d**: FogVolume (c4feaab) is the pattern to copy:
- the data is built once on the CPU and uploaded on first draw;
- shaders are embedded by `tools/shaders.sh` (luce-gpu's `embed_shaders.py`);
- a shared per-device pipeline cache;
- `draw(camera, target)`;
- a pixel test with a GPU-time report (`tests/fog_pixels`).

**luced-3d** threads fog through every layer, and splats follow the same path:
- `compute_worker.luc` builds the data keyed by `(stamp, "fog", …)`;
- `display_publisher.luc` holds FogVolumes by key so each uploads once;
- `viewport_batches.luc` holds the displayed list;
- `view.luc` draws after meshes, lines and the grid;
- `geometry_data.luc` caches it for local cooks.

Point clouds are **not drawn** in the viewport at all today.

**luced-3d files**:
- `.prisma` projects store recipes;
- the Cache node writes `.prism` through the geometry codec;
- File loads by extension in `node_evaluation.load_geometry` (obj, fbx, step) and `usd_nodes`;
- Export writes usd, obj, fbx and prism by extension.

**luce-render**: wavefront path tracer over triangles, with a software BVH or ray queries;
the shadow rays are any-hit and opaque only. It has no point or volume primitives yet.

**luce-compress**: deflate, gzip, zlib, brotli, lz4 and zip. **No zstd.**

**luce-usd**: the schema table already lists every `ParticleField*` API; there is no conversion yet.

## 5. Representation

### 5.1 Recommendation: points plus conventions, not a new component

| | Point cloud + conventions (recommended) | New `gsplats` component family |
|---|---|---|
| Houdini parity | Same model ("GSplats are point clouds") | Diverges |
| Existing nodes | Merge, Blast, Attribute*, Code, Cache, spreadsheet and groups work on day one, or as soon as they learn clouds, which every point workflow needs anyway | Each needs a splat path |
| Deformers | Rotate `orient`, keep `restorient` | Custom |
| Compact storage | f32 on CPU, compact only on the GPU | Could quantize in place |
| Mixed data | Splats and plain points cannot share one set (one points component) | Can coexist |

A dedicated family would duplicate the point machinery for a memory saving that only
matters on the GPU, where we pack anyway. The one real loss, splats and plain points in
one set, matches Houdini, where a set of points either has the splat attributes or does
not.

### 5.2 Conventions (geocore `src/splats/conventions.lucb`)

A cloud **is a splat cloud** when it has point attributes `orient` (f32 × 4), `scale`
(f32 × 3) and `opacity` (f32). The other attributes are as in §1:
- `Cd` defaults to 0.5 gray;
- `sh` is absent at degree 0;
- `restorient` is absent when `orient` is the SH frame.

**Why these choices:**
- **Houdini's names where they are general.** `Cd`, `orient`, `scale` and `restorient` are Houdini's, and its quaternion order xyzw matches geocore's future `Quat`.
- **`opacity` over `GS_Alpha`.** `opacity` is the 3DGS and USD name and fits our lean-name rule. Import accepts `GS_Alpha` and `Alpha` (open question Q1).
- **One `sh` array over three per-channel arrays.** It is one ragged column, not three.
  - Its layout matches the GPU, USD and SPZ: per point, coefficient-major, RGB interleaved, bands 1..3, m = −l..l.
  - It excludes DC, which lives in `Cd`, so plain point tools that recolor `Cd` keep working.
  - The degree follows from the item count: 0, 3, 8 or 15. Every point of a cloud has the same count; Bake and Merge enforce it.
- **Linear opacity and scale.** These are what tools and wrangles want; PLY's logit and log are file details.
- **The color stays as trained.** `Cd` and `sh` keep the file's numeric values, so export round-trips exactly. The detail `gsplat_color_space` says how to read them: `srgb` for captures, `linear` for splats made from linear renders (luce-render, the Karma recipe's analogue). The display shader evaluates SH in that space and then decodes to linear before blending. Houdini's "Linearize Color" instead rewrites `Cd` only, which leaves the SH bands in the old space.
- **New role `Role.rotation`** (quaternion) for `orient` and `restorient`, so every transform rotates them. `scale` stays generic. Splat-aware placement handles scale, below.

### 5.3 Transforms

- **`place_cloud` honors roles**, as `detail.lucb` already does: positions, vectors, normals and now rotations. This fixes plain clouds too.
- **For a splat cloud, placement is covariance-exact.**
  - Each splat takes Σ′ = M Σ Mᵀ, where M is the 3×3 part.
  - Σ′ is eigendecomposed into `orient` and `scale`, with a closed-form symmetric 3×3 solver in Base.
  - `restorient` is written first, as a copy of `orient`, if absent.
  - A rigid or uniform M takes the cheap path: q′ = q_M · q and s′ = s·|scale|.
- **A reflection (det M < 0)** cannot live in `orient` versus `restorient`. Placement reflects the `sh` items directly, with sign flips per band and parity, and normalizes so `orient` stays a proper rotation.
- **Export bakes the frame**: it rotates `sh` by `orient · restorient⁻¹` (Wigner D) and drops `restorient`.

### 5.4 Memory

| | Bytes per splat (degree 3) | 1M | 6M |
|---|---|---|---|
| CPU, ours | P 12 + orient 16 + scale 12 + opacity 4 + Cd 12 + sh 180 + sh offsets 4 = **240** (+16 with `restorient`) | 240 MB | 1.44 GB |
| PLY on disk | 248 | 248 MB | 1.49 GB |
| GPU, static | center f32 × 3, covariance f16 × 6, Cd+opacity f16 × 4, SH f16 × 45 = **122**, padded to 128 | 128 MB | 768 MB |
| GPU, per view | projected quad 32 + keys/values 2 × 8 (ping-pong) = **48** per visible splat | 48 MB | 288 MB |

The ragged column's offsets cost 4 bytes per splat, under 2%. A later "uniform ragged" flag
(offsets implied by a fixed count) would remove them without an API change. GPU SH can drop
to u8 with a per-cloud scale, about 45 bytes, if 10M+ scenes need it. The M4 Max has
unified memory and these sizes fit.

## 6. Nodes

Each node is a set verb in a new geocore file, `set_verbs/splat_verbs.lucb`, with the
kernels in `src/splats/`. They appear in the menu under **GSplats** through VerbCatalog.
Houdini names are used where Houdini has a node, and GSOPs names otherwise.

| Node | Houdini / GSOPs | Geocore verb and kernel | Main parameters |
|---|---|---|---|
| **Bake GSplats** | Bake GSplats (H21) | `bake_gsplats_verb`, `splats/bake.lucb` | Source attributes: Auto (PLY `f_dc_*`/`rot_*`… or vector forms; Houdini `GS_*`), Points (from `pscale`/`Cd`: isotropic splats). Opacity default, Color Space (sRGB/linear), Keep SH Degree (0–3), Delete Original Attributes. Writes §5.2. |
| **Crop GSplats** | GSOPs crop | `crop_gsplats_verb` | Shape (Box, Sphere, Bounds of second input), center/size or radius, Invert, Keep Partially Inside (by 3σ extent). Works on any cloud. |
| **Clean GSplats** | Procedural cleanup (H22), GSOPs dbscan | `clean_gsplats_verb`, `splats/clean.lucb` | Min Opacity, Max/Min Scale (world or relative to median), Max Anisotropy, Remove NaN/degenerate, Outliers: k-NN statistical (k, σ multiplier), later DBSCAN (ε, min points). Outputs a group or deletes. |
| **Reduce GSplats** | GSOPs reduce | `reduce_gsplats_verb`, `splats/reduce.lucb` | Target (count or ratio), Method: Importance (keep the largest opacity × volume) or Merge (pairwise moment matching: merged μ, Σ and opacity-weighted color and SH, over a k-NN graph, greedy by cost). |
| **GSplats SH Degree** | Bake's "Compute SPH" | `sh_degree_verb` | Degree 0–3: truncate bands, or pad zeros. |
| **Transform, Mirror, Copy to Points** | Transform, GSOPs transform/mirror | existing placement, splat-aware (§5.3) | — |
| **Merge** | Merge | existing `join_clouds`, splat-aware | Pads `sh` to the larger degree; `restorient` defaults to `orient`; color space must agree (warns). |
| **Blast / Delete, Attribute nodes, Group** | — | existing, extended to clouds where they are mesh-only | — |
| **GSplats from Polygons** | GSOPs from_polygons | `gsplats_from_polygons_verb` | Density (splats per unit area), Thickness (normal σ as a fraction of the tangent σ), Color from `Cd` or a texture, Opacity. Disc splats aligned to faces: sample the surface, tangent frame to `orient`. |
| **GSplats to Volume** | GSOPs bake (density), Houdini Normals (VDB) | `gsplats_to_volume_verb` into `fields` | Voxel Size, Grid Name, Density Scale. Splats each Gaussian's opacity-weighted density into a SparseGrid (fog). Feeds FogVolume display, `Convert to Mesh` and level-set tools: splats to mesh is GSplats to Volume then Convert to Mesh. |
| **Normals from GSplats** | Labs Normals from GSplats (H22) | `normals_from_gsplats_verb` | Method: Shortest Axis (fast: the axis of the smallest scale, oriented away from the local k-NN centroid) or Surface (through GSplats to Volume, a level set, gradient). Refine (k-NN smoothing), Search Radius. Writes `N`. |

**As built (stage 7).** The three conversions are luce-geocore set verbs (`set_verbs/splat_conversions.lucb`).
- **GSplats from Polygons** (`splats/from_surface.lucb`): Density, Size (0: 0.6/√density, so neighbors overlap), Thickness, Opacity, Color (without a `Cd`), Seed, Keep Input. Discs land on the display triangles, density × area each, the fraction and the points drawn from a hash of the seed, so a cook is the same on any thread count. `Cd` comes from the mesh's point, vertex or primitive `Cd`, and `N` is the face normal. No texture lookup yet.
- **GSplats to Volume** (`fields/splat_density.lucb`, in fields because it builds a grid): Voxel Size (0 sizes it to the capture since stage 8: about 256³ voxels across the extent between the 1st and 99th percentiles, never finer than the median largest σ; the median alone made 8M-point meshes of whole captures), Density Scale, Cutoff (σ, default 3), Keep Input, and the grid's Name in the text row. Each Gaussian is widened by half a voxel, so sub-voxel splats still land, and normalized so its voxels integrate to its mass, opacity · (2π)^{3/2} σ₁σ₂σ₃. Inside the cutoff its peak is therefore about 3% high at 3σ. On the 1.16M-splat bonsai capture at 0.05 voxels, the volume takes 0.44 s and Convert to Mesh (isovalue 0.2) 0.31 s, giving 4.6M faces. On the bonsai alone (cropped to 124k splats, 0.01 voxels), the volume takes 55 ms and the mesh 30 ms, 172k faces.
- **Normals from GSplats** (`splats/normals.lucb`, `orientation.lucb`): Houdini's fast idea, the shortest axis, with Search Radius, Refine Normals, Smooth Amount, Sharpen Amount and Visualize Normals.
  - Each splat's side is first voted by its 16 nearest neighbors' centroid.
  - That vote points inward in concave regions; a bumpy ball showed inward patches. So the sides then propagate over a minimum spanning tree of 1 − |aᵢ·aⱼ| over the symmetric k-NN graph (Hoppe et al. 1992), and each connected part faces the way the sum of its votes says.
  - Refine is a bilateral k-NN blend.
  - The Surface method and Houdini's second output, the surface mesh, are GSplats to Volume then Convert to Mesh.
  - The full bonsai capture takes 1.7 s; the spanning tree is sequential.

| **Edit GSplats** (later) | SuperSplat's brush/lasso | an Edit-node kind (`edit_kinds.luc`) | Viewport selection of splats by brush, lasso or box over projected centers, then delete, separate, or recolor and opacity. The steps are stored as point-id groups. |
| **Delight / Relight GSplats** (later) | Labs Delight, Labs Relight | `splats/light.lucb` | After luce-render splats (§9); Delight's bilateral filter needs only k-NN and is independent. |
| **Train GSplats** | ML Train GSplats TOP | not planned | Q5 |

## 7. Formats: luce-ply, luce-spz, luce-usd

Following the owner's rule that formats own their read and write, each package returns or
takes a GeometrySet whose cloud follows §5.2, and owns the decode from its convention.
Shared math (sigmoid, logit, C0, quaternion normalize and smallest-three, Wigner D for SPZ
coordinate conversion) comes from `luce_geocore.splats`, so the packages depend on
geocore as luce-obj does.

### luce-ply (new package)

PLY is general technology: scans, meshes and point clouds.
- **Reader**: ascii and binary LE/BE headers, any elements and properties, and lists for faces.
- **Mesh path**: `vertex` plus `face` gives a Mesh with properties as point attributes.
- **Splat path**: when the `vertex` element carries `f_dc_0`, `rot_0`, `scale_0` and `opacity`, it decodes straight to the convention: sigmoid, exp, wxyz to xyzw normalized, channel-major `f_rest` to interleaved `sh`, and `Cd = 0.5 + C0·f_dc`. Unknown properties stay as attributes.
- **PlayCanvas compressed PLY**: read, and write later.
- **Writer**: the 3DGS layout (degree from `sh`, `restorient` baked in), or a generic layout for meshes and clouds.
- **Fast path**: a fixed-stride binary body decodes in parallel blocks on the luce-std pool. Reading is memory-bound; the target is at least 1 GB/s on the M4 Max.

Without a separate Bake step, a `.ply` dropped on a File node displays as splats at once
("remove repeated typing"). Bake GSplats remains for clouds made by other means.

### luce-spz (new package)

- **SPZ**: read v1–v4 and write v4, or v3 when zstd is unavailable. The flags carry the antialiased setting (stored as detail `gsplat_antialiased`, which the display honors). Positions are 24-bit fixed point with an explicit `fractionalBits` choice on write (default 12). Coordinate systems convert to Y-up right-handed, our viewport's, by the 90° rotations with SH rotation.
- **`.splat`**: read and write; 32-byte records, no SH, `srgb`.
  - It is too small for its own package. Keeping it here, as "the compact splat formats", is a judgment call (Q4).
- **As built (stage 6):** luce-spz reads SPZ and `.splat` into a 3DGS PLY's raw names and RDF axes, exactly what luce-ply gives for a PLY (SPZ's RUB, or the system its Adobe coordinate extension names, converted as Niantic's loader does for a PLY), so the File node bakes them the same way (Up Axis Y Down, `gsplat_up_axis`) and a capture loads identically from either format. Saving unbakes a baked cloud; a `y_down` cloud goes back to RDF and is converted to RUB, others are Y-up already. The encoder matches Niantic's packer byte for byte, and decoding then encoding gives a file's streams back.
- **zstd**: SPZ v4 needs a zstd codec, which goes in **luce-compress**, general technology like brotli. The decoder (RFC 8878) is needed for reading; the encoder can be a simple greedy level 1–3 at first. Test vectors come from the RFC and the zstd repository's decode corpus, ported as tests and never copied.

### luce-usd

Add `convert/particle_fields.lucb`:
- **Read**: `ParticleField3DGaussianSplat` (and the generic ParticleField with the Gaussian kernel), half and float variants, SH (d+1)² with DC split into `Cd`, gives a cloud.
- **Write**: the reverse, with `sortingModeHint` and `projectionModeHint` passed through as detail attributes.

The opacity and scale conventions must be checked first (§2.4). This is Houdini 22's SOP to
LOP path.

- **Checked (stage 7):** the schema's text leaves the SH convention open, but OpenUSD's own reference code settles it, and luce-usd matches it. Coefficient 0 is 3DGS's raw DC, the PLY's `f_dc` (color 0.5 + C0 · c₀), and bands 1–3 are `f_rest` with 3DGS's order and signs, one RGB item per coefficient. Opacities are linear, scales linear σ, and orientations GfQuatf (stored imaginary first, printed real first). Sources in the OpenUSD repository: `extras/imaging/examples/hdParticleField/py3dgsPlyToUsd.py` (f_dc written as coefficient 0, f_rest transposed, sigmoid and exp applied), `gsRenderer.cpp` (C0 · c₀ + 0.5; "DC (0.5, 0.5, 0.5)" filled as (0, 0, 0)) and `third_party/renderman/shaders/SphericalHarmonicsToColor.osl`. Autodesk's arnold-usd and LichtFeld Studio agree. Houdini 22 is said to put a degree-0 color in `primvars:displayColor` instead (arnold-usd's notes); reading that is open. Export now also writes `interpolation = "vertex"` and `elementSize = (d + 1)²` on the coefficients, as Pixar's converters do and Omniverse's validator expects, and a cloud stood up from a Y-down file carries the custom `luce:gsplatUpAxis` (named like `luce:gsplatColorSpace`), which import turns back into `gsplat_up_axis`, so a later PLY export turns it back down.

### File and Export nodes

- `load_geometry` gains `.ply`, `.spz` and `.splat`.
- Export gains the same.
- Both join the import cache (`SourceCache`), keyed like OBJ.

## 8. Viewport renderer

### 8.1 Shape

**luce-3d `renderers/gaussian_splats.lucb`**: `GaussianSplats`, following FogVolume.
- `GaussianSplats.of(geometry, matrix)` packs the static GPU buffers (§5.4) in Base, on the compute worker, once per content key. `count(geometry)` says whether a set has a splat cloud.
- `draw(camera, target, settings)` uploads on the first draw. Each frame it then:
  1. records a compute pass (§8.2) when the view or settings changed;
  2. records one quad draw.
- A shared per-device cache holds the kernels and pipelines, like `fog_pipeline`.

**luced-3d** adds a `splats` list beside `volumes`, in four places:
- `compute_worker.display`, keyed by `(stamp, "splats", …)`;
- `DisplayPublisher.held_splats`;
- `ViewportBatches.splats`;
- `GeometryData.splat_cache`.

`view.luc` draws splats after meshes, lines and the grid, and before fog.

### 8.2 Per-frame GPU work

All of it is one `Compute` pass submitted before the frame records the draw.

1. **Project** (`splat_project.comp`, one thread per splat).
   - Transform the center, then cull against the frustum with a 3σ guard and α < cull threshold.
   - EWA Σ′ with the 1.3 tan clamp, the 0.3 low-pass and, when antialiased, the opacity compensation.
   - Compute the eigenvectors and the quad half-axes at `√(2 ln(255 α))·√λ`, capped at 3√λ and a maximum pixel size.
   - Evaluate SH at the view direction rotated into the rest frame (`orient · restorient⁻¹`, precomputed per splat at pack time as a per-splat SH-frame quaternion only when `restorient` exists), add `Cd`, then decode sRGB to linear when `gsplat_color_space` says `srgb`.
   - Append a 32-byte record: clip-space center and depth f32 × 3; the two pixel half-axes f16 × 4; RGBA f16 × 4, premultiplied later.
   - Write a key (view depth as a monotonic u32; or 16 bits over the visible depth range, two passes) and a value (the record index). An atomic counter yields the visible count and the indirect arguments.
2. **Sort** (`splat_sort_count/scan/scatter.comp`): LSD radix, 8 bits per pass, reduce-then-scan, sized by the indirect visible count, no forward-progress assumption. Keys sort back to front.
3. **Draw** (new luce-gpu primitive, §8.3): instanced quads in sorted order with the client fragment shader `splat.frag`. It takes the local quad coordinates (u, v), computes `α = opacity · exp(−½(u² + v²)·k²)`, discards α < 1/255, clamps to 0.99 and outputs premultiplied color. The pipeline uses `Blend.over` and `depth_test = true` without depth writes, so meshes occlude splats and splats veil meshes behind them, as fog does.

**Re-sorting and multiple clouds.**
- When the camera is still and nothing changed, the last sorted order is reused. Only step 3 runs.
- **Several displayed clouds** sort in one combined pass: the packed buffers concatenate per view, with a per-cloud matrix index, so splats from different nodes interleave correctly. The first version sorts per cloud, which is enough for one cloud and wrong only where clouds overlap.

### 8.3 What luce-gpu needs

The vertex stage belongs to luce-gpu, and `shade_triangles` and `shade_instances` take CPU
data, which is far too slow at millions per frame. One general addition serves splats,
particles and billboards alike:

- **`shade_quads(target, pipeline, quads: Buffer, order: Buffer?, count: Buffer, count_offset, uniforms?, images?, filter)`** draws instanced quads whose records live in a GPU buffer, optionally through an index buffer, with the instance count read from the GPU (Metal `drawPrimitives` with indirect arguments; Vulkan `vkCmdDrawIndirect`). Each record is clip center xyzw and two clip-space half-axes. The fragment shader gets quad coordinates at location 0, as `shade_triangles` passes them in the vertex color, and the record's extra data flat at locations 1..3.

luce-gpu is shared, so the request goes to its owner with a small pixel test.

**Plan B without it.** A compute tile rasterizer, gsplat style, writes an rgba16f storage
image, which is composited with `draw_image`. Everything stays inside luce-3d, but splats
lose per-pixel occlusion with meshes, because compute cannot read the frame's depth. Use
it only if the primitive is refused.

### 8.4 Display options

These live in the shading menu or a splat display block:
- **Mode**: Splats (shaded), Centers (points, which wireframe shows, as Houdini does), Ellipsoids (GSOPs' visualize boxes: instanced low-poly spheres through draw_mesh, for picking and inspection).
- **Alpha Culling** threshold: default 1/255, never higher by default (Houdini's lesson, §2.4).
- **SH Degree cap** 0–3: lower is faster.
- **Splat Scale** multiplier.
- **Max splat size** in pixels, for navigation.

Plain point clouds, which are not drawn today, use the Centers mode through the same
`shade_quads`.

### 8.5 Performance target and budget

**Target:**
- **3M splats**: at least 60 fps (16 ms) in a 2800×1800 viewport on the M4 Max.
- **6M** (the size of Mip-NeRF 360 bicycle or garden captures): at least 30 fps.
- **Camera at rest**: draw only.

**Budget:**
- **Project**: about 128 bytes read per splat, about 0.8 GB at 6M, about 2 ms at the M4 Max's bandwidth.
- **Sort**: 4 passes over 8-byte pairs, about 1–2 ms at 6M; 16-bit keys halve that.
- **Raster**: the remainder, dominated by overdraw, which the tight quad bound and α culling reduce.

These are estimates to measure, not measurements. Stage 3 reports GPU times per step with
`Compute.timestamp`, as `tests/fog_pixels` reports fog.

**Beyond about 10M splats:** a level-of-detail hierarchy built at cook time (clusters of
merged splats, as Reduce GSplats' Merge method makes them), chosen per frame by screen size.

## 9. luce-render (later)

luce-render is a triangle path tracer with opaque any-hit shadows. Faithful splat rendering
there would take three things:
1. **Primitives.** An AABB (procedural) BLAS in luce-gpu, which Metal and Vulkan ray queries both support with procedural candidates. Today's BLAS is triangles only. The fallback is 3DGRT's stretched-icosahedron proxies, at 20 triangles per splat, which is too heavy at 6M.
2. **A k-buffer traversal.** Following 3DGRT, collect the k nearest Gaussian hits per segment at the point of maximum response along the ray, composite them, and continue. It needs no sort and gives correct secondary rays: shadows, reflections, refraction.
3. **Shading.** Splats are emissive radiance as captured (SH evaluated at the ray direction). Relit splats would use `albedo` and `N` from Delight and Normals from GSplats, as Houdini's Labs Relight does.

The cheaper first step is primary visibility only, composited with the path-traced frame by
depth, which is what H21's Karma preview amounted to. This is stage 9, after everything
interactive.

## 10. Code node

**Prerequisite: Run Over Points over a point cloud.**
- `run_code` takes the points component when the set has no mesh, or always under a new Run Over menu choice: "Points (cloud)" versus mesh points, Q6.
- Positions, attributes, groups, and add or remove points apply to the cloud.
- `build_layout` already abstracts columns. The edits path needs a cloud variant of `applied`.
- **Decided (stage 6 follow-up):** a run over a cloud gives a cloud back, and polygons a snippet adds (`k.add_prim`) become a mesh beside it, over copies of the points they use. The cloud keeps every point, so a splat cloud stays drawn as splats when a snippet adds faces to it; a set holding a mesh and a cloud is the representation §5.1 already allows. `p.orient` reads the identity (0, 0, 0, 1) on points without one.

**Stubs** (`src/code/stubs.lucb`), on `Point`:

```luce
## Rotation, xyzw (Houdini's @orient); identity without one.
pub var orient: f32[4]
## Per-axis size (σ), lane 3 zero (@scale); writing creates it.
pub var scale: f32[4]
## Linear opacity 0..1 (3DGS's sigmoid of the PLY logit).
pub var opacity: f32
## SH coefficient `i` (0..<sh_count, bands 1..3 in order), RGB in lanes 0..2.
pub func sh(i: i32) -> f32[4]
pub func set_sh(i: i32, value: f32[4])
## 0, 3, 8 or 15.
pub func sh_count() -> i32
```

A helper module **`gsplat`** goes in the kernel library, beside Mat3, Mat4 and Quat:
- `gsplat.covariance(p) -> Mat3` and `gsplat.set_covariance(p, m)` (eigendecomposition into orient and scale);
- `gsplat.color(p, direction) -> f32[4]` (the SH evaluation of §3.1, rest frame applied);
- `gsplat.rotate_sh(p, q)` (Wigner D, in place);
- `gsplat.sigmoid(x)` and `gsplat.logit(x)`;
- `gsplat.rest(p) -> Quat` (`orient · restorient⁻¹`).

Examples for `examples/wrangles/`:

```luce
# Fade splats out above a height.
p.opacity *= 1.0 - math32.smoothstep(1.0, 2.0, p.P[1])
```

```luce
# Squash every splat along world Y (a non-uniform scale done through the covariance).
let s = Mat3.scaling([1.0, 0.2, 1.0, 0.0])          # hypothetical helper name
gsplat.set_covariance(p, s * gsplat.covariance(p) * s)
```

```luce
# Desaturate the view-independent color, keep the view-dependent bands.
let g = (p.Cd[0] + p.Cd[1] + p.Cd[2]) / 3.0
p.Cd = [g, g, g, 0.0]
```

## 11. Files and caches

- **Projects (`.prisma`)** store recipes as now: a File node keeps its path, and splats are never embedded.
- **Caches (`.prism`)** need nothing new. The points codec writes every attribute, the ragged `sh` included, losslessly, at about 240 bytes per splat. An optional compact cache can come later, if 6M-splat caches (about 1.4 GB) prove too large: a Cache node option writing f16 attributes, once the codec gains f16 columns.
- **Imports** are cached by path, size, mtime and hash in `SourceCache`. A 6M-splat PLY parses once per session.
- **Exports** by extension: `.ply` (3DGS), `.spz`, `.splat`, `.usd*` (ParticleField) and `.prism`.

## 12. Build order

Each stage lands on main with its tests green under `luc test`, per the test and release
model. Stages 1–3 are the minimum to load and look at a capture.

| Stage | Work | Tests |
|---|---|---|
| **1. Geocore foundation** | `src/splats/`: conventions, detection, sigmoid and logit, SH evaluation, Wigner D bands 1–3 and reflection, symmetric 3×3 eigensolver, covariance compose and decompose. `Role.rotation`. `place_cloud` honoring roles and splat-exact placement. Splat-aware `join_clouds`. **Bake GSplats** and **GSplats SH Degree** verbs. | SH evaluation against fixed reference values. Rotation invariance: evaluating rotated SH at a rotated direction equals the original, for random rotations, per band. Reflection likewise. Decompose(compose(q, s)) round trips up to sign and order. A rigid placement equals the general path. Merge pads degrees. Bake from PLY-named attributes. |
| **2. luce-ply** | Package with reader and writer (generic plus the 3DGS path, parallel binary decode). File and Export wiring. | Ascii, binary LE and BE fixtures. A 3DGS round trip is bit-exact. Channel-major to interleaved SH against a hand-built file. A 1M-splat read time is reported. |
| **3. Viewport** | luce-gpu `shade_quads` with indirect count (pixel test on Metal and Vulkan). luce-3d `GaussianSplats`: pack, project, radix sort, draw; display options. luced-3d wiring (worker, publisher, batches, view); Centers mode for all clouds. | `tests/splat_pixels`: one Gaussian's pixels against the analytic falloff; two overlapping splats in both depth orders; a mesh occluding splats and splats veiling a mesh. The GPU sort against a CPU sort on random keys, including ties and the empty case. Timings at 1M, 3M and 6M synthetic splats and on a real capture, reported per step. Windows and Linux runs over ssh. |
| **4. Core nodes** | Crop, Clean and Reduce GSplats. Blast, Delete, groups and attribute nodes on clouds. | Crop counts on known layouts. Clean thresholds. Reduce hits the target count and keeps total opacity-weighted mass and centroid within a tolerance. A viewport screenshot compares before and after on a capture. |
| **5. Code** | Run Over Points on clouds. `orient`, `scale`, `opacity`, `sh` bindings. The `gsplat` helpers. Three example scenes. | Wrangle results against the same edits done in geocore. Faults name the point. A 1M-splat opacity edit is timed. |
| **6. More formats** | zstd in luce-compress. luce-spz (SPZ v1–v4 and `.splat`). luce-usd ParticleField read and write. | RFC 8878 and zstd corpus vectors. Niantic sample files decode within quantization error of their PLY sources. Coordinate-system conversions keep SH evaluations equal. A USD round trip. |
| **7. Conversions** | GSplats from Polygons, GSplats to Volume (then the existing Convert to Mesh), Normals from GSplats. | A plane makes coplanar discs. Volume density integrates to the splat mass. Normals on a sphere capture point outward (and on a torus, concave on its inner ring). |
| **8. Interaction and scale** | Edit GSplats (brush, lasso, box selection). Combined multi-cloud sort. LOD past about 10M. Optional per-pixel sort quality mode (StopThePop). | Selection matches on synthetic layouts. Two interleaved clouds composite correctly. LOD frame time at 20M. |
| **9. Rendering and light** | luce-gpu AABB BLAS. luce-render splat k-buffer tracing. Delight GSplats and Relight GSplats. | A render matches the viewport (primary only) within noise. Shadows from splats onto a mesh. |

Training (Houdini's ML Train GSplats) is not on this list; see Q5.

## 13. Open questions for the owner

1. **Names.** Should splat attributes use `opacity` and one interleaved `sh` array (recommended), or Houdini's exact `GS_Alpha` and `GS_SPH_R/G/B`, which would make files from Houdini load as is? Either way, import accepts both.
2. **Color.** Should splats stay in their trained (sRGB) values, with the display decoding (recommended, exact round trips), or be linearized at import as Houdini's Bake option does?
3. **luce-gpu.** Is `shade_quads` (indirect, buffer-fed instanced quads) the right general addition, and who builds it: this session or the luce-gpu owner?
4. **Packages.** Should we create luce-ply and luce-spz, with `.splat` inside luce-spz, and zstd in luce-compress? Or should `.splat` go elsewhere?
5. **Training.** Houdini trains through Python (TOPs) with a venv. Do we want training at all? It would need autodiff kernels on luce-gpu, close to the paused luce-nn work. Or do we accept trained files from outside, as Houdini does for camera solving?
6. **Code on clouds.** Should Run Over Points pick the cloud automatically when there is no mesh, or should a mesh and a cloud in one set need an explicit choice?
7. **Mixed sets.** Splats and plain points cannot share one set (one points component). Is that acceptable, as in Houdini? A second component family would allow it at the cost of §5.1's duplication.

## Sources

**SideFX:**
- [Bake GSplats](https://www.sidefx.com/docs/houdini/nodes/sop/bakegsplat.html)
- [Rasterize GSplats COP](https://www.sidefx.com/docs/houdini/nodes/cop/rasterizegsplats.html)
- [ML Train GSplats TOP](https://www.sidefx.com/docs/houdini/nodes/top/ml_traingsplats.html)
- [ML Preprocess GSplats TOP](https://www.sidefx.com/docs/houdini/nodes/top/ml_preprocessgsplats.html)
- [ML Train GSplats from Karma](https://www.sidefx.com/docs/houdini/ml/train_solutions/ml_traingsplatsfromkarma.html)
- [Labs Delight GSplats](https://www.sidefx.com/docs/houdini/nodes/sop/labs--delight_gsplats.html)
- [Labs Normals from GSplats](https://www.sidefx.com/docs/houdini/nodes/sop/labs--normals_from_gsplats.html)
- [Labs Relight GSplats 1.1](https://www.sidefx.com/docs/houdini/nodes/lop/labs--relight_gsplats-1.1.html)
- What's new in H22: [Karma](https://www.sidefx.com/docs/houdini/news/22/karma.html), [viewport](https://www.sidefx.com/docs/houdini/news/22/viewport.html), [ML](https://www.sidefx.com/docs/houdini/news/22/ml.html), [Copernicus](https://www.sidefx.com/docs/houdini/news/22/copernicus.html), [Solaris](https://www.sidefx.com/docs/houdini/news/22/solaris.html)
- [H21 Karma](https://www.sidefx.com/docs/houdini/news/21/karma.html)
- [Display Options](https://www.sidefx.com/docs/houdini/ref/windows/displayopts_3d.html)
- [H22 Gaussian Splats product page](https://www.sidefx.com/products/whats-new-in-h22/gaussian-splats/)
- [Forum: GSplat quality in the Vulkan viewport](https://www.sidefx.com/forum/topic/102417/)

**Press:**
- [radiancefields: H22 first-class splats](https://radiancefields.com/houdini-22-makes-gaussian-splats-a-first-class-citizen-—-rigging-relighting-and-reconstruction)
- [radiancefields: H22 ships](https://radiancefields.com/houdini-22-ships-making-native-gaussian-splats-generally-available)
- [radiancefields: SideFX platform page](https://radiancefields.com/platforms/sidefx)
- [CG Channel: H22 sneak peek](https://www.cgchannel.com/?p=176344)

**Third party:**
- [GSOPs](https://github.com/cgnomads/GSOPs) and [its node list](https://github.com/cgnomads/GSOPs/wiki/GSOPs-Nodes)
- [GSOPs 3.0 notes](https://radiancefields.com/cg-nomads-adds-houdini-22-support-and-gaussian-splat-baking-in-gsops-3.0.0)

**Formats and standards:**
- [OpenUSD ParticleField3DGaussianSplat](https://openusd.org/dev/user_guides/schemas/usdVol/ParticleField3DGaussianSplat.html)
- [OpenUSD SH API](https://openusd.org/dev/user_guides/schemas/usdVol/ParticleFieldSphericalHarmonicsAttributeAPI.html)
- [OpenUSD 26.03 note](https://radiancefields.com/openusd-26.03-adds-native-gaussian-splat-support)
- [Niantic SPZ](https://github.com/nianticlabs/spz)

**Viewers:**
- [antimatter15/splat](https://github.com/antimatter15/splat)
- [Spark system design](https://sparkjs.dev/docs/system-design/)

**Papers:**
- Kerbl et al. 2023 (3DGS)
- Zwicker et al. 2002 (EWA splatting)
- Yu et al. 2024 (Mip-Splatting)
- Ye et al. 2024 (gsplat)
- Radl et al. 2024 (StopThePop)
- Moenne-Loccoz et al. 2024 (3DGRT)
- Wu et al. 2025 (3DGUT)
- Kheradmand et al. 2024 (3DGS as MCMC)
- Adinets & Merrill 2022 (Onesweep)

## 14. Owner decisions (2026-10-09)

1. **Names:** ours: `orient`, `scale`, `opacity`, `Cd`, one `sh` array; import also accepts Houdini's `GS_Alpha` / `GS_SPH_*`.
2. **Color:** linearize at import, as Houdini's Bake option does. `Cd` is linear like every other `Cd`, and export converts back to the file's convention. The detail `gsplat_color_space` records what the file had, so a round trip restores it.
3. **Training:** not now; splats trained elsewhere are imported.
4. **Packages:** as designed. luce-ply and luce-spz are new, zstd goes in luce-compress, and `shade_quads` goes in luce-gpu, built by this session.
5. **Defaults taken for Q6–Q7:** Run Over Points picks the cloud when the set has no mesh. Splats and plain points don't share a set, as in Houdini.
6. **Up axis (stage 4):** Bake GSplats' Up Axis defaults to **Y Down (COLMAP)**. COLMAP's cameras look down +Z with +Y pointing down and a reconstruction keeps the first camera's frame, so a capture shot upright has its up near -Y. Checked on the Mip-NeRF 360 bonsai: the flattest axis of its dense splats is (0.13, 0.80, 0.59), the floor's sharp cutoff lies on its + side, so up is near -Y (the capture is also tilted about 36°, which no default fixes). The turn is exact (a half turn about X; `splats/axes.lucb` in luce-geocore), recorded in `gsplat_up_axis`, and undone on export.

## 15. Stage 8 as built (2026-10-09)

**Edit GSplats** (luced-3d `edit_gsplats.luc`, `splat_select.luc`; luce-geocore `SplatEdits`, `splats/footprints.lucb`, `splats/edits.lucb`). Houdini 22 has no node of this name; it edits splats as points with its usual point tools and selection shapes. This node gathers them on the Edit framework, as Edit Mesh does for polygons:
- Levels: Object (the whole cloud) and Splats. Edges and faces are missing.
- Selection: a drag selects with a box, a lasso or a brush. Q pressed again while Select is active cycles the shape, and [ and ] size the brush. Shift adds and Ctrl removes. A click is a dab.
- A splat is selected where its footprint (the EWA ellipse out to where its Gaussian falls to the footprint alpha, 0.1) meets the shape, not only by its center. Selection goes through the depth, as SuperSplat's does.
- The selection is tinted on the drawn cloud (luce-3d `set_marks`). No point markers are drawn.
- Tools: Delete, Recolor (Cd toward a color, the SH faded by as much) and Opacity (multiply or set). The QWERT gizmo moves, rotates and scales, each splat's orient, scale and SH frame exactly. Every edit is a recipe step on groups of the pick mesh.
- On the 1.16M-splat bonsai: a box selection takes 13 ms, a brush update about 11 ms, and a Recolor step 0.2 s.

**One sort for all clouds** (luce-3d `SplatScene`, `renderers/splat_view.lucb`). Every displayed cloud and instance takes a run of slots in one index space. Each cloud is projected into its slots, then one gather and one radix sort order them all. Interleaved clouds now composite in depth order: `tests/splat_pixels` checks this from both sides, and drawing the clouds apart fails the same check.

**Level of detail** (luce-3d `renderers/splat_lod.lucb`).
- Clouds of 2^20 splats or more are packed in Morton order. One merged, moment-matched splat is appended per run of 4, 16, 64 and 256 splats.
- Per view, the coarsest merged splat whose 3σ footprint is under 2 pixels stands in for its run. This engages once the clouds drawn number 10M or more.
- On a 20M-splat field 200 units across, at 2800×1800 on the M4 Max:
  - from eye level: 37 ms without LOD, 33 ms at 2 px and 17 ms at 4 px;
  - from overhead: 29 ms without LOD, 22.5 ms at 2 px and 7 ms at 4 px.
- At 2 px the images match the full draw within noise.

**Not done:** the StopThePop per-pixel sort (optional).

