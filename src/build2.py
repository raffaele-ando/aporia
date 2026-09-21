"""Adaptive hybrid builder: lines + optimised G1 Bezier chains."""
import numpy as np
from scipy.ndimage import gaussian_filter1d
from corners import turning
from optfit import fit_arc
from build_shape import tls_line, line_intersect, project

def smooth_closed(xy, sigma):
    if sigma <= 0: return xy.copy()
    return np.stack([gaussian_filter1d(xy[:, i], sigma, mode='wrap') for i in range(2)], axis=1)

def detect_corners(xy, scales=((6,10),(10,16),(14,22),(20,28)), min_gap=8, merge=12):
    N = len(xy); allc = set()
    for k, thr in scales:
        t = turning(xy, k); mag = np.abs(t)
        idx = np.where(mag > np.radians(thr))[0]
        if len(idx) == 0: continue
        groups, start, prev = [], idx[0], idx[0]
        for i in idx[1:]:
            if i - prev > min_gap: groups.append((start, prev)); start = i
            prev = i
        groups.append((start, prev))
        for a, b in groups:
            seg = np.arange(a, b+1)
            allc.add(int(seg[np.argmax(mag[seg])]))
    cands = sorted(allc); grouped = []
    for c in cands:
        if grouped and (c - grouped[-1][-1]) <= merge: grouped[-1].append(c)
        else: grouped.append([c])
    if len(grouped) > 1 and (grouped[0][0] + N - grouped[-1][-1]) <= merge:
        grouped[0] = grouped[-1] + grouped[0]; grouped.pop()
    t14 = turning(xy, 14)
    return sorted(int(max(g, key=lambda c: abs(t14[c]))) for g in grouped)

def split_fillets(xy, corners, k=4, thr_deg=6.0, min_span=8, pad=1):
    """Replace a corner whose curvature is spread over many points (a fillet)
    with two break points at the fillet boundaries."""
    N = len(xy); t = np.abs(turning(xy, k)); thr = np.radians(thr_deg)
    out = []
    for c in corners:
        lo = c
        while t[(lo-1) % N] > thr and (c - lo) < 60: lo -= 1
        hi = c
        while t[(hi+1) % N] > thr and (hi - c) < 60: hi += 1
        span = hi - lo
        if span >= min_span:
            out.append((lo - pad) % N); out.append((hi + pad) % N)
        else:
            out.append(c % N)
    return sorted(set(int(x) for x in out))

def build_path(xy, corners, straight_tol=0.5, trim=0.10, target_err=0.25, kmax=9):
    N, M = len(xy), len(corners)
    def arc(a, b): return xy[a:b+1] if b > a else np.vstack([xy[a:], xy[:b+1]])
    arcs = []
    for i in range(M):
        a, b = corners[i], corners[(i+1) % M]
        seg = arc(a, b)
        t = max(3, int(len(seg)*trim)); core = seg[t:-t] if len(seg) > 2*t+4 else seg
        c, d, mx = tls_line(core)
        if np.dot(seg[-1]-seg[0], d) < 0: d = -d
        arcs.append(dict(i=i, pts=seg, line=(c, d), lerr=mx, straight=mx < straight_tol))
    verts = []
    for i in range(M):
        prev, nxt = arcs[(i-1) % M], arcs[i]
        p = xy[corners[i]]
        if prev['straight'] and nxt['straight']:
            v = line_intersect(*prev['line'], *nxt['line']); verts.append(v if v is not None else p)
        elif prev['straight']: verts.append(project(p, *prev['line']))
        elif nxt['straight']:  verts.append(project(p, *nxt['line']))
        else: verts.append(p)
    segs, report = [], []
    for i in range(M):
        A = arcs[i]; v0, v1 = verts[i], verts[(i+1) % M]
        if A['straight']:
            segs.append(('L', v1)); report.append((i, 'line', A['lerr'], 1)); continue
        pts = A['pts'].copy(); pts[0] = v0; pts[-1] = v1
        prev, nxt = arcs[(i-1) % M], arcs[(i+1) % M]
        best = None
        for K in range(2, kmax+1):
            ctrls, mx, rms = fit_arc(pts, v0, v1, K)
            if best is None or mx < best[1]: best = (ctrls, mx, rms, K)
            if mx < target_err: best = (ctrls, mx, rms, K); break
        ctrls, mx, rms, K = best
        for c in ctrls: segs.append(('C', c[1], c[2], c[3]))
        report.append((i, 'curve', mx, K))
    return verts, segs, report

def to_d(verts, segs, prec=2, sx=1.0, sy=1.0, ox=0.0, oy=0.0):
    def f(v): return f"{round((v[0]-ox)*sx, prec):g} {round((v[1]-oy)*sy, prec):g}"
    d = [f"M{f(verts[0])}"]
    for s in segs:
        d.append(f"L{f(s[1])}" if s[0] == 'L' else f"C{f(s[1])} {f(s[2])} {f(s[3])}")
    return "".join(d) + "Z"
