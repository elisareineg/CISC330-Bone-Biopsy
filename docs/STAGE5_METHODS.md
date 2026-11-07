# Stage 5: targeting error, displacement tolerance, and statistical method

## Question and interpretation

The assignment asks how much random target displacement can be tolerated when
marker localization is noisy, the insertion depth is 100 mm, and at least 95%
of targeting errors must be within 3 mm. It explicitly defines compound error
as perpendicular distance between the needle trajectory and displaced target.
Its additional wording about the needle tip motivates a second endpoint metric.
Both are reported, never combined into one ambiguous metric.

The primary exercise convention treats the pose inferred from noisy markers as
the perturbed needle trajectory. This estimates uncertainty propagated through
registration. Mere measurement noise does not physically move an otherwise fixed
needle; a real closed-loop procedure would need an additional control/aiming
model. No such control loop is asserted here.

## Baseline scene and geometry

Ground-truth model and CT frames coincide. P=(0,0,0), v=(0,-1,0), and the
planned target is C=P+100v=(0,-100,0) mm. Markers are (20,180,0), (80,180,0),
and (20,240,0) mm under the approved centimetre interpretation of Figure 2.
No marker positions, scale, or noise levels are tuned to satisfy the requirement.

The target is a point for this task; tumor radius and tissue-core changes are
not used. Stage 2 calibration uncertainty is excluded: the input tip and axis
are known model quantities, so this task isolates the requested CT localization
and target-displacement sources. The model and CT marker correspondences are
known. There is no averaging of repeated CT frames within one trial.

## Random errors

For each trial and marker j:

    M_j_observed = M_j_true + epsilon_j
    epsilon_j ~ N(0, sigma_marker^2 * I3)
    sigma_marker = 1 / sqrt(chi2.ppf(0.95,3)) = 0.357720 mm

Thus P(||epsilon_j|| < 1 mm)=0.95. The 95% condition is per marker observation,
not a claim that all three markers simultaneously satisfy that bound.

Target displacement is independent:

    delta = sigma_target * z,  z ~ N(0,I3)
    C_displaced = C + delta

sigma_target is standard deviation of each coordinate. The 95th percentile of
radial target displacement would be about 2.79548*sigma_target. Marker errors
are independent across markers, coordinates, and trials. The target stream is
independent of the marker stream, generated from separate SeedSequence children.

## Propagation and errors

For every trial, perform a fresh least-squares proper rigid registration of the
model markers to the noisy observations. Batched SVD implements the same formula
as registration.rigid_registration; a dedicated test compares its tip and axis
outputs to register_tool for the same noisy inputs.

Let R_hat,t_hat be the inferred transform:

    P_hat = R_hat P + t_hat
    v_hat = R_hat v, normalized
    e_trajectory = ||(C_displaced - P_hat) cross v_hat||
    e_endpoint = ||C_displaced - (P_hat + 100*v_hat)||

The first metric is distance to the infinite axis. The second uses the predicted
tip after exactly 100 mm insertion. Endpoint distance is at least line distance.
Axial target displacement contributes to endpoint error but not line error for
a perfectly aligned axis. The fixed-depth endpoint calculation also retains
axial tool localization error.

## Trial count and sweep

Use 200,000 independent trials at each of 31 levels: 0,0.1,...,3.0 mm.
Generate noisy registered poses once, and reuse them with the same independent
standard-normal target draws rescaled at each level. This common-random-number
scheme makes adjacent levels comparable without confounding fresh simulation
noise. Trials within a level are independent; different levels are paired,
so the sweep is not 6.2 million independent tool registrations.

Report success count, estimated probability of error<=3 mm, a two-sided 95%
Wilson interval, mean, median, and empirical 95th percentile for each metric.
For the estimated success probability p=k/n and z=1.95996:

    denominator = 1 + z^2/n
    centre = (p + z^2/(2*n)) / denominator
    half_width = z*sqrt(p*(1-p)/n + z^2/(4*n^2)) / denominator

A supported pass requires the interval lower bound >=0.95. A supported failure
requires the upper bound <0.95. Anything between is labelled uncertain. These
are pointwise intervals, not simultaneous confidence bands for all grid levels.
The clinical 95% probability target and the statistical 95% confidence level are
different concepts.

