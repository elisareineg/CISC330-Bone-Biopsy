"""Calibration receives marker templates and observations, never the true tip/axis."""
import numpy as np
from scipy.spatial.transform import Rotation
from geometry import fit_line, unit
from registration import rigid_registration

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

def calibrate_axis(template, observations):
    """Translate along a straight shaft guide at fixed orientation.

    Observations must be ordered from retracted to advanced. The marker centroid
    moves along the shaft regardless of where the unknown tip lies. A TLS line
    fit estimates the tracker direction; the mean measured rotation maps it back
    to marker coordinates. No ground-truth axis is passed to this function.
    """
    rotations, _ = poses_from_markers(template, observations)
    centers = np.asarray(observations).mean(axis=1)
    center, axis, singular = fit_line(centers)
    forward = centers[-1]-centers[0]
    if np.linalg.norm(forward) < 1e-10 or abs(np.dot(axis,forward)) < 1e-10:
        raise ValueError("A nonzero ordered forward displacement is required")
    if np.dot(axis,forward) < 0:
        axis = -axis
    mean_rotation = Rotation.from_matrix(rotations).mean().as_matrix()
    deviations = Rotation.from_matrix(rotations @ mean_rotation.T).magnitude()
    off_line = centers-center-np.outer((centers-center)@axis,axis)
    return {"axis":unit(mean_rotation.T@axis),
            "translation_span_mm":float(np.ptp((centers-center)@axis)),
            "line_residual_rms_mm":float(np.sqrt(np.mean(np.sum(off_line**2,axis=1)))),
            "orientation_rms_deg":float(np.degrees(np.sqrt(np.mean(deviations**2)))),
            "line_singular_values":singular}

# Author: Serhat Yaylacam
