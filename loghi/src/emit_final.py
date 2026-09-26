import sys, json; sys.path.insert(0,'work')
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from levels import level_paths

P = json.load(open('src/best_params.json'))
SHAPE_D = open('src/d_dust_shape2.txt').read()
CLEAN_D = open('src/d_tight.txt').read()

def build_levels():
    g = np.array(Image.open('src/src_dust.webp').convert('L')).astype(float)/255
    F = gaussian_filter(g, P['pre_sigma'])
    N = P['levels']
    out = []
    for i in range(1, N):
        d = level_paths(F, i/N, min_area=P['min_area'], eps=P['eps'], prec=1)
        if d: out.append(((i+0.5)/N, d))
    return out

def build_glow():
    g = np.array(Image.open('src/src_dust.webp').convert('L')).astype(float)/255
    shape = np.array(Image.open('src/dust_shape_mask.png').convert('L')).astype(float)/255 > 0.5
    from scipy.ndimage import binary_dilation
    outside = ~binary_dilation(shape, iterations=1)
    F = gaussian_filter(np.where(outside, g, 0.0), P['pre_sigma'])
    N = P['glow_levels']; out = []
    for i in range(1, N+1):
        t = P['glow_max']*i/(N+1)
        d = level_paths(F, t, min_area=P['glow_min_area'], eps=P['eps']*1.4, prec=1)
        if d: out.append((t + P['glow_max']/(2*(N+1)), d))
    return out

def gray(v, compensate=True):
    v = float(np.clip(v, 0, 1))
    gm = P['speck_mean']
    if compensate and gm > 0:
        v = (v - gm)/(1.0 - gm)
    c = int(round(float(np.clip(v, 0, 1))*255))
    return f'#{c:02x}{c:02x}{c:02x}'

