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
keep their own fixtures (FBX: luce-fbx; STEP: luce-step). `step_limits.step`
(made with luce-step's tests/generate_fixtures.py: a 64-hole plate, past
the 64-loop face budget, beside a square) checks the File node's warning.
