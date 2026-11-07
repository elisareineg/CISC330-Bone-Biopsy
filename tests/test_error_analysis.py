import unittest
import numpy as np
from scipy.stats import chi2
from config import MARKERS_MODEL,TIP_MODEL,AXIS_MODEL,MARKER_SIGMA_MM
from registration import register_tool
from error_analysis import register_many,simulate_trials,compound_errors,wilson_interval,summarize_errors,sweep


class TargetingTests(unittest.TestCase):
    def test_batched_registration_matches_scalar(self):
        rng=np.random.default_rng(111)
        obs=MARKERS_MODEL+rng.normal(0,MARKER_SIGMA_MM,(12,3,3))
        tips,axes=register_many(MARKERS_MODEL,obs,TIP_MODEL,AXIS_MODEL)
        for i,m in enumerate(obs):
            pose=register_tool(MARKERS_MODEL,TIP_MODEL,AXIS_MODEL,m)
            np.testing.assert_allclose(tips[i],pose['tip_ct'],atol=1e-10)
            np.testing.assert_allclose(axes[i],pose['axis_ct'],atol=1e-12)

    def test_zero_errors_exact_baseline(self):
        tips,axes,z=simulate_trials(10,4,marker_sigma=0)
        line,end=compound_errors(tips,axes,z,0)
        self.assertLess(max(line.max(),end.max()),1e-10)

    def test_lateral_and_axial_displacement(self):
        tips=np.zeros((2,3)); axes=np.tile(AXIS_MODEL,(2,1))
        z=np.array([[3.,0.,4.],[0.,2.,0.]])
        line,end=compound_errors(tips,axes,z,1)
        np.testing.assert_allclose(line,[5,0],atol=1e-12)
        np.testing.assert_allclose(end,[5,2],atol=1e-12)
        self.assertTrue(np.all(line<=end+1e-12))

    def test_target_only_matches_analytic_distributions(self):
        n=60000; rng=np.random.default_rng(9)
        line,end=compound_errors(np.zeros((n,3)),np.tile(AXIS_MODEL,(n,1)),rng.normal(size=(n,3)),1.)
        self.assertAlmostEqual(np.mean(line<=3),1-np.exp(-4.5),delta=.003)
        self.assertAlmostEqual(np.mean(end<=3),chi2.cdf(9,3),delta=.003)

    def test_wilson_known_interval(self):
        low,high=wilson_interval(50,100)
        self.assertAlmostEqual(low,.4038315304,places=8)
        self.assertAlmostEqual(high,.5961684696,places=8)
        self.assertLess(summarize_errors(np.full(100,5.))['wilson95_high'],.95)

    def test_seed_reproducibility(self):
        a=simulate_trials(10,42);b=simulate_trials(10,42)
        for x,y in zip(a,b): np.testing.assert_array_equal(x,y)

    def test_sweep_preserves_sigma_and_status(self):
        n=1000; tips=np.zeros((n,3));axes=np.tile(AXIS_MODEL,(n,1));z=np.ones((n,3))
        rows=sweep(tips,axes,z,[0,4])
        self.assertEqual(rows[0]['trajectory']['status'],'supported_pass')
        self.assertEqual(rows[1]['trajectory']['status'],'supported_fail')
        self.assertEqual(rows[1]['target_sigma_mm'],4)

    def test_invalid_simulation_inputs(self):
        for n in [0,1,2.5]:
            with self.assertRaises(ValueError): simulate_trials(n)
        with self.assertRaises(ValueError): simulate_trials(3,marker_sigma=-1)
        with self.assertRaises(ValueError): compound_errors(np.zeros((2,3)),np.zeros((2,3)),np.zeros((2,3)),0)
        with self.assertRaises(ValueError): sweep(np.zeros((2,3)),np.ones((2,3)),np.ones((2,3)),[-1])

if __name__=='__main__': unittest.main()

# Author: Serhat Yaylacam
