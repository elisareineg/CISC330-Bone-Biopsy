"""Ground truth is used only here to synthesize measurements and in validation."""
import numpy as np
from scipy.spatial.transform import Rotation
from transforms import transform_points

def pivot_observations(template, tip, rng, n=80, sigma=0.):
    if n < 3 or sigma < 0:
        raise ValueError("Invalid sample count or noise")
    # Rich multi-axis tilts: three independently varying rotation-vector components.
    rotations = Rotation.from_rotvec(rng.uniform(-0.9,0.9,(n,3))).as_matrix()
    pivot = np.array([45.,-30.,75.])
    translations = pivot-np.einsum('nij,j->ni',rotations,tip)
    exact = np.array([transform_points(template,r,t) for r,t in zip(rotations,translations)])
    return exact+rng.normal(0,sigma,exact.shape), rotations, translations, pivot

def axis_observations(template, axis, tip, rng, n=80, sigma=0., span_deg=360.):
    """Spin the tool about its own shaft with the tip held in a divot.

    The shaft keeps a fixed (nontrivial) tracker direction; only the spin angle
    about it changes, over span_deg degrees. Markers therefore trace circles
    around the shaft. Returns noisy observations, rotations, translations, divot.
    """
    if n < 3 or sigma < 0 or not 0 < span_deg <= 360:
        raise ValueError("Invalid sample count, noise, or spin span")
    base = Rotation.from_euler('xyz',[25.,-20.,35.],degrees=True).as_matrix()
    shaft = base@np.asarray(axis,dtype=float)/np.linalg.norm(axis)
    divot = np.array([30.,40.,-15.])
    angles = np.radians(np.linspace(0, span_deg, n, endpoint=span_deg < 360))
    rotations = Rotation.from_rotvec(np.outer(angles, shaft)).as_matrix()@base
    translations = divot-np.einsum('nij,j->ni', rotations, tip)
    exact = np.array([transform_points(template,r,t) for r,t in zip(rotations,translations)])
    return exact+rng.normal(0,sigma,exact.shape), rotations, translations, divot

# Author: Serhat Yaylacam
