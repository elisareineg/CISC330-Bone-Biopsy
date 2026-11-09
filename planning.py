"""Forward biopsy planning for a point tip and straight axis through a sphere."""
from geometry import vector3, unit, point_line_distance, intersect_line_sphere

def plan_biopsy(tumor_center, tumor_radius, tip_ct, axis_ct, tolerance=1e-9):
    """Calculate targeting error, tissue core length, and insertion depth.

    Distances are in mm when inputs are in mm. The needle advances
    only forward. Misses and behind-only intersections have no
    insertion depth; tangencies have zero core length."""

    tip = vector3(tip_ct)
    center = vector3(tumor_center)
    axis = unit(axis_ct)

    # Calculate targeting error and line-sphere intersections
    targeting_error = point_line_distance(center, tip, axis)
    intersections = intersect_line_sphere(
        tip, axis, center, tumor_radius, tolerance
    )

    # Default result for a trajectory that misses the tumor
    result = {
        "targeting_error_mm": targeting_error,
        "core_length_mm": 0.0,
        "insertion_depth_mm": None,
        "entry_depth_mm": None,
        "line_intersections_mm": intersections,
        "status": "miss",
        "harvest_possible": False,
        "entry_point_ct_mm": None,
        "end_point_ct_mm": None
    }

    # No intersection with the infinite needle axis
    if intersections is None:
        return result

    near, far = intersections

    # Tumor lies entirely behind the needle tip
    if far < -tolerance:
        result["status"] = "behind"
        return result

    # Restrict the intersection to the forward needle trajectory
    entry_depth = max(0.0, near)
    end_depth = max(0.0, far)

    if end_depth < entry_depth:
        end_depth = entry_depth

    # Length of the needle trajectory inside the tumor
    core_length = end_depth - entry_depth

    result.update({
        "core_length_mm": core_length,
        "insertion_depth_mm": end_depth,
        "entry_depth_mm": entry_depth,
        "entry_point_ct_mm": tip + entry_depth * axis,
        "end_point_ct_mm": tip + end_depth * axis,
        "harvest_possible": bool(core_length > 0),
        "status": "intersects" if core_length > 0 else "contact"
    })

    return result


# Author: Akshay Kapal, Serhat Yaylacam
