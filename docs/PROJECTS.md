# Projects and UI persistence

`project_graph` owns the version-1 editor schema inside a Prism 4.0 text document.
`project_values` validates types, finite values, IDs and inspector-compatible
text. `project_file` handles atomic Prism saves and project-relative geometry
references. `project_session` owns native file dialogs, dirty state, commands and
the Save / Don't Save / Cancel lifecycle. No custom file parser is used.

`/scene` is a `luced3d` prim with a `network` child containing stable `n<ID>`
node prims. Nodes author input IDs, parent Group ID, output/enabled/visibility,
name, position and typed parameter arrays. Ordered Edit children retain operation
kind, element IDs, a 64-bit topology hash guard, displacement and amount.
Older projects' whole-connectivity guards load as unguarded recipes. `/scene/view`
stores camera and graph pan/zoom. Cached geometry, worker progress and undo history
are deliberately not serialized. This is an editor schema built on Prism, not
an OpenUSD interchange schema or an embedded copy of external assets.

Loads validate the full file, port counts, IDs, DAG cycles, parent hierarchy,
selection/scope and camera before replacing live state. Files are bounded to
64 MiB. Missing source geometry is an ordinary File-node error; it does not make
an otherwise valid project unreadable. Worker generations and source revisions
prevent old computations from replacing a newly opened document.

Saving commits an active authoring gesture. Dirty state compares authored data
against the saved snapshot, so undoing back to that state clears the marker;
camera motion, selection and cooked results don't mark the document dirty.
Prism writes through a synchronized temporary file and atomic replacement.

`ui_state` writes a separate small Prism preference document at
`~/.luced-3d/ui.prisma`, at most twice per second and only on change. `dock_layout`
validates then restores DStack's native layout text using stable panel IDs, with
splits, tab order/selection and floating rectangles. All panels may float. Invalid
settings fall back to the default workspace with a warning and are preserved for
inspection rather than silently overwritten. Absolute OS window position and
monitor assignment are not persisted yet.

Regression coverage includes Group and Edit round trips, quoted/Unicode text,
relative external files and Save As relocation, dirty undo/redo, cancellation,
failed-load atomicity, invalid cycles/text, floating viewport/all-floating layouts,
split/tab restoration, preferences and corrupt-file preservation. Native Metal
captures now accept `--width`, `--height` and `--viewport-only`; actual pixel sizes
are reported, since the window system may constrain the requested dimensions.
