"""Validate the three hand-derived CT cases and export a comparison report."""
import json
from pathlib import Path
import numpy as np
from config import MARKERS_MODEL, TIP_MODEL, AXIS_MODEL, DIAGRAM_UNIT_TO_MM
from registration import register_tool
from registration_cases import registration_cases
from geometry import angle_degrees


def run_registration(output=None):
    output=Path(output) if output is not None else Path(__file__).resolve().parent/'results'
    output.mkdir(exist_ok=True)
    records=[]
    lines=['# Stage 3 CT registration results','',
           f'Diagram unit to mm: {DIAGRAM_UNIT_TO_MM:g}. All positions and residuals are in mm.',
           'Expected values are hand-derived in docs/STAGE3_DERIVATIONS.md.', '',
           '| Case | Tip error (mm) | Axis error (degrees) | Marker RMS (mm) | Passed |',
           '|---|---:|---:|---:|---|']
    for case in registration_cases():
        got=register_tool(MARKERS_MODEL,TIP_MODEL,AXIS_MODEL,case['markers_ct'])
        tip_error=float(np.linalg.norm(got['tip_ct']-case['tip_ct']))
        axis_error=angle_degrees(got['axis_ct'],case['axis_ct'])
        passed=all(np.allclose(got[k],case[k],rtol=0,atol=1e-10)
                   for k in ['rotation','translation','tip_ct','axis_ct'])
        passed=bool(passed and got['marker_residual_rms']<1e-10)
        records.append({'case':case['name'],'expected':case,'computed':got,
                        'tip_error_mm':tip_error,'axis_error_deg':axis_error,'passed':passed})
        lines.append(f"| {case['name']} | {tip_error:.6g} | {axis_error:.6g} | {got['marker_residual_rms']:.6g} | {passed} |")
    lines+=['','All three cases check the recovered rotation and translation as well as',
            'the transformed tip and axis. The combined case rotates the marker triangle',
            'from the model XY plane into the CT YZ plane. Small residuals are numerical',
            'roundoff, not physical localization errors. These are exact-data checks.',
            'Noisy marker propagation will be quantified in Stage 5.','']
    report='\n'.join(lines)
    (output/'STAGE3_RESULTS.md').write_text(report)
    (output/'registration_summary.json').write_text(json.dumps(records,indent=2,
        default=lambda x:x.tolist() if isinstance(x,np.ndarray) else x.item())+'\n')
    print(report)
    if not all(r['passed'] for r in records):
        raise AssertionError('A registration validation case failed')
    return records

if __name__=='__main__': run_registration()

# Author: Serhat Yaylacam
