"""Logo dust v4.

Rispetto alla v3:
- la luce vicino a fiume e bandiera è quella vera dell'immagine e sfuma da sola (la sagoma
  lì non taglia), mentre sui bordi esterni della A resta netta;
- la superficie è resa opaca prima della grana: niente più aloni/linee grigie dove la luce
  sfuma (era la causa delle "linee" tra polvere e bianco);
- l'intensità della grana varia come nell'originale: piena sul corpo della A, polvere liscia
  e trascinata a strisce nel fiume;
- --dust passa davvero da superficie pulita (0) a polvere piena (1).

Dentro la maschera la sorgente usa due canali: rosso/verde = luce, blu = intensità della
grana. I filtri leggono i canali separatamente e restituiscono sempre un grigio."""
import numpy as np

P4 = dict(
    soften=4.0,            # morbidezza del campo luminoso
    feather_soft=4.5, feather_hard=1.1, feather_zone=8.0,
    glow_sigma=2.0,
    kmap_blur=10.0,        # morbidezza della mappa di intensità della grana
    flow_freq=0.011, flow_oct=2, flow_seed=5,
    grain_fx=0.50, grain_fy=0.34, grain_oct=3, grain_seed=7, grain_slope=1.8, sweep=14,
    streak_fx=0.010, streak_fy=0.16, streak_oct=3, streak_seed=11, streak_slope=1.2, streak_sweep=40,
    speck_fx=0.34, speck_fy=0.21, speck_oct=3, speck_seed=23, speck_slope=5.0, speck_thr=0.60,
    speck_sweep=22, halo=9.0, speck_gain=1.0,
    highlight="1 1 1 1 1 0.95 0.82 0.6 0.3",   # quanta polvere per fascia di luce (dal nero al bianco)
    edge_sigmas=(0.6, 3.5, 9.0), edge_top=14.0, edge_map_blur=7.0,   # morbidezza del bordo: netto -> sfumato
)

def rg(v):
    c = int(round(float(np.clip(v, 0, 1))*255)); return f'#{c:02x}0000'

def gr(v):
    c = int(round(float(np.clip(v, 0, 1))*255)); return f'#00{c:02x}00'

def bl(v):
    c = int(round(float(np.clip(v, 0, 1))*255)); return f'#0000{c:02x}'

R2RGB = "1 0 0 0 0  1 0 0 0 0  1 0 0 0 0  0 0 0 1 0"
B2RGB = "0 0 1 0 0  0 0 1 0 0  0 0 1 0 0  0 0 0 0 1"
G2RGB = "0 1 0 0 0  0 1 0 0 0  0 1 0 0 0  0 0 0 0 1"

