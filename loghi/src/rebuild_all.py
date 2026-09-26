import sys, pickle, re, time; sys.path.insert(0,'src')
import numpy as np
t0=time.time()
verts = np.load('src/sym_verts.npy'); segs = pickle.load(open('src/sym_segs.pkl','rb'))
clean=[]; cur=verts[0].copy()
for s in segs:
    end=np.array(s[-1],float)
    if np.linalg.norm(end-cur) < 0.05: continue
    clean.append(s); cur=end
segs=clean
from exact_edges import exactify
verts, segs, log = exactify(verts, segs)
from exact_edges import exact_corners
verts, segs, log2 = exact_corners(verts, segs)
log += log2
from exact_edges import straighten
verts, segs, log3 = straighten(verts, segs)
log += log3
for l in log: print('  ', l)
pickle.dump(segs, open('src/sym_segs_exact.pkl','wb')); np.save('src/sym_verts_exact.npy', np.array(verts))
fi = lambda v: f"{round(float(v[0]),2):g} {round(float(v[1]),2):g}"
d_img = "M"+fi(verts[0]) + "".join(("L"+fi(s[1])) if s[0]=='L' else ("C"+fi(s[1])+" "+fi(s[2])+" "+fi(s[3])) for s in segs) + "Z"
open('src/d_sym_imgcoords.txt','w').write(d_img)

# bbox reale (flattening delle Bezier)
def flatten(verts, segs, n=24):
    pts=[np.array(verts[0],float)]; cur=pts[0]
    for s in segs:
        if s[0]=='L': pts.append(np.array(s[1],float)); cur=pts[-1]
        else:
            c1,c2,p3 = [np.array(x,float) for x in s[1:]]
            for k in range(1,n+1):
                t=k/n; mt=1-t
                pts.append(mt**3*cur + 3*mt**2*t*c1 + 3*mt*t**2*c2 + t**3*p3)
            cur=p3
    return np.array(pts)
F = flatten(verts, segs)
minx,maxx,miny,maxy = F[:,0].min(), F[:,0].max(), F[:,1].min(), F[:,1].max()
W,Hh = maxx-minx, maxy-miny
f = lambda v: f"{round(float(v[0])-minx,3):g} {round(float(v[1])-miny,3):g}"
d_tight = "M"+f(verts[0]) + "".join(("L"+f(s[1])) if s[0]=='L' else ("C"+f(s[1])+" "+f(s[2])+" "+f(s[3])) for s in segs) + "Z"
open('src/d_sym_tight.txt','w').write(d_tight)
open('aporia-logo.svg','w').write(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.3f} {Hh:.3f}" width="{W:.3f}" height="{Hh:.3f}" role="img" aria-labelledby="t">
  <title id="t">Aporia</title>
  <path fill="currentColor" d="{d_tight}"/>
</svg>
''')
print(f'logo pulito {W:.3f} x {Hh:.3f}  ({len(segs)} segmenti)', flush=True)

from symmetrize import transform
from warp_field import warp_path_d, affine_path_d
p = np.load('src/align_refined.npy'); sx,sy,tx,ty,sh=p
M=np.array([[sx,sh],[0,sy]]); t=np.array([tx,ty]); Minv=np.linalg.inv(M)
# frame dust SENZA taglio obliquo: la lettera resta perfettamente simmetrica
Y_MID = (892.578 + 220.708)/2
Mf = np.array([[sx, 0.0],[0, sy]]); tf = np.array([tx + sh*Y_MID, ty])
shape_d = affine_path_d(d_img, Mf, tf, prec=2); open('src/d_dust_shape_sym.txt','w').write(shape_d)
class AW:
    def __call__(self, q):
        q=np.asarray(q,float); return (transform((q-t) @ Minv.T) @ Mf.T + tf) - q
w=AW()
old = np.load('src/contour_dust_regular.npy'); new = np.load('src/contour_sym.npy') @ Mf.T + tf
res = np.linalg.norm(old + w(old) - new, axis=1)
print(f'residuo trasformazione: medio {res.mean():.3f} max {res.max():.3f}', flush=True)
lv_old, gw_old, _ = pickle.load(open('src/dust_regular_layers.pkl','rb'))
lv=[(v, warp_path_d(dd,w,prec=1)) for v,dd in lv_old]
gw=[(v, warp_path_d(dd,w,prec=1)) for v,dd in gw_old]
pickle.dump((lv,gw,shape_d), open('src/dust_sym_layers.pkl','wb'))
import emit_v2 as E
open('aporia-logo-dust.svg','w').write(E.emit(shape_d, lv, gw, animated=True))
open('aporia-logo-dust-static.svg','w').write(E.emit(shape_d, lv, gw, animated=False))
inv=E.emit(shape_d, lv, gw, animated=False, title='Aporia — logo dust (inverso)')
inv=inv.replace('--ink: #ffffff;','--ink: #0b0b0c;').replace('--mask: url(#aporiaMaskLight);','--mask: url(#aporiaMaskDark);')
open('aporia-logo-dust-inverted.svg','w').write(inv)
nums=[float(x) for x in re.findall(r'-?\d+\.?\d*', shape_d)]
xs=np.array(nums[0::2]); ys=np.array(nums[1::2]); m=26
x0,y0=xs.min()-m, ys.min()-m; wd,h=(xs.max()-xs.min())+2*m,(ys.max()-ys.min())+2*m
svg=open('aporia-logo-dust.svg').read()
open('aporia-logo-dust-tight.svg','w').write(svg
   .replace('viewBox="0 0 1254 1254" width="1254" height="1254"', f'viewBox="{x0:.1f} {y0:.1f} {wd:.1f} {h:.1f}" width="{wd:.0f}" height="{h:.0f}"')
   .replace('<rect id="aporiaBg" width="1254" height="1254"/>', f'<rect id="aporiaBg" x="{x0:.1f}" y="{y0:.1f}" width="{wd:.1f}" height="{h:.1f}"/>')
   .replace('<rect id="aporiaInk" width="1254" height="1254"/>', f'<rect id="aporiaInk" x="{x0:.1f}" y="{y0:.1f}" width="{wd:.1f}" height="{h:.1f}"/>'))
print('completato', f'{time.time()-t0:.0f}s')
