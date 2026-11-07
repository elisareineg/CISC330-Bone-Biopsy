"""Stage 5: seeded sweep of target displacement, with independent baseline check."""
import csv
import json
from pathlib import Path
import numpy as np
import scipy
from scipy.stats import chi2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from config import MARKER_SIGMA_MM,DIAGRAM_UNIT_TO_MM
from error_analysis import simulate_trials,compound_errors,summarize_errors,sweep


def run_targeting(output=None,n=200000,seed=335):
    output=Path(output) if output else Path(__file__).resolve().parent/'results'
    output.mkdir(exist_ok=True)
    tips,axes,z=simulate_trials(n,seed)
    sigmas=np.round(np.arange(31)*.1,10)
    rows=sweep(tips,axes,z,sigmas)
    # Separate marker/target streams and independent validation seed.
    vt,va,vz=simulate_trials(n,seed+10000)
    vl,ve=compound_errors(vt,va,vz,0)
    validation={'trajectory':summarize_errors(vl),'endpoint':summarize_errors(ve)}
    feasible=[r['target_sigma_mm'] for r in rows if r['trajectory']['status']=='supported_pass']
    baseline=rows[0]['trajectory']
    if baseline['status']=='supported_fail' and not feasible:
        conclusion='No feasible target-displacement sigma: even sigma=0 fails; all sampled levels also fail.'
        maximum=None
    else:
        conclusion='Baseline or feasibility changed: inspect sweep; grid maximum is not a continuous optimized threshold.'
        maximum=max(feasible) if feasible else None
    summary={'stage':5,'n_per_sigma':n,'seed':seed,'independent_validation_seed':seed+10000,
             'marker_sigma_per_coordinate_mm':MARKER_SIGMA_MM,'diagram_unit_to_mm':DIAGRAM_UNIT_TO_MM,
             'insertion_depth_mm':100.,'error_threshold_mm':3.,'required_probability':.95,
             'target_sigma_grid_mm':sigmas.tolist(),'grid_step_mm':.1,
             'primary_metric':'distance from noisy registered trajectory to displaced target',
             'secondary_metric':'endpoint distance after 100 mm insertion',
             'maximum_supported_grid_sigma_mm':maximum,'conclusion':conclusion,
             'baseline':rows[0],'independent_baseline_validation':validation,
             'target_only_analytic_sigma_limits_mm':{
                 'trajectory':float(3/np.sqrt(-2*np.log(.05))),
                 'endpoint':float(3/np.sqrt(chi2.ppf(.95,3)))},
             'versions':{'numpy':np.__version__,'scipy':scipy.__version__},'sweep':rows}
    (output/'targeting_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    with (output/'targeting_sweep.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['sigma_mm','metric','success_probability','wilson95_low','wilson95_high','p95_error_mm','status'])
        for row in rows:
            for metric in ['trajectory','endpoint']:
                r=row[metric];w.writerow([row['target_sigma_mm'],metric,*[r[k] for k in ['success_probability','wilson95_low','wilson95_high','p95_error_mm','status']]])
    # Retain all baseline errors for distribution inspection, not just plot summaries.
    line,end=compound_errors(tips,axes,z,0)
    np.savez_compressed(output/'targeting_baseline_errors.npz',trajectory_error_mm=line,endpoint_error_mm=end)
    sample_count=min(1000,n)
    np.savez_compressed(output/'targeting_trial_sample.npz',estimated_tips_mm=tips[:sample_count],
                        estimated_axes=axes[:sample_count],target_standard_normals=z[:sample_count])
    fig,axs=plt.subplots(1,2,figsize=(11,4.5),layout='constrained')
    for metric,color in [('trajectory','#246b94'),('endpoint','#b45d32')]:
        probs=np.array([r[metric]['success_probability'] for r in rows])
        lo=np.array([r[metric]['wilson95_low'] for r in rows]);hi=np.array([r[metric]['wilson95_high'] for r in rows])
        axs[0].plot(sigmas,probs,label=metric,color=color)
        axs[0].fill_between(sigmas,lo,hi,color=color,alpha=.2)
        axs[1].plot(sigmas,[r[metric]['p95_error_mm'] for r in rows],label=metric,color=color)
    axs[0].axhline(.95,color='black',linestyle='--',label='Required: 95%')
    axs[1].axhline(3,color='black',linestyle='--',label='Limit: 3 mm')
    axs[0].set(xlabel='Target sigma per coordinate (mm)',ylabel='Fraction within 3 mm',ylim=(0,1))
    axs[1].set(xlabel='Target sigma per coordinate (mm)',ylabel='95th-percentile error (mm)')
    for ax in axs: ax.legend(fontsize=8);ax.grid(alpha=.2)
    fig.suptitle(f'Targeting error at 100 mm insertion: {n:,} trials per sigma')
    fig.savefig(output/'targeting_sigma_sweep.png',dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(7,4),layout='constrained')
    for values,label,color in [(line,'Trajectory distance','#246b94'),(end,'Endpoint distance','#b45d32')]:
        values=np.sort(values);ax.plot(values,np.arange(1,n+1)/n,label=label,color=color)
    ax.axvline(3,color='black',ls='--',label='3 mm threshold');ax.axhline(.95,color='gray',ls=':')
    ax.set(xlim=(0,float(np.quantile(end,.999))),ylim=(0,1),xlabel='Error (mm)',ylabel='Cumulative probability',
           title='Marker noise alone: target displacement sigma = 0')
    ax.legend();ax.grid(alpha=.2);fig.savefig(output/'targeting_baseline_cdf.png',dpi=180);plt.close(fig)
    lines=['# Stage 5 targeting-error simulation','',conclusion,'',
           f'{n:,} independent trials per sigma; seed {seed}; marker coordinate sigma {MARKER_SIGMA_MM:.6f} mm.',
           'The grid runs from 0 to 3 mm in 0.1 mm steps. Insertion depth is 100 mm.',
           'Target sigma is per coordinate, not a radial displacement bound.','',
           '## Baseline: marker noise only','',
           '| Metric | Fraction within 3 mm | 95% Wilson interval | 95th-percentile error |',
           '|---|---:|---|---:|']
    for metric in ['trajectory','endpoint']:
        b=rows[0][metric]
        lines.append(f"| {metric} | {b['success_probability']:.6f} | [{b['wilson95_low']:.6f}, {b['wilson95_high']:.6f}] | {b['p95_error_mm']:.6f} mm |")
    lines+=['','## Independent baseline validation','']
    for metric,b in validation.items():
        lines.append(f"- {metric}: success fraction {b['success_probability']:.6f}, 95% interval [{b['wilson95_low']:.6f}, {b['wilson95_high']:.6f}], p95 error {b['p95_error_mm']:.6f} mm.")
    lines+=['','## Selected sweep values','',
            '| Target sigma (mm) | Trajectory success | Trajectory p95 (mm) | Endpoint success | Endpoint p95 (mm) |',
            '|---|---:|---:|---:|---:|']
    for row in rows[::5]:
        a,b=row['trajectory'],row['endpoint']
        lines.append(f"| {row['target_sigma_mm']:.1f} | {a['success_probability']:.6f} | {a['p95_error_mm']:.6f} | {b['success_probability']:.6f} | {b['p95_error_mm']:.6f} |")
    lines+=['','## Interpretation and scope','',
            'Under the approved coordinate scale, the 60 mm marker spacing is small',
            'relative to the roughly 300 mm marker-to-target lever arm. Submillimetre',
            'marker localization errors become angular uncertainty, amplified at the',
            'target. The 1 mm marker bound is not a 1 mm needle-target error bound.',
            '',
            'A value of zero is NOT a tolerable maximum in this run: zero also fails.',
            'The result is no feasible sigma under the baseline-first tolerance search.',
            'Every sampled sigma in [0,3] mm fails. The finite grid is not a proof about',
            'all arbitrarily large sigmas, and no continuous threshold is inferred.',
            '',
            'The primary metric follows the assignment trajectory-distance definition.',
            'The endpoint metric is reported separately; axial displacement affects it',
            'even when distance to the infinite trajectory remains zero. Neither metric',
            'meets the requirement at baseline. The 95% success requirement is distinct',
            'from the 95% confidence intervals used to estimate that probability.',
            '',
            'Intervals are pointwise, not simultaneous across the sweep. Common random',
            'numbers pair sigma levels; trials at each level remain independent. A',
            'separate run validates the prespecified baseline, far from the pass/fail',
            'boundary. No maximum was selected from noisy passing levels.',
            '',
            'Stage 2 calibration error is not added: this experiment holds the model',
            'tip/axis fixed and isolates the requested CT marker noise and independent',
            'target displacement. The noisy registered pose defines the perturbed',
            'trajectory in the exercise; this is not a model of a real control loop.',
            'See docs/STAGE5_METHODS.md for equations, assumptions, and checks.','']
    report='\n'.join(lines);(output/'STAGE5_RESULTS.md').write_text(report);print(report)
    return summary

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--targeting-trials',type=int,default=200000)
    parser.add_argument('--seed',type=int,default=335)
    args=parser.parse_args();run_targeting(n=args.targeting_trials,seed=args.seed)

# Author: Serhat Yaylacam
