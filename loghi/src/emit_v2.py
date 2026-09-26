"""Genera i loghi dust con architettura a maschera: fondo trasparente, colore/gradiente liberi."""
import sys, json; sys.path.insert(0, 'src')
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, binary_dilation
from levels import level_paths

P = json.load(open('src/best_params.json'))

def light_levels(img_path='src/src_dust.webp'):
    g = np.array(Image.open(img_path).convert('L')).astype(float)/255
    F = gaussian_filter(g, P['pre_sigma'])
    N = P['levels']
    out = []
    for i in range(1, N):
        d = level_paths(F, i/N, min_area=P['min_area'], eps=P['eps'], prec=1)
        if d: out.append(((i+0.5)/N, d))
    return out

def glow_levels(mask_path='src/dust_shape_mask.png', img_path='src/src_dust.webp'):
    g = np.array(Image.open(img_path).convert('L')).astype(float)/255
    shape = np.array(Image.open(mask_path).convert('L')).astype(float)/255 > 0.5
    outside = ~binary_dilation(shape, iterations=1)
    F = gaussian_filter(np.where(outside, g, 0.0), P['pre_sigma'])
    N = P['glow_levels']; out = []
    for i in range(1, N+1):
        t = P['glow_max']*i/(N+1)
        d = level_paths(F, t, min_area=P['glow_min_area'], eps=P['eps']*1.4, prec=1)
        if d: out.append((t + P['glow_max']/(2*(N+1)), d))
    return out

def gray(v):
    gm = P['speck_mean']
    v = float(np.clip(v, 0, 1))
    if gm > 0: v = (v - gm)/(1.0 - gm)
    c = int(round(float(np.clip(v, 0, 1))*255))
    return f'#{c:02x}{c:02x}{c:02x}'

def dust_filter(fid, invert=False, animated=True):
    gi = round(0.5 - P['grain_slope']*0.5, 4)
    si = round(-P['speck_slope']*P['speck_thr'], 4)
    sfx = 'Inv' if invert else ''
    anim = ''
    if animated and not invert:
        anim = '''
      <animate xlink:href="#agoraGrainNoise" attributeName="seed" values="7;19;31;43;55;67;79;91;7"
               dur="1.1s" calcMode="discrete" repeatCount="indefinite" id="agoraBoil"/>
      <animate xlink:href="#agoraGrainShift" attributeName="dx" values="0;46;0" dur="26s" repeatCount="indefinite" id="agoraDriftX"/>
      <animate xlink:href="#agoraGrainShift" attributeName="dy" values="0;-34;0" dur="37s" repeatCount="indefinite" id="agoraDriftY"/>
      <animate xlink:href="#agoraDisplace" attributeName="scale" values="0;3.2;0" dur="17s" repeatCount="indefinite" id="agoraSwirl"/>
      <animate xlink:href="#agoraFlowNoise" attributeName="baseFrequency" values="0.006;0.0085;0.006" dur="23s" repeatCount="indefinite" id="agoraFlow"/>'''
    inv = ''
    if invert:
        inv = '''
      <feComponentTransfer in="toned" result="inverted">
        <feFuncR type="table" tableValues="1 0"/><feFuncG type="table" tableValues="1 0"/><feFuncB type="table" tableValues="1 0"/>
      </feComponentTransfer>
      <feComposite in="inverted" in2="surface" operator="in"/>'''
    else:
        inv = '''
      <feComposite in="toned" in2="surface" operator="in"/>'''
    return f'''<filter id="{fid}" x="-20%" y="-20%" width="140%" height="140%" color-interpolation-filters="sRGB">
      <feTurbulence id="agoraGrainNoise{sfx}" type="fractalNoise" baseFrequency="{P['grain_freq']}" numOctaves="{P['grain_oct']}" seed="{P['grain_seed']}" result="noiseGrain"/>
      <feOffset id="agoraGrainShift{sfx}" in="noiseGrain" dx="0" dy="0" result="noiseGrainMoved"/>
      <feColorMatrix in="noiseGrainMoved" type="matrix" result="grain"
        values="{P['grain_slope']} 0 0 0 {gi} {P['grain_slope']} 0 0 0 {gi} {P['grain_slope']} 0 0 0 {gi} 0 0 0 0 1"/>
      <feTurbulence id="agoraSpeckNoise{sfx}" type="fractalNoise" baseFrequency="{P['speck_freq']}" numOctaves="1" seed="{P['speck_seed']}" result="noiseSpeck"/>
      <feColorMatrix in="noiseSpeck" type="matrix" result="speckMono"
        values="1 0 0 0 0  1 0 0 0 0  1 0 0 0 0  0 0 0 0 1"/>
      <feComponentTransfer in="speckMono" result="speck">
        <feFuncR type="linear" slope="{P['speck_slope']}" intercept="{si}"/>
        <feFuncG type="linear" slope="{P['speck_slope']}" intercept="{si}"/>
        <feFuncB type="linear" slope="{P['speck_slope']}" intercept="{si}"/>
        <feFuncA type="table" tableValues="1 1"/>
      </feComponentTransfer>
      <feTurbulence id="agoraFlowNoise{sfx}" type="fractalNoise" baseFrequency="{P['warp_freq']}" numOctaves="2" seed="{P['warp_seed']}" result="noiseFlow"/>
      <feDisplacementMap id="agoraDisplace{sfx}" in="SourceGraphic" in2="noiseFlow" scale="{P['warp_scale']}"
                         xChannelSelector="R" yChannelSelector="G" result="surface"/>
      <feBlend in="grain" in2="surface" mode="overlay" result="dusted"/>
      <feBlend in="speck" in2="dusted" mode="screen" result="dustedSpecks"/>
      <feComponentTransfer in="dustedSpecks" result="toned">
        <feFuncR id="agoraTone{sfx}R" type="linear" slope="1" intercept="0"/>
        <feFuncG type="linear" slope="1" intercept="0"/>
        <feFuncB type="linear" slope="1" intercept="0"/>
      </feComponentTransfer>{inv}{anim}
    </filter>'''

