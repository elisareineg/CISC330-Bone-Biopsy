"""Run independent biopsy-planning cases and export results and geometry plots."""
import csv
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from planning import plan_biopsy
from planning_cases import planning_cases


def run_planning(output=None):
    output=Path(output) if output is not None else Path(__file__).resolve().parent/'results'
    output.mkdir(exist_ok=True)
    records=[]
    lines=['# Stage 4 biopsy planning results','',
           'All distances are in mm. Sphere centre (0,0,0), radius 1; direction +x.',
           'Expected values are derived independently in docs/STAGE4_DERIVATIONS.md.','',
           '| Case | Targeting error | Core length | Insertion depth | Status | Passed |',
           '|---|---:|---:|---:|---|---|']
    for c in planning_cases():
        got=plan_biopsy(c['center'],c['radius'],c['tip'],c['axis'])
        passed=all(got[k]==v if v is None or isinstance(v,str)
                   else bool(np.isclose(got[k],v,atol=1e-10,rtol=0)) for k,v in c['expected'].items())
        records.append({'case':c,'computed':got,'passed':passed})
        depth='N/A' if got['insertion_depth_mm'] is None else f"{got['insertion_depth_mm']:.6g}"
        lines.append(f"| {c['name']} | {got['targeting_error_mm']:.6g} | {got['core_length_mm']:.6g} | {depth} | {got['status']} | {passed} |")
    lines+=['','N/A means the forward trajectory cannot reach the sphere. It is stored as',
            'JSON null / Python None, not as a zero insertion depth. Tangency has zero',
            'harvestable core and a finite contact depth. Starting on the surface and',
            'pointing outward also gives zero core, with contact already at depth zero.',
            'The inside case counts only the forward part of the chord.','',
            'These geometric results idealize the needle as a line and the tumor as a',
            'sphere. They do not model cutting geometry, actual core-device sampling',
            'length, tissue deformation, or finite needle radius.','']
    report='\n'.join(lines)
    (output/'STAGE4_RESULTS.md').write_text(report)
    (output/'planning_summary.json').write_text(json.dumps(records,indent=2,
        default=lambda x:x.tolist() if isinstance(x,np.ndarray) else x.item())+'\n')
    with (output/'planning_cases.csv').open('w',newline='') as f:
        writer=csv.writer(f)
        writer.writerow(['case','targeting_error_mm','core_length_mm','insertion_depth_mm','status','passed'])
        for rec in records:
            g=rec['computed']
            writer.writerow([rec['case']['name'],g['targeting_error_mm'],g['core_length_mm'],
                             g['insertion_depth_mm'],g['status'],rec['passed']])
    fig,axes=plt.subplots(1,3,figsize=(12,4.4),layout='constrained')
    for ax,rec in zip(axes,records[:3]):
        c,g=rec['case'],rec['computed']; p=np.array(c['tip'],dtype=float)
        ax.add_patch(Circle((0,0),1,color='#cfe5ec',ec='#246b94',lw=2))
        ax.plot([p[0],1.6],[p[1],p[1]],'--',color='#555555',lw=1.5)
        ax.annotate('',xy=(1.6,p[1]),xytext=(.9,p[1]),arrowprops={'arrowstyle':'->','color':'#555555'})
        ax.scatter(p[0],p[1],color='black',s=28,zorder=4)
        ax.text(p[0],p[1]+.2,'Initial tip',fontsize=8)
        ax.plot([0,0],[0,p[1]],color='#b43b32',lw=2)
        ax.scatter(0,0,color='#246b94',s=20)
        if g['core_length_mm']>0:
            a,b=g['entry_point_ct_mm'],g['end_point_ct_mm']
            ax.plot([a[0],b[0]],[a[1],b[1]],color='#258044',lw=5)
        elif g['status']=='contact': ax.scatter(0,1,color='#258044',s=35,zorder=5)
        depth='N/A' if g['insertion_depth_mm'] is None else f"{g['insertion_depth_mm']:.1f} mm"
        ax.set(title=c['name'].capitalize(),xlabel='CT x (mm)',ylabel='CT y (mm)',
               xlim=(-5.5,2),ylim=(-1.5,2.8),aspect='equal')
        ax.set_title(f"{c['name'].capitalize()}\nError: {g['targeting_error_mm']:.1f} mm | Core: {g['core_length_mm']:.1f} mm\nDepth: {depth}", fontsize=10)
        ax.grid(alpha=.15)
    fig.suptitle('Biopsy planning: sphere cross-section at z = 0\nGreen: available core/contact; red: targeting error')
    fig.savefig(output/'planning_scenarios.png',dpi=180); plt.close(fig)
    print(report)
    if not all(r['passed'] for r in records): raise AssertionError('Planning case failed')
    return records

if __name__=='__main__': run_planning()

# Author: Serhat Yaylacam
