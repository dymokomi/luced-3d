# Surfacing for luced-3d: Alias, Plasticity, xNURBS, Parasolid and Rhino

Research and design, 2026-10-12. No product code was changed for this document. It answers the
owner's request:

> "For CAD work let's also look at Plasticity and Alias Automotive Studio for different tools,
> especially for doing blends and alignments and projections and trims and CV manipulations. I
> think Alias, XNurbs, Parasolid are good things to pay attention to."

It follows [FUSION-CAD-UX.md](FUSION-CAD-UX.md) (cited as **FUSION §n**). That document made the
CAD context a Fusion 360 workflow of sketches, solid features and direct modeling. This one covers
the tools that work on freeform surfaces and the curves that drive them, where Fusion is thin:
blends between surfaces, matching continuity across edges, projecting and trimming, building
surfaces from curves, filling holes, and editing control vertices (CVs).

The owner's rules apply throughout:

- full parity with the reference tools;
- degree 5 by default for freeform curves and patches, and G3 as multi-span quintic B-splines;
- hot geometry in Luce Base;
- learn from the references, never copy their code.

Sources:

- **Alias.** The current Alias help is built in JavaScript and could not be fetched. The static
  reference pages of the 2014–2016 help sets could, and they are the main source:
  - `help.autodesk.com/cloudhelp/2014/ENU/Alias/files/<Tool>.htm`;
  - `help.autodesk.com/cloudhelp/2015/ENU/Alias-Reference/files/...`.

  The 2023 reference, the 2025 and 2026 What's New pages, Autodesk tutorials and forums fill in
  the rest. Option names have been stable since then, and later additions are marked (2025+).
- **Plasticity.** Its manual at doc.plasticity.xyz and the release notes there.
- **xNURBS.** xnurbs.com, its Rhino and SolidWorks release notes, McNeel's forum and blog.
- **Parasolid.** The V35.0 Functional Description (July 2022), read through an unofficial mirror
  (`q-solid.com/Parasolid_Docs_V35/chapters/fd_chap.NNN.html`, where file NNN holds chapter NNN−1),
  and Siemens' release-note blog posts.
- **Rhino 8.** Its help, `docs.mcneel.com/rhino/8/help/en-us/commands/<cmd>.htm`.
- **Our code.** luced-3d and luce-cad at `origin/main` on 2026-10-12 (luced-3d 3b09240), read.

Claims carry FUSION's tags:

- **[doc]**: the vendor's help or reference;
- **[comm]**: a forum, blog, tutorial or third party;
- **[unverified]**: not confirmed in a source.

URLs are given once, where a tool is first described.

## 1. Decision in one page

**These tools are a second modeling style.** Fusion's tools work on solids, through sketches and
features. Alias works on surfaces, through curves and their CVs, and it is built out of a small
number of ideas:

- **Curves come first.** Most surfaces are built from curves: free 3D curves, blend curves, curves
  on surfaces, isoparms and edges. luced-3d has curves only inside planar sketches. There are no 3D
  CAD curves, and no curves lying on a surface.
- **Every surface tool sets continuity per edge.** The choices are G0, G1, G2 or G3, with a
  continuity check drawn on the model.
- **Continuity is matched by moving CV rows.** G1 is set by the row next to the edge, G2 by the
  next row and G3 by the one after that. Align, Alias's central tool, does this to an existing
  surface. Its sliders (Tangent Scale, Curvature Scale, G3 Scale) are the free parameters of the
  match (§6.1).
- **Structure is explicit.** "Explicit Control" in every tool sets the degree and span count. CV
  tools edit the net in world space, along the hull, or along the surface's normal and its U and V
  directions.
- **Trims are curves on surfaces.** Projections and intersections make curves on surfaces. Trim
  keeps or discards the regions they bound, or divides them into separate surfaces. Stitch joins
  surfaces into shells.

**Plasticity and xNURBS add filling and a modern UX.** Plasticity runs on Parasolid (it began on
C3D). Its surfacing commands that need more than Parasolid offers (xNURBS, Square, Align) come from
the xNURBS library. xNURBS is an energy-minimizing ("variational") surface solver: it makes the
smoothest NURBS surface that meets the boundary at G0, G1 or G2. Its algorithm is not published,
but the method family is (Welch & Witkin 1992, Greiner 1994). Rhino 9's rewritten Patch follows
the same approach.

**Parasolid sets the bar for blends on solids.** Edge blends, face-face blends between surface sets
and three-face blends; conic, G2 and chamfer sections; four overflow behaviors; limits and caps;
setbacks and Y-blends. luce-cad already does Fusion's fillets. Parasolid's model is wider, and
Alias's Surface Fillet, Freeform Blend and Round are its surface-side counterparts.

**What we have.** luce-cad's blends, local operations and sketch Blend Curve; Edit CAD's CVs and
Patch levels; and zebra, isophote and curvature shading. These cover a few of the tools here
(§3). The rest is missing: 3D curves, curves on surfaces, every curve-built surface, Align, the
trims, stitching, N-sided fill, a NURBS structure toolkit, curvature combs and continuity checks.

**The plan** (§8) builds the measuring tools first, then the NURBS toolkit and CV editing, then
curves and trims. Align follows, then the surface builders, then blends and fill. Parasolid's
remaining blend options on solids come last.

| Stage | What it delivers |
|---|---|
| 0 | Measuring: exact curvature combs, continuity checks, deviation (Base: third derivatives). **Done** (§8) |
| 1 | The NURBS toolkit in luce-cad, and CV editing at Edit CAD's CVs level |
| 2 | 3D CAD curves and curves on surfaces; Blend Curve in 3D, G0–G4 |
| 3 | Project, Intersect, Trim, Untrim, Divide, Trim Convert, Stitch; open surface bodies throughout |
| 4 | Align (match) G0–G3, with every Alias option |
| 5 | Surfaces from curves: Square, Skin, Rail, Profile, Set Planar, Extend |
| 6 | Blends between surfaces: Freeform Blend, Profile Blend, Surface Fillet between face sets |
| 7 | Fill: N-sided and four-sided variational patches (xNURBS parity) |
| 8 | Parasolid's blend options on solids: conic, overflow, limits, caps, Y-blends, corners |

## 2. Shared ideas across the references

### 2.1 Continuity

