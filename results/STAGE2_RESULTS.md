# Stage 2 calibration results

Seed: 330. Independent calibration repetitions: 500.
Each calibration uses 80 poses. Axis calibration uses 100 mm of guided translation.
Diagram coordinates are assumed to be centimetres; calculations use millimetres.

| Validation | Result |
|---|---:|
| Exact tip error | 4.77857e-14 mm |
| Exact axis error | 1.39179e-14 degrees |
| Exact pivot error | 5.90221e-14 mm |
| Gaussian sigma per coordinate | 0.357720 mm |
| Observed fraction of marker errors below 1 mm | 0.950010 |

| Noisy calibration error | Mean | Median | 95th percentile | Maximum |
|---|---:|---:|---:|---:|
| tip_error_mm | 0.348836 | 0.336950 | 0.617251 | 0.841156 |
| axis_error_deg | 0.076342 | 0.071870 | 0.151196 | 0.214728 |

## Interpretation

Exact-data errors are at floating-point precision. With noisy marker observations,
the recovered poses are imperfect. The tip is far from the marker triangle, so
small orientation errors contribute to tip-position uncertainty. Multiple distinct
pivot poses reduce random uncertainty. Axis calibration benefits from a long
translation baseline and averaging the orientation over many observations.

The empirical 95th percentiles describe repeated calibrations for this geometry,
pose count, motion range, noise distribution, and estimator. They are not exact
confidence bounds or clinical validation. A different marker scale or restricted
motions changes the results. Pose recovery and pivot fitting involve noisy
rotations, so finite-sample errors and estimator bias are both possible.

The simulated tracker noise is isotropic and independent across markers, poses,
and repetitions. Marker-template uncertainty, guide misalignment, tip slippage,
correlated tracker error, and tool bending are excluded. Axis calibration assumes
constant orientation and a guide aligned with the shaft. These constraints are
part of the experiment, not conclusions inferred solely from the marker data.

Stage 5 will examine targeting error. Calibration errors in this stage do not
establish whether the final 3 mm targeting requirement is satisfied.
