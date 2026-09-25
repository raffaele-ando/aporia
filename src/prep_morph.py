"""Prepara il "racconto" della polvere per l'intro:
  S      = la A piena, fatta di polvere (il logo prima che il vento scavi il fiume)
  Bstay  = la parte del logo che è già lì nella A piena (resta ferma)
  Bmove  = la parte del logo che arriva col vento (bandiera, bordi del fiume)
  movers = granelli: da dove il vento solleva la polvere (fiume) a dove la deposita (bandiera)
S*(1-F) + Bstay*F + Bmove*A = logo finale, con F = fronte della folata e A = polvere arrivata.
Tutto nel riquadro dei fotogrammi del logo (src/logo_frames.json)."""
import io, re, json, base64, pathlib, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter, binary_dilation
from scipy.optimize import linear_sum_assignment
root = pathlib.Path(__file__).resolve().parent.parent
J = json.loads((root/'src'/'logo_frames.json').read_text())
M = J['meta']; U0, V0, U1, V1 = M['u0'], M['v0'], M['u1'], M['v1']

def decode(uri):
    return Image.open(io.BytesIO(base64.b64decode(uri.split(',', 1)[1]))).convert('RGBA')
B0 = np.asarray(decode(J['frames'][0]).getchannel('A'), np.float32)/255.
h, w = B0.shape; k = w/(U1 - U0)
to_px = lambda u, v: ((u - U0)*k, (v - V0)*k)

def poly_mask(pts, ss=4):
    im = Image.new('L', (w*ss, h*ss), 0)
    ImageDraw.Draw(im).polygon([(x*ss, y*ss) for x, y in (to_px(*p) for p in pts)], fill=255)
    return np.asarray(im.resize((w, h), Image.LANCZOS), np.float32)/255.

def path_points(d):
    import sys as _s; _s.path.insert(0, str(root/'src'))
    from light_path import flatten
    return flatten(d)

# la A piena: contorno esterno della lettera meno il vano tra le gambe (simmetrica rispetto all'asse)
AX = (232.69 + 985.6)/2
LETTER = [(232.69, 966.42), (538.24, 317.77), (680.05, 317.77), (985.6, 966.42),
          (826.11, 966.42), (AX, 490.0), (392.17, 966.42)]
solid = poly_mask(LETTER)

# la A pulita di polvere: chiara, con una luce morbida e la stessa grana del logo
yy, xx = np.mgrid[0:h, 0:w]
lowf = gaussian_filter(np.random.default_rng(5).random((h, w)).astype(np.float32), 38)
lowf = (lowf - lowf.min())/(lowf.max() - lowf.min())
light = 0.84 + 0.12*lowf + 0.04*(yy/h)                       # un po' più chiara verso i piedi
rg = np.random.default_rng(11)
nz = lambda sg: (lambda a: a/a.std())(gaussian_filter(rg.standard_normal((h, w)).astype(np.float32), sg))
speck = np.clip(nz(0.8) - 2.3, 0, None)*0.35                     # granelli più chiari, sparsi
tex = 0.075*nz(0.6) + 0.05*nz(1.6) - 0.03*np.clip(nz(3.0), 0, None) + speck
S = np.clip((light + tex)*solid, 0, 1)

# ripartizione del logo: ciò che resta e ciò che arriva col vento
g = lambda a: gaussian_filter(a, 5)
r = np.clip(g(S)/np.maximum(g(B0), 1e-3), 0, 1)
Bstay = B0*r; Bmove = B0 - Bstay
Smove = S*(1 - np.clip(g(B0)/np.maximum(g(S), 1e-3), 0, 1))
print('massa  S %.0f  B %.0f  Smove %.0f  Bmove %.0f' % (S.sum(), B0.sum(), Smove.sum(), Bmove.sum()))

# granelli: sorgenti dove il vento solleva, destinazioni dove deposita
rng = np.random.default_rng(7)
def sample(D, n):
    p = (D/D.sum()).ravel(); idx = rng.choice(p.size, n, p=p)
    y, x = np.divmod(idx, w); x = x + rng.random(n); y = y + rng.random(n)
    return np.stack([U0 + x/k, V0 + y/k], 1)
NS = int(sys.argv[1]) if len(sys.argv) > 1 else 2600
NT = min(NS, int(round(NS*Bmove.sum()/Smove.sum())))
src = sample(Smove, NS); tgt = sample(Bmove, NT)
dx = tgt[None, :, 0] - src[:, None, 0]; dy = tgt[None, :, 1] - src[:, None, 1]
cost = np.where(dx < 0, (2.5*dx)**2, (0.55*dx)**2) + (1.4*dy)**2       # il vento porta a destra
ri, ci = linear_sum_assignment(cost)
T = np.full((NS, 2), np.nan); T[ri] = tgt[ci]
print('granelli', NS, 'con destinazione', NT, 'portati via', NS - NT)

def enc(a):
    img = Image.merge('RGBA', (Image.new('L', (w, h), 255),)*3 + (Image.fromarray((np.clip(a, 0, 1)*255).round().astype('uint8')),))
    buf = io.BytesIO(); img.save(buf, 'WEBP', quality=80, method=6)
    return 'data:image/webp;base64,' + base64.b64encode(buf.getvalue()).decode(), img
out = {'meta': M, 'movers': None}
for name, a in [('S', S), ('Bstay', Bstay), ('Bmove', Bmove)]:
    out[name], img = enc(a)
    if len(sys.argv) > 2: (root/'.tmp').mkdir(exist_ok=True); img.save(root/'.tmp'/f'prep_{name}.png')
mv = np.round(np.nan_to_num(np.concatenate([src, T], 1), nan=-1)*2).astype('<i2')
out['movers'] = base64.b64encode(mv.tobytes()).decode()
(root/'src'/'morph.json').write_text(json.dumps(out))
print({k: len(v)//1024 for k, v in out.items() if isinstance(v, str)}, 'KB')
