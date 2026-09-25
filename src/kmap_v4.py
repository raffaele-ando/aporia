"""Mappa dell'intensità della grana, misurata sull'originale (dopo la correzione della lettera):
1 = grana piena (corpo della A), valori bassi = polvere liscia e trascinata (fiume, bandiera)."""
import sys; sys.path.insert(0, 'src')
import numpy as np
from scipy.ndimage import gaussian_filter
from levels import level_paths

def kmap(ratio, Lw, top=1.15, lo=0.2):
    valid = ((Lw > 0.05) & (Lw < 0.95)).astype(float)
    r = np.clip(ratio, 0, 2.0)
    num = gaussian_filter(r*valid, 18); den = gaussian_filter(valid, 18)
    k = np.where(den > 0.02, num/np.maximum(den, 1e-6), 1.0)
    return np.clip(k/top, lo, 1.0)

def kmap_levels(k, N=8):
    """tracciati annidati: regioni dove la grana è SOTTO la soglia (si dipingono sopra un fondo pieno)"""
    out = []
    for i in range(N-1, 0, -1):
        t = i/N
        d = level_paths(1.0 - k, 1.0 - t, min_area=300, eps=2.0, prec=1)   # k < t
        if d: out.append((t - 0.5/N, d))
    return out

if __name__ == '__main__':
    # ratio = grana locale dell'originale / grana locale del render con k=1 (stessa luce),
    # Lw = luminanza sfocata dell'originale, entrambe già nel riferimento della lettera corretta
    ratio = np.load(sys.argv[1]); Lw = np.load(sys.argv[2])
    k = kmap(ratio, Lw)
    from PIL import Image
    Image.fromarray((k*255).round().astype(np.uint8)).save('src/kmap_v4.png')
    kl = kmap_levels(k)
    import pickle; pickle.dump(kl, open('src/kmap_v4_levels.pkl', 'wb'))
    print([round(t, 3) for t, _ in kl], sum(len(d) for _, d in kl))
