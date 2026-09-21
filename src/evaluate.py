import sys, os, json; sys.path.insert(0,'work')
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from playwright.sync_api import sync_playwright
CHROME='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'

REF = np.array(Image.open('src/src_dust.webp').convert('L')).astype(float)/255
SHAPE = np.array(Image.open('src/dust_shape_mask.png').convert('L')).astype(float)/255 > 0.5
REF_MACRO = gaussian_filter(REF, 8)
REF_GRAIN = REF - REF_MACRO

def render_batch(svgs, size=1254, scale=0.5):
    """Render a list of svg strings; returns list of grayscale arrays."""
    out = []
    w = int(size*scale)
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox','--disable-gpu'])
        pg = b.new_page(viewport={'width':w,'height':w}, device_scale_factor=1)
        for i, svg in enumerate(svgs):
            svg = svg.replace('width="1254" height="1254"', f'width="{w}" height="{w}"')
            html = f'<!doctype html><html><head><style>html,body{{margin:0;background:#000;overflow:hidden}}svg{{display:block}}</style></head><body>{svg}</body></html>'
            pg.set_content(html); pg.wait_for_timeout(120)
            path = f'/tmp/_r{i}.png'
            pg.screenshot(path=path, clip={'x':0,'y':0,'width':w,'height':w})
            out.append(np.array(Image.open(path).convert('L')).astype(float)/255)
        b.close()
    return out

def metrics(ren, scale=0.5):
    if ren.shape[0] != REF.shape[0]:
        ref = np.array(Image.fromarray((REF*255).astype('uint8')).resize(ren.shape[::-1], Image.LANCZOS)).astype(float)/255
        shape = np.array(Image.fromarray(SHAPE.astype('uint8')*255).resize(ren.shape[::-1], Image.NEAREST)).astype(float)/255 > 0.5
        sig = 8*scale
    else:
        ref, shape, sig = REF, SHAPE, 8
    rm = gaussian_filter(ref, sig); rn = gaussian_filter(ren, sig)
    macro = float(np.sqrt(((rm-rn)**2).mean()))
    macro_in = float(np.sqrt((((rm-rn)[shape])**2).mean()))
    gr = ref-rm; gn = ren-rn
    # grain std as a function of macro level
    bins = [(0.05,0.25),(0.25,0.5),(0.5,0.75),(0.75,0.95)]
    gerr = 0.0; gdet = []
    for lo, hi in bins:
        sel = shape & (rm>=lo) & (rm<hi)
        if sel.sum() > 200:
            a, b_ = gr[sel].std(), gn[sel].std()
            gdet.append((round(a,4), round(b_,4)))
            gerr += (a-b_)**2
    gerr = float(np.sqrt(gerr/max(len(gdet),1)))
    full = float(np.sqrt(((ref-ren)**2).mean()))
    return dict(macro=macro, macro_in=macro_in, grain=gerr, gdet=gdet, full=full)
