"""Rende la gamba destra parallela e dello stesso peso dell'asta sinistra."""
import numpy as np, math

def fit_line_xy(P):
    """x = a*y + b  (adatta per bordi quasi verticali)"""
    a, b = np.polyfit(P[:,1], P[:,0], 1)
    resid = np.abs(np.polyval([a,b], P[:,1]) - P[:,0]).max()
    return a, b, resid

def build(W=152.4, i_full=(185, 430), i_blend_end=575,
          outer_idx=(4700, 4930), contour='src/contour_clean.npy'):
    xy = np.load(contour)[:-1] + 0.5
    n = len(xy)
    # 1. retta del bordo esterno della gamba (parte dritta)
    Pout = xy[outer_idx[0]:outer_idx[1]]
    a, b, res = fit_line_xy(Pout)
    ang = math.degrees(math.atan2(1, a))
    sin_a = math.sin(math.radians(ang))
    dx_horiz = W / sin_a                     # spessore orizzontale equivalente
    # 2. retta interna parallela, spostata verso l'interno (a sinistra)
    b_in = b - dx_horiz
    # 3. sposta i punti del bordo interno
    new = xy.copy()
    i0, i1 = i_full
    for i in range(i0, i_blend_end+1):
        y = xy[i,1]
        target_x = a*y + b_in
        if i <= i1:
            w = 1.0
        else:
            t = (i - i1)/(i_blend_end - i1)
            w = 0.5*(1+math.cos(math.pi*t))   # 1 -> 0 dolce
        new[i,0] = (1-w)*xy[i,0] + w*target_x
    # 4. angolo inferiore: interseca la linea interna con la baseline
    y_base = xy[i0,1]
    corner_x = a*y_base + b_in
    keep = np.ones(n, bool)
    for i in range(0, i0):
        if new[i,0] < corner_x - 0.25: keep[i] = False
    new[i0] = [corner_x, y_base]
    out = new[keep]
    info = dict(angolo=ang, spessore_orizzontale=dx_horiz, corner_x=corner_x,
                retta_esterna=(a,b), residuo_retta=res, rimossi=int((~keep).sum()))
    return out, info

if __name__ == '__main__':
    out, info = build()
    for k,v in info.items(): print(f'  {k}: {v}')
    np.save('src/contour_regular.npy', out)
    print('punti', len(out))
