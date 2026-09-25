"""Esporta l'intro (versione 10) nel colore, fondo e formato che vuoi.

La simulazione è salvata come "luce" (src/master/: polvere bianca su nero, 60 fps): la luce
diventa la trasparenza, il colore si sceglie a parte. Nessuna nuova simulazione da rifare.

Esempi:
  python src/export.py                                   # bianco, trasparente, 9:16, tutti i tipi
  python src/export.py --color "#ff4d2e" --format 1:1
  python src/export.py --gradient "#ff8a3d,#ff2e63,#4d5bff" --angle 45 --format 16:9
  python src/export.py --color "#101014" --bg "#f2efe9" --types mp4
  python src/export.py --types mov --fps 30              # ProRes 4444 con trasparenza (programmi di montaggio)

Tipi:
  webm  trasparente (VP9 con alpha): browser, Canva, OBS, siti web. Leggero.
  mov   trasparente (ProRes 4444): Premiere, Final Cut, DaVinci, After Effects, Keynote, CapCut desktop. Pesante (30 fps: 30-45 MB).
  mp4   su fondo pieno (--bg, di default nero): qualsiasi app. Con fondo nero e modalità di
        fusione "Scherma/Screen" (CapCut: Sovrapposizione > Fusione > Schiarisci/Scherma) il nero sparisce.
  png   sequenza di PNG trasparenti in una cartella (universale).
"""
import argparse, pathlib, subprocess, math, sys, shutil
import numpy as np

root = pathlib.Path(__file__).resolve().parent.parent
ff = __import__('imageio_ffmpeg').get_ffmpeg_exe()
MASTER = {'portrait': root/'src'/'master'/'luce-verticale.mp4', 'landscape': root/'src'/'master'/'luce-orizzontale.mp4'}
# ritagli (x, y, larghezza, altezza) nei master 1080×1920 / 1920×1080, centrati sul logo
FORMATS = {
    '9:16': ('portrait', (0, 0, 1080, 1920)),
    '4:5':  ('portrait', (0, 333, 1080, 1350)),
    '1:1':  ('portrait', (0, 468, 1080, 1080)),
    '16:9': ('landscape', (0, 0, 1920, 1080)),
}
DUST_WHITE = 241.0            # la luce piena nel master (polvere 244,241,235)
# centro e grandezza del logo nei master (per stendere il gradiente sul logo, non su tutto il quadro)
LOGO = {'portrait': (527, 1008, 520), 'landscape': (949, 548, 440)}

def hexrgb(h):
    h = h.strip().lstrip('#'); return np.array([int(h[i:i+2], 16) for i in (0, 2, 4)], np.float32)

def ink_layer(args, w, h, orient, cx, cy):
    """colore della polvere per ogni pixel (h, w, 3), 0..255"""
    if args.gradient:
        lx, ly, size = LOGO[orient]; lx -= cx; ly -= cy
        cols = [hexrgb(c) for c in args.gradient.split(',')]
        a = math.radians(args.angle); dx, dy = math.cos(a), -math.sin(a)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        t = ((xx - lx)*dx + (yy - ly)*dy)/size + 0.5
        t = np.clip(t, 0, 1)*(len(cols) - 1)
        i = np.minimum(t.astype(int), len(cols) - 2); f = (t - i)[..., None]
        C = np.stack(cols)
        return C[i]*(1 - f) + C[i + 1]*f
    return np.broadcast_to(hexrgb(args.color), (h, w, 3)).astype(np.float32)

