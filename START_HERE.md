# Final cumulative project: start here

Author: Serhat Yaylacam

This directory contains all six workflow stages and all four assignment tasks.
The software is complete for the supplied assignment; the simulated targeting
requirement is not met under the documented assumptions. That finding is fully
reported and does not mean the tests failed.

## Existing Windows installation

Copy the contents of the archive's BoneBiopsyPlanning folder into:

    C:\Desktop\CISC 330\Assignments\project2

Replace matching project files and keep your existing .venv. No new dependencies
are required. Do not place the whole folder inside project2 unless you intend
to change the working path. Historical files are included in docs/history.

Run each command separately in PowerShell:

```powershell
cd "C:\Desktop\CISC 330\Assignments\project2"
```

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

```powershell
.\.venv\Scripts\python.exe demo_flow.py --stage all --trials 500 --targeting-trials 200000
```

Expected: 39 tests pass; all three registration and all seven planning cases
pass; targeting reports no feasible tolerance starting from zero. Minor
floating-point differences across systems are expected. Fixed-seed results
should be close to the included reports.

## Interactive presentation

To walk through the assignment with pauses, figure windows, and a clickable
planning exercise, run this command by itself:

```powershell
.\.venv\Scripts\python.exe .\demo_flow.py
```

Press Enter when prompted. Close each plot to continue. In the planner, click
the starting needle tip, then an aiming point. Results appear immediately.
Click Reset to try another path or Continue to move on. This uses a synthetic
XY sphere view, not real CT images. A GUI-capable Python/Matplotlib installation
is required. There are no new Python package dependencies.

Use the explicit --stage all command above when you want to regenerate results
without pausing. Use the .venv interpreter rather than base Python to ensure
the installed dependencies are used.

## Fresh installation

After changing into the extracted directory, first run these separately:

```powershell
python -m venv .venv
```

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Then use the test and demo commands above. Dependencies are NumPy, SciPy, and
Matplotlib; unittest is built into Python. Tested Python/package versions are
recorded in the generated JSON summaries. A system with working versions from
an earlier stage can continue using them.

## Reading and submission materials

1. FINAL_REPORT.md: concise report of all methods, results, and conclusions.
2. README.md: full cumulative technical guide covering Stages 1-6.
3. RUBRIC_REVIEW.md: evidence for every criterion in the supplied rubric.
4. STAGE3_DERIVATIONS.md and docs/: detailed design, hand calculations, and methods.
5. results/: all generated reports, plots, trial data, and verification logs.
6. Python source and tests/: implementation and executable validation.
7. reference/: original assignment PDF; docs/history/: earlier README snapshots.

The archive contains the whole cumulative project without .venv, bytecode caches,
or downloaded helper tools. It does not contain credentials or require network
access during computation. Package installation may require internet access.
Rename the ZIP only if your course portal specifies a filename. No submission
has been uploaded to the course portal by this workflow.

Every Python source/test file ends with '# Author: Serhat Yaylacam'.
