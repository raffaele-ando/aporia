"""Costruisce intro-canvas.html, la versione precedente calcolata dal vivo nel browser:
src/template.html + fotogrammi del logo dust (src/morph.json). Se si passa un percorso, scrive anche
la versione senza <html>/<head>."""
import sys, re, pathlib
here = pathlib.Path(__file__).resolve().parent
root = here.parent
# immagini e granelli della polvere (src/render_logo.py poi src/prep_morph.py)
logo = (here/'morph.json').read_text()
body = (here/'template.html').read_text().replace('__LOGO_JSON__', logo)
title_end = body.index('</title>') + len('</title>')
head, rest = body[:title_end], body[title_end:]
style_end = rest.index('</style>') + len('</style>')
page = ('<!doctype html>\n<html lang="it">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        + head + rest[:style_end] + '\n</head>\n<body>' + rest[style_end:] + '</body>\n</html>\n')
(root/'intro-canvas.html').write_text(page)
if len(sys.argv) > 1: pathlib.Path(sys.argv[1]).write_text(body)
print('intro-canvas.html', len(page)//1024, 'KB')

# le altre pagine del sito (index.html, versioni.html, laboratorio.html, download.html) si modificano direttamente
