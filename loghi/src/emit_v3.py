"""Logo dust v3: luce estesa oltre i bordi, bordi interni sfumati,
grana spazzata da un campo di flusso, granelli a grumi con dispersione naturale."""
import sys, json, pickle; sys.path.insert(0, 'src')
import numpy as np

P3 = dict(
    soften=2.6,            # morbidezza del campo luminoso
    feather_soft=4.5,      # sfumatura dei bordi del fiume (in alto)
    feather_hard=1.1,      # sfumatura minima dei bordi interni (in basso)
    glow_sigma=2.0,
    flow_freq=0.011, flow_oct=2, flow_seed=5,
    grain_fx=0.50, grain_fy=0.34, grain_oct=3, grain_seed=7, grain_slope=1.55, sweep=14,
    speck_fx=0.34, speck_fy=0.21, speck_oct=3, speck_seed=23, speck_slope=5.0, speck_thr=0.60,
    speck_sweep=22, halo=9.0, speck_gain=1.0,
    level_comp=0.0,
)

def gray(v, comp):
    v = float(np.clip(v, 0, 1))
    if comp > 0: v = (v - comp)/(1 - comp)
    c = int(round(float(np.clip(v, 0, 1))*255)); return f'#{c:02x}{c:02x}{c:02x}'

def dust_filter(fid, P, invert=False, animated=True):
    sfx = 'Inv' if invert else ''
    gs = P['grain_slope']; gi = round(0.5 - gs*0.5, 4)
    ss = P['speck_slope']; si = round(-ss*P['speck_thr'], 4)
    anim = ''
    if animated and not invert:
        anim = '''
      <animate xlink:href="#aporiaGrainNoise" attributeName="seed" values="7;19;31;43;55;67;79;91;7"
               dur="1.1s" calcMode="discrete" repeatCount="indefinite" id="aporiaBoil"/>
      <animate xlink:href="#aporiaGrainShift" attributeName="dx" values="0;46;0" dur="26s" repeatCount="indefinite" id="aporiaDriftX"/>
      <animate xlink:href="#aporiaGrainShift" attributeName="dy" values="0;-34;0" dur="37s" repeatCount="indefinite" id="aporiaDriftY"/>
      <animate xlink:href="#aporiaSweep" attributeName="scale" values="%(sw)s;%(sw2)s;%(sw)s" dur="17s" repeatCount="indefinite" id="aporiaSwirl"/>
      <animate xlink:href="#aporiaFlowNoise" attributeName="baseFrequency" values="%(ff)s;%(ff2)s;%(ff)s" dur="23s" repeatCount="indefinite" id="aporiaFlow"/>''' % dict(
            sw=P['sweep'], sw2=round(P['sweep']*1.6, 2), ff=P['flow_freq'], ff2=round(P['flow_freq']*1.35, 5))
    tail = '''
      <feComposite in="speckW" in2="base" operator="over" result="final"/>'''
    if invert:
        tail = '''
      <feComposite in="speckW" in2="base" operator="over" result="final0"/>
      <feComponentTransfer in="final0" result="inverted">
        <feFuncR type="table" tableValues="1 0"/><feFuncG type="table" tableValues="1 0"/><feFuncB type="table" tableValues="1 0"/>
      </feComponentTransfer>
      <feComposite in="inverted" in2="SourceAlpha" operator="in"/>'''
    return f'''<filter id="{fid}" x="-20%" y="-20%" width="140%" height="140%" color-interpolation-filters="sRGB">
      <!-- campo di flusso: guida il movimento della polvere -->
      <feTurbulence id="aporiaFlowNoise{sfx}" type="fractalNoise" baseFrequency="{P['flow_freq']}" numOctaves="{P['flow_oct']}" seed="{P['flow_seed']}" result="flow"/>
      <!-- superficie (deformabile), resa opaca su nero: nella maschera il nero è trasparente,
           e così la grana non lascia aloni grigi dove la luce sfuma -->
      <feFlood flood-color="#000" result="black"/>
      <feComposite in="SourceGraphic" in2="black" operator="over" result="opaque"/>
      <feDisplacementMap id="aporiaDisplace{sfx}" in="opaque" in2="flow" scale="0" xChannelSelector="R" yChannelSelector="G" result="surface"/>
      <!-- grana: rumore spazzato dal flusso -->
      <feTurbulence id="aporiaGrainNoise{sfx}" type="fractalNoise" baseFrequency="{P['grain_fx']} {P['grain_fy']}" numOctaves="{P['grain_oct']}" seed="{P['grain_seed']}" result="g0"/>
      <feOffset id="aporiaGrainShift{sfx}" in="g0" dx="0" dy="0" result="g1"/>
      <feDisplacementMap id="aporiaSweep{sfx}" in="g1" in2="flow" scale="{P['sweep']}" xChannelSelector="R" yChannelSelector="G" result="g2"/>
      <feColorMatrix in="g2" type="matrix" result="grain"
        values="{gs} 0 0 0 {gi} {gs} 0 0 0 {gi} {gs} 0 0 0 {gi} 0 0 0 0 1"/>
      <feBlend in="grain" in2="surface" mode="overlay" result="dusted"/>
      <feComponentTransfer in="dusted" result="toned">
        <feFuncR type="linear" slope="1" intercept="0"/><feFuncG type="linear" slope="1" intercept="0"/><feFuncB type="linear" slope="1" intercept="0"/>
      </feComponentTransfer>
      <feComposite in="toned" in2="surface" operator="in" result="base"/>
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
      <feComposite in="speckA" in2="halo" operator="in" result="speckLit"/>
      <feFlood flood-color="#fff" result="white"/>
      <feComposite in="white" in2="speckLit" operator="in" result="speckW0"/>
      <feComponentTransfer in="speckW0" result="speckW"><feFuncA type="linear" slope="{P['speck_gain']}" intercept="0"/></feComponentTransfer>{tail}{anim}
    </filter>'''