def dust_filter(fid, P, invert=False, animated=True):
    sfx = 'Inv' if invert else ''
    gs = P['grain_slope']; gi = round(0.5 - gs*0.5, 4)
    ts = P['streak_slope']; ti = round(0.5 - ts*0.5, 4)
    ss = P['speck_slope']; si = round(-ss*P['speck_thr'], 4)
    anim = ''
    if animated and not invert:
        anim = '''
      <animate xlink:href="#aporiaGrainNoise" attributeName="seed" values="7;19;31;43;55;67;79;91;7"
               dur="1.1s" calcMode="discrete" repeatCount="indefinite" id="aporiaBoil"/>
      <animate xlink:href="#aporiaGrainShift" attributeName="dx" values="0;46;0" dur="26s" repeatCount="indefinite" id="aporiaDriftX"/>
      <animate xlink:href="#aporiaGrainShift" attributeName="dy" values="0;-34;0" dur="37s" repeatCount="indefinite" id="aporiaDriftY"/>
      <animate xlink:href="#aporiaStreakShift" attributeName="dx" values="0;-120;0" dur="19s" repeatCount="indefinite" id="aporiaStream"/>
      <animate xlink:href="#aporiaSweep" attributeName="scale" values="%(sw)s;%(sw2)s;%(sw)s" dur="17s" repeatCount="indefinite" id="aporiaSwirl"/>
      <animate xlink:href="#aporiaFlowNoise" attributeName="baseFrequency" values="%(ff)s;%(ff2)s;%(ff)s" dur="23s" repeatCount="indefinite" id="aporiaFlow"/>''' % dict(
            sw=P['sweep'], sw2=round(P['sweep']*1.6, 2), ff=P['flow_freq'], ff2=round(P['flow_freq']*1.35, 5))
    tail = '''
      <feComposite in="speckW" in2="base" operator="over"/>'''
    if invert:
        tail = '''
      <feComposite in="speckW" in2="base" operator="over" result="final0"/>
      <feComponentTransfer in="final0">
        <feFuncR type="table" tableValues="1 0"/><feFuncG type="table" tableValues="1 0"/><feFuncB type="table" tableValues="1 0"/>
      </feComponentTransfer>'''
    return f'''<filter id="{fid}" x="-20%" y="-20%" width="140%" height="140%" color-interpolation-filters="sRGB">
      <!-- campo di flusso: guida il movimento della polvere -->
      <feTurbulence id="aporiaFlowNoise{sfx}" type="fractalNoise" baseFrequency="{P['flow_freq']}" numOctaves="{P['flow_oct']}" seed="{P['flow_seed']}" result="flow"/>
      <!-- sorgente resa opaca (su nero; su bianco nella versione inversa): niente aloni grigi ai bordi -->
      <feFlood flood-color="#000" result="black"/>
      <feComposite in="SourceGraphic" in2="black" operator="over" result="opaque"/>
      <feDisplacementMap id="aporiaDisplace{sfx}" in="opaque" in2="flow" scale="0" xChannelSelector="R" yChannelSelector="G" result="src"/>
      <!-- canale rosso = luce, blu = intensità della grana, verde = dove la polvere è trascinata -->
      <feColorMatrix in="src" type="matrix" values="{R2RGB}" result="surface"/>
      <feColorMatrix in="src" type="matrix" values="{G2RGB}" result="drag"/>
      <feColorMatrix in="src" type="matrix" values="{B2RGB}" result="k0"/>
      <feGaussianBlur id="aporiaGrainMapBlur{sfx}" in="k0" stdDeviation="{P['kmap_blur']}" result="k"/>
      <feComponentTransfer in="k" result="ik"><feFuncR type="table" tableValues="1 0"/><feFuncG type="table" tableValues="1 0"/><feFuncB type="table" tableValues="1 0"/></feComponentTransfer>
      <!-- grana: rumore spazzato dal flusso -->
      <feTurbulence id="aporiaGrainNoise{sfx}" type="fractalNoise" baseFrequency="{P['grain_fx']} {P['grain_fy']}" numOctaves="{P['grain_oct']}" seed="{P['grain_seed']}" result="g0"/>
      <feOffset id="aporiaGrainShift{sfx}" in="g0" dx="0" dy="0" result="g1"/>
      <feDisplacementMap id="aporiaSweep{sfx}" in="g1" in2="flow" scale="{P['sweep']}" xChannelSelector="R" yChannelSelector="G" result="g2"/>
      <feColorMatrix in="g2" type="matrix" result="grain"
        values="{gs} 0 0 0 {gi} {gs} 0 0 0 {gi} {gs} 0 0 0 {gi} 0 0 0 0 1"/>
      <!-- scie: polvere trascinata lungo il fiume -->
      <feTurbulence id="aporiaStreakNoise{sfx}" type="fractalNoise" baseFrequency="{P['streak_fx']} {P['streak_fy']}" numOctaves="{P['streak_oct']}" seed="{P['streak_seed']}" result="t0"/>
      <feOffset id="aporiaStreakShift{sfx}" in="t0" dx="0" dy="0" result="t1"/>
      <feDisplacementMap in="t1" in2="flow" scale="{P['streak_sweep']}" xChannelSelector="G" yChannelSelector="R" result="t2"/>
      <feColorMatrix in="t2" type="matrix" result="streak"
        values="{ts} 0 0 0 {ti} {ts} 0 0 0 {ti} {ts} 0 0 0 {ti} 0 0 0 0 1"/>
      <!-- sui bianchi la polvere si dirada piano piano (come nell'originale), niente confine netto -->
      <feComponentTransfer id="aporiaHighlight{sfx}" in="surface" result="hl">
        <feFuncR type="table" tableValues="{P['highlight']}"/><feFuncG type="table" tableValues="{P['highlight']}"/><feFuncB type="table" tableValues="{P['highlight']}"/>
      </feComponentTransfer>
      <feComposite in="k" in2="hl" operator="arithmetic" k1="1" k2="0" k3="0" k4="0" result="kh"/>
      <!-- miscela: grana dove k è alto, scie dove k è basso -->
      <feComposite in="grain" in2="kh" operator="arithmetic" k1="1" k2="0" k3="-0.5" k4="0.5" result="gK"/>
      <feComposite in="ik" in2="drag" operator="arithmetic" k1="1" k2="0" k3="0" k4="0" result="sw0"/>
      <feComposite in="sw0" in2="hl" operator="arithmetic" k1="1" k2="0" k3="0" k4="0" result="sw"/>
      <feComposite in="streak" in2="sw" operator="arithmetic" k1="1" k2="0" k3="-0.5" k4="0.5" result="sK"/>
      <feComposite in="gK" in2="sK" operator="arithmetic" k1="0" k2="1" k3="1" k4="-0.5" result="texture"/>
      <feBlend in="texture" in2="surface" mode="overlay" result="dusted"/>
      <!-- tono: curva che lascia fermi nero e bianco (esposizione e contrasto senza tagli netti) -->
      <feComponentTransfer id="aporiaTone{sfx}" in="dusted" result="base">
        <feFuncR type="table" tableValues="0 1"/><feFuncG type="table" tableValues="0 1"/><feFuncB type="table" tableValues="0 1"/>
      </feComponentTransfer>
      <!-- granelli: grumi irregolari, trascinati dal flusso -->
      <feTurbulence id="aporiaSpeckNoise{sfx}" type="fractalNoise" baseFrequency="{P['speck_fx']} {P['speck_fy']}" numOctaves="{P['speck_oct']}" seed="{P['speck_seed']}" result="s0"/>
      <feDisplacementMap in="s0" in2="flow" scale="{P['speck_sweep']}" xChannelSelector="G" yChannelSelector="R" result="s1"/>
      <feColorMatrix in="s1" type="matrix" result="s2" values="1 0 0 0 0  1 0 0 0 0  1 0 0 0 0  0 0 0 0 1"/>
      <feComponentTransfer in="s2" result="speck">
        <feFuncR type="linear" slope="{ss}" intercept="{si}"/><feFuncG type="linear" slope="{ss}" intercept="{si}"/><feFuncB type="linear" slope="{ss}" intercept="{si}"/>
      </feComponentTransfer>
      <feColorMatrix in="speck" type="luminanceToAlpha" result="speckA"/>
      <!-- i granelli stanno dove c'è luce e si disperdono poco oltre -->
      <feColorMatrix in="surface" type="luminanceToAlpha" result="lum"/>
      <feGaussianBlur id="aporiaHalo{sfx}" in="lum" stdDeviation="{P['halo']}" result="halo"/>
      <feComposite in="speckA" in2="halo" operator="in" result="speckLit0"/>
      <!-- fuori dalla lettera solo nella zona morbida (la sagoma è nel canale alpha) -->
      <feComposite in="speckLit0" in2="SourceAlpha" operator="in" result="speckLit"/>
      <feFlood flood-color="#fff" result="white"/>
      <feComposite in="white" in2="speckLit" operator="in" result="speckW0"/>
      <feComponentTransfer in="speckW0" result="speckW"><feFuncA id="aporiaSpeckGain{sfx}" type="linear" slope="{P['speck_gain']}" intercept="0"/></feComponentTransfer>{tail}{anim}
    </filter>'''

