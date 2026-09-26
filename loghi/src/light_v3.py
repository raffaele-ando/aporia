import sys, pickle; sys.path.insert(0,'src')
import numpy as np
from scipy.ndimage import gaussian_filter, median_filter
from levels import level_paths
from warp_field import build_warp, warp_path_d
from symmetrize import transform
p = np.load('src/align_refined.npy'); sx,sy,tx,ty,sh=p
M=np.array([[sx,sh],[0,sy]]); t=np.array([tx,ty]); Minv=np.linalg.inv(M)
Y_MID=(892.578+220.708)/2; Mf=np.array([[sx,0.0],[0,sy]]); tf=np.array([tx+sh*Y_MID, ty])
W1 = build_warp(np.load('src/contour_dust.npy'), np.load('src/contour_dust_regular.npy'), stride=6, smoothing=8.0)
class AW:
    def __call__(self, q):
        q=np.asarray(q,float); return (transform((q-t) @ Minv.T) @ Mf.T + tf) - q
W2 = AW()
def field(med, sig):
    g_ext = np.load('src/g_ext.npy')
    F = median_filter(g_ext, size=med) if med > 1 else g_ext
    return gaussian_filter(F, sig)
def levels(med, sig, N=20, eps=2.0, min_area=150):
    F = field(med, sig); out=[]
    for i in range(1, N):
        d = level_paths(F, i/N, min_area=min_area, eps=eps, prec=1)
        if d: out.append(((i+0.5)/N, warp_path_d(warp_path_d(d, W1, prec=2), W2, prec=1)))
    return out
