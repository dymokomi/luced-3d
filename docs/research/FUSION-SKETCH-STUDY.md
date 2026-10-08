# Fusion sketching: behavioral reference

This is a study of the Sketch environment in Autodesk Fusion (formerly Fusion 360), written for the engineer building the luced-3d Sketch node. It records what Fusion does, step by step, so that our CREATE / MODIFY / CONSTRAINTS tools can match it on purpose rather than by accident.

Research date: 2026-10-08. Most material comes from the current Fusion help (`help.autodesk.com/cloudhelp/ENU/Fusion-Sketch/...`) and the Fusion API reference, which is often more precise than the user help. The Autodesk product blog and forums returned HTTP 403 to automated fetches, so anything taken from them comes only from search-result excerpts and is marked as such.

Every claim carries one of these tags:

- **[doc]**: stated in official Autodesk help or API reference (URL given).
- **[comm]**: from an Autodesk blog or forum excerpt, or a third-party tutorial (URL given). Probably right, but not checked against the help.
- **[unverified]**: widely known Fusion behavior that I could not confirm in a source this session. Treat it as a design suggestion, not a fact.

Short names used for help URLs:

- `SK/` = `https://help.autodesk.com/cloudhelp/ENU/Fusion-Sketch/files/`
- `MD/` = `https://help.autodesk.com/cloudhelp/ENU/Fusion-Model/files/`
- `API/` = `https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/`
- `GS/` = `https://help.autodesk.com/cloudhelp/ENU/Fusion-GetStarted/files/`

---

## 1. Creating, finishing and editing a sketch

### 1.1 Choosing the plane

- Run **Create Sketch** from the Solid, Surface, Form, Sheet Metal or Base Feature tab, then pick the plane. Valid picks are the origin planes (XY, YZ, XZ), construction ("work") planes and planar faces of bodies. [doc] `SK/GUID-0EEF7073-6CDE-4E31-AF1A-0811F969F031.htm`, `SK/SKT-CREATE-3D-SKETCH.htm`
- If the pick is an existing sketch entity, or a sketch node in the browser, Fusion **edits that sketch** instead of creating a new one. [doc] same page.
- **Sketching on a planar face automatically projects that face's edges into the sketch.** [doc] `SK/GUID-6EE7B230-A280-45B7-8868-D96E4CE44B62.htm` ("If you create a sketch on an existing planar face, the edges of that face automatically project into the sketch.")
- Related preferences, from the API mirror of Preferences > General > Design [doc] `API/fusion_FusionProductPreferences.htm`:
  - `isAutoLookAtSketch2`: whether the camera re-orients to look at a new sketch, and if so whether it keeps the current camera or switches to orthographic.
  - `isAutoProjectGeometry`: whether geometry outside the sketch plane is projected automatically.
  - `isAutoProjectEdgesOnReference`: when the view is normal to the sketch plane, model edges are projected automatically as you use them as references for constraints and dimensions. This is how clicking a body edge with the Dimension tool "just works".
  - `isAutoHideSketchOnFeatureCreation`: hides the sketch when a feature consumes it.
  - `is3DSketchingAllowed`: allows 3D lines and splines.
  - `isDimensionEditedWhenCreated`: whether the value box opens as soon as a dimension is placed.
  - `isSketchScaledWithFirstDimension`: **the first dimension in a sketch scales all of its geometry**, so typing 100 mm on a sketch drawn at 3 mm does not produce a spike.
- The 2D/3D distinction: a 2D sketch keeps all geometry on its plane. Turning on **3D Sketch** in the palette lifts that restriction. [doc] `SK/SKT-3D-SKETCH.htm`

### 1.2 The environment

- Entering a sketch adds a **Sketch contextual tab**. The tab and the Finish Sketch button are highlighted blue to show that you are in a temporary mode. [doc] `SK/GUID-0EEF7073-...htm`
- **Starting a 3D modeling tool (Extrude, for example) while a sketch is active finishes the sketch automatically.** [doc] `SK/SKT-3D-SKETCH.htm`
- Look At rotates the camera to face the sketch plane. View transitions are animated unless "Animate view transitions" is turned off. [doc] `GS/GUID-878489CD-3A23-4303-8450-C2F4F8E410B1.htm`

### 1.3 Sketch Palette (floating panel in the canvas)

Source: [doc] `SK/GUID-4183A4B7-E002-4396-AD5A-7FF3C8B2F33A.htm`

- **Contextual Options / Feature Options.** Shows options for the active tool or the current selection:
  - The sub-type switch for the active tool (Line ↔ Midpoint Line; the rectangle, circle, arc, slot, polygon and chamfer types).
  - Spline degree (3 or 5) while Control Point Spline is active.
  - Normal/Construction and Curvature Comb when a spline is selected.
  - Change Spline Degree when a control-point spline is selected.
  - The Blend Curve G1/G2 choice.
- **Linetype**: Construction and Centerline toggles. With nothing selected they set the mode for new geometry. With a selection they convert it.
- **Look At**.
- **Sketch Grid**: shows or hides the grid.
- **Snap**: snaps to the grid.
- **Slice**: temporarily cuts away bodies on the viewer's side of the sketch plane.
- **Show Profile**: the blue shading on closed profiles.
- **Show Points**.
- **Show Dimensions**.
- **Show Constraints**.
- **Show Construction Geometries**.
- **Show Projected Geometries**.
- **3D Sketch**.
- The palette also carries a **Finish Sketch** button. [doc] the tutorial `SK/GUID-0A723EF7-...htm` says "Click Finish Sketch on the Sketch Palette".

### 1.4 Linetypes and their colors

Source: [doc] `SK/SKT-3D-SKETCH.htm`

| Type | Counts toward profiles? | Display |
|---|---|---|
| Normal sketch geometry | yes | solid **blue** while under-defined |
| Construction | **no** | dashed **orange** |
| Centerline | yes | dashed orange centerline. Revolve auto-picks it as the axis, and Dimension auto-creates a **diameter** dimension across it. [doc] `SK/SKT-CENTERLINE-GEOMETRY.htm` |
| Projected | yes | **purple**, associative, "locked by default" |
| Fixed (Fix/UnFix) | yes | **green** |
| Fully constrained | — | **black** |

**X** toggles Normal/Construction, either on the selection or as the mode for new geometry. [doc] `GS/GUID-F0491540-0324-470A-B651-2238D0EFAC30.htm`. The same toggle is in the right-click marking menu. [doc] `SK/SKT-CONSTRUCTION-GEOMETRY.htm`

### 1.5 Finishing and editing

- **Finish Sketch**: from the toolbar, the palette, or the marking menu (Sketch > Finish Sketch). A dropdown also offers **Finish with AutoConstrain** (an AI-based pass, not available in the personal-use edition). [doc] `SK/SKT-FINISH-SKETCH.htm`
- **Edit an existing sketch**: right-click it in the browser or timeline and choose Edit Sketch, or double-click its timeline node. [doc] `SK/GUID-0EEF7073-...htm` and a tutorial.
- Editing rolls the timeline back to that sketch. [unverified]

