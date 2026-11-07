import unittest
import numpy as np
from geometry import intersect_line_sphere, point_line_distance
from planning import plan_biopsy
from planning_cases import planning_cases


class PlanningTests(unittest.TestCase):
    def check_case(self, index):
        c=planning_cases()[index]
        got=plan_biopsy(c['center'],c['radius'],c['tip'],c['axis'])
        for key,value in c['expected'].items():
            if value is None or isinstance(value,str): self.assertEqual(got[key],value)
            else: self.assertAlmostEqual(got[key],value,places=12)
        self.assertEqual(got['harvest_possible'],c['expected']['core_length_mm']>0)

    def test_intersecting_oblique_chord(self): self.check_case(0)
    def test_tangent(self): self.check_case(1)
    def test_miss(self): self.check_case(2)
    def test_backward_intersection(self): self.check_case(3)
    def test_tip_inside(self): self.check_case(4)
    def test_surface_inward(self): self.check_case(5)
    def test_surface_outward(self): self.check_case(6)

    def test_normalization(self):
        a=plan_biopsy([0,0,0],1,[-5,.6,0],[9,0,0])
        self.assertAlmostEqual(a['core_length_mm'],1.6)
        self.assertAlmostEqual(a['insertion_depth_mm'],5.8)

    def test_general_3d_rigid_invariance(self):
        # Orthonormal frame with a fully 3D axis; independent hand chord remains 1.6.
        u=np.array([1.,2.,2.])/3
        w=np.array([2.,-1.,0.])/np.sqrt(5)
        center=np.array([12.,-8.,34.])
        got=plan_biopsy(center,1,center-5*u+.6*w,u)
        self.assertAlmostEqual(got['targeting_error_mm'],.6)
        self.assertAlmostEqual(got['core_length_mm'],1.6)
        self.assertAlmostEqual(got['insertion_depth_mm'],5.8)
        self.assertAlmostEqual(np.linalg.norm(got['entry_point_ct_mm']-center),1.)
        self.assertAlmostEqual(np.linalg.norm(got['end_point_ct_mm']-center),1.)

    def test_line_distance_is_not_ray_distance(self):
        self.assertEqual(point_line_distance([0,0,0],[5,0,0],[1,0,0]),0.)
        self.assertEqual(plan_biopsy([0,0,0],1,[5,0,0],[1,0,0])['status'],'behind')

    def test_tangency_tolerance(self):
        self.assertEqual(intersect_line_sphere([-5,1+1e-10,0],[1,0,0],[0,0,0],1),(5.,5.))
        self.assertIsNone(intersect_line_sphere([-5,1+1e-7,0],[1,0,0],[0,0,0],1))
        roots=intersect_line_sphere([-5,1-1e-7,0],[1,0,0],[0,0,0],1)
        self.assertGreater(roots[1]-roots[0],0.)

    def test_bad_inputs(self):
        for radius in [0,-1,float('nan'),float('inf')]:
            with self.assertRaises(ValueError): plan_biopsy([0,0,0],radius,[0,0,0],[1,0,0])
        for axis in [[0,0,0],[1,2],[float('nan'),0,1]]:
            with self.assertRaises(ValueError): plan_biopsy([0,0,0],1,[0,0,0],axis)
        with self.assertRaises(ValueError): plan_biopsy([0,0,0],1,[0,0,0],[1,0,0],-1)
        with self.assertRaises(ValueError): plan_biopsy([0,0,float('nan')],1,[0,0,0],[1,0,0])

if __name__=='__main__': unittest.main()

# Author: Serhat Yaylacam
