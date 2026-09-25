"""Intro Aporia come video: simulazione fisica di vento e polvere, resa fotogramma per fotogramma.

Racconto (circa 4,8 s): dal nero il vento porta la polvere, che si posa e costruisce una A pulita;
una raffica attraversa la lettera, solleva la polvere del fiume e la trascina nella bandiera
(una parte viene portata via): il risultato è il logo; l'ultima raffica porta via tutto.

Il logo è fatto dai granelli stessi (nessuna immagine che compare): i punti di arrivo sono presi
dalle immagini di src/morph.json (A pulita S, logo = Bstay + Bmove).

Uso: python src/sim_video.py portrait|landscape [n_granelli] [--preview]
"""
import sys, io, json, base64, pathlib, subprocess, time
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, map_coordinates

root = pathlib.Path(__file__).resolve().parent.parent
LAYOUT = sys.argv[1] if len(sys.argv) > 1 else 'portrait'
N = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 450_000
PREVIEW = '--preview' in sys.argv
W, H = (1080, 1920) if LAYOUT == 'portrait' else (1920, 1080)
if PREVIEW: W, H = W//2, H//2
FPS = 60
DUR = float(__import__("os").environ.get("DUR", 5.0))
rng = np.random.default_rng(1)

# ---- riquadro del logo (come nella pagina) ------------------------------------------
BOX = min(W*0.96, H*0.9)
SC = BOX/1254                                  # pixel per unità del viewBox
BX, BY = (W - BOX)/2, (H - BOX)/2
to_px = lambda u, v: (BX + u*SC, BY + v*SC)
UMIN, UMAX = -BX/SC, (W - BX)/SC               # schermo in unità del logo
VMIN, VMAX = -BY/SC, (H - BY)/SC

J = json.loads((root/'src'/'morph.json').read_text())
M = J['meta']; U0, V0, U1, V1 = M['u0'], M['v0'], M['u1'], M['v1']
def img(key):
    a = Image.open(io.BytesIO(base64.b64decode(J[key].split(',', 1)[1]))).convert('RGBA').getchannel('A')
    return np.asarray(a, np.float32)/255.
S_img, Bs_img, Bm_img = img('S'), img('Bstay'), img('Bmove')
B_img = np.clip(Bs_img + Bm_img, 0, 1)
kimg = S_img.shape[1]/(U1 - U0)                # pixel dell'immagine per unità

def to_screen(a):
    """immagine del riquadro del logo -> fotogramma del video"""
    out = np.zeros((H, W), np.float32)
    x0, y0 = to_px(U0, V0); x1, y1 = to_px(U1, V1)
    sub = np.asarray(Image.fromarray((a*65535).astype(np.uint16)).resize((int(round(x1 - x0)), int(round(y1 - y0))), Image.LANCZOS), np.float32)/65535
    ix, iy = int(round(x0)), int(round(y0))
    out[iy:iy + sub.shape[0], ix:ix + sub.shape[1]] = sub[:H - iy, :W - ix]
    return np.clip(out, 0, 1)
S_scr, B_scr, Bs_scr = to_screen(S_img), to_screen(B_img), to_screen(Bs_img)

def sample(D, n):
    p = (D/D.sum()).ravel(); idx = rng.choice(p.size, n, p=p)
    y, x = np.divmod(idx, D.shape[1])
    u = U0 + (x + rng.random(n))/kimg; v = V0 + (y + rng.random(n))/kimg
    return u.astype(np.float32), v.astype(np.float32)

