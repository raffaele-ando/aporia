import sys, base64
from playwright.sync_api import sync_playwright
CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'

def render_svg_file(path, out_png, width, height, bg='#ffffff'):
    svg = open(path).read()
    html = f'''<!doctype html><html><head><style>html,body{{margin:0;padding:0;background:{bg};overflow:hidden}}
    svg{{display:block;width:{width}px;height:{height}px}}</style></head>
    <body>{svg}</body></html>'''
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox','--disable-gpu','--force-device-scale-factor=1'])
        pg = b.new_page(viewport={'width':width,'height':height}, device_scale_factor=1)
        pg.set_content(html)
        pg.wait_for_timeout(350)
        pg.screenshot(path=out_png, clip={'x':0,'y':0,'width':width,'height':height})
        b.close()

def render_html(html, out_png, width, height):
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROME, args=['--no-sandbox','--disable-gpu','--force-device-scale-factor=1'])
        pg = b.new_page(viewport={'width':width,'height':height}, device_scale_factor=1)
        pg.set_content(html); pg.wait_for_timeout(400)
        pg.screenshot(path=out_png, clip={'x':0,'y':0,'width':width,'height':height})
        b.close()

if __name__ == '__main__':
    render_svg_file(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
