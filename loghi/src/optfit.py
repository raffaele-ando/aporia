"""Fit a G1 chain of K cubic Beziers to an open arc, minimising distance to samples."""
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree

def chain_points(params, P0, P1, K, fix_t1=None, fix_t2=None):
    """Decode parameter vector -> list of K cubic control arrays.
    params layout:
      a1                      (len of first handle)
      [th1]                   (angle of first tangent, if not fixed)
      for each interior join j=1..K-1:  x, y, theta, lin, lout
      [th2]                   (angle of last tangent, if not fixed)
      a2                      (len of last handle)
    """
    idx = 0
    a1 = params[idx]; idx += 1
    if fix_t1 is None:
        th1 = params[idx]; idx += 1
        t1 = np.array([np.cos(th1), np.sin(th1)])
    else:
        t1 = fix_t1
    joins = []
    for _ in range(K-1):
        x, y, th, lin, lout = params[idx:idx+5]; idx += 5
        joins.append((np.array([x,y]), np.array([np.cos(th), np.sin(th)]), lin, lout))
    if fix_t2 is None:
        th2 = params[idx]; idx += 1
        t2 = np.array([np.cos(th2), np.sin(th2)])
    else:
        t2 = fix_t2
    a2 = params[idx]; idx += 1

    pts = [P0] + [j[0] for j in joins] + [P1]
    ctrls = []
    for k in range(K):
        p_start, p_end = pts[k], pts[k+1]
        if k == 0:
            c1 = p_start + t1*abs(a1)
        else:
            _, tj, lin, lout = joins[k-1]
            c1 = p_start + tj*abs(lout)
        if k == K-1:
            c2 = p_end - t2*abs(a2)
        else:
            _, tj, lin, lout = joins[k]
            c2 = p_end - tj*abs(lin)
        ctrls.append(np.array([p_start, c1, c2, p_end]))
    return ctrls

def sample_chain(ctrls, n_per=200):
    out = []
    for c in ctrls:
        t = np.linspace(0, 1, n_per)[:, None]
        mt = 1-t
        out.append(mt**3*c[0] + 3*mt**2*t*c[1] + 3*mt*t**2*c[2] + t**3*c[3])
    return np.vstack(out)

def residuals(params, pts, P0, P1, K, fix_t1, fix_t2, n_per):
    ctrls = chain_points(params, P0, P1, K, fix_t1, fix_t2)
    S = sample_chain(ctrls, n_per)
    tree = cKDTree(S)
    d, _ = tree.query(pts)
    return d

def init_params(pts, P0, P1, K, fix_t1, fix_t2):
    n = len(pts)
    idxs = [int(round(i*(n-1)/K)) for i in range(K+1)]
    p = []
    seg_len = np.linalg.norm(P1-P0)/max(K,1)
    def tang(i):
        lo, hi = max(0, i-8), min(n-1, i+8)
        v = pts[hi]-pts[lo]; nv = np.linalg.norm(v)
        return v/nv if nv > 0 else np.array([1.0,0.0])
    t1 = fix_t1 if fix_t1 is not None else tang(0)
    p.append(seg_len/3)
    if fix_t1 is None: p.append(np.arctan2(t1[1], t1[0]))
    for k in range(1, K):
        i = idxs[k]; q = pts[i]; t = tang(i)
        p += [q[0], q[1], np.arctan2(t[1], t[0]), seg_len/3, seg_len/3]
    t2 = fix_t2 if fix_t2 is not None else tang(n-1)
    if fix_t2 is None: p.append(np.arctan2(t2[1], t2[0]))
    p.append(seg_len/3)
    return np.array(p, dtype=float)

def fit_arc(pts, P0, P1, K, fix_t1=None, fix_t2=None, n_per=120, max_nfev=300, stride=None):
    x0 = init_params(pts, P0, P1, K, fix_t1, fix_t2)
    if stride is None:
        stride = max(1, len(pts)//180)
    fit_pts = pts[::stride]
    if not np.allclose(fit_pts[-1], pts[-1]):
        fit_pts = np.vstack([fit_pts, pts[-1]])
    method = 'lm' if len(fit_pts) > len(x0) else 'trf'
    res = least_squares(residuals, x0, args=(fit_pts, P0, P1, K, fix_t1, fix_t2, n_per),
                        method=method, max_nfev=max_nfev, xtol=1e-11, ftol=1e-11)
    ctrls = chain_points(res.x, P0, P1, K, fix_t1, fix_t2)
    S = sample_chain(ctrls, 600)
    d, _ = cKDTree(S).query(pts)
    return ctrls, float(d.max()), float(np.sqrt((d**2).mean()))
