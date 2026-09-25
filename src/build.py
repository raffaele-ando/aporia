"""Costruisce l'apertura del sito Aporia: src/template.html + logo dust (da ../agora_loghi_svg).
Uscite: index.html (pagina completa) e, se si passa un percorso, la versione senza <html>/<head>
usata per l'anteprima pubblicata."""
import sys, re, pathlib
here = pathlib.Path(__file__).resolve().parent
root = here.parent
svg = (root.parent/'agora_loghi_svg'/'agora-logo-dust.svg').read_text()
svg = svg.replace('width="1254" height="1254" id="agoraDustLogo"', 'width="100%" height="100%" id="agoraDustLogo" focusable="false"', 1)
svg = re.sub(r'\s*role="img" aria-labelledby="agoraTitle agoraDesc"', ' aria-hidden="true"', svg, count=1)
body = (here/'template.html').read_text().replace('__LOGO__', svg)
title_end = body.index('</title>') + len('</title>')
head, rest = body[:title_end], body[title_end:]
style_end = rest.index('</style>') + len('</style>')
page = ('<!doctype html>\n<html lang="it">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        + head + rest[:style_end] + '\n</head>\n<body>' + rest[style_end:] + '</body>\n</html>\n')
(root/'index.html').write_text(page)
if len(sys.argv) > 1: pathlib.Path(sys.argv[1]).write_text(body)
print('index.html', len(page)//1024, 'KB')
