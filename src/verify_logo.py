"""Verifica geometrica del logo pulito renderizzato in Chromium."""
import sys, math
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright
CHROME='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
S=4
txt=open('agora-logo.svg').read()
import re
vw,vh = [float(v) for v in re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', txt).groups()]
W,H=int(vw*S), int(vh*S)
svg=re.sub(r'width="[\d.]+" height="[\d.]+"', f'width="{W}" height="{H}"', txt, count=1)
html=f'<!doctype html><html><head><style>html,body{{margin:0;background:#fff}}svg{{display:block}}</style></head><body><div style="color:#000">{svg}</div></body></html>'
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=CHROME,args=['--no-sandbox','--disable-gpu'])
    pg=b.new_page(viewport={'width':W,'height':H}); pg.set_content(html); pg.wait_for_timeout(400)
    pg.screenshot(path='/tmp/logo_check.png', clip={'x':0,'y':0,'width':W,'height':H}); b.close()
m=np.array(Image.open('/tmp/logo_check.png').convert('L'))<128
ys,xs=np.where(m); C=(xs.min()+xs.max()+1)/2/S
def runs(y):
    idx=np.where(m[y])[0]; o=[];s=idx[0];p=idx[0]
    for i in idx[1:]:
        if i>p+1: o.append((s,p)); s=i
        p=i
    o.append((s,p)); return o
L=lambda r:(r[1]-r[0]+1)/S
print(f'centro asse: {C:.2f}')
r=runs(ys.min()+1); a,b=r[0][0]/S, (r[0][1]+1)/S
print(f'CIMA  {a:.2f} → {b:.2f}  larga {b-a:.2f}   distanza dal centro  sx {C-a:.2f}  dx {b-C:.2f}   Δ {abs((b-C)-(C-a)):.2f}')
r=runs(ys.max()-1)
l0,l1,r0,r1 = r[0][0]/S,(r[0][1]+1)/S,r[-1][0]/S,(r[-1][1]+1)/S
print(f'BASE  piede sx {l0:.2f}→{l1:.2f} ({l1-l0:.2f})   piede dx {r0:.2f}→{r1:.2f} ({r1-r0:.2f})   Δ {abs((l1-l0)-(r1-r0)):.2f}')
print(f'      dal centro: esterni {C-l0:.2f} / {r1-C:.2f}   interni {C-l1:.2f} / {r0-C:.2f}')
def edge(y0,y1,side):
    P=[]
    for y in range(int(y0*S),int(y1*S)):
        rr=runs(y); P.append(((rr[0][0] if side=='L' else rr[-1][1]+1)/S, y/S))
    P=np.array(P); k=np.polyfit(P[:,1],P[:,0],1)
    return math.degrees(math.atan2(1,abs(k[0]))), float(np.abs(np.polyval(k,P[:,1])-P[:,0]).max())
aL,eL=edge(500,668,'L'); aR,eR=edge(500,668,'R')
print(f'ANGOLI esterni  sx {aL:.3f}°  dx {aR:.3f}°   Δ {abs(aL-aR):.3f}°   (scarto dalla retta {eL:.2f} / {eR:.2f})')
for y in (520,580,640,665):
    rr=runs(int(y*S))
    print(f'PESO  y={y}: asta sx {L(rr[0])*math.sin(math.radians(aL)):.2f}   gamba dx {L(rr[-1])*math.sin(math.radians(aR)):.2f}')