### 1.6 Sketching on a face that later changes

- The sketch plane and the projected face edges are **references**. If the face is changed or consumed, the projections can be lost.
- A lost projection link shows a **yellow warning on the sketch's timeline node**, and the affected projected curves are highlighted orange or yellow in the canvas. [doc] `SK/GUID-850061C4-71F5-4418-AF9C-F0D232022F9C.htm`
- Recovery: right-click the timeline node > **Manage Lost Projections**. For each lost item choose:
  - **Re-Link**: pick a new body, face, edge or point.
  - **Break Link**: keep the curves as plain geometry where they are.
  - **Delete Geometry**.

  Bulk Delete All and Break Link All are available, and **Fade Other Geometry** helps find the lost items. [doc] same page.
- A lost plane is fixed with **Redefine Sketch Plane** (right-click the sketch). [doc] a video page, `SK/GUID-3E407E01-65AE-4DCC-A3A7-1439D9B5182F.htm`. Users report that redefining can rotate or mirror the sketch unexpectedly. [comm] https://forums.autodesk.com/t5/fusion-design-validate-document/redefine-sketch-plane-unexpected-rotation-mirroring-expected/td-p/14081806
- **Implementation note:** store the sketch's local frame (origin and X axis), not only the plane, and define a deterministic rule for re-deriving that frame from a replacement face.

### 1.7 3D sketch specifics

Source: [doc] `SK/SKT-CREATE-3D-SKETCH.htm`

- With 3D Sketch on, a **3D Sketch Manipulator** (a triad) appears at (0,0,0). It has:
  - plane handles that act as the temporary sketch plane (XY by default),
  - axis lines,
  - rotation handles.
- Hover along an axis until its extension line shows to restrict the point to that axis.
- The triad moves to the last placed point.
- Keys:
  - **Alt** cycles the active plane.
  - **Tab** cycles the rotation handles.
  - **Up Arrow** locks XY so that the next point changes only Z.
- Right-click offers Reset Triad Orientation, Show Rotation Handles and Show Planes.
- Constraints supported in 3D: H/V, Coincident, Tangent, Equal, Parallel, Perpendicular, Fix, Midpoint, Concentric, Collinear. Symmetry and Curvature are **not** on that list. [doc] `SK/SKT-REF-3D-SKETCH-SUPPORTED-CONSTRAINT.htm`

---

## 2. CREATE tools

### 2.0 Conventions common to every create tool

- **Tools stay active and repeat.** After a shape is finished, the next click starts a new one. **Enter** (or Esc) leaves the tool. Every create-tool help page ends with "Optional: Repeat steps… Press Enter to complete the tool." [doc] e.g. `SK/SKT-CREATE-RECTANGLES.htm`
- **Placement is click-click, not click-drag.** Each defining point is its own click. The rubber band follows the cursor between clicks. The tutorials say "Drag the mouse … Click to create", where "drag" means moving the mouse, not holding the button. [doc] e.g. tutorial pages `SK/Fusion_Sketch_tutorials_3_sketch_basics_sketch_fork_activity1_html.htm`. One exception: in the Line tool, **press-and-drag from an endpoint makes a tangent arc** (see 2.1).
- **Heads-up value fields.** While the rubber band is live, editable boxes float next to it: length and angle for lines, diameter for circles, width and height for rectangles, and so on.
  - Typing goes into the focused box.
  - **Tab** moves to the next box.
  - **Enter** commits the value and locks it, so the cursor then controls only the remaining free values.
  - [doc] polygon/slot/ellipse pages: "Press the Tab key to switch from radius to number of sides", "Press Tab to specify the angle value". [comm] https://forums.autodesk.com/t5/fusion-design-validate-document/seeing-dimensions-while-applying-lines-etc/m-p/5944827 ("You can use Tab to cycle between boxes, and press enter to lock in a dimension").
- **Typed values become dimensions.** "The rectangles, and any construction geometry, constraints, and dimensions that are added to them, display in the canvas." [doc] `SK/SKT-CREATE-RECTANGLES.htm` and the matching sentence on every create page. Values you type become **driving sketch dimensions**. Values only shown on the rubber band and never typed do **not**. [unverified as a rule; consistent with the doc wording and with the tutorials, where typed diameters later appear as dimensions]
- **Snapping adds constraints.** "As you move the mouse cursor, object snap symbols display near the geometry when you snap to the sketch grid or other geometry… If you snap to a specific point, the logical constraints are automatically added." [doc] repeated in the Tips of every create page.
- **Sub-type switch**: the Sketch Palette > Feature Options lets you change the sub-type while the tool is active. [doc]
- **Construction mode**: press **X**, or the palette's Construction toggle, before or while drawing. New geometry is then created as construction. [doc] `SK/SKT-CONSTRUCTION-GEOMETRY.htm`
- **Point display**: unconstrained endpoints show as **white dots**. Point-to-point coincidences show **no** glyph. Point-on-curve coincidences show the coincident glyph. Internal spline fit points show as grey dots. [doc] `SK/GUID-685B9D79-E3BC-4EB8-AA4E-096A34E94249.htm`

### 2.1 Line (L) and Midpoint Line

Source: [doc] `SK/SKT-CREATE-LINES.htm`, `SK/SKT-SKETCH-CREATE-LINES.htm`

- **Sequence**:
  1. Click the first point.
  2. Click the second point, or type a length, Tab, type an angle, then click or Enter.
  3. Each further click adds a **connected segment starting at the last endpoint** (chaining).
- **Tangent arc inside Line**: "pause over a point, then click and drag to create an arc segment that is tangent to the previous line segment. Move the mouse to the opposite side of the line segment to flip the direction of the arc." You can type a **radius** for the arc. After release, the chain continues as lines. [doc] same page and https://www.autodesk.com/products/fusion-360/blog/quick-tip-sketching-tangent-arcs/ [comm, title only]
  - The tangent arc is created from the **last endpoint** of the chain, or from any endpoint you hover over when starting a new chain.
  - The tangent reference is the curve that ends at that point.
  - Users report that sometimes no tangent arc is made, which suggests a hover-dwell requirement. [comm] https://forums.autodesk.com/t5/fusion-support-forum/sketching-click-dragging-while-in-line-mode-sometimes-doesn-t/td-p/10901155
- **Ending a chain**:
  - Click the start point to close the loop. The chain ends but the tool stays active.
  - Click the green check (the in-canvas OK), or **double-click** the last point, to end the chain and stay in Line.
  - **Esc** or **Enter** leaves the tool.
  - [doc] for close/check/Enter. [comm] for double-click and Esc: https://www.lynda.com/Fusion-360-tutorials/Terminating-line-chain-creation/2810401/2270578-4.html (excerpt: "click the green check mark or double-click the endpoint to end the current chain of lines and remain in the Line command, or press Esc to exit the command").
