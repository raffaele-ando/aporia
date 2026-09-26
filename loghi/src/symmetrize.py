"""A con scheletro perfettamente simmetrico: base e cima orizzontali,
stessa distanza dal centro, stessi angoli, stessi pesi.
Trasformazione analitica: shear globale + correzione locale della gamba destra."""
import numpy as np, math

BASE, TOP = 892.578, 220.708
LF, RF = 270.910, 1073.660
CENTER = (LF + RF)/2.0
H = BASE - TOP
APEX_W = 151.20
APEX_L, APEX_R = CENTER - APEX_W/2, CENTER + APEX_W/2
SLOPE = (APEX_L - LF)/H                      # rientro per unità di altezza salendo
ANG   = math.degrees(math.atan2(1.0, SLOPE))
W_PERP = 153.00
W_HORIZ = W_PERP/math.sin(math.radians(ANG))

# geometria di partenza (dopo la regolarizzazione della gamba)
APEX_L0, APEX_R0 = 612.30, 763.47
SLOPE0_L = (APEX_L0 - LF)/H
SLOPE0_R = 0.495437                          # pendenza attuale del bordo esterno della gamba

K_SHEAR = (APEX_L0 - APEX_L)/H               # shear: la cima va a sinistra
K_LEG   = (SLOPE0_R + K_SHEAR) - SLOPE       # correzione angolare della gamba dopo lo shear

def left_outer(y):  return LF + SLOPE*(BASE-y)
def right_outer(y): return RF - SLOPE*(BASE-y)
def left_inner(y):  return left_outer(y) + W_HORIZ
def right_inner(y): return right_outer(y) - W_HORIZ

def smoothstep(t):
    t = min(max(t, 0.0), 1.0)
    return t*t*(3-2*t)

def transform(xy):
    out = xy.copy()
    for i,(x,y) in enumerate(xy):
        dy = BASE - y
        nx = x - K_SHEAR*dy                       # 1) shear globale
        # 2) correzione della gamba destra: torna all'angolo speculare
        fy = smoothstep((y - 470.0)/170.0)         # 0 sopra y=470, 1 sotto y=640
        if fy > 0:
            ri = right_inner(y); li = left_inner(y)
            mid = (li + ri)/2.0
            fx = smoothstep((nx - mid)/max(ri - mid, 1e-6))
            nx += K_LEG*dy*fy*fx
        out[i,0] = nx
    # 2b) bordi interni delle due aste: portali esattamente al peso voluto.
    #     Si agisce solo sui punti che sono GIA' praticamente sulla retta interna
    #     (peso che svanisce con la distanza), così le curve del fiume restano intatte.
    for i,(x,y) in enumerate(out):
        if y > BASE - 2.5: continue
        li, ri = left_inner(y), right_inner(y)
        for tgt, fy in ((li, smoothstep((y-560.0)/120.0)), (ri, smoothstep((y-660.0)/120.0))):
            if fy <= 0: continue
            dist = abs(x - tgt)
            if dist > 18.0: continue
            fd = 1.0 if dist <= 6.0 else 1.0 - (dist-6.0)/12.0
            out[i,0] = x + (tgt - x)*fy*fd
            break
    # 3) vincoli esatti: base e cima orizzontali
    out[np.abs(xy[:,1] - BASE) < 0.35, 1] = BASE
    out[np.abs(xy[:,1] - TOP)  < 0.35, 1] = TOP
    return out

def build(contour='src/contour_regular_full.npy'):
    xy = np.load(contour)
    out = transform(xy)
    # riallinea esattamente i bordi esterni (elimina derive di frazioni di pixel)
    for i,(x,y) in enumerate(out):
        if 2500 <= i <= 3512:  out[i,0] = left_outer(y)
        elif 3513 <= i < 3663: out[i,1] = TOP
    info = dict(angolo=round(ANG,4), apice=(round(APEX_L,2), round(APEX_R,2)),
                peso_perp=W_PERP, peso_oriz=round(W_HORIZ,2), centro=CENTER,
                shear=round(K_SHEAR,6), corr_gamba=round(K_LEG,6))
    return out, info
