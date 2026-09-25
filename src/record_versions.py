"""Registra le versioni v1–v7 (pagine animate dal vivo) come video, fotogramma per fotogramma,
con l'orologio del browser fermo e fatto avanzare a mano: ogni fotogramma è quello che il browser
avrebbe mostrato a 60 fps. Così nel selettore tutte le versioni si riproducono come video.
Uso: python src/record_versions.py 1 2 3 ... [--orient portrait|landscape]"""
import sys, os, subprocess, pathlib, time
from playwright.sync_api import sync_playwright
root = pathlib.Path(__file__).resolve().parent.parent
ff = __import__('imageio_ffmpeg').get_ffmpeg_exe()
CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
FPS = 60
args = [a for a in sys.argv[1:] if not a.startswith('--')]
orients = [sys.argv[sys.argv.index('--orient') + 1]] if '--orient' in sys.argv else ['portrait', 'landscape']
args = [a for a in args if a not in ('portrait', 'landscape')]
SIZE = {'portrait': (540, 960), 'landscape': (960, 540)}      # ×2 = 1080×1920 / 1920×1080
media = root/'versioni'/'media'; media.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox'])
    for v in args:
        for o in orients:
            w, h = SIZE[o]; t0 = time.time()
            ctx = b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=2)
            pg = ctx.new_page()
            pg.clock.install(time=1_000_000); pg.clock.pause_at(1_000_000)
            pg.goto('file://' + str(root/'versioni'/f'v{v}.html'))
            # la home "Aporia" la mostra il selettore: nella registrazione resta solo l'animazione
            pg.add_style_tag(content='#home{visibility:hidden!important}')
            pg.wait_for_timeout(400)
            raw = pathlib.Path('/tmp/claude-0/sp')/f'rec-v{v}-{o}.mp4'
            enc = subprocess.Popen([ff, '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', str(FPS), '-c:v', 'mjpeg', '-i', '-',
                                    '-c:v', 'libx264', '-preset', 'fast', '-crf', '14', '-pix_fmt', 'yuv420p', str(raw)], stdin=subprocess.PIPE)
            n = 0; tail = 0; ms = 0
            while n < FPS*13:
                step = round((n + 1)*1000/FPS) - ms; ms += step      # millisecondi interi (16, 17, 17, …)
                pg.clock.run_for(step)
                enc.stdin.write(pg.screenshot(type='jpeg', quality=93)); n += 1
                if pg.evaluate("(() => { const i = document.getElementById('intro'); return !i || i.classList.contains('gone') || getComputedStyle(i).opacity === '0'; })()"):
                    tail += 1
                    if tail > 6: break
            enc.stdin.close(); enc.wait(); ctx.close()
            out = media/f'v{v}-{o}'
            subprocess.run([ff, '-y', '-loglevel', 'error', '-i', str(raw), '-c:v', 'libx264', '-preset', 'veryslow', '-crf', '29', '-pix_fmt', 'yuv420p',
                            '-profile:v', 'high', '-level', '4.2', '-movflags', '+faststart', '-an', f'{out}.mp4'], check=True)
            subprocess.run([ff, '-y', '-loglevel', 'error', '-i', str(raw), '-c:v', 'libvpx-vp9', '-b:v', '0', '-crf', '50', '-row-mt', '1',
                            '-pix_fmt', 'yuv420p', '-an', f'{out}.webm'], check=True)
            print(f'v{v} {o}: {n} fotogrammi ({n/FPS:.1f} s), {pathlib.Path(f"{out}.mp4").stat().st_size//1024} KB mp4, {time.time()-t0:.0f}s', flush=True)
    b.close()