- **Midpoint Line**:
  1. Click the midpoint.
  2. Type a length and an angle, or click an endpoint. The line is symmetric about the first point.
  3. Press Enter.

  The result is a line whose midpoint is the first click (a midpoint constraint is implied). [doc] `SK/SKT-CREATE-MIDPOINT-LINES.htm`

### 2.2 Rectangles (R = 2-Point)

Source: [doc] `SK/SKT-CREATE-RECTANGLES.htm`

| Type | Clicks | Value fields |
|---|---|---|
| 2-Point | opposite corners | width, height (either or both) |
| 3-Point | corner 1, corner 2 (sets direction and length), then a third click for the width | length, then width |
| Center | center, then a corner | width, height |

- What a rectangle carries: 4 lines with coincident corners, **horizontal/vertical constraints** for axis-aligned types, **perpendicular plus parallel** for 3-point, and for Center Rectangle **construction diagonals with the center as their midpoint**. [unverified in text; the help only says "any construction geometry, constraints and dimensions that are added to them"]

### 2.3 Circles (C = Center Diameter)

Source: [doc] `SK/SKT-CREATE-CIRCLES.htm`

| Type | Input |
|---|---|
| Center Diameter | click center → type **diameter** or click |
| 2-Point | two clicks at the ends of a diameter (or type the diameter after the first click) |
| 3-Point | three clicks on the circumference |
| 2-Tangent | pick 2 **lines** → click to place, or type a **radius** |
| 3-Tangent | pick 3 lines. Window selection works. |

- Tangent circles add tangent constraints. [unverified; the name and doc imply it]

### 2.4 Arcs

Source: [doc] `SK/SKT-CREATE-ARCS.htm`, `SK/SKT-SKETCH-CREATE-ARCS.htm`

- **3-Point**: start → end (a distance can be typed) → a point on the arc.
- **Center Point**: center → start → end, or type the sweep **angle**.
- **Tangent Arc**: the first click must be on an **existing endpoint**, which gets a tangent constraint automatically. The second click, or a typed **radius**, sets the end. The arc "maintains tangency with the geometry it connects to at each end".
- The Line tool's drag-arc (2.1) is the faster path to tangent arcs.

### 2.5 Polygon

Source: [doc] `SK/SKT-CREATE-POLYGONS.htm`

- **Circumscribed**: click the center → type the radius of the circle the polygon is drawn around (edge midpoints lie on it) → **Tab** → number of sides → move the mouse to set orientation → click.
- **Inscribed**: the same, but the vertices lie on the circle.
- **Edge**: click the first edge point → length, Tab, angle → click or Enter → number of sides → move to choose which side of the edge → click.
- The result carries a **Polygon constraint**. The API object `PolygonConstraint` exposes `centerPoint` and the vertex `points`. It was introduced March 2016. [doc] `API/fusion_PolygonConstraint.htm`. The API's `addPolygon` requires existing lines that are equal length, joined end to end, with equal angles, forming a closed shape. [comm, search excerpt of `API/GeometricConstraints_addPolygon.htm`]
- The construction circle and center point are probably created too. [unverified]

### 2.6 Ellipse

Source: [doc] `SK/SKT-CREATE-ELLIPSE.htm`

1. Click the center.
2. Set the first axis endpoint: length, Tab, angle, then Enter or click.
3. Set a point on the ellipse (the other semi-axis): type and Enter, or click.

### 2.7 Slots

Source: [doc] `SK/SKT-CREATE-SLOTS.htm`

| Type | Sequence |
|---|---|
| Center to Center | arc center 1 → arc center 2 (distance, Tab, angle) → width (type or click on the straight edge) |
| Overall | overall end 1 → end 2 (distance, Tab, angle) → width |
| Center Point | slot center → one arc center (distance, Tab, angle) → width |
| Three Point Arc | arc center 1 → arc center 2 → a point on the center arc → width |
| Center Point Arc | center of the centerline arc → one end center (radius) → sweep angle → width |

- The width can be typed as a width, or as the end-arc diameter or radius.
- A slot includes a construction centerline (or arc) and center points. [doc] example images; constraint set [unverified]

### 2.8 Splines

Source: [doc] `SK/SKT-CREATE-SPLINES.htm`, `SK/SKT-REF-SPLINE-DEGREE-CONTROL.htm`

- **Fit Point**:
  - Click points; the curve passes through them.
  - Finish with the **Check** icon, Enter, or by clicking the start point, which makes a **closed** spline.
  - Selecting the spline shows **curvature (tangent) handles** at fit points. Dragging a handle end sets the tangent direction and magnitude.
  - The right-click menu on a handle offers Activate/Deactivate Curvature Handle.
- **Control Point (CV)**:
  - Choose the degree in the palette: **5 (default, "G4 internally")** or 3.
  - Click the control frame, then Check.
  - No tangent handles. Add points instead.
- Right-click on a spline: Open/Close Spline (fit only), Insert Fit Point / Insert Control Point, Toggle Curvature Display (density and scale).
- Starting a spline by **dragging away from an existing endpoint** adds a tangent constraint, which appears when the spline is complete. [doc]
- Change Spline Degree (palette) raises or lowers the degree. Lowering it changes the shape.

### 2.9 Conic Curve

Source: [doc] `SK/SKT-CREATE-CONIC-CURVE.htm`

1. Click end 1.
2. Click end 2.
3. Click the vertex (the intersection of the end tangents). Guidelines from the ends to the vertex can be used to snap tangency to other geometry.
4. Drag the **Rho** handle or type Rho:
   - Rho < 0.5 gives an ellipse.
   - Rho = 0.5 gives a parabola.
   - Rho > 0.5 gives a hyperbola.

   The doc names the three outcomes but does not give the thresholds. [unverified]
5. Press Enter.

### 2.10 Point

Click repeatedly; points snap to the grid or to geometry and pick up coincidences. Press Enter to finish. [doc] `SK/SKT-CREATE-POINT.htm`

### 2.11 Text

Source: [doc] `SK/SKT-CREATE-TEXT.htm`, `SK/SKT-REF-TEXT-DIALOG.htm`

- **Text** type:
  1. Click two corners of a **text frame**.
  2. Rotate it with the rotation handle or a typed angle. Any snap point on the frame can be chosen as the rotation pivot.
  3. Type the content **in single quotes**, e.g. `'ABC'`. It can concatenate text parameters: `'Rev '+RevParam`.
  4. Set font, bold/italic, height (in design units), character spacing (%), flip H/V, and alignment (3×3).

  The frame can be **dimensioned and constrained** like ordinary geometry.
- **Text On Path**: pick a sketch curve as the path, then set placement above or below, Fit to Path, horizontal alignment, and flip. The text follows later edits to the path.
- Each text creates a **text model parameter**.
- SHX single-line fonts are listed first and have no thickness.
- **Explode Text** turns text into curves. [doc] `SK/SKT-EXPLODE-TEXT.htm` (TOC entry)

