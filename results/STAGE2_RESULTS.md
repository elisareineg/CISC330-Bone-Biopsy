# Stage 2 calibration results

Seed: 330. Independent calibration repetitions: 500.
Each calibration uses 80 poses. Axis calibration spins the tool through a full turn
about its shaft, with the tip held in a divot.
Diagram coordinates are assumed to be centimetres; calculations use millimetres.

| Validation | Result |
|---|---:|
| Exact tip error | 2.175e-13 mm |
| Exact axis error | 1.36852e-15 degrees |
| Exact pivot error | 1.972e-13 mm |
| Gaussian sigma per coordinate | 0.357720 mm |
| Observed fraction of marker errors below 1 mm | 0.950010 |

| Noisy calibration error | Mean | Median | 95th percentile | Maximum |
|---|---:|---:|---:|---:|
| tip_error_mm | 0.348836 | 0.336950 | 0.617251 | 0.841156 |
| axis_error_deg | 0.053707 | 0.049203 | 0.107135 | 0.169598 |

## Interpretation

Exact-data errors are at floating-point precision. With noisy marker observations,
the recovered poses are imperfect. The tip is far from the marker triangle, so
small orientation errors contribute to tip-position uncertainty. Multiple distinct
pivot poses reduce random uncertainty. Axis calibration benefits from the full
spin and from the markers' distance from the shaft (circle radii of 20 to 80 mm):
larger circles define the plane, and therefore the axis, more precisely.

The empirical 95th percentiles describe repeated calibrations for this geometry,
pose count, motion range, noise distribution, and estimator. They are not exact
confidence bounds or clinical validation. A different marker scale or restricted
motions changes the results. Pose recovery and pivot fitting involve noisy
rotations, so finite-sample errors and estimator bias are both possible.

The simulated tracker noise is isotropic and independent across markers, poses,
and repetitions. Marker-template uncertainty, sleeve wobble, tip slippage,
correlated tracker error, and tool bending are excluded. Axis calibration assumes
the tool turns only about its own shaft, with no tilt or axial sliding. These constraints are
part of the experiment, not conclusions inferred solely from the marker data.

Stage 5 will examine targeting error. Calibration errors in this stage do not
establish whether the final 3 mm targeting requirement is satisfied.
