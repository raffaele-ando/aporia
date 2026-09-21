import numpy as np
from skimage import measure

def rdp(points, eps):
    """iterative Douglas-Peucker"""
    n = len(points)
    if n < 3: return points
    keep = np.zeros(n, bool); keep[0] = keep[-1] = True
    stack = [(0, n-1)]
    while stack:
        i, j = stack.pop()
        if j <= i+1: continue
        p, q = points[i], points[j]
        seg = q - p; L = np.hypot(*seg)
        if L < 1e-9:
            d = np.hypot(*(points[i+1:j] - p).T)
        else:
            nrm = np.array([-seg[1], seg[0]])/L
            d = np.abs((points[i+1:j] - p) @ nrm)
        k = int(np.argmax(d))
        if d[k] > eps:
            k += i+1; keep[k] = True; stack += [(i,k),(k,j)]
    return points[keep]

def catmull_to_bezier_d(pts, closed=True, prec=1):
    """Smooth closed polyline -> cubic path data (Catmull-Rom)."""
    P = np.asarray(pts, float)
    if closed and np.allclose(P[0], P[-1]): P = P[:-1]
    n = len(P)
    if n < 3: return ""
    f = lambda v: f"{round(v[0],prec):g} {round(v[1],prec):g}"
    d = [f"M{f(P[0])}"]
    for i in range(n if closed else n-1):
        p0 = P[(i-1) % n]; p1 = P[i]; p2 = P[(i+1) % n]; p3 = P[(i+2) % n]
        c1 = p1 + (p2 - p0)/6.0
        c2 = p2 - (p3 - p1)/6.0
        d.append(f"C{f(c1)} {f(c2)} {f(p2)}")
    return "".join(d) + ("Z" if closed else "")

def level_paths(field, level, min_area=60, eps=1.2, prec=1):
    """Return SVG path data for all regions where field >= level."""
    cs = measure.find_contours(field, level)
    parts = []
    for c in cs:
        if len(c) < 8: continue
        xy = c[:, ::-1] + 0.5
        # area (shoelace)
        a = 0.5*np.abs(np.dot(xy[:,0], np.roll(xy[:,1],-1)) - np.dot(xy[:,1], np.roll(xy[:,0],-1)))
        if a < min_area: continue
        s = rdp(xy, eps)
        if len(s) < 4: continue
        parts.append(catmull_to_bezier_d(s, closed=True, prec=prec))
    return "".join(parts)
