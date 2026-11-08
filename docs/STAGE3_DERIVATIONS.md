# Stage 3: rigid registration, worked predictions, and validation

## Inputs and outputs

Input: three labeled markers M1tool, M2tool, M3tool; tip Ptool; direction vtool;
and their corresponding CT markers M1ct, M2ct, M3ct. All tool quantities must
use the same source frame. All point coordinates must use the same units.

Output: Pct = R Ptool + t and vct = R vtool, normalized to unit length.
register_tool additionally returns R, t, and the RMS marker-fit residual.
The returned dictionary keys are tip_ct, axis_ct, rotation, translation,
and marker_residual_rms. This residual has the input length unit (mm here).

The template is fixed and its correspondence labels are known. With noisy CT
markers, the transformation minimizes the sum of squared marker residuals.
The tip and axis must come from calibration expressed in this same template
frame, or from the ground-truth model for these validation cases.

## Rigid fit by SVD

1. Compute source and destination centroids a_bar and b_bar.
2. Centre each set: A_i = a_i - a_bar, B_i = b_i - b_bar.
3. Form H = A.T @ B and its SVD H = U S V.T.
4. Set D = diag(1, 1, det(V @ U.T)).
5. Set R = V @ D @ U.T and t = b_bar - R @ a_bar.
6. Transform the tip with R and t; transform the direction with R only.

The determinant correction enforces a right-handed rigid rotation. The model
triangle has rank two, which is sufficient: two independent directions fix
an oriented plane, and their cross product fixes its normal. Collinear points
have rank less than two and are rejected. A very narrow triangle can still
be poorly conditioned even if numerical rank is two.

## Ground truth

Using the documented centimetre assumption, convert the figure to mm:

    M1 = (20, 180, 0)
    M2 = (80, 180, 0)
    M3 = (20, 240, 0)
    P  = (0, 0, 0)
    v  = (0, -1, 0)

The following CT markers and predicted outputs are obtained by the coordinate
rules shown below, before running registration. registration_cases.py contains
these expectations explicitly, independently of the transform implementation.
It scales the diagram coordinates if DIAGRAM_UNIT_TO_MM is changed; translations
remain fixed in mm. Numeric tables below correspond to the default scale of 10.

## Case 1: pure translation

R = I; t = (30, -40, 50) mm.
The point mapping is (x,y,z) -> (x+30, y-40, z+50).

| Quantity | Expected CT value |
|---|---|
| M1 | (50, 140, 50) mm |
| M2 | (110, 140, 50) mm |
| M3 | (50, 200, 50) mm |
| Tip | (30, -40, 50) mm |
| Axis | (0, -1, 0) |

The axis remains unchanged because translation does not change a direction.

## Case 2: pure rotation

Rotate +90 degrees about the model origin's z axis using the right-hand rule.
R has rows (0,-1,0), (1,0,0), (0,0,1); t=(0,0,0).
The point mapping is (x,y,z) -> (-y,x,z).

| Quantity | Expected CT value |
|---|---|
| M1 | (-180, 20, 0) mm |
| M2 | (-180, 80, 0) mm |
| M3 | (-240, 20, 0) mm |
| Tip | (0, 0, 0) mm |
| Axis | (1, 0, 0) |

The tip remains at the origin because the rotation is about that origin.
The marker coordinates and axis still provide nontrivial checks of rotation.

## Case 3: rotation and translation

Use the cyclic rotation (x,y,z) -> (z,x,y), followed by t=(10,-20,30) mm.
R has rows (0,0,1), (1,0,0), (0,1,0). This is a proper rotation of
+120 degrees about (1,1,1)/sqrt(3). The point mapping is:

    (x,y,z) -> (z+10, x-20, y+30)

| Quantity | Expected CT value |
|---|---|
| M1 | (10, 0, 210) mm |
| M2 | (10, 60, 210) mm |
| M3 | (10, 0, 270) mm |
| Tip | (10, -20, 30) mm |
| Axis | (0, 0, -1) |

The marker plane changes from XY to YZ. The axis mapping is
(0,-1,0) -> (0,0,-1), with no translation added.

## Extra checks beyond the three assignment cases

- A hypothetical nonzero tip (4,5,6) must map in Case 3 to (16,-16,35).
  This catches implementations that transform the origin correctly but omit
  rotation of general tips.
- A non-unit input axis is normalized; adding CT translation leaves it unchanged.
- Using the marker frame instead of the model frame gives the same CT tip and
  axis when all source quantities are converted consistently.
- Non-finite tips, zero axes, mismatched correspondence counts, and collinear
  marker sets are rejected.
- A reflected noncoplanar point set cannot be fitted by silently returning an
  improper rotation. The returned rotation must still have determinant +1.

## Numerical agreement

Run `python registration_demo.py` or `python demo_flow.py --stage registration`.
The report checks each entry of R, t, Pct, and vct against the independent
prediction with absolute tolerance 1e-10 and zero relative tolerance. It also
requires marker RMS below 1e-10 mm. Failure raises an exception.
See results/STAGE3_RESULTS.md for measured discrepancies and
results/registration_summary.json for complete expected and computed values.

## Connecting to Stage 2

calibrate_tip and calibrate_axis return quantities in their input template frame.
In the Stage 2 demo, this is the marker frame. Either:

1. Register that marker-frame template and calibrated marker-frame tip/axis
   directly to CT marker observations; or
2. Convert the calibration to model coordinates first with
   p_model = B @ p_marker + origin and v_model = B @ v_marker, then register
   using MARKERS_MODEL.

Both give the same CT result. The dedicated frame-consistency test checks this
relationship with exact values. The required three assignment cases use the
known model tip/axis so registration accuracy is evaluated separately from
calibration uncertainty. No marker localization from actual CT pixels is
implemented or required by this coordinate-based registration task.
