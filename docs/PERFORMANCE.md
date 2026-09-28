# Performance investigation — 2026-09-26

**Latest:** [large-file engine audit](ENGINE_AUDIT_2026-09-27.md) documents the
retained GPU path, 171.5 → 0.48 ms recording comparison, large OBJ imports and
remaining bottlenecks. The entries below are historical; their CPU-projection
and “GPU buffers remain future work” statements no longer describe device frames.

## Update 2026-09-27: camera model and background compute

The 2,710-surface camera fixture's CPU full-UI recording fell from **468.93 ms**
to **19.68 ms** at `--opt 0`, then measured **14.25 ms** at `--opt 2`.
Run `LUCE_PROFILE_OPT=2 python3 tools/profile.py camera /path/to/camera.step`.
These are local 100-frame averages after 20 warmups, not GPU timings or
input-to-photon latency. They do not establish 120 Hz performance.

The renderer now caches immutable world-space positions and lighting, gathers
active lights once, and invalidates on scene epoch changes. Native retained wire
batches eliminate per-frame Luce-to-Base endpoint copies. Camera projection and
frame recording remain CPU work. No vsync or shared UI change was made.
The GPU canvas now has an opt-in larger frame budget: luce-3d requests up to
8,388,608 vertices; ordinary UI frames retain the 1,048,576 default. Allocation
still grows on demand. This removes the camera's frame rejection, not the cost
of expanding indexed geometry into triangles.
Retained indexed GPU geometry and camera uniforms remain the next large gain.

Node computation, CAD display meshing and overlay preparation now run on a worker;
the UI retains the old scene and displays per-node progress. The complete camera
at 16 divisions passes a closed-manifold audit and native background-compute
viewport capture. See [compute architecture](COMPUTE-AND-GIZMOS.md).

Historical measurements below describe earlier implementations.

## Update 2026-09-27: depth-tested wires

The same dense fixture now records the full UI in **9.49 ms in Edit mode**
(9.54 ms with grid hidden), versus the earlier 48.23/43.97 ms. Object mode is
6.56 ms; face picking 0.004–0.008 ms. These use the same 100-sample/20-warmup CPU
harness, not GPU timestamps or input-to-photon measurements. The comparison is
indicative local data, not a controlled cross-platform benchmark.

Per-edge midpoint ray tests and whole-mesh projection were removed from face-mode
drawing. Native homogeneous pixel-width wires use scene depth; ray tests remain
for picking. This fixes partial-edge occlusion and perspective grid thickness.
See [viewport research](VIEWPORT-AND-IMPORTS.md) for Blender findings and GPU proposals.

The measurements and dense-orbit warning below describe the earlier baseline.

## Measurements

`python3 tools/profile.py` uses a monotonic nanosecond clock, reports milliseconds,
warms 20 iterations and averages 100. Native compilation uses the same `--opt 0`
as the current test harness. Full UI recording includes Frame creation, drawing
and closure at 1400×900 logical pixels. It does NOT submit work to a GPU.
These small-scene measurements do not establish dense-mesh performance.

| Phase | Before grid batching | After grid batching |
| --- | ---: | ---: |
| Cube, CPU full UI recording | 0.836 ms | 0.539 ms |
| Edit/extrusion, CPU full UI recording | 0.996 ms | 0.696 ms |
| Edit, grid hidden | 0.730 ms | 0.662 ms |

Camera update: approximately 0.0005–0.0008 ms. Face ray-picking: approximately
0.002–0.003 ms on this tiny scene. Differences in the grid-hidden control show
run-to-run noise: these are not statistically controlled laboratory results.

Grid changed from 42 separate box meshes / 504 triangles to 3 material batches /
84 triangles, constructed once. No shared UI/GPU changes were needed.

