# Stage 3 CT registration results

Diagram unit to mm: 10. All positions and residuals are in mm.
Expected values are hand-derived in docs/STAGE3_DERIVATIONS.md.

| Case | Tip error (mm) | Axis error (degrees) | Marker RMS (mm) | Passed |
|---|---:|---:|---:|---|
| pure_translation | 7.10543e-14 | 1.59028e-14 | 2.00972e-14 | True |
| pure_rotation | 6.07088e-14 | 9.54166e-15 | 2.90802e-14 | True |
| rotation_and_translation | 5.68434e-14 | 1.59028e-14 | 7.39556e-15 | True |

All three cases check the recovered rotation and translation as well as
the transformed tip and axis. The combined case rotates the marker triangle
from the model XY plane into the CT YZ plane. Small residuals are numerical
roundoff, not physical localization errors. These are exact-data checks.
Noisy marker propagation will be quantified in Stage 5.
