import sys, pickle, json; sys.path.insert(0,'src')
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, distance_transform_edt
from playwright.sync_api import sync_playwright
import emit_v3 as E
CHROME='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
lv, gw, shape_d = pickle.load(open('src/dust_v3_layers.pkl','rb'))
hull_d = open('src/d_dust_hull.txt').read(); open_d = open('src/d_dust_open.txt').read()
REF = np.array(Image.open('src/src_dust.webp').convert('L')).astype(float)/255
def build(P, animated=False): return E.emit(shape_d, hull_d, open_d, lv, gw, P=P, animated=animated, y_soft_end=838.4)
def render(svgs):
    out=[]
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=CHROME,args=['--no-sandbox','--disable-gpu'])
        pg=b.new_page(viewport={'width':1254,'height':1254})
        for i,s in enumerate(svgs):
            pg.set_content(f'<!doctype html><html><head><style>html,body{{margin:0;background:#000}}svg{{display:block}}</style></head><body>{s}<style>svg#aporiaDustLogo{{--bg:#000}}</style></body></html>')
            pg.wait_for_timeout(250); pg.screenshot(path=f'/tmp/v3_{i}.png', clip={'x':0,'y':0,'width':1254,'height':1254})
            out.append(np.array(Image.open(f'/tmp/v3_{i}.png').convert('L')).astype(float)/255)
        b.close()
    return out
MASK = None
def metrics(r):
    global MASK
    if MASK is None:
        MASK = r > -1
    RM=gaussian_filter(REF,8); NM=gaussian_filter(r,8)
    sh = RM>0.03
    BINS=[(0.03,0.15),(0.15,0.3),(0.3,0.45),(0.45,0.6),(0.6,0.75),(0.75,0.9),(0.9,1.0)]
    pr=[float((REF-RM)[sh&(RM>=a)&(RM<b)].std()) for a,b in BINS]
    pn=[float((r-NM)[sh&(RM>=a)&(RM<b)].std()) for a,b in BINS]
    return dict(macro=float(np.sqrt(((NM-RM)**2).mean())), mae=float(np.abs(r-REF).mean()*255),
                gerr=float(np.sqrt(np.mean((np.array(pr)-np.array(pn))**2))), pr=[round(v,3) for v in pr], pn=[round(v,3) for v in pn])
if __name__=='__main__':
    r = render([build(E.P3)])[0]
    print(metrics(r))
    Image.fromarray((np.clip(r,0,1)*255).astype('uint8')).save('/tmp/v3.png')
