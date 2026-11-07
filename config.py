"""Assignment Fig. 2 geometry. Explicit assumption: diagram units are cm."""
import numpy as np
from scipy.stats import chi2
DIAGRAM_UNIT_TO_MM = 10.0
MARKERS_MODEL = np.array([[2.,18.,0.],[8.,18.,0.],[2.,24.,0.]]) * DIAGRAM_UNIT_TO_MM
TIP_MODEL = np.zeros(3)
AXIS_MODEL = np.array([0.,-1.,0.])
MARKER_SIGMA_MM = 1.0 / np.sqrt(chi2.ppf(0.95, df=3))
SEED = 330

# Author: Serhat Yaylacam
