# Design: geometry, frames, and methods

This document records the design decisions behind the project: the tool geometry,
coordinate frames, noise model, and the method chosen for each assignment task.
The README describes the implementation and results.

## Assignment structure

The grading categories are tool calibration (30%), CT registration (20%), biopsy
planning (20%), and targeting-error simulation (30%).

## Geometry and units

Figure 2 specifies M1=(2,18,0), M2=(8,18,0), M3=(2,24,0), tip P=(0,0,0),
and insertion direction v=(0,-1,0). Its coordinates have no explicit unit label.
We assume centimetres and convert to millimetres internally.
DIAGRAM_UNIT_TO_MM=10 in config.py controls that assumption.

In mm the markers are (20,180,0), (80,180,0), (20,240,0). The tool tip remains
the origin, and the insertion direction is the negative y direction. Results
depend on this scale; it must not be silently changed to improve performance.

## Frames and transformation conventions

- Model frame: the ground-truth coordinates from the figure.
- Marker frame: origin at M1; x toward M2; y along the orthogonal component of
  M3-M1; z=x cross y.
- Tracker frame: external observations for calibration.
- CT frame: marker observations for procedure planning.

The true marker-frame tip is (-20,-180,0) mm. With marker basis B and origin o,
p_model=B@p_marker+o and v_model=B@v_marker. For registration,
p_ct=R@p_model+t and v_ct=R@v_model. Unit vectors receive no translation.
Marker correspondences are assumed known and ordered consistently.

## Calibration plan

Tip: hold the tip fixed at an unknown pivot while tilting around multiple axes.
Estimate each pose from markers and solve R_i p + t_i = c for both p and c.
Check observability and validate exact and noisy recovery.

Axis: keep the tip in the divot and spin the tool about its own shaft (for
example inside a sleeve). Each marker moves on a circle in a plane perpendicular
to the shaft. Fit a plane to the marker trajectories (its normal is the axis
direction) and a circle to each marker (its centre lies on the shaft). Map the
direction back into the marker frame. A spin cannot reveal which way the needle
points, so the calibrated tip fixes the sign: the axis points from the markers
toward the tip.

Ground truth belongs to the simulator and validation, not the solver inputs.

## Noise model

Independent coordinate errors follow N(0,sigma_m^2). Choose
sigma_m=1/sqrt(chi2.ppf(0.95,3)) mm, approximately 0.357720 mm, so 95% of
3D marker displacements are below 1 mm. This is a radial 3D requirement.
Calibration repeats quantify tip-position error in mm and axis error in degrees.

## Registration plan

Use rigid registration from the three corresponding noncollinear markers.
Validate pure translation, pure rotation, and combined rotation/translation
against independently worked predictions. Transform the tip as a point and
axis as a direction. Retain reusable geometry and transformation modules.

## Biopsy planning plan

Inputs: tumor centre/radius and registered tip/direction in CT coordinates.
Compute perpendicular distance from the needle axis to the tumour centre,
harvestable forward trajectory length inside the sphere, and insertion depth
to the far end of that segment. Test intersection, tangency, and complete miss,
plus backward-only and other geometric edge cases. A backward-only intersection
cannot be harvested by forward insertion. Clearly define tangent/no-core output.

## Targeting simulation plan

Use identical model and CT frames for the baseline. With the initial tip at
(0,0,0) and insertion direction (0,-1,0), the planned 100 mm target is
(0,-100,0) mm. Add independent marker noise, re-register, and independently
perturb the target using isotropic Gaussian displacement. Start displacement
sigma at zero and sweep upward. Estimate the maximum compatible with the 95%
requirement, accounting for Monte Carlo uncertainty. If marker noise alone
fails, report that rather than forcing a positive tolerable sigma.

The assignment defines compound error as distance to the trajectory but also
mentions endpoint accuracy. Report trajectory distance and separately examine
endpoint error after 100 mm insertion, with explicit interpretation.

## Tools

Tests use Python's built-in unittest (pytest also runs them). NumPy, SciPy, and
Matplotlib are the runtime dependencies.
