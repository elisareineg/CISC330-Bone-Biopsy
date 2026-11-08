import unittest
import numpy as np
from scipy.spatial.transform import Rotation
from config import MARKERS_MODEL, TIP_MODEL, AXIS_MODEL
from transforms import marker_frame, transform_points
from calibration import calibrate_tip, calibrate_axis
from simulation import pivot_observations, axis_observations
from registration import rigid_registration
from geometry import angle_degrees, fit_plane, fit_circle

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

    def test_spin_recovers_signed_axis(self):
        obs,*_=axis_observations(self.template,self.axis,self.tip,self.rng)
        result=calibrate_axis(self.template,obs,self.tip)
        self.assertLess(angle_degrees(result['axis'],self.axis),1e-10)
        # Spinning the other way gives the same axis: the tip, not the motion, fixes the sign
        self.assertLess(angle_degrees(calibrate_axis(self.template,obs[::-1],self.tip)['axis'],self.axis),1e-10)
        # The calibrated tip lies on the fitted shaft
        self.assertLess(result['tip_offset_from_axis_mm'],1e-9)

    def test_single_axis_pivot_is_unidentifiable(self):
        rs=Rotation.from_euler('y',np.linspace(0,180,20)[:,None],degrees=True).as_matrix()
        obs=np.array([transform_points(self.template,r,-r@self.tip) for r in rs])
        with self.assertRaises(ValueError): calibrate_tip(self.template,obs)

    def test_axis_requires_motion(self):
        with self.assertRaises(ValueError):
            calibrate_axis(self.template,np.repeat(self.template[None],10,axis=0),self.tip)

    def test_short_spin_rejected(self):
        obs,*_=axis_observations(self.template,self.axis,self.tip,self.rng,span_deg=10.)
        with self.assertRaises(ValueError): calibrate_axis(self.template,obs,self.tip)

    def test_collinear_markers_rejected(self):
        m=np.array([[0.,0.,0.],[1.,0.,0.],[2.,0.,0.]])
        with self.assertRaises(ValueError): rigid_registration(m,m)

    def test_arbitrary_tip_axis_and_marker_geometry(self):
        template=np.array([[0.,0.,0.],[40.,5.,0.],[-8.,55.,9.]])
        tip=np.array([12.,-133.,27.]); axis=np.array([1.,-2.,3.])/np.sqrt(14.)
        obs,*_=pivot_observations(template,tip,self.rng)
        np.testing.assert_allclose(calibrate_tip(template,obs)['tip'],tip,atol=1e-10)
        obs,*_=axis_observations(template,axis,tip,self.rng)
        self.assertLess(angle_degrees(calibrate_axis(template,obs,tip)['axis'],axis),1e-10)

    def test_noisy_calibration_is_finite(self):
        obs,*_=pivot_observations(self.template,self.tip,self.rng,sigma=.358)
        result=calibrate_tip(self.template,obs)
        self.assertTrue(np.isfinite(result['tip']).all())
        self.assertGreater(result['residual_rms_mm'],0.)
        obs,*_=axis_observations(self.template,self.axis,self.tip,self.rng,sigma=.358)
        axis=calibrate_axis(self.template,obs,result['tip'])
        self.assertLess(angle_degrees(axis['axis'],self.axis),1.)
        self.assertGreater(axis['circle_residual_rms_mm'],0.)


class FittingTests(unittest.TestCase):
    def test_circle_fit_recovers_centre_radius_and_normal(self):
        centre=np.array([5.,-2.,7.]); normal=np.array([1.,2.,2.])/3.
        e1=np.cross(normal,[1.,0.,0.]); e1/=np.linalg.norm(e1); e2=np.cross(normal,e1)
        angles=np.linspace(0,1.5,12)   # an 86 degree arc is enough without noise
        pts=centre+4.*(np.outer(np.cos(angles),e1)+np.outer(np.sin(angles),e2))
        c,r,n,residual=fit_circle(pts)
        np.testing.assert_allclose(c,centre,atol=1e-9)
        self.assertAlmostEqual(r,4.,places=9)
        self.assertLess(angle_degrees(n,normal) if np.dot(n,normal)>0 else angle_degrees(-n,normal),1e-9)
        self.assertLess(residual,1e-9)

    def test_plane_fit_rejects_collinear_points(self):
        with self.assertRaises(ValueError): fit_plane(np.outer(np.arange(5.),[1.,2.,3.]))

if __name__=='__main__': unittest.main()

# Author: Serhat Yaylacam
