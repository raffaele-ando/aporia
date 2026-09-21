import sys; sys.path.insert(0,'work')
import numpy as np, re
from PIL import Image
from build2 import smooth_closed, detect_corners, split_fillets, build_path
from compare import render_path, metrics, gray_metrics

ref = np.array(Image.open('src/src_clean.webp').convert('L')); H, W = ref.shape
mask = ref < 128
xy0 = np.load('src/contour_clean.npy')[:-1] + 0.5
xy = smooth_closed(xy0, 0.4)
corners = split_fillets(xy, detect_corners(xy))
verts, segs, rep = build_path(xy, corners, target_err=0.18, kmax=8)
verts = [np.array(v, float) for v in verts]

# ---- snap axis-aligned design features ----
def snap_group(idxs, axis, tol=0.6):
    vals = np.array([verts[i][axis] for i in idxs])
    if vals.max()-vals.min() > tol: return None
    tgt = vals.mean()
    deltas = {}
    for i in idxs:
        deltas[i] = tgt - verts[i][axis]
        verts[i][axis] = tgt
    return deltas

groups = [([0, 11, 12, 19], 1),   # bottom baseline y
          ([13, 14], 1),          # apex top y
          ([1, 2], 0),            # left tip x
          ([3, 4], 0),            # river right tip x
          ([15, 16], 0),          # right bulge x
          ([5, 6], 1),            # counter bottom tip y
          ([9, 10], 0),           # river bank tip x
          ]
all_deltas = {}
for idxs, axis in groups:
    dd = snap_group(idxs, axis)
    if dd:
        for i, dv in dd.items(): all_deltas.setdefault(i, np.zeros(2))[axis] += dv
        print(f'snapped {idxs} axis={axis} -> {verts[idxs[0]][axis]:.3f}')

# rebuild segment list applying vertex deltas to endpoints + adjacent handles
M = len(verts)
seg_owner = []   # which vertex each segment ends at, and which it starts from
vi = 0; start_v = 0
out = []
# reconstruct mapping: iterate segs, tracking arcs -> we know each arc ends at next vertex
arc_lengths = []
for i, kind, err, K in rep:
    arc_lengths.append(1 if kind == 'line' else K)
pos = 0
for ai, n in enumerate(arc_lengths):
    v_start, v_end = ai, (ai+1) % M
    d0 = all_deltas.get(v_start, np.zeros(2)); d1 = all_deltas.get(v_end, np.zeros(2))
    for k in range(n):
        s = segs[pos]; pos += 1
        if s[0] == 'L':
            out.append(('L', verts[v_end].copy()))
        else:
            c1, c2, p = [np.array(x, float) for x in s[1:]]
            if k == 0: c1 = c1 + d0
            if k == n-1:
                c2 = c2 + d1; p = verts[v_end].copy()
            out.append(('C', c1, c2, p))

def to_d(verts, segs, prec=3, ox=0.0, oy=0.0, sx=1.0, sy=1.0):
    def f(v):
        return f"{round((v[0]-ox)*sx, prec):g} {round((v[1]-oy)*sy, prec):g}"
    d = [f"M{f(verts[0])}"]
    for s in segs:
        d.append(f"L{f(s[1])}" if s[0]=='L' else f"C{f(s[1])} {f(s[2])} {f(s[3])}")
    return "".join(d) + "Z"

d_img = to_d(verts, out, prec=3)
ren = render_path(d_img, W, H)
mm = metrics(mask, ren); gm = gray_metrics(ref, ren)
print(f'AFTER SNAP: IoU={mm["iou"]:.6f} xor={mm["xor_px"]} rmse={gm["rmse"]:.5f} segs={len(out)}')
open('src/d_clean_final_imgcoords.txt','w').write(d_img)

xs = [verts[i][0] for i in range(M)]; ys = [verts[i][1] for i in range(M)]
allpts = np.array([p for s in out for p in ([s[1]] if s[0]=='L' else [s[1],s[2],s[3]])])
minx, maxx = allpts[:,0].min(), allpts[:,0].max()
miny, maxy = allpts[:,1].min(), allpts[:,1].max()
print('geometry bbox', minx, maxx, miny, maxy, 'w', maxx-minx, 'h', maxy-miny)
np.save('src/final_verts.npy', np.array(verts))
import pickle
pickle.dump(out, open('src/final_segs.pkl','wb'))
