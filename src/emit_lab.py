import json, re
svg = open('agora-logo-dust.svg').read()
# strip the XML width/height so it scales in the lab
svg_inline = svg.replace('width="1254" height="1254"', 'width="100%" height="100%" preserveAspectRatio="xMidYMid meet"')

HTML = '''<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Agorà · Dust Lab</title>
<style>
  :root {
    --bg:#08090b; --panel:#101216; --line:#1e222a; --txt:#e8eaee; --dim:#8a92a0; --acc:#d8dee9;
  }
  * { box-sizing:border-box; }
  html,body { margin:0; height:100%; background:var(--bg); color:var(--txt);
    font:13px/1.5 ui-sans-serif,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }
  .wrap { display:grid; grid-template-columns: 330px 1fr; height:100%; }
  @media (max-width: 860px){ .wrap{ grid-template-columns:1fr; grid-template-rows:auto 1fr; } }
  aside { background:var(--panel); border-right:1px solid var(--line); overflow-y:auto; padding:18px 16px 40px; }
  h1 { font-size:14px; letter-spacing:.14em; text-transform:uppercase; margin:0 0 4px; font-weight:600; }
  .sub { color:var(--dim); font-size:11.5px; margin:0 0 18px; }
  fieldset { border:0; border-top:1px solid var(--line); margin:0 0 14px; padding:14px 0 0; }
  legend { font-size:10.5px; letter-spacing:.16em; text-transform:uppercase; color:var(--dim); padding:0; }
  .row { display:grid; grid-template-columns: 1fr 52px; gap:8px; align-items:center; margin:9px 0; }
  .row label { font-size:12px; color:var(--acc); }
  .row output { font-variant-numeric:tabular-nums; font-size:11.5px; color:var(--dim); text-align:right; }
  input[type=range] { grid-column:1 / -1; width:100%; accent-color:#fff; height:18px; }
  .chk { display:flex; align-items:center; gap:8px; margin:7px 0; font-size:12px; }
  .btns { display:flex; gap:8px; flex-wrap:wrap; margin-top:12px; }
  button { background:#1a1e25; color:var(--txt); border:1px solid var(--line); border-radius:7px;
    padding:8px 12px; font:inherit; font-size:12px; cursor:pointer; }
  button:hover { background:#222833; }
  button.primary { background:#e8eaee; color:#0b0d10; border-color:#e8eaee; font-weight:600; }
  main { display:grid; place-items:center; padding:24px; overflow:auto; background:
    repeating-conic-gradient(#0c0d10 0% 25%, #0a0b0e 0% 50%) 50% / 26px 26px; }
  .stage { width:min(86vh, 100%); aspect-ratio:1; box-shadow:0 30px 90px rgba(0,0,0,.6); }
  .stage svg { display:block; width:100%; height:100%; }
  input[type=color]{ width:100%; height:30px; background:none; border:1px solid var(--line); border-radius:6px; }
  .hint { color:var(--dim); font-size:11px; margin-top:6px; }
</style>
</head>
<body>
<div class="wrap">
  <aside>
    <h1>Agorà · Dust Lab</h1>
    <p class="sub">Controlli dal vivo di ogni parametro della polvere. Le modifiche agiscono sul vero SVG: esportalo quando ti piace.</p>

    <fieldset><legend>Grana</legend>
      <div class="row"><label for="gf">Dimensione grano</label><output id="gf_v"></output>
        <input type="range" id="gf" min="0.05" max="1.2" step="0.005"></div>
      <div class="row"><label for="go">Ottave (ricchezza)</label><output id="go_v"></output>
        <input type="range" id="go" min="1" max="5" step="1"></div>
      <div class="row"><label for="gs">Intensità grana</label><output id="gs_v"></output>
        <input type="range" id="gs" min="0" max="4" step="0.01"></div>
      <div class="row"><label for="gsd">Seme (pattern)</label><output id="gsd_v"></output>
        <input type="range" id="gsd" min="1" max="120" step="1"></div>
    </fieldset>

    <fieldset><legend>Granelli sparsi</legend>
      <div class="row"><label for="sf">Dimensione granello</label><output id="sf_v"></output>
        <input type="range" id="sf" min="0.1" max="1.5" step="0.01"></div>
      <div class="row"><label for="ss">Densità</label><output id="ss_v"></output>
        <input type="range" id="ss" min="0" max="10" step="0.05"></div>
      <div class="row"><label for="st">Soglia</label><output id="st_v"></output>
        <input type="range" id="st" min="0.3" max="0.95" step="0.005"></div>
    </fieldset>

    <fieldset><legend>Movimento / turbolenza</legend>
      <div class="row"><label for="dsc">Deformazione</label><output id="dsc_v"></output>
        <input type="range" id="dsc" min="0" max="40" step="0.2"></div>
      <div class="row"><label for="ff">Scala del flusso</label><output id="ff_v"></output>
        <input type="range" id="ff" min="0.001" max="0.05" step="0.0005"></div>
      <div class="row"><label for="ox">Scorrimento X</label><output id="ox_v"></output>
        <input type="range" id="ox" min="-120" max="120" step="1"></div>
      <div class="row"><label for="oy">Scorrimento Y</label><output id="oy_v"></output>
        <input type="range" id="oy" min="-120" max="120" step="1"></div>
      <div class="chk"><input type="checkbox" id="a_boil" checked><label for="a_boil">Grana viva (boil)</label></div>
      <div class="chk"><input type="checkbox" id="a_drift" checked><label for="a_drift">Deriva lenta</label></div>
      <div class="chk"><input type="checkbox" id="a_swirl" checked><label for="a_swirl">Turbolenza animata</label></div>
      <div class="row"><label for="spd">Velocità animazioni</label><output id="spd_v"></output>
        <input type="range" id="spd" min="0.15" max="4" step="0.05"></div>
    </fieldset>

    <fieldset><legend>Luce e materia</legend>
      <div class="row"><label for="amt">Quantità di polvere</label><output id="amt_v"></output>
        <input type="range" id="amt" min="0" max="1" step="0.01"></div>
      <div class="row"><label for="glo">Alone sui bordi</label><output id="glo_v"></output>
        <input type="range" id="glo" min="0" max="2" step="0.01"></div>
      <div class="row"><label for="gb">Diffusione alone</label><output id="gb_v"></output>
        <input type="range" id="gb" min="0" max="20" step="0.1"></div>
      <div class="row"><label for="sof">Morbidezza superficie</label><output id="sof_v"></output>
        <input type="range" id="sof" min="0" max="12" step="0.1"></div>
      <div class="row"><label for="con">Contrasto</label><output id="con_v"></output>
        <input type="range" id="con" min="0.3" max="2.2" step="0.01"></div>
      <div class="row"><label for="bri">Luminosità</label><output id="bri_v"></output>
        <input type="range" id="bri" min="0.3" max="2" step="0.01"></div>
      <div class="row" style="grid-template-columns:1fr"><label for="bgc">Fondo</label>
        <input type="color" id="bgc" value="#000000"></div>
    </fieldset>

    <div class="btns">
      <button class="primary" id="export">Esporta SVG</button>
      <button id="png">Esporta PNG 2048</button>
      <button id="reset">Ripristina</button>
    </div>
    <p class="hint">L'export contiene esattamente ciò che vedi, animazioni incluse.</p>
  </aside>

  <main><div class="stage" id="stage">
__SVG__
  </div></main>
</div>

<script>
const $ = s => document.querySelector(s);
const svg = $('#agoraDustLogo');
const N = {
  grain:  $('#agoraGrainNoise'),  shift: $('#agoraGrainShift'),
  speck:  $('#agoraSpeckNoise'),  speckT:$('#agoraSpeckNoise').parentNode.querySelector('feComponentTransfer'),
  flow:   $('#agoraFlowNoise'),   disp:  $('#agoraDisplace'),
  bloom:  $('#agoraBloom').querySelector('feGaussianBlur'),
  soften: $('#agoraSoften').querySelector('feGaussianBlur'),
};
const ANIM = { boil:$('#agoraBoil'), driftX:$('#agoraDriftX'), driftY:$('#agoraDriftY'),
               swirl:$('#agoraSwirl'), flow:$('#agoraFlow') };
const BASE_DUR = {}; Object.entries(ANIM).forEach(([k,a]) => { if(a) BASE_DUR[k] = parseFloat(a.getAttribute('dur')); });
const speckFns = [...N.speckT.querySelectorAll('feFuncR,feFuncG,feFuncB')];
const grainMat = svg.querySelector('feColorMatrix[result="grain"]');

const DEF = {
  gf: parseFloat(N.grain.getAttribute('baseFrequency')),
  go: parseInt(N.grain.getAttribute('numOctaves')),
  gs: __GS__, gsd: parseInt(N.grain.getAttribute('seed')),
  sf: parseFloat(N.speck.getAttribute('baseFrequency')),
  ss: parseFloat(speckFns[0].getAttribute('slope')),
  st: __ST__,
  dsc: parseFloat(N.disp.getAttribute('scale')),
  ff: parseFloat(N.flow.getAttribute('baseFrequency')),
  ox: 0, oy: 0, spd: 1, amt: 1, glo: 1,
  gb: parseFloat(N.bloom.getAttribute('stdDeviation')),
  sof: parseFloat(N.soften.getAttribute('stdDeviation')),
  con: 1, bri: 1, bgc: '#000000',
};
const S = {...DEF};

function setGrainSlope(v){
  const i = 0.5 - v*0.5;
  grainMat.setAttribute('values', `${v} 0 0 0 ${i} ${v} 0 0 0 ${i} ${v} 0 0 0 ${i} 0 0 0 0 1`);
}
function setSpeck(slope, thr){
  speckFns.forEach(f => { f.setAttribute('slope', slope); f.setAttribute('intercept', (-slope*thr).toFixed(4)); });
}
function apply(){
  N.grain.setAttribute('baseFrequency', S.gf);
  N.grain.setAttribute('numOctaves', S.go);
  N.grain.setAttribute('seed', S.gsd);
  setGrainSlope(S.gs);
  N.speck.setAttribute('baseFrequency', S.sf);
  setSpeck(S.ss, S.st);
  N.disp.setAttribute('scale', S.dsc);
  N.flow.setAttribute('baseFrequency', S.ff);
  N.shift.setAttribute('dx', S.ox); N.shift.setAttribute('dy', S.oy);
  N.bloom.setAttribute('stdDeviation', S.gb);
  N.soften.setAttribute('stdDeviation', S.sof);
  svg.style.setProperty('--dust-amount', S.amt);
  svg.style.setProperty('--dust-glow', S.glo);
  svg.style.setProperty('--dust-contrast', S.con);
  svg.style.setProperty('--dust-brightness', S.bri);
  svg.style.setProperty('--dust-bg', S.bgc);
  // animation speed + enable flags
  const on = { boil:$('#a_boil').checked, driftX:$('#a_drift').checked, driftY:$('#a_drift').checked,
               swirl:$('#a_swirl').checked, flow:$('#a_swirl').checked };
  Object.entries(ANIM).forEach(([k,a]) => {
    if (!a) return;
    a.setAttribute('dur', (BASE_DUR[k]/S.spd).toFixed(3)+'s');
    if (on[k]) { a.beginElement?.(); a.removeAttribute('display'); }
    else { a.setAttribute('display','none'); a.endElement?.(); }
  });
  for (const k in S) { const o = document.getElementById(k+'_v'); if (o) o.value = (typeof S[k]==='number') ? (+S[k]).toFixed(k==='ff'?4:2) : S[k]; }
}
for (const k of Object.keys(DEF)) {
  const el = document.getElementById(k); if (!el) continue;
  if (el.type === 'color') { el.value = DEF[k]; el.addEventListener('input', e => { S[k]=e.target.value; apply(); }); }
  else { el.value = DEF[k]; el.addEventListener('input', e => { S[k] = parseFloat(e.target.value); apply(); }); }
}
['a_boil','a_drift','a_swirl'].forEach(id => $('#'+id).addEventListener('change', apply));
$('#reset').addEventListener('click', () => {
  Object.assign(S, DEF);
  for (const k of Object.keys(DEF)) { const el = document.getElementById(k); if (el) el.value = DEF[k]; }
  ['a_boil','a_drift','a_swirl'].forEach(id => $('#'+id).checked = true);
  apply();
});
function currentSVG(){
  const c = svg.cloneNode(true);
  c.setAttribute('width','1254'); c.setAttribute('height','1254');
  c.style.cssText = svg.style.cssText;
  return '<?xml version="1.0" encoding="UTF-8"?>\\n' + new XMLSerializer().serializeToString(c);
}
function download(name, blob){
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name;
  a.click(); setTimeout(()=>URL.revokeObjectURL(a.href), 4000);
}
$('#export').addEventListener('click', () => download('agora-logo-dust-custom.svg',
  new Blob([currentSVG()], {type:'image/svg+xml'})));
$('#png').addEventListener('click', () => {
  const size = 2048;
  const blob = new Blob([currentSVG()], {type:'image/svg+xml'});
  const url = URL.createObjectURL(blob); const img = new Image();
  img.onload = () => {
    const cv = document.createElement('canvas'); cv.width = cv.height = size;
    const ctx = cv.getContext('2d'); ctx.drawImage(img, 0, 0, size, size);
    cv.toBlob(b => download('agora-logo-dust.png', b), 'image/png');
    URL.revokeObjectURL(url);
  };
  img.src = url;
});
apply();
</script>
</body>
</html>
'''
import json
P = json.load(open('src/best_params.json'))
out = HTML.replace('__SVG__', svg_inline).replace('__GS__', str(P['grain_slope'])).replace('__ST__', str(P['speck_thr']))
open('agora-dust-lab.html','w').write(out)
print('lab written', len(out)//1024, 'KB')
