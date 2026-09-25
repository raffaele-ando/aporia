"""Render in Chromium della v4 e confronto con l'immagine caricata."""
import sys, pickle, json; sys.path.insert(0, 'src')
import numpy as np
from PIL import Image
import eval_v3 as V
import emit_v4 as E
D = pickle.load(open('src/dust_v4_layers.pkl', 'rb'))
def build(P=E.P4, animated=False, **kw):
    return E.emit(D['hull'], D['open'], D['zone'], D['levels'], D['glows'], D['klevels'],
                  k_bg=D['k_bg'], P=P, animated=animated, **kw)
render, metrics, REF = V.render, V.metrics, V.REF
if __name__ == '__main__':
    over = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    r = render([build(dict(E.P4, **over))])[0]
    print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in metrics(r).items()})
    Image.fromarray((np.clip(r, 0, 1)*255).astype('uint8')).save('/tmp/claude-0/sp/full.png')
