"""Intro Aporia come video: simulazione di vento e polvere, resa fotogramma per fotogramma.

Un solo vento, continuo, da sinistra verso destra, con vortici trasportati dall'aria.
Ogni granello ha UNA destinazione nel logo definitivo e ci arriva portato dal vento. Mentre
arriva passa dalla forma della A (la sua destinazione scivola nel verso del vento, dalla A al
logo), ma non si ferma mai lì: tutto è in movimento fino al logo, che è il momento più pieno.
Poi il vento rinforza e lo porta via, un granello alla volta, da sinistra a destra.

Il video riempie sempre tutto lo schermo (nella pagina: object-fit: cover); il logo sta nella
zona centrale che resta visibile con qualsiasi proporzione dello schermo.

Uso: python src/sim_video.py portrait|landscape [n_granelli] [--preview]
"""
import sys, io, os, json, base64, pathlib, subprocess, time
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, map_coordinates
from scipy.optimize import linear_sum_assignment
from scipy.spatial import cKDTree

root = pathlib.Path(__file__).resolve().parent.parent
LAYOUT = sys.argv[1] if len(sys.argv) > 1 else 'portrait'
N = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 450_000
PREVIEW = '--preview' in sys.argv
W, H = (1080, 1920) if LAYOUT == 'portrait' else (1920, 1080)
if PREVIEW: W, H = W//2, H//2
FPS = 60
DUR = float(os.environ.get('DUR', 4.7))
rng = np.random.default_rng(1)

# ---- riquadro del logo: piccolo abbastanza da restare intero anche quando il video viene
#      ritagliato per riempire schermi con proporzioni diverse (da 9:21 a 21:9)
BOX = W*0.80 if LAYOUT == 'portrait' else H*0.68
SC = BOX/1254
BX, BY = (W - BOX)/2, (H - BOX)/2 + (0.02*H if LAYOUT == 'portrait' else 0)
UMIN, UMAX = -BX/SC, (W - BX)/SC
VMIN, VMAX = -BY/SC, (H - BY)/SC

J = json.loads((root/'src'/'morph.json').read_text())
M = J['meta']; U0, V0, U1, V1 = M['u0'], M['v0'], M['u1'], M['v1']
def img(key):
    a = Image.open(io.BytesIO(base64.b64decode(J[key].split(',', 1)[1]))).convert('RGBA').getchannel('A')
    return np.asarray(a, np.float32)/255.
S_img = img('S'); B_img = np.clip(img('Bstay') + img('Bmove'), 0, 1)
kimg = S_img.shape[1]/(U1 - U0)

def sample(D, n):
    p = (D/D.sum()).ravel(); idx = rng.choice(p.size, n, p=p)
    y, x = np.divmod(idx, D.shape[1])
    return (U0 + (x + rng.random(n))/kimg).astype(np.float32), (V0 + (y + rng.random(n))/kimg).astype(np.float32)

# ---- resa: la luce è 1 - exp(-K·densità). Si campiona il logo con densità -ln(1-B) così che,
#      quando tutti i granelli sono posati, la luce sia esattamente quella del logo
KEXP = 2.2
G_img = -np.log(1 - np.clip(B_img, 0, 0.965))
ub, vb = sample(G_img, N)                        # destinazione: logo definitivo
GS = -np.log(1 - np.clip(S_img, 0, 0.965))
# passaggio dalla A: abbinamento "sottovento" tra punti della A e punti del logo (a destra costa
# poco, a sinistra molto), fatto su rappresentanti e poi esteso a tutti i granelli
NR = 3000
ra_u, ra_v = sample(GS, NR); rb_idx = rng.choice(N, NR, replace=False)
rb_u, rb_v = ub[rb_idx], vb[rb_idx]
dx = rb_u[None, :] - ra_u[:, None]; dy = rb_v[None, :] - ra_v[:, None]
cost = np.where(dx < 0, (3.0*dx)**2, (0.45*dx)**2) + (1.3*dy)**2
ri, ci = linear_sum_assignment(cost)
A_of_B = np.empty((NR, 2), np.float32); A_of_B[ci] = np.stack([ra_u[ri], ra_v[ri]], 1)
_, nn = cKDTree(np.stack([rb_u, rb_v], 1)).query(np.stack([ub, vb], 1))
ua = A_of_B[nn, 0] + (ub - rb_u[nn]); va = A_of_B[nn, 1] + (vb - rb_v[nn])
print(f'granelli {N}; spostamento medio A→logo {np.hypot(ub-ua, vb-va).mean():.1f} unità')

# ---- tempi di ogni granello (secondi) -----------------------------------------------------
fx = ((ub - U0)/(U1 - U0)).astype(np.float32)
r = rng.random((6, N)).astype(np.float32)
tcap = 0.3 + 0.6*fx + 0.45*r[0]**1.4            # la raffica lo sbatte sul logo (sinistra -> destra)
dcap = 0.18 + 0.22*r[1]                          # si ferma quasi di colpo, come polvere che urta
tmor = tcap + 0.05 + 0.25*r[2]                   # la sua destinazione scivola dalla A al logo
dmor = 0.35 + 0.3*r[3]
trel = 3.05 + 0.8*fx + 0.14*r[4]                 # il vento se lo riprende: un fronte da sinistra a destra
tau = np.clip(np.exp(rng.normal(np.log(0.11), 0.45, N)), 0.035, 0.4).astype(np.float32)

