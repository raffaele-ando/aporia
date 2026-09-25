"""Raccoglie tutte le versioni dell'intro fatte finora (dallo storico git) in versioni/,
per il selettore della home. Le versioni video usano versioni/video.html#vN."""
import pathlib, subprocess, json
root = pathlib.Path(__file__).resolve().parent.parent
out = root/'versioni'; out.mkdir(exist_ok=True)
CANVAS = [  # (numero, commit, file nel commit)
    (1, '60b1ede', 'index.html'), (2, 'f97f745', 'index.html'), (3, 'fdc43d8', 'index.html'),
    (4, 'a15ac9d', 'index.html'), (5, '17dafcd', 'index.html'), (6, 'c1e365f', 'index.html'),
    (7, 'dfcc4ba', 'index.html'),
]
for n, c, f in CANVAS:
    html = subprocess.run(['git', 'show', f'{c}:aporia_intro_sito/{f}'], cwd=root, capture_output=True, text=True, check=True).stdout
    (out/f'v{n}.html').write_text(html)
    print(f'v{n}.html', len(html)//1024, 'KB')