- **Names.** Alias's menus read G0 Position, G1 Tangent, G2 Curvature, G3 Curvature. G3 is
  defined as continuity of "the rate of change of curvature" [doc]
  ([Surface Fillet](https://help.autodesk.com/cloudhelp/2014/ENU/Alias/files/SurfacesMultiSurfacefilletSurfacefillet.htm)).
  Older dialogs and the check locators say Position, Tangent, Curvature, with locators lettered P,
  T and C. Align's Diagnostic Feedback also reports torsion [doc].
- **How high each tool goes.** Blend curves go up to G4 in Alias
  ([Constraint Continuity](https://download.autodesk.com/us/alias/2013help/files/BlendConstraintContinuity.htm))
  and in Rhino (BlendCrv, BlendSrf) [doc]. Rhino's MatchSrf and MatchCrv stop at G2 [doc].
  Plasticity's Bridge Curve goes to G3; its Align, Patch, Loft and xNURBS to G2 [doc].
- **Implied continuity.** Alias's Square and Rail also offer Implied Tangent and Implied Curvature,
  which give continuity with the mirrored half across a symmetry plane. They also offer Tangent
  Angle, a fixed angle to the neighbor [doc].
- **Degree needed.** Alias states the degree a continuity needs across a single span [doc]
  (Freeform Blend, Profile Blend):
  - G2 needs degree 4 on one side or 5 on both;
  - G3 needs degree 6 on one side or 7 on both.

  So Alias's G3 fillet sections are fixed at degree 7. We reach G3 at degree 5 with three spans
  (eight control points: four rows from each side), as luce-cad's G3 fillets already do (its
  MODELING.md, "G2 and G3 fillets"). Where a reference tool offers a single-span (Bézier) result, our
  default is the multi-span quintic. Explicit Control lets a user ask for a single span of higher
  degree (§10, question 2).

### 2.2 Explicit Control and Bézier patches

- **Explicit Control.** Alias tools carry an "Explicit Control" switch with the same meaning
  everywhere [doc]:
  - Off: the tool picks degree and spans. It raises the degree to the master's and inserts spans,
    up to **Max. New Spans**. With **Insert at Midpoint** on, a span is split at its middle rather
    than at the worst deviation.
  - On: the user sets U and V degree and spans.
  - In Align, Explicit Control is on by default and starts at the input's own structure.

  Plasticity's Studio commands (Square, Align, Rebuild Face Explicit) expose the same as Degree and
  Spans [doc].
- **Surface Type.** Alias's multi-surface builders (Surface Fillet, Freeform Blend, Profile Blend,
  Skin, Profile, Tubular Offset, Draft) choose **Single surface** or **Multiple surfaces** (one patch
  per input boundary pair) [doc].
  - With Multiple, **Bézier Surfaces** makes each patch one span, U degree 5 by default.
  - **Short Edge Tolerance** is the shortest span allowed when cross knots are inserted.
  - **Surface Edit › NURBS to Bezier** splits any surface into single spans
    ([page](https://help.autodesk.com/cloudhelp/2014/ENU/Alias/files/GUID-CA27685F-1EC8-44B7-9088-92704B6FCE82.htm)).
- **Class A practice.** That class-A surfacers prefer single-span patches of degree 5 to 7 is
  practitioner lore, not an Autodesk statement [comm]. An Autodesk tutorial does say that "many
  A-class surfacers prefer the Align tool's direct control" over blend curves
  ([Blend curve tips](https://help.autodesk.com/cloudhelp/2019/ENU/Alias-Tutorials/files/GUID-0461C378-446B-4166-85FB-9D0DA0F6F9E8.htm)).

### 2.3 The tool window, history and checks

**Alias** [doc]:

- **Control window.** Each tool's options are in a "<Tool> Control" window. **Auto Update**
  recomputes live; with it off, Update (or the space bar) recomputes.
- **Buttons.** Reset, Undo All or Revert, and **Next** (finish this one and start another).
- **History.** **Create History** keeps construction history: edit an input and the result is
  rebuilt. Query Edit reopens a tool on an object that has history.
- **Continuity Check.** Draws P, T and C locators along the boundaries, green when met and
  yellow or red when not.
- **Chain Select.** Takes every tangent-continuous edge or curve.
- **Flow Control.** Says how the cross edges at Start, Interior and End meet the boundaries: Edge
  align, Extend, Connect ends, or Default/Free (square to the boundary). Clicking the label on the
  model cycles the choices.
- **Modify Range.** Start and End sliders, 0 to 1, with arrows on the model.
- **Variable values** (radius, offset, angle). A slider ball runs on a rail, with a value handle
  beside it. A modifier click on the rail adds one; a modifier right click deletes one.
- **Vector Options** (Project, Trim, Align's Project, Draft): X, Y, Z, View (the view's normal,
  refreshed on request), Picked (a vector object), or Normal (each point's surface normal).
  **Retain Vector** keeps a reusable vector object.

**Plasticity** [doc] (doc.plasticity.xyz: selection-mode, command-palette, radial-menu, command-bar):

- **Selection modes.** 1 control point, 2 edge or curve, 3 face, 4 solid or sheet. Shift adds a mode.
- **Starting a command.** Selecting often starts the likely command: edges start Fillet, a face starts
  Offset Face, outer sheet edges start Extend.
- **Handles and keys.** A yellow dot drags the main value, and a floating dialog holds the rest.
  Letter keys set a value by moving the mouse (D distance, A angle, Tab cycles a mode or
  continuity). A right click is OK. Ctrl shows the original.
- **Per-edge continuity.** Set by clicking black circles drawn on each boundary (Patch, Loft,
  Align).
- **Other ways in.** Shift+F offers commands for the selection, F searches commands, and radial
  menus are user-defined.

**Rhino** [doc]: history per command (where "Delete input" is off); BlendSrf's Edit reopens a blend;
Shift makes edits symmetric; Alt changes a shape curve's angle.

**Our equivalents.**

| Their idea | Ours |
|---|---|
| Create History, Query Edit | A node in a CAD network: its inputs re-cook it, and selecting it edits it (FUSION §4) |
| A one-off result | An Edit CAD step |
| Control window, Auto Update | The parameter panel and the tool bar; every cook is live, on the worker |
| Next | Repeat, which leads the A and S menus (FUSION §6.5) |
| Continuity Check locators | Stage 0's check, drawn by the tool and as its own display |
| Black circles per edge | Per-edge continuity labels on the model, clicked to cycle (§7.3) |
| Variable value manipulators | The variable fillet's handles, generalized (§7.3) |

## 3. What we have, and the gaps

Checked in the code on 2026-10-12.

### 3.1 What exists

**luce-cad geometry** (`src/geometry/`):

- **Evaluation.** Rational B-spline curves and surfaces, degree 1 to 8 (`nurbs.lucb`; the basis
  buffer is nine wide). Basis derivatives go to the second order only, so the third derivatives
  that a G3 check needs are missing.
- **Point inversion** on B-spline surfaces (`inversion.lucb`): Newton from a seed, then a lattice
  and Greville starts.
- **Surface-surface intersection by marching** (`modeling/march.lucb`), each curve fitted as a
  cubic.
- **Knot insertion and degree elevation exist, but privately.** They live inside `spline_rays`,
  `setback` and `strip_join`. There is no public knot removal, degree reduction, splitting, fitting
  or rebuild.

**The B-rep:**

- **Edges** are 3D curves: lines, arcs, ellipses, and trimmed B-spline intervals. They carry no
  parameter-space curves (pcurves).
- **Faces** are planes, cylinders, cones, spheres, tori and rational B-splines.
- **Tolerance.** One tolerance per model.
- **Open surface bodies.** They exist (Copy faces, the quilts Replace Face takes), but no tool
  makes surfaces from curves.

**Blends** (luce-cad MODELING.md):

- **Fillets.** Edge fillets at G1, G2 and G3 (G2 one quintic span, G3 three); variable radius along
  tangent chains; chord length; Full Round; setback corners for three edges (thin-plate least
  squares, `patch_fit.lucb`).
- **Chamfers.** Equal, two distances, distance and angle; corner types.
- **Loops.** Loops between two curved faces.

**Local operations.** Offset, move, rotate, replace, delete with healing, split face, shell (FUSION
§9).

**Sketch** (planar):

- **Splines.** Fit-point and control-point splines (degree 5), and conics.
- **Blend Curve** joins two sketch curves' ends with a quintic at G1, G2 or G3.
- **Project** casts edges, faces and silhouettes onto the sketch plane only.

**Edit CAD**:

- **Levels.** Object, CVs, Edges, Faces, Smart, Patch. Patch is a whole surface, picked by its
  `cad_surface`.
- **CV tools.** At the CVs level, CVs move with the gizmo, Rotate and Scale, and with Noise
  (Mountain), Flatten and Snap. Soft radius and falloff are by 3D distance. Symmetry works. A
  moved boundary CV takes its trims along (luce-cad `with_cvs_moved`, `with_cvs_at`).

**Viewport shading** (luce-3d `set_shading`). Zebra (stripes, duty, axis, planar, stripes only),
Isophotes, and Curvature (mean, Gaussian, k1, k2, largest |k|). All three read the tessellation.

### 3.2 Gaps

| # | Gap | Where it is needed |
|---|---|---|
| S1 | **Closed by Stage 0** (§8). Was: no third derivatives; no exact continuity measure along an edge (G0 gap, G1 angle, G2 and G3 differences); no curvature combs on curves, edges or isoparms; no deviation map. | Every tool's check; Stage 0 |
| S2 | No public NURBS toolkit: insert and remove knots, raise and lower degree, split, extract a span, make knot vectors compatible, reparameterize, fit within tolerance, rebuild, reduce spans, remove multiple knots, convert analytic faces to B-splines. Degree is capped at 8: Alias builds to degree 9, Rhino rebuilds to 11. | Every stage |
| S3 | CV editing has only world-space moves. Missing: moves along the normal and U and V (NUV); sliding along the hull; picking a whole hull row; falloff counted in CV rows rather than 3D distance; a proxy of the original hull; step size and drag strength; locked rows that keep continuity. | Stage 1 |
| S4 | No 3D CAD curves outside sketches, and no curves on surfaces. No isoparms as objects, and no duplicating an edge or isoparm as a curve. | Stages 2–7 |
| S5 | No Project or Intersect onto surfaces. The sketch's Project casts onto its own plane only. | Stage 3 |
| S6 | No trimming by curves: Trim, Untrim, Divide, Trim Convert. Split Face takes only a face or a plane. | Stage 3 |
| S7 | No stitching or unstitching of surfaces into shells, and no tolerant edges. | Stage 3 |
| S8 | No Align or match of a surface or curve to another, at any continuity. | Stage 4 |
| S9 | No surfaces from curves: Square, Skin (loft), Rail (sweep), Profile, Set Planar, Revolve or Extrude of a free curve to a sheet. Sweep and loft are luce-cad's limit 5. | Stage 5 |
| S10 | No Extend of a surface or curve (linear, natural, soft, reflective). | Stage 5 |
| S11 | No blends between surfaces: Freeform Blend, Profile Blend, a fillet between two face sets that need not share an edge (Parasolid's face-face blend), 3D Blend Curve, Tubular Offset. | Stages 2, 6 |
| S12 | No N-sided or four-sided fill with continuity (xNURBS, Alias N-sided, Rhino Patch). | Stage 7 |
| S13 | Blends on solids lack conic (rho) and Bias, Lead and Form Factor sections; one-sided curvature; Parasolid's overflow choices (smooth, cliff, notch); limits and caps; Y-blends; vertex blends; corners of more than three edges; delete and identify blends beyond healing. | Stage 8 |
| S14 | No corner tools between existing surfaces: Ball Corner, Corner Blend, Bridge Fillet. | Stage 8 |

## 4. Alias AutoStudio

### 4.1 Blends

**Surface Fillet** (Surfaces › Multi-Surface Fillet) [doc]
([reference](https://help.autodesk.com/cloudhelp/2014/ENU/Alias/files/SurfacesMultiSurfacefilletSurfacefillet.htm),
[workflow](https://help.autodesk.com/cloudhelp/2015/ENU/Alias-Modeling/files/Create_a_fillet_surface.htm)).

- **What it joins.** A fillet between two **sets of surfaces**. They need not share an edge, and a
  tangent break splits a set by itself.
- **Picking.** An arrow on each set shows the side; a click flips it. Build makes the fillet, and
  history lets surfaces be added to or taken from either set.
- **Construction.** Radius (rolling ball) or Chord. Chord's Chordal Type is the distance between the
  contact lines, or the tangent length.
- **Section Type:**
  - G0 Chamfer;
  - G1 Circular;
  - G2 Curvature;
  - G3 Curvature;
  - Bias (peak radius pushed toward one set by a Bias Factor, negative toward set 1);
  - Lead (peak radius plus a tangent offset, tangent both sides).
- **Curvature** (None, Side 1, Side 2, Both). G2 or G3 on one side only; for Bias, G2 and G3.
- **Radius sizing.** **Specify** is Center Radius (the radius at the section's middle), Tangent
  Offset (the ball touching both inputs) or both. For Bias and Lead it is Peak Radius or Knee Ratio
  (peak over tangent offset).
- **Form Factor**, 0.1–2: the ratio of inner to outer CV arm lengths. Smaller is sharper.
- **Variable Fillets.** Radius or chord set at points along the fillet with handles.
- **Explicit Control.** U degree 2–9. V degree 3–6 for G1, 5–7 for G2, 7 for G3. Max. Spans, or
  Uniform Spans.
- **Flow Control.** Edge align, Extend or Free at Start, Interior and End. **Modify Range** sets
  the ends. A forum fix for many failures is to set Flow Control to Default
  ([forum](https://forums.autodesk.com/t5/alias-forum/problems-with-round-tool/m-p/6848254)) [comm].
- **Surface Type and Trim.** Surface Type and Bézier (as §2.2). Trim Type is Automatic (the inputs
  trimmed back to the contact lines), Curves-on-surface (the contact curves only) or Off.
- **Checks.** Curvature Comb on the result: drags change its density and slide it along (2025.1).
  Continuity Check.

**Symmetric Fillet** [doc]
([page](https://help.autodesk.com/cloudhelp/2014/ENU/Alias/files/GUID-3D7BE61C-2D8F-4A4B-883B-B54560A1D778.htm)):
the fillet across a symmetry plane, with the same section types and Flip Fillet.

**Freeform Blend** (Surfaces › Multi-Surface Blend) [doc]
([page](https://help.autodesk.com/cloudhelp/2014/ENU/Alias/files/SurfacesMultiSurfaceblendFreeformblend.htm)).

- **What it joins.** A blend between two picked contact lines rather than a radius. Each side is a
  chain of surface edges, isoparms, curves on surfaces or free curves.
- **Continuity.** Side 1 and Side 2 each G0–G3. A side of free curves only is G0.
- **Shape.** **Side 1 / Side 2 Shape**: above 1 is tighter toward the corner, below 1 rounder.
  **Lock Shape Controls** keeps the two alike.
- **Proportional Crown** with a Crown Value (−0.25 to 0.25 of the rail distance), when both sides
  are G0.
- **Structure.** Explicit Control (U degree 2–9, Max. Spans). Flow Control (Edge align, Connect
  ends, Free). Modify Range for both sides. Surface Type and Bézier. There is no trim option.

**Profile Blend** [doc]
([page](https://help.autodesk.com/cloudhelp/2014/ENU/Alias/files/SurfacesMultiSurfaceblendProfileblend.htm)).

- **What it adds.** Freeform Blend shaped by any number of **profile curves** placed between the
  sides: blend curves, free curves or surface boundaries.
- **Options.** Side 1 / Side 2 continuity G0–G3. **Interior Edge Align** (off: the cross edges meet
  at 90°).
- **A stated limit.** Between several blend patches only G1 is guaranteed, even when the sides are
  G2.

**Round** (Surfaces › Round) [doc]
([page](https://help.autodesk.com/cloudhelp/2014/ENU/Alias/files/SurfacesRound.htm)).

- **What it does.** Rounds many edges at once and builds the corner pieces.
- **Workflow.** Pick or box edges. Set radii on handles; clicking the green line adds a radius
  point, so radius can vary. Build. Revert keeps the handles.
- **Corner options:**
  - **Equal Radius Corner**: Three surfaces, Triangular surface (one degenerate side) or With
    setbacks (six surfaces);
  - **Unequal Radius Corner**: Single Surface or With Setbacks;
  - **Mitred Corner** (one edge of radius 0): Blended or Sharp;
  - **Four Sided**: Single Surface or With Setbacks (eight surfaces).
- **Trim Type.** As Surface Fillet's.
- **How it differs from Surface Fillet.** An Autodesk course says Round needs exactly
  coincident edges, is meant for many small detail fillets, and builds the three-fillet corner that
  Surface Fillet does not
  ([course](https://www-pt.autodesk.com/learn/ondemand/course/alias-essentials/unit/4bvhzMxB6PmFmvqfTWNV9h))
  [comm]. Round is G1 only.

**Ball Corner** [doc]
([page](https://help.autodesk.com/cloudhelp/2014/ENU/Alias/files/SurfacesBallCorner.htm)).

- **What it makes.** A corner patch between three fillets and a primary surface.
- **Shape.** Pivot Curve Length Ratio. Start and End Length Ratios. Center Adjust with Center
  Height.
- **Continuity.** Position (the default), Tangent or Curvature.
- **Structure and trim.** Explicit Control (Side and Pivot degree 3, one span each, by default).
  Trim Primary.

**Corner Blend** (2025+): where three or four surfaces meet, with Edge Shape sliders. Its Base
Curve Type is Fillet (Base Radius and Form Factor) or Freeform (contact points movable)
([2025](https://help.autodesk.com/cloudhelp/2025/ENU/Alias-WhatsNew/files/wn-whatsnewinalias2025/wn-alias-corner-blend-2025.html),
[2025.1](https://help.autodesk.com/cloudhelp/2025/ENU/Alias-WhatsNew/files/wn-whatsnewinalias2025/wn-alias-corner-blend-2025-1.html))
[doc]. The full option list could not be fetched.

**Bridge Fillet** (2025+): circular fillets joining three surfaces or sets, tangent to all three,
with an optional trim. In 2025.1 it gained Bézier in V and a Bridge Treatment option
([page](https://help.autodesk.com/cloudhelp/2025/ENU/Alias-WhatsNew/files/wn-whatsnewinalias2025/wn-alias-bridge-fillet-2025.html))
[doc].

**Tubular Offset** [doc]
([page](https://help.autodesk.com/cloudhelp/2014/ENU/Alias/files/SurfacesRollededgeTubularoffset.htm)):

- **What it makes.** A tube, groove or bump along a curve on a surface.
- **Options.** Variable radius on handles; Flip (groove to bump); Tangent and Normal offsets;
  Bézier; trim of curves on the surface, or of the inside of the tube.
- **Its neighbors.** **Fillet Flange** builds a wall, a fillet (G1 or G2, Form Factor) and a flange
  together. **Panel Gap** and **Tube Flange** are the other "rolled edge" tools.

**Blend Curve toolbox** [doc]
([Create](https://help.autodesk.com/cloudhelp/2014/ENU/Alias/files/BlendCurvecreate.htm),
[Edit](https://download.autodesk.com/us/alias/2013help/files/Blendcurveedit.htm)).

- **What a blend curve is.** A free curve defined by constraints at **blend points**: a position,
  and continuity to a curve or surface. It stays associated with what it touches.
- **Create:**
  - Knot Spacing: Uniform (the default) or Chord;
  - **Curve Degree**: 1, 2, 3, 5 (the default) or 7;
  - Auto Align at Surface Corners;
  - Curve to Curve Continuity: G2 or G0;
  - Pivot Position;
  - (2025.1) **Curve Shape**: Relax (long, loose) or Tight (shorter, fixes inflection kinks).
- **Constraints**, set per blend point:
  - Continuity G0–G4;
  - Interpolation Direction: location only, a fixed direction, or relative to the object;
  - Direction Type: one sense, or parallel either way;
  - **Curvature Type**: Parametric (along the surface's isoparm, for G2 to an edge) or Geometric (in
    the plane of the normal and the direction).
- **Blend Curve Edit.** A handle on each blend point for position, tangent length and tangent
  direction, with separate Tangent and Curvature handles. Picking both points edits them
  symmetrically.

### 4.2 Align

Object Edit › Align › Align, since 2009 [doc]
([reference](https://help.autodesk.com/cloudhelp/2015/ENU/Alias-Reference/files/ObjectEditAlignAlign.htm),
[workflows](https://help.autodesk.com/cloudhelp/2015/ENU/Alias-Modeling/files/Workflows_for_the_Align_tool.htm)).

**Picking:**

- Click the **input** edge (the one that changes), then the **master**. The master may be a surface
  edge, an isoparm, a curve on a surface, a trim edge or a free curve.
- On a curve, click near the end to align.
- Two masters, at both ends or on opposite edges, live in one history item, and a label on the
  model switches between them.

**Options:**

- **Continuity**: G0, G1, G2, G3.
- **Alignment Type:**
  - **Edge** (the default);
  - **Project**: the input edge is projected onto the master along a vector, and a curve on the
    surface is made so the master is trimmed. Shrink to Fit; NoCOS skips the curve.
  - **U/V**: a curve to a surface;
  - **Vector**: only along a chosen vector.
- **Vector** (Edge type, G1 and G2): G0 first, then the tangent and curvature rows move only along
  the vector.
- **Position Influence**, 0–1. At 0 the input keeps its own parameterization and its CVs move least
  (nothing moves if the fit is already within tolerance). At 1 the input takes the master's
  parameterization: a better fit, but CVs may slide sideways. This is the nearest Align comes to
  "proportional or fixed".
- **Tangent Balance.** Sets the tangent and curvature row lengths so their start and end ratios
  match the master's, mimicking the master's inner hull. The scale sliders then work in proportion.
- **Blending.** **Extra CV Rows** carry the change further into the surface; the continuity rows
  are left alone. **Blend Factor**: positive decays the change exponentially, 0 linearly, negative
  grows it.
- **Partial** (off by default for surfaces). The input aligns to the nearest part of the master.
  Start and End sliders have arrows that snap to the master's ends.
- **Explicit Control** (on): the input's degree and spans, shown and editable. Off: the degree is
  raised to the master's and spans are inserted until continuity holds.
- **Outer Edge** (G1 and up): Start Align and End Align are Edge Align (the side edges follow the
  neighbor's edge) or **Skew**, with an angle and a rotation handle. **Align Start/End Together**.
- **Tangent and curvature rows:**
  - Starting and Ending **Tangent Scale**, **Curvature Scale** and **G3 Scale**;
  - **AutoScale G2** or **AutoScale G3** keeps the rows' relative lengths as one is scaled;
  - on the model, outer arrows scale each end and a middle arrow slides the whole row.
- **Curves only.** **Attach Point**, 0–1, on the master.
- **Display and checks:**
  - **Continuity Check** with its type;
  - **Enable Proxy Display**: a green ghost of the original hull;
  - **Diagnostic Feedback**: the smallest and largest Position, Tangent, Curvature and Torsion
    deviations, and the start and end angles;
  - dashed edges where the current constraints cannot be met.
- **Buttons.** Reset, Update. **Revert** removes the history and restores the original.
  **Accept / Restore** checkpoint a series of aligns.

**Align 2008** (legacy) [doc]
([page](https://help.autodesk.com/cloudhelp/2014/ENU/Alias/files/ObjectEditAlignAlign2008.htm)) keeps
options the 2009 tool dropped:

- **Modify**: First, Second or Both (meeting in the middle).
- **Intersection**: Fixed (the end points stay, tangent CVs move) or Free (the reverse).
- **Alignment types**: proportional, by project, colinear (hulls parallel to the target's),
  directional, perpendicular to edge.
- **Lock Position CV Row** and **Lock Tangent CV Row**.
- **Partial Joins**: T-Join, or General with Attach Hardness. Hard inserts multiple knots.

**Symmetry Plane Align** [doc]
([page](https://help.autodesk.com/cloudhelp/2014/ENU/Alias/files/ObjectEditAlignSymmetryPlaneAlign.htm)):
makes a surface G0 and G1 (or G2) with its mirror half. Project For Position is on by default.

There is no separate curve Align or "Multi-align" in the help: curves go through Align itself, and
Accept chains aligns.

### 4.3 Project, Intersect, Trim, Stitch, Extend

- **Project** (Surface Edit › Create CurvesOnSurface) [doc]
  ([page](https://help.autodesk.com/cloudhelp/2014/ENU/Alias/files/SurfaceEditCreateCurvesOnSurfaceProject.htm)):
  - Create curves on the surface, or free curves;
  - Curve fit with degree and spans;
  - Match original: projects the original edit points, so the span count stays similar;
  - Vector Options (§2.3);
  - history.
- **Intersect** [doc]
  ([page](https://help.autodesk.com/cloudhelp/2014/ENU/Alias/files/SurfaceEditCreateCurvesOnSurfaceIntersec.htm)):
  surface with surface or with a plane, making curves on the first surface or on both, with
  history.
- **Trim Surface** [doc]
  ([page](https://help.autodesk.com/cloudhelp/2014/ENU/Alias/files/SurfaceEditTrimTrimsurface.htm)):
  - Picking: pick the surface and the curves (or with **3D Trimming**, curves off the surface,
    by Project or Intersect).
  - Regions: click region markers, then **Keep** or **Discard**, or **Divide**. Divide cuts each
    picked region into its own trimmed surface.
  - **Show Intersections** marks where curves meet (green) or dangle (yellow, red).
  - In 2026 trim stages became editable, and a Curve Trim tool with history arrived.
- **Untrim** [doc]: Untrim Stages Last or All. Trims are kept as a stack of stages.
- **Trim Convert** [doc]
  ([page](https://help.autodesk.com/cloudhelp/2014/ENU/Alias/files/SurfaceEditTrimTromconvert.htm)):
  a four-sided trimmed region becomes an untrimmed surface. Options: U and V degree and spans,
  Switch U/V, Show Surface and Edge Deviations, Keep Originals.
- **Shell Stitch / Unstitch** [doc]
  ([page](https://help.autodesk.com/cloudhelp/2014/ENU/Alias/files/SurfaceEditStitchShellstitch.htm)):
  - Stitch joins surfaces into a shell within a gap tolerance (0.0001–1, or the preferences'
    Maximum Gap Distance).
  - Detach periodic surfaces; detach single-curve boundaries (for CAD export).
  - Keep originals is on by default, because unstitching may not give back the originals exactly.
  - Shell booleans follow.
- **Extend** (Object Edit) [doc]
  ([page](https://help.autodesk.com/cloudhelp/2014/ENU/Alias/files/ObjectEditExtend.htm)):
  - **Linear** (straight on; a curvature break) or **Extrapolate** (keeps the rate of change of
    curvature, adds no edit points);
  - Merge (on);
  - a distance or a percentage;
  - Chain Select.

### 4.4 CVs and structure

**Transform CV** (Control Panel) [doc]
([page](https://help.autodesk.com/cloudhelp/2016/ENU/Alias-Reference/files/GUID-521240C9-D869-44CB-8E81-17FC8992FE20.htm)):

- **Operations:** Move, Rotate, Scale, Non-proportional scale, Pivot and Prop mod.
- **Modes:**
  - **XYZ**: world;
  - **SLIDE**: along the CV's own hull;
  - **NUV**: the left button moves along the normal, the middle along U, the right along V;
  - **PROJ**: along a hull line or vector, or held to a reference plane;
  - **PARA**: parallel to a vector or hull line;
  - **VIEW**: the screen plane;
  - **ROT** and **NPSCL**: Prop mod only.
- **CV or HULL picking.** A hull pick takes the whole row.
- **Locks and sensitivity.** Lock X, Y, Z. Mouse sensitivity 1–100. Step size, and Lock step size
  (arrow keys).
- **Proxy Display**: the original hull as a ghost.

**Proportional Mod** [doc]
([page](https://help.autodesk.com/cloudhelp/2014/ENU/Alias/files/TransformModifyProportionalmod.htm)):

- **Falloff.** In U and V, −5 to 5. 0 is uniform, positive values damp distant CVs, and negative
  values push them the other way.
- **Reach.** **Preceding # / Succeeding #** count CVs along U and V. Falloff is counted in rows,
  not 3D distance.
- **Later versions.** 2026 replaced it with Soft Proportional Modification, which colors the
  falloff and has a volumetric mode.

**Move CV Normal**: CVs along the normal or tangentially [doc].

**Insert** (Object Edit) [doc]
([page](https://help.autodesk.com/cloudhelp/2015/ENU/Alias-Reference/files/ObjectEditInsert.htm)):
one more span at a picked parameter, with a green preview of the new hull.

**Rebuild Curve / Rebuild Surface** [doc]
([curve](https://help.autodesk.com/cloudhelp/2015/ENU/Alias-Reference/files/CurveEditRebuildcurve.htm),
[surface](https://help.autodesk.com/cloudhelp/2014/ENU/Alias/files/SurfaceEditReuildsurface.htm)).
Types:

- **Curvature**: spans added where curvature is high, with Max Spans;
- **Reduce Spans**: within a tolerance;
- **Del Multi Knots**;
- **Uniform Knots**, with a CV count and a degree;
- **Match Knots**: to another object;
- **Non-rational**: surfaces only.

Rebuild Surface works in U, V or both, at degree 1–9. **MixMax Display** shows the deviation, and
the largest deviation is reported. The Modeling Control Panel's Rebuild fields change the degree
and spans of several objects at once, with the deviation to accept or cancel
([page](https://help.autodesk.com/cloudhelp/2016/ENU/Alias-Reference/files/GUID-F5A5E4DB-683E-4FAE-8869-3A3718FF57A9.htm)).

**Curve tools:**

- **Stretch** [doc]
  ([page](https://help.autodesk.com/cloudhelp/2014/ENU/Alias/files/CurveEditModifyStretch.htm)):
  reshapes a curve with handles on it while keeping its CV layout. Up to degree + 1 handles.
  Parameter Locked or Floating.
- **Attach** [doc]: Blend (both ends move to meet, Blend Bias) or Connect (a straight span with
  multiple knots).
- **Detach** and **Close** (Preserve Shape) [doc].
- **Duplicate Curve** [doc]: a free curve from an isoparm, an edge, a trim edge or a curve on a
  surface.

### 4.5 Diagnostics

- **Diagnostic Shading** [doc]
  ([2023 index](https://help.autodesk.com/cloudhelp/2023/ENU/Alias-Reference/files/Menus/Object-Display-menu/GUID-9827166C-1FEC-4C74-A41D-DA808D5EA511.html)).
  Modes:
  - **Curvature Evaluation**: U, V, X, Y, Z, Mean, Gaussian, Principal Min, Principal Max, with a
    radius ramp and min/max radius limits;
  - **Zebra**: horizontal or vertical, Lock Texture or camera-projected, repeats, thickness, light
    linked to the camera or set by azimuth and elevation;
  - **Isophote**: count, thickness, sharpness, camera vector or fixed light;
  - **Light Tunnel**;
  - **Iso Angle**;
  - **Draft Angle**;
  - **Deviation Map**.

  **Layer** overlays curvature or zebra on another shader.
- **Evaluate › Surface Continuity** [doc]
  ([page](https://help.autodesk.com/cloudhelp/2014/ENU/Alias/files/EvaluateContinuitySurfacecontinuity.htm)):
  - Find Positional, Tangent or Curvature breaks, checked by arc length or a number per span.
  - The locator stays live. Check Interior looks at multiple-knot isoparms inside the surface.
  - Labels: the largest in red, the smallest in blue.
  - Show Comb draws the gap, tangent and curvature breaks as combs.
  - Curvature is checked relative to the boundary, square to it.
- **Curve Continuity** [doc]: Simple (a green or red circle) or full P/T/C display.
- **Locators › Curve Curvature** [doc]
  ([page](https://help.autodesk.com/cloudhelp/2014/ENU/Alias/files/LocatorsCurvecurvature.htm)):
  - a live comb plotting curvature, radius or unit normal;
  - Surface Relative (along the surface normal for curves on a surface);
  - auto or log scale; samples with a drag handle;
  - Comb, Outline or both; torsion quills;
  - **inflection points** as red arrows;
  - a radius limit: green quills inside the range, rose outside;
  - min and max radius (2025.1: computed apart from the comb's density).
- **Evaluate › Highlights** [doc]: highlight lines as real curves on the surface, from parallel
  lights.
- **Dynamic Section** [doc]: live section planes with curvature combs.
- **Deviation Map** [doc]: ramp distance, acceptable distance, bands.
- **Gap Check** (2025): gaps along a guide curve, with a min/max comb.

### 4.6 Surfaces from curves

- **Square** (four boundaries) [doc]
  ([page](https://help.autodesk.com/cloudhelp/2014/ENU/Alias/files/SurfacesBoundarySurfacesSquare.htm)):
  - **Continuity per edge**: Free, G0, G1, G2, Implied Tangent, Implied Curvature, or Tangent Angle
    with a handle.
  - **Rebuild per edge.**
  - **Blend Type**: Linear or Cubic. 1-3 and 2-4 Boundary Blend (the middle of each pair's
    influence) and Influence.
  - **Colinear Options**: isoparms line up with the neighbors'.
  - Explicit Control; Max. New Spans, Insert at Midpoint.
  - Boundary Labels and Continuity Check.
- **Rail Surface** [doc]
  ([page](https://help.autodesk.com/cloudhelp/2014/ENU/Alias/files/SurfacesSweptsurfacesRailSurface.htm)):
  - **Generation curves**: 1, 2 (Gen. Blend Value) or more. **Rail curves**: 1 or 2.
  - **Continuity per edge** as Square's. Rebuild per curve.
  - **Sweep Mode**: Proportional, Spine, View, Parallel, Natural.
  - **Sweep Pivot** (one rail).
  - **Transform Control** (two rails): Rotate No Trim, Rotate & Trim, Non-Prop Scale, Scale.
  - Fixed Curve. Curve Segments (start and end picked on the curves). Colinear Options.
  - Explicit Control.
- **Skin** [doc]
  ([page](https://help.autodesk.com/cloudhelp/2014/ENU/Alias/files/GUID-3CC0C09F-BABF-4463-B7DD-ADBD27C617E8.htm)):
  - a loft through curve sets, open or closed;
  - Proportional Crown;
  - U and V degree 1–7;
  - Flow Control (Connect Ends by default), Modify Range;
  - Surface Type, Bézier.
- **Profile** [doc]
  ([page](https://help.autodesk.com/cloudhelp/2014/ENU/Alias/files/GUID-F7BB3BC4-43A9-4141-8E66-5821C2453BF2.htm)):
  - rails with profiles placed on them;
  - Orientation: Parallel, Radial or Surface Normal;
  - Transition: Linear, Local, Global or Limited (no overshoot);
  - Match Parameterization.
- **N-sided** [doc]
  ([page](https://help.autodesk.com/cloudhelp/2014/ENU/Alias/files/SurfacesBoundarysurfacesNsided.htm)):
  - a trimmed patch over N boundaries;
  - per edge Free, Position (the default), Tangent or Curvature;
  - trim curves Linear or Cubic;
  - surface degree 1–7, 3 by default;
  - **Center Adjust** (height and weight); Smoothing Weight; Max. New Spans;
  - per-edge continuity feedback.
- **Set Planar** [doc]: a trimmed planar fill of closed curves.
- **Multi-Surface Draft** [doc]
  ([page](https://help.autodesk.com/cloudhelp/2014/ENU/Alias/files/SurfacesDraftsurfacesMultisurfacedraft.htm)):
  - draft or normal walls from edges or curves, at an angle and length;
  - Double Sided; Intersect Flanges;
  - V degree 1.

## 5. Plasticity, xNURBS, Parasolid and Rhino

### 5.1 Plasticity

**Kernel.** Plasticity began on C3D, as the open-source repository's `lib/c3d` shows. It moved to
Parasolid. Wikipedia and Digital Production (October 2023) both say it runs on Parasolid
([Wikipedia](https://en.wikipedia.org/wiki/Plasticity_(software)),
[Digital Production](https://digitalproduction.com/2023/10/04/plasticity-3d-cad-for-artists/)), and
Nick Kallen wrote in March 2022 that he was considering the switch
([post](https://x.com/nk/status/1507667984357203971)) [comm]. luce-cad's CAD-MODELING-STUDY dates
the move "around 2024–2025". The sources above put it in 2022–23 [unverified, exact date].

**xNURBS.** It is a separate surfacing library on top of Parasolid. Since 2024.1 it is in the Studio
tier only (xNURBS, Square, Align, Rebuild Face Explicit)
([licenses](https://doc.plasticity.xyz/getting-started/license-types-and-features)) [doc].

**The surfacing commands** (doc.plasticity.xyz, the page named after each) [doc]:

- **Fillet** (`solid/fillet-shell`):
  - Drag the yellow dot one way for a fillet, the other way for a chamfer.
  - **Shape**: Conic, Chordal (constant chord), G2, Full (full round).
  - **Tension** (2025.2), for every shape but Full.
  - **V** adds a variable-radius point. **L** adds up to two limit points that stop the fillet,
    clicked again to flip.
  - Y-Blend "Attempt" for three fillets at a corner. Add tangent edges.
  - Chamfer shapes: Offset or Apex.
  - **Remove Fillets From Shell**: by maximum radius and convexity, a Parasolid-style defeature.
- **Bridge Curve** (`sketch/bridge-curve`):
  - Ends picked on curves, edges or faces, each with a parameter and a sense.
  - Per end G0–G3, and three **tension tiers** per end: tension 1 moves CVs 1–3, tension 2 CVs 2–3,
    tension 3 CV 3.
  - 2025.2: the tensions are set by dragging the visible CVs, and a comb shows.
  - Trim.
- **Bridge Surface**: between two sheets, or two crossing surfaces. Width, Tension, Shape (G2 or
  Chamfer), Trim walls (Both, Short, Long, None).
- **Loft**:
  - Profiles, then guides.
  - Per end G0–G2 by Tab or the black circles. Per edge tension.
  - Limit points; Loop.
  - **Simplify** (on: planar trimmed patches; off: a consistent CV layout).
  - Guides that miss a profile show a red dot.
- **Sweep**: twist, scale at the end; alignment Parallel or Normal; guides by Point, Chord or Curve;
  corner Mitre or Round.
- **Patch** (Parasolid's fill, not xNURBS):
  - Inputs: closed curves, edge holes, guide curves (each needs an isoparm where it touches), or
    every hole at once to close a solid.
  - **Per-edge** Planar, G0, G1 or G2.
  - Faces: Single, Minimal or Quality.
  - Method: Trim to hole or Trim to sheet.
- **xNURBS** (`solid/xnurbs`):
  - Inputs: boundary edges, and open guide curves that need not touch the boundary.
  - Continuity G0, G1 or G2. The page shows one setting; whether the per-edge circles apply here is
    [unverified].
  - **Quad sided**: an untrimmed four-sided result.
  - **Flatness** (0.95–1 for quads). **Tension** 0.1–1 (quads).
  - **Boundary** flow: Natural, Normal (isocurves square to the boundary), Next, Adjacent (V
    isocurves follow neighboring trimmed edges).
  - Quality Auto, High or Max. Satisfy tolerances.
  - An N-sided result is one trimmed surface.
- **Square** (xNURBS, Studio):
  - Continuity Free, G0, G1 or G2. Flatness. **Per-edge tension** (2025.2).
  - Degree and Spans in U and V. Boundary flow as xNURBS's.
  - **Weight**: lower relaxes the boundary for better reflections; higher enforces it.
  - Analysis.
  - It also serves as Loft, Sweep, Patch and **Refit Surfaces**: a trimmed four-sided face rebuilt
    with spans that follow its flow.
- **Align** (xNURBS, Studio, 2025.2; `solid/align-surface`). Plasticity's match surface:
  - Per edge G0–G2. Tension.
  - **Blend extra rows**, and **Input shape influence**.
  - **Partial start / end**.
  - Degree and Spans; Boundary flow.
  - Analysis with per-level comb scales.
  - Several neighboring surfaces at once.
  - B-spline surfaces only: analytic ones need Rebuild or Raise Degree first.
  - 2026.1 added curve-to-curve and vertex-to-vertex G0–G3.
- **Match Face**: not continuity. It replaces faces with a target surface (Parasolid's replace),
  with Grow Moving, Fixed or None.
- **Project Curve** (I): Normal or Vector, bidirectional, hide occluded, screen space.
- **Imprint Curve** (Shift+I): the same, plus **Completion**: None, Edge (extend until it meets
  edges) or Boundary.
- **Cut** (by a curve or a face), **Untrim** (Keep edges imprints the old trims), and **Extend
  Sheet**:
  - Shape: Natural, Linear, Soft (G2), Reflective;
  - limit to a target;
  - the result stays one sheet.
- **Offset Face** (Push Face):
  - **Angle Adjacent** tilts the neighbors.
  - Grow Moving, Fixed or None.
  - **Dependent Offset** runs until the face meets a picked one.
- **Thicken, Hollow, Draft Face.** Draft Face has methods Isocline, Curve, Surface, Offset and
  Normal: Parasolid's taper methods.
- **Join Sheets** and **Unjoin**.
- **Control points:**
  - Mode 1 shows the CVs of curves and faces, trimmed or not. A trimmed face is edited through its
    hidden "nominal surface".
  - **Move Control Point**: falloff None, All or Selected, measured in **UV hull distance**;
    mirror across the C-plane.
  - **Slide** (Shift+G) along the hull: U, V, or N for the normal.
  - Alt-hover selects a hull row (2025.2).
  - **Isoparam** (Ctrl+R): knot insertion, U or V, a count, and Subdivide to split the face.
  - **Raise Surface Degree** (also turns analytic surfaces into splines).
  - **Rebuild Face**: Explicit (degree, spans, extend, Shrink) or by tolerance. Rebuild Edge.
  - **Rebuild Curve**: Refit, Points, or Explicit (degree, spans, Weight). Insert Knot. Raise Curve
    Degree.
- **Analysis.** Measure Continuity (live G0–G2 between edge pairs, comb scales, maxima), curvature
  combs, isophote and draft shaders.

### 5.2 xNURBS

**Who and what** [comm]:

- **The team.** Its people "previously held senior R&D positions at PTC" and spent over a decade
  on "variational surfacing" ([about](https://www.xnurbs.com/about-us/)).
- **The kernel.** `xnkernel.dll` is licensed only to software vendors
  ([product](https://www.xnurbs.com/product/)). End users get it as a Rhino plug-in, a SolidWorks
  add-in, or inside Plasticity Studio.
- **No Fusion use found.** A 2020 forum thread proposed an Alias module, with no visible outcome.

**The method** [comm]:

- **The claim.** "An energy-minimization method to generate the smoothest NURBS surface among all
  possible solutions", explained with a bending batten
  ([home](https://www.xnurbs.com/), [Rhino blog](https://blog.rhino3d.com/2022/01/xnurbs-rhino-plugin-v52-released.html)).
- **The constraints.** Curves or points anywhere, each with contact, tangent or curvature
  continuity ([forum, 2017](https://discourse.mcneel.com/t/xnurbs-releases-a-ground-breaking-nurbs-software/49049)).
- **Nothing published.** No paper or patent was found, under PTC or otherwise.
- **Our reading** [unverified]. A quadratic bending energy over a fixed NURBS net, with G0, G1 and
  G2 conditions as constraints, refined where they fail, then trimmed to the boundary for N sides.
  This is the published family below.

**Features by version** [comm] ([what's new](https://www.xnurbs.com/whats-new/)):

- **Per-edge continuity.** A demo sets one edge G1 and the others G0.
- **Rhino plug-in 5.2.** Boundary curves trimmed automatically.
- **7.0 (2025):**
  - XNurbsSquare, with a user's degree and spans;
  - interior points and curves on four-sided surfaces;
  - two-, three- and four-sided and L-shaped domains;
  - Tension; Align to Next;
  - conflicting constraints shown on the model.

**How others answered** [comm]:

- **Rhino 9 WIP Patch, reimplemented** (February 2025,
  [forum](https://discourse.mcneel.com/t/rhino-wip-feature-patch-re-implemented/198660)):
  - "a thin membrane with elasticity and internal strain under bending";
  - per-edge constraints I, G0, G1 or G2;
  - Stiffness; degree 3–5; U and V spans; a starting surface;
  - position, normal and internal tolerances, with **Refine** adding CV lines where a constraint
    fails;
  - domains Untrimmed, MultiBlend (several quads), Projected or Molded.
- **Rhino 9 MultiSidedPatch**
  ([forum](https://discourse.mcneel.com/t/rhino-9-feature-multi-sided-surface-patches/194768)):
  - a transfinite patch: ribbons per side blended by generalized barycentric coordinates;
  - Fullness; G1 to edges, no G2 yet.
- **Benchmark.** A 2025 paper (Li and Li, "An Improved N-Sided Filling Algorithm Based on GNURBS
  Surface", J. CAD & CG) reports about 70% fewer control points than xNURBS for the same error.

**Background.**

- **Coons** (1967) and **Gordon** (1971): transfinite interpolation of four curves, and of a curve
  network.
- **Gregory** (1974), **Chiyokura & Kimura** (SIGGRAPH 1983), **Charrot & Gregory** (CAGD 1984):
  G1 patches over three, four and five sides.
- **Variational surfaces.** Celniker & Gossard (SIGGRAPH 1991), Welch & Witkin "Variational surface
  modeling" (SIGGRAPH 1992), Moreton & Séquin (SIGGRAPH 1992), Greiner "Variational design and
  fairing of spline surfaces" (Eurographics 1994): minimize ∫|S_uu|² + 2|S_uv|² + |S_vv|² under
  linear constraints.
- **Transfinite N-sided patches.** Várady, Salvi and Rockwood (CAD 2011, CAGD 2014); the
  Generalized Bézier patch (CGF 2016); Midpoint patches (2020); the survey "Genuine multi-sided
  parametric surface patches" (CAGD 2024).

### 5.3 Parasolid

From the V35.0 Functional Description, chapters 46, 48, 62–78 and 16–17 [doc].

**Three blend families** (overview chapter 11):

- edge blends, which replace edges;
- face-face blends between two wall sets, which need not touch or be in one body;
- three-face blends, full rounds whose middle wall is consumed.

**Edge blends** (chapters 74–76):

- **Set, then fix.** Blends are first set on edges as attributes, then **fixed** together in one
  call. Parasolid resolves how they interact, so the caller never chooses an order.
- **Three types:**
  - constant rolling ball: circular or curvature-continuous section;
  - chamfer: face-offset, or apex-range (measured from where the walls' tangents meet);
  - **variable rolling ball**: radii at two or more positions, circular, conic or G2 section.
- **The blend surface is procedural**:
  R(u,v) = C(u) + r X(u) cos(v a(u)) + r Y(u) sin(v a(u)), C being the ball's center (the spine).
  It is simplified to a cylinder or torus where it can be.
- **Section shape:**
  - **conic** by default: a circle when both sizes are equal, else a least-tension ellipse; with
    **rho**, any conic;
  - **G2**: matches each wall's curvature at the contact;
  - **chamfer**.
- **Rho can be given three ways:**
  - absolute: 0.5 parabolic, below elliptic, above hyperbolic;
  - relative to the angle subtended;
  - as the radius of curvature at the section's middle.

  Clamp indices hold the rate of change at given positions.
- **Fix-time options:**
  - **Cliff edges**: the blend is tangent to one wall and runs along an edge of the other.
  - **Y-blends**: two blends of different convexity meeting at a vertex of three or more edges.
  - **Setbacks**: per edge distances from a vertex, the gap patched, with or without collar faces.
  - **Vertex blends**: roll past sharp edges of the other convexity.
  - **Round order** at mixed-convexity corners: concave first, convex first, minority or majority
    convexity.
  - **Limits**: at a vertex, at a point on an edge (the plane through it caps the blend), or where
    blends start to overlap.
  - **Caps**: faces, planes or sheets.
  - **Limit topologies**: trim along the blend's isoparameter where it crosses faces, with a
    blend-like patch between limits.
  - **Transfer**: topology a blend covers, such as a hole, is moved into the blend face.
  - **inside_tight**: walls tighter than the radius.
  - **Previews**: output the blend as a separate sheet, always or on failure. `suggest_limit`
    returns where to stop a failing blend.
  - **Tracking** of which walls each blend face came from.
- **Overflow** (chapter 76), where a blend runs off a face next to its edge:
  - **smooth**: the blend continues on the next face; all bounding edges must be smooth;
  - **cliff**: cliff-edge blends round the overflow region;
  - **cliff end**: a cliff-edge blend at the chain's end;
  - **notch**: the blend is unchanged and the neighbors are extended or trimmed.

  The default order is smooth, then cliff, then notch. A table of defaults by convexity and edge
  smoothness is given in the chapter. SolidWorks' "Keep edge / Keep surface" overflow choice
  probably maps onto these [unverified].

**Face-face blends** (chapter 77) are built from three independent choices:

- **Section plane:**
  - rolling ball (square to the walls);
  - **disc** (square to a given spine);
  - **isoparameter** (along the left wall's isocurves, for turbine blades).
- **Size or boundary:**
  - radius, or two ranges;
  - range laws along a spine;
  - **constant width** (the chord between the contacts, with a ratio);
  - variable width;
  - apex-range chamfers;
  - or **holdlines**: a tangent holdline gives one boundary and the blend's radius varies to meet
    it; a conic holdline sets one side's range; cliff edges; inverted holdlines.
- **Section shape:**
  - conic with rho;
  - chamfer;
  - **G2**, with depth (0 at the chord, 1 at the walls' tangent intersection) and skew (0 at the
    left wall, 1 at the right), or a **softness** (higher is flatter and deeper, lower is "like a
    chamfer with rounded edges").

Further options:

- **Trim** to the walls, none, long or short.
- **Walls**: untrimmed, both trimmed, attached (two bodies united) or made a solid.
- **Limit planes**, **caps**, and a **run-out angle** that stops the blend where the walls become
  too shallow.
- **Help points** choose among several solutions.
- **Ribs**: section curves, output for an outside surfacer when the blend fails.
- **prevent_sharp** smooths kinks from G2 breaks in the walls.
- **user_surface**: you supply the blend's surface.

**Three-face blends** (chapter 78): walls up to 260° apart, against 180° for face-face blends.

**Recognition and editing** (chapters 62–64):

- **Finding blends.** `PK_FACE_identify_blends` finds constant rolling-ball blends and blend-like
  B-surfaces.
- **Removing blends.** `PK_FACE_delete_blends` removes them and heals, knowing what blending
  changed. Delete with **heal** caps, shrinks or grows the neighbors.
- **Editing blends.** A blend's radius is changed through `PK_FACE_change`, which rebuilds blends
  when their walls move ("reblend"). v38 extends this to constant-width blends with overflows
  ([v38](https://blogs.sw.siemens.com/plm-components/whats-new-in-parasolid-v-38-0/)).

**Local operations** (chapters 58–72):

- **One growth rule.** Offset, taper, transform, hollow, thicken and face change share it:
  moving faces grow, fixed faces grow, caps, automatic, or fail.
- **Offset**: G1 and exact, simplified to analytic surfaces where possible. Optional rolling-ball
  blends on convex offset edges.
- **Taper**: Isocline (molds), Curve, Surface, Offset, Normal; step tapers; parting edges.
- **Replace surfaces**, **replace with sheet**.
- **PK_FACE_cover**: one fitted B-surface over a smooth face set.
- **Fill hole** (`PK_BODY_fill_hole`):
  - methods: create patch, trim a supplied sheet to the hole, trim to sheet, extend the neighbors;
  - G1 or **G2** (G2 needs the quality setting);
  - per-edge relaxation (non-smooth edges, non-G2 edges);
  - supporting wires, or a point the patch passes through;
  - single, multiple or minimal patch topology;
  - prefer planes or analytic surfaces.
- **PK_FACE_change**: offset (or dependent offset, tracking a reference face), taper, transform,
  replace, reblend, bend, patch, deform and radiate, in one call.
- **Extension** (`PK_BODY_extend`): linear (the default; may break G2), **soft** (C2 at the
  boundary, tending to linear) or **reflective** (C2, mirroring the shape).

**Sheets and tolerance:**

- **Sewing** (`PK_BODY_sew_bodies`): sheets joined within a gap bound, run incrementally with
  growing bounds. Knitting is separate.
- **Tolerant modeling** (chapter 16): a precision per edge (a tube) and per vertex (a sphere).
  Tolerant edges carry curves in each face's parameter space (SP-curves). `PK_EDGE_repair` sets
  them.
- **B-geometry tools**: raise and lower degree, add and remove knots, clamp, reparameterize,
  extend; a constrained B-surface through points and normals; lofting; isoclines.
- **Rules for a valid B-surface face**: no zero first partials except at legal degeneracies, no
  self-intersection, no cusps except at knot lines.

### 5.4 Rhino 8

`docs.mcneel.com/rhino/8/help/en-us/commands/<command>.htm` [doc].

- **MatchSrf:**
  - Continuity: Position, Tangency or Curvature (the default).
  - **Preserve other end**: None, Position (the default), Tangency or Curvature. The structure
    changes so the opposite edge does not move.
  - **Average surfaces**: both move to meet.
  - **Match edges by closest points.**
  - **Refine match**: adds knots until within a distance, an angle and a curvature percentage.
  - **Isocurve direction**: Automatic, Preserve, Match target, or Perpendicular to the target edge.
  - Multiple matches. Match to a curve pulled onto a surface.
- **Match** (curves): Position, Tangency or Curvature; Preserve other end; perpendicular to an edge;
  average; join; merge.
- **BlendSrf:**
  - Per end Position to G4.
  - Two bulge sliders with a lock.
  - **Add Shapes** (section lines) and Remove Shapes; Straighten with an angle threshold.
  - Interior shapes, or Refine.
  - Planar sections parallel to a direction. **Same height** for a varying gap.
  - Alt turns a shape; Shift edits both sides symmetrically. Edit reopens a blend.
- **BlendCrv**: per end Position to G4; picked points or curve ends; perpendicular to edges; Edit;
  Show curvature.
- **NetworkSrf**: tolerances for edge curves, interior curves and angle; per edge Loose, Position,
  Tangency or Curvature.
- **Patch** (before Rhino 9):
  - a surface fitted to sampled boundary and interior points, with a spring stiffness, over a
    starting plane or surface;
  - U and V spans;
  - Adjust tangency (G1 to surface edges);
  - automatic trim; Preserve edges.
- **Sweep1, Sweep2:**
  - frames Freeform, Roadlike or Align with surface;
  - Rebuild or Refit;
  - Preserve first and last sections; **Maintain height**;
  - rail edge continuity Position, Tangency or Curvature (when the rails are surface edges).
- **EdgeSrf**: from two to four curves or edges.
- **Fillets and chamfers:**
  - **FilletEdge**: rail type DistFromEdge, RollingBall or DistBetweenRails; handles add radius
    points.
  - **FilletSrf**: Arc, Deformable (degree 3–5, tangent and bulge) or G2; trim and extend.
  - **VariableFilletSrf**, **ChamferSrf**.
- **Project**: along CPlane Z, the view or a custom direction; Loose. **Pull**: along the normal
  (closest point).
- **Trimming:**
  - **Trim**, **Split** (at an isocurve, with Shrink), **Untrim**.
  - **ShrinkTrimmedSrf**: drops CVs beyond the trims; the shape is unchanged.
  - **ExtendSrf**: Smooth or Line; Merge.
- **Structure:**
  - **Rebuild**: point counts and degree up to 11. Retrim. **Calculate** colors the deviation
    green, yellow or red.
  - **RebuildUV**: one direction.
  - **RebuildCrvNonUniform**.
  - **ChangeDegree**: Deformable. The exact wording of what changes the shape was not confirmed
    [unverified].
  - **InsertKnot**, **RemoveKnot**, **RemoveMultiKnot**; **InsertControlPoint** (changes the shape);
    **FitCrv**.
- **Point editing:**
  - **MoveUVN**: U, V and N sliders with a scale; moves along the isocurves' tangents, along the
    control polygon, or along extensions; symmetry and smoothing in U and V.
  - **SoftEditSrf**: falloff distances in U and V, Fix edges, direction constraints.
  - Gumball **Drag Strength** for fine moves.
- **Analysis:**
  - **CurvatureAnalysis**: Gaussian, Mean, Min radius, Max radius, with auto or max range.
  - **CurvatureGraph**: combs on curves and on surfaces' isocurves in U and V, scale, density.
  - **Zebra**; **EMap**.

## 6. Algorithms we would need

Each is a luce-cad kernel in Base (`.lucb`): luced-3d calls it and draws what it returns.

### 6.1 Matching continuity across an edge by CV rows (Align, MatchSrf)

Let the input surface S meet the master M along S's edge u = 0. S's CVs in rows P₀, P₁, P₂, P₃ …
(row 0 on the edge). At a clamped end of degree p with knots t, the derivatives across the edge are
fixed by the first rows alone:

- S_u = p / (t_{p+1} − t₁) · (P₁ − P₀) (as B-spline curves along the edge);
- S_uu takes P₀ to P₂;
- S_uuu takes P₀ to P₃.

So G0 sets row 0, G1 row 1, G2 row 2 and G3 row 3. Each needs the rows below it.

**Geometric continuity.** Continuity of order k means that S's derivatives across the edge equal
M's after some reparameterization s = φ(u) with φ' = α > 0, φ'' = β, φ''' = γ. By the chain rule
(Faà di Bruno), with D the cross-boundary derivatives of M:

- G1: S_u = α D₁ + τ T;
- G2: S_uu = α² D₂ + β D₁ + (terms along T);
- G3: S_uuu = α³ D₃ + 3αβ D₂ + γ D₁ + (terms along T).

Here T is the edge's tangent and τ the skew.

- **The free parameters are Alias's sliders.** α, β and γ are Align's Tangent Scale, Curvature
  Scale and G3 Scale. The skew τ is its Skew option. AutoScale keeps β and γ in proportion to α.
  Fixing α to the master's own spacing is Tangent Balance.
- **Each row in turn.** Given them, each row is solved in turn, a linear back-substitution: P₁ from
  S_u and P₀, P₂ from S_uu, P₀ and P₁, and so on.
- **Rhino's MatchSrf** is the same at G0–G2.
- **Vector mode** restricts each row's motion to a direction. Each row is then a least-squares
  solve, still linear.

**When it is exact.**

- **The conditions.** The match is exact when M's cross-boundary derivative fields along the edge
  lie in the space of S's B-splines along the edge, and α, β and γ are constants.
- **Making the spaces match.** For a natural (untrimmed) master edge, this holds after S is raised
  to M's degree along the edge and M's knots are inserted into S. That is Alias's Explicit Control
  off.
- **Position Influence.** At 0, S's own parameterization is kept, and the master's fields are
  fitted in S's space by least squares. At 1, S takes the master's knots.
- **Approximate cases.** A trimmed master edge, a curve on a surface, or α varying along the edge
  (Alias's Starting and Ending scales) cannot be exact. The rows are then fitted by least squares to
  sampled targets. Refine (Rhino) inserts knots where a check fails, until the G0 distance, G1
  angle, G2 curvature difference and G3 difference are within tolerance. Max. New Spans caps it.

**The rest of Align's options:**

- **Extra CV Rows / Blend Factor.** The change to the last constrained row is carried to the next k
  rows with weights w(i/k): exponential, linear or growing, by the factor. The constrained rows
  themselves are untouched.
- **Partial.** Knots are inserted (to full multiplicity) at the partial range's ends on S's edge.
  The match applies inside the range and is tapered to zero over the extra rows outside it.
- **Two masters** (both ends, or opposite edges). Solve both when the row sets do not overlap; the
  surface needs at least 2(k+1) rows across, eight for G3 at both ends. With degree 5 that is three
  spans. Fewer rows are refused with the number needed, or spans are inserted when Explicit Control
  is off.
- **Modify Both** (Align 2008, Rhino's Average). Both surfaces move toward a shared middle: P₀ is
  averaged, then each side's rows are solved against the averaged field.
- **Curves.** The same with one row per end. Curve-to-surface matching uses the surface's derivative
  in the chosen cross direction: along the isoparm (U/V) or square to the edge (Rhino's
  "perpendicular").
- **Symmetry Plane Align.** The master is the mirror image of S: G1 sets row 1 square to the plane,
  and G2 sets row 2 so the mirror's curvature matches.

### 6.2 Blend curves in 3D, G0–G4

A blend curve between two ends, each on a curve, an edge or a surface:

- **CVs fixed by each end.** An end at G_k fixes k+1 CVs from the end's derivatives, as in §6.1.
  The shape parameters per end are tangent length α, curvature β, G3 γ, G4 δ.
- **Degree 5 and its spans.** The curve has 6 + (spans − 1) CVs, which must be at least the sum of
  both ends' k+1:

  | Both ends | CVs needed | Spans at degree 5 |
  |---|---|---|
  | G1 | 4 | 1 |
  | G2 | 6 | 1 |
  | G3 | 8 | 3 |
  | G4 | 10 | 5 |
  | G3 and G1 | 6 | 1 |

  Alias builds degree 5 by default (§4.1), and so does our sketch Blend Curve. G4 needs five
  spans at degree 5. Alias and Rhino reach it at degree 7 or 9 [comm].
- **CVs left free.** Free interior CVs minimize ∫|C'''|² with the ends fixed: one linear solve.
- **Default shape parameters.** Chosen from the chord length: Alias's Relax and Tight, and
  Plasticity's tensions, are presets of α and β. Plasticity's three tension tiers per end move CV
  groups 1–3, 2–3 and 3.
- **Ends on a surface.** The derivatives come from the cross direction chosen (Alias's Parametric
  or Geometric curvature type). Geometric uses the normal section's curvature in the plane of the
  normal and the direction.
- **Associativity.** Kept by the node: a moved end re-cooks.

The sketch's planar Blend Curve (`sketch_freeform.luc`) is the same algorithm restricted to a plane.
It should call the 3D kernel.

### 6.3 Projection and intersection onto faces

- **Along a vector d.** For samples t of a curve C, solve S(u,v) = C(t) + λd for (u, v, λ) by
  Newton. The first seed is the face's lattice (`inversion.lucb`); later seeds are the previous
  sample's solution.
  - **Several hits.** Keep the nearest along d, or both ways (Plasticity's Bidirectional), or every
    sheet (all hits).
  - **Misses.** A ray that misses the face ends a piece. A piece reaching the face's boundary ends
    on it, at the boundary curve's crossing.
  - **Sampling.** Samples are adaptive by chord error in 3D.
- **Along the normal (Pull).** The closest point (`nearest_parameters`), with the same continuation.
- **The output is a curve on the surface.** It has two forms: a uv curve in the face's parameter
  space, and a 3D curve. Both are fitted at degree 5 within tolerance (or the input's degree and
  spans, Alias's Match original), and kept consistent: the 3D curve is the surface evaluated along
  the uv curve, refitted.
- **Intersect.** `march.lucb`'s traced curves, kept with their uv parameters on both surfaces.
- **The missing link.** Today the B-rep has no pcurves. Curves on surfaces bring them, first as
  data on the new trim edges, which is what Parasolid's SP-curves are (§5.3).

### 6.4 Trim, Divide, Untrim, Trim Convert

- **Trim:**
  - The face's existing loops and the curves on it are laid out in the face's uv domain. Seams of
    periodic surfaces are cut.
  - luce-cad's sketch arrangement (`arrangement.lucb`: crossing curves split each other, smallest
    regions) is the same problem in a plane, so it is reused on uv curves.
  - Regions picked by a click (a point inverted onto the face) are kept or discarded.
  - **Divide** makes each region its own face, with the dividing curves as shared edges.
- **Untrim.** The face's trim history is a stack of stages; Last or All pops them. Without history,
  Untrim gives the natural surface (the untrimmed B-spline, or the analytic surface bounded by its
  natural range).
- **Trim Convert.** A four-sided region's boundary curves are made compatible in pairs. A Coons
  surface is fitted through them, then the interior is refined by least squares to the original
  surface (deviation reported). The result is an untrimmed B-spline face.
- **Shrink.** A surface is cut down to the trim's uv box by knot insertion at the box (Rhino's
  ShrinkTrimmedSrf); the shape does not change.

### 6.5 Stitch and tolerant edges

- **Stitching.** Boundary edges of sheet faces are matched within a gap bound: boxes in a grid,
  then the distance between edges sampled both ways. A pair within the bound becomes one edge.
  Each edge keeps a precision (a tube radius) and each vertex one (a sphere), as Parasolid's
  tolerant edges do.
- **Orientation.** Shells are oriented consistently. A closed shell becomes a solid.
- **Unstitch** splits the shared edges again.
- **Growing bounds.** Sewing in steps (Parasolid's advice) avoids matching short overlaps first.
- **What changes.** Today a model has one tolerance (§3.1). Per-edge precision is a B-rep change,
  and the booleans and the tessellator must read it.

### 6.6 Surfaces from curves

- **Compatibility first.** Curves that a surface interpolates are raised to a common degree and
  given a common knot vector by inserting each other's knots. Where the knots are too many,
  Rebuild with a tolerance comes first.
- **Square.**
  - G0: a bilinearly blended Coons patch.
  - G1 and G2: Hermite terms from each edge's neighbor, with twist compatibility at the corners
    (Gregory's correction where the corners disagree).
  - The result is then faired: §6.8's energy with the boundary rows fixed. Alias's Linear or
    Cubic blend and its Influence are the weights of the Coons terms.
- **Skin (loft).** Interpolate compatible sections in the cross direction (degree 5 when there are
  enough sections, else lower), or approximate.
- **Rail.** Sections swept along one or two rails:
  - Frames: rotation-minimizing (Proportional, Natural), along a spine, parallel, or from a view.
  - Two rails: each section moved, turned and scaled (non-proportionally under Non-Prop Scale) to
    touch both.
  - The surface: sections sampled along the rails, then fitted. With continuity to the rails'
    surfaces, the first rows are set as in §6.1.
- **Profile.** Rail plus profiles placed by parameters, with transition laws (linear, local,
  global, limited).
- **Set Planar.** The existing planar profile (`profile.lucb`), on a fitted plane, as a sheet face.
- **Extrude and Revolve of free curves** to sheets: the existing sweeps without caps.

### 6.7 Blends between surfaces

- **Freeform Blend and Bridge Surface.** The two sides are chains of curves on surfaces.
  - **Matching the sides.** Both are reparameterized to a common knot vector along the blend.
    Flow Control sets where the ends go: Edge align follows the neighbors' edges, Connect ends joins
    the ends, Free stays square.
  - **Sections.** At each station, a §6.2 section runs between the two sides' cross derivatives.
  - **Rows.** The section CVs at matching stations form rows, each fitted as a curve along the blend.
    With G3 on both sides that is eight rows: degree 5, three spans across.
  - **Shape.** Shape factors scale α; Crown pushes the middle rows along the average normal.
- **Profile Blend.** The same with interior sections forced through the profile curves: those rows
  are interpolated, not free.
- **Surface Fillet between face sets** (Parasolid's face-face blend):
  - **Spine.** The rolling ball's center is where the two offset surfaces meet. `march.lucb`
    already traces a B-spline's signed distance as a field, and offsetting it by r is that field
    minus r. Contacts come by projection.
  - **Sections.** The circular section is today's. G2 and G3 sections use the existing quintic
    shapes. Conic sections are a rational quadratic with weight ρ/(1−ρ), raised to degree 5. Bias,
    Lead and Form Factor are CV arm ratios on the quintic.
  - **Sizes.** Chord or constant width solves r along the spine for the chord.
  - **Trims.** The result is trimmed to the contact curves on both sets (§6.4), or left untrimmed.
  - **Reuse.** luce-cad's edge blends are the special case where the walls share an edge. Their
    section and row code (`blend_tools`, `row_fit`) is reused.
- **Tubular Offset.** A circular (or G2) section swept along a curve on a surface, its contacts at
  ±r along the surface, trimmed out or added.

### 6.8 Filling: variational patches (xNURBS, Rhino 9 Patch, Alias N-sided)

The unknowns are the CVs of a degree 5 B-spline net over a parameter domain.

- **The domain:**
  - four-sided (Quad or Square): the unit square, the boundaries on its sides;
  - N-sided: the boundary projected onto a best-fit plane (Projected), or a smoother map onto a
    disk (Molded); the result is trimmed by the boundary's uv image (§6.4).
- **The energy:** E = w_b ∫(|S_uu|² + 2|S_uv|² + |S_vv|²) + w_s ∫(|S_u|² + |S_v|²).
  - The first term is bending, the second membrane.
  - Plasticity's Tension and Rhino's Stiffness set w_s : w_b. Flatness adds a pull toward the
    best-fit plane.
  - The Gram matrices of B-spline derivatives are exact by Gauss quadrature per span. They are
    banded and sparse, a Base hot path.
- **Constraints**, sampled along each boundary at stations:
  - **G0**: S(uv_k) = B_k, linear.
  - **G1**: n_k · S_u = 0 and n_k · S_v = 0 at uv_k, with n_k the neighbor's normal. This is linear,
    because n_k is fixed.
  - **G2**: the normal curvature across the boundary equals the neighbor's,
    n_k · S_dd = κ_k |S_d|², with d square to the boundary. It is linearized about the current
    surface and iterated (a Gauss–Newton step).
  - **Interior curves and points** (guides, Rhino's points, Parasolid's supporting wires): G0
    constraints at their projected uv, or G1 when they carry a normal.
  - **Boundary flow** (Natural, Normal, Next, Adjacent) adds conditions on S_v's direction along
    the boundary: square to it, or along the neighboring edge.
- **The solve.** Constraints as heavily weighted least squares (Plasticity's Weight, Rhino's
  tolerances), or exact through Lagrange multipliers.
  - **Refinement.** Each pass checks the four measures of Stage 0 at the stations. Where one fails,
    knots are inserted in that span (Rhino's Refine, xNURBS's Quality), up to a span limit.
  - **Conflicts.** Constraints that conflict (G2 asked at a corner whose neighbors disagree) are
    reported where they are, as xNURBS 7 draws them.
- **Reuse.** luce-cad's corner patches (`patch_fit.lucb`) already solve a thin-plate least-squares
  problem with fixed boundary rows. That code is the start.
- **A cross-check.** A transfinite patch (a Midpoint or Generalized Bézier patch) is cheaper and
  gives a starting surface; Rhino's MultiSidedPatch is one. We use it as the first guess and as an
  independent check, not as the result.

### 6.9 Structure: the NURBS toolkit

As The NURBS Book's algorithms (Piegl and Tiller), for curves and for surfaces in U or V:

- **Knots and degree:**
  - knot insertion and refinement;
  - knot removal within a tolerance;
  - degree elevation;
  - degree reduction within a tolerance;
  - Bézier extraction (Alias's NURBS to Bezier).
- **Pieces:** split at a parameter; extract a range; join with continuity (Alias's Attach Blend);
  close (Preserve Shape).
- **Fitting and rebuilding:**
  - compatible knot vectors for a set;
  - reparameterization (uniform, chord);
  - least-squares fitting at a given degree and span count, with end rows held, so a rebuild keeps
    the continuity Align made;
  - fitting within a tolerance, adding spans where needed;
  - non-rational approximation of rational surfaces;
  - conversion of analytic faces to B-splines (Plasticity's Raise Degree).
- **Extension:**
  - natural: extrapolate the last span's polynomial (unclamp, extend, clamp again);
  - linear;
  - soft: C2, tending to linear;
  - reflective.
- **Evaluation to the third derivative.** The basis derivatives (`nurbs.lucb`) need a fourth row,
  so a G3 check needs no finite differences.
- **The degree cap.** Raised from 8 to at least 9, Alias's maximum, so STEP and IGES surfaces from
  Alias load. Rhino's 11 is the safer bound.

### 6.10 CV editing with constraints

- **NUV.** Each CV moves along the surface's normal and its U and V tangents at the CV's Greville
  point (Alias's NUV, Rhino's MoveUVN).
- **Slide.** Along the hull: the line through the CV's neighbors in U or V.
- **Hull.** A pick takes a whole row.
- **Falloff in rows.** Proportional modification counts CVs in U and V, with Alias's exponent
  (−5 to 5) and preceding and succeeding counts. Plasticity measures distance along the hull. Both
  are offered beside today's 3D soft radius.
- **Kept continuity.** A face aligned by a node keeps its continuity because the Align node
  re-cooks after any change upstream. In Edit CAD, a CV move on a row an earlier Align step
  constrained re-runs that step's row solve afterward (the owner's answer, §10).
- **Proxy.** The hull before the drag, drawn as a ghost.
- **Steps.** Step size, Drag strength (Rhino's), arrow-key nudges.

### 6.11 Measuring

At stations along an edge between faces F₁ and F₂ (or a curve's join):

- **G0**: the distance.
- **G1**: the angle between normals.
- **G2**: the normal curvatures in the direction square to the edge, compared relative to the
  larger, in percent (Alias since v13, Rhino's Refine).
- **G3**: the derivative of that curvature along the same direction, relative.

Their outputs:

- **Combs:** per measure, auto or log scaled, with min and max labels.
- **Curvature combs** on curves, edges and isoparms: curvature or radius quills, torsion,
  inflections marked, a radius band.
- **Deviation** between two surfaces or a surface and a mesh: a color map with ramp and acceptable
  distance.
- **Draft angle** shading from a pull direction.

All of it is evaluated on the exact geometry in Base, then drawn as overlay lines.

## 7. Tools in luced-3d

### 7.1 Nodes, Edit CAD steps, menus

Our split follows FUSION §4 and §7. A node is Alias's construction history: its inputs re-cook it.
An Edit CAD step is a one-off result. Every builder is both, running the same luce-cad call.

| Reference tools | Node (CAD network) | Edit CAD step, at the level | Reached by |
|---|---|---|---|
| Free curves (CV, EP), Duplicate Curve (edge, isoparm) | **Curve** (CV / fit / from edge / from isoparm) | Curves are objects of the model; Create Curve | Create menu; right-click on an edge: Duplicate as curve |
| Blend Curve (Alias), Bridge Curve, BlendCrv | **Blend Curve** | Blend Curve, at Edges and Curves | Right-click on two curve ends or edges; S menu |
| Project, Pull, Imprint | **Project** (vector, view, normal; bidirectional; Completion) | Project, at Faces (then curves) | Right-click on a face with curves selected |
| Intersect | **Intersect** | Intersect, at Faces or Object | Right-click on two faces |
| Trim, Divide, Cut | **Trim** (Keep, Discard, Divide) | Trim, at Faces: regions clicked | Right-click on a face with curves on it |
| Untrim, Trim Convert, Shrink | **Untrim**, **Trim Convert** | Untrim, Trim Convert, Shrink, at Faces | Right-click on a trimmed face |
| Shell Stitch / Unstitch, Join / Unjoin Sheets | **Stitch**, **Unstitch** | Stitch, Unstitch, at Object | Right-click on sheets |
| Align, MatchSrf, Match Crv, Symmetry Plane Align | **Align** | Align, at Edges: the input edge, then the master | Right-click on an edge: Align to…; S menu at Edges |
| Square, EdgeSrf, xNURBS Square | **Square** | Square, at Edges or curves | S menu with four boundaries picked |
| Skin, Loft | **Skin** | Skin | S menu |
| Rail, Sweep1/2, Profile | **Rail**, **Profile** | Rail, Profile | S menu |
| Set Planar | **Set Planar** | Set Planar | Right-click on closed curves |
| Extend (surfaces, curves) | **Extend** | Extend, at Edges (sheet edges) | Right-click on a sheet edge; selecting one offers it first, as in Plasticity |
| Freeform Blend, Bridge Surface, BlendSrf, Profile Blend | **Blend Surface** (profiles optional) | Blend Surface, at Edges | Right-click on two edges or curve chains |
| Surface Fillet, FilletSrf, face-face blend | **Surface Fillet** (two face sets) | Surface Fillet, at Faces: set 1, then set 2 | Right-click on faces: Fillet between… |
| Tubular Offset | **Tube** | Tube | Right-click on a curve on a surface |
| N-sided, Patch, xNURBS, fill hole | **Fill** (N-sided or Quad) | Fill, at Edges (a loop) | Right-click on a boundary loop; S menu |
| Ball Corner, Corner Blend, Bridge Fillet | **Corner** | Corner, at Faces | Right-click on three or four faces |
| Insert, Isoparam, InsertKnot | none: structure is direct | **Insert** at CVs and Patch: click a parameter, the new isoparm previewed | S menu at CVs; right-click on a face |
| Rebuild, Reduce, Del multi-knots, Uniform, Match knots, Non-rational, Raise Degree, NURBS to Bezier | **Rebuild** (for history after an import) | **Rebuild** and its types, at Patch and curves | Right-click on a face or curve |
| Transform CV (XYZ, NUV, SLIDE, PROJ, PARA, VIEW), Prop mod, Move CV Normal | none | The CVs level's move modes (§7.2) | The tool bar's mode row; the A menu at CVs |
| Stretch, Attach, Detach, Close, Reverse | none | Curve steps at Curves | Right-click on a curve |
| Continuity checks, combs, deviation | **Check** (a display node, no change to geometry) | Always on while a step's tool is active; a viewport toggle otherwise | The shading menu; the viewport's Display menu |

### 7.2 The CVs level

The owner asked for this level especially.

- **Picking:**
  - **CV or Hull.** A toggle, or Alt-hover as Plasticity's: a click takes a CV or its whole row.
  - **A second click** on a CV takes its row; on a row, the whole net.
- **The move modes**, Alias's Transform CV, are a row in the tool bar:
  - **World**: the gizmo, as now;
  - **NUV**: the gizmo's axes become the normal, U and V at each CV; each CV moves in its own frame;
  - **Slide**: along the hull;
  - **Project**: onto a picked plane or along a vector;
  - **Parallel**: parallel to a hull line;
  - **View**: the screen plane.

  Rotate and Scale keep their pivot setting. Non-proportional scale is the gizmo's axis scales.
- **Falloff:** today's Soft radius (3D), plus **Rows** (Alias's U and V counts and exponent) and
  **Hull distance** (Plasticity's).
- **Structure steps:**
  - **Insert** (a knot at a clicked parameter, the new isoparm shown in green before the click);
  - **Remove knot**;
  - **Raise degree**;
  - **Rebuild** (its types);
  - **Convert to B-spline** (an analytic face);
  - **Untrim**.

  Each is one step, one undo.
- **Continuity.** **Align** runs from here too: pick a row's edge, then the master. Its rows are
  marked: position, tangent, curvature and G3 rows drawn in four tints. A drag on a marked row
  follows §6.10.
- **Display:**
  - the **proxy** hull while dragging;
  - **Diagnostic feedback**: a comb on the edges of the faces being edited, live, with the G0–G3
    readout (§6.11);
  - the **curvature comb** on picked curves.

### 7.3 Handles and per-edge labels

- **Per-edge continuity.**
  - **Labels.** A label at each boundary's middle (G0, G1, G2, G3, Free) cycles on a click, as
    Plasticity's black circles and Alias's on-model labels do. It is the same value as the
    parameter row.
  - **Who has them.** Square, Rail, Fill, Blend Surface, Align and Skin.
- **Scale arrows.** Align's Tangent, Curvature and G3 scales are arrows on the row: the outer
  arrows scale each end, the middle slides the row (Alias's).
- **Flow Control labels.** At the ends of a blend: Edge align, Extend, Connect, Free, cycled by a
  click.
- **Variable values.** Radius, crown and offset handles along a blend, added with Shift-click on
  its rail and deleted with Shift-right-click. This generalizes the variable fillet's points
  (FUSION §9, parity round 2).
- **Partial range.** Arrows at the ends of the partial range, snapping to the master's ends.

## 8. Staged build plan

Each stage ends with `luc test` green in luced-3d and luce-cad, preview captures for the docs, and
both MODELING.md files updated. Tests drive the workspace as `cad_*_tests` and `edit_cad_*_tests`
do, and check geometry with Stage 0's measures. Where a closed form exists (a cylinder's curvature,
a Coons patch of four lines), they check against it.

**Stage 0: measuring** (S1).

**Stage 0: done** (2026-10-12). What was built:

- **luce-cad** `measure/` (public `CadMeasure`):
  - `basis_jet` and third-order jets of every curve and surface kind, with one-sided limits at
    knot lines (`geometry/jets.lucb`);
  - `check` (the continuity, combs and the lines that draw them, as `CadCheck`);
  - `deviation` (a colored tessellation and its statistics).
- **luce-gpu and luce-3d**: Draft shading (mesh shading 7), and the curvature map's radius band.
- **luced-3d**:
  - the **Check** node (`cad_check.luc`), with Check continuity on selected edges;
  - its lines published through the worker and drawn in four colors;
  - Draft and the radius band in the shading menu.

Captures: `tools/preview.py --scene` with `surf_check`, `surf_check_g1`, `surf_check_g3`
(`--mode 7`), `surf_combs`, `surf_deviation`, `surf_band` (`--mode 9`) and `surf_draft`
(`--mode 10`).

Tests run against closed forms:

- a rational ellipse's curvature rate;
- G1, G2 and G3 fillets;
- split faces;
- a cylinder's combs;
- concentric spheres, and a G1 fillet's depth against its box.

Left for later:

- **Combs.** No combs on isoparms or on curves on surfaces (curves arrive in Stage 2). No
  inflection marks, torsion quills or comb radius band.
- **Surface-relative combs** for edges.
- **Edges without a shared face.** No checks between faces that share no edge (Stage 3's
  stitching).
- ~~**Labels.**~~ Done after Stage 0: Alias-style text labels on the model ("G2  κ 0.00%"), and
  Deviation as a display tint over the CAD body rather than a mesh in its place.
- **Deviation's precision.** It resolves single precision tessellation points: about 1e-7 of the
  model's size.

The plan as first written:


- luce-cad:
  - third derivatives in `nurbs.lucb`;
  - `continuity(model, edge, stations)`, giving the four measures per station;
  - `curvature_comb(curve | edge | isoparm, samples)`;
  - `deviation(a, b)`.
- luced-3d:
  - comb and continuity overlays, and a Check node;
  - the shading menu gains Draft angle;
  - Curvature shading gains a radius band.
- Tests:
  - a cylinder's comb is constant at 1/r;
  - a G2 fillet's edge measures G2 within 1e-6 and fails G3;
  - a G3 fillet's edge passes G3;
  - the two pieces of a face cut by Split Face measure equal at every order.

**Stage 1: the NURBS toolkit and CV editing** (S2, S3).

- luce-cad: §6.9 in full, public, on curves and B-spline faces with their trims; degree cap 9 or
  more.
- luced-3d:
  - the CVs level's modes, Hull picking, Rows and Hull-distance falloff, proxy and steps (§7.2);
  - Insert, Remove knot, Raise degree, Rebuild (all types), Convert to B-spline.
- Tests:
  - every knot and degree operation leaves the surface within 1e-9 of where it was, except
    reductions, which stay within their tolerance;
  - Rebuild reports its deviation, and its result is within it;
  - an NUV move of a planar face's middle CV keeps the others still and moves it along the normal;
  - Rows falloff with Preceding 1 moves one neighbor by the exponent's weight.

**Stage 2: 3D curves and Blend Curve** (S4, S11 in part).

- luce-cad:
  - a curve component in CAD geometry sets: exact NURBS curves, with links to the edges or faces
    they came from;
  - curves on faces (uv and 3D, §6.3);
  - Blend Curve G0–G4 (§6.2).
- luced-3d:
  - a Curves level in Edit CAD;
  - Curve and Blend Curve nodes;
  - Duplicate as curve;
  - Stretch, Attach, Detach, Close, Reverse.
- The sketch's Blend Curve uses the 3D kernel.
- Tests:
  - G0–G4 ends measure their continuity, and the CV count follows §6.2's table;
  - a blend's end follows its edge when the body changes upstream;
  - Attach Blend at 0.5 meets in the middle.

**Stage 3: project, intersect, trim, stitch** (S5–S7).

- luce-cad:
  - Project (vector, normal, bidirectional, Completion) and Intersect, as curves on faces;
  - trimming by curves in uv: Keep, Discard, Divide;
  - Untrim with stages; Trim Convert; Shrink;
  - per-edge and per-vertex precision; Stitch and Unstitch.
- luced-3d: those nodes and steps; region markers to click; Show Intersections.
- Tests:
  - a circle projected along Z onto a cylinder's side gives the known intersection curve within
    tolerance;
  - Trim Keep of a disc region removes the outside, and its area matches;
  - Divide then Stitch gives back one face's area and a closed edge loop;
  - six squares stitch into a closed solid with the cube's volume;
  - Untrim All gives the natural surface.

**Stage 4: Align** (S8).

- luce-cad: §6.1. Rows G0–G3; Edge, Project, U/V and Vector types; Position Influence; Tangent
  Balance; Blending; Partial; two masters; Modify Both; Explicit Control on and off; Refine;
  curves; Symmetry Plane Align.
- luced-3d: the Align node and step; the row tints, scale arrows and partial arrows; diagnostic
  feedback; Accept chains in Edit CAD.
- Tests:
  - two quintic patches with an angle between them: after G1, G2 and G3 the edge measures each,
    and rows beyond Extra CV Rows have not moved;
  - with Position Influence 0, the input's knots are unchanged;
  - a G3 request on a patch with fewer than eight rows is refused with "needs 8 rows across, has 6"
    (Explicit Control on), or adds spans (off);
  - Partial 0.2–0.8 leaves the edge outside the range where it was.

**Stage 5: surfaces from curves** (S9, S10).

- luce-cad: Square (per edge Free, G0–G2, implied, tangent angle; Linear and Cubic blend);
  Skin; Rail (one or two rails, generation curves, sweep modes, transform control); Profile;
  Set Planar; sheet Extrude and Revolve; Extend (Linear, Natural, Soft, Reflective).
- luced-3d: the nodes and steps; per-edge labels; Boundary Labels.
- Tests:
  - Square of four lines is the bilinear patch;
  - Square G1 against four neighbors measures G1 on every edge;
  - Skin of three circles is a surface of revolution within tolerance;
  - Rail with two rails keeps each section's ends on both;
  - Extend Natural of a B-spline is the same polynomial (a point past the old edge evaluates as
    before).

**Stage 6: blends between surfaces** (S11).

- luce-cad: §6.7.
  - Blend Surface: per side G0–G3, shape, crown, flow control, range, profiles.
  - Surface Fillet between face sets: Radius or Chord; sections G0 chamfer, G1, G2, G3, Bias,
    Lead, conic; one-sided curvature; Form Factor; variable; trim Automatic, curves on surface or
    off.
  - Tube.
- luced-3d: the nodes and steps; arrows that flip each set's side; variable handles.
- Tests:
  - a Surface Fillet between two planes at 90° is today's edge fillet, face for face, for G1, G2
    and G3;
  - between a plane and a cylinder that do not touch, the G1 fillet's contact curves lie at r
    from the ball's center;
  - Blend Surface G3 both sides is three quintic spans across and measures G3.

**Stage 7: fill** (S12).

- luce-cad: §6.8.
  - Quad and N-sided; per-edge Free, G0, G1, G2.
  - Guides and points; tension, flatness, boundary flow.
  - Refine, quality, conflicts reported.
  - The transfinite start.
- luced-3d: the Fill node and step; per-edge labels; conflicts drawn on the edges.
- Tests:
  - a five-sided hole in a G2 body fills G2, measured on every edge within the tolerances;
  - a four-sided hole between planes gives a plane;
  - a guide curve lies on the result;
  - Quad mode gives an untrimmed face.

**Stage 8: Parasolid's blend options on solids** (S13, S14).

- luce-cad:
  - conic sections (rho, three ways); chamfer apex-range;
  - overflow smooth, cliff and notch, with Parasolid's default order;
  - limits (point, overlap) and caps; Y-blends; vertex blends;
  - corners of four or more edges, with Round's corner options;
  - G2 face blends by depth, skew and softness;
  - identify blends;
  - Ball Corner, Corner Blend, Bridge Fillet.
- luced-3d: those rows on the Fillet node and in Edit CAD.
- Tests:
  - an overflow that Parasolid's table says is a cliff becomes one;
  - a four-edge corner with setbacks measures G1 on every patch edge;
  - conic ρ 0.5 relative with equal sizes is the circle.

## 9. Notes for the build

- **Parity checks without the apps.** Alias, Plasticity and Rhino are not installed here. A
  behavior marked [unverified] stays so until a script in the real application settles it, as
  FUSION §9 suggests for Fusion.
- **Don't copy.** The Parasolid Functional Description describes behavior and option sets, and we
  match those. Its algorithms are not given there, and none of its code is used.
- **Degree 5 everywhere.** A reference tool's default degree (Alias's fillet sections at 7, its
  N-sided at 3, Rhino's Patch at 3) becomes our degree 5 with the spans the continuity needs.
  Explicit Control can still ask for theirs.

## 10. Questions answered by the owner

The owner's answers (2026-10-12):

1. **Curves and sheets as first-class objects: yes.** CAD geometry sets gain free 3D curves,
   curves on surfaces and open surface bodies as objects, beside sketches.
2. **Single spans: yes, on request.** The default is the multi-span quintic. Explicit Control
   offers a single span of degree 7.
3. **G4: on blend curves only.**
4. **Order: as planned.** Stages 0 to 8, in order.
5. **CV edits on aligned rows: re-run the Align.** In Edit CAD, a CV drag on a row that an Align
   step constrained re-runs that Align afterwards (§6.10's toggle is not needed).
6. **Alias's production extras come after Stage 8.**

The questions as asked:

1. **Curves and sheets as first-class objects.** Alias's workflow needs free 3D curves, curves on
   surfaces and open surface bodies in CAD networks and in Edit CAD (Stages 2–3). Agreed that CAD
   geometry sets gain a curve component beside sketches?
2. **Single-span results.** Alias and Plasticity offer single-span (Bézier) patches. A G3 single
   span needs degree 7. Default to multi-span quintic, with Explicit Control allowing degree 7
   single spans on request?
3. **G4 for curves.** Alias and Rhino blend curves go to G4: five quintic spans by our rule. Offer
   it on curves only, as they do?
4. **Order.** Measuring and the NURBS toolkit first (Stages 0–1), then curves, trims and Align
   before the builders, blends and fill. Or should Align or Fill come earlier?
5. **History of CV edits.** CV edits in Edit CAD are direct. Should a CV drag on a row that an Align
   step constrained be refused for that row, or re-run the Align afterward?
6. **Class A extras.** Light Tunnel, Highlights as curves, Fillet Flange, Panel Gap and Draft walls
   are Alias tools for production surfacing. Include them in this round's parity, or after Stage 8?
