"""Rigid registration and tool-to-CT transformation."""
import numpy as np
from geometry import points


def rigid_registration(source, target):
    """Compute the rigid transformation between corresponding 3D markers."""

    source_points = points(source)
    target_points = points(target)

    if source_points.shape != target_points.shape:
        raise ValueError("Source and target marker arrays must have matching shapes")

    # Calculate the centroid of each marker set
    source_centroid = np.mean(source_points, axis=0)
    target_centroid = np.mean(target_points, axis=0)

    # Center the marker coordinates
    source_centered = source_points - source_centroid
    target_centered = target_points - target_centroid

    # Reject collinear marker configurations
    if (np.linalg.matrix_rank(source_centered) < 2 or
            np.linalg.matrix_rank(target_centered) < 2):
        raise ValueError("Markers must be noncollinear")

    # Calculate the covariance matrix
    covariance = source_centered.T @ target_centered

    # Perform singular value decomposition
    U, _, Vt = np.linalg.svd(covariance)

    # Recover the rotation matrix
    rotation = Vt.T @ U.T

    # Correct for reflections
    if np.linalg.det(rotation) < 0:
        Vt[-1, :] *= -1
        rotation = Vt.T @ U.T

    # Calculate the translation vector
    translation = target_centroid - rotation @ source_centroid

    return rotation, translation



def register_tool(markers_tool, tip_tool, axis_tool, markers_ct):
    """Transform the biopsy tool tip and axis into CT coordinates.

    Marker coordinates must correspond and use consistent units.
    The tip and axis must be expressed in the tool's coordinate frame.
    """

    from geometry import unit

    # Validate the tool tip
    tip = np.asarray(tip_tool, dtype=float)

    if tip.shape != (3,) or not np.all(np.isfinite(tip)):
        raise ValueError("Tool tip must be a finite 3D point")

    # Normalize the tool axis
    axis = unit(axis_tool)

    # Determine the tool-to-CT transformation
    rotation, translation = rigid_registration(markers_tool, markers_ct)

    # Transform the tip and axis
    tip_ct = rotation @ tip + translation
    axis_ct = unit(rotation @ axis)

    # Transform the original markers to check registration accuracy
    transformed_markers = np.asarray(markers_tool) @ rotation.T + translation
    observed_markers = np.asarray(markers_ct)

    # Calculate root mean square registration error
    differences = transformed_markers - observed_markers
    squared_distances = np.sum(differences ** 2, axis=1)
    rms_error = float(np.sqrt(np.mean(squared_distances)))

    return {
        "tip_ct": tip_ct,
        "axis_ct": axis_ct,
        "rotation": rotation,
        "translation": translation,
        "marker_residual_rms": rms_error
    }


# Author: Akshay Kapal, Serhat Yaylacam
