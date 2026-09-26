import sys, pickle; sys.path.insert(0,'src')
import numpy as np
from build2 import smooth_closed, detect_corners, split_fillets, build_path
from symmetrize import BASE, TOP, LF, RF, CENTER, APEX_L, APEX_R, left_outer, right_outer, W_HORIZ
xy = np.load('src/contour_sym.npy')
xys = smooth_closed(xy, 0.5)
corners = sorted(set(split_fillets(xys, detect_corners(xys)) + [2024, 363]))
print('corners', len(corners), flush=True)
verts, segs, rep = build_path(xys, corners, target_err=0.2, kmax=8)
verts = [np.array(v, float) for v in verts]
print('segmenti', len(segs))

# --- snap esatto dei vertici chiave ---
def snap(v):
    if abs(v[1]-BASE) < 1.2: v[1] = BASE
    if abs(v[1]-TOP)  < 1.2: v[1] = TOP
    return v
for v in verts: snap(v)
# vertici della base e della cima sui valori esatti
for v in verts:
    if v[1] == BASE:
        if abs(v[0]-LF) < 2.0: v[0] = LF
        if abs(v[0]-RF) < 2.0: v[0] = RF
        if abs(v[0]-(LF+W_HORIZ)) < 3.0: v[0] = LF + W_HORIZ
        if abs(v[0]-(RF-W_HORIZ)) < 3.0: v[0] = RF - W_HORIZ
    if v[1] == TOP:
        if abs(v[0]-APEX_L) < 2.5: v[0] = APEX_L
        if abs(v[0]-APEX_R) < 2.5: v[0] = APEX_R
np.save('src/sym_verts.npy', np.array(verts)); pickle.dump(segs, open('src/sym_segs.pkl','wb'))
f = lambda v: f"{round(v[0],2):g} {round(v[1],2):g}"
d = "M"+f(verts[0]) + "".join(("L"+f(s[1])) if s[0]=='L' else ("C"+f(s[1])+" "+f(s[2])+" "+f(s[3])) for s in segs) + "Z"
open('src/d_sym_imgcoords.txt','w').write(d)
print('d len', len(d))
for i,v in enumerate(verts):
    if v[1] in (BASE, TOP): print(f'  V{i}: ({v[0]:.2f},{v[1]:.2f})')
