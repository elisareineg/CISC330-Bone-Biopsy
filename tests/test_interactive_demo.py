import unittest
from types import SimpleNamespace
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from interactive_demo import ClickPlanner

class InteractiveTests(unittest.TestCase):
    def setUp(self): self.planner=ClickPlanner()
    def tearDown(self): plt.close(self.planner.fig)
    def click(self,x,y):
        self.planner.on_click(SimpleNamespace(inaxes=self.planner.ax,button=1,xdata=x,ydata=y))
    def test_two_clicks_compute_plan(self):
        self.click(-30,0);self.click(0,0)
        self.assertAlmostEqual(self.planner.last_plan['core_length_mm'],20)
        self.assertAlmostEqual(self.planner.last_plan['insertion_depth_mm'],40)
    def test_identical_click_is_ignored(self):
        self.click(-30,0);self.click(-30,0)
        self.assertEqual(len(self.planner.selected),1)
        self.assertIsNone(self.planner.last_plan)
    def test_reset_allows_second_plan(self):
        self.click(-30,0);self.click(0,0);self.planner.reset()
        self.assertEqual(self.planner.selected,[])
        self.click(-30,20);self.click(0,20)
        self.assertEqual(self.planner.last_plan['status'],'miss')

# Author: Serhat Yaylacam
