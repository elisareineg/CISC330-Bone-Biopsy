"""Reusable geometric validation, fitting, distance, and intersection utilities."""
import numpy as np

def points(value, minimum=3):
    a = np.asarray(value, dtype=float)
    if a.ndim != 2 or a.shape[1] != 3 or len(a) < minimum or not np.isfinite(a).all():
        raise ValueError("Expected finite N x 3 points with sufficient samples")
    return a

def unit(vector):
    v = np.asarray(vector, dtype=float)
    if v.shape != (3,) or not np.isfinite(v).all() or np.linalg.norm(v) < 1e-12:
        raise ValueError("Expected a finite nonzero 3-vector")
    return v / np.linalg.norm(v)

def fit_plane(samples):
    """Total-least-squares plane through N >= 3 points.

    Returns (centroid, unit normal, singular values). The normal is the right
    singular vector with the smallest singular value; its sign is arbitrary.
    Points that are identical or collinear do not define a plane.
    """
    p = points(samples)
    centroid = p.mean(axis=0)
    _, s, vt = np.linalg.svd(p-centroid, full_matrices=False)
    if s[1] < 1e-10:
        raise ValueError("Plane fit requires at least three noncollinear points")
    return centroid, vt[2], s


def fit_circle(samples):
    """Least-squares circle through N >= 3 points lying (nearly) in a plane.

    Fit the plane first, express the points in 2D in-plane coordinates (x, y),
    then solve the algebraic (Kasa) circle x^2 + y^2 + D x + E y + F = 0 by
    linear least squares. Centre (-D/2, -E/2), radius sqrt(cx^2 + cy^2 - F).
    Returns (centre, radius, unit normal, radial residual RMS).
    """
    p = points(samples)
    centroid, normal, _ = fit_plane(p)
    _, _, vt = np.linalg.svd(p-centroid, full_matrices=False)
    e1, e2 = vt[0], vt[1]
    x, y = (p-centroid)@e1, (p-centroid)@e2
    a = np.column_stack((x, y, np.ones(len(p))))
    (d, e, f), _, rank, _ = np.linalg.lstsq(a, -(x**2+y**2), rcond=None)
    if rank < 3:
        raise ValueError("Circle fit requires at least three non-collinear points")
    cx, cy = -d/2, -e/2
    radius_squared = cx**2+cy**2-f
    if radius_squared <= 0:
        raise ValueError("Circle fit failed: points do not lie on a circle")
    centre = centroid+cx*e1+cy*e2
    radius = float(np.sqrt(radius_squared))
    residual = np.linalg.norm(p-centre-np.outer((p-centre)@normal, normal), axis=1)-radius
    return centre, radius, normal, float(np.sqrt(np.mean(residual**2)))

def angle_degrees(a, b):
    # atan2 remains accurate near zero, unlike acos of a rounded dot product.
    a, b = unit(a), unit(b)
    return float(np.degrees(np.arctan2(np.linalg.norm(np.cross(a,b)), np.dot(a,b))))


def vector3(value):
    """Validate a finite position/vector, allowing zero."""
    a = np.asarray(value, dtype=float)
    if a.shape != (3,) or not np.isfinite(a).all():
        raise ValueError('Expected a finite 3-vector')
    return a


def point_line_distance(point, origin, direction):
    """Shortest distance to the infinite axis, not the forward ray."""
    return float(np.linalg.norm(np.cross(vector3(point)-vector3(origin), unit(direction))))


def intersect_line_sphere(origin, direction, center, radius, tolerance=1e-9):
    """Return signed distances (near, far) along the unit direction, or None.

    Distances and tolerance have the input length unit (mm in this project).
    Tangencies within tolerance return a repeated root. These are LINE roots:
    the caller must restrict them to forward insertion (distance >= 0).
    """
    p, c, v = vector3(origin), vector3(center), unit(direction)
    radius = float(radius)
    tolerance = float(tolerance)
    if not np.isfinite(radius) or radius <= 0:
        raise ValueError('Sphere radius must be finite and positive')
    if not np.isfinite(tolerance) or tolerance < 0:
        raise ValueError('Tolerance must be finite and nonnegative')
    delta = c-p
    along = float(np.dot(delta, v))
    distance = point_line_distance(c, p, v)
    if distance > radius + tolerance:
        return None
    if abs(distance-radius) <= tolerance:
        return along, along
    # Product form avoids subtracting two large squared quantities near tangency.
    half_chord = float(np.sqrt(max(0., (radius-distance)*(radius+distance))))
    return along-half_chord, along+half_chord

# Author: Serhat Yaylacam
