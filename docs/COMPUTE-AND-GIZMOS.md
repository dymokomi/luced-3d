# Background computation and node gizmos

Runtime node evaluation is performed by a persistent worker. `Node.compute`
receives resolved inputs; the worker owns its graph, CAD objects and cached
results. The UI sends versioned recipe snapshots, never shared Luce objects.
Native polygon copies cross the boundary and are adopted on the UI thread.
Boundary/normal line batches remain native to avoid serializing every endpoint
on each camera frame.

`compute_protocol` handles snapshots/cache reuse, `compute_worker` evaluates and
prepares display data, `compute_bridge` owns synchronization/native transfer, and
`compute_session` schedules and applies results. New requests replace pending
requests; generation checks prevent stale results from being displayed. Progress
is shown on nodes, including per-face CAD progress. The UI keeps the previous
scene visible while cooking. Parsing and some individual geometry operations are
not yet interruptible internally; cancellation is cooperative at checkpoints.
Shutdown joins the worker. A 16 ms UI timer polls completion while otherwise idle.

Cube corner handles resize its dimensions while holding the opposite corner.
Transform and Group offer Move, Rotate, Scale and Pivot via viewport icons or
W/E/R/P. Move/Pivot use world axes and XY/XZ/YZ plane handles; Scale follows the
node's rotation. Rotation edits Euler components. Center handles provide free
movement/uniform scale. Pivot movement compensates translation to preserve the
geometry, including rotated, non-uniformly scaled nodes.

Shift snaps movement to 0.1 units, rotation to 15 degrees, and scale factors to
0.1 increments. Plus/minus adjust handle size. Hover/active handles use orange;
axes use muted red/green/blue. A drag is one undo transaction; Escape cancels it.
Gizmo drawing and picking live in `node_gizmos`/`gizmo_math`, independent of mesh
evaluation. Numpad Enter is normalized to Enter by the macOS window backend.

Regression coverage includes copied worker snapshots, newest-request wins,
undo, STEP preview/conversion, cube corners, plane constraints, snapping, pivot
compensation and handle sizing. Native captures cover Move and camera conversion.