# ---- polvere del logo: dalla A pulita al logo ------------------------------------------
ua, va = sample(S_img, N)                      # dove si posa nella A pulita
g = lambda a: gaussian_filter(a, 4)
pstay = np.clip(g(B_img)/np.maximum(g(S_img), 1e-3), 0, 1)
iy = np.clip(((va - V0)*kimg).astype(int), 0, S_img.shape[0] - 1); ix = np.clip(((ua - U0)*kimg).astype(int), 0, S_img.shape[1] - 1)
stay = rng.random(N) < pstay[iy, ix]
mov = np.nonzero(~stay)[0]
n_land = int(round(len(mov)*min(1, (B_img*(1 - np.clip(g(S_img)/np.maximum(g(B_img), 1e-3), 0, 1))).sum()/max(1e-6, (S_img*(1 - pstay)).sum()))))
ub, vb = ua.copy(), va.copy()
land = np.zeros(N, bool)
if n_land > 0:
    # chi si posa: abbinamento "sottovento" (a destra costa poco, a sinistra molto) fatto su
    # 3000 rappresentanti, poi ogni granello segue il suo rappresentante
    from scipy.optimize import linear_sum_assignment
    from scipy.spatial import cKDTree
    Bm_only = np.clip(B_img - np.clip(g(S_img), 0, None), 0, None) + 1e-4*Bm_img
    tu, tv = sample(np.maximum(Bm_img, 1e-6)*(Bm_img > 0.02), n_land)
    reps = rng.choice(len(mov), min(3000, len(mov)), replace=False)
    trep = rng.choice(n_land, min(3000, n_land), replace=False)
    su, sv = ua[mov[reps]], va[mov[reps]]
    dx = tu[trep][None, :] - su[:, None]; dy = tv[trep][None, :] - sv[:, None]
    cost = np.where(dx < 0, (2.5*dx)**2, (0.55*dx)**2) + (1.4*dy)**2
    ri, ci = linear_sum_assignment(cost)
    # i granelli più vicini (in partenza) a un rappresentante abbinato vanno verso la sua zona
    tree = cKDTree(np.stack([su[ri], sv[ri]], 1))
    order = rng.permutation(len(mov))[:n_land]
    _, nn = tree.query(np.stack([ua[mov[order]], va[mov[order]]], 1))
    # ogni granello prende un punto di arrivo vero vicino a quello del suo rappresentante
    ttree = cKDTree(np.stack([tu, tv], 1))
    anchor = np.stack([tu[trep][ci][nn], tv[trep][ci][nn]], 1) + rng.normal(0, 10, (len(order), 2))
    _, tj = ttree.query(anchor)
    ub[mov[order]] = tu[tj]; vb[mov[order]] = tv[tj]
    land[mov[order]] = True
away = ~stay & ~land
print(f'granelli {N}: restano {stay.sum()}, si spostano {land.sum()}, portati via {away.sum()}')

# tempi di ogni granello (in secondi)
fxA = (ua - U0)/(U1 - U0)
r = rng.random((6, N)).astype(np.float32)
tc = 0.8 + 0.55*fxA + 0.5*r[0]**1.5                       # si posa nella A (sinistra -> destra, un granello alla volta)
tv_ = 1.85 + 0.62*fxA + 0.08*r[1]                        # la raffica del fiume lo raggiunge
tland = tv_ + 0.18 + 0.35*r[2]                           # comincia a posarsi nel logo
dland = 0.35 + 0.35*r[3]
te = 3.45 + 0.4*fxA + 0.45*r[4]**1.5                      # l'ultima raffica lo porta via, un granello alla volta
tau = np.exp(rng.normal(np.log(0.12), 0.5, N)).astype(np.float32)   # inerzia: leggeri seguono il vento
tau = np.clip(tau, 0.035, 0.5)

# partenza: sopravento rispetto al punto dove si poserà, così arriva col vento
x = (ua - 600*tc - 520*rng.random(N)).astype(np.float32)
y = (va + rng.normal(0, 380, N)).astype(np.float32)
vx = np.full(N, 420, np.float32); vy = np.zeros(N, np.float32)

# polvere nell'aria (non si posa mai)
NA = N//12
ax_ = rng.uniform(UMIN - 300, UMAX, NA).astype(np.float32); ay_ = rng.uniform(VMIN - 50, VMAX + 50, NA).astype(np.float32)
avx = np.zeros(NA, np.float32); avy = np.zeros(NA, np.float32)
atau = np.clip(np.exp(rng.normal(np.log(0.1), 0.5, NA)), 0.03, 0.4).astype(np.float32)
aw = (0.25 + 0.75*rng.random(NA)).astype(np.float32)

# ---- vento: fondo + raffiche che attraversano lo schermo + vortici trasportati dall'aria ----
# raffiche: arrivano di colpo (fronte), poi calano piano. arrivo sul bordo sinistro, salita, durata, forza, pendenza
FRONT = 1500.0                                           # velocità del fronte (unità/s)
DLY = (500 - UMIN)/FRONT                                 # ritardo con cui il fronte raggiunge il centro della lettera
GUSTS = [(0.05, 0.35, 2.2, 520, -0.10), (1.85 - DLY, 0.25, 1.7, 700, -0.05), (3.45 - DLY, 0.2, 1.9, 1100, -0.18)]
def gust(xx, t):
    gx = np.full_like(xx, 150 + 60*np.sin(t*1.3)); gy = np.full_like(xx, -8.0); ge = np.zeros_like(xx)
    for t0, rise, d, s, sl in GUSTS:
        loc = t - t0 - (xx - UMIN)/FRONT
        up = np.clip(loc/rise, 0, 1); up = up*up*(3 - 2*up)
        dn = np.clip((loc - d*0.45)/(d*0.55), 0, 1); dn = dn*dn*(3 - 2*dn)
        e = up*(1 - dn)*s
        gx += e; gy += e*sl; ge += e
    return gx, gy, ge

