# Geometry workflow research

The implementation is original; no Blender GPL implementation was copied.
These references guided contracts and interaction, not claims of full parity.

## Houdini: geometry as inspectable data

[Attributes](https://www.sidefx.com/docs/houdini/model/attributes.html) distinguish
points, vertices, primitives and detail. Keeping corners separate from shared
points is essential for UV seams and discontinuous data. We adopted these four
domains, numeric tuple attributes, explicit topology provenance and named groups.

The [Geometry Spreadsheet](https://www.sidefx.com/docs/houdini/ref/panes/geosheet.html)
makes intermediate results debuggable. Our pane follows selection rather than
display, with pinning, domain tabs, filters and numeric sorting. Keeping this
read-only avoids hidden mutations outside the procedural history.

[Network nodes](https://www.sidefx.com/docs/houdini/network/nodes.html) and
[network options](https://www.sidefx.com/docs/houdini/network/options.html) informed
compact node bodies, external labels, top/bottom ports, curved vertical wires,
independent selected/display/bypass states and fixed-size hover controls. We
retain the editor's grey/orange palette rather than Houdini's flag colors.
The supplied ResearchGate image was unavailable (403), so exact visual fidelity
to that image could not be verified.

## Blender: attributes and reusable geometry evaluation

Blender's [attribute design](https://developer.blender.org/docs/features/objects/attributes/)
and [geometry sockets](https://developer.blender.org/docs/features/nodes/geometry_socket/)
reinforce that geometry data and domain adaptation belong below the UI. Our
attribute arrays live in immutable engine meshes; graph nodes only specify
operations. Unlike Blender's broad field system, this iteration exposes numeric
parameters and explicit groups. Field evaluation should be a deliberate future
type-system addition, not ad-hoc expressions inside widgets.

## Operator fidelity and scope

The [Subdivide SOP](https://www.sidefx.com/docs/houdini/nodes/sop/subdivide.html)
motivated Catmull–Clark topology/position handling and separate linear attribute
interpolation. [Fuse](https://www.sidefx.com/docs/houdini/nodes/sop/fuse.html)
highlights that merging points requires explicit attribute ownership and cleanup
rules, not only proximity tests. Our spatial-hash fuse deterministically retains
the first representative; Clean is a separate explicit operation.

[PolyBevel](https://www.sidefx.com/docs/houdini/nodes/sop/polybevel.html) is much
broader than this release's closed-mesh fractional chamfer. Selected edges,
constant distance, multiple segments and corner handling need dedicated work.
[Smooth](https://www.sidefx.com/docs/houdini/nodes/sop/smooth.html) similarly has
more controls than our one-step neighbor relaxation. MODELING.md documents these
differences rather than presenting simplified operations as full SOP equivalents.

## Architecture direction

Preserve one graph context. Subgraphs should expose ports without introducing
separate modeling/material/animation editor modes. Add serialization and stable
attribute schemas before expanding into fields, instances and shader graphs.
Keep topology algorithms and acceleration in luce-3d, with editor commands,
recipes and selection in luced-3d. Shared UI/GPU changes require separate review
because luced-2d is being developed concurrently.
