# CT-guided Bone Biopsy Planning: final report

Author: Serhat Yaylacam

## Scope and assumptions

This project implements tool calibration, rigid registration into CT coordinates,
forward biopsy planning for a spherical target, and simulation of marker and
target localization errors. Source code, tests, reproducible outputs, detailed
hand calculations, and the original assignment are included in this directory.

The unlabelled figure coordinates are interpreted as centimetres, as documented
and approved during project setup, then converted to millimetres. Marker positions
are (20,180,0), (80,180,0), and (20,240,0) mm. The model tip is (0,0,0), and
insertion follows (0,-1,0). Changing the physical scale changes uncertainty.

## Calibration

The marker frame originates at M1, with its axes determined by the marker
triangle. Tip calibration holds the tip at a fixed pivot while the tool tilts
through diverse orientations. Stacking R_i p+t_i=c yields a least-squares
estimate of both the unknown local tip and unknown tracker-frame pivot.
Rank checks reject unidentifiable motions.

Axis calibration translates the tool through a shaft-aligned guide at constant
orientation. A line fitted to the marker-centroid trajectory identifies the
tracker-frame shaft direction; the measured mean orientation maps it into the
marker frame. Ordered forward motion determines the sign. Each calibration
uses 80 poses, and the axis translation spans 100 mm.

Exact observations recover the known parameters to numerical precision. For
noisy observations, each marker coordinate has Gaussian standard deviation
1/sqrt(chi2.ppf(0.95,3)) = 0.357720 mm. This gives a 95% radial error bound
of 1 mm, rather than a separate 1 mm bound on each coordinate.

Across 500 independent calibration repetitions:

| Error | Mean | Empirical 95th percentile |
|---|---:|---:|
| Tip position | 0.348836 mm | 0.617251 mm |
| Axis direction | 0.076342 degrees | 0.151196 degrees |

See README Stage 2 and results/STAGE2_RESULTS.md for motions, conditioning,
noise verification, plots, and limitations. True tip/axis values are not passed
to the calibration solvers.

## CT registration

A proper rigid least-squares transform is fitted to corresponding markers by
SVD. The tip is mapped with R p+t, while the axis receives rotation only.
Three independent reference cases cover pure translation, pure rotation, and
combined rotation/translation. All match their hand calculations to numerical
precision. STAGE3_DERIVATIONS.md gives expected marker, tip, and axis coordinates
before fitting; results/STAGE3_RESULTS.md records measured errors.

## Biopsy planning

For unit direction v, let a=(C-P) dot v and d=||(C-P) cross v||. Targeting
error is d. When d<=r, line intersections lie at a +/- sqrt(r^2-d^2).
Restricting these distances to forward insertion gives available core length
and insertion depth to the far endpoint. Targets only behind the tip are
unreachable. A tangent gives zero tissue core and a finite contact depth.

For a unit sphere at the origin and direction +x:

| Initial tip | Error (mm) | Core (mm) | Depth (mm) |
|---|---:|---:|---:|
| (-5,0.6,0) | 0.6 | 1.6 | 5.8 |
| (-5,1,0) | 1 | 0 | 5, contact only |
| (-5,2,0) | 2 | 0 | None |

All seven reference scenarios pass, including behind-only, inside, and initial
surface cases. See docs/STAGE4_DERIVATIONS.md for full calculations. This
axis-based model does not simulate finite needle width or a cutting mechanism.

## Targeting-error simulation and tolerance

Place the ideal target at (0,-100,0) mm. Each trial perturbs all three markers,
re-registers the tool, and independently displaces the target with a zero-mean
3D Gaussian. The primary error is the perpendicular distance from the inferred
trajectory to the displaced target. Endpoint error after exactly 100 mm of
insertion is recorded separately to address the assignment's alternate wording.

The simulation uses 200,000 trials for each of 31 target sigmas from 0 to 3 mm.
Each sigma is a coordinate standard deviation. Common random numbers pair the
levels, while individual trials at a fixed level remain independent. Pointwise
Wilson intervals describe uncertainty in the estimated success probability.
A separate 200,000-trial baseline provides independent confirmation.

| Baseline metric, sigma_target=0 | Fraction within 3 mm | 95% Wilson interval | Error p95 |
|---|---:|---|---:|
| Trajectory distance | 0.621670 | [0.619542, 0.623793] | 5.639103 mm |
| Endpoint distance | 0.617805 | [0.615673, 0.619932] | 5.649044 mm |

The independent baseline gives 0.624400 trajectory success, again far below
0.95. All sampled sigma levels fail. Therefore there is **no feasible target
sigma starting from zero** under these assumptions. Reporting a maximum of zero
would be misleading because zero also fails. The output uses null with an
explicit explanation. The finite sweep is not a claim of continuous optimization.

The approximately 300 mm marker-to-target distance amplifies angular uncertainty
from a marker triangle with 60 mm spacings. Marker localization within 1 mm does
not imply target localization within 1 mm. The low Stage 2 calibration errors
also benefit from 80 observations; each CT trial here uses one three-marker set.

Calibration uncertainty, systematic bias, correlated tracking errors, and tool
bending are excluded. The noisy-pose trajectory convention follows the exercise,
not a real control loop. See docs/STAGE5_METHODS.md and the full sweep outputs.

## Verification and reproducibility

The final cumulative suite contains 39 tests, including an end-to-end
calibration-to-registration-to-planning check. The complete demo reproduces all
four computational tasks. START_HERE.md gives commands, README.md retains the
full cumulative technical guide, and RUBRIC_REVIEW.md maps every rubric row to
code and evidence. Earlier documentation remains in docs/history.

## Guided demonstration update

The no-argument demo now provides a live guided walkthrough with plot windows
and a two-click planning exercise. Three additional tests verify click handling
and reset behavior. The full batch workflow remains available through explicit
--stage commands. GUI event handling was tested headlessly; native Windows
window rendering remains to be checked on the user machine.
