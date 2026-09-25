"""Fotografa il logo dust (dall'SVG vero, ../agora_loghi_svg) in due fotogrammi con grana diversa.
Il logo nell'intro è un'immagine: nessun filtro SVG da calcolare durante l'animazione, quindi niente
blocchi sui telefoni e nessun tremolio su Safari/iPad."""
import pathlib, re, io, base64, json
from PIL import Image
from playwright.sync_api import sync_playwright
root = pathlib.Path(__file__).resolve().parent.parent
svg0 = (root.parent/'agora_loghi_svg'/'agora-logo-dust-static.svg').read_text()
K = 1.15                                   # pixel per unità del viewBox
U0, V0, U1, V1 = 196, 196, 1044, 996       # ritaglio attorno alla lettera (con la polvere che esce)
CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'

def variant(seed_g, seed_s):
    s = re.sub(r'(id="agoraGrainNoise"[^>]*seed=")\d+', rf'\g<1>{seed_g}', svg0)
    s = re.sub(r'(id="agoraSpeckNoise"[^>]*seed=")\d+', rf'\g<1>{seed_s}', s)
    return s.replace('width="1254" height="1254"', f'width="{1254*K:.0f}" height="{1254*K:.0f}"', 1)

def smear_frame(a):
    """scia di vento del logo: sfocatura di movimento verso sinistra (da dove arriva la polvere),
    rigata da striature orizzontali; a metà risoluzione (è morbida) per pesare poco"""
    import numpy as np
    from scipy.ndimage import gaussian_filter, gaussian_filter1d
    A = np.asarray(a, np.float32)/255.
    A = A[::2, ::2]
    h, w = A.shape
    out = np.zeros_like(A); acc = np.zeros(h, np.float32); d = 0.94
    for x in range(w - 1, -1, -1):                     # la scia si allunga a sinistra
        acc = np.maximum(A[:, x], acc*d); out[:, x] = acc
    out = 0.55*out + 0.45*A
    out = gaussian_filter(out, (0.8, 2.5))
    rng = np.random.default_rng(3)
    stri = gaussian_filter1d(rng.random((h, w//8 + 2)).astype(np.float32), 0.6, axis=0)
    stri = np.repeat(stri, 8, axis=1)[:, :w]
    stri = gaussian_filter1d(stri, 12, axis=1)
    stri = np.clip((stri - stri.mean())*4.5 + 0.6, 0.05, 1.0)
    grain = np.clip(gaussian_filter(rng.normal(1.0, 0.35, (h, w)), 0.7)*1.0, 0.5, 1.4).astype(np.float32)
    x = np.arange(w)/w
    edge = np.clip(x/0.22, 0, 1)**1.5*np.clip((1 - x)/0.03, 0, 1)   # sfuma verso i bordi: nessun taglio netto
    S = np.clip(out*stri*grain*edge[None, :], 0, 1)
    img = Image.merge('RGBA', (Image.new('L', (w, h), 255),)*3 + (Image.fromarray((S*255).astype('uint8')),))
    buf = io.BytesIO(); img.save(buf, 'WEBP', quality=70, method=6)
    return 'data:image/webp;base64,' + base64.b64encode(buf.getvalue()).decode()

def main():
    frames, alphas = [], []
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
        pg = b.new_page(viewport={'width': int(1254*K), 'height': int(1254*K)})
        for sg, ss in [(7, 23), (43, 61)]:
            pg.set_content(f'<!doctype html><html><head><style>html,body{{margin:0;background:transparent}}svg{{display:block}}</style></head><body>{variant(sg, ss)}</body></html>')
            pg.wait_for_timeout(800)
            png = pg.screenshot(omit_background=True, clip={'x': U0*K, 'y': V0*K, 'width': (U1-U0)*K, 'height': (V1-V0)*K})
            im = Image.open(io.BytesIO(png)).convert('RGBA')
            a = im.getchannel('A')                       # il logo è bianco: basta l'alpha
            alphas.append(a)
            out = Image.merge('RGBA', (Image.new('L', im.size, 255),)*3 + (a,))
            buf = io.BytesIO(); out.save(buf, 'WEBP', quality=80, method=6)
            frames.append('data:image/webp;base64,' + base64.b64encode(buf.getvalue()).decode())
        b.close()
    frames.append(smear_frame(alphas[0]))
    meta = dict(u0=U0, v0=V0, u1=U1, v1=V1)
    (root/'src'/'logo_frames.json').write_text(json.dumps(dict(meta=meta, frames=frames)))
    print('fotogrammi', [len(f)//1024 for f in frames], 'KB')

if __name__ == '__main__':
    main()