### 2.12 Mirror, Circular Pattern, Rectangular Pattern

Sources: [doc] `SK/SKT-CREATE-MIRROR.htm`, `SK/SKT-CREATE-CIRCULAR-PATTERN.htm`, `SK/SKT-CREATE-RECTANGULAR-PATTERN.htm`

- **Mirror** (dialog):
  - Select the objects, then the Mirror Line field, then a line. The line can be normal or construction but **cannot be curved**.
  - The result is associative: the tutorial notes that edits to the source half carry over to the mirror. Fusion implements this with **symmetry constraints** between the pairs. [doc, tutorial `SK/GUID-E8C8752F-...htm`; constraint mechanism unverified]
- **Circular Pattern**:
  - Select the objects, then the Center Point.
  - Angular spacing: **Full** (360°), **Angle** (one direction, Total Angle), or **Symmetric**.
  - Set Quantity with the in-canvas handle or by typing.
- **Rectangular Pattern**:
  - Select the objects; optionally choose geometry for Direction 1 and 2.
  - Distance Type: **Extent** (total distance) or **Spacing**.
  - Per direction: Quantity, Distance, and One Direction or Symmetric.
- **Both patterns**: every instance shows a **checkbox in the canvas**; unchecking it suppresses that instance. A **glyph** sits next to the original (rectangular) or at the center (circular). **Double-clicking the glyph reopens the dialog.** The API treats patterns as constraints (`addCircularPattern`, `addRectangularPattern`). [doc] `API/fusion_GeometricConstraints.htm`

### 2.13 Project / Include (P = Project)

Sources: [doc] `SK/SKT-SKETCH-CREATE-PROJECT-INCLUDE.htm`, `SK/GUID-850061C4-...htm`, `SK/GUID-6EE7B230-...htm`

- **Project**:
  - Selection filter: **Specified Entities** (faces, edges, points) or **Bodies**. Projecting a body gives its closed silhouette profiles.
  - **Projection Link** checkbox: associative (on by default) or a static copy.
  - The result is **purple** and locked by default.
- **Intersect**: the section of selected bodies, edges or points with the sketch plane.
- **Include 3D Geometry**: brings edges and points into the sketch as 3D curves, without flattening.
- **Project To Surface**, **Intersection Curve**, **Spun Profile**, **Isoparametric Curve**: specialty tools.
- **Show Projected Geometries** (palette) hides or shows them.
- Projected geometry **cannot be constrained or moved** until the link is broken (right-click > Break Link). [comm] https://forums.autodesk.com/t5/fusion-design-validate-document/overconstrained-sketch/m-p/10178361

### 2.14 Sketch Dimension (D)

See §5.

---

## 3. Inference, snapping and automatic constraints

### 3.1 What gets inferred

- **Coincident**: snapping onto an existing point gives point–point coincidence; snapping onto a curve gives point-on-curve coincidence. [doc] (create-tool Tips; coincidence display in `SK/GUID-685B9D79-...htm`)
- **Horizontal / Vertical**: when a line is near axis-aligned, an inferred H/V glyph shows and clicking commits it. [comm] https://origin-www.lynda.com/Fusion-360-tutorials/Sketch-constraints-Horizontal-vertical-collinear/667363/703400-4.html (excerpt: "as you move the cursor you can see inferred constraints appear, such as a horizontal inferred constraint… left-click and the Horizontal/Vertical constraint will be applied")
- **Perpendicular / Parallel**: to the previous segment in the chain, and to other lines the cursor has recently touched. [comm] https://forums.autodesk.com/t5/fusion-design-validate-document/auto-constraints/m-p/5486827 (excerpt: perpendicular is inferred for lines in the same command session; for older lines you may need to "slide" along them to wake them up)
- **Tangent**:
  - from line-drag arcs,
  - from the Tangent Arc start,
  - from splines dragged off endpoints,
  - when dragging a circle edge onto a line: "A Tangent constraint (square) appears". [doc] tuning-fork tutorial
- **Midpoint**: hold **Shift** while hovering over a line and the cursor snaps to its midpoint and creates a **midpoint constraint**. This works while drawing, constraining and dimensioning.
  - [doc] the shortcut table lists "Sketch Coincident Constraint at Midpoint — Shift" (`GS/GUID-F0491540-...htm`).
  - [comm] https://www.autodesk.com/products/fusion-360/blog/quick-tip-sketch-gems-part-3/
  - The midpoint glyph is a **triangle**. [doc] tutorial: "A triangle glyph indicates that your circle is locked to the midpoint."
- **Equal**: not confirmed as an inference during drawing. [unverified; I do not believe Fusion infers Equal while drawing. Equal is created by tools such as Polygon and Center Rectangle, or applied explicitly]
- **Origin**: hovering the sketch origin snaps to it, and the point becomes coincident with the projected origin. [doc] tutorial ("Hover over the origin… The cursor snaps automatically")

### 3.2 Glyphs and guides

- While drawing, a **small constraint glyph** (H, V, ⊥, ∥, tangent, coincident, midpoint triangle) shows next to the cursor or segment for the constraint that would be created. [doc] the create-page wording "object snap symbols display near the geometry". The exact artwork is not documented.
- Dotted or dashed **alignment guides** run from existing points when the cursor lines up with them horizontally or vertically. [unverified for Fusion. The general description of "orange dashed line" guides in the search excerpt came from Onshape's docs, not Fusion's, so do not cite it as Fusion behavior.]
- After creation, glyphs remain as **grey badges** beside the geometry. [doc] tutorial: "there are gray glyphs that represent different constraints that were created"

### 3.3 Suppressing inference

- Hold **Ctrl (Windows) / Cmd (macOS)** while placing a point. **No constraints are created and no snapping happens.** [comm] Autodesk blog "Quick Tip: Sketch Gems Part 3", https://www.autodesk.com/products/fusion-360/blog/quick-tip-sketch-gems-part-3/ (excerpt: "hold down the Ctrl key or Cmd on a Mac and no constraints will be added to your sketch"). Snapping is lost too, per a forum excerpt from https://forums.autodesk.com/t5/fusion-support-forum/struggles-with-constraints/m-p/9505577
- There is no preference that turns off auto-constraints globally. Users have requested one in IdeaStation threads. [comm] https://forums.autodesk.com/t5/fusion-360-ideastation-archived/preference-to-disable-auto-contraint-creation/idc-p/7917811
- **Implementation note:** Shift adds a snap (midpoint) and Ctrl/Cmd removes all snaps and inference. Keep the two keys separate.

### 3.4 Grid and snap

- The palette's **Sketch Grid** shows the grid; **Snap** snaps to it. [doc] `SK/GUID-4183A4B7-...htm`
- Grid settings live in **Navigation bar > Grid and Snaps > Grid Settings**:
  - **Adaptive** (spacing changes with zoom), or
  - **Fixed** (a major spacing plus a number of minor subdivisions, e.g. 5 mm major / 20 minor gives a 0.25 mm snap).
  - [comm] https://forums.autodesk.com/t5/fusion-design-validate-document/fusion-360-grid/m-p/6571577 and https://forums.autodesk.com/t5/fusion-design-validate-document/incremental-move/m-p/7061796