`python3 tools/profile.py native` drives orbit through a 1 ms timer in a real
Metal window, excludes 30 warm-up intervals and observes 300 subsequent intervals.
Observed mean 16.665 ms, worst 18.507 ms. This measures callback-to-callback pacing
including the application loop and presentation; it is NOT GPU timestamp timing,
display scanout measurement, input-to-photon latency, or proof of 120 Hz readiness.
Do not equate nanosecond clock units with nanosecond measurement accuracy.

## Shared-library proposals (not applied)

1. **luce-ui modifier/capture correctness.** `layout/tree.lucb`'s special secondary
   press route constructs an Event without modifiers. Preserve all pointer metadata
   and route right-drag movement to the secondary holder, including outside its
   bounds. The editor currently arms right drag and confirms Alt on its first move.
   This supports dolly without changing the shared package, but is not a substitute
   for proper secondary capture across pane boundaries.
2. **Instrument luce-gpu presentation phases.** `gpu/metal/surface.lucb` explicitly
   sets `setDisplaySyncEnabled:false`, despite a nearby comment saying synchronized.
   Every `metal_render` first calls `metal_surface_wait` (`waitUntilCompleted`), then
   acquires `nextDrawable`, records and commits. Measure those phases separately,
   together with command-buffer GPU start/end timestamps, before attributing the
   observed 60 Hz pacing to any one of them. CPU recording is not the current
   small-scene frame-interval bottleneck.
3. **Bounded frames in flight.** Evaluate a two-slot resource ring/completion
   callbacks instead of an unconditional main-thread wait. Audit ownership and
   mutable upload buffers first; never remove the wait without fixing lifetimes.
   Prefer newest camera state over queuing stale frames. Compare latency as well as
   throughput; deeper queues can make mouse interaction worse.
4. **Explicit presentation policy.** Offer low-latency interactive and synchronized
   animation policies, selected per surface. Compare 60/120 Hz displays using
   p50/p95/p99 frame intervals, missed refreshes, and input-to-submit age. Do not
   globally re-enable vsync to hide irregular pacing.
5. **luce-ui event budget / render invalidation.** The loop processes up to 512
   events before rendering. Profile long bursts; consider a time budget and
   coalescing consecutive hover/camera moves only (never drawing samples, presses,
   releases or modifier boundaries). Separate view redraw from inspector/graph
   refresh and cache unchanged panel rendering where safe.

## Next engine work

The current renderer CPU-transforms indexed vertices and illuminates them every
frame. Polygon picking scans triangles; edit overlays perform visibility rays for
points/edges. Dense meshes need a cached BVH, projected selection caches, retained
GPU vertex/index buffers and GPU transforms. Benchmark 1k/10k/100k triangles before
choosing thresholds. Current component overlays can become quadratic; the small
cube timings must not be presented as a scalable engine benchmark.

No changes were made to luce-ui, luce-gpu or luced-2d during this investigation.
# Modeling expansion measurements

The expanded engine now builds an immutable triangle BVH for picking/occlusion.
Viewport projections and visibility are cached across pointer-only redraws.
Edit edges, points and selected triangles use batched Painter meshes; individual
draws previously exceeded the canvas's 4096-draw limit on the dense fixture.
No shared luce-ui or luce-gpu changes were required for that fix.

`python3 tools/profile.py dense`, current debug/test toolchain, 100 samples after
20 warmups, 1400×900 logical UI: sphere with 1,986 points, 2,048 faces and 3,968
triangles. Object-mode full CPU UI recording averaged 7.43 ms; Edit averaged
48.23 ms (43.97 ms without grid), while face picking averaged 0.009–0.010 ms.
These are CPU recordings, not GPU timings or input-to-photon latency. Concurrent
development/build load makes them diagnostic, not a controlled benchmark.

**Dense Edit orbit is not yet sufficiently smooth.** The next engine work should
batch projection/occlusion queries across the native boundary and retain overlay
buffers; avoid interpreting the BVH improvement as a solved frame-time problem.
The existing shared-library proposals below remain proposals, not applied fixes.
