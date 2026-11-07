# Bone Biopsy Planning: Stages 2 and 3

CISC/CMPE 330, CT-guided Bone Biopsy Planning.
This cumulative checkpoint implements tool calibration, CT registration, and
three hand-derived registration validations. It is not the complete assignment.
Biopsy planning and targeting-error simulation remain for Stages 4 and 5.

## Run on Windows (PowerShell)

The ZIP contains a BoneBiopsyPlanning folder. Copy the CONTENTS of that folder
into your existing C:\Desktop\CISC 330\Assignments\project2 folder, replacing
matching project files. Keep your existing .venv. No new dependencies are needed.
The included generated results are from the supplied validation run; rerun to
replace them with results from your own environment.

```powershell
cd "C:\Desktop\CISC 330\Assignments\project2"
# Only for a fresh installation without an existing .venv:
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe demo_flow.py --trials 500
```

For an existing Stage 2 installation, skip environment creation and installation.
Run the test command above, then run just Stage 3:

```powershell
.\.venv\Scripts\python.exe demo_flow.py --stage registration
```

The default `--stage all` runs calibration and registration. Use
`--stage calibration --trials 500` to rerun calibration alone.
No environment activation or PowerShell execution-policy changes are needed.
If extracted elsewhere, adjust the first path. Python 3.11 or newer is recommended;
the included run was verified on Python 3.12. Use the generated JSON for exact
package versions. On Linux/macOS, use `.venv/bin/python` instead.
Tests use Python's built-in unittest, so pytest is not required.

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

## Calibration formulation and constraints

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

### Axis: constrained translation calibration

Slide the tool forward through a straight guide aligned with its shaft, while
holding orientation fixed. The marker centroid follows a line parallel to the
shaft. Fit this line using total least squares (SVD of centred centroids).
The first-to-last displacement determines the insertion sign. Average the
measured rotations and map the fitted tracker direction back into marker space.

This uses 80 positions over a 100 mm stroke at a nontrivial fixed orientation.
No true tip or axis is passed into either calibration solver. The simulator
knows ground truth; the solver receives only marker templates and observations.
No-motion data are rejected. The reported orientation RMS is a diagnostic for
the fixed-orientation constraint; the solver cannot prove that a real guide is
aligned with the physical shaft. The ordered forward-motion convention resolves
an ambiguity that an unordered line fit cannot resolve.

## Gaussian tracker error

Every coordinate of every marker receives independent N(0,sigma^2) error.
For isotropic 3D error, ||error||^2/sigma^2 has a chi-square distribution with
three degrees of freedom. Therefore:

    sigma = 1 mm / sqrt(chi2.ppf(0.95, 3)) = approximately 0.358 mm

Using 1/1.96 mm would describe a 1D coordinate interval and is incorrect for
this 3D magnitude requirement. The demo checks the radial error on 200,000
independent draws and runs 500 independent calibration repetitions. Random
streams are seeded and separated. Repetitions regenerate both motions and noise.

## Files and outputs

| File | Purpose |
|---|---|
| config.py | Figure geometry, unit assumption, noise scale, seed |
| geometry.py | Validation, normalization, line fitting, angular error |
| transforms.py | Marker-frame construction and point transforms |
| registration.py | Rigid fit and register_tool API for CT tip/axis |
| registration_cases.py | Three independently calculated reference cases |
| registration_demo.py | Registration validation and result generation |
| tests/test_registration.py | Required cases and additional safeguards |
| STAGE3_DERIVATIONS.md | Hand calculations, method, and frame conventions |
| results/STAGE3_RESULTS.md | Measured registration validation errors |
| results/registration_summary.json | Complete expected/computed registration values |
| calibration.py | Tip and axis solvers and diagnostics |
| simulation.py | Constrained ground-truth observations |
| demo_flow.py | Exact/noisy experiments and output generation |
| tests/test_calibration.py | Exact recovery, arbitrary geometry, failure cases |
| requirements.txt | Runtime dependencies |
| results/STAGE2_RESULTS.md | Measured results and interpretation |
| results/calibration_summary.json | Detailed results, settings, versions |
| results/calibration_trials.csv | All repeated-calibration errors |
| results/example_observations.npz | Exact and noisy example input arrays |
| results/calibration_errors.png | Tip/axis error distributions |
| results/marker_noise.png | Radial marker-noise distribution |
| results/test_log.txt | Captured test output |

The NPZ arrays can be inspected with numpy.load. Their names state their frames
and units; the marker template and observations are sufficient to rerun the
calibration functions. Full trial errors are preserved in CSV. Rerunning the
demo replaces generated result files reproducibly for the supplied seed and
software versions.

## Rubric coverage and remaining work

Stage 2 addresses calibration formulation, tip and axis methods, motion
constraints, ground-truth generation, perfect-data validation, Gaussian marker
noise, quantified errors, and reusable documented modules.

Stage 3 now covers rigid registration, tip and direction transforms, three
hand-derived cases, and numerical agreement. See STAGE3_DERIVATIONS.md.
Stage 4 will
add sphere/trajectory planning and intersection/tangent/miss tests. Stage 5 will
add target displacement and determine whether any positive displacement sigma
satisfies the targeting requirement. That conclusion must be measured, not assumed.

Future planning uses forward insertion along v. Targeting error is point-to-line
distance, core length is the reachable spherical chord, and insertion depth is
the distance to its far endpoint. Backward-only intersections cannot be harvested.
The final simulation will distinguish trajectory distance from endpoint error
after 100 mm insertion because the assignment uses both phrasings.

## Limits

This is a simulated course exercise, not clinical guidance or validated navigation
software. It assumes rigid tools, known marker correspondence and geometry,
independent isotropic error, a fixed pivot, and an aligned translation guide.
No CT images, segmentation tools, or external datasets are required for Stage 2.