- **Incremental Move** (same menu) applies to manipulators (Move, Press Pull), not to sketch drawing. [comm] same thread.

---

## 4. Constraints

### 4.1 How the tools work

The general pattern:

1. Choose the tool. Its icon follows the cursor.
2. Click the entities. The constraint is created as soon as the last required entity is picked.
3. The tool stays active for the next pair.
4. **Esc** ends it.

[doc] each `SK/SKT-CONSTRAIN-*.htm`. The tutorial says "Press Esc to finish applying the constraint."

**Selection order decides what moves.** "The first selection is your reference, then your second selection aligns to match the reference" — if neither entity is constrained, the **second** one moves. [doc] `SK/GUID-E8C8752F-8DBC-4802-9DC7-F2D798C4C483.htm`. Equal says the same: "snaps to match the size of the **first** object you selected". [doc] `SK/SKT-CONSTRAIN-EQUAL.htm`. If the second entity is constrained, the solver moves whatever is free. [unverified]

Pre-selection should also work: select geometry first, then pick a constraint, and the palette offers constraints valid for that selection. [unverified]

| Constraint | Valid picks | Behavior | Source |
|---|---|---|---|
| Horizontal/Vertical | one line, **or two points** | snaps to whichever axis is **closer to the current orientation**. The API has `addHorizontal(line)` and `addHorizontalPoints(p1,p2)`. | [doc] `SK/SKT-CONSTRAIN-HORIZONTAL-VERTICAL.htm`, `API/fusion_GeometricConstraints.htm` |
| Coincident | point+point, or point+curve | snap together. Point–point shows no glyph. **Delete via right-click on the point > Delete Coincident.** | [doc] `SK/SKT-CONSTRAIN-COINCIDENT.htm`, `SK/GUID-685B9D79-...htm` |
| Tangent | curve + curve (line/arc/circle/spline/ellipse) | touch without crossing. The glyph is a small square. | [doc] |
| Equal | 2 lines (length), or arcs/circles (radius) | the second matches the first. The tool takes "similar objects". | [doc], API `addEqual` |
| Parallel | 2 lines | — | [doc] |
| Perpendicular | a line and another curve (`addPerpendicular2`) | — | [doc] API |
| Fix/UnFix | any point or curve | locks size and position. **The curve turns green.** Click it again with the tool to unfix. | [doc] `SK/SKT-CONSTRAIN-FIX-UNFIX.htm` |
| Midpoint | a point + a line or arc | the point snaps to the midpoint | [doc], API `addMidPoint(point, curve)` |
| Concentric | 2+ arcs, circles, ellipses or elliptical arcs | the second center moves to the first | [doc] |
| Collinear | 2+ lines (e.g. a line and a rectangle edge) | — | [doc] |
| Symmetry | **two entities, then the symmetry line** | they mirror across the line | [doc] `SK/SKT-CONSTRAIN-SYMMETRY.htm` |
| Curvature (G2) | a **spline** + a chained curve (spline, line or arc) that meets it at an end | G2 continuity at the joint. API name `addSmooth`; one curve must be a spline. | [doc] `SK/SKT-CONSTRAIN-CURVATURE.htm`, API |
| Polygon | the lines of a closed equal-sided loop | regular polygon about a center point | [doc] API only (`PolygonConstraint`). **The current user help's Constraints list has 12 tools and no Polygon tool**, so in the UI the constraint seems to come from the Polygon create tool. Confirm in the product before building a separate UI tool. |
| Offset | created by the Offset tool | keeps the offset curves associated with their source | [doc] `SK/SKT-OFFSET.htm` |
| Pattern | created by the Pattern tools | see §2.12 | [doc] |

### 4.2 Display and deletion

- Constraint **badges** (glyphs) show next to constrained geometry. **Show Constraints** in the palette toggles all of them. [doc]
- To delete a constraint, select its glyph and press **Delete**, or use the right-click menu. [doc] the AutoConstrain page uses "select it in the canvas and press Delete" for constraints. The general case is [unverified] but standard.
- Hovering a glyph highlights the geometry it ties together. [unverified]
- Deleting an offset glyph breaks the offset association. Deleting only the offset **dimension** keeps the association but frees the distance. [doc] `SK/SKT-OFFSET.htm`

### 4.3 Over-constraining

- **Dimensions**: if a new dimension would over-constrain the sketch, Fusion **creates it as a Driven dimension** after a warning. Driven dimensions show their value **in parentheses**, update live, and appear greyed and read-only in the Parameters dialog. [doc] `SK/SKT-SKETCH-CREATE-DIMENSIONS.htm`. Wording found in excerpts: Fusion "says the sketch is over constrained and wants to create a driven dimension instead". [comm] https://forums.autodesk.com/t5/fusion-design-validate-document/overconstrained-sketch/m-p/10178361. **The exact dialog text and button labels could not be verified.**
- **Geometric constraints**: a constraint that would over-constrain is **refused**, with a message along the lines of "Sketch geometry is over constrained". The message does not say which constraints conflict, which forum users often complain about. [comm] https://forums.autodesk.com/t5/fusion-design-validate-document/sketch-geometry-overconstrained/m-p/5222537
- I found no evidence of a SolidWorks-style "SketchXpert" conflict resolver dialog in Fusion. [unverified, absence]
- **Recommendation for luced-3d:** do what Fusion does (refuse the constraint; downgrade the dimension to driven) and also highlight the conflicting set, which Fusion does not do.

### 4.4 AutoConstrain (for reference)

- **Constraints > AutoConstrain** (also on an Automate tab) proposes complete constraint-and-dimension sets as result tiles.
- Suggestions preview in **purple**.
- Controls:
  - a slider for fewer or more constraints,
  - **Modify Geometry** with a tolerance (lets it adjust geometry to fit),
  - a **datum** point that dimensions align to,
  - Generate more.
- Each tile shows its status: Fully or Partially constrained.

[doc] `SK/SKT-AUTO-CONSTRAIN.htm`, `SK/REF-AUTO-CONSTRAIN.htm`

---

## 5. Dimensions

### 5.1 The Sketch Dimension tool (D)

Source: [doc] `SK/SKT-CREATE-DIMENSIONS.htm`

- **Pick → result**:

  | Picks | Result |
  |---|---|
  | one line | its length |
  | two parallel lines | the distance between them |
  | two points | linear distance |
  | two non-parallel lines | **angle** |
  | a circle | **diameter** |
  | an arc | **radius** |
  | a centerline + another entity | diameter across the centerline (used for revolve profiles) |

  [doc] `SK/SKT-CENTERLINE-GEOMETRY.htm` for the centerline case.