def emit(shape_d, levels, glows, animated=True, ink='#ffffff', bg='transparent',
         mask='light', title='Agorà — logo dust'):
    lv = "\n        ".join(f'<path fill="{gray(t)}" d="{d}"/>' for t, d in levels)
    gw = "\n        ".join(f'<path fill="{gray(t)}" d="{d}"/>' for t, d in glows)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     viewBox="0 0 1254 1254" width="1254" height="1254" id="agoraDustLogo"
     role="img" aria-labelledby="agoraTitle agoraDesc">
  <title id="agoraTitle">{title}</title>
  <desc id="agoraDesc">Logo Agorà con polvere procedurale. Il disegno è una maschera:
  il colore si cambia con --ink (tinta piatta o url di un gradiente), il fondo con --bg
  (di default trasparente), e si passa da chiaro-su-scuro a scuro-su-chiaro con --mask.</desc>

  <style>
    #agoraDustLogo {{
      --ink: #ffffff;                 /* tinta o gradiente del logo: es. url(#agoraGradient) */
      --bg: transparent;              /* fondo: transparent, #000, #fff, url(#...)           */
      --mask: url(#agoraMaskLight);   /* url(#agoraMaskDark) = logo scuro su fondo chiaro    */
      --glow: 1;                      /* 0..1.5 alone esterno                                */
      --dust: 1;                      /* 0 = superficie pulita, 1 = polvere piena            */
      /* colori del gradiente pronto all'uso */
      --c1: #ff8a3d; --c2: #ff2e63; --c3: #4d5bff;
    }}
    #agoraBg   {{ fill: var(--bg); }}
    #agoraInk  {{ fill: var(--ink); mask: var(--mask); }}
    #agoraGlowLayer {{ opacity: var(--glow); }}
    #agoraDustyLight, #agoraDustyDark {{ opacity: var(--dust); }}
    @media (prefers-reduced-motion: reduce) {{
      #agoraBoil, #agoraDriftX, #agoraDriftY, #agoraSwirl, #agoraFlow {{ display: none; }}
    }}
  </style>

  <defs>
    <linearGradient id="agoraGradient" x1="0" y1="1" x2="1" y2="0">
      <stop offset="0"   stop-color="var(--c1)"/>
      <stop offset="0.5" stop-color="var(--c2)"/>
      <stop offset="1"   stop-color="var(--c3)"/>
    </linearGradient>

    <clipPath id="agoraClip"><path d="{shape_d}"/></clipPath>

    <filter id="agoraSoften" x="-15%" y="-15%" width="130%" height="130%" color-interpolation-filters="sRGB">
      <feGaussianBlur stdDeviation="{P['post_sigma']}"/>
    </filter>
    <filter id="agoraBloom" x="-25%" y="-25%" width="150%" height="150%" color-interpolation-filters="sRGB">
      <feGaussianBlur stdDeviation="{P['glow_sigma']}"/>
    </filter>

    {dust_filter('agoraDustFx', invert=False, animated=animated)}
    {dust_filter('agoraDustFxInv', invert=True, animated=False)}

    <!-- campo luminoso vettoriale: è il "disegno" del logo, usato come maschera -->
    <g id="agoraField" clip-path="url(#agoraClip)" filter="url(#agoraSoften)">
      <path fill="#000" d="{shape_d}"/>
      {lv}
    </g>
    <g id="agoraGlowField" filter="url(#agoraBloom)">
      {gw}
    </g>

    <mask id="agoraMaskLight" maskUnits="userSpaceOnUse" x="-40" y="-40" width="1334" height="1334">
      <g id="agoraDustyLight" filter="url(#agoraDustFx)">
        <g id="agoraGlowLayer"><use xlink:href="#agoraGlowField"/></g>
        <use xlink:href="#agoraField"/>
      </g>
    </mask>

    <mask id="agoraMaskDark" maskUnits="userSpaceOnUse" x="-40" y="-40" width="1334" height="1334">
      <g id="agoraDustyDark" clip-path="url(#agoraClip)" filter="url(#agoraDustFxInv)">
        <use xlink:href="#agoraField"/>
      </g>
    </mask>
  </defs>

  <rect id="agoraBg" width="1254" height="1254"/>
  <rect id="agoraInk" width="1254" height="1254"/>
</svg>
'''

if __name__ == '__main__':
    shape_d = open('src/d_dust_shape2.txt').read()
    lv, gw = light_levels(), glow_levels()
    open('agora-logo-dust.svg','w').write(emit(shape_d, lv, gw, animated=True))
    open('agora-logo-dust-static.svg','w').write(emit(shape_d, lv, gw, animated=False))
    inv = emit(shape_d, lv, gw, animated=False, title='Agorà — logo dust (inverso)')
    inv = inv.replace('--ink: #ffffff;', '--ink: #0b0b0c;').replace('--mask: url(#agoraMaskLight);', '--mask: url(#agoraMaskDark);')
    open('agora-logo-dust-inverted.svg','w').write(inv)
    print('ok')
