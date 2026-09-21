"""Deforma i tracciati del campo luminoso per farli seguire la nuova sagoma."""
import sys, re; sys.path.insert(0,'src')
import numpy as np
from scipy.interpolate import RBFInterpolator

def regular_contour_full(W=152.4, i_full=(185,470), i_blend_end=592, outer_idx=(4700,4930)):
    """come regularize.build ma mantiene tutti i punti (clamp invece di drop)"""
    import math
    xy = np.load('src/contour_clean.npy')[:-1] + 0.5
    P = xy[outer_idx[0]:outer_idx[1]]
    a, b = np.polyfit(P[:,1], P[:,0], 1)
    ang = math.degrees(math.atan2(1, a)); sin_a = math.sin(math.radians(ang))
    b_in = b - W/sin_a
    new = xy.copy()
    i0, i1 = i_full
    for i in range(i0, i_blend_end+1):
        tgt = a*xy[i,1] + b_in
        w = 1.0 if i <= i1 else 0.5*(1+math.cos(math.pi*(i-i1)/(i_blend_end-i1)))
        new[i,0] = (1-w)*xy[i,0] + w*tgt
    corner_x = a*xy[i0,1] + b_in
    new[i0] = [corner_x, xy[i0,1]]
    for i in range(0, i0):                       # bordo inferiore: clamp
        if new[i,0] < corner_x: new[i,0] = corner_x
    return new

def build_warp(src_pts, dst_pts, stride=6, smoothing=8.0):
    S = src_pts[::stride]; D = dst_pts[::stride]
    return RBFInterpolator(S, D - S, kernel='thin_plate_spline', smoothing=smoothing)

def warp_path_d(d, warp, prec=1):
    """applica il warp a tutti i punti di un path d (solo M/L/C con coordinate assolute)"""
    tokens = re.findall(r'[MLCZ]|-?\d+\.?\d*', d)
    nums, idxs = [], []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t in 'MLC':
            n = {'M':2,'L':2,'C':6}[t]
            for k in range(0, n, 2):
                nums.append((float(tokens[i+1+k]), float(tokens[i+2+k])))
                idxs.append(i+1+k)
            i += 1+n
        else:
            i += 1
    if not nums: return d
    pts = np.array(nums)
    out = pts + warp(pts)
    for (ix, p) in zip(idxs, out):
        tokens[ix]   = f'{round(float(p[0]),prec):g}'
        tokens[ix+1] = f'{round(float(p[1]),prec):g}'
    # ricompone
    res, i = [], 0
    while i < len(tokens):
        t = tokens[i]
        if t in 'MLC':
            n = {'M':2,'L':2,'C':6}[t]
            vals = tokens[i+1:i+1+n]
            if t == 'C':
                res.append('C' + ' '.join(f'{vals[k]} {vals[k+1]}' for k in (0,2,4)))
            else:
                res.append(t + f'{vals[0]} {vals[1]}')
            i += 1+n
        else:
            res.append(t); i += 1
    return ''.join(res)

def affine_path_d(d, M, t, prec=2):
    class A:
        def __call__(self, pts):
            return pts @ M.T + t - pts
    return warp_path_d(d, A(), prec=prec)
