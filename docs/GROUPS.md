# Imported hierarchy and Blast

Geometry owns named primitive groups; nodes only expose those paths in their
evaluation summary. The Outliner projects the paths below each exposed node.
It does not create graph nodes for imported parts or infer ancestry from wires.
Actual Group nodes still own nested networks and transforms.

STEP product names, occurrence names and solid names form paths. For the supplied
camera, one path is `Camera - 6/Lens:1/Phone Camera Lens v3:1/LensShell`.
Unnamed solids use `solid_<STEP entity ID>`. Literal `/` and `%` in names are
encoded as `%2F` and `%25`, so they cannot accidentally add hierarchy levels.
Repeated product instances and STEP Unicode escape decoding remain unsupported;
duplicate sibling labels are not yet disambiguated.

File returns analytic CAD plus groups. Tessellate uses the native primitive
`cad_face` attribute to map each analytic face's group onto every generated
polygon. Transform preserves membership; Merge offsets member/model IDs.
Other modeling operators do not yet all propagate this path metadata.

Blast accepts whitespace/comma-separated selectors, quoted names, `*` and `?`.
An exact parent path includes its descendants. `^pattern` subtracts matches from
a preceding positive selection. Empty selection means everything. The default
deletes matches; Delete non-selected / isolate retains them. For example:

```
*/LensShell
'Camera - 6/Lens:1'
* ^*/LensShell
```

CAD extraction copies only referenced topology, preserving colors and placement;
polygon extraction remaps face groups and removes unused points. Both run inside
the existing background DAG compute. The Outliner receives only a copied path
summary, not worker-owned geometry. Imported rows collapse independently; clicking
one selects its producing node, not yet an individual geometry component.

The interaction follows [Houdini Blast](https://www.sidefx.com/docs/houdini/nodes/sop/blast.html),
but does not implement its complete selection-expression language.

Verified by the portable assembly fixture (including transformed colored CAD,
partial subsets, conversion, wildcard selection, Outliner and async undo), and by
native camera captures: the imported hierarchy, and File → Blast → Tessellate →
Transform.

![Imported camera hierarchy in the Outliner](preview_camera_hierarchy.png)

![Blast isolating part of the camera](preview_camera_blast.png)
