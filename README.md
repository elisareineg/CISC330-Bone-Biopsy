# CT-guided Bone Biopsy Planning

CISC/CMPE 330 assignment. Authors: Serhat Yaylacam, Akshay Kapal, Elisa Goncalves.

This project implements the four assignment tasks: tool calibration, registration
of the tool into the CT frame, biopsy planning for a spherical tumour, and a
targeting-error simulation. It includes the code, tests, worked hand calculations,
and generated results. The assignment PDF is in
[reference/HW-Bone-Biopsy-Planning.pdf](reference/HW-Bone-Biopsy-Planning.pdf), and
[FINAL_REPORT.md](FINAL_REPORT.md) is the consolidated written report.

## How to run

From the repository root, with Python 3.11 or newer (verified on 3.12):

1. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Run the tests (42 tests; `pytest` also runs them):

   ```bash
   python -m unittest discover -s tests -v
   ```

3. Regenerate every result in `results/` without windows or prompts (about 20 seconds):

   ```bash
   python demo_flow.py --stage all
   ```

4. Or run the guided walkthrough with plot windows and a clickable planner:

   ```bash
   python demo_flow.py
   ```

A single task can be rerun with `--stage calibration`, `--stage registration`,
`--stage planning`, or `--stage targeting`. The defaults are `--trials 500`
(calibration repetitions) and `--targeting-trials 200000` (trials per sigma level).
The commands work in Windows PowerShell and macOS/Linux terminals; if `python`
is not found, use `python3` (macOS/Linux) or `py` (Windows).

### Guided walkthrough

Press Enter between parts and close each figure window to continue. The 3D tool
views can be rotated with the mouse. The planning window takes two clicks: the
initial needle tip, then an aiming point. Reset allows another plan; Continue
closes the planner. Its XY slice is synthetic, with a 10 mm radius sphere at the
origin, not patient CT data. Exact calibration and registration run live; the
statistical results are read from `results/` rather than recomputed. The
walkthrough needs a desktop Matplotlib backend (usually TkAgg); the `--stage`
commands do not.

## Results at a glance

| Task | Result |
|---|---|
| 1. Tool calibration | Exact data recovers the tip and axis to about 1e-13. With realistic marker noise (500 repetitions): tip error mean 0.35 mm (95th percentile 0.62 mm), axis error mean 0.054 degrees (95th percentile 0.107 degrees) |
| 2. Registration | Pure translation, pure rotation, and combined cases all match their hand-derived predictions to about 1e-13 mm |
| 3. Biopsy plan | All seven hand-derived cases pass, including intersect (error 0.6 mm, core 1.6 mm, depth 5.8 mm), tangent, and miss |
| 4. Targeting simulation | The requirement is not met even with zero target displacement: 62.2% of trials within 3 mm (95% needed), 95th percentile 5.64 mm, so no target sigma is tolerable. Meeting it would need marker noise of at most 0.190 mm per coordinate |

## Geometry and coordinate conventions

The assignment's Figure 2 specifies M1=(2,18,0), M2=(8,18,0),
M3=(2,24,0), P=(0,0,0), v=(0,-1,0). The figure omits units.
We explicitly assume centimetres and convert coordinates to mm with
DIAGRAM_UNIT_TO_MM=10 in config.py. This gives 60 mm marker spacing and a
180 mm axial distance from the tip to the lower markers. Change this one
setting and rerun if course guidance confirms another unit. Never interpret
the 3D noise threshold in diagram units: it always remains 1 mm.

Three noncollinear labeled markers define a right-handed frame: origin M1,
x toward M2, y toward the perpendicular component of M3-M1, z=x cross y.
For this model the marker-frame tip is (-20,-180,0) mm and the axis is (0,-1,0).
The triangle is planar, which is valid for rigid registration; collinearity is not.

B contains marker-frame basis vectors expressed in model coordinates:

    p_model = B @ p_marker + origin
    v_model = B @ v_marker
    p_tracker = R @ p_marker + t

Arrays contain row points, so their implementation is points @ R.T + t.
Axes are unit direction vectors and do not receive translations.
See [docs/STAGE1_DESIGN.md](docs/STAGE1_DESIGN.md) for the design decisions.

## Task 1: tool calibration

### Recover tracker poses

For each frame, fit the known marker template to the observed corresponding
markers using a least-squares rigid transform (SVD/Kabsch). Enforce determinant
+1 so the solution is a rotation rather than a reflection. Marker identities
are known; correspondence search is outside this task.

### Tip: fixed-pivot calibration

Hold the tip at a stationary point c and tilt the tool through multiple axes.
For each pose, R_i p + t_i = c, where p is the unknown tip in the marker frame.
Stack [R_i, -I] [p; c] = -t_i and solve the overdetermined system by least squares.
Both p and c are unknown. Reject rank-deficient systems; report conditioning
and the 3D RMS pivot residual. Merely spinning the tool about one fixed axis
leaves a component unobservable. Noise can obscure degeneracy, so motion design
and the reported condition number still matter even when numerical rank is six.