def curl_grid(n, cells, seed):
    rr = np.random.default_rng(seed)
    psi = gaussian_filter(rr.standard_normal((n, cells, cells)).astype(np.float32), (1.2, 1.6, 1.6), mode='wrap')
    psi /= psi.std()
    dpdy, dpdx = np.gradient(psi, axis=(1, 2))
    return dpdy, -dpdx                                  # curl: senza divergenza, come l'aria vera
OCT = [(240.0, 1.0, curl_grid(24, 48, 3)), (60.0, 0.6, curl_grid(24, 48, 4))]
def turb(xx, yy, t, adv):
    tx = np.zeros_like(xx); ty = np.zeros_like(yy)
    for L, amp, (gxg, gyg) in OCT:
        c = [np.full_like(xx, t*2.2), (yy)/L, (xx - adv*0.85)/L]
        tx += map_coordinates(gxg, c, order=1, mode='wrap')*amp
        ty += map_coordinates(gyg, c, order=1, mode='wrap')*amp
    return tx, ty

# ---- resa: densità dei granelli con scia di movimento --------------------------------------
wN = S_scr.sum()/N                             # peso per granello: la A posata ha la luce di S
def splat(acc, px, py, w):
    x0 = np.floor(px).astype(np.int64); y0 = np.floor(py).astype(np.int64); fx = px - x0; fy = py - y0
    ok = (x0 >= 0) & (y0 >= 0) & (x0 < W - 1) & (y0 < H - 1)
    x0, y0, fx, fy, w = x0[ok], y0[ok], fx[ok], fy[ok], w[ok]
    i = y0*W + x0
    acc += np.bincount(i, w*(1 - fx)*(1 - fy), W*H)
    acc += np.bincount(i + 1, w*fx*(1 - fy), W*H)
    acc += np.bincount(i + W, w*(1 - fx)*fy, W*H)
    acc += np.bincount(i + W + 1, w*fx*fy, W*H)

def smooth(a, b, t):
    q = np.clip((t - a)/(b - a), 0, 1); return q*q*(3 - 2*q)

out = root/'assets'; out.mkdir(exist_ok=True)
name = f'intro-{LAYOUT}' + ('-preview' if PREVIEW else '')
ff = __import__('imageio_ffmpeg').get_ffmpeg_exe()
enc = subprocess.Popen([ff, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-c:v', 'libx264', '-preset', 'slow', '-crf', '24' if not PREVIEW else '28', '-pix_fmt', 'yuv420p',
                        '-profile:v', 'high', '-level', '4.2', '-movflags', '+faststart', '-tune', 'grain', str(out/f'{name}.mp4')],
                       stdin=subprocess.PIPE)
