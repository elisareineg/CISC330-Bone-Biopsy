"""Active transforms: column p_out=R@p_in+t; arrays contain row points."""
import numpy as np
from geometry import points, unit

def transform_points(p, rotation, translation):
    return np.asarray(p) @ np.asarray(rotation).T + np.asarray(translation)

def marker_frame(markers):
    """Return origin and basis B: p_model = B @ p_marker + origin."""
    m = points(markers)
    if len(m) != 3:
        raise ValueError("Exactly three labeled markers required")
    x = unit(m[1]-m[0])
    y = unit((m[2]-m[0])-np.dot(m[2]-m[0],x)*x)
    return m[0].copy(), np.column_stack((x,y,np.cross(x,y)))

# Author: Serhat Yaylacam
