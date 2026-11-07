# Cumulative project progress

Current checkpoint: Stages 1-6 complete; final cumulative package prepared.

| Stage | Completed deliverables | Validation |
|---|---|---|
| 1: Design | Units, tool geometry, frames, methods, architecture, six-stage plan | Figure coordinates inspected; assumptions documented and approved |
| 2: Calibration | Tip/axis solvers, simulations, plots, sample observations, CSV/JSON results | 7 calibration tests; 500 noisy repetitions; exact recovery at numerical precision |
| 3: Registration | CT tip/axis API, three literal reference cases, hand derivations, results | 8 additional tests; 15 cumulative passing tests; all three reference cases agree |
| 4: Biopsy planning | Geometry utilities, planner, seven reference cases, derivations, plot, CSV/JSON results | 12 added tests; 27 cumulative passing tests; all seven planning cases agree |
| 5: Targeting simulation | Error propagation, 31-level sigma sweep, independent baseline, plots, data and methodology | 8 added tests; 35 total; 200,000 trials per sigma; no feasible tolerance from zero |
| 6: Final review | Rubric mapping, consolidated report, setup guide, author tags, final package | 36 passing tests including end-to-end integration; complete demo succeeds |

## Current measured calibration results

With the documented centimetre interpretation and 80 poses per calibration:
mean tip error 0.348836 mm, empirical 95th percentile 0.617251 mm;
mean axis error 0.076342 degrees, empirical 95th percentile 0.151196 degrees.
See results for the full settings, raw trial errors, and limitations.

## Documentation correction after Stage 3

The earlier Stage 3 ZIP already included Stage 2 code and results, but its README
title mentioned only Stages 2 and 3. The current master README explicitly includes
Stage 1 and all completed work. The Stage 1 design is now a standalone document;
previous Stage 2 and Stage 3 READMEs are preserved in docs/history. The original
assignment PDF is included under reference. No solver code changed in this
packaging/documentation update; the existing validation logs remain applicable.

## Stage 4 update

Added forward sphere-intersection planning. Tangency reports a contact depth but
no core; miss/behind cases report no feasible depth. Earlier code, derivations,
results, assignment PDF, and historical READMEs are retained. The master README
now covers Stages 1-4. Shared geometry and demo modules were extended; the full
27-test suite validates both earlier work and planning.

## Stage 5 update

Completed the requested simulation with the approved geometry and noise.
Baseline success is 0.621670 (95% Wilson interval 0.619542 to 0.623793),
with trajectory p95 error 5.639103 mm. A separate run confirms failure.
All target-sigma levels from 0 to 3 mm fail. No feasible tolerance is reported;
zero must not be described as a passing maximum. Endpoint results are separate.
Earlier files remain present; the master README now covers Stages 1-5.

## Final status

All planned stages are complete. All project Python scripts and tests carry the
requested author tag. The complete assignment workflow has been validated.
START_HERE.md provides run and submission instructions. The unit assumption and
unsatisfied simulated clinical criterion remain explicit; no grade or clinical
validation is claimed. Course-portal submission has not been performed.

Future deliveries must extend this complete directory and update the master
README and this progress record, preserving earlier stages' useful materials.

## Interactive presentation update

Added a no-argument guided demo, live exact calculations, saved plot viewing,
and a two-click synthetic planner. The former batch implementation is retained
in batch_demo.py. All 39 tests pass, including three click-handler tests.
Every Python file retains the requested author tag.
