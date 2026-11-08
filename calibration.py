"""Calibration receives marker templates and observations, never the true tip/axis."""
import numpy as np
from scipy.spatial.transform import Rotation
from geometry import fit_plane, fit_circle, unit
from registration import rigid_registration

# Smallest spin about the shaft accepted for axis calibration. Short arcs make the
# circle and plane fits poorly conditioned; a full turn is best.
MIN_SPIN_DEG = 30.0


def poses_from_markers(template, observations):
    obs = np.asarray(observations, dtype=float)
    if obs.ndim != 3 or obs.shape[1:] != np.asarray(template).shape or len(obs) < 3:
        raise ValueError("Expected at least three N-marker observations")
    poses = [rigid_registration(template, sample) for sample in obs]
    return np.array([p[0] for p in poses]), np.array([p[1] for p in poses])

def calibrate_tip(template, observations):
    """Pivot calibration: R_i p + t_i = c. Solve for unknown p and c.

    The tip must stay fixed in tracker coordinates. Tilt around multiple axes;
    rotating only about the shaft cannot identify the axial tip component.
    """
    rotations, translations = poses_from_markers(template, observations)
    a = np.vstack([np.column_stack((r,-np.eye(3))) for r in rotations])
    b = -translations.reshape(-1)
    solution, _, rank, singular = np.linalg.lstsq(a,b,rcond=None)
    if rank != 6:
        raise ValueError("Pivot poses do not sufficiently excite multiple rotation axes")
    residual = (a@solution-b).reshape(-1,3)
    return {"tip":solution[:3], "pivot":solution[3:], "rank":int(rank),
            "condition_number":float(singular[0]/singular[-1]),
            "residual_rms_mm":float(np.sqrt(np.mean(np.sum(residual**2,axis=1))))}

def calibrate_axis(template, observations, tip):
    """Spin calibration: rotate the tool about its own shaft and fit circles.

    Motion constraint: the tip stays in a divot while the shaft turns in a sleeve,
    so the tool rotates only about its own axis (no tilt, no axial sliding).
    Every marker then moves on a circle in a plane perpendicular to the shaft:

    1. Plane fit: all marker circles lie in parallel planes, so the common normal
       of the stacked, per-marker-centred trajectories is the axis direction in
       tracker coordinates.
    2. Circle fit: each marker's circle centre lies on the shaft, which locates
       the axis line (used for diagnostics).
    3. The shaft is invariant under the spin, R_i a = a_tracker for every pose,
       so a = mean_i(R_i^T a_tracker) expresses the axis in marker coordinates.
    4. A spin cannot tell which way the needle points. The calibrated tip (from
       calibrate_tip, in marker coordinates) fixes the sign: the axis points from
       the marker triangle toward the tip, i.e. the insertion direction.

    No ground-truth axis is passed to this function.
    """
    obs = np.asarray(observations, dtype=float)
    rotations, translations = poses_from_markers(template, obs)
    tip = np.asarray(tip, dtype=float)
    if tip.shape != (3,) or not np.isfinite(tip).all():
        raise ValueError("Calibrated tip must be a finite 3-vector")

    spin = Rotation.from_matrix(rotations @ rotations[0].T).magnitude()
    spin_deg = float(np.degrees(spin.max()))
    if spin_deg < MIN_SPIN_DEG:
        raise ValueError(f"Spin the tool at least {MIN_SPIN_DEG:g} degrees about its shaft")

    # 1. Common plane normal of all marker circles = axis direction (tracker frame)
    centred = obs - obs.mean(axis=0)
    _, axis_tracker, plane_singular = fit_plane(centred.reshape(-1, 3))

    # 2. Circle centres lie on the shaft
    circles = [fit_circle(obs[:, j]) for j in range(obs.shape[1])]
    centres = np.array([c[0] for c in circles])
    axis_point = centres.mean(axis=0)
    off_axis = centres-axis_point-np.outer((centres-axis_point)@axis_tracker, axis_tracker)

    # 3. Express the direction in marker coordinates
    axis = unit(np.mean(np.einsum('nji,j->ni', rotations, axis_tracker), axis=0))

    # 4. Resolve the sign with the calibrated tip
    toward_tip = float(np.dot(tip-np.asarray(template, dtype=float).mean(axis=0), axis))
    if abs(toward_tip) < 1e-9:
        raise ValueError("Axis sign is undefined: the tip is level with the marker centroid")
    if toward_tip < 0:
        axis = -axis

    # Diagnostic: the calibrated tip should lie on the fitted shaft line
    point_marker = np.mean(np.einsum('nji,nj->ni', rotations, axis_point-translations), axis=0)
    tip_offset = np.linalg.norm(np.cross(tip-point_marker, axis))

    return {"axis": axis,
            "axis_tracker": axis_tracker,
            "spin_span_deg": spin_deg,
            "circle_radii_mm": [c[1] for c in circles],
            "circle_residual_rms_mm": float(np.sqrt(np.mean([c[3]**2 for c in circles]))),
            "plane_residual_rms_mm": float(plane_singular[2]/np.sqrt(centred.reshape(-1, 3).shape[0])),
            "centre_line_residual_rms_mm": float(np.sqrt(np.mean(np.sum(off_axis**2, axis=1)))),
            "tip_offset_from_axis_mm": float(tip_offset)}

# Author: Serhat Yaylacam