A separate 200,000-trial baseline with seed 10335 validates the prespecified
zero-displacement result independently of sweep fluctuations. The main seed is
335. The baseline is far enough from 95% that small Monte Carlo variation cannot
change the conclusion. No close threshold needs adaptive refinement in this run.

## Result: no feasible tolerance from zero

See results/STAGE5_RESULTS.md for the numerical output. Marker noise alone gives
about 62% success, and the 95th-percentile trajectory error is about 5.64 mm.
The independent baseline confirms the failure. All 31 sampled displacement
levels fail for both metrics.

The requested maximum tolerance cannot be a positive number, and it should not
be reported as zero: sigma=0 also violates the requirement. The result is
**no feasible sigma under the baseline-first tolerance search**. The JSON uses
null for maximum_supported_grid_sigma_mm, with an explicit conclusion string.
The finite grid documents [0,3] mm; it is not a theorem about every unsampled
sigma or a continuous optimized maximum. If a future configuration passes the
baseline, refine and independently validate any crossing before reporting a
continuous maximum; this checkpoint only reports a supported grid candidate
in that hypothetical case.

## Why marker noise alone fails

The marker centroid is (40,200,0) mm and the target is (0,-100,0), so their
separation is roughly 303 mm. The principal marker spacings are only 60 mm.
Small localization errors perturb rotation; at a point far from the marker
triangle, that angular error is multiplied by a long lever arm. A submillimetre
marker-error bound therefore does not imply submillimetre target accuracy.
The low errors from Stage 2 use 80 observations per calibration, unlike the
single three-marker CT observation used for each Stage 5 trial.

Improving accuracy would require changing measurement precision, marker layout,
or the observation protocol. Those are potential design changes, not changes
made to the assigned simulation to force a favorable result. Confirming the
unlabelled figure units with the teaching team remains relevant to physical
interpretation; this package consistently uses the approved assumption.

## Independent analytic checks

With zero marker noise and sigma_target=1 mm, trajectory error is the norm of
two independent standard Gaussian coordinates. Its success probability at 3 mm
is 1-exp(-9/2). Endpoint error is the norm of three such coordinates; its success
probability is chi2.cdf(9,3). A seeded 60,000-sample test checks both against
these analytic values. A separate deterministic check gives a 5 mm trajectory
error for lateral displacement (3,0,4), but zero trajectory error for purely
axial displacement (0,2,0), while endpoint error is 2 mm in the latter case.

If markers were perfect, the theoretical target-only sigma limits would be:

    trajectory: 3/sqrt(-2*log(0.05))
    endpoint:   3/sqrt(chi2.ppf(0.95,3))

These benchmarks are recorded in JSON only as diagnostics, not as the answer
with actual marker noise. Additional tests cover exact zero-error registration,
reproducibility, Wilson interval arithmetic, sweep classification, and invalid
inputs. The cumulative suite contains 35 passing tests.

## Files, execution, and limitations

Run `python demo_flow.py --stage targeting --targeting-trials 200000`.
The standalone targeting_demo.py also accepts --seed. Changing the sample count
changes estimates and is reflected in output metadata.

- STAGE5_RESULTS.md: result and explanation.
- targeting_summary.json: full settings, both baselines, and every sweep row.
- targeting_sweep.csv: compact machine-readable results for both metrics.
- targeting_baseline_errors.npz: all main-run zero-displacement error samples.
- targeting_trial_sample.npz: first 1,000 registered tips, axes, and target draws.
- targeting_sigma_sweep.png: success probability and p95 versus sigma.
- targeting_baseline_cdf.png: baseline error distributions.
- targeting_log.txt: standalone Stage 5 console output.

All these generated outputs are under results/. Re-running uses the same seed
and model but can differ slightly across numerical-library versions. Quantile
estimates are empirical and do not carry a separate quantile confidence interval.
The simulation excludes systematic localization bias, correlated error, marker
misidentification, tool bending, calibration uncertainty, and realistic patient
biomechanics. It is a course simulation, not clinical validation.
