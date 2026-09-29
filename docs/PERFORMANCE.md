# Performance

Current interactive numbers, the caching design behind them, how to measure,
and the open work. Numbers are local observations on the development Mac with
optimized native builds, not controlled cross-platform benchmarks. CPU timings
are not GPU completion or input-to-photon latency.

## Current numbers

Fixture: `camera.step` tessellated at 16 divisions, 707k points and 655k faces.

| Action | Time |
| --- | ---: |
| Edit-mode hover | 1.2 ms |
| Shift-click with 1,000 faces selected | 2.8 ms |
| Move | 0.3 ms UI + 1.2 s worker |
| Gizmo drag step | 0.2 ms UI + 0.4 s worker |
| Undo | 12–13 ms |
| Node select | under 1 ms |
| Tessellate 16 → 8 divisions | 4.5 s |
| First draw of a changed mesh (CPU prep) | ~1.8 s — open |
| File node displayed (load, preview, publish) | 1.2 s |
| Tessellate (16 divisions), cook | 1.8 s |
| Tessellate displayed after File | 3.1 s |

Worker times run off the UI thread; the previous scene stays visible and
interactive while they cook.

## What makes it fast

- **Nodes cache by content stamp.** Every node gets a 64-bit stamp of what its
  cook reads (kind, bypass, parameters, texts, Edit recipe keys, file epoch and
  input stamps). Names, positions, display/output flags, visibility, selection
  and the Edit tool amount are not in it, so renames, visibility toggles,
  selection and undo/redo to an earlier state never recook: they hit the
  worker's stamp-keyed result store (LRU, a quarter of physical memory, pinning
  the displayed and selected stamps and their inputs).
- **Delta requests.** The UI sends node bodies only when the worker's copy is
  stale, and each Edit element list once by content key. Only the newest queued
  request is cooked; a still-wanted cook is never cancelled.
- **Incremental Edit.** An Edit node applies only the recipes after its longest
  stored prefix; a gizmo drag previews by applying one recipe per pointer move.
  Recipes guard their input with the mesh's 64-bit topology hash instead of
  serializing connectivity.
- **Position edits share topology.** Move and drag create meshes that share the
  input's topology and display triangles; only positions change.
- **Shared storage across threads.** A published mesh is a new owner of the
  worker's immutable storage and caches (atomic owner counts), not a copy.
  Meshes are published by content key, and a key the UI still holds is
  republished with no work.
- **Renderer keeps prepared data per geometry.** Unchanged objects survive scene
  changes; display-mode and wire toggles never evaluate the DAG. Geometry lives in
  retained GPU buffers; camera motion updates a small uniform block per batch.
- **Picking and selection on the GPU.** Faces come from the renderer's id pass
  (points and edges from the picked face), selected faces tint from one bit
  per face, and a local Move uploads only its neighbourhood of the previous
  buffers. The query BVH is lazy (first CPU query) and refits after Moves.
- **Process-level source caches.** Parsed files (path, size, mtime, content hash,
  tolerance) and tessellations (parsed model and options) are reused on reload.
- **CAD.** luce-cad runs its per-face work (layout seeding, speculative
  crossings, meshing, normals, previews) on one persistent pool of
  processors - 1 workers; the serial layout reconcile reuses their exact
  results, so output does not depend on the core count. The File preview is
  one `CadModel.preview` call that meshes faces in parallel and returns
  display batches. Intermediate CAD meshes skip
  query-index construction; sliver dissolves update a native workspace instead
  of rebuilding the patch per edit.

See [DESIGN.md](DESIGN.md#background-computation) for the full design.

## How to measure

Always measure optimized builds (`--opt 2`, or `luc build --release` for the app);
debug builds are several times slower and not representative.

```sh
# CPU recording of the full UI (100 samples after 20 warm-ups) on a model
LUCE_PROFILE_OPT=2 python3 tools/profile.py camera /path/camera.step
LUCE_PROFILE_OPT=2 python3 tools/profile.py mesh /path/camera.step wire
# ...recording through the GPU recorder, or native orbit callback intervals
LUCE_PROFILE_OPT=2 python3 tools/profile.py mesh /path/camera.step wire gpu
LUCE_PROFILE_OPT=2 python3 tools/profile.py mesh /path/camera.step wire native
# Small built-in scenes: cube, Edit/extrusion, grid hidden; or a dense sphere
LUCE_PROFILE_OPT=2 python3 tools/profile.py
LUCE_PROFILE_OPT=2 python3 tools/profile.py dense
# Tessellation time and counts
python3 tools/cad_probe.py /path/camera.step --opt 2
# Background cook through the real app, with 300 orbit callbacks after warm-up
python3 tools/preview.py --scene cad_wire --file /path/camera.step --background --opt 2 --orbit
```

`tools/profile.py` builds `tools/profile.luc` with the test harness's
`prepare`/`build` and times phases with `tools/timing.lucb` (monotonic
nanosecond clock, reported in milliseconds). `mesh` tessellates at 16 divisions;
`camera` shows the analytic preview; `obj` loads an OBJ. `native` measures
callback-to-callback intervals in a real window, which include the event loop and
presentation.

`tests/bench/run.py` is the geometry-core benchmark's headless editor case: the
real `Workspace`, worker, publisher, renderer and Edit overlay drawing into an
offscreen texture, on the 700k-face grid and `~/Desktop/camera.step` (`--step`).
It times import, first display, selecting 1k faces and the Move round trip; the
figures for each migration step are in luce-3d's `docs/BENCHMARKS.md`.

The Edit-mode and worker numbers above come from driving the real `Workspace`,
compute worker and `app.render` on the camera fixture and timing each call on
the UI thread and the worker separately. Report UI and worker time separately,
warm up first, and note concurrent load; single runs are indicative only.

## Open work

- **A spread-out Move** (1k faces across a 700k mesh) still re-uploads whole
  arrays (23–32 ms round trip; a local one is 13 ms): per-element GPU
  scatter would close it.
- **Tessellation (1.8 s)**: what remains serial is geocore's final
  geocore `Mesh` construction (~0.27 s), layout reconcile/balance (~0.2 s) and
  the slowest faces' tails. CAD File 9.3 s and Tessellate 7.4 s cooks
  (18.3 s File to Tessellate displayed) were the 2026-09-28 starting point.
- Large models: `car2.step` (4.1M polygons) takes minutes from File to viewport;
  imports are whole-file, not streaming.
- Vulkan is cross-compiled and linked but not runtime-measured here.
- Presentation: measure Metal/Vulkan wait, drawable acquisition and GPU time
  separately before changing frames-in-flight or vsync policy; consider a time
  budget and coalescing of hover/camera events in the UI loop.
