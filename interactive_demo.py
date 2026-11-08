"""Live, paused walkthrough. Saved statistical results are displayed, not rerun."""
import json
import sys
from pathlib import Path
import numpy as np
from config import MARKERS_MODEL,TIP_MODEL,AXIS_MODEL,DIAGRAM_UNIT_TO_MM,MARKER_SIGMA_MM
from transforms import marker_frame
from simulation import pivot_observations,axis_observations
from calibration import calibrate_tip,calibrate_axis
from registration import register_tool
from registration_cases import registration_cases
from planning import plan_biopsy

ROOT=Path(__file__).resolve().parent
RESULTS=ROOT/'results'


def pause(message='Press Enter to continue...'):
    input('\n'+message)


def heading(title):
    print('\n'+'='*70+'\n'+title+'\n'+'='*70)


def show_image(filename,title):
    import matplotlib.pyplot as plt
    path=RESULTS/filename
    if not path.exists():
        print(f'Missing figure: {path.name}. Regenerate it with an explicit --stage command.')
        return
    fig,ax=plt.subplots(figsize=(11,7),layout='constrained')
    ax.imshow(plt.imread(path));ax.axis('off');ax.set_title(title+'\nClose this window to continue.')
    plt.show(block=True)
    plt.close(fig)


def load_result(filename):
    path=RESULTS/filename
    if not path.exists():
        print(f'Missing {filename}; this section will skip the saved summary.')
        return None
    return json.loads(path.read_text())


def tool_figure(markers,tip,axis,title):
    import matplotlib.pyplot as plt
    fig=plt.figure(figsize=(8,7),layout='constrained');ax=fig.add_subplot(projection='3d')
    markers=np.asarray(markers);tip=np.asarray(tip);axis=np.asarray(axis)
    ax.scatter(*markers.T,s=70,color='#246b94')
    for i,m in enumerate(markers): ax.text(*m,f' M{i+1}')
    triangle=np.vstack([markers,markers[0]]);ax.plot(*triangle.T,color='#246b94')
    ax.scatter(*tip,color='#b43b32',s=60);ax.text(*tip,' Tip')
    back=tip-axis*np.linalg.norm(markers.mean(0)-tip)
    ax.plot(*np.vstack([back,tip]).T,color='gray',lw=3)
    ax.quiver(*tip,*axis,length=60,color='#b43b32',normalize=True)
    bound=np.vstack([markers,tip,back,tip+60*axis]);lo=bound.min(0);hi=bound.max(0)
    center=(lo+hi)/2;half=max(float((hi-lo).max())*.6,20)
    ax.set(xlim=(center[0]-half,center[0]+half),ylim=(center[1]-half,center[1]+half),
           zlim=(center[2]-half,center[2]+half),xlabel='x (mm)',ylabel='y (mm)',zlabel='z (mm)',
           title=title+'\nDrag to rotate; close window to continue.')
    ax.set_box_aspect((1,1,1))
    return fig


