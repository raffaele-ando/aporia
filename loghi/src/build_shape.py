"""Build a clean hybrid line/bezier path from a sub-pixel contour."""
import numpy as np
from fitcurve import fit_cubic
from corners import find_corners

def tls_line(pts):
    c = pts.mean(axis=0)
    _, _, vt = np.linalg.svd(pts - c)
    d = vt[0] / np.linalg.norm(vt[0])
    resid = np.abs((pts - c) @ np.array([-d[1], d[0]]))
    return c, d, resid.max()

def line_intersect(p1, d1, p2, d2):
    A = np.array([[d1[0], -d2[0]], [d1[1], -d2[1]]])
    if abs(np.linalg.det(A)) < 1e-9:
        return None
    t = np.linalg.solve(A, p2 - p1)
    return p1 + t[0]*d1

def project(p, c, d):
    return c + np.dot(p - c, d) * d

def build(xy, k=14, thr_deg=22, min_gap=10, straight_tol=0.5, trim=0.10,
          curve_tol=0.12, corners_override=None):
    N = len(xy)
    if corners_override is not None:
        corners, _ = corners_override, None
    else:
        corners, _ = find_corners(xy, k=k, thr_deg=thr_deg, min_gap=min_gap)
    M = len(corners)

    def arc(a, b):
        return xy[a:b+1] if b > a else np.vstack([xy[a:], xy[:b+1]])

    arcs = []
    for i in range(M):
        a, b = corners[i], corners[(i+1) % M]
        seg = arc(a, b)
        t = max(3, int(len(seg)*trim))
        core = seg[t:-t] if len(seg) > 2*t+4 else seg
        c, d, mx = tls_line(core)
        # orient direction along travel
        if np.dot(seg[-1]-seg[0], d) < 0:
            d = -d
        arcs.append(dict(i=i, a=a, b=b, pts=seg, line=(c, d), lerr=mx,
                         straight=mx < straight_tol))

    # refine vertices
    verts = [None]*M
    for i in range(M):
        prev = arcs[(i-1) % M]      # arc ending at corner i
        nxt = arcs[i]               # arc starting at corner i
        p_raw = xy[corners[i]]
        if prev['straight'] and nxt['straight']:
            v = line_intersect(*prev['line'], *nxt['line'])
            verts[i] = v if v is not None else p_raw
        elif prev['straight']:
            verts[i] = project(p_raw, *prev['line'])
        elif nxt['straight']:
            verts[i] = project(p_raw, *nxt['line'])
        else:
            verts[i] = p_raw

    # build segments
    out = []   # list of ('L', p) or ('C', c1, c2, p)
    for i in range(M):
        A = arcs[i]
        v0, v1 = verts[i], verts[(i+1) % M]
        if A['straight']:
            out.append(('L', v1))
        else:
            pts = A['pts'].copy()
            pts[0] = v0; pts[-1] = v1
            # end tangents
            prev, nxt = arcs[(i-1) % M], arcs[(i+1) % M]
            if prev['straight']:
                t1 = A['pts'][min(8, len(pts)-1)] - v0
                # keep contour tangent (corner: no continuity constraint)
            t1 = _tangent(pts, 0, 10)
            t2 = -_tangent(pts[::-1], 0, 10)
            beziers = fit_cubic(pts, t1, -t2, A.get('tol', curve_tol))
            for bz in beziers:
                out.append(('C', bz[1], bz[2], bz[3]))
    return verts, out, arcs, corners

def _tangent(pts, idx, win):
    seg = pts[idx:idx+win+1]
    if len(seg) < 2:
        v = pts[-1]-pts[0]
    else:
        c = seg.mean(axis=0)
        _, _, vt = np.linalg.svd(seg - c)
        v = vt[0]
        if np.dot(v, seg[-1]-seg[0]) < 0: v = -v
    n = np.linalg.norm(v)
    return v/n if n > 0 else np.array([1.0, 0.0])

def to_d(verts, out, prec=2, sx=1.0, sy=1.0, ox=0.0, oy=0.0):
    def f(v):
        x = (v[0]-ox)*sx; y = (v[1]-oy)*sy
        return f"{round(x,prec):g} {round(y,prec):g}"
    d = [f"M{f(verts[0])}"]
    for s in out:
        if s[0] == 'L':
            d.append(f"L{f(s[1])}")
        else:
            d.append(f"C{f(s[1])} {f(s[2])} {f(s[3])}")
    d.append("Z")
    return "".join(d)
