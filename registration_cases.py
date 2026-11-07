"""Hand-derived expectations, independent of the transform implementation.

Marker coordinates below are literal algebraic results, not generated using
transform_points or the fitted registration. Diagram scale is configurable;
translations are always stated in mm.
"""
import numpy as np
from config import DIAGRAM_UNIT_TO_MM


def registration_cases():
    s = DIAGRAM_UNIT_TO_MM
    return [
        {'name': 'pure_translation',
         'rotation': np.eye(3), 'translation': np.array([30., -40., 50.]),
         'markers_ct': np.array([[2*s+30,18*s-40,50],
                                 [8*s+30,18*s-40,50],
                                 [2*s+30,24*s-40,50]]),
         'tip_ct': np.array([30.,-40.,50.]), 'axis_ct': np.array([0.,-1.,0.])},
        {'name': 'pure_rotation',
         'rotation': np.array([[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]]),
         'translation': np.zeros(3),
         'markers_ct': np.array([[-18*s,2*s,0],[-18*s,8*s,0],[-24*s,2*s,0]]),
         'tip_ct': np.zeros(3), 'axis_ct': np.array([1.,0.,0.])},
        {'name': 'rotation_and_translation',
         'rotation': np.array([[0.,0.,1.],[1.,0.,0.],[0.,1.,0.]]),
         'translation': np.array([10.,-20.,30.]),
         'markers_ct': np.array([[10,2*s-20,18*s+30],
                                 [10,8*s-20,18*s+30],
                                 [10,2*s-20,24*s+30]]),
         'tip_ct': np.array([10.,-20.,30.]), 'axis_ct': np.array([0.,0.,-1.])},
    ]

# Author: Serhat Yaylacam