class ClickPlanner:
    """Click initial tip, then an aiming point in a simulated CT XY plane.

    The aiming point selects a direction only, not the insertion endpoint.
    All selected points have z=0; the full planner remains a 3D computation.
    This is a synthetic teaching view, not manual segmentation of patient CT.
    """
    def __init__(self):
        import matplotlib.pyplot as plt
        from matplotlib.patches import Circle
        from matplotlib.widgets import Button
        self.fig,self.ax=plt.subplots(figsize=(9,7))
        self.fig.subplots_adjust(bottom=.27,top=.85)
        self.ax.add_patch(Circle((0,0),10,facecolor='#d8eaf1',edgecolor='#246b94'))
        self.ax.set(xlim=(-40,40),ylim=(-35,35),aspect='equal',xlabel='CT x (mm)',ylabel='CT y (mm)')
        self.ax.grid(alpha=.2)
        self.fig.suptitle('Interactive biopsy planning | synthetic XY slice, z = 0\nSphere centre (0,0,0), radius 10 mm')
        self.message=self.fig.text(.12,.12,'',fontsize=11)
        self.artists=[];self.selected=[];self.last_plan=None
        self.reset_button=Button(self.fig.add_axes([.57,.025,.17,.055]),'Reset clicks')
        self.close_button=Button(self.fig.add_axes([.76,.025,.17,.055]),'Continue / close')
        self.reset_button.on_clicked(self.reset)
        self.close_button.on_clicked(lambda event:plt.close(self.fig))
        self.connection=self.fig.canvas.mpl_connect('button_press_event',self.on_click)
        self.reset()

    def reset(self,event=None):
        for artist in self.artists: artist.remove()
        self.artists=[];self.selected=[];self.last_plan=None
        self.ax.set_title('Click 1: choose the initial needle tip')
        self.message.set_text('Click a tip position, then a second point to aim the needle.\nTry intersecting, tangent, and missed paths. Reset to try again.')
        self.fig.canvas.draw_idle()

    def on_click(self,event):
        if event.inaxes is not self.ax or event.button!=1 or event.xdata is None or event.ydata is None:
            return
        if len(self.selected)==2: return
        point=np.array([event.xdata,event.ydata,0.])
        if not self.selected:
            self.selected.append(point)
            self.artists.append(self.ax.scatter(point[0],point[1],color='black',s=45,zorder=5))
            self.ax.set_title('Click 2: choose a point in the insertion direction')
        else:
            vector=point-self.selected[0]
            if np.linalg.norm(vector)<1e-6:
                self.message.set_text('Choose a different point: two identical clicks cannot define a direction.')
                self.fig.canvas.draw_idle();return
            self.selected.append(point)
            p=self.selected[0];v=vector/np.linalg.norm(vector)
            plan=plan_biopsy([0,0,0],10,p,v);self.last_plan=plan
            self.artists.append(self.ax.scatter(point[0],point[1],color='#b43b32',marker='x',s=55))
            self.artists.append(self.ax.annotate('',xy=(p+12*v)[:2],xytext=p[:2],
                arrowprops={'arrowstyle':'->','color':'#777777','linestyle':'--'},annotation_clip=True))
            # The clipped line stays visible even when its arrowhead is outside the axes.
            self.artists.extend(self.ax.plot([p[0],p[0]+100*v[0]],[p[1],p[1]+100*v[1]],'--',color='gray'))
            if plan['entry_point_ct_mm'] is not None:
                a,b=plan['entry_point_ct_mm'],plan['end_point_ct_mm']
                self.artists.extend(self.ax.plot([a[0],b[0]],[a[1],b[1]],color='#258044',lw=5))
                self.artists.append(self.ax.scatter([a[0],b[0]],[a[1],b[1]],color='#258044',s=30))
            depth=plan['insertion_depth_mm'];depth_text='N/A (not reachable)' if depth is None else f'{depth:.3f} mm'
            self.message.set_text(f"Status: {plan['status']} | Targeting error: {plan['targeting_error_mm']:.3f} mm\n"
                                  f"Core: {plan['core_length_mm']:.3f} mm | Depth/contact: {depth_text}\n"
                                  'Green = available core/contact. Reset to try again; Continue closes this view.')
            self.ax.set_title('Plan calculated from your two clicks')
            print(f"Clicked plan: error={plan['targeting_error_mm']:.3f} mm, core={plan['core_length_mm']:.3f} mm, depth={depth_text}")
        self.fig.canvas.draw_idle()


def configure_gui():
    import matplotlib
    # Computational plot modules use Agg. They are kept out of this process.
    import matplotlib.pyplot as plt
    if str(matplotlib.get_backend()).lower()=='agg':
        for backend in ('TkAgg','QtAgg'):
            try:
                plt.switch_backend(backend)
                fig=plt.figure();plt.close(fig)
                return
            except (ImportError,RuntimeError):
                continue
        raise RuntimeError('No desktop plotting backend is available. Run locally with Tk/Qt support, or use --batch for calculations.')


