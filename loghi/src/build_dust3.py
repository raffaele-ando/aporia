import sys; sys.path.insert(0,'work')
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from levels import level_paths

_cache = {}

def glow_defs(P):
    key = ('glow', P['pre_sigma'], P['glow_levels'], P['glow_max'], P['eps'], P['glow_min_area'])
    if key in _cache: return _cache[key]
    g = np.array(Image.open('src/src_dust.webp').convert('L')).astype(float)/255
    shape = np.array(Image.open('src/dust_shape_mask.png').convert('L')).astype(float)/255 > 0.5
    from scipy.ndimage import binary_dilation
    outside = ~binary_dilation(shape, iterations=1)
    F = gaussian_filter(np.where(outside, g, 0.0), P['pre_sigma'])
    N = P['glow_levels']; paths = []
    for i in range(1, N+1):
        t = P['glow_max']*i/(N+1)
        d = level_paths(F, t, min_area=P['glow_min_area'], eps=P['eps']*1.4, prec=1)
        if d: paths.append((t*(N+1-0.5)/(N+1) if False else t + P['glow_max']/(2*(N+1)), d))
    _cache[key] = paths
    return paths

def level_defs(P):
    key = (P['pre_sigma'], P['levels'], P['eps'], P['min_area'])
    if key in _cache: return _cache[key]
    g = np.array(Image.open('src/src_dust.webp').convert('L')).astype(float)/255
    F = gaussian_filter(g, P['pre_sigma'])
    N = P['levels']
    paths = []
    for i in range(1, N):
        d = level_paths(F, i/N, min_area=P['min_area'], eps=P['eps'], prec=1)
        if d: paths.append(((i+0.5)/N, d))
    _cache[key] = paths
    return paths

def make_svg(P, shape_d, levels=None, animate=True, ids=True):
    if levels is None: levels = level_defs(P)
    gm = P['speck_mean']
    def gray(v):
        v = float(np.clip((np.clip(v,0,1)-0.5)*P['contrast'] + 0.5 + P['brightness'], 0, 1))
        v = (v - gm)/(1.0 - gm) if gm > 0 else v
        v = float(np.clip(v, 0, 1))
        c = int(round(v*255)); return f'#{c:02x}{c:02x}{c:02x}'
    lv = "\n        ".join(f'<path fill="{gray(t)}" d="{d}"/>' for t, d in levels)
    gw = "\n        ".join(f'<path fill="{gray(t)}" d="{d}"/>' for t, d in glow_defs(P))
    gi  = round(0.5 - P['grain_slope']*0.5, 4)
    si = round(-P['speck_slope']*P['speck_thr'], 4)
    mi  = round(0.5 - P['mottle_slope']*0.5, 4)
    anim_grain = anim_warp = ''
    if animate:
        anim_grain = (f'<animate attributeName="seed" dur="{P["anim_dur"]}s" '
                      f'values="{P["grain_seed"]};{P["grain_seed"]+40}" repeatCount="indefinite"/>')
        anim_warp = (f'<animate attributeName="baseFrequency" dur="{P["anim_dur"]*3}s" '
                     f'values="{P["warp_freq"]};{P["warp_freq"]*1.3};{P["warp_freq"]}" repeatCount="indefinite"/>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1254 1254" width="1254" height="1254">
  <defs>
    <clipPath id="aporiaClip"><path d="{shape_d}"/></clipPath>
    <filter id="soften" x="-15%" y="-15%" width="130%" height="130%" color-interpolation-filters="sRGB">
      <feGaussianBlur stdDeviation="{P['post_sigma']}"/>
    </filter>
    <filter id="bloom" x="-25%" y="-25%" width="150%" height="150%" color-interpolation-filters="sRGB">
      <feGaussianBlur stdDeviation="{P['glow_sigma']}"/>
    </filter>
    <filter id="dust" x="-5%" y="-5%" width="110%" height="110%" color-interpolation-filters="sRGB">
      <feTurbulence id="dustGrain" type="fractalNoise" baseFrequency="{P['grain_freq']}" numOctaves="{P['grain_oct']}" seed="{P['grain_seed']}" result="n1">{anim_grain}</feTurbulence>
      <feTurbulence id="dustMottle" type="fractalNoise" baseFrequency="{P['mottle_freq']}" numOctaves="{P['mottle_oct']}" seed="{P['mottle_seed']}" result="n2"/>
      <feTurbulence id="dustSpeck" type="fractalNoise" baseFrequency="{P['speck_freq']}" numOctaves="1" seed="{P['speck_seed']}" result="n4"/>
      <feTurbulence id="dustWarp" type="fractalNoise" baseFrequency="{P['warp_freq']}" numOctaves="2" seed="{P['warp_seed']}" result="n3">{anim_warp}</feTurbulence>
      <feColorMatrix in="n1" type="matrix" result="grain"
        values="{P['grain_slope']} 0 0 0 {gi} {P['grain_slope']} 0 0 0 {gi} {P['grain_slope']} 0 0 0 {gi} 0 0 0 0 1"/>
      <feColorMatrix in="n2" type="matrix" result="mottle"
        values="{P['mottle_slope']} 0 0 0 {mi} {P['mottle_slope']} 0 0 0 {mi} {P['mottle_slope']} 0 0 0 {mi} 0 0 0 0 1"/>
      <feDisplacementMap id="dustDrift" in="SourceGraphic" in2="n3" scale="{P['warp_scale']}" xChannelSelector="R" yChannelSelector="G" result="warped"/>
      <feComponentTransfer in="n4" result="speckA">
        <feFuncR type="linear" slope="{P['speck_slope']}" intercept="{si}"/><feFuncG type="linear" slope="{P['speck_slope']}" intercept="{si}"/>
        <feFuncB type="linear" slope="{P['speck_slope']}" intercept="{si}"/><feFuncA type="table" tableValues="1 1"/>
      </feComponentTransfer>
      <feBlend in="grain" in2="warped" mode="overlay" result="b1"/>
      <feBlend in="mottle" in2="b1" mode="soft-light" result="b2"/>
      <feBlend in="speckA" in2="b2" mode="screen" result="b3"/>
      <feComposite in="b3" in2="warped" operator="in"/>
    </filter>
  </defs>
  <rect width="1254" height="1254" fill="#000"/>
  <g filter="url(#dust)">
    <g id="aporiaShaded">
      <g clip-path="url(#aporiaClip)" filter="url(#soften)">
        <path fill="#000" d="{shape_d}"/>
        {lv}
      </g>
    </g>
    <g id="aporiaGlow" filter="url(#bloom)" opacity="{P['glow_opacity']}">
        {gw}
    </g>
    <use href="#aporiaShaded"/>
  </g>
</svg>
'''

DEFAULT = dict(pre_sigma=1.5, post_sigma=2.0, levels=20, eps=2.2, min_area=150,
               contrast=1.0, brightness=0.0, glow_sigma=3.0, glow_opacity=1.0, glow_levels=5, glow_max=0.75, glow_min_area=120,
               grain_freq=0.45, grain_oct=1, grain_seed=7, grain_slope=2.0,
               mottle_freq=0.03, mottle_oct=3, mottle_seed=11, mottle_slope=1.6,
               warp_freq=0.006, warp_seed=5, warp_scale=0.0,
               speck_freq=0.7, speck_seed=23, speck_thr=0.545, speck_slope=3.2, speck_mean=0.0,
               add_grain=0.0, anim_dur=9)
