# Stage 1: approved design and project plan

This document consolidates the Stage 1 design approved in the conversation.
Stage 1 originally established the plan in the conversation; it did not have a
separate downloadable README. This file preserves those decisions within the
cumulative directory. The master README contains their current implementation.

> Historical design: pending labels below describe the original plan. Stages 1-6 are
> now complete; consult the master README and PROGRESS.md for current status.

## Assignment structure

The grading categories are tool calibration (30%), CT registration (20%), biopsy
planning (20%), and targeting-error simulation (30%). Our six workflow stages
separate design and final verification from these four implementation tasks.

## Geometry and units

Figure 2 specifies M1=(2,18,0), M2=(8,18,0), M3=(2,24,0), tip P=(0,0,0),
and insertion direction v=(0,-1,0). Its coordinates have no explicit unit label.
The approved assumption is centimetres, converted to millimetres internally.
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

Axis: translate along a shaft-aligned straight guide at fixed orientation.
Fit a line to observed marker-centroid motion and map the direction back into
the marker frame. Ordered forward motion resolves the direction sign.

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

## Biopsy planning plan (Stage 4, pending)

Inputs: tumor centre/radius and registered tip/direction in CT coordinates.
Compute perpendicular distance from the needle axis to the tumour centre,
harvestable forward trajectory length inside the sphere, and insertion depth
to the far end of that segment. Test intersection, tangency, and complete miss,
plus backward-only and other geometric edge cases. A backward-only intersection
cannot be harvested by forward insertion. Clearly define tangent/no-core output.

## Targeting simulation plan (Stage 5, pending)

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

## Project organization and final stage

config.py, transforms.py, geometry.py, registration.py, calibration.py,
simulation.py, demo_flow.py, tests/, results/, README.md, and requirements.txt
support completed work. planning.py and error_analysis.py are planned additions,
not implemented placeholders. Stage 6 will review every rubric item and package
all code, explanations, validation outputs, and dependencies.

The initial design suggested pytest. The implementation uses Python's built-in
unittest instead, preserving the planned validation without another dependency.
NumPy, SciPy, and Matplotlib are the runtime dependencies.

## Cumulative delivery convention

Each checkpoint includes all completed stages in one BoneBiopsyPlanning folder.
The master README covers the full project to date. Stage-specific derivations
and results remain in place, and PROGRESS.md identifies completed and pending
work. Prior README snapshots are historical references, not competing setup
instructions. Review occurs before starting the next workflow stage.
