"""Costruisce l'apertura del sito Aporia: src/template.html + fotogrammi del logo dust (src/logo_frames.json).
Uscite: index.html (pagina completa) e, se si passa un percorso, la versione senza <html>/<head>
usata per l'anteprima pubblicata."""
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

# pagina principale: il video (src/sim_video.py) e la home
vp = (here/'video_page.html').read_text()
te = vp.index('</title>') + len('</title>'); r2 = vp[te:]; se = r2.index('</style>') + len('</style>')
(root/'index.html').write_text('<!doctype html>\n<html lang="it">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
    + vp[:te] + r2[:se] + '\n</head>\n<body>' + r2[se:] + '</body>\n</html>\n')
if len(sys.argv) > 2: pathlib.Path(sys.argv[2]).write_text(vp)
print('index.html', len(vp)//1024, 'KB + video in assets/')
