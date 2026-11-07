import unittest
import numpy as np
from scipy.spatial.transform import Rotation
from config import MARKERS_MODEL, TIP_MODEL, AXIS_MODEL
from transforms import marker_frame, transform_points
from calibration import calibrate_tip, calibrate_axis
from simulation import pivot_observations, axis_observations
from registration import rigid_registration
from geometry import angle_degrees

class CalibrationTests(unittest.TestCase):
    def setUp(self):
        origin,basis = marker_frame(MARKERS_MODEL)
        self.template = (MARKERS_MODEL-origin)@basis
        self.tip = basis.T@(TIP_MODEL-origin)
        self.axis = basis.T@AXIS_MODEL
        self.rng = np.random.default_rng(42)

    def test_pivot_recovers_tip_and_unknown_pivot(self):
        obs,_,_,pivot = pivot_observations(self.template,self.tip,self.rng)
        result=calibrate_tip(self.template,obs)
        np.testing.assert_allclose(result['tip'],self.tip,atol=1e-10)
        np.testing.assert_allclose(result['pivot'],pivot,atol=1e-10)

    def test_axis_recovers_signed_direction(self):
        obs,_,_=axis_observations(self.template,self.axis,self.rng)
        self.assertLess(angle_degrees(calibrate_axis(self.template,obs)['axis'],self.axis),1e-10)
        self.assertLess(angle_degrees(calibrate_axis(self.template,obs[::-1])['axis'],-self.axis),1e-10)

    def test_single_axis_pivot_is_unidentifiable(self):
        rs=Rotation.from_euler('y',np.linspace(0,180,20)[:,None],degrees=True).as_matrix()
        obs=np.array([transform_points(self.template,r,-r@self.tip) for r in rs])
        with self.assertRaises(ValueError): calibrate_tip(self.template,obs)

    def test_axis_requires_motion(self):
        with self.assertRaises(ValueError):
            calibrate_axis(self.template,np.repeat(self.template[None],10,axis=0))

    def test_collinear_markers_rejected(self):
        m=np.array([[0.,0.,0.],[1.,0.,0.],[2.,0.,0.]])
        with self.assertRaises(ValueError): rigid_registration(m,m)

    def test_arbitrary_tip_axis_and_marker_geometry(self):
        template=np.array([[0.,0.,0.],[40.,5.,0.],[-8.,55.,9.]])
        tip=np.array([12.,-133.,27.]); axis=np.array([1.,-2.,3.])/np.sqrt(14.)
        obs,*_=pivot_observations(template,tip,self.rng)
        np.testing.assert_allclose(calibrate_tip(template,obs)['tip'],tip,atol=1e-10)
        obs,*_=axis_observations(template,axis,self.rng)
        self.assertLess(angle_degrees(calibrate_axis(template,obs)['axis'],axis),1e-10)

    def test_noisy_calibration_is_finite(self):
        obs,*_=pivot_observations(self.template,self.tip,self.rng,sigma=.358)
        result=calibrate_tip(self.template,obs)
        self.assertTrue(np.isfinite(result['tip']).all())
        self.assertGreater(result['residual_rms_mm'],0.)

if __name__=='__main__': unittest.main()

# Author: Serhat Yaylacam
