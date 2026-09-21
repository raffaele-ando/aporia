"""Schneider-style cubic Bezier fitting with corner constraints + line detection."""
import numpy as np

def _q(ctrl, t):
    mt = 1 - t
    return (mt**3)[:,None]*ctrl[0] + (3*mt**2*t)[:,None]*ctrl[1] + (3*mt*t**2)[:,None]*ctrl[2] + (t**3)[:,None]*ctrl[3]

def chord_params(pts):
    d = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    u = np.concatenate([[0], np.cumsum(d)])
    return u / u[-1] if u[-1] > 0 else u

def generate_bezier(pts, u, t1, t2):
    n = len(pts)
    A = np.zeros((n, 2, 2))
    mt = 1 - u
    A[:,0] = (3*mt**2*u)[:,None] * t1
    A[:,1] = (3*mt*u**2)[:,None] * t2
    C = np.zeros((2,2)); X = np.zeros(2)
    p0, p3 = pts[0], pts[-1]
    tmp = pts - ((mt**3)[:,None]*p0 + (3*mt**2*u)[:,None]*p0 + (3*mt*u**2)[:,None]*p3 + (u**3)[:,None]*p3)
    C[0,0] = np.sum(A[:,0]*A[:,0]); C[0,1] = np.sum(A[:,0]*A[:,1])
    C[1,0] = C[0,1];                C[1,1] = np.sum(A[:,1]*A[:,1])
    X[0] = np.sum(A[:,0]*tmp);      X[1] = np.sum(A[:,1]*tmp)
    det_C = C[0,0]*C[1,1] - C[1,0]*C[0,1]
    det_X0 = X[0]*C[1,1] - C[0,1]*X[1]
    det_X1 = C[0,0]*X[1] - X[0]*C[1,0]
    seg = np.linalg.norm(p3-p0)
    if abs(det_C) < 1e-12:
        a1 = a2 = seg/3.0
    else:
        a1, a2 = det_X0/det_C, det_X1/det_C
        if a1 < 1e-6 or a2 < 1e-6:
            a1 = a2 = seg/3.0
    return np.array([p0, p0 + a1*t1, p3 + a2*t2, p3])

def reparameterize(ctrl, pts, u):
    def qprime(t):
        mt = 1-t
        return 3*(mt**2)[:,None]*(ctrl[1]-ctrl[0]) + 6*(mt*t)[:,None]*(ctrl[2]-ctrl[1]) + 3*(t**2)[:,None]*(ctrl[3]-ctrl[2])
    def qprimeprime(t):
        mt = 1-t
        return 6*(mt)[:,None]*(ctrl[2]-2*ctrl[1]+ctrl[0]) + 6*(t)[:,None]*(ctrl[3]-2*ctrl[2]+ctrl[1])
    d = _q(ctrl, u) - pts
    d1 = qprime(u); d2 = qprimeprime(u)
    num = np.sum(d*d1, axis=1)
    den = np.sum(d1*d1, axis=1) + np.sum(d*d2, axis=1)
    out = np.where(np.abs(den) < 1e-12, u, u - num/den)
    return np.clip(out, 0, 1)

def max_error(ctrl, pts, u):
    d = np.linalg.norm(_q(ctrl, u) - pts, axis=1)
    i = int(np.argmax(d))
    return d[i], i

def fit_cubic(pts, t1, t2, tol, depth=0, max_depth=24):
    """Returns list of control-point arrays (4x2)."""
    if len(pts) == 2:
        seg = np.linalg.norm(pts[1]-pts[0])/3.0
        return [np.array([pts[0], pts[0]+t1*seg, pts[1]+t2*seg, pts[1]])]
    u = chord_params(pts)
    ctrl = generate_bezier(pts, u, t1, t2)
    err, split = max_error(ctrl, pts, u)
    if err < tol:
        return [ctrl]
    if err < tol*16 and depth < 12:
        for _ in range(24):
            u = reparameterize(ctrl, pts, u)
            ctrl = generate_bezier(pts, u, t1, t2)
            err, split = max_error(ctrl, pts, u)
            if err < tol:
                return [ctrl]
    if depth >= max_depth:
        return [ctrl]
    split = int(np.clip(split, 1, len(pts)-2))
    # centre tangent at split
    v = pts[split+1] - pts[split-1]
    nv = np.linalg.norm(v)
    tc = v/nv if nv > 0 else np.array([1.0, 0.0])
    left = fit_cubic(pts[:split+1], t1, -tc, tol, depth+1, max_depth)
    right = fit_cubic(pts[split:], tc, t2, tol, depth+1, max_depth)
    return left + right

def line_error(pts):
    """max distance of pts from the chord p0->p_last"""
    p0, p1 = pts[0], pts[-1]
    v = p1 - p0; L = np.linalg.norm(v)
    if L < 1e-9:
        return np.linalg.norm(pts - p0, axis=1).max()
    n = np.array([-v[1], v[0]])/L
    return np.abs((pts - p0) @ n).max()
