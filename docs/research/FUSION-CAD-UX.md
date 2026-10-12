# Fusion CAD UX for luced-3d: sketches, features and direct modeling

Research and design, 2026-10-11. No product code was changed for this document. It answers
the owner's request:

> "the whole CAD and sketch is actually a bigger thing... The UX is really odd. If I draw
> Sketch I cant instantly select the solid inside so that I can extrude. When I draw I also
> would like to see sizes and they should be editable.. [...] we have this dual workflow - we
> do nodes, so connected nodes act the same as history in Fusion, and then we have direct
> modeling Edit CAD node - I suggest that in there we have full support. Also selecting a face
> and creating a new sketch on that face (it should retain that face projection so that I can
> easily do offset."

Sources:

- **Fusion's sketch tools.** [FUSION-SKETCH-STUDY.md](FUSION-SKETCH-STUDY.md) (2026-10-08) already covers the Sketch environment's CREATE, MODIFY and CONSTRAINTS tools in detail. This document does not repeat it. It cites it as **SK-STUDY §n**.
- **Fusion help.** Autodesk's help and API reference were read again for what that study left out: Create Sketch on a face, auto-projection, the heads-up dimension boxes, profiles, the Solid features, direct modeling and the timeline. Claims carry the same tags:
  - **[doc]**: Autodesk help or API reference;
  - **[comm]**: a blog, forum or tutorial;
  - **[unverified]**: not confirmed in a source.
- **SolidCraft.** [SolidCraft](https://github.com/bherbruck/solidcraft) is an open-source Rust reimplementation of Fusion's Design workspace, built on truck. I cloned it to `luce_work/cad/solidcraft` for reference only; none of it goes into our repos. Its file names are given so a later reader can find the behavior. It is young: its own parity table counts 335 of 541 Fusion commands, and booleans, shell and offset cover a limited set of cases. Its UX layer, though, is close to Fusion's and well factored, and several of its rules are worth copying (§3).
- **Our code.** luced-3d and luce-cad at `origin/main` on 2026-10-11, read and run. `luc test` passes (editor and examples). The `cad_sketch`, `cad_node` and `cad_pick` preview scenes were captured.

## 1. Decision in one page

**The odd part is the hand-off, not the tools.** The Sketch node already has most of Fusion's
drawing, modifying and constraint tools, and luce-cad already finds profiles (closed regions)
and keeps them by key. What is missing is the path between them:

- Profiles are not shown in the sketch.
- You cannot click a region and extrude it.
- Sizes cannot be typed while drawing, and dimensions can't be clicked to edit them.
- An Extrude has to be added from a menu, wired by hand (a second wire for Join or Cut), and given its profiles with a "Pick profiles" button in the parameter panel.

The plan fixes the hand-off first.

**Nodes are the history.** A CAD network's chain is Fusion's timeline:

- **One body flows down the chain**, as Fusion's design state flows along its timeline. A Sketch passes its input body through beside its curves. An Extrude cuts or joins that same body, with the operation chosen by where the extrusion goes, as Fusion does. The second input remains only for an explicit target.
- **The display flag is the rollback marker.** The Output node is the timeline's end.
- **Other timeline actions map onto the network:**
  - editing a feature is selecting its node: the viewport shows its handles and value boxes;
  - suppressing is bypass;
  - reordering is rewiring, checked by evaluating the new order before it is kept;
  - an upstream edit re-cooks everything after it, and lost references show on the nodes that lost them.

**Edit CAD is direct modeling.** It is the place for Fusion's "Do not capture design
history" and for its Base Feature:

- sketches live inside it as objects;
- Extrude, Press Pull, Move Face, Offset Face, Delete Face, Replace Face, Shell, Fillet, Chamfer, Combine and Move/Copy are steps of its recipe;
- each step is one undo, and nothing earlier is re-edited.

The same luce-cad operations serve both workflows. A node runs them on its input, and an Edit CAD step runs them on the recipe so far.

**Sketch on a face keeps the face.** You select a flat face and choose Sketch. The new Sketch node is put after the displayed node. It is on that face, kept by the face's name, and the face's loops are projected in as linked curves. An Offset of a projected loop stays tied to it, so when the body upstream changes, the loop and its offset follow.

**luce-cad's part:**

- profile fills, a profile's area and middle (for the arrow);
- one call that projects a face's loops as linked curves;
- an Offset relation over a chain with a single distance;
- an inside test (for the automatic Join/Cut);
- Extrude's missing extents (two sides, taper, to object, all, from a face);
- the local face operations (move, offset, delete with healing, replace);
- Shell;
- blends of edges between curved faces. This is what blocks filleting an earlier fillet's edges. A separate fix is under way for "cube, fillet 4 edges G3, then fillet or chamfer the rounded top edge chain: it fails silently".

**Staged plan** (§9):

| Stage | What it delivers |
|---|---|
| 0 | Small fixes found here (done) |
| 1 | Profiles you can see, pick and extrude (done) |
| 2 | Dimensions while drawing, and on the canvas (done) |
| 3 | Sketch on a face from the viewport, with projection and offset (done) |
| 4 | Extrude, Revolve and Press Pull in full (done; the parity round added Thin, faces as profiles, Start object, Extend, Objects To Cut and Revolve To) |
| 5 | Fillet and Chamfer in the viewport (done; the parity round added Full round, chord length, variable radius, G1 setback corners and chamfer corner types) |
| 6 | Edit CAD direct modeling (done; its parity gaps closed with stages 7–8) |
| 7 | Shell, Move/Copy, Combine, Split Body and the other Modify features as nodes (done) |
| 8 | A timeline strip and history polish (done) |

## 2. What we have, and the gaps

Checked in the code and the app on 2026-10-11.

### 2.1 What works

**Sketch node** (`sketch_node.luc`, `sketch_editor.luc`, `sketch_*.luc`; luce-cad `src/sketch/`):

- **Planes.** XY, XZ, YZ or Face (kept by name), with an Offset.
- **CREATE.** Every Fusion entry except Intersect, Include 3D Geometry and Project To Surface: lines, rectangles, circles, arcs, polygons, ellipse, slots, splines, conic, point, text, mirror and patterns.
- **MODIFY.** All of it.
- **CONSTRAINTS.** All, Polygon included (one constraint on the polygon's one construction circle).
- **Inference and snapping.** Snapping to points, middles, crossings, curves and the grid; Horizontal or Vertical inferred within 3°.
- **Fully constrained coloring.**
- **Sketch Dimension.** It opens a value box after placing a dimension. Dimensions appear as d1, d2… rows in the parameter panel, in the document's unit.
- **Project.** It casts body edges onto the plane as fixed, linked curves, which follow the body (`CadProjection`, `relink`).
- **Offset.** It works on any chain, projected curves included.
- **Levels and menus.** The Points, Lines and Shapes levels, and the A/S/D marking menus.

**Profiles** (luce-cad `profile.lucb`, `arrangement*.lucb`):

- crossing curves split each other, as in Fusion;
- each smallest closed region is a profile with a stable key (`0+,1-`);
- `profile_at` finds the profile under a point;
- `profile_outlines` draws them.

**Features** (`cad_nodes.luc`):

- **Extrude:** distance, New body/Join/Cut/Intersect, symmetric.
- **Revolve:** about the plane's U or V axis, with an angle.
- **The rest:** Boolean, Fillet (G1/G2/G3, tangent chain, a plan kept while the radius is dragged), Chamfer, Mirror Body, Pattern, the solid primitives.
- **Edge references.** Fillet and Chamfer keep their edges by the names of the faces each lies between, so the edges survive upstream edits.

**Edit CAD** (`edit_cad.luc`). Levels are Object, CVs, Edges, Faces and Patch. Its tools:

- move, rotate, scale and delete models;
- delete faces, which leaves an open shell;
- Noise, Flatten and Snap on CVs;
- Fillet and Chamfer on picked edges;
- primitives.

### 2.2 Gaps against Fusion

| # | Gap | Where |
|---|---|---|
| G1 | Profiles are not drawn in the sketch. They show, as outlines and not fills, only while an Extrude's "Pick profiles" prompt is open. | `sketch_view.luc`, `profile_pick.luc` |
| G2 | There is no way from a picked region to an Extrude. You add Extrude from the A menu, wire it, then press Pick profiles in the parameter panel. | `marking_items.luc`, `inspector.luc` |
| G3 | Join, Cut and Intersect need the target body wired to Extrude's second input, because a Sketch outputs only curves. | `cad_nodes.operated`, `sketch_node.evaluate_sketch` |
| G4 | You can only edit a sketch while it is the displayed node, and then its curves are all that shows. On a face sketch, the body it sits on is not drawn (only its edges, while Project is in use). | `workspace.sketching`, `sketch_view.draw_lines` |
| G5 | No value boxes while drawing. A shape's size is set afterwards with Sketch Dimension, then typed. | `sketch_value.luc` (one field, opened after a dimension is placed) |
| G6 | Dimensions are drawn as a value in a box at the entity's middle, without extension lines, arrows or a movable label. They cannot be clicked, double-clicked to edit, dragged or deleted on the canvas; editing is in the parameter panel only. No Driven/Driving toggle in the viewport. | `sketch_view.glyphs` |
| G7 | Constraint glyphs are text labels that cannot be picked. A constraint cannot be removed except by undo. | `sketch_view.glyphs`, `sketch_editor.remove_selection` |
| G8 | Sketching on a face takes Plane: Face in the panel, then Pick face. You cannot select a face in the viewport and choose Sketch. The face's edges are not projected; Project takes one edge per click. | `tool_prompts.pick_face`, `sketch_editor.project_at` |
| G9 | Offsetting a chain dimensions each line copy separately. A chain's offset is not one value you can change afterwards. | luce-cad `sketch/offset.lucb` |
| G10 | Extrude lacks two-sided (different distances), taper, To Object, All, start offset, and faces as input (Press Pull). There is no arrow to drag and no value box in the viewport, and the operation is never chosen automatically. | `cad_nodes.evaluate_cad`, `node_catalog.cad_fields` |
| G11 | Revolve's axis can only be the plane's U or V axis, not a picked line. | same |
| G12 | Fillet and Chamfer take their edges through a "Pick edges" prompt from the panel. There is no "select edges, Fillet, drag the radius" flow, and no fillet of edges between curved faces. That case covers an earlier fillet's edges, and is the separately tracked G3 bug. No variable radius, setback choice, chord length or rule fillet. Chamfer has only equal distance. | `cad_nodes`, luce-cad `blend*.lucb` |
| G13 | No Shell, Press Pull, Move Face, Offset Face, Replace Face, Split Body or Split Face, either as nodes or in Edit CAD. Edit CAD's Delete removes faces without healing. | luce-cad, `edit_cad.luc` |
| G14 | No sketches inside Edit CAD, so direct modeling cannot start from a sketch. `EditStep` carries numbers and a group expression, with no text for a sketch. | `edit_cad.luc`, `edit_operations.EditStep` |
| G15 | A new Sketch node's second text defaults to `"weight"` (`node.luc:102`, the AttributeCreate default given to every kind). The parameter panel's Face row shows "weight". With Plane: Face and nothing picked, the error is "no longer on the body" rather than "Pick the face". | `node.luc` |
| G16 | The sketch's input body is cooked on the UI thread (`sketch_frames.body` evaluates a network copy). This is fine for small parts; heavy bodies will stall drawing. | `sketch_frames.luc` |

## 3. What Fusion and SolidCraft do

This section covers only what the plan uses. For the sketch tools themselves, see SK-STUDY.

### 3.1 Creating a sketch on a face

Fusion:

- **What can carry a sketch.** Create Sketch takes an origin plane, a construction plane or a planar face of a body. A curved face can't carry one [comm].
- **Auto Look At Sketch.** When this preference is on, the view turns to face the new sketch. The API's `isAutoLookAtSketch2` also chooses whether the camera switches to orthographic [doc] (`https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_FusionProductPreferences.htm`).
- **Two projection preferences** [doc] (same page):
  - `isAutoProjectGeometry`: geometry not in the sketch plane is projected automatically.
  - `isAutoProjectEdgesOnReference`: a model edge is projected when a constraint or dimension refers to it while you look straight at the sketch.
- **Is the face's loop projected?** Older Fusion projected the loop when the sketch was made. Whether current Fusion does, and what the defaults are, is [unverified]: users describe edges arriving only when referenced or projected.
- **Project (P)** [doc] (`https://help.autodesk.com/cloudhelp/ENU/Fusion-Sketch/files/SKT-SKETCH-CREATE-PROJECT-INCLUDE.htm`).
  - It takes Specified entities (faces, edges, points) or Bodies (the silhouette as closed profiles).
  - A **Projection Link** box keeps the curves associative.
  - A face given to `Sketch.project2` brings all its edges [doc] (`https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_Sketch_project2.htm`).
  - Intersect brings in where geometry crosses the plane. Include 3D Geometry brings edges in without flattening them.
- **Linked curves are purple and can't be edited** [comm].
  - Break Link turns them into plain curves, for good.
  - A projection that loses its source warns on the sketch's timeline icon. It is repaired with Manage Lost Projections (Re-Link, Break Link, Delete; SK-STUDY §1.6).
- **Offset is one relation** [doc] (`https://help.autodesk.com/cloudhelp/ENU/Fusion-Sketch/files/SKT-OFFSET.htm`).
  - It takes a curve, a chain or a profile, and goes one side, two sides or symmetric.
  - It makes one offset constraint, with its glyph, and one dimension.
  - Deleting the dimension keeps the relation with the distance free; deleting the glyph breaks the link.
  - Chain-picking a linked projected loop is unreliable in Fusion [comm]. Picking the loop's profile works.

SolidCraft (`engine/cmd/sketch_face.rs`, `sketch/src/link.rs`):

- **The face is kept by a certificate, in its own frame.** When the box grows or moves, the sketch moves with the face and keeps its local coordinates.
- **Projection is automatic and live.** The face's loops are projected by default as linked curves (purple, their points fixed). They bound profiles, and constraints and dimensions can attach to them.
- **Refresh keeps curve ids.** When projections are refreshed, existing curves are matched before new positions are assigned, so the constraints on them survive. Ambiguity is reported as a lost reference, never guessed.
- **Offsets follow.** An offset of a projected loop stays associative and follows it.
- **A lost face can be repaired.** Redefine Sketch Plane offers the repair with a preview.

### 3.2 Dimensions while drawing

Fusion:

- **Lines.** After the first click, a line takes a click or typed length and angle [doc] (SKT-CREATE-LINES).
- **Rectangles.** A rectangle takes `50 mm`, Tab, `50 mm`, Enter. The boxes take parameter names, with completion [comm] (Autodesk Learn).
- **Locking.** Tab moves between the boxes, and a typed value locks and becomes a sketch dimension; values not typed stay free [comm]. The help does not describe this.
- **No setting found.** I found no Fusion preference named "show dimensions while drawing"; "Heads-Up Display" is Inventor's term.
- **The nearest documented preferences** [doc] are:
  - `isDimensionEditedWhenCreated`: Sketch Dimension's value box opens at once;
  - `isSketchScaledWithFirstDimension`.
- **Editing later.** A double-click on a dimension's text edits it, and the value may be an expression [doc] (SKT-CREATE-DIMENSIONS). One driven by a parameter shows `fx:` [comm].

SolidCraft's `sketch_dims.rs` is the clearest model.

- **Fields per tool and stage:**

  | Tool | Fields |
  |---|---|
  | Line | Length, Angle |
  | Rectangle | Width, Height |
  | Circle | Diameter |
  | Center arc | Radius, then Sweep |
  | Polygon | Radius, Sides |
  | Slot | Length, then Width |

- **Placement and typing.** Each box sits beside the segment it measures and shows the live value from the cursor, with its text selected. Typing replaces the text and locks the value; a locked box changes color.
- **Locked values steer the cursor.** A line with a locked length keeps the cursor's direction at that length.
- **Keys.** Tab and Shift+Tab move between the boxes, and Enter places the point.
- **Typed values become driving dimensions.** They are added in the same undo step as the shape, and keep the text that was typed, so an expression stays an expression.
- **A typed angle switches off Horizontal and Vertical inference** for that line.

On the canvas afterwards (`dim_view.rs`):

- **Drawing.** Dimensions have extension lines, arrows, R and Ø prefixes, and angle arcs. A driven dimension is shown in parentheses.
- **Gestures.** A click selects a dimension. Delete removes it. Dragging the label moves it. A double-click opens an inline box on the label.
- **Drafts.** A new dimension is first measured in a scratch copy, and nothing is committed until Enter.

### 3.3 Profiles

Fusion (more in SK-STUDY §8):

- **Shading.** Closed regions are shaded light blue. Show Profile turns them off, and turning them off takes them away from features using them [comm].
- **One sketch at a time.** Regions are found within one sketch, never across sketches [comm].
- **Extrude's inputs** are coplanar profiles or planar faces [doc] (`SLD-REF-EXTRUDE`). Its selection rules:
  - selecting a sketch in the browser or timeline selects all its profiles;
  - when only one profile is visible as Extrude starts, it is taken.
- **E inside a sketch** opens Extrude and finishes the sketch in one step [comm]. That profiles picked in the sketch carry into Extrude is [unverified] for Fusion; SolidCraft does it.

SolidCraft:

- **Drawing.** Profiles are shaded as translucent fills, lifted a little off a face they lie on. The one under the pointer is lit.
- **Picking.** A ray meets the sketch plane, and the smallest region containing the hit wins. Profiles win over the face beneath them.
- **E works in and out of the sketch.** Picking a profile and pressing E works both while editing the sketch and after Finish Sketch. Applying the Extrude leaves the sketch.
- **With nothing picked,** Extrude takes the active sketch, or else the last one.
- **Profiles are kept by the curves around them.** More than one match is an error. Neighboring picked profiles become one body. This is the same rule as our keys.

### 3.4 Extrude, Press Pull, Fillet, Shell, Move

Fusion [doc] (`https://help.autodesk.com/cloudhelp/ENU/Fusion-Model/files/SLD-REF-EXTRUDE.htm` and the pages named):

- **Extrude** (E):
  - Type: Extrude or Thin Extrude (wall thickness, Side 1 / Side 2 / Center).
  - Start: Profile Plane, Offset or Object.
  - Direction: One Side, Two Sides (an extent and taper each) or Symmetric (half or whole length).
  - Extent: Distance, To Object (a face, body or plane, with an offset) or All.
  - Taper angle.
  - Operation: Join, Cut, Intersect, New Body, New Component.
  - Objects To Cut: visible bodies at creation, kept, or Auto-Select again.

  The operation follows where the extrusion goes: into a solid it becomes Cut, otherwise Join or New Body [comm]. I found no preference that stops the switching. The help doesn't describe the arrow; an arrow on the profile, a taper handle, and an arrow per side for Two Sides is [unverified].
- **Revolve:**
  - Axis: any linear or circular object, with Project Axis.
  - Extent: Partial angle, To Object or Full.
  - Directions as Extrude.
- **Press Pull** (Q) depends on the selection [doc]:
  - a profile gives Extrude;
  - an edge gives Fillet;
  - **a face gives Offset Face**.

  On a face made by a feature it may jump into editing that feature instead [comm].
- **Fillet** (F) [doc] (`SLD-REF-FILLET`):
  - Types: Fillet (edges, faces or features), Rule Fillet (All Edges or Between Faces; Rounds, Fillets or both) and Full Round.
  - Each row is an edge set with its own radius type: Constant, Chord Length, Variable (points along an edge) or Asymmetric.
  - Continuity: Tangent (G1) or Curvature (G2) with a weight.
  - Corner: Rolling Ball or Setback.
  - Tangent Chain is on by default.
- **Chamfer** [doc]:
  - Equal Distance, Two Distance, or Distance and Angle.
  - Corner type: Chamfer, Miter or Blend.
- **Shell** [doc]:
  - Faces to remove (or a whole body, hollowed closed).
  - Tangent Chain.
  - Inside, Outside or Both thickness.
- **Move/Copy** (M) [doc]:
  - What it moves: components, bodies, faces or sketch objects.
  - How: Free Move, Translate, Rotate, Point to Point or Point to Position, with a settable pivot.
  - Create Copy leaves the original in place.

SolidCraft:

- **Automatic operation.** It probes the point halfway along the extrusion. Inside material, the operation is Cut. Otherwise it is Join when a body exists, else New Body. The probe runs again on every frame while you drag the arrow, so pushing into the part turns it into a cut. Choosing an operation by hand stops the automatic choice.
- **The arrow and its box.** The arrow's drag is the pointer ray projected onto the arrow's line, snapped to 1, 2 or 5 × 10ⁿ for the zoom (Alt drags freely). It writes into the same field you can type in, so the field is the one truth. The box by the arrow's tip takes typing at once, with its text selected.
- **Press Pull dispatches** on what is selected: edges go to Fillet; faces and profiles go to Extrude, a face becoming a linked face sketch.
- **Previews run off the UI thread on a scratch copy.** The last good preview stays up while the next computes, or when it fails.
- **Inputs filter the pick.** Each input of a feature accepts some kinds (profiles, faces, edges, bodies…), and only those light up under the pointer. A selection made beforehand goes to the input that accepts it.

### 3.5 Direct modeling

Fusion [doc]:

- **Switching to direct modeling** (`https://help.autodesk.com/cloudhelp/ENU/Fusion-Designs/files/ASM-DO-NOT-CAPTURE-DESIGN-HISTORY.htm`). The root component's menu or the timeline's gear changes the design to Direct Modeling Mode.
  - The timeline is deleted, after a confirmation. Holes, fillets and chamfers stay editable as browser items; Extrude, Revolve and Shell can only be dissolved or deleted.
  - Switching back makes everything one **Base Feature** at the timeline's start.
- **Base Feature** (`https://help.autodesk.com/cloudhelp/ENU/Fusion-Model/files/SLD-CREATE-BASE-FEATURE.htm`). It is a direct-modeling block inside a parametric design: one timeline item whose inner operations are not recorded. Inside it, Move/Copy defaults to Faces. Finish Base Feature leaves it, and Edit re-enters it.
- **Direct tools** (`SLD-MODIFY-SOLID-BODY`):
  - **Offset Face** shifts faces along their normals, with tangent curved neighbors following where possible.
  - **Replace Face** removes faces and trims or extends the body to target faces.
  - **Split Face** and **Split Body**.
  - **Delete on a face** heals the body: the other faces are extended to fill the gap, and it fails when they can't be (`https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/DeleteFaceFeatures.htm`). Deleting a fillet's face removes the fillet [comm].
  - **Remove** takes a body away as a recorded feature; **Delete** has no feature.
  - **Move/Copy of faces** moves them in place, with neighbors following [unverified].

### 3.6 The timeline

Fusion [doc] (`https://help.autodesk.com/cloudhelp/ENU/Fusion-Designs/files/ASM-USE-TIMELINE.htm`):

- **The marker.** The bar's buttons and a drag move the marker. Features after it are rolled back, and **new features are inserted at the marker** [comm].
- **Edit Feature** (double-click, or right-click) rolls back to just before the feature while it is edited [doc] (API, custom features).
- **Reorder** is a drag. It refuses to put a feature before something it depends on, including hidden dependencies such as a hole dimensioned from an edge [doc]/[comm].
- **Suppress** dims a feature and its dependents. Features can be grouped.
- **Icons.** Yellow is a warning: it computes, but something it refers to is lost. Red is an error: it can't compute. Compute All is Ctrl/Cmd+B [comm].
- **Upstream sketch edits** that merge or split profiles leave the Extrude warning, and you re-pick its profiles in Edit Feature [comm]. Lost faces or edges downstream show the same way.

SolidCraft (`doc/src/eval.rs`, `engine/cmd/edit.rs`):

- **Replay is linear and cached.** Each feature's evaluation is cached by a hash of its inputs, the parameters it reads and the incoming state. Previews share the cache. We get the same from node stamps.
- **Edit Feature** rolls the marker to just before the feature, opens its dialog filled in, and restores the marker afterwards.
- **Reorder** evaluates the new order first, and refuses it when something that worked before would break.
- **Face names** come from the feature that made the face, as ours do, with a geometric vote to follow faces through later features. Its notes count the vote as a weakness, because the kernel does not report face history. Ours names faces in every luce-cad modeling operation instead (its MODELING.md, Names).

### 3.7 Selection, marking menu, keys

Fusion [doc] (`https://help.autodesk.com/cloudhelp/ENU/Fusion-Model/files/SLD-SELECTION-FILTERS.htm`, `SLD-SELECTION-PRIORITY-FILTERS.htm`, `SLD-SELECTION.htm`):

- **Filters.** Each kind can be switched on or off: bodies, body edges, faces, vertices, sketch curves, points, profiles, constraints, dimensions, work geometry and more. Select Through lets a window reach hidden objects.
- **Priority.** Selection Priority (Component, Body, Face or Edge) leaves one kind on.
- **Window and freeform.**
  - Window left to right takes what is wholly inside; right to left takes what is inside or crossed.
  - Freeform: clockwise or counterclockwise, with the same split.
  - Ctrl/Cmd toggles a selection; Shift adds.
- **Select Other.** Press and hold to list everything under the cursor.
- **No edge-loop double-click** in the Solid environment, as far as I could find [comm]: that is the Form environment's.
- **The marking menu** [doc] (`https://help.autodesk.com/cloudhelp/ENU/Fusion-GetStarted/files/GUID-6514ABC1-CB75-4F0B-AB0E-316FAD36BA93.htm`).
  - The right button's ring holds Repeat, Press Pull, Redo, Hole, Sketch, Move/Copy, Undo and Delete.
  - Sketch opens a second ring: Finish Sketch, 2-Point Rectangle, Fit Point Spline, Project, Line, Offset, Sketch Dimension, Center Diameter Circle.
  - Commands can be flicked as gestures.
- **The S toolbox** searches commands and holds pinned ones.
- **Keys** [comm]: E Extrude, Q Press Pull, F Fillet, H Hole, M Move/Copy, D Dimension, L Line, R Rectangle, P Project. I found no default key for Create Sketch.

SolidCraft:

- **Pick order.** Its picking returns hits in this order: sketch points, sketch curves, vertices, edges, axes, then surfaces by depth.
- **Filters and priority.** A selection filter (faces, edges, vertices, sketch geometry, profiles, dimensions, constraints, bodies) decides which hit counts. While sketching, dimension labels and constraint glyphs win over geometry.
- **Double-clicks.** On an edge, a double-click takes its tangent chain; on a sketch curve, its chain.
- **Radial menu.** Its radial menu puts Repeat at the top. In a sketch it holds Line, Rectangle, Circle, Dimension and Finish Sketch.

## 4. Nodes are the history

### 4.1 Fusion features as nodes

| Fusion | Node | Changes |
|---|---|---|
| Create Sketch | Sketch | Passes its input body through beside its curves (§4.2). Made from a selected face (§5.1). |
| Extrude | Extrude | Takes profiles from the nearest Sketch upstream and the body flowing with them. Operation Auto by default. Gains the missing extents (§6.1). Faces as input. |
| Revolve | Revolve | Axis may be a picked sketch line or a body edge. |
| Press Pull | none: a gesture | As Fusion's: a profile makes an Extrude, an edge a Fillet, a face an Offset Face node (§6.2). |
| Fillet, Chamfer | Fillet, Chamfer | Created from selected edges with Shift+F or the S menu, radius on an arrow. |
| Shell | Shell (new) | Faces to remove, thickness, inside, outside or both. Built (stage 7). |
| Combine | Combine (stage 7; Boolean replaced) | Target and tool bodies, or a wired tool. |
| Move/Copy | Move (stage 7) | Bodies or faces, every Move type, pivot, Create copy. |
| Split Body, Split Face, Replace Face, Delete, Remove | Split Body, Split Face, Replace Face, Delete Face, Remove (stage 7) | The same code as Edit CAD's steps (§7). |
| Base Feature | Edit CAD | It is one: a direct-modeling block inside a history. |
| Mirror, Pattern | Mirror Body, Pattern | Unchanged. |

### 4.2 One body down the chain

Today a Sketch's result is its curves only, so the body is lost at every sketch. Each Join
or Cut then needs a second wire from the body (G3). Fusion's design state passes through every
feature. Ours should too:

- **Sketch** outputs its input set (the body, earlier curves) plus its own curves, tagged with
  the sketch's node id (a primitive attribute on the curves, `sketch`).
- **Extrude and Revolve** read the curves of the nearest Sketch upstream, the last `sketch` tag
  in the set. They build the new solid and combine it with the set's bodies by the operation.
  They drop the consumed sketch's curves from their output, as Fusion hides a consumed sketch.
  A second input, when wired, is the explicit target instead.
- **Fillet, Chamfer, Shell** pass the curves of sketches not yet consumed.

The chain then reads like the timeline: `Box → Sketch (on top) → Extrude (Cut) → Fillet`,
one wire. Profile keys still name sketch curves by index, scoped to the sketch's tag, so they
are unchanged.

### 4.3 The timeline, mapped

| Fusion timeline | Ours |
|---|---|
| The design at the end | The Output node (or the display flag, while you work) |
| New features go in at the marker | New nodes go in after the displayed node, as tools already insert them (`insert_after_display`) |
| Drag the rollback marker | Move the display flag up the chain. Because the Sketch passes the body through, displaying a sketch shows the body as it was there, as Fusion's rollback does. |
| Edit Feature (double-click) | Select the node: its handles, value boxes and inputs show in the viewport (§6), its rows in the panel. The display stays where it is, so the result downstream re-cooks live. Fusion rolls back here; we need not, because the node's handles draw on whatever is displayed. |
| Edit Sketch | Select the Sketch node and press Enter (or double-click it). The display flag moves to the sketch while you edit and back on Finish (Enter on empty, or Esc), as Fusion rolls back and forward. |
| Suppress | Bypass (B) |
| Reorder | Rewire. Fusion refuses a move before a dependency. We cook the new order first, and refuse it when a node that worked would fail (SolidCraft's rule), naming that node. |
| Yellow and red icons | Node badges: yellow, a warning (a lost reference, named); red, an error. |
| Manage Lost Projections | On the Sketch node: Re-link (pick again), Break link (keep as plain curves), Delete. |
| Capture Position | Not needed: moves are Transform nodes or Edit CAD steps. |

Fusion's timeline is linear. Ours is a graph: branches and merges are normal, and that is a
gain. A **timeline strip** (stage 8) can still show the chain from the displayed node back to the
CAD node's start as a row of icons along the network's bottom, with a marker you drag. It is a
second view of the same nodes, not a second history.

### 4.4 Upstream edits

Editing a sketch's dimension re-solves it and re-cooks every node after it. The pieces
that make this hold already exist:

- profile keys name regions by the curves round them;
- face names say which feature and sketch curve made each face;
- edge references name edges by their two faces.

What changes:

- **A lost profile** (its curves gone) is an error on the Extrude: "Profile 0+,1- is gone: pick
  profiles again". It is never quietly another region.
- **A lost face under a sketch** is an error on the Sketch, with Re-link on its panel and in the
  viewport.
- **A lost projection** is a warning, and those curves draw yellow. Their constraints stay.

## 5. The sketch, changed

### 5.1 Starting a sketch

- **From a face.** At the Faces level (or Smart), select a flat face and choose Sketch from the
  A menu, or press K. Fusion has no default key for it, and K is free here.
  - The Sketch node is put after the displayed node with Plane: Face, that face's name, and the face's loops projected (§5.4).
  - The view looks straight at it. Editing starts at once, with Line ready.
- **From a plane.** With nothing selected, Sketch shows the three origin planes as squares in
  the viewport, as Fusion does. A click picks one.
- **The body stays visible.** While editing, the body the sketch passes through is drawn, dimmed. In Fusion's "Slice" spirit, the part in front of the plane may be cut away by a toggle (§10, question 8).
- **Editing no longer needs the display flag** (G4). Selecting a Sketch node and pressing Enter edits it. The editor draws the sketch from the selected node, and the viewport shows that node's result.

### 5.2 Dimensions while drawing

As Fusion's heads-up boxes and SolidCraft's `sketch_dims`:

- **Which boxes.** Once a shape's first point is down, value boxes follow the cursor beside what they measure:

  | Tool | Boxes |
  |---|---|
  | Line | Length and Angle |
  | Rectangles | Width and Height |
  | Center Diameter Circle | Diameter |
  | 2- and 3-point circles | Diameter |
  | Center Point Arc | Radius, then Sweep |
  | Polygon | Radius and Sides |
  | Slots | Length, then Width |
  | Ellipse | Major, then Minor |
  | Offset | Distance |
  | Fillet, Chamfer | Radius or Distance |

- **Typing.** Typing goes into the first box, replacing its text, and locks the value; Tab and Shift+Tab move between boxes. A locked box keeps its value, and the cursor is steered by it.
- **Enter places the point.** The typed values become driving dimensions in the same undo step. An expression stays an expression, through the units module that the parameter fields already use ("25.4 mm", "1 in", "10 + 5 mm").
- **Esc** leaves the boxes and ends the shape.
- **A typed angle stops Horizontal and Vertical inference.**

`sketch_value.luc` becomes a row of fields with a focus index. Its `ask` stays for one-value
tools. The tool table in `sketch_tools.luc` gains each tool's boxes per click.

### 5.3 Dimensions and constraints on the canvas

- **Drawing.** Dimensions are drawn as drawings draw them:
  - extension lines, a dimension line with arrows and the value over it;
  - radius and diameter with a leader;
  - angles with an arc.

  A dimension's label place is kept in the sketch text (an offset from its entities), so it stays where it was put.
- **A click** selects a dimension or a constraint glyph. Labels and glyphs win over geometry under the pointer, as in Fusion and SolidCraft.
- **Dragging the label** moves it, as one undo.
- **Double-click** opens the value box on the label (the same box as §5.2). Enter re-solves. While you type, a click on another dimension inserts its name (d3), as in Fusion.
- **Delete** removes the selected dimensions and constraints (G7).
- **The right-click menu** on a dimension offers Driven/Driving; on a constraint, Delete.
- **When a new dimension would over-constrain,** Fusion warns and makes it driven [doc] (SK-STUDY §4.3). Ours makes it driven, says so in the status line and lights the dimensions and constraints it repeats (polish, §9).
- **Hovering a glyph** lights what it holds.

### 5.4 Projection and offset on a face

- **The face's outer and inner loops** are projected when the sketch is made on it. They are linked, fixed and drawn purple. This is what the owner asks for, SolidCraft's default, and Fusion's `isAutoProjectGeometry` [doc]. A project setting turns it off.
- **Edges referenced by a constraint or dimension** are projected too, as with Fusion's `isAutoProjectEdgesOnReference`. That covers an edge of the body that is not on the face.
- **Project accepts a face** as well as an edge: a click inside a face brings its loops.
- **Offset of a projected loop** makes one Offset relation (luce-cad, §8 item 5): the copies, one distance shown as one dimension, tied to the loop. When the face grows upstream, the projection is cast again, and the offset follows. This is the owner's case: "retain that face projection so that I can easily do offset".
- **Break Link** turns linked curves into plain ones.

### 5.5 Profiles you can see and use

- **Shading.** Every closed region is shaded with a translucent fill (Fusion's Show Profile [doc], on by default with a toggle in the viewport's sketch row). The region under the pointer is lit.
- **Picking.** At the Shapes level, a click inside a region selects the profile; a click on a curve selects its chain, as now. Shift adds.
- **Extrude with profiles selected** makes the Extrude right after the Sketch. It is E inside the sketch, where Rotate means nothing, Shift+E in the CAD context, or the S menu (§10, question 3):
  - with those profile keys;
  - the operation Auto;
  - its arrow and distance box in the viewport, the box taking typing at once.

  Enter finishes, and the display moves to the Extrude. Esc removes it.
- **With nothing selected,** Extrude takes the sketch's closed shapes (today's default).
- **Revolve (no Fusion key; the S menu)** works the same way, then asks for its axis: a sketch line, a body edge, or the plane's axes.
- **After the sketch is finished,** its profiles stay pickable while its node's result is shown. Downstream nodes consume them and stop showing them.

## 6. Features in the viewport

### 6.1 Extrude

- **The arrow.** The arrow sits at the middle of the profiles' area, along the plane's normal. Dragging it sets the distance: the pointer ray projected onto the arrow line, snapped to 1, 2 or 5 × 10ⁿ for the zoom, Cmd for free.
- **The box.** The distance box sits by the tip. The panel row, the box and the arrow are one value.
- **Operation Auto** probes the point halfway along the extrusion: inside a body it cuts, otherwise it joins when there is a body, else it makes a new body. Choosing one by hand keeps it. The row shows which Auto chose.
- **Rows added:**
  - Direction: One side, Two sides, Symmetric. Two sides has a second distance and a second arrow.
  - Start: Profile plane, Offset.
  - Extent: Distance, To object (pick a face or body), All.
  - Taper angle, with a side handle.
  - Thin.
- **Faces as input.** A planar face is a profile (Press Pull's case).
- **The preview** runs on the compute worker, as every cook does. The new material is tinted; material a Cut takes is a ghost. The last good result stays up while one cooks, or when one fails.

### 6.2 Press Pull

Q is the Select tool here, so Press Pull takes Shift+Q, or the S menu. It dispatches as Fusion's does [doc]:

- a profile makes an Extrude;
- an edge makes a Fillet;
- a face makes an **Offset Face** node: the face moved along its normal, its neighbors following, with an arrow.

Offset Face needs luce-cad's local face operations (§8, item 9). Until they exist, a planar face whose neighbors are square to it can go to an Extrude of the face, Join or Cut, which gives the same solid. Any other face is refused with the reason.

### 6.3 Fillet and Chamfer

- **Starting.** Select edges at the Edges level, then Fillet (Shift+F, or the S menu) or Chamfer.
  - The node is put after the displayed node with those edge references.
  - The radius has an arrow at the first edge and a box.
  - A double-click on an edge selects its tangent chain. Ours already has this gesture; Fusion's Solid environment does not.
- **Rows to add:**
  - Fillet: Corner type (Rolling ball, Setback), Chord length, Variable radius (stage 5b), Rule fillet (all edges, or between faces). Asymmetric radius and Full Round come later.
  - Chamfer: Equal, Two distances, Distance and angle; corner type Chamfer, Miter or Blend.
- **Failure is never silent.** A blend luce-cad cannot make fails with its reason on the node. The tracked G3 bug is the counter-example: a cube with four top edges filleted G3, then a fillet or chamfer of the rounded top chain, fails without a word.

### 6.4 Shell, Move/Copy

- **Shell.** Select faces to remove, then Shell. The thickness has an arrow, and its rows are Inside, Outside, Both and Tangent chain.
- **Move/Copy of bodies** is the Transform node, with "Create copy".
- **Move/Copy of faces** is Edit CAD's (§7, stage 6).

### 6.5 Selection

Our levels are Fusion's selection priority:

| Fusion | Our level |
|---|---|
| Select Body Priority | Object |
| Select Face Priority | Faces |
| Select Edge Priority | Edges |
| (Fusion's default: hover decides) | Smart |

Built in the parity round (§9, "Fusion parity round"):

- **Profiles at Faces and Smart,** when a sketch's result is shown: a profile wins over the face it lies on.
- **Sketch points and curves at Smart.**
- **Each tool's inputs filter the pick.** While Extrude's "To object" waits for a face, only faces light up.
- **Window and crossing,** by drag direction, as Fusion's [doc]. This replaces the owner's earlier answer 5 ("everything inside, either way"), now that Fusion parity is the rule.
- **Repeat** leads the A and S menus in a CAD context.

## 7. Edit CAD: direct modeling

Edit CAD is Fusion with "Do not capture design history" [doc], and Fusion's Base Feature
when it sits in a chain:

- the recipe is its undo;
- each tool is a step on the model so far;
- nothing earlier changes when something later does.

**Sketches inside Edit CAD.**

- **A sketch is an object of the model,** held in the geometry set as a sketch component: its text and its frame, or its face name. It is not a step's parameters. It needs a sketch entry in luce-cad's `CadGeometry` (or a text attribute on a curve set; §10, question 6).
- **Steps edit sketches.** A Sketch step creates one, on a picked face or plane, with the face's loops projected once (the projection is not live, since nothing re-cooks). An Edit Sketch step replaces its text: the editor is the same Sketch editor, working on that object. An Extrude made earlier does not change, as in Fusion's direct mode.
- **`EditStep` gains a `text` field** for the sketch text and for profile keys.

**Steps, each one luce-cad operation:**

| Step | On |
|---|---|
| Sketch, Edit Sketch | a face or plane; a sketch object |
| Extrude, Revolve | a sketch's profiles (Auto operation against the models) |
| Press Pull | faces: planar faces move along their normal (Offset Face); edges: fillet |
| Move Face | faces: translate or rotate with the gizmo, neighbors re-intersected |
| Offset Face | faces: along their normals |
| Delete Face | faces: removed and healed, the neighbors extended to close the gap (Fusion's Delete with heal [doc]); "Remove" keeps today's open-shell delete |
| Replace Face | faces → a target face or surface |
| Fillet, Chamfer | edges (today) |
| Shell | faces to remove |
| Combine | two models: Join, Cut, Intersect |
| Split Body, Split Face | a model or face by a plane or face |
| Move/Copy | models (today's gizmo), with Copy |

The tool strip shows these at the levels they act on. The gizmo at the Faces level becomes
Move Face. Value boxes and arrows are the same as the nodes' (§6). They edit the last step,
the way the tool bar edits it today (`set_last_step`).

## 8. What luce-cad needs

In build order. Built ahead of the UI stages (2026-10-11, luce-cad docs/MODELING.md has the
details): 4 (`CadSketch.project_face`, `project_end`, `relink` with gained edges), 5
(`ConstraintKind.offset`, `offset(..., relation = true)`), 7 but Thin and a face as a profile
(`extruded_sides`, `extruded_through`, `extruded_to`), 8 (`revolved_about`, `edge_axis`), 9
(`CadDirect.offset_faces`, `moved_faces`, `rotated_faces`, `replaced_faces`, `deleted_faces`), 10 for
analytic faces (`shelled`), 11 (drafted walls, open ends and loops between two curved faces;
B-spline faces in booleans at any angle), and Split Body, lumps and Move/Copy (`split_by_plane`,
`split_by_face`, `lump_count`, `lump`, `moved_body`).

1. **Profile fills.** `CadModeling.profile_fills(set, keys)` triangulates profile regions with the planar polygon mesher (`polygons/`) for shading. `profile_anchor(set, keys)` gives the middle and area, where the arrow goes. Closed splines as profiles (MODELING.md lists them as missing).
2. **Sketch tags.** Curves made by a sketch carry its tag. `extruded` and `revolved` take the tag and use only those curves. This keeps keys stable when other sketches' curves are in the set.
3. **Inside test.** `CadModeling.inside(model, point)`, from the boolean classifier's rays (`rays.lucb`). Auto operation needs it.
4. **Face loops projected.**
   - `CadSketch.project_face(model, face name, frame)` adds the face's loops as linked curves, linked by the face's name and each edge's reference.
   - The existing `relink` then keeps them. When a loop gains or loses edges, the edges it still has keep their curves, and the change is a warning.
   - A link on a vertex (a point) as well as on an edge.
5. **Offset relation.** One constraint ties a chain's copy to its source at one distance:
   - lines parallel at that distance;
   - arcs concentric, their radius differing by it;
   - corners where neighbors meet.

   It is one dimension. Today each line copy gets its own (G9).
6. **Dimension placement in the sketch text.** Each dimension's label offset, so a moved label stays.
7. **Extrude extents.**
   - Two distances, taper (side faces become planes at an angle, cones from arcs), start offset.
   - To object: the extrude is cut by the target face's surface, which is a boolean with the half-space beyond it.
   - All.
   - Thin: an offset profile pair.
   - A planar face as a profile: its loops as a region.
8. **Revolve about any axis** in the plane (a line given by two points).
9. **Local face operations,** built directly like `local_blend` (no booleans), on bodies of planes first, then cylinders, cones and spheres:
   - Offset Face and Move Face (the face's surface moved, its neighbors' loops re-intersected);
   - Delete Face with healing (the neighbors extended until they close);
   - Replace Face.

   Each declines what it cannot do with a reason, never a broken solid. Face names carry through.
10. **Shell.**
    - Analytic surfaces offset to analytic ones (planes, cylinders, cones, spheres, tori); B-spline faces offset by fitting a degree 5 approximation within tolerance.
    - The inner shell is built from the offset faces, and the removed faces are opened.
    - Start with bodies of planes and cylinders.
11. **Blends between curved faces.** This covers an earlier fillet's edges (plane against swept B-spline, and the rounded chain around a top face), and is MODELING.md's limit 2. The tracked G3 bug (fillet or chamfer of the rounded top chain after a four-edge G3 fillet fails silently) is the first case; whatever the separate fix lands, Stage 5 builds on it.
12. **Fillet options.**
    - Setback corners at G1: the same patch with one row (MODELING.md's limit 1).
    - Variable radius along an edge.
    - Chord length.
    - Chamfer by two distances, and by distance and angle.
13. **A sketch in `CadGeometry`.** A component holding a sketch's text and frame, for Edit CAD (§7).

## 9. Staged build plan

Each stage ends with `luc test` green in luced-3d (and luce-cad when it changed), a preview
capture for the docs, and luced-3d's docs/MODELING.md updated. Tests drive the workspace as the
existing `sketch_node_tests` and `cad_node_tests` do: events into the editor, then the node's
texts, values and the result's volume checked.

**Stage 0: fixes found here.** Done 2026-10-11 (`sketch_glyph_tests`, `selection_rules_tests`).
- The Sketch's second text starts empty (G15): CAD nodes start with empty texts. Test: a new Sketch's Face row reads "None picked". Plane: Face with no face fails with "Pick the face".
- Constraint glyphs pickable and deletable (G7). Test: two lines, Parallel, click its glyph, Delete. The constraint count drops and the lines can be dragged apart.
  - Built: `sketch_glyphs.luc` places glyphs and labels once for drawing and picking; glyphs on one place stand side by side. A click on a glyph selects its constraint (lit, what it holds lit); Delete removes selected constraints and entities as one undo step. A right click on a glyph selects it and opens the viewport's right-click menu (`viewport_menu.luc`) with Delete constraint.
- Box selection in a sketch takes only what lies wholly inside the box, either way it is dragged (owner's answer 5; luce-cad `boxing.lucb`); at Shapes, chains wholly inside.

**Stage 1: see a profile, extrude it** (G1–G4; luce-cad 1–3). Done 2026-10-11 (`cad_flow_tests`; luce-cad `profile_tests`). As built, after the owner's answers:
- No new plain keys (answer 3): Extrude, Finish Sketch, Sketch on face, Fillet and Chamfer are reached by the viewport's new right-click menu (`viewport_menu.luc`, selection-aware), the A and S marking menus and the menu bar's Create and Modify (`cad_commands.luc`, Actions' commands). E stays Rotate.
- The Sketch passes its input's bodies on beside its curves (answer 2). A set carries one sketch's curves, its nearest one's (the sketch plane is the set's), so no separate sketch tag attribute was needed; an earlier sketch's unconsumed curves do not pass a later Sketch. Extrude and Revolve drop the curves they consume.
- Rollback (answer 1): selecting a Sketch gives it the display flag, remembering the node shown before (`Workspace.sketch_return`); Finish Sketch, or selecting another node or nothing, shows that node again.
- Profiles shaded with `profile_fills` and picked at Shapes and Smart (a press in a region that is not dragged into a box); the arrow stands on `profile_anchor`. Auto (answer 4) probes the anchor halfway along with `CadModeling.inside`; the row shows "Auto", not which operation it chose (open).
- Sketch on face is wired (face selected → Sketch after the displayed node, edited at once); its loops are not projected yet (stage 3). A face's Extrude and Press Pull show disabled until stage 4. Fillet and Chamfer of selected edges make the node after the displayed one (stage 5 adds the radius arrow).
- Profile hover runs luce-cad's arrangement on each pointer move; fine for sketches of tens of curves, a cache by sketch revision is the next step if large sketches lag.
- The Sketch passes its input through, with tagged curves. Extrude and Revolve read the nearest sketch and combine with the chain's body, Auto by default. The second input stays as an explicit target.
- Profile fills in the sketch, and profiles at the Shapes level.
- E makes the Extrude with the selected keys. Its arrow and box appear in the viewport.
- Editing a sketch no longer needs the display flag.
- Tests:
  - A 40 × 20 plate with a hole shows two shaded regions, the plate's ring and the hole's disc, and a click in each selects its key.
  - Clicking the plate and pressing E makes an Extrude whose Profiles text is the plate's key. Its volume is the plate's area times 10.
  - `Box → Sketch on top → circle → E → drag down`: Auto becomes Cut, and the volume drops by πr²d.
  - Changing the circle's diameter re-cooks to the new volume, with the key kept.
  - Arrow drags are tested through the same value path as typing.
  - A preview capture of the shaded profiles.

**Stage 2: sizes while drawing, dimensions on the canvas** (G5, G6; luce-cad 6). Done 2026-10-11 (`sketch_dimension_tests`; luce-cad `dimension_tests`). As built:
- Value boxes are drawn and typed by the editor itself (`sketch_typing.luc`), not widgets: the viewport takes text while they show, so tool letters and the A/S/D menus wait, and Tab stays theirs. Boxes: Line (Length, Angle), 2-point and center rectangles (Width, Height), 3-point rectangle (Length, then Width), center-diameter and 2-point circles (Diameter: Fusion's box for those tools), center point arc (Radius, then Sweep), polygons (Radius, Sides). A typed line angle is dimensioned against the sketch's x axis (the origin, polish below).
- Dimensions are laid out by luce-cad (`CadSketch.lay_out`, `dimensions.lucb`) and drawn by `sketch_dimensions.luc`; labels keep their place in the sketch's text (`g` lines). A click on a selected dimension opens its box on the label (this covers the double-click). Driven/Driving and Edit value are on the right-click menu. Hovering a glyph lights what it holds (stage 0).
- Not built: inserting another dimension's name while typing (no named parameters yet), expressions kept as text (a typed value is stored as its number).
- Plan as written:
- Value boxes per tool and stage, Tab, Enter, locked values steering the cursor.
- Typed values become dimensions in one undo.
- Dimensions drawn with extension lines and arrows, clickable, draggable, double-click to edit, Driven/Driving, the over-constrain notice.
- Tests:
  - A Line typed `25` Tab `30`, Enter: its length dimension reads 25 mm and its angle 30°, one undo removes both.
  - A Rectangle typed `40` Tab `20`: two dimensions.
  - `1 in` gives 25.4 mm.
  - A double-click edit re-solves.
  - A third dimension on a fully constrained line is added driven, in parentheses, with the notice.
  - A dragged label keeps its place through save and load.

**Stage 3: sketch on a face** (G8, G9; luce-cad 4, 5). Done 2026-10-11 (`sketch_face_tests`, `selection_rules_tests`; luce-cad `link_tests`, `profile_tests`). As built:
- Sketch on face (right-click menu, A, Create; no K, answer 3) makes the Sketch; its first cook projects the face's loops, linked (`sketch_node.evaluate_sketch`, luce-cad `project_face`), so they come from the body however the sketch was made. Projected curves draw purple and hide their Fix glyphs; the editor's lines are lifted a hair toward the camera so the loop shows over the face.
- G16: the editor never cooks the body. Each Sketch cook reports a state (`SketchState`: its plane, its text when casting changed it, its lost curves) through the result store and the worker's report to the node (`Node.sketch_state`); the editor's frame and text come from it (`sketch_frames.FrameCache`), the last face frame standing while the next cooks. Project's cast is made by the cook too: while Project is the tool the request names the sketch (`Network.projecting`), and the worker's report carries every edge's samples and reference as text (luce-cad `CadShadows`), which the editor draws, picks and projects from. Without the worker (tests, scripts) the UI-thread cook makes the same.
- Offset makes one Offset relation over the chain (luce-cad `relation = true`): one dimension, drawn across the copy's middle and its source; a projected loop's offset follows the face as the body changes.
- Lost links: the cook names them; they draw yellow (over the edge projected again in their place when the face's loop gained it), the node's badge is yellow (a warning), red when the sketch fails (its face gone). Right-click on selected projected curves: Re-link (Project's next edge click points them at that edge) and Break link (plain curves); Delete removes them. Badges show on every node with a warning or a failure.
- Slice (right-click in a sketch, checked while on): the sketch node's shown body is clipped by its plane, keeping what is behind it (`slice_view.luc`, luce-geocore's Clip on the CAD preview, keyed apart so the whole body's products are not reused). Display only; the clipped body shows no B-rep edges.
- Not built: auto-projection of edges a dimension refers to, a project setting to turn the face's projection off. (Project of a face and a body came with the polish below.)
- Follow-ups: the Operation row reads "Auto (Cut)" (the cook reports Auto's choice, `Node.automatic`); CAD component boxes (Edit CAD, CAD networks) take a B-rep face or edge only when all of it lies inside, either way dragged (luce-3d `wholly`); an Extrude made from a rolled-back sketch goes in right after the sketch and keeps the display (Fusion's marker at the new feature; the later features stay rolled back until selected); profile hover reads a layout made once per sketch (luce-cad `CadProfileMap`).
- Plan as written:
- Faces level, select a flat face, A → Sketch (or K): the node after the displayed one, the face's loops projected and linked, Look At.
- Project accepts faces.
- Offset of a projected loop is one relation.
- Lost-link handling: Re-link, Break link, Delete.
- The editor's view of the input body comes from the worker's cook, not a cook on the UI thread (G16).
- Tests:
  - A box's top face gives a sketch with four linked lines at the face's corners.
  - Offset inward by 2 gives one dimension.
  - Changing the box's width upstream moves the projection, and the offset follows (corner positions checked).
  - Deleting the face upstream (a Cut through it) warns and draws the lost curves yellow.

**Polish after stages 2–3.** Done 2026-10-11 (`sketch_reference_tests`, `sketch_face_tests`; luce-cad `sketch_origin_tests`, `shadow_face_tests`). Every behavior follows Fusion's where Fusion defines one (owner, 2026-10-11):
- **Labels apart.** Dimension labels laid out automatically step to the other side or a row further out (round the circle for a radius) when another label is there or another dimension's lines cross them, in a second pass against all the others; a label the user dragged keeps its place (luce-cad `lay_out(at, pixel, step)`). Constraint glyphs keep off the labels and each other. Dimensions and glyphs are placed once per sketch change or view (`SketchGlyphs` shares the dimensions' key).
- **The origin.** Every sketch shows its origin point and x (red) and y (green) axes across the view (`sketch_origin.luc`). Select, the constraint tools and Sketch Dimension pick them where nothing else is; drawing tools snap to them. The entities are made in the sketch when first held to (luce-cad `CadSketch.origin`: fixed, axes construction), as Fusion projects its origin when referenced; never in a profile, never deleted, boxed or trimmed at.
- **Typed values as Fusion keeps them.** A line's and a 3-point rectangle's typed Angle is an angle dimension from the x axis; an arc's Sweep an angle dimension on the arc (luce-cad `ConstraintKind.sweep`); the circle's box stays Diameter (Fusion's). Sides is no dimension (Fusion has none): the polygon is made with that many sides and held by luce-cad's Polygon constraint (`ConstraintKind.polygon`, `CadSketch.add_polygon`) on its one construction circle, as Fusion's: through the corners when inscribed, touching the sides at their middles when circumscribed; it stays regular as it is dragged, and the typed Radius is that circle's. Its glyph (Poly) sits on the circle.
- **Over-constraints lit.** A constraint refused, a dimension added driven, or Make driving refused lights (warning color) the dimensions and constraints the over-constraint runs through, and what they hold, until the next change or Esc (luce-cad `find_dependent`: each constraint that, made driven, leaves fewer redundant or conflicting).
- **Project of a face and a body.** With Project, a click inside a face (off its edges) brings every edge of its loops, the face nearest the camera where several cast there, its loops lit under the pointer first; the face is remembered so edges it gains upstream come too. Project body (the right-click menu while Project is the tool, Fusion's Bodies filter) brings the body's outline: the edges bounding the body's shadow, one of each pair casting the same shadow. Silhouettes come too, as Fusion's: a cylinder seen from its side brings its two silhouette lines and its rims seen edge-on (lines), one closed profile, linked to the face so they follow it (luce-cad `silhouettes.lucb`; preview scene `cad_project_silhouette`). All of it comes from the worker's cast (luce-cad `CadShadows` now carries faces and edge heights).
- **Projected curves purple.** They were also drawn among the fully constrained (white) lines, which covered them: now they draw only in Fusion's purple, their points too.
- **Slice as Fusion's.** Fusion's Slice (AU class MFG121944, Jeff Strater's handout, page 10: a sliced cylinder) removes the body in front of the sketch plane and caps the cut: the cap lighter than the body, black diagonal hatch, a dark outline, the body's edges round the cut, the sketch's curves and profiles over the cap. Ours now matches: the body is sliced (luce-cad `CadModeling.sliced`, a boolean with the half-space in front, cached by the body's stamp and the plane in each cook's `Slicer`), so its B-rep edges show round the cut; the cap's loops travel to the editor as a sketch's text in the worker's report (`section`, as Project's cast does), and the editor fills the cap, hatches it (`OverlayLines.add_hatch`, spacing following the zoom) and outlines it under the sketch. The UI-thread cook does the same. A body the boolean cannot cut shows its tessellation clipped, uncapped, with the reason on the node.

**Stage 4: Extrude, Revolve, Press Pull complete** (G10, G11; luce-cad 7, 8). Done 2026-10-11 (`cad_extent_tests`; luce-cad `direct_tests`). As built, Fusion's options and defaults:
- **Extrude** (`cad_features.luc`): Start Profile plane or Offset; Direction One side, Two sides or Symmetric (Measurement Half length, Fusion's, or Whole length); per side Extent Distance, To object (a face picked in the viewport with Pick object, kept by name, plus an Offset) or All (Flip for one side), and Taper angle in Fusion's sign (Autodesk's API reference: negative tapers in, positive out; luce-cad's is the opposite, turned over in the node). Sides of different extents are built apart and joined. Operation stays Auto by default (owner's answer 4).
- **Revolve**: Axis Picked (Pick axis: a sketch line, construction lines too, kept by index so it follows the line; or a straight or round body edge, kept by reference) or an origin axis X, Y, Z, projected onto the sketch plane as Fusion's Project Axis; Type Partial or Full; Direction One side, Two sides or Symmetric (the angle each way, Fusion's). A Revolve made from the sketch (right-click, A, Create) asks for its axis at once. The worker gets the sketch's text for a line axis (`Network.sketch_text`).
- **Press Pull** (right-click, S, Modify › CAD features; no key, owner's answer 3) dispatches as Fusion's: in a sketch Extrude, on faces an **Offset Face** node (`CadDirect.offset_faces`, tangent faces following), on edges a Fillet. **Extrude face** makes a Sketch on the face (its loops projected) and an Extrude of it.
- **Handles** (`feature_handles.luc`, `handle_lines.luc`): the cook reports where they stand (through the worker, like Auto's choice), so the viewport never cooks to draw them. An arrow per Distance side from the start, a taper ring beside each (pulled out sideways: positive), an angle ring per Revolve side, Offset Face's arrow, a blend's radius arrow out of its first edge's corner (luce-cad `edge_frame`, `face_point`). Drags snap (grid steps, whole degrees; Cmd frees), one undo each; a click on a handle opens its value box; a feature made from the viewport opens it by itself.
- Not built at stage 4, built in the parity round below: Thin; Start From object; a planar face as a profile directly; Start offset with To object or All; To object for Revolve; Objects To Cut; To object's Extend options; the per-tool selection filter.
- Plan as written:
- Two sides, taper, start offset, To object, All, Thin, faces as input.
- Revolve about a picked line.
- Press Pull (Shift+Q) dispatching on faces and edges.
- Tests:
  - Volumes against closed forms (a tapered square prism is a frustum).
  - To object onto a slanted face matches a boolean of the long extrusion with that face's half-space.
  - Press Pull on a box's top face by 5 adds 5 × area; on an edge it makes a Fillet node with that edge's reference.

**Stage 5: Fillet and Chamfer in the viewport** (G12; luce-cad 11, 12). Done 2026-10-11 (`cad_blend_view_tests`; luce-cad `rule_tests`, `chamfer_side_tests`). As built:
- Edges picked at the Edges level (a second click takes the tangent chain), Fillet or Chamfer from the right-click menu, S or Modify (no Shift+F, owner's answer 3): the node after the displayed one, its radius arrow and box (`cad_blends.luc`).
- Fillet: Type Fillet or **Rule fillet** (All edges or Between faces of two picked face sets; Rounds, Fillets or both; luce-cad `rule_edges`, found again each cook); Continuity G1 (Tangent), G2 (Curvature), G3; Tangent chain.
- Chamfer: **Equal distance, Two distances, Distance and angle** (luce-cad `chamfered_sides`; the first distance on the face more of the picked edges lie on, Flip swaps; straight outside edges between flat faces for now, said on the node otherwise).
- The owner's case is a regression through nodes: a cube's uprights filleted G3, then the rounded top chain filleted G1, G2, G3 and chamfered: closed, watertight tessellations of 18 faces, smaller than the cube.
- Failures are said on the node; while a drag makes a blend fail the viewport keeps its last good result (worker and local cook), and its handles stay; released, it shows the input with the reason.
- Not built at stage 5: Full round fillet, variable radius, chord length, G1 setback corners (luce-cad limit 1), Fusion's chamfer corner types. The parity round built Full round, chord length and the corner types; variable radius and G1 setback corners stay open. (Two distances and Distance and angle chamfers on curved and inside edges came with luce-cad f19fb15.)
- Plan as written:
- Edges selected, Shift+F, a radius arrow and box, a double-click for the chain. Chamfer types.
- Clear failures.
- Builds on the separate fix for the G3 rounded-chain bug.
- Tests:
  - That bug's case as a regression: a cube, four top edges G3, then a fillet of the rounded chain, and a chamfer of it. Both either succeed with a closed solid and the expected face count, or fail with a message. Never a silent pass-through.
  - Volumes of Two distances chamfers against closed forms.
- 5b: variable radius and G1 setback corners.

**Stage 6: Edit CAD direct modeling** (G13, G14; luce-cad 9, 10, 13). Done 2026-10-12 (`edit_cad_direct_tests`; luce-cad `sketch_object_tests`, `cad_edits_tests`). As built:
- **Sketches are objects of the model** (owner's answer 6): luce-cad's `CadSketches`, a geometry set component holding each sketch's name, text, plane and visibility; it places, joins and saves with the set, and the Outliner lists the sketches under the node. Steps (`edit_cad_sketches.luc`): **Sketch** (an origin plane, or a flat face whose loops are projected once, when it is made), **Edit Sketch** (the text replaced, the plane kept) and **Sketch Visibility**. The editor is the Sketch node's own (`sketch_source.luc` reads and writes either); a drawing commit changes the step that made the sketch while it is the recipe's last, else adds an Edit Sketch step, one undo each. The model's sketches reach the viewport from the cook as text (`state_of`), so the editor never cooks; sketches shown and not edited draw on their planes (`model_sketch_view.luc`). Project casts the model's own edges; Slice cuts the model by the sketch's plane.
- **Extrude and Revolve steps** take a sketch's picked profiles (none: its closed shapes) with the nodes' code and rows (`cad_features.luc`): every option, the arrows, taper and angle rings, the value box, Auto (a Cut into a model, else Join, else New body). Operations act Fusion's way on several bodies: Join merges the new body with the models it touches, Cut and Intersect act on the models it reaches, the others stay. A feature hides its sketch, as Fusion's does. To object waits for its face once chosen in the tool bar; a Revolve waits for its axis (a sketch line, construction too, or a body edge; an origin axis in the tool bar and Enter).
- **Direct steps on the selection** (`edit_cad_faces.luc`): the gizmo's Move at the Faces level moves and turns faces with their neighbors following (luce-cad `CadEdits.transformed_faces`), whole models at Object; **Move/Copy** (its tool bar: X, Y, Z, the angles, Create copy, which copies bodies); **Press Pull** (profiles Extrude, faces Offset Face, edges Fillet); **Offset Face**; **Delete** (models go, faces heal: Fusion's Delete; a box's side, with nothing to close it, is refused with why); **Remove Faces** (the old open delete); **Replace Face** (then the target face clicked); **Shell** (faces opened, a whole body a closed void; Inside, Outside, Both); **Combine** (the target selected, then the tool bodies clicked, Enter; Join, Cut, Intersect, Keep tools); **Split Body** (by a clicked face's surface or an origin plane with an offset; each piece a model); Fillet and Chamfer as before. Faces a step makes are named for its place in the recipe (`#s<n>`); unnamed imported faces are named when the recipe starts (`CadEdits.named_models`).
- **Reached** by the viewport's right-click menu (selection-aware: faces, edges, bodies, or nothing: Create Sketch, Edit Sketch, Show/Hide Sketch, Create), the A menu (Create Sketch first, on the selected face or an origin plane), the S menu (Press Pull, then the tools the level takes) and Modify › CAD features; Create holds Create Sketch, Edit Sketch, Show/Hide Sketch. No new plain keys.
- **Handles and tool bar**: the last step's Extrude, Revolve, Offset Face, Fillet, Chamfer or Shell shows the nodes' handles (`feature_handles.luc` drags the step's numbers), its value box opens by its arrow, its rows are in the tool bar.
- **Failures**: a step that cannot be built says why under its rows in the tool bar and on the node (WARNING), and the model before it shows; a step waiting for a pick says what it waits for. While a drag makes the last step fail, the node fails instead so the viewport keeps the drag's last good result, as a feature node's does.
- **Selection** stays on the same B-rep faces and edges when a step meshes them again (luce-cad `CadEdits.carried`), so a face can be moved again at once.
- Follow-ups from stages 4–5: a Revolve node waiting for its axis is a warning, not an error; arrows keep at least 44 points on screen (Fusion's manipulators keep their size), and a drag moves the value by how far the pointer goes along the arrow.
- Not built at stage 6, closed with stages 7–8 (below), but Combine's New component and picking a sketch's curves in the viewport to edit it: Split Face (luce-cad has no face split); Replace Face onto several target faces or a surface body, with Tangent chain; Shell's Tangent chain (luce-cad shells the faces named); Move/Copy's Point to Point and Point to Position, a settable pivot, copies of faces; Combine's New component; Delete healing more than one strip or corner at a time (luce-cad limit 7); a sketch's plane redefined after it is made; a body's Remove as a recorded feature apart from Delete; picking a sketch's curves in the viewport to edit it (Edit Sketch is a menu of the model's sketches).
- Plan as written:
- Sketch objects and the Sketch/Edit Sketch steps.
- Extrude and Revolve steps.
- Press Pull, Move Face, Offset Face, Delete Face with heal, Replace Face, Shell, Combine, Split, Move/Copy.
- Tests:
  - Each step's undo restores the model exactly (its stamp).
  - An L-bracket's inner wall moved 3 mm changes the volume by 3 × the wall's area.
  - Delete Face on a fillet's face heals back to the sharp edge, giving the unfilleted volume.
  - Editing a sketch after its extrude leaves the extrude as it was.

**Fusion parity round** (2026-10-12; `cad_parity_tests`, `selection_rules_tests`, `cad_flow_tests`, `cad_node_tests`; luce-cad `extent_start_tests`, `thin_tests`, `chamfer_corner_tests`, `fillet_option_tests`, `sketch_tests`). Fusion parity is now the owner's top rule: every behavior and option as Fusion's. As built:
- **Extrude** (`extrude_inputs.luc`, `cad_features.luc`; luce-cad `extent_starts.lucb`, `extent_targets.lucb`, `sketch/thicken.lucb`):
  - Type **Thin extrude**: Wall thickness, Wall location Side 1 (inside a closed profile, left of an open curve as drawn), Side 2 (outside, right) or Center; open chains are walls too; with profiles picked, the chains round them, else every chain.
  - **A face as the profile**: Extrude face makes an Extrude of the face itself (Profiles "face <name>", no Sketch), and Pick profiles takes a flat face clicked off the regions.
  - Start **Object** (Pick start object): a face parallel to the sketch is a start offset (every extent and taper); a slanted or curved one bounds the extrusion, its end the start face moved the distance on, to a face, or past the body; one side, no taper.
  - **Start offset with To object and All**.
  - To object's **Extend**, Fusion's: To selected face (its surface extended), To adjacent faces (checked to stop on the face and its neighbors alone, else refused naming the other choices), To body, Through body (the long extrusion less what lies past the body's last face).
  - **Objects To Cut** (Pick bodies at the Object level; Auto-select every body): Join, Cut and Intersect act on the bodies named, kept by one face name each; Cut and Intersect act on each body apart, as Fusion's (before, the bodies were unioned first).
- **Revolve** Type Angle, Full or **To** (Pick object; Flip turns the other way; luce-cad `revolve_to.lucb`).
- **Fillet**: Type **Full round** (Pick center face; the circle tangent to the center face and the faces across its longest parallel edges: both edges filleted to that radius, G1, G2 or G3; flat faces along straight edges); Radius type **Chord length** (r = c / (2 cos(θ/2)); edges at different angles refused) and **Variable** (Radius at the start, End radius, Points between, Smooth transition; an exact rational B-spline blend, luce-cad `variable_fillet.lucb`; one straight edge between flat faces ending at faces square to it, G1).
- **Chamfer** Corner type, where three chamfers meet: **Chamfer** (Fusion's default: a flat face through the points where the contact lines meet on each face), **Miter** (they run on to a point), **Blend** (the chamfers stop at setbacks and the setback patch blends them into the faces, G2; equal distances). The Chamfer node now defaults to Fusion's Chamfer corners: a box with every edge chamfered has 26 faces, not 18.
- **Selection**:
  - Window and crossing by drag direction (left to right window, right to left crossing, drawn dashed) in CAD networks, Edit CAD and sketches; luce-cad `select_box(crossing)`.
  - Per-prompt filters (`tool_prompt.domain`, `Workspace.prompt_level`): faces for Pick face, object, start object, center face and faces; edges for Pick edges and Pick axis; bodies for Pick bodies; the level caption says "Faces only".
  - A shown, finished sketch (`sketch_shown.luc`): its profiles shaded and picked at the Faces level and Smart over the face beneath, its points and curves at Smart; Extrude and Revolve take them (a picked line is the Revolve's axis).
- **Marking menus**: in a CAD network the A and S menus lead with Repeat and the CAD tool used last, under the repeat icon (a command again, or its node added bare when nothing selected applies).
- **The ghost wireframe** round filleted bodies (`stage45/shots/cad_g3_chain.png`, `kernel/shots2/runout_fillet_g3.png`) was the B-spline faces' control nets, drawn as the control hull: G2/G3 strips and setback patches showed their nets standing off the body. luce-cad `hull_lines` now leaves out faces a modeling feature named (imported and freeform surfaces keep theirs); likewise a CAD network's sketch curves no longer show their circles' control triangles (`cad_nodes.shows_curve_hulls`). Fusion draws neither.
- **Open ends that stop flat** (a fillet's open end where the face going on does not turn away): Fusion's help, its API reference and the forums found do not say what Fusion does there (ACIS/ShapeManager "capping" is not documented publicly either); the flat end face (luce-cad `cap_runout.lucb`) stays, documented as unverified against Fusion.
- Fillet **Corner type** Rolling ball or **Setback** (G1; G2 and G3 corners are always setbacks): luce-cad fits the setback patch rational now (homogeneous fit, the weights first) and gives the edges' tools the same rational arc as their section, so the patch meets them exactly.
- **Still open**: variable radius beyond one straight edge (chains, curved faces, corners with other fillets, G2/G3).
- Screenshots: `luce_work/cad/parity/shots/` (`cad_crossing`, `cad_repeat`, `cad_filter`, `cad_thin`, `cad_face_extrude`, `cad_through`, `cad_bodies`, `cad_revolve_to`, `cad_full_round`, `cad_chamfer_corner`, `cad_chamfer_blend`, `cad_shown_sketch`, `cad_variable`, `cad_setback`, `g3_after`).

**Stage 7: the Modify features as nodes** (luce-cad 10). Done 2026-10-12 (`cad_modify_tests`, `edit_cad_direct_tests`; luce-cad `face_parity_tests`, `shell_tests`). As built:
- **Nodes** (`cad_modify.luc`): **Shell**, **Move** (Fusion's Move/Copy; a node may not be named with a `/`, Fusion's timeline calls the feature Move), **Combine** (Boolean is gone: Combine with its tool wired is it), **Split Body**, **Split Face**, **Replace Face**, **Delete Face** and **Remove**, in the chain beside Extrude, Revolve, Offset Face, Fillet and Chamfer. Each keeps its faces by luce-cad's names and its bodies by a name only that body's faces have (`cad_names.model_names`: the pieces of a split body share the split face's name); at each cook the names become groups on the input's pick mesh (`cad_names.lucb`, one Base pass) and the node runs **Edit CAD's own step code** (`edit_cad_faces.luc`, `cad_moves.luc`), so the node and the direct-modeling step cannot drift apart. A name no longer found upstream is an error saying so.
- **Fusion's options**:
  - Shell: Faces or Bodies (hollowed closed), **Tangent chain** (on, Fusion's default), **Inside thickness**, **Outside thickness**, Direction Inside, Outside or **Both** (a thickness each way; luce-cad `shelled(chain, outside_thickness)`).
  - Move: Move object Bodies or Faces; Move type **Free move** (X, Y, Z and turns about each), **Translate**, **Rotate** (an origin axis or a **picked edge's line**, an angle), **Point to point** (from a picked point to another), **Point to position** (from a picked point to typed coordinates); **Pivot** the selection's middle, the origin or a point (Set pivot picks it); **Create copy** of bodies, and of **faces** (a surface body, luce-cad `copied_faces`). A point pick snaps as Fusion's does: the nearer end of the clicked B-rep edge, a round edge's middle (`cad_names.edge_point`).
  - Combine: Target body, Tool bodies (and the second input's bodies; wired with no target picked, the chain's first body is the target, Houdini's way), Join, Cut, Intersect, Keep tools.
  - Split Body, Split Face: the bodies or faces, Splitting tool a picked face (its surface extended) or an origin plane with an offset. Split Face's piece on the tool's outer side is named `<tag>/split[<name>]` (luce-cad), so it can be picked and changed apart.
  - Replace Face: the faces, **Target faces** (several: one surface, or a closed solid's faces; luce-cad trims or extends the body to the quilt), **Tangent chain**.
  - Delete Face heals several fillet, chamfer or corner faces at once where every face round them is flat (luce-cad `face_heal.lucb`); Remove takes bodies away as a recorded feature, apart from Delete.
- **Reached** from the viewport's right-click menu (faces: the features on faces, then on their bodies; nothing selected: a Modify submenu), the S marking menu, and Modify › CAD features (`modify_commands.luc`); the same commands are Edit CAD's steps in an edited model. Made from a selection, a node takes it (faces, or the bodies they are on); then it **waits input by input** for what it lacks (`modify_picks.luc`): its input body shows, picks go in by name, a single pick (a face, a body, an edge, a point) finishes at once and the others at Enter, and the next empty input starts by itself, as Fusion's dialog moves to its next selection field. Each input is a row of the parameter panel with its pick button.
- **Handles**: Shell's Inside arrow into the body and Outside arrow out of it, its value box opening by itself; Move's arrows along X, Y, Z and rings about them at the pivot (Free move), the arrows (Translate), the ring about its axis (Rotate).
- **Waiting is not a fault**: a node or Edit CAD step waiting for a pick ("Pick …") shows "waiting" in the muted color with no badge, the prompt in the viewport's prompt line and the panel; only failures (red) and lost references (yellow) badge (`node.waiting`). While Combine waits for its tool bodies its target is lit in the sketch blue (`combine_target.luc`), in the node and in Edit CAD.
- **Stage 6's gaps closed in Edit CAD**: Split Face (waits for its splitting face, or an origin plane from its tool bar and Enter), Replace Face onto several target faces (Shift adds, Enter) with Tangent chain, Shell's Tangent chain and two thicknesses, Move/Copy's dialog in its tool bar (Move type, Axis and Angle, Pivot and Pivot point, From and To points; choosing Point to point waits for the From point clicked, then the To point, the move standing still meanwhile so the model is picked where it was; Rotate about a picked edge and a Point pivot wait for theirs), copies of faces, **Remove** as a step of its own, Delete healing several strips at once, **Redefine Sketch Plane** (below). Faces a step makes are named for the node too (`#<node>s<n>`, imported models `#<node>m<i>`), so two Edit CAD nodes in one chain never make the same names. Edit CAD's parameter panel shows the Edit framework's Soft radius, Falloff, Symmetry and Keep selection only at its CVs level, the one level they act on (Fusion's direct edits have none).
- **Redefine Sketch Plane** (Fusion's): in a Sketch node, from the sketch's right-click menu, the sketch waits for the face it goes onto (Pick face; an origin plane is its Plane row); in Edit CAD, from the right-click menu on a sketch's curve or the Redefine Sketch Plane submenu, a step `Sketch Plane` moves it onto the selected face, else waits for a face clicked or an origin plane chosen in its tool bar and Enter. The drawing keeps its own coordinates; curves projected from the old face stay as they were (a Sketch node's draw yellow as lost).
- **Not built**: Combine's **New Component**: a CAD node is one component (one object of the scene), so Fusion's "a new component with the results" has no place inside it; the equivalent is the result brought into another CAD node with an Import node. The other gaps listed here at first were closed in the gaps round below.
- Screenshots: `luce_work/cad/stage78/shots/` (`modify_shell`, `modify_face_menu`, `modify_marking`, `modify_combine`, `modify_move`, `modify_split_face`, `direct_move_face`).
- Plan as written: Tests: a shelled box's volume (outer minus inner, with the removed face open). Inside, Outside and Both.

**Stage 8: history polish.** Done 2026-10-12 (`cad_history_tests`, `sketch_plane_tests`). As built:
- **The timeline strip** (`cad_timeline.luc`) along the Network panel's bottom, over its tools, shown inside a CAD network: Fusion's playback buttons (to the start, a feature back, a feature on, to the end), each feature of the chain an icon in order, the selected one outlined, a failed one underlined red and one with a lost reference yellow (a waiting one: none), bypassed and rolled-back ones dimmed (rolled back struck through), the marker an accent bar after the displayed feature, the hovered feature's name at the right. The chain (`cad_chain.luc`) runs up first inputs from the Output node the displayed node feeds, else as far down as one node at a time takes it on; branches off it are not on it (the strip is a second view of the nodes, not a second history).
- **The marker**: dragged between icons it rolls the design back or forward (the display flag; one undo step), as do the buttons.
- **Reorder**: an icon dragged along the strip. It is cooked first on a copy of the network; when a feature that cooked would fail (or gain a warning), it is refused, the reason in the status line ("Reorder refused: Fillet 6 would fail: The first input has no solid body"), and the network is unchanged. A primitive making the body from nothing stays first. Otherwise the first inputs are rewired as one undo step.
- **Edit Feature**: a double-click on a feature node in the network, or on its icon in the strip, edits it in the viewport as Fusion's Edit Feature does: selected, the marker rolled to it while it is edited (selecting another node rolls forward again, as a sketch's editing does), its value box open by its first handle; a feature still waiting for picks asks for them; a Sketch or Edit node is edited as selecting it does; a container is entered.
- Screenshots: `luce_work/cad/stage78/shots/` (`timeline_strip`, `timeline_rolled`, `timeline_refused`).
- Plan as written: The timeline strip; reorder checked by a trial cook; double-click a node to edit it in the viewport. Tests: a reorder that would put a Fillet before the Extrude making its edges is refused with the reason, and the network is unchanged.

**Gaps round** (2026-10-12; luced-3d `cad_gap_tests`; luce-cad `reach_parity_tests`). As built:
- **Delete healing beside curved faces** (luce-cad `face_band.lucb`): a band of deleted faces between one face and a ring of faces round it, the ring curved too, heals by extending them until they meet: each ring face meets the top along a line, an analytic curve or a traced cubic, and the edges between ring faces run on along their carriers to the top's surface. The owner's case (a box's uprights rounded G1, G2 or G3, its top chain filleted or chamfered, the chain's faces deleted) heals back to the rounded box exactly, in the Delete Face node and Edit CAD's Delete alike.
- **Replace Face onto an open surface body of several surfaces** (luce-cad `face_quilt.lucb`): the quilt is closed into a solid by sweeping it along the way the replaced faces face (walls planar, cylindrical or ruled B-spline), then trimmed or extended to as a solid's faces.
- **Split Body's Extend splitting tool** (on, Fusion's default): off, the picked face cuts only where it reaches (luce-cad `split_by_face(..., extend = false)`: the face swept past the body is the tool, what its walls cut joins the body again); a face only part way across is refused, naming the option. A row of the Split Body node and of Edit CAD's step.
- **The Move node's manipulator** (`move_manipulator.luc`): Free move and Translate show Fusion's whole manipulator, the gizmo Edit CAD's Move Face drags: arrows, plane squares, the middle square (the view's plane) and, for Free move, rings about X, Y and Z. It stands at the pivot moved by Translate, so it follows the moved body; drags set Translate and Rotate (grid and whole degrees; Cmd frees), one undo step each. Rotate keeps its single ring about its axis; Point to point and Point to position move by picked points.
- **Split Face's edge**: the edge between the two pieces is drawn, with a piece selected or not (checked in the preview, `gaps3/shots/split_edge.png`, `split_face.png`).
- **Kept as they are** (owner): the node names Move and Delete Face (Fusion's own timeline feature names, its API's MoveFeature and DeleteFaceFeature; Move/Copy cannot name a node, and a plain Delete reads as the Delete key and the Edit nodes' Delete step); Combine's wired tool default (no target picked: the chain's first body); the timeline strip as one chain.

## 10. Open questions for the owner

1. **Editing a sketch: roll back or show downstream?** Fusion rolls back: the body as it was at the sketch shows, and nothing after it. Houdini keeps the display where it is, so the result downstream updates live while you edit. The plan does Fusion's by default (the display flag moves to the sketch while editing and back on Finish). Should "keep the display downstream" be the default, or a toggle?
2. **The sketch passes the body through** (§4.2), so the chain is one wire like the timeline. Is that the network shape you want, or should sketches stay curves-only and Extrude find the body some other way?
3. **Keys.** Fusion's E, F and Q are taken here:
   - E is Rotate, F is Frame and Q is Select;
   - D is the display flag;
   - A, S and D are held for the marking menus.

   The plan uses:
   - E for Extrude inside a sketch only, where Rotate has no use;
   - Shift+E, Shift+F and Shift+Q in the CAD context;
   - K for Sketch.

   Or should the CAD context take Fusion's plain keys, with Rotate and Frame moving there?
4. **Auto operation.** Fusion's Extrude picks Join or Cut by drag direction. On by default?
5. **Window and crossing selection.** Adopt Fusion's left-to-right window, right-to-left crossing in CAD contexts? (Answered "everything inside" first; the parity round adopted Fusion's split, parity being the owner's top rule.)
6. **Edit CAD sketches as objects.** Sketches in a direct-modeling node are kept in the model as objects, editable later without changing what was already extruded (Fusion's direct mode). Agreed? It needs a sketch component in the geometry set.
7. **Projected loops on by default** when sketching on a face? Fusion has a preference; SolidCraft defaults on.
8. **Fusion's Slice** cuts away the body in front of the sketch plane while sketching. Wanted?
9. **Order.** Stages 1–3 are the UX the request names. Stage 6 (direct modeling in full) needs the luce-cad local operations, which are the largest new kernel work here. Should any of stage 6 come before stages 4–5?
