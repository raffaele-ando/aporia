"""Campo luminoso v4.
Bordi netti (contorno esterno della A): la luce viene prolungata oltre la sagoma, così
la correzione della lettera non lascia bordi scuri. Bordi morbidi (fiume, bandiera): si
usa la luce vera dell'immagine, che sfuma da sola, e la sagoma lì non taglia nulla."""
import sys, pickle; sys.path.insert(0, 'src')
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt, gaussian_filter, median_filter
from levels import level_paths
from warp_field import warp_path_d
import light_v3 as L

def build_field():
    R = np.array(Image.open('src/src_dust.webp').convert('L'))/255.
    M = np.array(Image.open('src/dust_shape_mask.png').convert('L')) > 127
    din = distance_transform_edt(M); dout = distance_transform_edt(~M)
    def ncv(sel, s=5): return gaussian_filter(R*sel, s)/(gaussian_filter(sel*1., s)+1e-6)
    o = ncv((dout >= 3) & (dout < 10)); i = ncv((din >= 3) & (din < 9))
    soft = np.clip((o/(i+0.03) - 0.12)/0.2, 0, 1)          # 1 = la luce esce dalla sagoma
    bnd = (dout > 0) & (dout < 2)
    _, (by, bx) = distance_transform_edt(~bnd, return_indices=True)
    S = gaussian_filter(soft[by, bx], 8)
    core = din >= 3
    _, (iy, ix) = distance_transform_edt(~core, return_indices=True)
    near = R[iy, ix]
    hard = R.copy(); rim = M & ~core; hard[rim] = near[rim]
    # prolungamento solo fin dove la correzione ha spostato i bordi (max ~14 px), poi sfuma
    fade = np.clip((24 - dout)/8, 0, 1)
    out = ~M; hard[out] = np.maximum(R[out], near[out]*fade[out])
    Hw = np.clip((0.8 - S)/0.6, 0, 1)                    # peso dei bordi netti
    G = R + Hw*(hard - R)
    G[dout > 45] = 0
    zone = (S > 0.5) & (M | (dout < 40))
    return G, S, zone

def inverse_map(step=2):
    """per ogni pixel del disegno corretto, il punto dell'immagine da cui prendere la luce
    (si deforma il raster, non i tracciati: niente livelli che si accavallano)"""
    from scipy.interpolate import griddata
    ys, xs = np.mgrid[150:1100:step, 150:1150:step]
    src = np.stack([xs.ravel(), ys.ravel()], 1).astype(float) + 0.5
    p1 = src + L.W1(src); dst = p1 + L.W2(p1)
    gy, gx = np.mgrid[0:1254, 0:1254]
    q = np.stack([gx.ravel()+0.5, gy.ravel()+0.5], 1)
    inv = griddata(dst, src, q, method='linear')
    ident = np.isnan(inv[:, 0]); inv[ident] = q[ident]
    return (inv - 0.5).reshape(1254, 1254, 2)

def warp_raster(A, inv):
    from scipy.ndimage import map_coordinates
    return map_coordinates(A, [inv[..., 1], inv[..., 0]], order=1, mode='constant')

def levels(Fw, N=48, eps=1.6, min_area=120):
    # soglie fitte ai due estremi (ombre e luci): niente gradini dove la luce cambia piano
    ts = [0.5 - 0.5*np.cos(np.pi*k/N) for k in range(1, N)] + [1.01]; out = []
    for k in range(len(ts)-1):
        d = level_paths(Fw, ts[k], min_area=min_area, eps=eps, prec=1)
        if d: out.append(((ts[k]+ts[k+1])/2, d))
    return out

def soft_levels(Sw, N=8):
    """morbidezza del bordo (0 = netto, 1 = decide solo la luce) come tracciati annidati"""
    out = []
    for k in range(1, N+1):
        t = (k - 0.5)/N
        d = level_paths(gaussian_filter(Sw, 3), t, min_area=150, eps=1.5, prec=1)
        if d: out.append((min(1.0, t + 0.5/N), d))
    return out

def zone_path(zone_w):
    return level_paths(gaussian_filter(zone_w, 2), 0.5, min_area=200, eps=1.2, prec=1)

if __name__ == '__main__':
    import re
    import eval_v3 as V
    G, S, zone = build_field()
    inv = inverse_map()
    zd = zone_path(warp_raster(zone*1., inv))
    sl = soft_levels(warp_raster(S, inv))
    Fw = warp_raster(gaussian_filter(median_filter(G, size=5), 3.0), inv)
    lv = levels(Fw)
    # il taglio del fiume scende sotto la base: la base resta netta, senza filo chiaro
    open_d = re.sub(r'(-?\d+\.?\d*) 966\.42', lambda m: f'{m.group(1)} 990', V.open_d)
    kl = pickle.load(open('src/kmap_v4_levels.pkl', 'rb'))
    pickle.dump(dict(hull=V.hull_d, open=open_d, zone=zd, levels=lv, glows=V.gw, klevels=kl, k_bg=0.87, slevels=sl),
                open('src/dust_v4_layers.pkl', 'wb'))
    print(len(lv), 'livelli')
