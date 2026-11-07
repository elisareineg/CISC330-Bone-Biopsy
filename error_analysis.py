"""Monte Carlo marker-error propagation and independent target displacement.

Each trial re-registers noisy marker coordinates. Batched SVD uses the same
proper-rotation fit as registration.py, checked against that scalar API in tests.
The model-frame/CT-frame ground-truth transform is identity.
"""
import numpy as np
from scipy.stats import norm
from config import MARKERS_MODEL, TIP_MODEL, AXIS_MODEL, MARKER_SIGMA_MM
from geometry import points, vector3, unit


def register_many(template, observations, tip, axis):
    """Vectorized proper rigid fit; returns N estimated tips and unit axes."""
    template=points(template)
    obs=np.asarray(observations,dtype=float)
    if obs.ndim!=3 or obs.shape[1:]!=template.shape or len(obs)==0 or not np.isfinite(obs).all():
        raise ValueError('Expected finite N x markers x 3 observations')
    tip=vector3(tip); axis=unit(axis)
    ac=template-template.mean(0)
    bc=obs-obs.mean(axis=1)[:,None,:]
    if np.linalg.matrix_rank(ac)<2 or np.any(np.linalg.matrix_rank(bc)<2):
        raise ValueError('Noncollinear marker sets required')
    h=np.einsum('mi,nmj->nij',ac,bc)
    u,_,vt=np.linalg.svd(h)
    v=vt.transpose(0,2,1); ut=u.transpose(0,2,1)
    d=np.broadcast_to(np.eye(3),(len(obs),3,3)).copy()
    d[:,2,2]=np.linalg.det(v@ut)
    rotation=v@d@ut
    translation=obs.mean(axis=1)-np.einsum('nij,j->ni',rotation,template.mean(0))
    tips=np.einsum('nij,j->ni',rotation,tip)+translation
    axes=np.einsum('nij,j->ni',rotation,axis)
    axes/=np.linalg.norm(axes,axis=1)[:,None]
    return tips,axes


def simulate_trials(n=200000, seed=335, marker_sigma=MARKER_SIGMA_MM):
    """Independent trials, with independent streams for markers and targets.

    Target standard normals are reused across sigma levels (common random
    numbers). At each level trials are independent; levels are paired.
    """
    if not isinstance(n,(int,np.integer)) or n<2:
        raise ValueError('At least two trials required')
    if not np.isfinite(marker_sigma) or marker_sigma<0:
        raise ValueError('Marker sigma must be finite and nonnegative')
    marker_seed,target_seed=np.random.SeedSequence(seed).spawn(2)
    marker_rng=np.random.default_rng(marker_seed)
    target_rng=np.random.default_rng(target_seed)
    observations=MARKERS_MODEL+marker_rng.normal(0,marker_sigma,(n,len(MARKERS_MODEL),3))
    tips,axes=register_many(MARKERS_MODEL,observations,TIP_MODEL,AXIS_MODEL)
    return tips,axes,target_rng.normal(size=(n,3))


def compound_errors(tips, axes, target_standard_normals, sigma, depth=100.):
    """Return line-distance error and endpoint error after fixed insertion depth.

    This follows the exercise's perturbed-pose trajectory convention: the noisy
    registered pose defines the trajectory being compared to the displaced target.
    It is not a physical control-loop model of an unchanged tool plus mere display
    error. Calibration uncertainty is excluded to isolate the requested sources.
    """
    tips=np.asarray(tips,dtype=float); axes=np.asarray(axes,dtype=float)
    z=np.asarray(target_standard_normals,dtype=float)
    if tips.ndim!=2 or tips.shape[1]!=3 or axes.shape!=tips.shape or z.shape!=tips.shape:
        raise ValueError('Matching N x 3 arrays required')
    if not all(np.isfinite(a).all() for a in (tips,axes,z)):
        raise ValueError('Inputs must be finite')
    if not np.isfinite(sigma) or sigma<0 or not np.isfinite(depth) or depth<=0:
        raise ValueError('Nonnegative finite sigma and positive depth required')
    lengths=np.linalg.norm(axes,axis=1)
    if np.any(lengths<1e-12): raise ValueError('Nonzero directions required')
    axes=axes/lengths[:,None]
    planned_target=TIP_MODEL+depth*unit(AXIS_MODEL)
    displaced_target=planned_target+sigma*z
    delta=displaced_target-tips
    line_error=np.linalg.norm(np.cross(delta,axes),axis=1)
    endpoint_error=np.linalg.norm(displaced_target-(tips+depth*axes),axis=1)
    return line_error,endpoint_error


def wilson_interval(successes, n, confidence=.95):
    """Two-sided binomial Wilson interval for one fixed sigma and metric."""
    if n<=0 or not 0<=successes<=n or not 0<confidence<1:
        raise ValueError('Invalid binomial counts or confidence')
    z=norm.ppf((1+confidence)/2)
    p=successes/n; denominator=1+z*z/n
    center=(p+z*z/(2*n))/denominator
    half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/denominator
    return max(0.,float(center-half)), min(1.,float(center+half))


def summarize_errors(errors, threshold=3.):
    errors=np.asarray(errors,dtype=float)
    if errors.ndim!=1 or len(errors)<2 or not np.isfinite(errors).all() or np.any(errors<0):
        raise ValueError('Finite nonnegative error samples required')
    successes=int(np.count_nonzero(errors<=threshold))
    low,high=wilson_interval(successes,len(errors))
    status='supported_pass' if low>=.95 else ('supported_fail' if high<.95 else 'uncertain')
    return {'n':len(errors),'successes':successes,'success_probability':successes/len(errors),
            'wilson95_low':low,'wilson95_high':high,
            'mean_error_mm':float(errors.mean()),'median_error_mm':float(np.median(errors)),
            'p95_error_mm':float(np.quantile(errors,.95)), 'status':status}


def sweep(tips, axes, z, sigmas, depth=100.):
    levels=np.asarray(sigmas,dtype=float)
    if levels.ndim!=1 or len(levels)==0 or not np.isfinite(levels).all() or np.any(levels<0):
        raise ValueError('Finite nonnegative sigma levels required')
    rows=[]
    for sigma in levels:
        line,endpoint=compound_errors(tips,axes,z,float(sigma),depth)
        rows.append({'target_sigma_mm':float(sigma),
                     'trajectory':summarize_errors(line),'endpoint':summarize_errors(endpoint)})
    return rows

# Author: Serhat Yaylacam
