# Frame grid and polygon area scaling

Local checkpoint after [grazing cells](CAD_GRAZING_CELLS_2026-09-28.md).
The camera frame now accepts a clipped grid. This fixes its fallback and
improves sampled accuracy; it does **not** finish the crowded-row work.

## Causes and changes

Frame patch 2358 (`Camera - 6/Frame`, six coedges, NURBS support) first failed
while constructing the planar clipped UV mesh, before lifting to the surface.
A valid thin triangle had cross-product magnitude 4.8065e-13. Polygon face
normals used generic vector normalization, whose absolute 1e-12 cutoff rejected
it despite polygon triangulation's extent-relative degeneracy test.

`luce-3d` now applies the same scale-aware area policy to Newell face normals in
direct polygon construction and `MeshBuilder`: max(1e-30, extent² * 1e-14).
Generic vector normalization is unchanged. This is not tolerance inflation or
a promise of unit invariance throughout the CAD pipeline.

The lifted frame also contained a failed grazing cell occupying 1.84% of a
valid neighbor's UV area. The previous 1% merge candidate cap excluded it.
The cap is now one eighth. All other safeguards remain: one internal manifold
side, no extra touching vertices, at most 256 union corners and 32 merges,
fixed trim identities and positions, positive actual display normals, and the
same sampled surface-deviation check. This is a merge policy, not a relaxation
of geometric error. Unsafe candidates still roll back.

## Visual and numerical result

Matched native shaded-wire captures, isolated only after the full production
cook, at 4400 × 2604 pixels:
[before](preview_camera_frame2358_before.png),
[grid](preview_camera_frame2358_grid.png),
[assembled](preview_camera_frame2358_assembled.png).
Isolated captures use neutral inspection lighting; the assembled view retains
normal scene materials. Actual polygon wires, normals and depth are displayed.

| Frame 2358 | Before | After |
|---|---:|---:|
| Quads | 42 | 1,890 |
| Triangles | 742 | 3 |
| Cut n-gons | 0 | 104 |
| Strategy | Constrained | Clipped grid |

The grid still has 224 quads with edge ratio above 20 (maximum 428.84).
Visible double/triple rows come from overlapping stations on smooth flow rails,
not simply a remaining G0 classification override. This is the next spacing
target; deleting required incoming rows independently would break continuity.

## Verification

- Polygon regression: 96 concave-polygon scale/translation/plane/winding cases,
  tiny non-collinear UV wedge acceptance, collinear rejection, analytic area,
  direct/builder normal agreement, and allocation cleanup. Full 3D Base/Luce
  suite passes native optimization modes 0–3 and C debug/release.
- Merge candidate tests accept 2% and 10% neighbors and reject 25%, in both
  windings. Existing exact-boundary and global triangulation regressions pass.
- Full application suites pass native opt-2 and C release.
- Full camera: 615,219 points; 576,990 polygons (526,327 quads, 15,211 triangles,
  35,452 n-gons). Only patch 2358's polygon result changes from the preceding
  checkpoint. All 2,710 patches have zero display-normal flags. Native/C agree
  on every patch's counts, method and flags.
- Zero open, nonmanifold or inconsistently oriented edges; Euler 46.
  Actual display area 65,662.63065530368; signed volume 74,392.99417907407.
  Observed full native cook 8.16 s; this is not a controlled speed comparison.
- Fixed 4,096 OBJ-to-STEP samples: maximum 0.0259126 (previously 0.0297543),
  mean square 4.65839e-6 (previously 5.55978e-6). The worst reference sample
  now belongs to glass-lens patch 49, not frame 2358.
- STEP-to-OBJ: max 0.0212007, mean square 4.51958e-6. These sample locations
  change with the mesh, so this is not a like-for-like improvement measure or
  a Hausdorff certificate.
- `sign`, `1p5inR`, `33mm_angle`: unchanged counts and zero topology flags;
  Euler -30, 2 and 0 respectively.
- Release app rebuilt in 18 s; native `--smoke` exits 0.

No fixture-specific meshing branch, moved trim, hidden polygon edge, compiler
change or luce-tesselator change is retained. Kernel work remains local and
unpublished. Forty-four constrained camera patches and other dense/poorly
spaced regions still need inspection.

Records: `/private/tmp/polygon-scale-full.log`,
`/private/tmp/frame-grid-full-{native,c}.log`,
`/private/tmp/camera-frame-grid-{quality.txt,c-quality.txt,topology.log,delta.log}`,
`/private/tmp/{sign,1p5inR,33mm_angle}-frame-grid.log`,
`/private/tmp/luced-frame-grid-{build,smoke}.log`.
The delta log contains temporary diagnostic output from an otherwise identical
geometry run; this instrumentation was removed before final suites and build.
