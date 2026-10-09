# Editor fixtures

`triangle.obj`, `plane.step`, `cylinder.step` and `assembly.step` are original
minimal fixtures for the File node, worker, cache and Group tests;
`instancer.usda` (a point instancer with two prototypes, from luce-usd's
fixtures) and `room.usda` with its payload `room_lamp.usda` (a variant set,
a payload and two instances, also luce-usd's) are the USD File node's.
`instancing.fbx` (eight models sharing one mesh) is ufbx's
`blender_293_instancing_7400_binary.fbx` (MIT; see luce-fbx's
tests/fixtures/UFBX-LICENSE.txt), and `skinned.fbx` (ufbx's
`maya_dq_weights_7500_binary.fbx`, an animated dual quaternion skin) are the
FBX File node's. The format packages
keep their own fixtures (FBX: luce-fbx; STEP: luce-step). `step_skip.step`
(two unit squares on a plane, the second with a corner 0.1 above it, so no
mesher follows it) checks the tessellation's skipped-face warning.
`quad.ply` (an ASCII quad and triangle with point colors) and `splats.ply`
(two degree-1 Gaussian splats in the 3DGS layout, ASCII) are original
fixtures for the PLY File and Export nodes; `points.ply` (three colored
points, no faces) is a plain point cloud, drawn as dots.
`splats.spz` is `splats.ply`'s two splats as SPZ version 4, written by
Niantic's reference library (PLY axes converted to SPZ's RUB) for the SPZ
File and Export nodes.
