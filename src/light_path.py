"""Da path SVG (M/L/C assoluti) a polilinee."""
import numpy as np

def flatten(d, n=12):
    """path M/L/C assoluto -> lista di polilinee"""
    import re
    toks = re.findall(r'[MLCZ]|-?\d+\.?\d*', d); out = []; cur = None; i = 0
    while i < len(toks):
        t = toks[i]
        if t == 'M':
            cur = [np.array([float(toks[i+1]), float(toks[i+2])])]; out.append(cur); i += 3
        elif t == 'L':
            cur.append(np.array([float(toks[i+1]), float(toks[i+2])])); i += 3
        elif t == 'C':
            p0 = cur[-1]; c = np.array(toks[i+1:i+7], float).reshape(3, 2)
            for u in np.linspace(0, 1, n)[1:]:
                cur.append((1-u)**3*p0 + 3*(1-u)**2*u*c[0] + 3*(1-u)*u**2*c[1] + u**3*c[2])
            i += 7
        else:
            if cur: cur.append(cur[0])
            i += 1
    return [np.array(c) for c in out]