def emit(shape_d, hull_d, open_d, levels, glows, P=P3, animated=True, title='Aporia — logo dust',
         y_soft_end=760.0, zone_d=None):
    zone = '' if not zone_d else f'''
      <!-- zona morbida (fiume, bandiera): qui decide solo la luce, la sagoma non taglia -->
      <path fill="#fff" filter="url(#aporiaFeatherZone)" d="{zone_d}"/>'''
    lv = "\n        ".join(f'<path fill="{gray(t, P["level_comp"])}" d="{d}"/>' for t, d in levels)
    gw = "\n        ".join(f'<path fill="{gray(t, P["level_comp"])}" d="{d}"/>' for t, d in glows)
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
    @media (prefers-reduced-motion: reduce) {{
      #aporiaBoil, #aporiaDriftX, #aporiaDriftY, #aporiaSwirl, #aporiaFlow {{ display: none; }}
    }}
  </style>
  <defs>
    <linearGradient id="aporiaGradient" x1="0" y1="1" x2="1" y2="0">
      <stop offset="0" stop-color="var(--c1)"/><stop offset="0.5" stop-color="var(--c2)"/><stop offset="1" stop-color="var(--c3)"/>
    </linearGradient>
    <clipPath id="aporiaClip"><path d="{shape_d}"/></clipPath>

    <filter id="aporiaSoften" x="-15%" y="-15%" width="130%" height="130%" color-interpolation-filters="sRGB">
      <feGaussianBlur stdDeviation="{P['soften']}"/>
    </filter>
    <filter id="aporiaBloom" x="-25%" y="-25%" width="150%" height="150%" color-interpolation-filters="sRGB">
      <feGaussianBlur stdDeviation="{P['glow_sigma']}"/>
    </filter>
    <filter id="aporiaFeatherSoft" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="{P['feather_soft']}"/></filter>
    <filter id="aporiaFeatherZone" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="{P.get('feather_zone', 8)}"/></filter>
    <filter id="aporiaFeatherHard" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="{P['feather_hard']}"/></filter>
    <linearGradient id="aporiaSoftFade" gradientUnits="userSpaceOnUse" x1="0" y1="{y_soft_end-140:.1f}" x2="0" y2="{y_soft_end:.1f}">
      <stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#000"/>
    </linearGradient>
    <mask id="aporiaSoftZone" maskUnits="userSpaceOnUse" x="0" y="0" width="1254" height="1254">
      <rect width="1254" height="1254" fill="url(#aporiaSoftFade)"/>
    </mask>

    <!-- sagoma della superficie: bordi esterni netti, bordi del fiume sfumati -->
    <mask id="aporiaSurface" maskUnits="userSpaceOnUse" x="0" y="0" width="1254" height="1254">
      <path fill="#fff" d="{hull_d}"/>
      <g mask="url(#aporiaSoftZone)"><path fill="#000" filter="url(#aporiaFeatherSoft)" d="{open_d}"/></g>
      <path fill="#000" filter="url(#aporiaFeatherHard)" d="{open_d}"/>{zone}
    </mask>

    {dust_filter('aporiaDustFx', P, invert=False, animated=animated)}
    {dust_filter('aporiaDustFxInv', P, invert=True, animated=False)}

    <g id="aporiaField" mask="url(#aporiaSurface)">
      <g filter="url(#aporiaSoften)">
        {lv}
      </g>
    </g>
    <g id="aporiaGlowField" filter="url(#aporiaBloom)">
      {gw}
    </g>

    <mask id="aporiaMaskLight" maskUnits="userSpaceOnUse" x="-40" y="-40" width="1334" height="1334">
      <g id="aporiaDustyLight" filter="url(#aporiaDustFx)">
        <g id="aporiaGlowLayer"><use xlink:href="#aporiaGlowField"/></g>
        <use xlink:href="#aporiaField"/>
      </g>
    </mask>
    <mask id="aporiaMaskDark" maskUnits="userSpaceOnUse" x="-40" y="-40" width="1334" height="1334">
      <g id="aporiaDustyDark" filter="url(#aporiaDustFxInv)">
        <g mask="url(#aporiaSurface)"><rect width="1254" height="1254" fill="#000"/></g>
        <use xlink:href="#aporiaField"/>
      </g>
    </mask>
  </defs>
  <rect id="aporiaBg" width="1254" height="1254"/>
  <rect id="aporiaInk" width="1254" height="1254"/>
</svg>
'''
