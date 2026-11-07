# Stage 5 targeting-error simulation

No feasible target-displacement sigma: even sigma=0 fails; all sampled levels also fail.

200,000 independent trials per sigma; seed 335; marker coordinate sigma 0.357720 mm.
The grid runs from 0 to 3 mm in 0.1 mm steps. Insertion depth is 100 mm.
Target sigma is per coordinate, not a radial displacement bound.

## Baseline: marker noise only

| Metric | Fraction within 3 mm | 95% Wilson interval | 95th-percentile error |
|---|---:|---|---:|
| trajectory | 0.621670 | [0.619542, 0.623793] | 5.639103 mm |
| endpoint | 0.617805 | [0.615673, 0.619932] | 5.649044 mm |

## Independent baseline validation

- trajectory: success fraction 0.624400, 95% interval [0.622275, 0.626520], p95 error 5.641771 mm.
- endpoint: success fraction 0.620650, 95% interval [0.618521, 0.622774], p95 error 5.653117 mm.

## Selected sweep values

| Target sigma (mm) | Trajectory success | Trajectory p95 (mm) | Endpoint success | Endpoint p95 (mm) |
|---|---:|---:|---:|---:|
| 0.0 | 0.621670 | 5.639103 | 0.617805 | 5.649044 |
| 0.5 | 0.602625 | 5.759846 | 0.589025 | 5.794439 |
| 1.0 | 0.551060 | 6.116892 | 0.502900 | 6.219954 |
| 1.5 | 0.477775 | 6.663982 | 0.380570 | 6.871189 |
| 2.0 | 0.403035 | 7.379779 | 0.272830 | 7.739151 |
| 2.5 | 0.334780 | 8.235704 | 0.193330 | 8.770699 |
| 3.0 | 0.277810 | 9.172457 | 0.137790 | 9.901116 |

## Interpretation and scope

Under the approved coordinate scale, the 60 mm marker spacing is small
relative to the roughly 300 mm marker-to-target lever arm. Submillimetre
marker localization errors become angular uncertainty, amplified at the
target. The 1 mm marker bound is not a 1 mm needle-target error bound.

A value of zero is NOT a tolerable maximum in this run: zero also fails.
The result is no feasible sigma under the baseline-first tolerance search.
Every sampled sigma in [0,3] mm fails. The finite grid is not a proof about
all arbitrarily large sigmas, and no continuous threshold is inferred.

The primary metric follows the assignment trajectory-distance definition.
The endpoint metric is reported separately; axial displacement affects it
even when distance to the infinite trajectory remains zero. Neither metric
meets the requirement at baseline. The 95% success requirement is distinct
from the 95% confidence intervals used to estimate that probability.

Intervals are pointwise, not simultaneous across the sweep. Common random
numbers pair sigma levels; trials at each level remain independent. A
separate run validates the prespecified baseline, far from the pass/fail
boundary. No maximum was selected from noisy passing levels.

Stage 2 calibration error is not added: this experiment holds the model
tip/axis fixed and isolates the requested CT marker noise and independent
target displacement. The noisy registered pose defines the perturbed
trajectory in the exercise; this is not a model of a real control loop.
See docs/STAGE5_METHODS.md for equations, assumptions, and checks.