def save_posters(out, encs, ink, a, bgc, w, h):
    """un fotogramma come anteprima per il sito (i trasparenti sopra una scacchiera)"""
    from PIL import Image
    d = out/'anteprime'; d.mkdir(exist_ok=True)
    tw = 360 if w <= h else 640; th = round(h*tw/w)
    for k, (_, path) in encs.items():
        if k == 'mp4':
            img = ink*a + bgc*(1 - a)
        else:
            dark = float(np.mean(ink)) > 128        # polvere chiara: scacchiera scura, e viceversa
            c1, c2 = ((46, 44, 40), (31, 29, 26)) if dark else ((242, 239, 233), (220, 216, 208))
            yy, xx = np.mgrid[0:h, 0:w]
            chk = np.where((((xx//40) + (yy//40)) % 2)[..., None] == 0, np.array(c1, np.float32), np.array(c2, np.float32))
            img = ink*a + chk*(1 - a)
        im = Image.fromarray(img.clip(0, 255).astype(np.uint8)).resize((tw, th), Image.LANCZOS)
        im.save(d/(path.stem + '.jpg'), quality=82)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--color', default='#ffffff', help='colore della polvere')
    ap.add_argument('--gradient', help='gradiente: 2 o più colori separati da virgola')
    ap.add_argument('--angle', type=float, default=45, help='angolo del gradiente in gradi')
    ap.add_argument('--bg', default='transparent', help='fondo: transparent o un colore (solo per mp4)')
    ap.add_argument('--format', default='9:16', choices=list(FORMATS))
    ap.add_argument('--fps', type=int, default=60, choices=[60, 30])
    ap.add_argument('--types', default='webm,mp4', help='webm,mov,mp4,png')
    ap.add_argument('--name', default=None, help='nome dei file (senza estensione)')
    ap.add_argument('--out', default=str(root/'export'))
    ap.add_argument('--poster', type=float, default=2.4, help="secondo del fotogramma usato come anteprima (export/anteprime/), -1 per nessuna")
    args = ap.parse_args()
    types = [t.strip() for t in args.types.split(',') if t.strip()]
    orient, (cx, cy, w, h) = FORMATS[args.format]
    out = pathlib.Path(args.out); out.mkdir(parents=True, exist_ok=True)
    tag = args.name or 'aporia-intro-' + args.format.replace(':', 'x') + '-' + (
        'gradiente' if args.gradient else args.color.lstrip('#').lower())
    ink = ink_layer(args, w, h, orient, cx, cy)
    bg = None if args.bg == 'transparent' else hexrgb(args.bg)
    encs = {}
    def enc(kind, pix_in, codec_args, path):
        cmd = [ff, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', pix_in, '-s', f'{w}x{h}', '-r', str(args.fps), '-i', '-'] + codec_args + [str(path)]
        encs[kind] = (subprocess.Popen(cmd, stdin=subprocess.PIPE), path)
    if 'webm' in types:
        enc('webm', 'rgba', ['-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p', '-b:v', '0', '-crf', '34', '-row-mt', '1', '-auto-alt-ref', '0', '-an'], out/f'{tag}-trasparente.webm')
    if 'mov' in types:
        enc('mov', 'rgba', ['-c:v', 'prores_ks', '-profile:v', '4444', '-alpha_bits', '8', '-vendor', 'apl0', '-pix_fmt', 'yuva444p10le', '-an'], out/f'{tag}-trasparente.mov')
    if 'mp4' in types:
        name = 'su-' + ('nero' if bg is None or tuple(bg) == (0, 0, 0) else args.bg.lstrip('#').lower())
        enc('mp4', 'rgb24', ['-c:v', 'libx264', '-preset', 'slow', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an'], out/f'{tag}-{name}.mp4')
    pngdir = None
    if 'png' in types:
        pngdir = out/f'{tag}-png'; shutil.rmtree(pngdir, ignore_errors=True); pngdir.mkdir()
    # decodifica del master (solo la luce), un fotogramma alla volta
    W0, H0 = (1080, 1920) if orient == 'portrait' else (1920, 1080)
    dec = subprocess.Popen([ff, '-loglevel', 'error', '-i', str(MASTER[orient]), '-vf', f'fps={args.fps},crop={w}:{h}:{cx}:{cy}',
                            '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], stdout=subprocess.PIPE)
    n = 0; bgc = np.zeros(3, np.float32) if bg is None else bg
    while True:
        buf = dec.stdout.read(w*h)
        if len(buf) < w*h: break
        L = np.frombuffer(buf, np.uint8).reshape(h, w).astype(np.float32)
        a = np.clip((L - 3)/(DUST_WHITE - 3), 0, 1)[..., None]          # trasparenza = luce
        if 'webm' in encs or 'mov' in encs or pngdir:
            rgba = np.concatenate([ink, a*255], -1).clip(0, 255).astype(np.uint8)
            for k in ('webm', 'mov'):
                if k in encs: encs[k][0].stdin.write(rgba.tobytes())
            if pngdir:
                from PIL import Image
                Image.fromarray(rgba, 'RGBA').save(pngdir/f'{n:04d}.png', optimize=False, compress_level=6)
        if 'mp4' in encs:
            rgb = (ink*a + bgc*(1 - a)).clip(0, 255).astype(np.uint8)
            encs['mp4'][0].stdin.write(rgb.tobytes())
        if n == round(args.poster*args.fps):
            save_posters(out, encs, ink, a, bgc, w, h)
        n += 1
    for p, path in encs.values():
        p.stdin.close(); p.wait()
        print(f'{path.name}: {path.stat().st_size/1e6:.1f} MB')
    if pngdir: print(f'{pngdir.name}/: {n} PNG')
    print(f'{n} fotogrammi, {n/args.fps:.2f} s, {w}×{h}, {args.fps} fps')

if __name__ == '__main__':
    main()