def smooth(a, b, t):
    q = np.clip((t - a)/(b - a), 0, 1); return q*q*(3 - 2*q)

# ---- vento: un solo flusso continuo; rinforza verso la fine --------------------------------
def wind_speed(t):
    # raffica forte all'inizio (porta la polvere), poi brezza, poi rinforza per l'uscita
    return 330 + 650*(1 - smooth(0.9, 2.1, t)) + 60*np.sin(t*0.9) + 750*np.clip((t - 2.95)/0.9, 0, 1)**1.5
def curl_grid(n, cells, seed):
    rr = np.random.default_rng(seed)
    psi = gaussian_filter(rr.standard_normal((n, cells, cells)).astype(np.float32), (1.2, 1.6, 1.6), mode='wrap')
    psi /= psi.std()
    # derivate periodiche: il campo si ripete senza cuciture (altrimenti la polvere si accumula
    # lungo una riga dove il campo "salta")
    dpdy = (np.roll(psi, -1, 1) - np.roll(psi, 1, 1))/2; dpdx = (np.roll(psi, -1, 2) - np.roll(psi, 1, 2))/2
    return dpdy, -dpdx                               # senza divergenza, come l'aria vera
OCT = [(300.0, 1.0, curl_grid(24, 48, 3)), (90.0, 0.55, curl_grid(24, 48, 4)), (30.0, 0.25, curl_grid(24, 48, 5))]
def turb(xx, yy, t, adv):
    tx = np.zeros_like(xx); ty = np.zeros_like(yy)
    for L, amp, (gxg, gyg) in OCT:
        c = [np.full_like(xx, t*1.6), yy/L, (xx - adv)/L]    # i vortici viaggiano con l'aria
        tx += map_coordinates(gxg, c, order=1, mode='grid-wrap')*amp
        ty += map_coordinates(gyg, c, order=1, mode='grid-wrap')*amp
    return tx, ty
def wind(xx, yy, t, adv):
    U = wind_speed(t); tx, ty = turb(xx, yy, t, adv)
    if os.environ.get('NOTURB'): tx = tx*0; ty = ty*0
    a = 170 + 0.28*U
    return U + tx*a, -0.06*U + ty*a

# ---- stato iniziale: i granelli sono già nel vento, sopravento rispetto a dove si poseranno ----
x = (ua - 950*tcap - 700*rng.random(N)**0.8).astype(np.float32)   # arrivano da fuori schermo, a sinistra
y = (va + rng.normal(0, 150, N)).astype(np.float32)
vx = np.full(N, 950, np.float32); vy = np.zeros(N, np.float32)
NA = N//10                                          # polvere nell'aria: attraversa tutto lo schermo
ax_ = rng.uniform(UMIN - 400, UMAX, NA).astype(np.float32); ay_ = rng.uniform(VMIN - 60, VMAX + 60, NA).astype(np.float32)
avx = np.full(NA, 950, np.float32); avy = np.zeros(NA, np.float32)
atau = np.clip(np.exp(rng.normal(np.log(0.09), 0.5, NA)), 0.03, 0.35).astype(np.float32)
aw = (0.3 + 0.7*rng.random(NA)).astype(np.float32)

# peso di un granello posato: l'integrale della luce del logo è quello di G
wN = float(G_img.sum()/kimg**2*SC**2/N)/KEXP
vis_flight = np.where(r[5] < 0.16, 2.8, 0.1).astype(np.float32)   # in volo: pochi granelli ben visibili, niente nebbia

def splat(acc, px, py, w):
    x0 = np.floor(px).astype(np.int64); y0 = np.floor(py).astype(np.int64); fx_ = px - x0; fy_ = py - y0
    ok = (x0 >= 0) & (y0 >= 0) & (x0 < W - 1) & (y0 < H - 1)
    x0, y0, fx_, fy_, w = x0[ok], y0[ok], fx_[ok], fy_[ok], w[ok]
    i = y0*W + x0
    acc += np.bincount(i, w*(1 - fx_)*(1 - fy_), W*H)
    acc += np.bincount(i + 1, w*fx_*(1 - fy_), W*H)
    acc += np.bincount(i + W, w*(1 - fx_)*fy_, W*H)
    acc += np.bincount(i + W + 1, w*fx_*fy_, W*H)

