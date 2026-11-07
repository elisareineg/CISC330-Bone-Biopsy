import unittest
import numpy as np
from config import MARKERS_MODEL, TIP_MODEL, AXIS_MODEL
from registration import register_tool, rigid_registration
from registration_cases import registration_cases
from transforms import marker_frame


class RegistrationTests(unittest.TestCase):
    def check_case(self, index):
        case = registration_cases()[index]
        got = register_tool(MARKERS_MODEL, TIP_MODEL, AXIS_MODEL, case['markers_ct'])
        for key in ['tip_ct','axis_ct','rotation','translation']:
            np.testing.assert_allclose(got[key],case[key],atol=1e-10,rtol=0)
        self.assertLess(got['marker_residual_rms'],1e-10)
        np.testing.assert_allclose(got['rotation'].T @ got['rotation'],np.eye(3),atol=1e-12)
        self.assertAlmostEqual(np.linalg.det(got['rotation']),1.)

    def test_pure_translation(self): self.check_case(0)
    def test_pure_rotation(self): self.check_case(1)
    def test_rotation_and_translation(self): self.check_case(2)

    def test_nonzero_tip_receives_rotation_and_translation(self):
        # Cyclic map (x,y,z)->(z,x,y); independent expected result.
        case=registration_cases()[2]
        got=register_tool(MARKERS_MODEL,[4.,5.,6.],AXIS_MODEL,case['markers_ct'])
        np.testing.assert_allclose(got['tip_ct'],[16.,-16.,35.],atol=1e-10)

    def test_axis_normalization_and_translation_invariance(self):
        case=registration_cases()[2]
        a=register_tool(MARKERS_MODEL,TIP_MODEL,7*AXIS_MODEL,case['markers_ct'])
        shift=np.array([120.,-30.,80.])
        b=register_tool(MARKERS_MODEL,TIP_MODEL,AXIS_MODEL,case['markers_ct']+shift)
        np.testing.assert_allclose(a['axis_ct'],[0.,0.,-1.],atol=1e-12)
        np.testing.assert_allclose(b['axis_ct'],a['axis_ct'],atol=1e-12)
        np.testing.assert_allclose(b['tip_ct']-a['tip_ct'],shift,atol=1e-10)

    def test_marker_frame_input_matches_model_frame_input(self):
        origin,basis=marker_frame(MARKERS_MODEL)
        case=registration_cases()[2]
        got=register_tool((MARKERS_MODEL-origin)@basis,
                          basis.T@(TIP_MODEL-origin),basis.T@AXIS_MODEL,case['markers_ct'])
        np.testing.assert_allclose(got['tip_ct'],case['tip_ct'],atol=1e-10)
        np.testing.assert_allclose(got['axis_ct'],case['axis_ct'],atol=1e-12)

    def test_invalid_tip_axis_and_correspondences(self):
        for tip,axis in [([0,0,float('nan')],AXIS_MODEL),(TIP_MODEL,[0,0,0])]:
            with self.assertRaises(ValueError):
                register_tool(MARKERS_MODEL,tip,axis,MARKERS_MODEL)
        with self.assertRaises(ValueError):
            rigid_registration(MARKERS_MODEL,np.vstack([MARKERS_MODEL,[0,0,0]]))

    def test_reflection_is_not_accepted_as_rotation(self):
        # Noncoplanar set ensures a reflection cannot also fit as a proper rotation.
        a=np.array([[0.,0.,0.],[3.,0.,0.],[0.,4.,0.],[0.,0.,5.]])
        b=a*np.array([-1.,1.,1.])
        r,t=rigid_registration(a,b)
        self.assertAlmostEqual(np.linalg.det(r),1.)
        self.assertGreater(np.linalg.norm(a@r.T+t-b),1.)

if __name__=='__main__': unittest.main()

# Author: Serhat Yaylacam
