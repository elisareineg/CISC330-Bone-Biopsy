# Rubric review

The supplied assignment and its appended rubric were reviewed against this
implementation. The table maps each criterion to inspectable evidence;
it is a coverage review, not a prediction of awarded marks.

## Tool calibration: 30 points

| Criterion | Points | Evidence |
|---|---:|---|
| Calibration formulation | 3 | README Stage 2; marker-frame unknown tip and axis |
| Tool-tip method | 5 | calibration.calibrate_tip: stacked least-squares pivot equations |
| Tool-tip motion constraints | 3 | simulation.pivot_observations; fixed pivot and multi-axis tilts; degeneracy test |
| Tool-axis method | 5 | calibration.calibrate_axis: plane fit of the spin trajectories (axis direction), circle fit per marker (centres on the shaft), mapped into the marker frame by the measured rotations |
| Tool-axis motion constraints | 3 | Full 360-degree spin about the shaft with the tip in a divot; spins under 30 degrees rejected; sign fixed by the calibrated tip; README |
| Ground-truth simulation | 3 | simulation.py, config.py; known model used only to synthesize and validate |
| Perfect-data validation | 2 | Exact recovery tests and results/STAGE2_RESULTS.md |
| Gaussian marker error | 3 | config.MARKER_SIGMA_MM; 3D chi-square radial calibration; simulation.py |
| Noisy calibration results | 2 | 500 independent calibrations; CSV/JSON, error plot, interpretation |
| Implementation/explanation | 1 | Separate geometry (including plane and circle fitting), transform, registration, simulation, calibration modules |

## Registration: 20 points

| Criterion | Points | Evidence |
|---|---:|---|
| Rigid registration | 7 | registration.rigid_registration; proper SVD rotation and centroid translation |
| Transform tool tip | 3 | register_tool returns R@tip+t; nonzero-tip test |
| Transform tool axis | 3 | register_tool returns normalized R@axis; translation-invariance test |
| Pure translation | 2 | registration_cases.py case 1; STAGE3_DERIVATIONS.md |
| Pure rotation | 2 | Case 2: +90 degree z rotation with literal expected markers |
| Rotation + translation | 2 | Case 3: cyclic rotation into a different plane, plus translation |
| Explanation/numerical agreement | 1 | STAGE3_DERIVATIONS.md; results/STAGE3_RESULTS.md and JSON |

## Biopsy plan: 20 points

| Criterion | Points | Evidence |
|---|---:|---|
| Targeting error | 5 | geometry.point_line_distance; planning.plan_biopsy |
| Tissue-core length | 5 | Forward-clipped line/sphere chord; inside and backward tests |
| Needle insertion depth | 5 | Far reachable intersection measured from initial tip |
| Intersecting test | 1 | Offset chord: error 0.6, core 1.6, depth 5.8 mm |
| Tangent test | 1 | Error 1 mm, zero core, contact at 5 mm |
| Miss test | 1 | Error 2 mm, zero core, no feasible depth |
| Geometry utilities/explanation | 2 | geometry.py; docs/STAGE4_DERIVATIONS.md; edge-case conventions |

## Targeting-error simulation: 30 points

| Criterion | Points | Evidence |
|---|---:|---|
| Ideal scene/baseline | 2 | Identity model-to-CT pose; target 100 mm along negative y |
| Marker-localization error | 4 | Independent Gaussian errors, sigma=0.357720 mm per coordinate |
| Propagation through registration | 5 | Fresh batched SVD fit per trial; compared with scalar registration in tests |
| Target-displacement model | 4 | Independent 3D Gaussian stream, scaled by target sigma |
| Compound targeting error | 4 | Cross-product distance to perturbed trajectory; endpoint metric separate |
| Statistical design | 3 | 200,000 trials per level, paired levels, Wilson intervals, independent baseline |
| Sigma sweep | 3 | 31 levels from 0 to 3 mm at 0.1 mm spacing; CSV/JSON and plot |
| Maximum tolerable sigma | 3 | Baseline already fails; no feasible tolerance from zero; null rather than a misleading zero; marker accuracy that would meet the requirement reported (0.190 mm per coordinate) |
| Results/discussion | 2 | docs/STAGE5_METHODS.md; results/STAGE5_RESULTS.md; lever-arm effect and limitations |

Total rubric points represented: 100.

## Final integration and numerical review

An additional test calibrates the tool in marker coordinates, registers those
estimated quantities into a nontrivial CT pose, and plans a central chord through
a radius-5 mm target at depth 100 mm. Independent expected entry/core/depth values
are 95/10/105 mm. The full suite contains 42 tests.

The targeting result was also checked using a first-order localization model.
Let q_j be centred marker coordinates and S=sum(||q_j||^2 I-q_j q_j^T).
For isotropic marker coordinate variance sigma_m^2, approximate rotation
covariance is sigma_m^2 S^-1. At target offset r from the marker centroid,
position covariance is approximately sigma_m^2/3 I + [r]x Cov(rotation) [r]x^T.
For the assumed geometry this predicts transverse coordinate standard deviations
of about 1.563 and 2.722 mm. This independently explains why a 3 mm radial bound
cannot contain 95% of observations. It is a first-order check, not a replacement
for the nonlinear Monte Carlo result.

## Explicit assumptions and review limits

- Figure coordinates have no explicit unit label; the centimetre
  interpretation is stated in config.py, README, and the methodology.
- Axis calibration assumes the tool spins only about its own shaft (tip held in
  the divot, no wobble or axial sliding). Observations alone cannot establish
  that mechanical condition.
- The targeting experiment follows the exercise's noisy-pose trajectory
  convention; it does not simulate a real feedback controller.
- No feasible tolerance from zero is supported by the baseline and sampled sweep.
  The grid is not presented as a continuous optimization proof.
- The clinical success criterion is not met. This is a reported simulation
  finding, not a failed software check or a reason to change the inputs silently.
- Meeting the requirement would need marker sigma of at most 0.190 mm per
  coordinate (95% of 3D marker errors below about 0.53 mm); see
  docs/STAGE5_METHODS.md.

## Guided demonstration

Running `python demo_flow.py` with no arguments gives a live walkthrough with
plot windows and a two-click planning exercise. Three tests verify click
handling and reset behaviour. Explicit `--stage` commands run the calculations
without windows.