def main():
    if not sys.stdin.isatty():
        raise RuntimeError('The guided demo needs an interactive terminal. Use --batch or an explicit --stage for automation.')
    configure_gui()
    import matplotlib.pyplot as plt
    heading('CT-GUIDED BONE BIOPSY: GUIDED DEMONSTRATION')
    print('Press Enter between sections. Close each figure to proceed.\nThe planning section accepts mouse clicks. Saved Monte Carlo results are reused.\nThis is a synthetic geometry demonstration, not patient CT imaging.')
    pause()
    heading('PART 1: TOOL GEOMETRY AND FRAMES')
    print(f'Diagram scale: {DIAGRAM_UNIT_TO_MM:g} mm per figure unit (documented assumption).')
    print('Model markers (mm):\n',MARKERS_MODEL)
    fig=tool_figure(MARKERS_MODEL,TIP_MODEL,AXIS_MODEL,'Ground-truth tool geometry');plt.show(block=True);plt.close(fig)
    pause()
    heading('PART 2: TIP AND AXIS CALIBRATION')
    print('Tip: fixed pivot, varying tilt about multiple axes.\nAxis: spin the tool about its own shaft (tip in the divot); fit planes and circles.')
    origin,basis=marker_frame(MARKERS_MODEL);template=(MARKERS_MODEL-origin)@basis
    tip=basis.T@(TIP_MODEL-origin);axis=basis.T@AXIS_MODEL;rng=np.random.default_rng(606)
    po,*_=pivot_observations(template,tip,rng);ao,*_=axis_observations(template,axis,tip,rng)
    ct=calibrate_tip(template,po);ca=calibrate_axis(template,ao,ct['tip'])
    print('Expected marker-frame tip:',tip,'\nRecovered:',ct['tip'])
    print('Expected axis:',axis,'\nRecovered:',ca['axis'])
    print(f'Independent Gaussian marker coordinate sigma: {MARKER_SIGMA_MM:.6f} mm.')
    saved=load_result('calibration_summary.json')
    if saved:
        print(f"Saved noisy trials: {saved['trials']} | saved diagram scale: {saved['diagram_unit_to_mm']}")
        print('Saved noisy statistics:',json.dumps(saved['noisy_statistics'],indent=2))
    show_image('calibration_errors.png','Noisy calibration: tip and axis errors')
    show_image('marker_noise.png','Verification of the 1 mm radial noise bound')
    pause()
    heading('PART 3: REGISTER TOOL INTO CT')
    for case in registration_cases():
        pose=register_tool(MARKERS_MODEL,TIP_MODEL,AXIS_MODEL,case['markers_ct'])
        print('\n'+case['name']);print('Expected tip:',case['tip_ct'],'Recovered:',pose['tip_ct'])
        print('Expected axis:',case['axis_ct'],'Recovered:',pose['axis_ct'])
    case=registration_cases()[2];pose=register_tool(MARKERS_MODEL,TIP_MODEL,AXIS_MODEL,case['markers_ct'])
    fig=tool_figure(case['markers_ct'],pose['tip_ct'],pose['axis_ct'],'Combined rotation and translation in CT')
    plt.show(block=True);plt.close(fig);pause()
    heading('PART 4: BIOPSY PLANNING AND YOUR CLICKS')
    show_image('planning_scenarios.png','Reference cases: intersection, tangency, and miss')
    print('Now click the initial needle tip, then a point to aim toward.\nThe second click chooses direction, not insertion depth.\nUse Reset to try another path; Continue returns to the walkthrough.')
    pause('Press Enter to open the clickable planner...')
    planner=ClickPlanner();plt.show(block=True);plt.close(planner.fig)
    pause()
    heading('PART 5: TARGETING ERROR AND DISPLACEMENT TOLERANCE')
    saved=load_result('targeting_summary.json')
    if saved:
        print('Saved simulation, not recomputed:')
        print(f"Trials/level: {saved['n_per_sigma']:,}; scale: {saved['diagram_unit_to_mm']}; marker sigma: {saved['marker_sigma_per_coordinate_mm']:.6f} mm")
        b=saved['baseline']['trajectory']
        print(f"At zero target displacement: {100*b['success_probability']:.2f}% within 3 mm; p95={b['p95_error_mm']:.3f} mm")
        print(saved['conclusion'])
        if saved['diagram_unit_to_mm']!=DIAGRAM_UNIT_TO_MM or not np.isclose(saved['marker_sigma_per_coordinate_mm'],MARKER_SIGMA_MM):
            print('NOTE: saved settings differ from current config. Regenerate targeting results before interpreting them for this config.')
    show_image('targeting_baseline_cdf.png','Marker noise alone')
    show_image('targeting_sigma_sweep.png','Target displacement sweep')
    heading('DEMONSTRATION COMPLETE')
    print('Shown: geometry, live exact calibration, live CT registration,\nclick-based planning, and saved uncertainty results.\nUse explicit --stage commands to regenerate the saved outputs.')


if __name__=='__main__': main()

# Author: Serhat Yaylacam
