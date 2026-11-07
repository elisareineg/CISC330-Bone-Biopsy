# Stage 3 CT registration results

Diagram unit to mm: 10. All positions and residuals are in mm.
Expected values are hand-derived in STAGE3_DERIVATIONS.md.

| Case | Tip error (mm) | Axis error (degrees) | Marker RMS (mm) | Passed |
|---|---:|---:|---:|---|
| pure_translation | 4.9738e-14 | 1.14404e-14 | 2.3566e-14 | True |
| pure_rotation | 7.55317e-14 | 1.66388e-14 | 1.93506e-14 | True |
| rotation_and_translation | 6.70325e-14 | 8.41461e-15 | 2.40082e-14 | True |

All three cases check the recovered rotation and translation as well as
the transformed tip and axis. The combined case rotates the marker triangle
from the model XY plane into the CT YZ plane. Small residuals are numerical
roundoff, not physical localization errors. These are exact-data checks.
Noisy marker propagation will be quantified in Stage 5.