out = root/'assets'; out.mkdir(exist_ok=True)
name = f'intro-{LAYOUT}' + ('-preview' if PREVIEW else '')
master = pathlib.Path('/tmp/claude-0/sp')/f'master-{name}.mp4'
ff = __import__('imageio_ffmpeg').get_ffmpeg_exe()
enc = subprocess.Popen([ff, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', str(master)], stdin=subprocess.PIPE)
DUST = np.array([244, 241, 235], np.float32)/255
SUB, TR = 2, 5
adv = 0.0; t = 0.0; dt = 1/(FPS*SUB)
nframes = int(DUR*FPS); t0w = time.time(); snap = {}
for fi in range(nframes):
    px0, py0 = x.copy(), y.copy(); ax0, ay0 = ax_.copy(), ay_.copy()
    for _ in range(SUB):
        t += dt
        wx, wy = wind(x, y, t, adv)
        c = smooth(tcap, tcap + dcap, t)*(1 - smooth(trel, trel + 0.12, t))   # quanto è "posato"
        m = smooth(tmor, tmor + dmor, t)                                        # dalla A al logo
        tx = ua + (ub - ua)*m; ty = va + (vb - va)*m
        free = (1 - c)**2; c2 = c*c
        # posato: si muove appena con l'aria (la polvere "vive"), senza staccarsi
        jx, jy = turb(tx, ty, t, adv)
        tx = tx + jx*1.4*c; ty = ty + jy*1.4*c
        rel = t > trel
        tt = np.where(rel, tau*(0.6 + 1.6*r[1]), tau)
        lift = np.where(rel, -(40 + 120*r[2]), 0)
        axc = (wx - vx)/tt*free + (tx - x)*420*c2 - vx*40*c2
        ayc = (wy + lift - vy)/tt*free + (ty - y)*420*c2 - vy*40*c2
        kick = rel & (t - trel < dt)                                   # strappo: ognuno parte a modo suo
        vx[kick] += 250 + 500*r[3][kick]; vy[kick] += (r[2][kick] - 0.6)*380
        vx += axc*dt; vy += ayc*dt
        x += vx*dt; y += vy*dt
        wx, wy = wind(ax_, ay_, t, adv)
        avx += (wx - avx)/atau*dt; avy += (wy - avy)/atau*dt
        ax_ += avx*dt; ay_ += avy*dt
        wrap = ax_ > UMAX + 60
        ax_[wrap] = UMIN - 60 - 250*rng.random(wrap.sum()); ay_[wrap] = rng.uniform(VMIN - 60, VMAX + 60, wrap.sum())
        wrap = (ay_ < VMIN - 120) | (ay_ > VMAX + 120); ay_[wrap] = rng.uniform(VMIN, VMAX, wrap.sum())
        adv += wind_speed(t)*dt
    vis = smooth(0.0, 0.25, t)*(1 - smooth(4.2, 4.7, t))
    # portata via: la polvere del logo resta visibile mentre si apre nel vento, poi si disperde
    wl = wN*vis*(c + (1 - c)*np.where(rel, np.maximum(vis_flight, 0.6), vis_flight))
    wl = wl*np.where(rel, 1 - smooth(trel + 0.35, trel + 1.25, t), 1)
    wa = aw*wN*1.1*vis*(0 if os.environ.get('NOAIR') else 1)
    acc = np.zeros(W*H, np.float64)
    for k in range(TR):
        q = (k + 0.5)/TR
        splat(acc, BX + (px0 + (x - px0)*q)*SC, BY + (py0 + (y - py0)*q)*SC, (wl/TR).astype(np.float32))
        splat(acc, BX + (ax0 + (ax_ - ax0)*q)*SC, BY + (ay0 + (ay_ - ay0)*q)*SC, (wa/TR).astype(np.float32))
    D = gaussian_filter(acc.reshape(H, W).astype(np.float32), 0.6)
    L = 1 - np.exp(-KEXP*D)
    L = L + 0.08*gaussian_filter(L, 6)
    frame = (np.clip(L, 0, 1)[..., None]*DUST*255).astype(np.uint8)
    enc.stdin.write(frame.tobytes())
    if fi % 12 == 0: snap[round(t, 2)] = frame
    if fi % 60 == 0: print(f'{fi}/{nframes} {time.time() - t0w:.0f}s', flush=True)
enc.stdin.close(); enc.wait()
keys = sorted(snap); tw = 300; th = int(tw*H/W); cols = 7
sheet = Image.new('RGB', (cols*(tw + 4), ((len(keys) + cols - 1)//cols)*(th + 4)), (40, 40, 40))
for i, k in enumerate(keys):
    sheet.paste(Image.fromarray(snap[k]).resize((tw, th)), ((i % cols)*(tw + 4), (i//cols)*(th + 4)))
sheet.save(f'/tmp/claude-0/sp/{name}.png')
# versioni per il web
if not PREVIEW:
    subprocess.run([ff, '-y', '-loglevel', 'error', '-i', str(master), '-c:v', 'libx264', '-preset', 'veryslow', '-crf', '29',
                    '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-level', '4.2', '-movflags', '+faststart', '-an', str(out/f'{name}.mp4')], check=True)
    subprocess.run([ff, '-y', '-loglevel', 'error', '-i', str(master), '-c:v', 'libvpx-vp9', '-b:v', '0', '-crf', '52', '-row-mt', '1',
                    '-pix_fmt', 'yuv420p', '-an', str(out/f'{name}.webm')], check=True)
    print('video', {p.name: p.stat().st_size//1024 for p in out.glob(f'{name}.*')}, 'KB')
print(f'fatto in {time.time() - t0w:.0f}s')