- **Point + line** gives the perpendicular distance. [unverified but standard]
- **Two points** give horizontal, vertical or aligned distance depending on where the label is dragged. Aligned dimensions are a documented concept; see the video page `SK/GUID-27529A4E-...htm`, "Apply aligned dimensions". The placement-zone behavior is [unverified].
- **Sequence**:
  1. Pick the geometry.
  2. Move the mouse to position the label.
  3. Click to place it.
  4. A value box opens (controlled by the `isDimensionEditedWhenCreated` preference).
  5. Type a value or expression, or **click an existing dimension to insert its parameter name**.
  6. Press Enter.

  The doc lists "Enter value … Press Enter … then move the mouse … click to place". Either way, value entry and placement are both part of one dimension. The tool stays active; **Esc** ends it. Geometry constrained by the new dimension turns black.
- **Before placing, right-click** for options:
  - Radius ↔ Diameter,
  - Driven ↔ Driving,
  - **Pick Circle/Arc Center** vs **Pick Circle/Arc Tangent**, to measure to the center or to the nearest or farthest tangent.
  - [doc] Tips on the same page.
- **Shift** while hovering selects a line's **midpoint** as the dimension reference. [comm] https://www.autodesk.com/products/fusion-360/blog/mastering-midpoint-constraints-autodesk-fusion/
- Clicking a model edge or vertex with the Dimension tool auto-projects it, if `isAutoProjectEdgesOnReference` is on and the view is normal to the sketch. [doc] API preferences

### 5.2 Editing a dimension

- **Double-click** a dimension to edit its value.
- Right-click > **Toggle Driven** / **Toggle Driving**.
- Converting a driving dimension whose expression references only driving dimensions into driven **freezes the expression into a static value, and the expression is not restored** when you toggle back. [doc]
- Driven dimensions can be referenced by other dimensions and features, **except** in Tangent and Offset dimensions. [doc]
- To reference dimensions from **another sketch**, right-click that sketch in the browser > **Show Dimensions**, then click them while editing. [doc]
- Dragging a dimension label repositions it. [unverified, trivial]

### 5.3 Names, expressions, units

- Every dimension is a **model parameter**, named automatically **d1, d2, …** in creation order across the design. [unverified for the exact scheme. Model parameters with automatic names are documented in `MD/GUID-76272551-3275-46C4-AE4D-10D58B408C20.htm`; the `d<n>` pattern is common knowledge]
- **Naming inline**: type `name=expr` in any value field, e.g. `Width=50` or `Length=Width*2`. The parameter is created with that name and added to **Favorites**. [doc] `MD/SLD-MODIFY-CHANGE-PARAMETERS.htm`
- **Expressions** (`MD/GUID-76272551-...htm`, [doc]):
  - Operators: `+ - * / ^ %` and parentheses.
  - Precedence: parentheses > `^` > unary minus > `*` `/` > `+` `-`.
  - **Function arguments are separated with `;`, never `,`**, so that comma-decimal locales keep working.
  - Constants: `PI`, `E`, `Gravity`, `SpeedOfLight`.
  - Comparisons: `> < >= <= == <>`. Logic: `and`, `or`, `not`. `if(cond; a; b)` can be nested.
  - Functions include sin/cos/sqrt and similar (see the page).
  - Units can be attached to any literal: `if(H < 500mm; 2; 3)`, `sin(15 deg)`.
  - **Parameter names** may contain `_ " $ ° µ`.
- **Text parameters** use single quotes and `+` concatenation. [doc]
- **Change Parameters** dialog (Modify > Change Parameters; it is also on the sketch Modify menu) [doc]:
  - A tree of model parameters grouped by feature, plus User Parameters.
  - Columns: Name, Unit, Expression, Value, Comments.
  - Filters for User and Favorites; search; Sort in Timeline Order.
  - **Automatic Compute** checkbox, with Apply.
  - **+ User Parameter** opens a dialog for Name, Unit, Expression and Comment.
  - In any parametric field, the **fx** toggle switches between the expression and its evaluated value.
  - Typing a favorite's name offers autocomplete.

### 5.4 Behavior worth copying

- **First-dimension auto-scale** (`isSketchScaledWithFirstDimension`). [doc] API
- Dimensions are **driving by default**; driven only when needed or toggled. [doc]
- Chamfer dimensions: in Equal Distance, the second distance is **driven by the first**. Two Distance has two independent distances. [doc] `SK/SKT-ADD-CHAMFERS.htm`

---

## 6. Fully-constrained feedback and dragging

- **Colors**:
  - under-defined: **blue** (orange dashed for construction),
  - fully defined: **black**,
  - fixed: **green**,
  - projected: **purple**,
  - lost projection: **orange or yellow**.
  - [doc] `SK/SKT-3D-SKETCH.htm`, `SK/SKT-FULLY-DEFINE-CONSTRAIN-SKETCH.htm`
- Coloring is **per curve**: individual curves turn black as they become fully defined, before the whole sketch does. [doc] `SK/SKT-FULLY-DEFINE-CONSTRAIN-SKETCH.htm` ("Individual curves can also be fully constrained…"). An Autodesk blog excerpt calls this coloring "sketch geometry based on constraint status… changing the color of lines as each constraint is satisfied". [comm] https://www.autodesk.com/products/fusion-360/blog/?p=75656
- Fusion has **no dedicated "over-constrained" red state** that I could verify. Instead it prevents over-constraint at creation (§4.3). Red is used for **errors** (failed compute). [unverified]
- **Browser icon**: a sketch's browser node shows an unlocked icon when it is under-defined and a **lock (red per the help) when it is fully constrained**. [doc] `SK/SKT-FULLY-DEFINE-CONSTRAIN-SKETCH.htm`, `SK/SKT-3D-SKETCH.htm`
- **Points**:
  - Endpoints that are free show **white dots**.
  - Constrained point–point joins show no dot.
  - Internal spline fit points show grey dots.
  - **Show Points** in the palette hides all of them.
  - [doc] `SK/GUID-685B9D79-...htm`
- **Dragging**: in Select mode, press-drag on a curve or point. The solver moves the **remaining degrees of freedom**, and constrained geometry "cannot move when you try to drag it". The tutorial tells you to drag under-defined entities to find what is still free. [doc] `SK/SKT-3D-SKETCH.htm`, `SK/GUID-0A723EF7-...htm`
  - Dragging a line's interior **translates** it if its endpoints are free.
  - Dragging an endpoint stretches the line.
  - Dragging a circle's edge changes the radius; dragging its center moves it.
  - [unverified, standard]
  - The solver minimizes movement of everything else. [unverified; inferred from behavior]

---

## 7. MODIFY tools

### 7.1 Fillet

Source: [doc] `SK/SKT-ADD-FILLETS.htm`, `SK/SKT-SKETCH-MODIFY-TOOLS.htm`

- **Valid inputs**:
  - two intersecting lines,
  - **a vertex** (the shared point of two lines),
  - **two parallel lines** (makes a semicircle),
  - a line + an arc that intersect,
  - two intersecting arcs.