def edge_filter(fid, P, open_top):
    """bordo della lettera con morbidezza che cambia lungo il contorno:
    rosso = sagoma, verde = morbidezza (0 netto ... 1 sfumato). Uscita: maschera in grigio."""
    s1, s2, s3 = P['edge_sigmas']
    top = ('<feFlood flood-color="#fff" result="b4"/>' if open_top else
           f'<feGaussianBlur in="shp" stdDeviation="{P["edge_top"]}" result="b4"/>')
    tent = lambda v: f'<feFuncR type="table" tableValues="{v}"/><feFuncG type="table" tableValues="{v}"/><feFuncB type="table" tableValues="{v}"/>'
    return f'''<filter id="{fid}" x="-10%" y="-10%" width="120%" height="120%" color-interpolation-filters="sRGB">
      <feColorMatrix in="SourceGraphic" type="matrix" values="{R2RGB.replace('0 0 0 1 0', '0 0 0 0 1')}" result="shp"/>
      <feColorMatrix in="SourceGraphic" type="matrix" values="{G2RGB}" result="soft0"/>
      <feGaussianBlur in="soft0" stdDeviation="{P['edge_map_blur']}" result="soft"/>
      <feGaussianBlur in="shp" stdDeviation="{s1}" result="b1"/>
      <feGaussianBlur in="shp" stdDeviation="{s2}" result="b2"/>
      <feGaussianBlur in="shp" stdDeviation="{s3}" result="b3"/>
      {top}
      <feComponentTransfer in="soft" result="w1">{tent("1 1 0 0 0")}</feComponentTransfer>
      <feComponentTransfer in="soft" result="w2">{tent("0 0 1 0 0")}</feComponentTransfer>
      <feComponentTransfer in="soft" result="w3">{tent("0 0 0 1 0")}</feComponentTransfer>
      <feComponentTransfer in="soft" result="w4">{tent("0 0 0 0 1")}</feComponentTransfer>
      <feComposite in="b1" in2="w1" operator="arithmetic" k1="1" result="p1"/>
      <feComposite in="b2" in2="w2" operator="arithmetic" k1="1" result="p2"/>
      <feComposite in="b3" in2="w3" operator="arithmetic" k1="1" result="p3"/>
      <feComposite in="b4" in2="w4" operator="arithmetic" k1="1" result="p4"/>
      <feComposite in="p1" in2="p2" operator="arithmetic" k2="1" k3="1" result="q1"/>
      <feComposite in="p3" in2="p4" operator="arithmetic" k2="1" k3="1" result="q2"/>
      <feComposite in="q1" in2="q2" operator="arithmetic" k2="1" k3="1"/>
    </filter>'''