def emit(animated=True):
    lv = build_levels(); gw = build_glow()
    lv_svg = "\n        ".join(f'<path fill="{gray(t)}" d="{d}"/>' for t, d in lv)
    gw_svg = "\n        ".join(f'<path fill="{gray(t)}" d="{d}"/>' for t, d in gw)
    gi = round(0.5 - P['grain_slope']*0.5, 4)
    si = round(-P['speck_slope']*P['speck_thr'], 4)
    anim = ''
    if animated:
        anim = '''
      <!-- ANIMAZIONI: rimuovi questi <animate> per una versione statica -->
      <animate xlink:href="#aporiaGrainNoise" attributeName="seed" values="7;19;31;43;55;67;79;91;7"
               dur="1.1s" calcMode="discrete" repeatCount="indefinite" id="aporiaBoil"/>
      <animate xlink:href="#aporiaGrainShift" attributeName="dx" values="0;46;0" dur="26s"
               repeatCount="indefinite" id="aporiaDriftX"/>
      <animate xlink:href="#aporiaGrainShift" attributeName="dy" values="0;-34;0" dur="37s"
               repeatCount="indefinite" id="aporiaDriftY"/>
      <animate xlink:href="#aporiaDisplace" attributeName="scale" values="0;3.2;0" dur="17s"
               repeatCount="indefinite" id="aporiaSwirl"/>
      <animate xlink:href="#aporiaFlowNoise" attributeName="baseFrequency" values="0.006;0.0085;0.006"
               dur="23s" repeatCount="indefinite" id="aporiaFlow"/>'''
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     viewBox="0 0 1254 1254" width="1254" height="1254" id="aporiaDustLogo"
     role="img" aria-labelledby="aporiaTitle aporiaDesc">
  <title id="aporiaTitle">Aporia — logo dust</title>
  <desc id="aporiaDesc">Logo Aporia, versione polvere. La polvere è procedurale e animabile:
  vedi i nodi #aporiaGrainNoise (grana), #aporiaSpeckNoise (granelli), #aporiaFlowNoise + #aporiaDisplace
  (deriva/turbolenza), #aporiaGrainShift (scorrimento). Variabili CSS: --dust-bg, --dust-glow,
  --dust-contrast, --dust-brightness, --dust-amount.</desc>
  <style>
    #aporiaDustLogo {{
      --dust-bg: #000000;        /* colore di fondo                        */
      --dust-glow: 1;            /* 0..1.5 intensità alone sui bordi       */
      --dust-contrast: 1;        /* contrasto generale                     */
      --dust-brightness: 1;      /* luminosità generale                    */
      --dust-amount: 1;          /* 0 = superficie pulita, 1 = polvere piena */
    }}
    #aporiaBg   {{ fill: var(--dust-bg); }}
    #aporiaGlow {{ opacity: var(--dust-glow); }}
    #aporiaDusty {{ opacity: var(--dust-amount); }}
    #aporiaArt  {{ filter: contrast(var(--dust-contrast)) brightness(var(--dust-brightness)); }}
    @media (prefers-reduced-motion: reduce) {{
      #aporiaBoil, #aporiaDriftX, #aporiaDriftY, #aporiaSwirl, #aporiaFlow {{ display: none; }}
    }}
  </style>
  <defs>
    <clipPath id="aporiaClip"><path d="{SHAPE_D}"/></clipPath>

    <!-- morbidezza del campo luminoso vettoriale -->
    <filter id="aporiaSoften" x="-15%" y="-15%" width="130%" height="130%" color-interpolation-filters="sRGB">
      <feGaussianBlur stdDeviation="{P['post_sigma']}"/>
    </filter>

    <!-- diffusione dell'alone esterno -->
    <filter id="aporiaBloom" x="-25%" y="-25%" width="150%" height="150%" color-interpolation-filters="sRGB">
      <feGaussianBlur stdDeviation="{P['glow_sigma']}"/>
    </filter>

    <!-- ============ MOTORE POLVERE ============ -->
    <filter id="aporiaDust" x="-20%" y="-20%" width="140%" height="140%" color-interpolation-filters="sRGB">
      <!-- 1. grana fine -->
      <feTurbulence id="aporiaGrainNoise" type="fractalNoise" baseFrequency="{P['grain_freq']}"
                    numOctaves="{P['grain_oct']}" seed="{P['grain_seed']}" result="noiseGrain"/>
      <feOffset id="aporiaGrainShift" in="noiseGrain" dx="0" dy="0" result="noiseGrainMoved"/>
      <feColorMatrix in="noiseGrainMoved" type="matrix" result="grain"
        values="{P['grain_slope']} 0 0 0 {gi} {P['grain_slope']} 0 0 0 {gi} {P['grain_slope']} 0 0 0 {gi} 0 0 0 0 1"/>

      <!-- 2. granelli sparsi (le particelle che brillano nelle zone scure) -->
      <feTurbulence id="aporiaSpeckNoise" type="fractalNoise" baseFrequency="{P['speck_freq']}"
                    numOctaves="1" seed="{P['speck_seed']}" result="noiseSpeck"/>
      <feColorMatrix in="noiseSpeck" type="matrix" result="speckMono"
        values="1 0 0 0 0  1 0 0 0 0  1 0 0 0 0  0 0 0 0 1"/>
      <feComponentTransfer in="speckMono" result="speck">
        <feFuncR type="linear" slope="{P['speck_slope']}" intercept="{si}"/>
        <feFuncG type="linear" slope="{P['speck_slope']}" intercept="{si}"/>
        <feFuncB type="linear" slope="{P['speck_slope']}" intercept="{si}"/>
        <feFuncA type="table" tableValues="1 1"/>
      </feComponentTransfer>

      <!-- 3. campo di flusso: sposta la polvere e la superficie -->
      <feTurbulence id="aporiaFlowNoise" type="fractalNoise" baseFrequency="{P['warp_freq']}"
                    numOctaves="2" seed="{P['warp_seed']}" result="noiseFlow"/>
      <feDisplacementMap id="aporiaDisplace" in="SourceGraphic" in2="noiseFlow" scale="{P['warp_scale']}"
                         xChannelSelector="R" yChannelSelector="G" result="surface"/>

      <!-- 4. composizione -->
      <feBlend in="grain" in2="surface" mode="overlay" result="dusted"/>
      <feBlend in="speck" in2="dusted" mode="screen" result="dustedSpecks"/>
      <feComposite in="dustedSpecks" in2="surface" operator="in"/>{anim}
    </filter>
  </defs>

  <rect id="aporiaBg" width="1254" height="1254"/>

  <g id="aporiaArt">
    <g id="aporiaDusty" filter="url(#aporiaDust)">
      <g id="aporiaGlow" filter="url(#aporiaBloom)">
        {gw_svg}
      </g>
      <g id="aporiaShaded" clip-path="url(#aporiaClip)" filter="url(#aporiaSoften)">
        <path id="aporiaBase" fill="#000" d="{SHAPE_D}"/>
        {lv_svg}
      </g>
    </g>
  </g>
</svg>
'''

if __name__ == '__main__':
    open('aporia-logo-dust.svg','w').write(emit(True))
    open('aporia-logo-dust-static.svg','w').write(emit(False))
    print('written', len(open('aporia-logo-dust.svg').read())//1024, 'KB')