- **Sequence**:
  1. Hover the first curve; it highlights. Click it.
  2. Hover the second curve; a **preview** appears.
  3. Click it.
  4. Drag the **radius handle** or type a radius.
  5. Enter ends the tool.

  The initial radius is proportional to the shorter of the two curves.
- **Result**:
  - an arc,
  - the source curves **trimmed back** to the tangent points,
  - **tangent + coincident** constraints at both ends,
  - a **radius dimension**.

  Trimming and constraints are [unverified in text; the doc says "fillet geometry and radius dimension display"] but they are standard and visible in Fusion.
- If the original corner was dimensioned to the vertex, Fusion keeps a **virtual sharp** (a construction point at the old corner). [unverified]

### 7.2 Chamfer (Equal Distance / Distance and Angle / Two Distance)

Source: [doc] `SK/SKT-ADD-CHAMFERS.htm`

- Pick a **vertex** (instant preview) or two lines. Works at a real intersection or an **extended** one.
- Drag the handles or type values.
- Equal Distance: two dimensions, the **second driven by the first**.
- Distance and Angle: a distance dimension plus an angle dimension.
- Two Distance: independent distances. The first handle drag moves both values.

### 7.3 Trim (T)

Source: [doc] `SK/SKT-TRIM-EXTEND.htm`

- **Hover** a curve: the segment between the nearest intersections on either side of the cursor highlights as the preview. **Click** removes it.
- **Press and drag**: every segment the cursor path crosses is trimmed (a "paint" trim).
- **A curve with no intersections is deleted entirely.**
- Trimming to a projected edge or to construction geometry works too: all sketch curves act as cutters. [unverified for construction, but standard]
- Endpoints created at intersections get **coincident** constraints to the cutting curve. [unverified]
- Enter ends the tool.

### 7.4 Extend

- Hover to preview the extension of the nearer end to the next intersection (the doc says "nearest extended intersection"). Click to apply.
- If there is no intersection, nothing happens: it "cannot extend".

[doc] `SK/SKT-TRIM-EXTEND.htm`, `SK/SKT-SKETCH-MODIFY-TOOLS.htm`

### 7.5 Break

- Hover to preview where the curve will split (at its intersections with other curves). Click to split the curve into 2 or more pieces that keep their shape.

[doc] `SK/SKT-BREAK.htm`

### 7.6 Offset (O)

Source: [doc] `SK/SKT-OFFSET.htm`, `SK/SKT-SKETCH-MODIFY-TOOLS.htm`

- **Selection**: one curve, **a chain of connected curves** (clicking one curve selects the tangent/connected chain [unverified detail]), or a **profile**. Only one selection set per offset.
- **Direction**:
  - **One Side** (distance; the side follows the cursor or a flip),
  - **Two Sides** (Distance 1 and Distance 2),
  - **Symmetric**.
- **Match Topology**: limits the offset so the child keeps the parent's topology.
- **Result**:
  - new curves,
  - **offset dimension(s)**,
  - an **offset constraint glyph** on both the source and the offset.
- **Breaking the association**:
  - Delete the glyph to break it.
  - Delete only the dimension to keep it associated with a free distance.
  - Right-click the glyph > **Add Offset Dimension** to restore it.
- **Ellipse rule**:
  - Picking near a major or minor axis gives an **ellipse** result (the distance holds only at the axes).
  - Picking elsewhere gives a true **oval** offset (constant distance).
- The API spells out the direction convention: the offset side follows the **flow direction** of the input curves, with positive to the right. [doc] `API/fusion_GeometricConstraints.htm` (`addOffset`)

### 7.7 Sketch Scale

1. Select geometry.
2. Pick the **base point**.
3. Type a scale factor or drag the handle.
4. OK or Enter.

[doc] `SK/SKT-SCALE.htm`. Whether dimensions are scaled or block the scale is not documented. [unverified; the expected behavior is that driving dimensions on the selection prevent the scale, or are themselves rescaled]

### 7.8 Move/Copy (M)

Source: [doc] `MD/SLD-USE-MOVE-COPY.htm`, `MD/GUID-FFD25CD3-0707-429E-B0E6-B7F9984CDC4C.htm`

- Inside a sketch, the dialog works on **Sketch Objects**.
- **Move types**:
  - **Free Move** (triad with translate and rotate handles; X/Y/Z distance and angle fields),
  - **Translate**,
  - **Rotate** (axis + angle),
  - **Point to Point**,
  - **Point to Position**.
- **Set Pivot** moves the triad.
- **Create Copy** must be checked **before** making adjustments.
- Moving sketch objects off-plane makes them 3D sketch geometry. [doc] `SK/SKT-SKETCH-MODIFY-TOOLS.htm`
- Constraints on moved geometry are kept and **fight the move** if they tie it to unmoved geometry. [unverified]
- With Move/Copy active, clicking a spline point toggles all spline handles. [doc] `SK/SKT-CREATE-SPLINES.htm`
- Copy/paste also works: Ctrl/Cmd+C, then Ctrl/Cmd+V into an active sketch. The paste lands at the cursor and opens Move/Copy. [doc] tutorial `SK/GUID-...` "Right-click … Paste. Or … Ctrl+V"

### 7.9 Blend Curve

Source: [doc] `SK/SKT-BLEND-CURVE.htm`

1. Choose **G1 (Tangent)** or **G2 (Curvature)** in the palette.
2. Pick curve 1, then curve 2. Sketch curves and **model edges** are both valid.
3. **The end used is the one nearer the pick or hover point.**

- Hover shows a preview.
- Clicking a picked curve again deselects it.
- The result is a spline with tangent or curvature constraints at both joints.

### 7.10 Change Parameters

Opens the Parameters dialog (§5.3). [doc]

---

## 8. Profiles

- Profiles are **computed automatically** from the closed areas of the sketch. [doc] `API/fusion_Profile.htm` ("Profiles are automatically computed by Fusion and represent closed areas within the sketch")
- Closed profiles are **shaded blue** (toggle: Show Profile). Open profiles can be used for surfaces, thin extrudes and loft rails. [doc] `SK/SKT-3D-SKETCH.htm`
- **Region splitting**: crossing or overlapping curves cut the plane into **separate minimal regions**. Two overlapping circles give three profiles, and each is picked separately. Shift-click (and Ctrl/Cmd-click to toggle) builds a multi-profile selection. A window selection grabs many. [comm] https://forums.autodesk.com/t5/fusion-support-forum/extrude-entire-sketch/td-p/11441404, plus tutorial [doc] ("You can add or remove profiles from a selection later by using the CMD key on mac and CTRL key on windows").
- **Nesting**: a region inside another region (a hole) is its own profile; the outer profile is the ring. [unverified, standard] The API exposes `Profile.profileLoops`, with outer and inner loops. [doc] `API/fusion_ProfileLoops.htm` (TOC)
- **Construction geometry is excluded** from profile detection. [doc] tutorial: "Construction geometry is not considered when looking for profiles". **Centerlines and projected curves are included.** [doc] `SK/SKT-3D-SKETCH.htm`
- **Text** is extrudable directly as a text object, and its glyph outlines act as profiles. Explode Text turns it into ordinary curves and profiles. [doc] TOC entries `SK/SKT-EXPLODE-TEXT.htm`, `SK/SKT-CREATE-TEXT.htm` (Emboss, Extrude, Explode). Single-line SHX fonts make **no** closed profiles.
- Small gaps break closure. Fusion does not heal gaps silently. [comm] "Why is this shape not closed?" https://forums.autodesk.com/t5/fusion-design-validate-document/why-is-this-shape-not-closed/m-p/6698335

