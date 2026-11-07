"""Forward biopsy planning for a point tip and straight axis through a sphere."""
from geometry import vector3, unit, point_line_distance, intersect_line_sphere


def plan_biopsy(tumor_center, tumor_radius, tip_ct, axis_ct, tolerance=1e-9):
    """Return targeting error, reachable core length, and far-end insertion depth.

    All distances are mm when inputs are mm. The direction is normalized, so
    insertion distances do not depend on the input vector's magnitude.
    For a tangent, depth is distance to contact and core length is zero.
    For a miss/behind-only sphere, depth is None (JSON null), not zero.
    A tip inside the sphere can harvest only the forward portion of the chord.
    """
    p, c, v = vector3(tip_ct), vector3(tumor_center), unit(axis_ct)
    roots = intersect_line_sphere(p, v, c, tumor_radius, tolerance)
    out = {'targeting_error_mm': point_line_distance(c,p,v),
           'core_length_mm': 0., 'insertion_depth_mm': None,
           'entry_depth_mm': None, 'line_intersections_mm': roots,
           'status': 'miss', 'harvest_possible': False,
           'entry_point_ct_mm': None, 'end_point_ct_mm': None}
    if roots is None:
        return out
    near, far = roots
    if far < -tolerance:
        out['status'] = 'behind'
        return out
    # Values within tolerance of zero are treated as contact at the initial tip.
    end = max(0., far)
    start = max(0., near)
    if end < start:
        end = start
    length = end-start
    out.update(core_length_mm=length, insertion_depth_mm=end, entry_depth_mm=start,
               entry_point_ct_mm=p+start*v, end_point_ct_mm=p+end*v,
               harvest_possible=bool(length > 0),
               status='intersects' if length > 0 else 'contact')
    return out

# Author: Serhat Yaylacam
