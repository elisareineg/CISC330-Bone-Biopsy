# CT-guided Bone Biopsy Planning: final report

Authors: Serhat Yaylacam, Akshay Kapal, Elisa Goncalves

## Scope and assumptions

This project implements tool calibration, rigid registration into CT coordinates,
forward biopsy planning for a spherical target, and simulation of marker and
target localization errors. Source code, tests, reproducible outputs, detailed
hand calculations, and the original assignment are included in this directory.

The unlabelled figure coordinates are interpreted as centimetres, as documented
in config.py, then converted to millimetres. Marker positions
are (20,180,0), (80,180,0), and (20,240,0) mm. The model tip is (0,0,0), and
insertion follows (0,-1,0). Changing the physical scale changes uncertainty.

## Calibration

The marker frame originates at M1, with its axes determined by the marker
triangle. Tip calibration holds the tip at a fixed pivot while the tool tilts
through diverse orientations. Stacking R_i p+t_i=c yields a least-squares
estimate of both the unknown local tip and unknown tracker-frame pivot.
Rank checks reject unidentifiable motions.

Axis calibration keeps the tip in the divot and spins the tool through a full
turn about its own shaft. Each marker then moves on a circle in a plane
perpendicular to the shaft. A plane fitted to the marker trajectories gives the
shaft direction (its normal), and a circle fitted to each marker gives a centre
on the shaft. Because the shaft is unchanged by the spin, the measured rotations
map the direction into the marker frame. A spin cannot show which way the needle
points, so the calibrated tip fixes the sign: the axis points from the markers
toward the tip. Each calibration uses 80 poses.

Exact observations recover the known parameters to numerical precision. For
noisy observations, each marker coordinate has Gaussian standard deviation
1/sqrt(chi2.ppf(0.95,3)) = 0.357720 mm. This gives a 95% radial error bound
of 1 mm, rather than a separate 1 mm bound on each coordinate.

Across 500 independent calibration repetitions:

| Error          |             Mean | Empirical 95th percentile |
| -------------- | ---------------: | ------------------------: |
| Tip position   |      0.348836 mm |               0.617251 mm |
| Axis direction | 0.053707 degrees |          0.107135 degrees |

See the README (Task 1) and results/STAGE2_RESULTS.md for motions, conditioning,
noise verification, plots, and limitations. True tip/axis values are not passed
to the calibration solvers.

## CT registration

A proper rigid least-squares transform is fitted to corresponding markers by
SVD. The tip is mapped with R p+t, while the axis receives rotation only.
Three independent reference cases cover pure translation, pure rotation, and
combined rotation/translation. All match their hand calculations to numerical
precision. docs/STAGE3_DERIVATIONS.md gives expected marker, tip, and axis coordinates
before fitting; results/STAGE3_RESULTS.md records measured errors.

## Biopsy planning

For unit direction v, let a=(C-P) dot v and d=||(C-P) cross v||. Targeting
error is d. When d<=r, line intersections lie at a +/- sqrt(r^2-d^2).
Restricting these distances to forward insertion gives available core length
and insertion depth to the far endpoint. Targets only behind the tip are
unreachable. A tangent gives zero tissue core and a finite contact depth.

For a unit sphere at the origin and direction +x:

| Initial tip | Error (mm) | Core (mm) |      Depth (mm) |
| ----------- | ---------: | --------: | --------------: |
| (-5,0.6,0)  |        0.6 |       1.6 |             5.8 |
| (-5,1,0)    |          1 |         0 | 5, contact only |
| (-5,2,0)    |          2 |         0 |            None |

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

| Baseline metric, sigma_target=0 | Fraction within 3 mm | 95% Wilson interval  |   Error p95 |
| ------------------------------- | -------------------: | -------------------- | ----------: |
| Trajectory distance             |             0.621670 | [0.619542, 0.623793] | 5.639103 mm |
| Endpoint distance               |             0.617805 | [0.615673, 0.619932] | 5.649044 mm |

The independent baseline gives 0.624400 trajectory success, again far below
0.95. All sampled sigma levels fail. Therefore there is **no feasible target
sigma starting from zero** under these assumptions. Reporting a maximum of zero
would be misleading because zero also fails. The output uses null with an
explicit explanation. The finite sweep is not a claim of continuous optimization.

**What would be needed.** Repeating the zero-displacement simulation with lower
marker noise shows the requirement is met only when marker sigma is at most
0.190 mm per coordinate, that is, when 95% of 3D marker errors are below about
0.53 mm: roughly half the 1 mm specified. Any target displacement would require
even more accurate marker localization (see docs/STAGE5_METHODS.md).

The approximately 300 mm marker-to-target distance amplifies angular uncertainty
from a marker triangle with 60 mm spacings. Marker localization within 1 mm does
not imply target localization within 1 mm. The low calibration errors (Task 1)
also benefit from 80 observations; each CT trial here uses one three-marker set.

Calibration uncertainty, systematic bias, correlated tracking errors, and tool
bending are excluded. The noisy-pose trajectory convention follows the exercise,
not a real control loop. See docs/STAGE5_METHODS.md and the full sweep outputs.

## Verification and reproducibility

The suite contains 42 tests, including an end-to-end
calibration-to-registration-to-planning check. The batch demo reproduces all
four computational tasks. README.md explains how to run everything, and
docs/RUBRIC_REVIEW.md maps every rubric row to code and evidence.

## Guided demonstration

Running `python demo_flow.py` with no arguments gives a live walkthrough with
plot windows and a two-click planning exercise; three tests verify the click
handling and reset behaviour. Explicit `--stage` commands run the calculations
without windows.

## AI attribution

Parts of this project were developed with assistance from Claude (Anthropic) and ChatGPT (OpenAI).

Claude was used to review the code against the assignment rubric, implement the spin-based tool-axis calibration with plane and circle fitting, compute the marker accuracy needed to meet the targeting requirement, and reorganize the documentation.

ChatGPT was used to help with the implementation and refinement of the functions related to rigid registration and biopsy planning. It was also used to assist with code review, debugging, and test verification.

All AI-assisted code and text were reviewed by the team and tested with the full test suite and the reproducible results above.
