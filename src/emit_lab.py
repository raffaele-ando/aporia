import json, sys
sys.path.insert(0, 'src')
from emit_v4 import P4
svg = open('agora-logo-dust.svg').read()
svg_inline = svg.replace('width="1254" height="1254"', 'width="100%" height="100%" preserveAspectRatio="xMidYMid meet"', 1)
P = P4

HTML = r'''<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Agorà · Dust Lab</title>
<style>
  :root { --bg:#08090b; --panel:#101216; --line:#1e222a; --txt:#e8eaee; --dim:#8a92a0; --acc:#d8dee9; }
  * { box-sizing:border-box; }
  html,body { margin:0; height:100%; background:var(--bg); color:var(--txt);
    font:13px/1.5 ui-sans-serif,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }
  .wrap { display:grid; grid-template-columns: 340px 1fr; height:100%; }
  @media (max-width: 900px){ .wrap{ grid-template-columns:1fr; grid-template-rows:auto 1fr; } }
  aside { background:var(--panel); border-right:1px solid var(--line); overflow-y:auto; padding:18px 16px 44px; }
  h1 { font-size:14px; letter-spacing:.14em; text-transform:uppercase; margin:0 0 4px; font-weight:600; }
  .sub { color:var(--dim); font-size:11.5px; margin:0 0 16px; }
  fieldset { border:0; border-top:1px solid var(--line); margin:0 0 14px; padding:13px 0 0; }
  legend { font-size:10.5px; letter-spacing:.16em; text-transform:uppercase; color:var(--dim); padding:0; }
  .row { display:grid; grid-template-columns: 1fr 56px; gap:8px; align-items:center; margin:9px 0; }
  .row label { font-size:12px; color:var(--acc); }
  .row output { font-variant-numeric:tabular-nums; font-size:11.5px; color:var(--dim); text-align:right; }
  input[type=range] { grid-column:1 / -1; width:100%; accent-color:#fff; height:18px; }
  .chk { display:flex; align-items:center; gap:8px; margin:7px 0; font-size:12px; }
  .swatches { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin:8px 0; }
  .swatches input[type=color]{ width:100%; height:32px; background:none; border:1px solid var(--line); border-radius:6px; padding:2px; }
  .seg { display:flex; gap:6px; margin:8px 0 4px; flex-wrap:wrap; }
  .seg button { flex:1 1 auto; }
  button { background:#1a1e25; color:var(--txt); border:1px solid var(--line); border-radius:7px;
    padding:8px 11px; font:inherit; font-size:12px; cursor:pointer; }
  button:hover { background:#222833; } button.on { background:#e8eaee; color:#0b0d10; border-color:#e8eaee; font-weight:600; }
  button.primary { background:#e8eaee; color:#0b0d10; border-color:#e8eaee; font-weight:600; }
  .btns { display:flex; gap:8px; flex-wrap:wrap; margin-top:12px; }
  main { display:grid; place-items:center; padding:24px; overflow:auto; }
  .stage { width:min(86vh,100%); aspect-ratio:1; }
  .stage svg { display:block; width:100%; height:100%; }
  .hint { color:var(--dim); font-size:11px; margin-top:8px; }
  #stage.checker { background:repeating-conic-gradient(#3a3d44 0% 25%, #2b2e34 0% 50%) 50% / 28px 28px; }
</style>
</head>
<body>
<div class="wrap">
  <aside>
    <h1>Agorà · Dust Lab</h1>
    <p class="sub">Il logo è una maschera: colore, gradiente, fondo e polarità si cambiano al volo. Esporta quando ti piace.</p>

    <fieldset><legend>Colore</legend>
      <div class="seg">
        <button id="p_solid" class="on">Tinta piatta</button>
        <button id="p_grad">Gradiente</button>
      </div>
      <div class="row" style="grid-template-columns:1fr" id="solidRow"><label for="inkc">Colore logo</label>
        <input type="color" id="inkc" value="#ffffff" style="width:100%;height:32px;border:1px solid var(--line);border-radius:6px;background:none"></div>
      <div id="gradRow" hidden>
        <div class="swatches">
          <input type="color" id="c1" value="#ff8a3d"><input type="color" id="c2" value="#ff2e63"><input type="color" id="c3" value="#4d5bff">
        </div>
        <div class="row"><label for="gang">Angolo gradiente</label><output id="gang_v"></output>
          <input type="range" id="gang" min="0" max="360" step="1"></div>
      </div>
      <div class="seg">
        <button id="m_light" class="on">Chiaro su scuro</button>
        <button id="m_dark">Scuro su chiaro</button>
      </div>
      <div class="row" style="grid-template-columns:1fr"><label for="bgc">Fondo</label>
        <input type="color" id="bgc" value="#000000" style="width:100%;height:32px;border:1px solid var(--line);border-radius:6px;background:none"></div>
      <div class="chk"><input type="checkbox" id="bgnone"><label for="bgnone">Fondo trasparente</label></div>
    </fieldset>

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

    <fieldset><legend>Polvere trascinata</legend>
      <div class="row"><label for="tk">Intensità delle scie</label><output id="tk_v"></output>
        <input type="range" id="tk" min="0" max="4" step="0.01"></div>
      <div class="row"><label for="sw">Trascinamento della grana</label><output id="sw_v"></output>
        <input type="range" id="sw" min="0" max="80" step="0.5"></div>
      <div class="chk"><input type="checkbox" id="a_stream" checked><label for="a_stream">Scie che scorrono</label></div>
    </fieldset>

    <fieldset><legend>Granelli sparsi</legend>
      <div class="row"><label for="sf">Dimensione granello</label><output id="sf_v"></output>
        <input type="range" id="sf" min="0.1" max="1.5" step="0.01"></div>
      <div class="row"><label for="ss">Densità</label><output id="ss_v"></output>
        <input type="range" id="ss" min="0" max="10" step="0.05"></div>
      <div class="row"><label for="st">Soglia</label><output id="st_v"></output>
        <input type="range" id="st" min="0.3" max="0.95" step="0.005"></div>
      <div class="row"><label for="hl">Dispersione fuori dalla luce</label><output id="hl_v"></output>
        <input type="range" id="hl" min="0" max="30" step="0.1"></div>
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

    <fieldset><legend>Luce</legend>
      <div class="row"><label for="amt">Quantità di polvere</label><output id="amt_v"></output>
        <input type="range" id="amt" min="0" max="1" step="0.01"></div>
      <div class="row"><label for="glo">Alone sui bordi</label><output id="glo_v"></output>
        <input type="range" id="glo" min="0" max="2" step="0.01"></div>
      <div class="row"><label for="gb">Diffusione alone</label><output id="gb_v"></output>
        <input type="range" id="gb" min="0" max="20" step="0.1"></div>
      <div class="row"><label for="sof">Morbidezza superficie</label><output id="sof_v"></output>
        <input type="range" id="sof" min="0" max="12" step="0.1"></div>
      <div class="row"><label for="ton">Contrasto tonale</label><output id="ton_v"></output>
        <input type="range" id="ton" min="0.3" max="2.5" step="0.01"></div>
      <div class="row"><label for="lev">Esposizione</label><output id="lev_v"></output>
        <input type="range" id="lev" min="-0.4" max="0.4" step="0.005"></div>
    </fieldset>

    <div class="btns">
      <button class="primary" id="export">Esporta SVG</button>
      <button id="png">Esporta PNG 2048</button>
      <button id="reset">Ripristina</button>
    </div>
    <p class="hint">L'SVG esportato contiene esattamente ciò che vedi (colori, gradiente, animazioni).</p>
  </aside>
  <main><div class="stage" id="stage">
__SVG__
  </div></main>
</div>
<script>
const $ = s => document.querySelector(s);
const svg = $('#agoraDustLogo');
const N = {
  grain: $('#agoraGrainNoise'), shift: $('#agoraGrainShift'), speck: $('#agoraSpeckNoise'),
  flow: $('#agoraFlowNoise'), disp: $('#agoraDisplace'),
  bloom: $('#agoraBloom').querySelector('feGaussianBlur'),
  soften: $('#agoraSoften').querySelector('feGaussianBlur'),
  grad: $('#agoraGradient'), halo: $('#agoraHalo'), sweep: $('#agoraSweep'),
};
const speckFns = [...svg.querySelectorAll('#agoraDustFx feComponentTransfer feFuncR, #agoraDustFx feComponentTransfer feFuncG, #agoraDustFx feComponentTransfer feFuncB')]
  .filter(f => f.getAttribute('type') === 'linear' && f.parentNode.getAttribute('result') === 'speck');
const toneFns = [...svg.querySelectorAll('#agoraTone > *')];
const grainMat = svg.querySelector('#agoraDustFx feColorMatrix[result="grain"]');
const streakMat = svg.querySelector('#agoraDustFx feColorMatrix[result="streak"]');
const ANIM = { boil:$('#agoraBoil'), driftX:$('#agoraDriftX'), driftY:$('#agoraDriftY'), stream:$('#agoraStream'), swirl:$('#agoraSwirl'), flow:$('#agoraFlow') };
const BASE_DUR = {}; Object.entries(ANIM).forEach(([k,a]) => { if (a) BASE_DUR[k] = parseFloat(a.getAttribute('dur')); });

const DEF = {
  gf: parseFloat(N.grain.getAttribute('baseFrequency')), go: parseInt(N.grain.getAttribute('numOctaves')),
  gs: __GS__, gsd: parseInt(N.grain.getAttribute('seed')), tk: __TK__, sw: __SW__, hl: __HL__,
  sf: parseFloat(N.speck.getAttribute('baseFrequency')), ss: __SS__, st: __ST__,
  dsc: parseFloat(N.disp.getAttribute('scale')), ff: parseFloat(N.flow.getAttribute('baseFrequency')),
  ox: 0, oy: 0, spd: 1, amt: 1, glo: 1,
  gb: parseFloat(N.bloom.getAttribute('stdDeviation')), sof: parseFloat(N.soften.getAttribute('stdDeviation')),
  ton: 1, lev: 0, gang: 45,
};
const S = {...DEF};
let paintMode = 'solid', polarity = 'light';
let ink = '#ffffff', bg = '#000000', bgOff = false, cols = ['#ff8a3d','#ff2e63','#4d5bff'];

function slopeMat(m, v){ const i = 0.5 - v*0.5;
  m.setAttribute('values', `${v} 0 0 0 ${i} ${v} 0 0 0 ${i} ${v} 0 0 0 ${i} 0 0 0 0 1`); }
function setGrainSlope(v){ slopeMat(grainMat, v); }
function setSpeck(slope, thr){ speckFns.forEach(f => { f.setAttribute('slope', slope); f.setAttribute('intercept', (-slope*thr).toFixed(4)); }); }
function setTone(slope, shift){ toneFns.forEach(f => { f.setAttribute('slope', slope); f.setAttribute('intercept', (shift + (1-slope)/2).toFixed(4)); }); }
function gradAngle(deg){
  const r = deg*Math.PI/180, c = Math.cos(r), s = Math.sin(r);
  N.grad.setAttribute('x1', (0.5 - c/2).toFixed(4)); N.grad.setAttribute('y1', (0.5 + s/2).toFixed(4));
  N.grad.setAttribute('x2', (0.5 + c/2).toFixed(4)); N.grad.setAttribute('y2', (0.5 - s/2).toFixed(4));
}
function apply(){
  N.grain.setAttribute('baseFrequency', S.gf); N.grain.setAttribute('numOctaves', S.go);
  N.grain.setAttribute('seed', S.gsd); setGrainSlope(S.gs);
  N.speck.setAttribute('baseFrequency', S.sf); setSpeck(S.ss, S.st);
  slopeMat(streakMat, S.tk); N.halo.setAttribute('stdDeviation', S.hl); N.sweep.setAttribute('scale', S.sw);
  if (ANIM.swirl) ANIM.swirl.setAttribute('values', `${S.sw};${(S.sw*1.6).toFixed(2)};${S.sw}`);
  N.disp.setAttribute('scale', S.dsc); N.flow.setAttribute('baseFrequency', S.ff);
  N.shift.setAttribute('dx', S.ox); N.shift.setAttribute('dy', S.oy);
  N.bloom.setAttribute('stdDeviation', S.gb); N.soften.setAttribute('stdDeviation', S.sof);
  setTone(S.ton, S.lev); gradAngle(S.gang);
  svg.style.setProperty('--dust', S.amt); svg.style.setProperty('--glow', S.glo);
  svg.style.setProperty('--ink', paintMode === 'grad' ? 'url(#agoraGradient)' : ink);
  svg.style.setProperty('--bg', bgOff ? 'transparent' : bg);
  svg.style.setProperty('--mask', polarity === 'dark' ? 'url(#agoraMaskDark)' : 'url(#agoraMaskLight)');
  cols.forEach((c,i) => svg.style.setProperty('--c'+(i+1), c));
  $('#stage').classList.toggle('checker', bgOff);
  const on = { boil:$('#a_boil').checked, driftX:$('#a_drift').checked, driftY:$('#a_drift').checked, stream:$('#a_stream').checked,
               swirl:$('#a_swirl').checked, flow:$('#a_swirl').checked };
  Object.entries(ANIM).forEach(([k,a]) => { if(!a) return;
    a.setAttribute('dur', (BASE_DUR[k]/S.spd).toFixed(3)+'s');
    if (on[k]) { a.removeAttribute('display'); a.beginElement?.(); } else { a.setAttribute('display','none'); a.endElement?.(); }
  });
  for (const k in S) { const o = document.getElementById(k+'_v'); if (o) o.value = (+S[k]).toFixed(k==='ff'?4:2); }
}
for (const k of Object.keys(DEF)) { const el = document.getElementById(k); if (!el) continue;
  el.value = DEF[k]; el.addEventListener('input', e => { S[k] = parseFloat(e.target.value); apply(); }); }
['a_boil','a_drift','a_stream','a_swirl'].forEach(id => $('#'+id).addEventListener('change', apply));
$('#inkc').addEventListener('input', e => { ink = e.target.value; apply(); });
$('#bgc').addEventListener('input', e => { bg = e.target.value; bgOff = false; $('#bgnone').checked = false; apply(); });
$('#bgnone').addEventListener('change', e => { bgOff = e.target.checked; apply(); });
['c1','c2','c3'].forEach((id,i) => $('#'+id).addEventListener('input', e => { cols[i] = e.target.value; apply(); }));
$('#p_solid').addEventListener('click', () => { paintMode='solid'; $('#p_solid').classList.add('on'); $('#p_grad').classList.remove('on');
  $('#solidRow').hidden=false; $('#gradRow').hidden=true; apply(); });
$('#p_grad').addEventListener('click', () => { paintMode='grad'; $('#p_grad').classList.add('on'); $('#p_solid').classList.remove('on');
  $('#solidRow').hidden=true; $('#gradRow').hidden=false; apply(); });
$('#m_light').addEventListener('click', () => { polarity='light'; $('#m_light').classList.add('on'); $('#m_dark').classList.remove('on');
  if (ink === '#101014') { ink = '#ffffff'; $('#inkc').value = ink; } if (!bgOff && bg === '#f2efe9') { bg='#000000'; $('#bgc').value=bg; } apply(); });
$('#m_dark').addEventListener('click', () => { polarity='dark'; $('#m_dark').classList.add('on'); $('#m_light').classList.remove('on');
  if (ink === '#ffffff') { ink = '#101014'; $('#inkc').value = ink; } if (!bgOff && bg === '#000000') { bg='#f2efe9'; $('#bgc').value=bg; } apply(); });
$('#reset').addEventListener('click', () => { Object.assign(S, DEF);
  for (const k of Object.keys(DEF)) { const el=document.getElementById(k); if (el) el.value = DEF[k]; }
  ['a_boil','a_drift','a_stream','a_swirl'].forEach(id => $('#'+id).checked = true);
  paintMode='solid'; polarity='light'; ink='#ffffff'; bg='#000000'; bgOff=false; cols=['#ff8a3d','#ff2e63','#4d5bff'];
  $('#inkc').value=ink; $('#bgc').value=bg; $('#bgnone').checked=false;
  $('#p_solid').classList.add('on'); $('#p_grad').classList.remove('on'); $('#solidRow').hidden=false; $('#gradRow').hidden=true;
  $('#m_light').classList.add('on'); $('#m_dark').classList.remove('on');
  ['c1','c2','c3'].forEach((id,i)=> $('#'+id).value = cols[i]);
  apply(); });
function currentSVG(){
  const c = svg.cloneNode(true);
  c.setAttribute('width','1254'); c.setAttribute('height','1254'); c.removeAttribute('preserveAspectRatio');
  c.style.cssText = svg.style.cssText;
  return '<?xml version="1.0" encoding="UTF-8"?>\n' + new XMLSerializer().serializeToString(c);
}
function download(name, blob){ const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=name; a.click();
  setTimeout(()=>URL.revokeObjectURL(a.href),4000); }
$('#export').addEventListener('click', () => download('agora-logo-dust-custom.svg', new Blob([currentSVG()],{type:'image/svg+xml'})));
$('#png').addEventListener('click', () => { const size=2048; const url=URL.createObjectURL(new Blob([currentSVG()],{type:'image/svg+xml'}));
  const img=new Image(); img.onload=()=>{ const cv=document.createElement('canvas'); cv.width=cv.height=size;
    cv.getContext('2d').drawImage(img,0,0,size,size); cv.toBlob(b=>download('agora-logo-dust.png',b),'image/png'); URL.revokeObjectURL(url); };
  img.src=url; });
apply();
</script>
</body></html>
'''
out = (HTML.replace('__SVG__', svg_inline)
           .replace('__GS__', str(P['grain_slope']))
           .replace('__SS__', str(P['speck_slope']))
           .replace('__ST__', str(P['speck_thr']))
           .replace('__TK__', str(P['streak_slope']))
           .replace('__SW__', str(P['sweep']))
           .replace('__HL__', str(P['halo'])))
open('agora-dust-lab.html','w').write(out)
print('lab', len(out)//1024, 'KB')