DUST = np.array([244, 241, 235], np.float32)/255
SUB = 2                                        # passi di simulazione per fotogramma
TR = 5                                         # campioni della scia per fotogramma
adv = 0.0; t = 0.0; dt = 1/(FPS*SUB)
nframes = int(DUR*FPS); t0w = time.time()
snap = {}
for fi in range(nframes):
    px0, py0 = x.copy(), y.copy(); ax0, ay0 = ax_.copy(), ay_.copy()
    for _ in range(SUB):
        t += dt
        gx, gy, ge = gust(x, t); trx, try_ = turb(x, y, t, adv)
        amp = 150 + 1.15*ge
        wx = gx + trx*amp; wy = gy + try_*amp
        sA = smooth(tc - 0.4, tc + 0.2, t)                       # presa nella A pulita
        rel = 1 - smooth(tv_, tv_ + 0.06, t)                     # la raffica del fiume lo stacca
        sL = smooth(tland, tland + dland, t)                    # presa nel logo
        sE = 1 - smooth(te, te + 0.08, t)                        # l'ultima raffica lo stacca
        hold_A = np.where(stay, sA, sA*rel)
        hold_B = np.where(land, sL, 0)
        s = np.clip(np.maximum(hold_A, hold_B), 0, 1)*sE
        txg = np.where(stay | (hold_A >= hold_B), ua, ub); tyg = np.where(stay | (hold_A >= hold_B), va, vb)
        # i granelli che restano sussultano appena quando passa la raffica, poi si riassestano
        kick = stay & (np.abs(t - tv_) < dt)
        vx[kick] += 90*r[5][kick]; vy[kick] -= 40*r[5][kick]
        rip = np.abs(t - te) < dt                                # strappo dell'ultima raffica
        vx[rip] += 80 + 650*r[5][rip]**2; vy[rip] += (r[3][rip] - 0.65)*420
        s2 = s*s
        free = (1 - s)**2
        lift = np.where(sE < 1, -50 - 90*r[2], 0)
        te_on = t > te
        tt = np.where(te_on, tau*(0.5 + 1.5*r[1]), tau)             # all'uscita: pesanti in ritardo, leggeri via subito
        grav = np.where(te_on, 160*r[1]**2, 0)                        # i granelli pesanti cadono un po'
        axc = (wx - vx)/tt*free + (txg - x)*95*s2 - vx*17*s2
        ayc = (wy + lift - vy)/tt*free + grav*free + (tyg - y)*95*s2 - vy*17*s2
        # moto casuale dei granelli (turbolenza a scala piccolissima): li disperde quando sono liberi
        sig = (120 + 1.1*ge)*free
        axc += rng.standard_normal(N).astype(np.float32)*sig*6
        ayc += rng.standard_normal(N).astype(np.float32)*sig*6
        vx += axc*dt; vy += ayc*dt
        x += vx*dt; y += vy*dt
        # aria
        gx, gy, ge = gust(ax_, t); trx, try_ = turb(ax_, ay_, t, adv)
        amp = 55 + 0.3*ge
        avx += ((gx + trx*amp) - avx)/atau*dt; avy += ((gy + try_*amp) - avy)/atau*dt
        ax_ += avx*dt; ay_ += avy*dt
        wrap = ax_ > UMAX + 60
        ax_[wrap] = UMIN - 60 - 200*rng.random(wrap.sum()); ay_[wrap] = rng.uniform(VMIN, VMAX, wrap.sum())
        adv += (150 + 0.35*gust(np.array([0.0]), t)[2][0])*dt
    acc = np.zeros(W*H, np.float64)
    # visibilità: la polvere compare dal nero e alla fine se ne va
    vis = smooth(0.15, 0.6, t)*(1 - smooth(4.5, 5.0, t))
    # in volo si vede un granello su sei, più luminoso (scie di granelli, non nebbia);
    # quando si posano contano tutti e costruiscono la lettera piena
    sparse = np.where(r[5] < 0.17, 0.55/0.17, 0.0).astype(np.float32)
    wl = (wN*vis*(s + (1 - s)*sparse)).astype(np.float32)
    wl[away] *= 1 - smooth(tv_[away] + 0.4, tv_[away] + 1.3, t)          # la polvere portata via si dirada
    wl *= np.where(t > te, 1 - smooth(te + 0.35, te + 1.0, t), 1)        # uscita: si disperde
    wa = aw*wN*1.4*vis*(1 - 0.5*smooth(1.2, 2.2, t))
    for k in range(TR):
        q = (k + 0.5)/TR
        splat(acc, BX + (px0 + (x - px0)*q)*SC, BY + (py0 + (y - py0)*q)*SC, wl/TR)
        splat(acc, BX + (ax0 + (ax_ - ax0)*q)*SC, BY + (ay0 + (ay_ - ay0)*q)*SC, wa/TR)
    D = gaussian_filter(acc.reshape(H, W).astype(np.float32), 0.55)
    L = 1 - np.exp(-2.4*D)                       # la polvere densa satura dolcemente
    L = L + 0.10*gaussian_filter(L, 5)           # un filo di alone
    frame = (np.clip(L, 0, 1)[..., None]*DUST*255).astype(np.uint8)
    enc.stdin.write(frame.tobytes())
    if fi % 12 == 0: snap[round(t, 2)] = frame
    if fi % 30 == 0: print(f'{fi}/{nframes} {time.time() - t0w:.0f}s', flush=True)
    if '--debug' in sys.argv and fi % 6 == 0:
        fr = s < 0.2
        g_ = gust(x[fr], t) if fr.any() else (np.zeros(1),)*3
        print(f't={t:.2f} liberi={fr.mean():.2f} vx={vx[fr].mean() if fr.any() else 0:.0f} vento={g_[0].mean():.0f} x={x[fr].mean() if fr.any() else 0:.0f}', flush=True)
enc.stdin.close(); enc.wait()
# tavola di controllo
keys = sorted(snap)
tw = 300; th = int(tw*H/W); cols = 7
sheet = Image.new('RGB', (cols*(tw + 4), ((len(keys) + cols - 1)//cols)*(th + 4)), (40, 40, 40))
for i, k in enumerate(keys):
    sheet.paste(Image.fromarray(snap[k]).resize((tw, th)), ((i % cols)*(tw + 4), (i//cols)*(th + 4)))
sheet.save(f'/tmp/claude-0/sp/{name}.png')
print('video', out/f'{name}.mp4', (out/f'{name}.mp4').stat().st_size//1024, 'KB', f'{time.time() - t0w:.0f}s')