---

## 9. Units

- **Document units** are set per design: Browser > Document Settings (gear) > Units > Change Active Units, choosing mm, cm, m, in or ft. "**Set as Default**" applies them to new designs. [comm] https://www.autodesk.com/products/fusion-360/blog/de/how-to-set-units-in-fusion-360/. The preference **Default Units > Design** sets the default. [doc] `GS/GUID-878489CD-...htm`
- Fusion's new-design default is **mm** for most locales. [unverified per locale]
- **Internal units are cm** for length (and radians for angle). All API values are in cm. [doc] `API/core_UnitsManager.htm`. Not user-visible, but worth knowing if values are ever exchanged with Fusion.
- **Parsing**:
  - A bare number takes the document length unit (or degrees for angle fields).
  - A unit suffix overrides it, with or without a space: `10 mm`, `10mm`, `1 in`, `1"`, `2 ft`, `0.5 cm`, `30 deg`, `1 rad`.
  - **Units can be mixed** in one expression: `1 in + 5 mm`.
  - The full unit list is in `MD/DSN-REF-PARAMETERS-UNITS.htm` [doc]. Length: mm, cm, m, hm, micron/µ, in/", ft, yd, mi, nauticalMile, mil. Angle: rad, deg/°, grad.
  - Fusion **standardizes** what you typed when it stores it: `"1.5"` becomes `"1.5 mm"`, and `"1.5 cm + 1.50001 centimeter"` becomes `"1.5 cm + 1.50001 cm"`. [doc] `API/core_UnitsManager.htm` (`standardizeExpression`)
- **Display** (Preferences > Unit and Value Display) [doc] `API/core_UnitAndValuePreferences.htm`:
  - general (length) precision, in decimals,
  - angular precision,
  - trailing zeros hidden, with a minimum precision when they are hidden,
  - unit abbreviations or symbols,
  - period or comma decimal,
  - foot-inch and degree display formats,
  - scientific notation thresholds.

  The display rounds; the stored value and expression do not. Dimension labels show the value without its unit when the unit is the document unit. [unverified]

---

## 10. Shortcuts, selection, S toolbox

### 10.1 Keys

From [doc] `GS/GUID-F0491540-0324-470A-B651-2238D0EFAC30.htm` unless noted. The same keys work on Mac and Windows except where a modifier is shown.

| Key | Action |
|---|---|
| L | Line |
| R | 2-Point Rectangle |
| C | Center Diameter Circle |
| T | Trim |
| O | Offset |
| P | Project |
| D | Sketch Dimension |
| X | Normal/Construction toggle |
| M | Move/Copy |
| I | Measure |
| **Shift** (hold) | snap and constrain to a midpoint |
| **Ctrl / Cmd** (hold while placing) | suppress inference and snapping [comm, §3.3] |
| 1 / 2 / 3 | Window / Freeform / Paint selection mode |
| Del | delete |
| S | toolbox (search + pinned tools) |
| Enter | commit the current value; finish the tool |
| Esc | cancel the current pick; exit the tool [doc tutorials] |
| Tab | next heads-up field (on 3D sketches, the next rotation handle) |
| Ctrl+Z / Cmd+Z | undo |
| Ctrl+Y / **Cmd+Shift+Z** | redo |
| Ctrl/Cmd+C, V | copy and paste sketch geometry |
| Middle-drag / Shift+middle-drag / wheel | pan / orbit / zoom (Fusion mouse preset) |
| F6 | fit view [doc preferences page] |

- Keyboard shortcuts do not fire while a text field is focused. [doc]

### 10.2 Selection

- Click selects. **Shift- or Ctrl/Cmd-click** adds to the selection. [doc] `MD/SLD-SELECT-OBJECTS.htm`. Ctrl/Cmd-click toggles an item out. [doc] tutorial
- **Window selection**:
  - Drag **left to right** to select items **entirely inside** the box.
  - Drag **right to left** to select everything the box **crosses**.
  - The same applies to Freeform (lasso).
  - [doc] `MD/SLD-SELECTION-MODES.htm`
- In Select mode, dragging starts on empty space. Starting a drag on geometry drags the geometry (§6). [unverified, standard]
- **Click and hold** opens a **pick-through list** for overlapping items (Depth and Parents tabs). [doc] `MD/SLD-SELECT-OBJECTS.htm`
- Double-clicking a curve selects its connected chain. [unverified]
- Selection filters and priority (Select menu) apply in sketches too. [doc]

### 10.3 S toolbox and marking menu

- **S** opens a floating toolbox at the cursor:
  - a **search field** that finds any command,
  - **pinned shortcuts**, with a separate set per workspace and **one for Sketch**.
  - Hover a search result to pin it, or use "Pin to Shortcuts" on any toolbar item.
  - [comm] https://www.autodesk.com/products/fusion-360/blog/quick-tip-the-s-key/ and the [doc] shortcut table ("Model Toolbox — S").
- **Right-click marking menu**: a radial menu of common commands, with Finish Sketch and Normal/Construction under Sketch. [doc] `SK/SKT-FINISH-SKETCH.htm`, `SK/SKT-CONSTRUCTION-GEOMETRY.htm`; reference at `GS/GUID-6514ABC1-CB75-4F0B-AB0E-316FAD36BA93.htm`

---

## 11. Gaps: what this study could not verify

Confirm these in a running copy of Fusion before treating them as requirements:

1. The exact wording and buttons of the over-constrained dimension warning, and whether "don't ask again" exists.
2. Fusion's exact inference glyph artwork and the style of its alignment guide lines (dotted? color?).
3. Whether Equal is ever inferred while drawing.
4. The exact auto-constraint set placed by each rectangle, slot and polygon type.
5. Whether the sketch Fillet leaves a virtual sharp, and how it treats a dimension on the trimmed corner.
6. Whether Sketch Scale rescales or is blocked by driving dimensions.
7. Whether there is a standalone Polygon constraint tool in the Constraints panel. It is absent from current help, but the API has the constraint.
8. Dimension placement zones for two points (horizontal, vertical or aligned by cursor position) and how they are switched.
9. The `d<n>` naming counter: per design, and whether numbers are reused after deletion.
