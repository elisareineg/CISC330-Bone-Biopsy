# Stage 4: biopsy planning geometry and worked examples

## Inputs and coordinate convention

All inputs share the CT frame. C is the tumor centre, r>0 its radius, P the
initial needle-tip position, and v the insertion direction. Normalize v to unit
length. The forward needle path is X(s)=P+s*v for s>=0. Distances below are mm.
The sphere represents a supplied target model. Fitting an inscribed sphere to
segmentation is outside this task's stated inputs.

The model treats the needle as an ideal line. The assignment mentions a roughly
3 mm needle diameter but requests axis/sphere geometry; this calculation does
not erode the target by the needle radius. A unit sphere is a mathematical test
case explicitly suggested in the assignment, not a clinically sized target.

## 1. Targeting error

Let w=C-P and a=w dot v. The closest point on the infinite needle axis is P+a*v.
The perpendicular vector is w-a*v, so:

    d = ||w-a*v|| = ||w cross v||

The implementation uses the cross product to avoid subtracting nearly parallel
vectors. This is distance to the infinite line, as requested, rather than the
forward ray. An aligned target behind the tip therefore has d=0 but cannot be
harvested by advancing the tool. We report reachability separately.

## 2. Sphere intersections

Substitute X(s) into ||X-C||^2=r^2. Since v has unit length:

    s^2 - 2*a*s + ||w||^2-r^2 = 0
    (s-a)^2 = r^2-d^2
    h = sqrt((r-d)*(r+d))
    s_near = a-h
    s_far  = a+h

When d>r, the line misses. When d=r, h=0 and the line is tangent. When d<r,
the full line passes through the sphere along a chord of length 2*h.
geometry.intersect_line_sphere returns the signed distances, leaving forward
reachability to planning.plan_biopsy. The reusable distance utility is
geometry.point_line_distance.

## 3. Forward core and insertion depth

For a reachable intersection, clip the near distance to the initial tip:

    entry = max(0,s_near)
    depth = max(0,s_far)
    core_length = depth-entry

If s_far<0, both intersections are behind the tip, so no forward core is
available. A tip initially inside the sphere can harvest only the remaining
forward segment, not the part behind its initial position.

Insertion depth is the distance from the initial tip to the far end of the
available core. It includes the approach before entering the target. It is not
just the tissue-core length. This is the idealized maximum available core under
the assignment's straight-trajectory model, not a model of a specific cutting
notch, device stroke limit, or biopsy device.

## Return-value conventions

| Situation | Core length | Insertion depth | status | harvest_possible |
|---|---|---|---|---|
| Forward segment inside sphere | Positive | Far endpoint distance | intersects | True |
| Forward tangent | Zero | Distance to contact | contact | False |
| Initial surface, pointing out | Zero | Zero (already in contact) | contact | False |
| Infinite line misses sphere | Zero | None | miss | False |
| Intersections only behind tip | Zero | None | behind | False |

For zero-core contact, the reported depth is a contact depth, not a depth that
produces a sample. None is JSON null, displayed as N/A in the report and as a
blank CSV field. Other outputs include entry depth, signed line intersections,
and CT coordinates of the reachable entry/end points. Those points are None
for an unreachable sphere.

## Required hand-calculated cases

Choose C=(0,0,0), r=1, v=(1,0,0). All numbers below are mm.

### Intersecting trajectory

P=(-5,0.6,0). Then w=(5,-0.6,0), a=5, and d=0.6.

    h = sqrt(1-0.36) = 0.8
    s_near = 5-0.8 = 4.2
    s_far  = 5+0.8 = 5.8
    core_length = 5.8-4.2 = 1.6
    insertion_depth = 5.8

Entry=(-0.8,0.6,0), exit=(0.8,0.6,0). Both are exactly one unit from C.
An off-centre chord tests more than a simple diameter through the centre.

### Tangent trajectory

P=(-5,1,0). Then a=5, d=1, h=0, and both roots equal 5.
Targeting error=1, core length=0, contact depth=5. Contact=(0,1,0).
There is no positive-length tissue core.

### Missed trajectory

P=(-5,2,0). Then a=5 and d=2>r. There are no real intersection roots.
Targeting error=2, core length=0, insertion depth=None.

## Additional cases

| Initial tip, axis +x | Targeting error | Core length | Depth | Reason |
|---|---:|---:|---:|---|
| (5,0,0) | 0 | 0 | None | Roots -6 and -4 lie behind the tip |
| (0,0,0) | 0 | 1 | 1 | Tip starts at sphere centre |
| (-1,0,0) | 0 | 2 | 2 | Initial surface, directed inward |
| (1,0,0) | 0 | 0 | 0 | Initial surface, directed outward |

The test suite also checks a non-axis-aligned trajectory in 3D, translated sphere,
non-unit input direction, finite input validation, and near-tangent numerical
behaviour. Reference outputs are literal values in planning_cases.py, not
computed using the solver being tested.

## Numerical tolerance

The default absolute tolerance is 1e-9 mm. A line whose perpendicular distance
is within tolerance of r is treated as tangent. A far root between -tolerance
and zero is treated as contact at the initial tip. Thus the tolerance deliberately
collapses extremely small near-tangent chords/gaps. It is a numerical tolerance,
not a clinical safety margin. Radius must be positive and finite; direction
must be finite and nonzero; all positions must be finite three-vectors.

## Use with registration

    pose = register_tool(markers_tool, tip_tool, axis_tool, markers_ct)
    plan = plan_biopsy(center_ct, radius_mm, pose['tip_ct'], pose['axis_ct'])

This interface accepts the Stage 3 outputs without changing frames or units.
Run the Stage 4 examples using `python demo_flow.py --stage planning`.
See results/STAGE4_RESULTS.md, planning_summary.json, planning_cases.csv,
and planning_scenarios.png for the full computed outputs and illustration.
