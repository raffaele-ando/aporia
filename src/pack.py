"""Rigenera il pacchetto pronto in export/ (video, anteprime e export/pacchetto.json per il sito).

  python src/pack.py

Per un colore singolo basta src/export.py; questo script rifà tutti i file che il sito offre da scaricare.
"""
import json, pathlib, subprocess, sys

root = pathlib.Path(__file__).resolve().parent.parent
out = root/'export'
GRAD = '#ff8a3d,#ff2e63,#4d5bff'
JOBS = [  # (argomenti per export.py, nome del colore)
    *[(['--format', f, '--types', 'webm,mp4'], 'Bianco') for f in ('9:16', '4:5', '1:1', '16:9')],
    (['--format', '9:16', '--gradient', GRAD, '--types', 'webm,mp4'], 'Gradiente'),
    (['--format', '16:9', '--gradient', GRAD, '--types', 'webm,mp4'], 'Gradiente'),
    (['--format', '9:16', '--color', '#101014', '--types', 'webm'], 'Nero'),
    (['--format', '9:16', '--color', '#101014', '--bg', '#f2efe9', '--types', 'mp4'], 'Nero'),
    (['--format', '16:9', '--color', '#101014', '--bg', '#f2efe9', '--types', 'mp4'], 'Nero'),
    (['--format', '9:16', '--fps', '30', '--types', 'mov'], 'Bianco'),
    (['--format', '16:9', '--fps', '30', '--types', 'mov'], 'Bianco'),
]

def main():
    for f in out.glob('aporia-intro-*'):
        if f.is_file(): f.unlink()
    for f in (out/'anteprime').glob('*.jpg'): f.unlink()
    colors = {}
    for args, label in JOBS:
        print('export', ' '.join(args), flush=True)
        subprocess.run([sys.executable, str(root/'src'/'export.py'), *args], check=True)
        fmt = args[args.index('--format') + 1].replace(':', 'x')
        col = 'gradiente' if '--gradient' in args else (args[args.index('--color') + 1].lstrip('#') if '--color' in args else 'ffffff')
        colors[(fmt, col)] = label
    files = []
    for f in sorted(out.glob('aporia-intro-*.*')):
        _, _, fmt, col, rest = f.stem.split('-', 4)
        kind = f.suffix[1:]
        files.append(dict(
            file=f.name, format=fmt.replace('x', ':'), color=col, colorName=colors.get((fmt, col), col),
            type=kind, transparent=rest == 'trasparente', background=None if rest == 'trasparente' else rest.removeprefix('su-'),
            fps=30 if kind == 'mov' else 60, mb=round(f.stat().st_size/1e6, 1),
            poster=f'anteprime/{f.stem}.jpg' if (out/'anteprime'/f'{f.stem}.jpg').exists() else None))
    (out/'pacchetto.json').write_text(json.dumps(dict(gradient=GRAD.split(','), files=files), indent=1, ensure_ascii=False))
    print(len(files), 'file in export/, elenco in export/pacchetto.json')

if __name__ == '__main__':
    main()