def emit(hull_d, open_d, zone_d, levels, glows, klevels, k_bg=0.87, P=P4, animated=True,
         title='Aporia — logo dust', y_soft_end=838.4, drag_y0=640, drag_y1=780, slevels=()):
    import re
    base_y = max(float(v) for v in re.findall(r'-?\d+\.?\d*', hull_d)[1::2])
    lv = "\n        ".join(f'<path fill="{rg(t)}" d="{d}"/>' for t, d in levels)
    gw = "\n        ".join(f'<path fill="{rg(t)}" d="{d}"/>' for t, d in glows)
    kl = "\n        ".join(f'<path fill="{bl(t)}" d="{d}"/>' for t, d in klevels)
    sl = "\n        ".join(f'<path fill="{gr(t)}" d="{d}"/>' for t, d in slevels)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     viewBox="0 0 1254 1254" width="1254" height="1254" id="aporiaDustLogo"
     role="img" aria-labelledby="aporiaTitle aporiaDesc">
  <title id="aporiaTitle">{title}</title>
  <desc id="aporiaDesc">Logo Aporia con polvere procedurale. Il disegno è una maschera:
  --ink colore o gradiente, --bg fondo (trasparente di default), --mask polarità.</desc>
  <style>
    #aporiaDustLogo {{
      --ink: #ffffff; --bg: transparent; --mask: url(#aporiaMaskLight);
      --glow: 1; --dust: 1;
      --c1: #ff8a3d; --c2: #ff2e63; --c3: #4d5bff;
    }}
    #aporiaBg   {{ fill: var(--bg); }}
    #aporiaInk  {{ fill: var(--ink); mask: var(--mask); }}
    #aporiaGlowLayer {{ opacity: var(--glow); }}
    #aporiaDustyLight, #aporiaDustyDark {{ opacity: var(--dust); }}
    #aporiaLight, #aporiaLightDark, #aporiaDragMap, #aporiaEdgeLetter {{ mix-blend-mode: screen; }}
    @media (prefers-reduced-motion: reduce) {{
      #aporiaBoil, #aporiaDriftX, #aporiaDriftY, #aporiaStream, #aporiaSwirl, #aporiaFlow {{ display: none; }}
    }}
  </style>
  <defs>
    <linearGradient id="aporiaGradient" x1="0" y1="1" x2="1" y2="0">
      <stop offset="0" stop-color="var(--c1)"/><stop offset="0.5" stop-color="var(--c2)"/><stop offset="1" stop-color="var(--c3)"/>
    </linearGradient>

    <filter id="aporiaSoften" x="-15%" y="-15%" width="130%" height="130%" color-interpolation-filters="sRGB">
      <feGaussianBlur stdDeviation="{P['soften']}"/>
    </filter>
    <filter id="aporiaBloom" x="-25%" y="-25%" width="150%" height="150%" color-interpolation-filters="sRGB">
      <feGaussianBlur stdDeviation="{P['glow_sigma']}"/>
    </filter>
    <!-- superficie pulita (--dust: 0): legge solo il canale della luce -->
    <filter id="aporiaPlain" x="-20%" y="-20%" width="140%" height="140%" color-interpolation-filters="sRGB">
      <feColorMatrix type="matrix" values="{R2RGB}"/>
    </filter>
    <!-- inversione per la polarità scuro-su-chiaro (stessa polvere, stesse animazioni) -->
    <filter id="aporiaInvert" x="-20%" y="-20%" width="140%" height="140%" color-interpolation-filters="sRGB">
      <feFlood flood-color="#000" result="black"/>
      <feComposite in="SourceGraphic" in2="black" operator="over" result="o"/>
      <feColorMatrix in="o" type="matrix" values="-1 0 0 0 1  -1 0 0 0 1  -1 0 0 0 1  0 0 0 0 1"/>
    </filter>
    <linearGradient id="aporiaDragFade" gradientUnits="userSpaceOnUse" x1="0" y1="{drag_y0}" x2="0" y2="{drag_y1}">
      <stop offset="0" stop-color="#00ff00"/><stop offset="1" stop-color="#000000"/>
    </linearGradient>
    {edge_filter('aporiaEdge', P, True)}
    {edge_filter('aporiaEdgeShape', P, False)}
    <!-- sagoma (rosso) e morbidezza del bordo (verde): netta su lati, cima e base,
         sempre più sfumata verso fiume e bandiera, senza salti -->
    <g id="aporiaEdgeSource">
      <rect x="-40" y="-40" width="1334" height="1334" fill="#000"/>
      <g id="aporiaEdgeSoftness">
        {sl}
      </g>
      <g id="aporiaEdgeLetter">
        <path fill="#f00" d="{hull_d}"/>
        <path fill="#000" d="{open_d}"/>
      </g>
    </g>
    <!-- sagoma per la versione inversa: sfuma ma resta dentro la lettera -->
    <mask id="aporiaShape" maskUnits="userSpaceOnUse" x="-40" y="-40" width="1334" height="1334">
      <g filter="url(#aporiaEdgeShape)"><use xlink:href="#aporiaEdgeSource"/></g>
      <rect x="-40" y="{base_y}" width="1334" height="400" fill="#000"/>
    </mask>
    <!-- superficie: dove il bordo è morbido decide solo la luce -->
    <mask id="aporiaSurface" maskUnits="userSpaceOnUse" x="-40" y="-40" width="1334" height="1334">
      <g filter="url(#aporiaEdge)"><use xlink:href="#aporiaEdgeSource"/></g>
      <!-- sotto la base non passa nulla: base netta e a 0° -->
      <rect x="-40" y="{base_y}" width="1334" height="400" fill="#000"/>
    </mask>

    {dust_filter('aporiaDustFx', P, invert=False, animated=animated)}

    <!-- luce non ritagliata (prolungata oltre i bordi netti) -->
    <g id="aporiaFieldRaw" filter="url(#aporiaSoften)">
        {lv}
    </g>
    <!-- sorgente della polvere: rosso = luce, blu = intensità della grana, verde = trascinamento -->
    <g id="aporiaSource">
      <g id="aporiaMaps" mask="url(#aporiaSurface)">
      <g id="aporiaGrainMap">
        <rect x="-40" y="-40" width="1334" height="1334" fill="{bl(k_bg)}"/>
        {kl}
      </g>
      <rect id="aporiaDragMap" x="-40" y="-40" width="1334" height="1334" fill="url(#aporiaDragFade)"/>
      </g>
      <g id="aporiaLight">
        <g id="aporiaGlowLayer">
          <g id="aporiaGlowField" filter="url(#aporiaBloom)">
            {gw}
          </g>
        </g>
        <g id="aporiaField" mask="url(#aporiaSurface)"><use xlink:href="#aporiaFieldRaw"/></g>
      </g>
    </g>

    <mask id="aporiaMaskLight" maskUnits="userSpaceOnUse" x="-40" y="-40" width="1334" height="1334">
      <g filter="url(#aporiaPlain)"><use xlink:href="#aporiaSource"/></g>
      <g id="aporiaDustyLight" filter="url(#aporiaDustFx)"><use xlink:href="#aporiaSource"/></g>
    </mask>
    <!-- versione inversa: la luce non ritagliata, il bordo lo decide solo la sagoma
         (se la luce venisse tagliata due volte resterebbe un filo scuro lungo il contorno) -->
    <g id="aporiaSourceDark">
      <use xlink:href="#aporiaMaps"/>
      <g id="aporiaLightDark"><use xlink:href="#aporiaFieldRaw"/></g>
    </g>
    <mask id="aporiaMaskDark" maskUnits="userSpaceOnUse" x="-40" y="-40" width="1334" height="1334">
      <g mask="url(#aporiaShape)"><g filter="url(#aporiaInvert)">
        <g filter="url(#aporiaPlain)"><use xlink:href="#aporiaSourceDark"/></g>
        <g id="aporiaDustyDark" filter="url(#aporiaDustFx)"><use xlink:href="#aporiaSourceDark"/></g>
      </g></g>
    </mask>
  </defs>
  <rect id="aporiaBg" width="1254" height="1254"/>
  <rect id="aporiaInk" width="1254" height="1254"/>
</svg>
'''
