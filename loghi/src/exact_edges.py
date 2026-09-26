"""Sostituisce i tratti che giacciono sulle rette di costruzione con rette esatte."""
import numpy as np
from symmetrize import BASE, TOP, left_inner, right_inner, left_outer, right_outer

LINES = [('asta sx interna', left_inner, 600.0), ('gamba dx interna', right_inner, 700.0),
         ('diagonale sx esterna', left_outer, TOP), ('gamba dx esterna', right_outer, 700.0)]

def _points(verts, segs):
    pts = [np.array(verts[0], float)]
    for s in segs: pts.append(np.array(s[-1], float))
    return pts

def _near(fn, p, ymin, tol):
    return p[1] >= ymin - 1e-6 and abs(p[0] - fn(p[1])) <= tol

def exactify(verts, segs, tol=2.0):
    segs = [tuple([s[0]] + [np.array(v, float) for v in s[1:]]) for s in segs]
    log = []
    for name, fn, ymin in LINES:
        pts = _points(verts, segs)
        on = []
        for i, s in enumerate(segs):
            ctrl = [pts[i], pts[i+1]] + ([s[1], s[2]] if s[0] == 'C' else [])
            on.append(all(_near(fn, c, ymin, tol) for c in ctrl))
        i = 0; new = []
        while i < len(segs):
            if not on[i]:
                new.append(segs[i]); i += 1; continue
            j = i
            while j < len(segs) and on[j]: j += 1
            a, b = pts[i].copy(), pts[j].copy()
            a[0] = fn(a[1]); b[0] = fn(b[1])
            # riallinea la fine del segmento precedente
            if new:
                prev = new[-1]
                dx = a - np.array(prev[-1], float)
                if prev[0] == 'C':
                    new[-1] = ('C', prev[1], prev[2] + dx, a)
                else:
                    new[-1] = ('L', a)
            new.append(('L', b))
            # riallinea l'inizio del segmento successivo (maniglia c1)
            if j < len(segs) and segs[j][0] == 'C':
                dx = b - pts[j]
                s = segs[j]; segs[j] = ('C', s[1] + dx, s[2], s[3])
            log.append(f'{name}: {j-i} segmenti -> 1 retta')
            i = j
        segs = new
    # base e cima: y esatte
    fixed = []
    for s in segs:
        pts_ = [np.array(v, float) for v in s[1:]]
        for p in pts_:
            if abs(p[1] - BASE) < 0.6: p[1] = BASE
            if abs(p[1] - TOP) < 0.6:  p[1] = TOP
        fixed.append(tuple([s[0]] + pts_))
    v0 = np.array(verts[0], float)
    if abs(v0[1] - BASE) < 0.6: v0[1] = BASE
    verts = [v0] + list(verts[1:])
    # il primo punto coincide con la fine dell'ultimo segmento
    verts[0] = np.array(fixed[-1][-1], float)
    return verts, fixed, log

def exact_corners(verts, segs, radius=6.0):
    """Elimina i micro-raccordi attorno agli spigoli di costruzione e porta gli
    spigoli sulle coordinate esatte."""
    from symmetrize import LF, RF, W_HORIZ, APEX_L, APEX_R
    corners = [(LF, BASE), (LF + W_HORIZ, BASE), (RF - W_HORIZ, BASE), (RF, BASE),
               (APEX_L, TOP), (APEX_R, TOP)]
    log = []
    for cx, cy in corners:
        c = np.array([cx, cy])
        pts = _points(verts, segs)
        # 1) togli i segmenti che iniziano e finiscono vicino allo spigolo
        keep = []
        removed = 0
        for i, s in enumerate(segs):
            if np.linalg.norm(pts[i]-c) < radius and np.linalg.norm(pts[i+1]-c) < radius:
                removed += 1; continue
            keep.append(s)
        segs = keep
        # 2) porta sullo spigolo il punto più vicino (fine di un segmento)
        pts = _points(verts, segs)
        k = int(np.argmin([np.linalg.norm(p - c) for p in pts[1:]]))
        d = c - pts[k+1]
        s = segs[k]
        if s[0] == 'C': segs[k] = ('C', s[1], s[2] + d, c.copy())
        else:           segs[k] = ('L', c.copy())
        nxt = (k + 1) % len(segs)
        # l'inizio del segmento successivo ora è c: se è una retta va bene,
        # se è una curva sposta la sua prima maniglia dello stesso delta
        if segs[nxt][0] == 'C':
            s2 = segs[nxt]; segs[nxt] = ('C', s2[1] + d, s2[2], s2[3])
        if removed or np.linalg.norm(d) > 1e-3:
            log.append(f'spigolo ({cx:.2f},{cy:.2f}): rimossi {removed} micro-segmenti, correzione {np.linalg.norm(d):.2f}')
    verts = [np.array(segs[-1][-1], float)] + list(verts[1:])
    return verts, segs, log

def straighten(verts, segs, tol=0.05):
    """Una curva con entrambi gli estremi sulla stessa retta di costruzione diventa retta;
    rette consecutive allineate vengono fuse."""
    log = []
    pts = _points(verts, segs)
    out = []
    for i, s in enumerate(segs):
        a, b = pts[i], pts[i+1]
        if s[0] == 'C':
            for name, fn, ymin in LINES:
                if min(a[1], b[1]) >= ymin - 1 and abs(a[0]-fn(a[1])) < tol and abs(b[0]-fn(b[1])) < tol:
                    s = ('L', b.copy()); log.append(f'{name}: curva -> retta'); break
        out.append(s)
    # fusione di rette collineari
    pts = _points(verts, out)
    merged = []
    for i, s in enumerate(out):
        if merged and s[0] == 'L' and merged[-1][0] == 'L':
            a = pts[i-1] if len(merged) else pts[0]
            p0 = _points(verts, merged)[-2]; p1 = np.array(merged[-1][1]); p2 = np.array(s[1])
            u, v = p1 - p0, p2 - p1
            cross = abs(u[0]*v[1] - u[1]*v[0]) / (np.linalg.norm(u)*np.linalg.norm(v) + 1e-12)
            if cross < 1e-4 and np.dot(u, v) > 0:
                merged[-1] = ('L', p2.copy()); log.append('rette collineari fuse'); continue
        merged.append(s)
    return verts, merged, log
