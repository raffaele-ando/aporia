import sys, pickle; sys.path.insert(0,'work')
import numpy as np
from build2 import smooth_closed, detect_corners, split_fillets, build_path
xy = np.load('src/contour_dust.npy')
xys = smooth_closed(xy, 0.5)
corners = split_fillets(xys, detect_corners(xys))
print('corners', len(corners), flush=True)
verts, segs, rep = build_path(xys, corners, target_err=0.2, kmax=8)
print('segments', len(segs))
for i,kind,err,K in rep: print(f'  arc{i:2d} {kind:5s} err={err:.3f} K={K}')
np.save('src/dust_verts.npy', np.array(verts))
pickle.dump(segs, open('src/dust_segs.pkl','wb'))
f = lambda v: f"{round(v[0],2):g} {round(v[1],2):g}"
d = "M"+f(verts[0]) + "".join(("L"+f(s[1])) if s[0]=='L' else ("C"+f(s[1])+" "+f(s[2])+" "+f(s[3])) for s in segs) + "Z"
open('src/d_dust_shape2.txt','w').write(d)
print('d len', len(d))