Simulation uses 80 orientations, with rotation-vector components sampled from
[-0.9,0.9] radians, and sets t_i = c - R_i p to preserve the pivot exactly.
The pivot is (45,-30,75) mm in tracker coordinates. Independent marker noise is
added after generating the rigidly transformed marker positions.

### Axis: spin calibration with plane and circle fitting

Keep the tip in the divot and spin the tool about its own shaft, for example
inside a sleeve, so that it rotates only about its axis (no tilt, no axial
sliding). Each marker then moves on a circle in a plane perpendicular to the shaft:

1. **Plane fit.** All marker circles lie in parallel planes, so the common normal
   of the trajectories (each marker centred on its own mean) is the shaft
   direction in tracker coordinates (`geometry.fit_plane`).
2. **Circle fit.** Each marker's circle centre lies on the shaft
   (`geometry.fit_circle`, an algebraic least-squares fit in the plane). The
   centres locate the shaft line and serve as a consistency check.
3. **Back to the marker frame.** The spin leaves the shaft unchanged, so
   R_i a = a_tracker for every pose and a = mean_i(R_i^T a_tracker).
4. **Sign.** A spin cannot show which way the needle points. The calibrated tip
   fixes it: the axis points from the marker triangle toward the tip, which is
   the insertion direction.

The simulation spins the tool through a full turn in 80 steps, with the shaft at
a fixed, nontrivial tracker orientation. Spins under 30 degrees are rejected
because short arcs make the plane and circle fits poorly conditioned. The solver
reports the spin span, circle radii and fit residuals, and the distance of the
calibrated tip from the fitted shaft (zero for consistent data). No true tip or
axis is passed into either calibration solver: the simulator knows the ground
truth, and the solver receives only marker templates, observations, and the
calibrated tip.

### Gaussian tracker error

Every coordinate of every marker receives independent N(0,sigma^2) error.
For isotropic 3D error, ||error||^2/sigma^2 has a chi-square distribution with
three degrees of freedom. Therefore:

    sigma = 1 mm / sqrt(chi2.ppf(0.95, 3)) = approximately 0.358 mm

Using 1/1.96 mm would describe a 1D coordinate interval and is incorrect for
this 3D magnitude requirement. The demo checks the radial error on 200,000
independent draws and runs 500 independent calibration repetitions. Random
streams are seeded and separated. Repetitions regenerate both motions and noise.
Results: [results/STAGE2_RESULTS.md](results/STAGE2_RESULTS.md).

## Task 2: CT registration

`register_tool(markers_tool, tip_tool, axis_tool, markers_ct)` fits a proper
rigid transform from corresponding marker observations, then returns the CT tip,
unit axis, rotation, translation, and RMS marker-fit residual. Positions receive
rotation and translation; direction vectors receive rotation only. The SVD fit
rejects collinear marker sets and enforces a rotation determinant of +1.

Three independent hand-calculated cases validate pure translation, a +90 degree
z rotation, and a cyclic rotation with translation. The last case moves the
marker triangle from the XY plane to the YZ plane. Additional tests check a
nonzero tip, direction normalization, translation invariance, coordinate-frame
consistency, invalid inputs, and proper handling of reflected point sets.

See [docs/STAGE3_DERIVATIONS.md](docs/STAGE3_DERIVATIONS.md) for the full derivation
and expected marker/tip/axis coordinates. Measured outputs are in
[results/STAGE3_RESULTS.md](results/STAGE3_RESULTS.md) and registration_summary.json.

## Task 3: biopsy planning

`plan_biopsy(tumor_center, tumor_radius, tip_ct, axis_ct)` takes a spherical
target and the registered tip/axis in the CT frame. It returns the perpendicular
axis-to-centre distance, forward harvestable core length, and insertion depth to
the far end of the core. All distances are in mm. The input axis is normalized.
Reusable line-distance and line/sphere-intersection utilities live in geometry.py.

For unit direction v, let a=(C-P) dot v and d=||(C-P) cross v||. When d<r,
the line intersection depths are a +/- sqrt(r^2-d^2). Clip to nonnegative
depths to model forward insertion. The approach distance before the tumor is
included in total insertion depth but excluded from core length.

A tangent has zero core and reports the depth to contact. A miss or backward-only
intersection has zero core and no feasible depth (None / JSON null / N/A). A tip
inside the sphere can harvest only the remaining forward segment. The
`harvest_possible` flag distinguishes actual positive-length core from contact.
The 1e-9 mm default numerical tolerance is not a clinical margin.

All seven reference cases pass: intersection, tangency, miss, behind-only,
inside, initial-surface inward, and initial-surface outward. Twelve added tests
also cover 3D orientation/translation invariance, direction normalization,
invalid inputs, and numerical tangency. See [worked calculations](docs/STAGE4_DERIVATIONS.md)
and [results](results/STAGE4_RESULTS.md). The scenario plot is
results/planning_scenarios.png. This idealized line model does not model needle
diameter, the cutting mechanism, or deformation.

## Task 4: targeting-error simulation

