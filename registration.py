"""Rigid registration and tool-to-CT transformation."""
import numpy as np
from geometry import points

def rigid_registration(source, target):
    """Fit corresponding labeled points, rejecting collinear configurations.

    Three noncollinear markers are planar but still determine a proper rotation.
    The determinant correction prevents an improper reflection.
    """
    a, b = points(source), points(target)
    if a.shape != b.shape:
        raise ValueError("Correspondence arrays must have matching shapes")
    ac, bc = a-a.mean(0), b-b.mean(0)
    if np.linalg.matrix_rank(ac) < 2 or np.linalg.matrix_rank(bc) < 2:
        raise ValueError("Markers must be noncollinear")
    u, _, vt = np.linalg.svd(ac.T @ bc)
    d = np.diag([1.,1.,np.linalg.det(vt.T @ u.T)])
    r = vt.T @ d @ u.T
    return r, b.mean(0)-r@a.mean(0)


def register_tool(markers_tool, tip_tool, axis_tool, markers_ct):
    """Register a tool tip and signed unit axis into CT coordinates.

    All positions use the same physical units. Marker rows must correspond
    (M1, M2, M3). Tip and axis must be expressed in the template's frame.
    Extra corresponding markers are supported by the same least-squares fit.
    """
    from geometry import unit
    tip = np.asarray(tip_tool, dtype=float)
    if tip.shape != (3,) or not np.isfinite(tip).all():
        raise ValueError("Tool tip must be a finite 3-vector")
    axis = unit(axis_tool)
    rotation, translation = rigid_registration(markers_tool, markers_ct)
    fitted = np.asarray(markers_tool) @ rotation.T + translation
    residual = fitted - np.asarray(markers_ct)
    return {
        'tip_ct': rotation @ tip + translation,
        'axis_ct': unit(rotation @ axis),
        'rotation': rotation,
        'translation': translation,
        'marker_residual_rms': float(np.sqrt(np.mean(np.sum(residual**2, axis=1)))),
    }

# Author: Serhat Yaylacam
