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

def axis_observations(template, axis, rng, n=80, sigma=0.):
    if n < 3 or sigma < 0:
        raise ValueError("Invalid sample count or noise")
    rotation = Rotation.from_euler('xyz',[25.,-20.,35.],degrees=True).as_matrix()
    # Fixed orientation and an ordered 100 mm forward translation.
    translations = np.array([30.,40.,-15.])+np.outer(np.linspace(0,100,n),rotation@axis)
    exact = np.array([transform_points(template,rotation,t) for t in translations])
    return exact+rng.normal(0,sigma,exact.shape), rotation, translations

# Author: Serhat Yaylacam
