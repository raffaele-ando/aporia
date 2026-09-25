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

def main():
    frames = []
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
        pg = b.new_page(viewport={'width': int(1254*K), 'height': int(1254*K)})
        for sg, ss in [(7, 23), (43, 61)]:
            pg.set_content(f'<!doctype html><html><head><style>html,body{{margin:0;background:transparent}}svg{{display:block}}</style></head><body>{variant(sg, ss)}</body></html>')
            pg.wait_for_timeout(800)
            png = pg.screenshot(omit_background=True, clip={'x': U0*K, 'y': V0*K, 'width': (U1-U0)*K, 'height': (V1-V0)*K})
            im = Image.open(io.BytesIO(png)).convert('RGBA')
            a = im.getchannel('A')                       # il logo è bianco: basta l'alpha
            out = Image.merge('RGBA', (Image.new('L', im.size, 255),)*3 + (a,))
            buf = io.BytesIO(); out.save(buf, 'WEBP', quality=80, method=6)
            frames.append('data:image/webp;base64,' + base64.b64encode(buf.getvalue()).decode())
        b.close()
    meta = dict(u0=U0, v0=V0, u1=U1, v1=V1)
    (root/'src'/'logo_frames.json').write_text(json.dumps(dict(meta=meta, frames=frames)))
    print('fotogrammi', [len(f)//1024 for f in frames], 'KB')

if __name__ == '__main__':
    main()
