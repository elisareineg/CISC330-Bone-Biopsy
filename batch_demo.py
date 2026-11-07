"""Run completed stages: python demo_flow.py --stage all --trials 500."""
import argparse
import csv
import json
from pathlib import Path
import platform
import numpy as np
import scipy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from config import MARKERS_MODEL, TIP_MODEL, AXIS_MODEL, MARKER_SIGMA_MM, SEED, DIAGRAM_UNIT_TO_MM
from transforms import marker_frame
from calibration import calibrate_tip, calibrate_axis
from simulation import pivot_observations, axis_observations
from geometry import angle_degrees


def serial(value):
    if isinstance(value,np.ndarray): return value.tolist()
    if isinstance(value,np.generic): return value.item()
    raise TypeError(type(value).__name__)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trials',type=int,default=500)
    parser.add_argument('--stage',choices=['all','calibration','registration','planning','targeting'],default='all')
    parser.add_argument('--targeting-trials',type=int,default=200000)
    args=parser.parse_args()
    if args.stage == 'targeting':
        from targeting_demo import run_targeting
        run_targeting(n=args.targeting_trials)
        return
    if args.stage == 'planning':
        from planning_demo import run_planning
        run_planning()
        return
    if args.stage == 'registration':
        from registration_demo import run_registration
        run_registration()
        return
    if args.trials < 2: parser.error('Use at least two trials')
    output=Path(__file__).resolve().parent/'results'
    output.mkdir(exist_ok=True)
    origin,basis=marker_frame(MARKERS_MODEL)
    template=(MARKERS_MODEL-origin)@basis
    tip=basis.T@(TIP_MODEL-origin); axis=basis.T@AXIS_MODEL
    # Separate streams keep noise validation independent of calibration trials.
    exact_rng,noisy_rng,check_rng=[np.random.default_rng(s) for s in np.random.SeedSequence(SEED).spawn(3)]
    exact_pivot,_,_,pivot=pivot_observations(template,tip,exact_rng)
    exact_axis,_,_=axis_observations(template,axis,exact_rng)
    exact_tip_result=calibrate_tip(template,exact_pivot)
    exact_axis_result=calibrate_axis(template,exact_axis)
    rows=[]
    example=None
    for trial in range(args.trials):
        po,*_=pivot_observations(template,tip,noisy_rng,sigma=MARKER_SIGMA_MM)
        ao,*_=axis_observations(template,axis,noisy_rng,sigma=MARKER_SIGMA_MM)
        tr=calibrate_tip(template,po); ar=calibrate_axis(template,ao)
        rows.append([trial,float(np.linalg.norm(tr['tip']-tip)),angle_degrees(ar['axis'],axis)])
        if trial==0:
            example={'tip_marker_mm':tr['tip'], 'tip_model_mm':basis@tr['tip']+origin,
                     'axis_marker':ar['axis'],'axis_model':basis@ar['axis'],
                     'tip_diagnostics':tr,'axis_diagnostics':ar}
            np.savez_compressed(output/'example_observations.npz',marker_template_mm=template,
                                exact_pivot_observations_mm=exact_pivot,
                                exact_axis_observations_mm=exact_axis,
                                noisy_pivot_observations_mm=po,noisy_axis_observations_mm=ao)
    with (output/'calibration_trials.csv').open('w',newline='') as f:
        writer=csv.writer(f); writer.writerow(['trial','tip_error_mm','axis_error_deg']); writer.writerows(rows)
    errors=np.array(rows)[:,1:]
    noise=check_rng.normal(0,MARKER_SIGMA_MM,(200000,3))
    magnitudes=np.linalg.norm(noise,axis=1)
    stats={name:{'mean':float(v.mean()),'median':float(np.median(v)),
                 'p95':float(np.quantile(v,.95)),'max':float(v.max())}
           for name,v in zip(['tip_error_mm','axis_error_deg'],errors.T)}
    summary={'stage':2,'seed':SEED,'trials':args.trials,'poses_per_calibration':80,
             'axis_translation_span_mm':100,'diagram_unit_to_mm':DIAGRAM_UNIT_TO_MM,
             'marker_sigma_per_coordinate_mm':MARKER_SIGMA_MM,
             'noise_check':{'samples':len(noise),'fraction_below_1mm':float(np.mean(magnitudes<1)),
                            'p95_magnitude_mm':float(np.quantile(magnitudes,.95))},
             'ground_truth':{'tip_marker_mm':tip,'axis_marker':axis,'pivot_tracker_mm':pivot},
             'exact':{'tip_error_mm':float(np.linalg.norm(exact_tip_result['tip']-tip)),
                      'axis_error_deg':angle_degrees(exact_axis_result['axis'],axis),
                      'pivot_error_mm':float(np.linalg.norm(exact_tip_result['pivot']-pivot)),
                      'tip_diagnostics':exact_tip_result},
             'noisy_statistics':stats,'first_noisy_trial':example,
             'versions':{'python':platform.python_version(),'numpy':np.__version__,
                         'scipy':scipy.__version__,'matplotlib':matplotlib.__version__}}
    (output/'calibration_summary.json').write_text(json.dumps(summary,indent=2,default=serial)+'\n')
    fig,axs=plt.subplots(1,2,figsize=(10,4),layout='constrained')
    for ax,v,label in zip(axs,errors.T,['Tip error (mm)','Axis error (degrees)']):
        ax.hist(v,bins=28,color='#246b94',edgecolor='white')
        ax.axvline(np.quantile(v,.95),color='#b43b32',label='Empirical 95th percentile')
        ax.set(xlabel=label,ylabel='Calibration trials'); ax.legend(fontsize=8)
    fig.suptitle(f'Calibration with noisy markers: {args.trials} independent trials')
    fig.savefig(output/'calibration_errors.png',dpi=180); plt.close(fig)
    fig,ax=plt.subplots(figsize=(6,4),layout='constrained')
    ax.hist(magnitudes,bins=70,density=True,color='#246b94',edgecolor='white')
    ax.axvline(1,color='#b43b32',label='Theoretical 95th percentile: 1 mm')
    ax.set(xlabel='3D marker displacement (mm)',ylabel='Probability density',title='Marker-noise verification')
    ax.legend(fontsize=8); fig.savefig(output/'marker_noise.png',dpi=180); plt.close(fig)
    report=f'''# Stage 2 calibration results

Seed: {SEED}. Independent calibration repetitions: {args.trials}.
Each calibration uses 80 poses. Axis calibration uses 100 mm of guided translation.
Diagram coordinates are assumed to be centimetres; calculations use millimetres.

| Validation | Result |
|---|---:|
| Exact tip error | {summary['exact']['tip_error_mm']:.6g} mm |
| Exact axis error | {summary['exact']['axis_error_deg']:.6g} degrees |
| Exact pivot error | {summary['exact']['pivot_error_mm']:.6g} mm |
| Gaussian sigma per coordinate | {MARKER_SIGMA_MM:.6f} mm |
| Observed fraction of marker errors below 1 mm | {summary['noise_check']['fraction_below_1mm']:.6f} |

| Noisy calibration error | Mean | Median | 95th percentile | Maximum |
|---|---:|---:|---:|---:|
'''
    for name,st in stats.items():
        report+='| '+name+' | '+' | '.join(f'{st[k]:.6f}' for k in ['mean','median','p95','max'])+' |\n'
    report+='''
## Interpretation

Exact-data errors are at floating-point precision. With noisy marker observations,
the recovered poses are imperfect. The tip is far from the marker triangle, so
small orientation errors contribute to tip-position uncertainty. Multiple distinct
pivot poses reduce random uncertainty. Axis calibration benefits from a long
translation baseline and averaging the orientation over many observations.

The empirical 95th percentiles describe repeated calibrations for this geometry,
pose count, motion range, noise distribution, and estimator. They are not exact
confidence bounds or clinical validation. A different marker scale or restricted
motions changes the results. Pose recovery and pivot fitting involve noisy
rotations, so finite-sample errors and estimator bias are both possible.

The simulated tracker noise is isotropic and independent across markers, poses,
and repetitions. Marker-template uncertainty, guide misalignment, tip slippage,
correlated tracker error, and tool bending are excluded. Axis calibration assumes
constant orientation and a guide aligned with the shaft. These constraints are
part of the experiment, not conclusions inferred solely from the marker data.

Stage 5 will examine targeting error. Calibration errors in this stage do not
establish whether the final 3 mm targeting requirement is satisfied.
'''
    (output/'STAGE2_RESULTS.md').write_text(report)
    print(report)
    if args.stage == 'all':
        from registration_demo import run_registration
        run_registration(output)
        from planning_demo import run_planning
        run_planning(output)
        from targeting_demo import run_targeting
        run_targeting(output,n=args.targeting_trials)

if __name__=='__main__': main()

# Author: Serhat Yaylacam