At 100 mm insertion depth, independently perturb all three CT markers, re-register
the tool, and compare its inferred trajectory to an independently displaced target.
Target displacement sigma runs from 0 to 3 mm in 0.1 mm steps, with 200,000 trials
per level. Separate random streams generate marker and target errors. Common
random numbers pair levels; trials within each level remain independent.

The primary metric is point-to-line distance. Endpoint error after exactly 100 mm
insertion is also reported to address the assignment's alternate wording. Marker
coordinate sigma remains 0.357720 mm. The known model tip/axis are held fixed;
calibration uncertainty from Task 1 is not added to this separate experiment.

**Result: no feasible target-displacement tolerance from zero.** Marker noise
alone gives about 62.17% of trajectories within 3 mm, with p95 error 5.639 mm,
versus the required 95%. An independent baseline gives 62.44%. Every sampled
sigma fails. Zero itself fails, so the maximum is reported as null, not 0 mm.
The finite grid is not claimed to prove behavior at every unsampled sigma.
The roughly 300 mm marker-to-target lever arm amplifies small angular errors.

**What would be needed.** Repeating the zero-displacement simulation with lower
marker noise shows the requirement is met only when marker sigma is at most
0.190 mm per coordinate, that is, when 95% of 3D marker errors are below about
0.53 mm: roughly half the 1 mm specified. Any target displacement would require
even more accurate marker localization.

Both metrics include pointwise Wilson confidence intervals. Those intervals
quantify Monte Carlo uncertainty and are separate from the 95% success criterion.
See [full methodology](docs/STAGE5_METHODS.md), [results](results/STAGE5_RESULTS.md),
and the two plots in results/. Eight tests validate batched registration
against the scalar API, analytic target-only distributions, exact zero errors,
Wilson intervals, reproducibility, sweep status, and invalid inputs.

## Files

Result and derivation files keep the project's original stage numbering:
STAGE2 is Task 1 (calibration), STAGE3 is Task 2 (registration), STAGE4 is
Task 3 (planning), and STAGE5 is Task 4 (targeting).

| File | Purpose |
|---|---|
| config.py | Figure geometry, unit assumption, noise scale, seed |
| geometry.py | Validation, plane and circle fitting, point-to-line distance, line/sphere intersection |
| transforms.py | Marker-frame construction and point transforms |
| registration.py | Rigid fit and register_tool API for CT tip/axis |
| calibration.py | Pivot (tip) and spin (axis) calibration solvers and diagnostics |
| simulation.py | Ground-truth pivot and spin observations |
| planning.py | Forward biopsy-plan calculations and reachability |
| error_analysis.py | Noisy registration, compound errors, sweep, confidence intervals |
| demo_flow.py | Entry point: guided walkthrough, or batch runs with --stage |
| batch_demo.py | Noninteractive calculation and result generation |
| interactive_demo.py | Guided walkthrough, rotatable tool views, clickable planner |
| registration_cases.py, planning_cases.py | Independent hand-derived reference cases |
| registration_demo.py, planning_demo.py, targeting_demo.py | Per-task validation and result generation |
| tests/ | 42 unittest tests, including an end-to-end calibration-to-planning test |
| FINAL_REPORT.md | Consolidated report for all assignment tasks |
| docs/STAGE1_DESIGN.md | Design decisions: geometry, frames, methods |
| docs/STAGE3_DERIVATIONS.md | Registration hand calculations and frame conventions |
| docs/STAGE4_DERIVATIONS.md | Planning formulas, worked examples, output conventions |
| docs/STAGE5_METHODS.md | Targeting simulation equations, design, interpretation |
| docs/RUBRIC_REVIEW.md | Criterion-by-criterion mapping to code and evidence |
| reference/HW-Bone-Biopsy-Planning.pdf | Original assignment and rubric |
| results/STAGE2_RESULTS.md ... STAGE5_RESULTS.md | Measured results and interpretation for each task |
| results/*.json, *.csv, *.npz | Full settings, per-trial errors, and sample inputs |
| results/*.png | Calibration errors, marker noise, planning scenarios, targeting sweep and CDF |
| results/demo_log.txt, test_log.txt, targeting_log.txt | Console output of the last full run |

The NPZ arrays can be inspected with numpy.load. Their names state their frames
and units; the marker template and observations are sufficient to rerun the
calibration functions. Rerunning the demo replaces generated result files
reproducibly for the supplied seed and software versions.

## Limits

This is a simulated course exercise, not clinical guidance or validated navigation
software. It assumes rigid tools, known marker correspondence and geometry,
independent isotropic error, a fixed pivot, and a tool that spins only about its
own shaft during axis calibration. No CT images, segmentation tools, or external
datasets are required.

## AI attribution

Parts of this project were developed with help from Claude (Anthropic), an AI
assistant. It was used to review the code against the assignment rubric,
implement the spin-based tool-axis calibration with plane and circle fitting,
compute the marker accuracy needed to meet the targeting requirement, and
reorganise the documentation. All AI-assisted code and text were reviewed by
the team and tested with the full test suite and the reproducible results above.
