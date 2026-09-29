# Background computation and node gizmos

Runtime node evaluation is performed by a persistent worker. `Node.compute`
receives resolved inputs; the worker owns its graph mirror, CAD objects and
cached results. The UI never shares Luce objects with it.

**Stamps.** Before each request the UI stamps every node (`stamps`): a 64-bit
hash of what its cook reads (kind, bypass, parameters, texts, Edit recipe keys,
the file epoch and its inputs' stamps). Names, positions, display and output
flags, visibility, selection and the Edit tool amount are not in it; visibility
and output flags reach only the parent Group's stamp. An enabled Edit node's
stamp is the stamp of its input plus its recipe keys, so the state before a new
recipe is already stored under the prefix stamp. Recipes guard their input with
the mesh's 64-bit topology hash.

**Requests.** `compute_request` frames the shared graph schema (`project_graph`,
also used by project files) as a Prism document: every node's header and stamp,
but a body only when the worker's copy is stale, and each Edit element list once
by content key. Requests queue in order (each is a delta against the previous
one) and only the newest is cooked. A worker that loses its mirror asks for one
full resend.

**Result store.** `result_store` keys cooked results (and failures of a node's
own recipe) by stamp, with an LRU budget of a quarter of physical memory that
never evicts the displayed and selected stamps, their inputs or the Edit prefix
before their last recipe. Renames, visibility toggles, the tool amount and undo
or redo to an earlier state are store hits. An Edit node applies only the
recipes after its longest stored prefix; a gizmo drag previews by applying its
one recipe, with one request per pointer move. Parsed files (by path, size,
mtime, content hash and tolerance) and tessellations (by parsed model and
options) are cached for the process in `node_evaluation.SourceCache`.

**Cancellation.** A newer request stops publishing at the next checkpoint and
cancels a cook only when the new request no longer wants the stamp being
cooked; a still-wanted cook finishes into the store. Parsing and individual
geometry operations remain uninterruptible between checkpoints.

**Publishing.** Products are keyed by content: a displayed mesh by its stamp
and ordinal, or by the identity of a mesh already published (an Edit without
recipes, a Null or a bypass reuses its input's key). A published mesh is a new
owner of the worker's immutable storage and query index (atomic owner counts),
not a copy; the worker warms the index except while a gesture previews, and
extracts wire and normal overlays once per key. `display_publisher` keeps the
meshes the UI holds (this result's and six recent keys), so the worker
re-publishes a held key with no work, and rebuilds scene objects only when the
displayed keys change. The renderer keeps prepared data per geometry object, so
unchanged objects survive scene changes.

Progress is shown on nodes, including per-face CAD progress. The UI keeps the
previous scene visible while cooking. Shutdown joins the worker. A 16 ms UI
timer polls completion while otherwise idle.

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

Regression coverage includes stamp rules, store hits on undo, hashed guards,
small deltas and one-recipe Edit replay on a ~500k-face mesh, newest-request wins,
undo, STEP preview/conversion, cube corners, plane constraints, snapping, pivot
compensation and handle sizing. Native captures cover Move and camera conversion.
