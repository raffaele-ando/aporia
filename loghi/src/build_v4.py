"""Genera i file dust v4, il laboratorio e le anteprime.
Prima (solo se cambia la luce): python src/light_v4.py  -> src/dust_v4_layers.pkl"""
import sys, re, subprocess; sys.path.insert(0, 'src')
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright
import eval_v4 as V4

CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'

anim = V4.build(animated=True)
static = V4.build(animated=False)
inv = V4.build(animated=False, title='Aporia — logo dust (inverso)')
inv = inv.replace('--ink: #ffffff;', '--ink: #0b0b0c;').replace('--mask: url(#aporiaMaskLight);', '--mask: url(#aporiaMaskDark);')
open('aporia-logo-dust.svg', 'w').write(anim)
open('aporia-logo-dust-static.svg', 'w').write(static)
open('aporia-logo-dust-inverted.svg', 'w').write(inv)

# versione ritagliata sulla forma (con margine per la polvere che esce dalla bandiera)
nums = [float(x) for x in re.findall(r'-?\d+\.?\d*', V4.D['hull'])]
xs = np.array(nums[0::2]); ys = np.array(nums[1::2]); m = 26
x0, y0 = xs.min()-m, ys.min()-m; wd, h = (xs.max()-xs.min())+2*m, (ys.max()-ys.min())+2*m
open('aporia-logo-dust-tight.svg', 'w').write(anim
    .replace('viewBox="0 0 1254 1254" width="1254" height="1254"', f'viewBox="{x0:.1f} {y0:.1f} {wd:.1f} {h:.1f}" width="{wd:.0f}" height="{h:.0f}"')
    .replace('<rect id="aporiaBg" width="1254" height="1254"/>', f'<rect id="aporiaBg" x="{x0:.1f}" y="{y0:.1f}" width="{wd:.1f}" height="{h:.1f}"/>')
    .replace('<rect id="aporiaInk" width="1254" height="1254"/>', f'<rect id="aporiaInk" x="{x0:.1f}" y="{y0:.1f}" width="{wd:.1f}" height="{h:.1f}"/>'))

subprocess.run([sys.executable, 'src/emit_lab.py'], check=True)

# anteprime
def shot(pg, svg, css, bg, w, h, path):
    pg.set_viewport_size({'width': w, 'height': h})
    pg.set_content(f'<!doctype html><html><head><style>html,body{{margin:0;background:{bg}}}svg{{display:block;width:{w}px;height:{h}px}}</style></head>'
                   f'<body>{svg}<style>{css}</style></body></html>')
    pg.wait_for_timeout(600); pg.screenshot(path=path)

errors = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox', '--disable-gpu'])
    pg = b.new_page(); pg.on('console', lambda m: errors.append(m.text)); pg.on('pageerror', lambda e: errors.append(str(e)))
    shot(pg, static, '', '#000', 720, 720, 'preview/aporia-logo-dust.png')
    shot(pg, inv, 'svg#aporiaDustLogo{--bg:#f2efe9}', '#f2efe9', 720, 720, 'preview/aporia-logo-dust-inverso.png')
    shot(pg, static, 'svg#aporiaDustLogo{--ink:url(#aporiaGradient)}', '#0b0c10', 720, 720, 'preview/aporia-logo-dust-gradiente.png')
    tight = open('aporia-logo-dust-tight.svg').read()
    shot(pg, tight, '', '#000', 720, int(round(720*h/wd)), 'preview/aporia-logo-dust-tight.png')
    for f in ['aporia-logo-dust.svg', 'aporia-logo-dust-static.svg', 'aporia-logo-dust-inverted.svg', 'aporia-logo-dust-tight.svg']:
        pg.goto('file://' + __import__('os').path.abspath(f)); pg.wait_for_timeout(500)
    pg.goto('file://' + __import__('os').path.abspath('aporia-dust-lab.html')); pg.wait_for_timeout(800)
    for sel in ['#tk', '#sw', '#hl', '#gs', '#amt']:
        pg.eval_on_selector(sel, "e => { e.value = e.min; e.dispatchEvent(new Event('input')); }")
    pg.click('#m_dark'); pg.click('#p_grad'); pg.click('#reset'); pg.wait_for_timeout(300)
    b.close()
print('errori console:', errors)

# confronto con l'immagine caricata
r = V4.render([static])[0]
ref = Image.open('src/src_dust.webp').convert('L')
new = Image.fromarray((np.clip(r, 0, 1)*255).astype('uint8'))
C = Image.new('L', (1261, 627)); C.paste(ref.resize((627, 627)), (0, 0)); C.paste(new.resize((627, 627)), (634, 0))
C.save('preview/confronto-dust.png')
print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in V4.metrics(r).items()})
