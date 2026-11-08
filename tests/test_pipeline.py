"""Verify that calibrated marker-frame outputs feed registration and planning."""
import unittest
import numpy as np
from config import MARKERS_MODEL,TIP_MODEL,AXIS_MODEL
from transforms import marker_frame
from simulation import pivot_observations,axis_observations
from calibration import calibrate_tip,calibrate_axis
from registration import register_tool
from registration_cases import registration_cases
from planning import plan_biopsy


class PipelineTests(unittest.TestCase):
    def test_calibration_to_ct_to_biopsy_plan(self):
        origin,basis=marker_frame(MARKERS_MODEL)
        template=(MARKERS_MODEL-origin)@basis
        true_tip=basis.T@(TIP_MODEL-origin)
        true_axis=basis.T@AXIS_MODEL
        rng=np.random.default_rng(606)
        pivot,*_=pivot_observations(template,true_tip,rng)
        axial,*_=axis_observations(template,true_axis,true_tip,rng)
        calibrated_tip=calibrate_tip(template,pivot)['tip']
        calibrated_axis=calibrate_axis(template,axial,calibrated_tip)['axis']
        case=registration_cases()[2]
        pose=register_tool(template,calibrated_tip,calibrated_axis,case['markers_ct'])
        # Cyclic rotation + (10,-20,30) maps model target (0,-100,0)
        # to (10,-20,-70). A 5 mm radius gives entry 95, exit 105.
        plan=plan_biopsy([10.,-20.,-70.],5.,pose['tip_ct'],pose['axis_ct'])
        self.assertLess(plan['targeting_error_mm'],1e-10)
        self.assertAlmostEqual(plan['core_length_mm'],10.,places=10)
        self.assertAlmostEqual(plan['entry_depth_mm'],95.,places=10)
        self.assertAlmostEqual(plan['insertion_depth_mm'],105.,places=10)
        self.assertTrue(plan['harvest_possible'])

if __name__=='__main__': unittest.main()

# Author: Serhat Yaylacam
