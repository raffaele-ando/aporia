// Laboratorio: interfaccia, anteprima dal vivo, salvataggi ed export.
import { DustEngine, SIM_HZ } from './engine.js';
import { build, FORMATS } from './shapes.js';
import { inksForBackground, backgroundsForInk, contrast, contrastLabel } from './colors.js';
import { support, encode, record, Clip } from './exporter.js';

const $ = id => document.getElementById(id);
const fmt = (x, d = 2) => x.toFixed(d).replace('.', ',');
const clone = o => JSON.parse(JSON.stringify(o));
const mobile = matchMedia('(pointer: coarse)').matches || (navigator.hardwareConcurrency || 8) <= 4;

// ---- il progetto: tutto quello che si può regolare ---------------------------------------------
const DEFAULT = {
  v: 1, mode: 'forma', format: '9:16', particles: 0, seed: 1,
  wind: { angle: 0, strength: 1, turb: 1 },
  ink: { mode: 'solid', c: '#f4f1eb', g: ['#ff8a3d', '#ff2e63', '#4d5bff'], angle: 45 },
  bg: 'transparent', bgColor: '#000000', glow: 0.08,
  forma: { shapes: [{ kind: 'aporia-a', hold: 0 }, { kind: 'aporia-logo' }], size: 1, dy: 0, arrive: 1, final: 0.75, morph: 1, exit: true },
  transizione: { dur: 2.4, cover: false, tint: 0.25, grain: 1.7, mid: { kind: 'nessuna', text: 'Aporia' }, span: 'pezzo' },
  export: { fps: 60, res: 1080 },
  harm: 'bg',
};
const PARTS = {
  forma: [[0, 'Automatico'], [150000, '150 mila (telefoni vecchi)'], [400000, '400 mila'], [1000000, '1 milione'], [2000000, '2 milioni'], [4000000, '4 milioni']],
  transizione: [[0, 'Automatico'], [400000, '400 mila (telefoni vecchi)'], [1000000, '1 milione'], [2100000, '2 milioni (un granello per pixel)'], [4000000, '4 milioni'], [8000000, '8 milioni']],
};
const autoParts = mode => mode === 'forma' ? (mobile ? 400000 : 1000000) : (mobile ? 1000000 : 2100000);
const INKS = [['Bianco', '#f4f1eb'], ['Crema', '#ece8e1'], ['Oro', '#d9b56a'], ['Rosso', '#ff4d2e'], ['Blu', '#4d7bff'], ['Nero', '#101014']];
const BGS = [['Trasparente', 'transparent'], ['Nero', '#000000'], ['Notte', '#0d1526'], ['Chiaro', '#f2efe9'], ['Verde chroma', '#00ff00']];
const FONTS = ['Italiana', 'Playfair Display', 'Cormorant Garamond', 'Bodoni Moda', 'DM Serif Display', 'Cinzel', 'Inter', 'Montserrat',
  'Space Grotesk', 'Syne', 'Unbounded', 'Archivo Black', 'Anton', 'Bebas Neue', 'Caveat', 'Pacifico'];
const KINDS = [['aporia-a', 'La A'], ['aporia-logo', 'Il logo'], ['testo', 'Scritta'], ['immagine', 'Immagine']];

function merge(base, over) {
  if (Array.isArray(base) || typeof base !== 'object' || base === null) return over === undefined ? base : over;
  const o = { ...base };
  for (const k in over || {}) o[k] = k in base ? merge(base[k], over[k]) : over[k];
  return o;
}
let P = clone(DEFAULT);
try { const s = localStorage.getItem('aporia-lab'); if (s) P = merge(DEFAULT, JSON.parse(s)); } catch (e) {}
try { if (location.hash.length > 3) { P = merge(DEFAULT, JSON.parse(decodeURIComponent(escape(atob(location.hash.slice(1)))))); history.replaceState(null, '', location.pathname); } } catch (e) {}
const save = () => { try { localStorage.setItem('aporia-lab', JSON.stringify(P)); } catch (e) {} };

// caratteri caricati dall'utente (restano nel progetto come data URL)
const customFonts = new Set();
async function ensureFont(sp) {
  if (!sp || !sp.fontData || customFonts.has(sp.font)) return;
  try { const f = new FontFace(sp.font, `url(${sp.fontData})`); await f.load(); document.fonts.add(f); customFonts.add(sp.font); } catch (e) {}
}

// ---- motore -------------------------------------------------------------------------------------
const cv = $('gl'), stage = $('stage'), hint = $('hint');
let E = null;
try { E = new DustEngine(cv); }
catch (e) { hint.textContent = 'Questo browser non riesce a calcolare la polvere (serve WebGL2 con i float): prova con Chrome, Edge o Safari aggiornati.'; hint.classList.add('err'); }

const clips = { A: null, B: null };
let cfg = null, ready = false, building = 0, playing = true, loop = true, slow = false, t = 0, last = 0, exporting = false;
const say = (msg, err) => { hint.textContent = msg || ''; hint.classList.toggle('err', !!err); };

function projectForBuild() {
  const q = clone(P);
  q.particles = P.particles || autoParts(P.mode);
  q.forma.hold = [q.forma.shapes[0]?.hold || 0, q.forma.shapes[1]?.hold || 0];
  return q;
}
// ricostruisce i granelli solo quando cambia qualcosa che li riguarda; il resto va al volo
let lastKey = '', buildTimer = 0;
function geomKey() {
  const q = projectForBuild();
  return JSON.stringify([q.mode, q.format, q.particles, q.seed, q.wind, q.mode === 'forma' ? q.forma : q.transizione]);
}
function schedule(delay = 180) {
  const k = geomKey(); if (k === lastKey) return;
  clearTimeout(buildTimer); buildTimer = setTimeout(rebuild, delay);
}
async function rebuild() {
  if (!E || exporting) return;
  const k = geomKey(); lastKey = k;
  const my = ++building;
  $('busy').hidden = false;
  try {
    const q = projectForBuild();
    if (q.mode === 'forma') for (const s of q.forma.shapes) await ensureFont(s);
    else await ensureFont(q.transizione.mid);
    const r = await build(q, { onStage: s => { $('busy').textContent = s === 'abbinamento' ? 'Abbino le forme…' : 'Preparo i granelli…'; } });
    if (my !== building) return;
    cfg = r.cfg; E.load(r.cfg, r.data); ready = true;
    t = Math.min(t, cfg.dur); E.advanceTo(0);
    $('scrub').max = cfg.dur;
    $('stats').textContent = `${(r.data.n/1e6).toLocaleString('it-IT', { maximumFractionDigits: 2 })} M granelli`;
    say('');
    updateNotes();
  } catch (e) { console.error(e); say('Qualcosa non va: ' + e.message, true); }
  finally { if (my === building) $('busy').hidden = true; }
}

function look(fps) {
  const bg = P.bg === 'transparent' ? 'transparent' : P.bgColor;
  return { ink: P.ink, bg, glow: P.glow, fps: fps || 60, tint: P.transizione.tint };
}

// tempi delle clip durante la transizione (secondi di ciascuna clip), per "pezzo" e "intere"
function clipTimes(tt, span) {
  const D = cfg.dur, dA = clips.A && clips.A.kind === 'video' ? clips.A.duration : D;
  if (span === 'intere') {
    // tutta A, poi tutta B: la transizione è a cavallo del taglio
    const cut = dA;
    return { engine: Math.min(Math.max(0, tt - (cut - D/2)), D), a: tt, b: tt - cut };
  }
  return { engine: tt, a: Math.max(0, dA - D/2) + tt, b: tt - D/2 };
}

function sizeCanvas() {
  const r = stage.getBoundingClientRect(), dpr = Math.min(window.devicePixelRatio || 1, mobile ? 1.25 : 1.5);
  const [W, H] = FORMATS[P.format];
  const w = Math.max(2, Math.min(W, Math.round(r.width*dpr))), h = Math.max(2, Math.round(w*H/W));
  if (cv.width !== w || cv.height !== h) { cv.width = w; cv.height = h; }
}

function feedClipsPreview(tt) {
  if (!cfg || cfg.mode !== 'transizione' || cfg.cover) return;
  const ct = clipTimes(tt, 'pezzo'), w = Math.min(cv.width, 720), h = Math.round(w*cfg.H/cfg.W);
  const rate = slow ? 0.25 : 1;
  for (const k of ['A', 'B']) {
    const c = clips[k];
    if (!c) { E.setClip(k, null); continue; }
    const f = c.previewFrame(k === 'A' ? ct.a : Math.max(0, ct.b), w, h, playing ? rate : 0);
    if (!playing) c.pause();
    if (f) E.setClip(k, f);
  }
}

function frame(now) {
  requestAnimationFrame(frame);
  const dt = last ? Math.min(0.1, (now - last)/1000) : 0; last = now;
  if (!E || !ready || exporting) return;
  sizeCanvas();
  if (playing) {
    t += dt*(slow ? 0.25 : 1);
    // un dispositivo lento rallenta l'anteprima invece di saltare (l'export è sempre esatto)
    t = Math.min(t, E.t + 8/SIM_HZ);
    if (t > cfg.dur + 0.6) {
      if (loop) { t = 0; } else { t = cfg.dur; setPlaying(false); }
    }
  }
  E.setLook(look());
  feedClipsPreview(t);
  E.advanceTo(Math.min(t, cfg.dur));
  E.render();
  $('scrub').value = Math.min(t, cfg.dur);
  $('time').textContent = `${fmt(Math.min(t, cfg.dur))} / ${fmt(cfg.dur)} s`;
}
requestAnimationFrame(frame);

function setPlaying(v) {
  playing = v; $('play').textContent = v ? '❚❚' : '▶'; $('play').setAttribute('aria-label', v ? 'Pausa' : 'Riproduci');
  if (!v) for (const k in clips) clips[k] && clips[k].pause();
}
$('play').onclick = () => { if (cfg && t >= cfg.dur) t = 0; setPlaying(!playing); };
$('restart').onclick = () => { t = 0; setPlaying(true); };
$('scrub').oninput = e => { t = +e.target.value; setPlaying(false); };
$('loop').onclick = e => { loop = !loop; e.target.setAttribute('aria-pressed', String(loop)); };
$('slow').onclick = e => { slow = !slow; e.target.setAttribute('aria-pressed', String(slow)); };
stage.addEventListener('click', () => { if (cfg && t >= cfg.dur) t = 0; setPlaying(!playing); });

// ---- controlli ---------------------------------------------------------------------------------
function pressed(box, pred) { [...box.querySelectorAll('button')].forEach(b => b.setAttribute('aria-pressed', String(pred(b)))); }
function range(id, get, set, show, rebuildIt = true) {
  const el = $(id), v = $(id + 'V');
  const upd = () => { el.value = get(); if (v) v.textContent = show(get()); };
  el.addEventListener('input', () => { set(+el.value); if (v) v.textContent = show(+el.value); changed(rebuildIt); });
  return upd;
}
const updaters = [];
function changed(rebuildIt = true) { save(); if (rebuildIt) schedule(); refreshColorInfo(); }

// modo
document.querySelector('.tabs').addEventListener('click', e => {
  const b = e.target.closest('button'); if (!b) return;
  P.mode = b.dataset.mode; t = 0; refreshAll(); changed();
});

// forme
function shapeCard(sp, k, n) {
  const d = document.createElement('div'); d.className = 'shape';
  const head = document.createElement('div'); head.className = 'head';
  head.innerHTML = `<b>${n > 1 ? `Forma ${k + 1}${k === n - 1 ? ' · finale' : ''}` : 'Forma'}</b>`;
  const mk = (txt, fn, lab) => { const b = document.createElement('button'); b.type = 'button'; b.textContent = txt; b.setAttribute('aria-label', lab); b.onclick = fn; head.appendChild(b); return b; };
  const S = P.forma.shapes;
  if (k > 0) mk('↑', () => { [S[k - 1], S[k]] = [S[k], S[k - 1]]; renderShapes(); changed(); }, 'Sposta prima');
  if (k < n - 1) mk('↓', () => { [S[k + 1], S[k]] = [S[k], S[k + 1]]; renderShapes(); changed(); }, 'Sposta dopo');
  if (n > 1) mk('✕', () => { S.splice(k, 1); renderShapes(); changed(); }, 'Togli la forma');
  d.appendChild(head);
  const kinds = document.createElement('div'); kinds.className = 'kinds';
  for (const [id, lab] of KINDS) {
    const b = document.createElement('button'); b.type = 'button'; b.textContent = lab; b.setAttribute('aria-pressed', String(sp.kind === id));
    b.onclick = () => { sp.kind = id; if (id === 'testo' && !sp.text) sp.text = 'Aporia'; renderShapes(); changed(); };
    kinds.appendChild(b);
  }
  d.appendChild(kinds);
  const field = (html) => { const f = document.createElement('div'); f.className = 'field'; f.innerHTML = html; d.appendChild(f); return f; };
  const slider = (lab, key, min, max, step, def, show) => {
    const f = field(`<label class="lab">${lab} <span class="v"></span></label><input type="range" min="${min}" max="${max}" step="${step}">`);
    const inp = f.querySelector('input'), v = f.querySelector('.v');
    inp.value = sp[key] ?? def; v.textContent = show(+inp.value);
    inp.oninput = () => { sp[key] = +inp.value; v.textContent = show(sp[key]); changed(); };
  };
  if (sp.kind === 'testo') {
    const f = field(`<label class="lab">Testo (a capo per più righe)</label><textarea rows="2"></textarea>`);
    const ta = f.querySelector('textarea'); ta.value = sp.text || ''; ta.oninput = () => { sp.text = ta.value; changed(); };
    const g = field(`<div class="two"><div class="field"><label class="lab">Carattere</label><select></select></div><div class="field"><label class="lab">Peso</label><select><option value="400">Normale</option><option value="700">Grassetto</option><option value="900">Nero</option></select></div></div>
      <div class="row"><button type="button" class="it">Corsivo</button><label class="chip">Carica un carattere…<input type="file" accept=".ttf,.otf,.woff,.woff2,font/*"></label></div>`);
    const [fs, ws] = g.querySelectorAll('select');
    const fonts = [...FONTS]; if (sp.fontData && !fonts.includes(sp.font)) fonts.unshift(sp.font);
    for (const f of fonts) { const o = document.createElement('option'); o.value = f; o.textContent = f; o.style.fontFamily = `"${f}"`; fs.appendChild(o); }
    fs.value = sp.font || 'Italiana'; ws.value = String(sp.weight || 400);
    fs.onchange = () => { sp.font = fs.value; if (!customFonts.has(fs.value)) delete sp.fontData; changed(); };
    ws.onchange = () => { sp.weight = +ws.value; changed(); };
    const it = g.querySelector('.it'); it.setAttribute('aria-pressed', String(!!sp.italic)); it.onclick = () => { sp.italic = !sp.italic; it.setAttribute('aria-pressed', String(sp.italic)); changed(); };
    g.querySelector('input[type=file]').onchange = async e => {
      const file = e.target.files[0]; if (!file) return;
      if (file.size > 3e6) { say('Il carattere è troppo grande (più di 3 MB).', true); return; }
      const url = await new Promise(r => { const fr = new FileReader(); fr.onload = () => r(fr.result); fr.readAsDataURL(file); });
      sp.font = file.name.replace(/\.[^.]+$/, ''); sp.fontData = url; customFonts.delete(sp.font);
      await ensureFont(sp); renderShapes(); changed();
    };
    slider('Spaziatura delle lettere', 'spacing', -0.1, 0.6, 0.01, 0, v => fmt(v, 2));
    slider('Grana della polvere', 'grain', 0, 1, 0.05, 0.5, v => Math.round(v*100) + '%');
  }
  if (sp.kind === 'immagine') {
    const f = field(`<label class="lab">Immagine <span class="v">${sp.name || 'nessuna'}</span></label><div class="row"><label class="chip grow">Scegli PNG, JPG o SVG…<input type="file" accept="image/*"></label><button type="button" class="inv">Inverti</button></div>
      <p class="note">Un PNG trasparente o un SVG usa la sua forma; una foto usa la luce (con Inverti scegli se diventa polvere il chiaro o lo scuro).</p>`);
    f.querySelector('input').onchange = async e => {
      const file = e.target.files[0]; if (!file) return;
      sp.src = await shrinkImage(file); sp.name = file.name; delete sp.invert; renderShapes(); changed();
    };
    const inv = f.querySelector('.inv'); inv.setAttribute('aria-pressed', String(!!sp.invert));
    inv.onclick = () => { sp.invert = !sp.invert; inv.setAttribute('aria-pressed', String(sp.invert)); changed(); };
    slider('Grana della polvere', 'grain', 0, 1, 0.05, 0.5, v => Math.round(v*100) + '%');
  }
  slider('Grandezza', 'size', 0.3, 2, 0.01, 1, v => Math.round(v*100) + '%');
  const two = document.createElement('div'); two.className = 'two'; d.appendChild(two);
  const mini = (lab, key) => {
    const f = document.createElement('div'); f.className = 'field';
    f.innerHTML = `<label class="lab">${lab} <span class="v"></span></label><input type="range" min="-0.4" max="0.4" step="0.005">`;
    const inp = f.querySelector('input'), v = f.querySelector('.v'); inp.value = sp[key] || 0; v.textContent = Math.round((sp[key] || 0)*100) + '%';
    inp.oninput = () => { sp[key] = +inp.value; v.textContent = Math.round(sp[key]*100) + '%'; changed(); };
    two.appendChild(f);
  };
  mini('← →', 'dx'); mini('↑ ↓', 'dy');
  if (k < n - 1) slider('Tenuta (0 = solo di passaggio)', 'hold', 0, 4, 0.05, 0, v => fmt(v, 2) + ' s');
  return d;
}
function renderShapes() {
  const box = $('shapes'); box.textContent = '';
  const S = P.forma.shapes;
  S.forEach((sp, k) => box.appendChild(shapeCard(sp, k, S.length)));
  $('addShape').hidden = S.length >= 3;
}
$('addShape').onclick = () => { P.forma.shapes.push({ kind: 'testo', text: 'Aporia', font: 'Italiana' }); renderShapes(); changed(); };
async function shrinkImage(file) {
  const url = URL.createObjectURL(file);
  const im = await new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = url; });
  const k = Math.min(1, 1400/Math.max(im.naturalWidth || 1400, im.naturalHeight || 1400));
  const c = document.createElement('canvas'); c.width = Math.round((im.naturalWidth || 1400)*k); c.height = Math.round((im.naturalHeight || 1400)*k);
  c.getContext('2d').drawImage(im, 0, 0, c.width, c.height); URL.revokeObjectURL(url);
  return c.toDataURL('image/png');
}

updaters.push(range('fArrive', () => P.forma.arrive, v => P.forma.arrive = v, v => fmt(v, 2) + '×'));
updaters.push(range('fMorph', () => P.forma.morph, v => P.forma.morph = v, v => fmt(v, 2) + '×'));
updaters.push(range('fFinal', () => P.forma.final, v => P.forma.final = v, v => fmt(v, 2) + ' s'));
updaters.push(range('fSize', () => P.forma.size, v => P.forma.size = v, v => Math.round(v*100) + '%'));
updaters.push(range('fDy', () => P.forma.dy, v => P.forma.dy = v, v => Math.round(v*100) + '%'));
$('fExit').onclick = e => { const b = e.target.closest('button'); if (!b) return; P.forma.exit = b.dataset.v === '1'; refreshAll(); changed(); };

// transizione
async function loadClip(k, file) {
  try {
    say('Carico la clip…');
    const c = await Clip.fromFile(file);
    if (clips[k]) clips[k].dispose();
    clips[k] = c; $(`clip${k}Name`).textContent = c.name + (c.kind === 'video' ? ` · ${fmt(c.duration, 1)} s` : ' · foto');
    if (P.transizione.cover) { P.transizione.cover = false; refreshAll(); changed(); }
    t = 0; say(''); updateNotes();
  } catch (e) { say(e.message, true); }
}
$('clipA').onchange = e => e.target.files[0] && loadClip('A', e.target.files[0]);
$('clipB').onchange = e => e.target.files[0] && loadClip('B', e.target.files[0]);
for (const k of ['A', 'B']) $(`clip${k}x`).onclick = () => { if (clips[k]) clips[k].dispose(); clips[k] = null; E && E.setClip(k, null); $(`clip${k}Name`).textContent = 'nessuna'; $(`clip${k}`).value = ''; updateNotes(); };
$('tCover').onclick = e => { const b = e.target.closest('button'); if (!b) return; P.transizione.cover = b.dataset.v === '1'; refreshAll(); changed(); };
updaters.push(range('tDur', () => P.transizione.dur, v => P.transizione.dur = v, v => fmt(v, 1) + ' s'));
updaters.push(range('tTint', () => P.transizione.tint, v => P.transizione.tint = v, v => Math.round(v*100) + '%', false));
updaters.push(range('tGrain', () => P.transizione.grain, v => P.transizione.grain = v, v => fmt(v, 2) + '×'));
$('tMid').onclick = e => { const b = e.target.closest('button'); if (!b) return; P.transizione.mid.kind = b.dataset.k; refreshAll(); changed(); };
$('tMidText').oninput = e => { P.transizione.mid.text = e.target.value; changed(); };
$('tSpan').onclick = e => { const b = e.target.closest('button'); if (!b) return; P.transizione.span = b.dataset.v; refreshAll(); changed(false); };

// colore
const inkBox = $('inkPresets');
for (const [n, c] of INKS) { const b = document.createElement('button'); b.type = 'button'; b.dataset.c = c; b.innerHTML = `<span class="swatch" style="background:${c}"></span>${n}`; inkBox.appendChild(b); }
{ const b = document.createElement('button'); b.type = 'button'; b.dataset.grad = '1'; b.innerHTML = `<span class="swatch" style="background:linear-gradient(90deg,#ff8a3d,#ff2e63,#4d5bff)"></span>Gradiente`; inkBox.appendChild(b); }
inkBox.onclick = e => {
  const b = e.target.closest('button'); if (!b) return;
  if (b.dataset.grad) { P.ink.mode = 'grad'; P.ink.g = ['#ff8a3d', '#ff2e63', '#4d5bff']; }
  else { P.ink.mode = 'solid'; P.ink.c = b.dataset.c; }
  refreshAll(); changed(false);
};
$('ink').oninput = e => { P.ink.mode = 'solid'; P.ink.c = e.target.value; refreshAll(); changed(false); };
['g0', 'g1', 'g2'].forEach((id, k) => $(id).oninput = e => { P.ink.g[k] = e.target.value; refreshAll(); changed(false); });
$('inkGradBtn').onclick = () => { P.ink.mode = 'grad'; refreshAll(); changed(false); };
$('inkSolidBtn').onclick = () => { P.ink.mode = 'solid'; refreshAll(); changed(false); };
updaters.push(range('gAng', () => P.ink.angle, v => P.ink.angle = v, v => v + '°', false));
const bgBox = $('bgPresets');
for (const [n, c] of BGS) { const b = document.createElement('button'); b.type = 'button'; b.dataset.c = c; b.innerHTML = `<span class="swatch" style="background:${c === 'transparent' ? 'repeating-conic-gradient(#888 0 25%,#444 0 50%) 50%/6px 6px' : c}"></span>${n}`; bgBox.appendChild(b); }
bgBox.onclick = e => { const b = e.target.closest('button'); if (!b) return; if (b.dataset.c === 'transparent') P.bg = 'transparent'; else { P.bg = 'color'; P.bgColor = b.dataset.c; } refreshAll(); changed(false); };
$('bgc').oninput = e => { P.bg = 'color'; P.bgColor = e.target.value; refreshAll(); changed(false); };
updaters.push(range('glow', () => P.glow, v => P.glow = v, v => Math.round(v*100) + '%', false));

// teoria dei colori
$('harmFrom').onclick = e => { const b = e.target.closest('button'); if (!b) return; P.harm = b.dataset.v; refreshAll(); save(); };
const inkMain = () => P.ink.mode === 'solid' ? P.ink.c : P.ink.g[1];
const bgMain = () => P.bg === 'transparent' ? '#000000' : P.bgColor;
function refreshColorInfo() {
  const cr = contrast(inkMain(), bgMain()), lab = contrastLabel(cr);
  $('crNow').innerHTML = `<span class="${cr >= 4.5 ? 'ok' : cr >= 3 ? 'warn' : 'bad'}">${fmt(cr, 1)}:1 · ${lab}</span>${P.bg === 'transparent' ? ' (sul nero)' : ''}`;
  const box = $('harm'); box.textContent = '';
  const fromBg = P.harm !== 'ink';
  const list = fromBg ? inksForBackground(bgMain()) : backgroundsForInk(inkMain());
  $('harmNote').textContent = fromBg
    ? `Fondo ${bgMain()}${P.bg === 'transparent' ? ' (con il fondo trasparente si ragiona sul nero; scegli un fondo per avere consigli su misura)' : ''}: per ogni teoria il colore della polvere che si legge meglio. Tocca un colore per usarlo.`
    : `Polvere ${inkMain()}: per ogni teoria il fondo più compatibile, calmo e leggibile. Tocca un colore per usarlo.`;
  if (list[0] && list[0].note) $('harmNote').textContent += ' ' + list[0].note[0].toUpperCase() + list[0].note.slice(1) + '.';
  const best = list.reduce((a, b) => (b.score > a.score ? b : a));
  for (const h of list) {
    const r = document.createElement('div'); r.className = 'hrow' + (h === best ? ' best' : '');
    const ink = fromBg ? h.main : inkMain(), bg = fromBg ? bgMain() : h.main;
    const cls = h.cr >= 4.5 ? 'ok' : h.cr >= 3 ? 'warn' : 'bad';
    r.innerHTML = `<div class="nm">${h.name}${h === best ? ' <span class="tag">consigliato</span>' : ''}<small>${h.desc}</small></div><div class="sw"></div>
      <div class="cr"><span class="demo" style="color:${ink};background:${bg}">A</span><span class="${cls}">${fmt(h.cr, 1)}:1 ${contrastLabel(h.cr)}</span></div>`;
    const sw = r.querySelector('.sw');
    for (const c of h.colors) {
      const b = document.createElement('button'); b.type = 'button'; b.style.background = c; b.title = c; b.setAttribute('aria-label', `Usa ${c}`);
      if (c === h.main) b.classList.add('main');
      b.onclick = () => { if (fromBg) { P.ink.mode = 'solid'; P.ink.c = c; } else { P.bg = 'color'; P.bgColor = c; } refreshAll(); changed(false); };
      sw.appendChild(b);
    }
    if (fromBg && h.colors.length > 1) {
      const b = document.createElement('button'); b.type = 'button'; b.title = 'Usa come gradiente'; b.setAttribute('aria-label', 'Usa i colori come gradiente');
      const g = h.colors.length === 2 ? [h.colors[0], h.main, h.colors[1]] : h.colors.slice(0, 3);
      b.style.background = `linear-gradient(135deg, ${g.join(',')})`;
      b.onclick = () => { P.ink.mode = 'grad'; P.ink.g = g; refreshAll(); changed(false); };
      sw.appendChild(b);
    }
    box.appendChild(r);
  }
}

// vento
$('windDir').onclick = e => { const b = e.target.closest('button'); if (!b) return; P.wind.angle = +b.dataset.a; refreshAll(); changed(); };
updaters.push(range('wAng', () => P.wind.angle, v => P.wind.angle = v, v => v + '°'));
updaters.push(range('wStr', () => P.wind.strength, v => P.wind.strength = v, v => fmt(v, 2) + '×'));
updaters.push(range('wTurb', () => P.wind.turb, v => P.wind.turb = v, v => fmt(v, 2) + '×'));
updaters.push(range('seed', () => P.seed, v => P.seed = v, v => String(v)));

// formato e qualità
$('formats').onclick = e => { const b = e.target.closest('button'); if (!b) return; P.format = b.dataset.f; refreshAll(); changed(); };
$('parts').onchange = e => { P.particles = +e.target.value; refreshAll(); changed(); };
$('res').onchange = e => { P.export.res = +e.target.value; changed(false); };
$('fps').onchange = e => { P.export.fps = +e.target.value; changed(false); };

function updateNotes() {
  const X = P.transizione;
  $('coverNote').textContent = X.cover
    ? 'Nessuna clip: la polvere entra da un lato, copre tutto lo schermo a metà e se ne va. Nel tuo programma mettila sopra il taglio, centrata sul taglio.'
    : (!clips.A && !clips.B ? 'Carica le clip qui sopra (finché non ci sono, l’anteprima usa il colore della polvere).' : '');
  const D = X.dur;
  $('spanNote').textContent = X.span === 'pezzo'
    ? `Il file dura ${fmt(D, 1)} s: gli ultimi ${fmt(D/2, 1)} s della clip A e i primi ${fmt(D/2, 1)} s della B. Mettilo sopra il taglio, cominciando ${fmt(D/2, 1)} s prima.`
    : 'Il file contiene tutta la clip A e tutta la B, con la transizione sul taglio (senza audio).';
  const bgNote = P.bg === 'transparent' ? 'Con il fondo trasparente l’MP4 esce su nero.' : `MP4 su ${P.bgColor}.`;
  const tr = P.mode === 'transizione' && !X.cover && (clips.A || clips.B);
  $('mp4Sub').textContent = tr ? 'le clip con la transizione · ogni app' : 'su fondo pieno · ogni app';
  $('expNote').textContent = (tr ? 'Con le clip il video è pieno: il fondo non conta. ' : bgNote) + (SUP && !SUP.webcodecs ? ' Questo browser non ha WebCodecs: il video si registra in tempo reale, più lento e meno nitido; meglio Chrome o Edge.' : '');
}

function refreshAll() {
  for (const b of document.querySelectorAll('.tabs button')) b.setAttribute('aria-pressed', String(b.dataset.mode === P.mode));
  for (const d of document.querySelectorAll('details[data-for]')) d.hidden = d.dataset.for !== P.mode;
  pressed($('fExit'), b => (b.dataset.v === '1') === P.forma.exit);
  pressed($('tCover'), b => (b.dataset.v === '1') === !!P.transizione.cover);
  pressed($('tMid'), b => b.dataset.k === (P.transizione.mid.kind || 'nessuna'));
  $('tMidText').hidden = P.transizione.mid.kind !== 'testo'; $('tMidText').value = P.transizione.mid.text || '';
  pressed($('tSpan'), b => b.dataset.v === P.transizione.span);
  pressed(inkBox, b => b.dataset.grad ? P.ink.mode === 'grad' && P.ink.g.join() === '#ff8a3d,#ff2e63,#4d5bff' : P.ink.mode === 'solid' && b.dataset.c === P.ink.c);
  $('inkSolid').hidden = P.ink.mode !== 'solid'; $('inkGrad').hidden = P.ink.mode === 'solid'; $('gAngRow').hidden = P.ink.mode === 'solid';
  $('ink').value = P.ink.c; $('inkV').textContent = P.ink.c; ['g0', 'g1', 'g2'].forEach((id, k) => $(id).value = P.ink.g[k]);
  pressed(bgBox, b => b.dataset.c === 'transparent' ? P.bg === 'transparent' : P.bg !== 'transparent' && b.dataset.c === P.bgColor);
  $('bgc').value = P.bgColor; $('bgV').textContent = P.bg === 'transparent' ? 'trasparente' : P.bgColor;
  stage.classList.toggle('checker', P.bg === 'transparent');
  pressed($('harmFrom'), b => b.dataset.v === (P.harm || 'bg'));
  pressed($('windDir'), b => +b.dataset.a === P.wind.angle);
  pressed($('formats'), b => b.dataset.f === P.format);
  const [a, c] = P.format.split(':').map(Number);
  stage.style.aspectRatio = `${a} / ${c}`;
  stage.style.maxWidth = a >= c ? '100%' : `calc(78vh * ${a} / ${c})`;
  const ps = $('parts'); ps.textContent = '';
  for (const [v, lab] of PARTS[P.mode]) { const o = document.createElement('option'); o.value = v; o.textContent = v ? lab : `${lab} (${(autoParts(P.mode)/1e6).toLocaleString('it-IT')} M)`; ps.appendChild(o); }
  if (![...ps.options].some(o => +o.value === P.particles)) P.particles = 0;
  ps.value = String(P.particles);
  $('res').value = String(P.export.res); $('fps').value = String(P.export.fps);
  updaters.forEach(u => u());
  renderShapes(); updateNotes(); refreshColorInfo();
}

// ---- export ------------------------------------------------------------------------------------
let SUP = null, abort = null;
support().then(s => { SUP = s; updateNotes(); for (const b of document.querySelectorAll('.btns button')) {
  const k = b.dataset.k; if (s.webcodecs && ((k === 'mp4' && !s.mp4) || (k === 'webm' && !s.webm))) { b.disabled = true; b.title = 'Non disponibile in questo browser'; }
} });
function outSize() {
  const [W, H] = FORMATS[P.format], k = P.export.res/1080;
  const ev = x => Math.round(x*k/2)*2;                  // i codificatori vogliono lati pari
  return [ev(W), ev(H)];
}
function fileName() {
  const f = P.format.replace(':', 'x');
  if (P.mode === 'transizione') return `aporia-transizione-${P.transizione.cover ? 'muro' : 'clip'}-${f}`;
  const S = P.forma.shapes.map(s => s.kind === 'testo' ? (s.text || '').trim().split(/\s+/)[0].toLowerCase().replace(/[^a-z0-9àèéìòù]/g, '') : s.kind === 'aporia-a' ? 'a' : s.kind === 'aporia-logo' ? 'logo' : 'immagine');
  return `aporia-${S.join('-') || 'forma'}-${f}`;
}
document.querySelector('.btns').addEventListener('click', async e => {
  const b = e.target.closest('button'); if (!b || exporting || !ready) return;
  const kind = b.dataset.k;
  const [w, h] = outSize(), fps = P.export.fps;
  const tr = P.mode === 'transizione' && !P.transizione.cover;
  const span = tr ? P.transizione.span : 'pezzo';
  let total = cfg.dur;
  if (tr && span === 'intere') total = (clips.A && clips.A.kind === 'video' ? clips.A.duration : cfg.dur/2) + (clips.B && clips.B.kind === 'video' ? clips.B.duration : cfg.dur/2);
  const frames = Math.round(total*fps);
  exporting = true; abort = new AbortController();
  $('progRow').hidden = false; $('result').textContent = ''; $('prog').value = 0;
  const L = look(fps); if (kind !== 'mp4') L.bg = 'transparent'; else if (L.bg === 'transparent') L.bg = '#000000';
  E.setLook(L);
  const t0 = performance.now();
  try {
    E.reset();
    let res;
    if (SUP && !SUP.webcodecs && kind !== 'png') {
      // ripiego: registrazione in tempo reale del canvas alla risoluzione piena
      const ow = cv.width, oh = cv.height; cv.width = w; cv.height = h;
      res = await record({ canvas: cv, fps, seconds: total, name: fileName(), signal: abort.signal, onProgress: p => { $('prog').value = p; },
        drawAt: tt => { const ct = tr ? clipTimes(tt, span) : { engine: tt }; if (tr) feedExact(ct, w, h, true); E.advanceTo(Math.min(ct.engine, cfg.dur)); E.render({ width: w, height: h }); } });
      cv.width = ow; cv.height = oh;
    } else {
      const buf = new Uint8Array(w*h*4);
      res = await encode({ kind, w, h, fps, frames, name: fileName(), signal: abort.signal,
        onProgress: p => { $('prog').value = p; const el = (performance.now() - t0)/1000; $('progV').textContent = `${Math.round(p*100)}% · ${p > 0.02 ? 'ancora ' + Math.ceil(el/p - el) + ' s' : '…'}`; },
        frame: async i => {
          const tt = i/fps, ct = tr ? clipTimes(tt, span) : { engine: tt };
          if (tr) await feedExact(ct, w, h);
          E.advanceTo(Math.min(ct.engine, cfg.dur));
          E.render({ width: w, height: h, toOutput: true });
          return E.readOutput(buf);
        } });
    }
    const url = URL.createObjectURL(res.blob);
    const a = document.createElement('a'); a.href = url; a.download = res.name;
    a.innerHTML = `Scarica ${res.name}<small>${fmt(res.blob.size/1e6, 1)} MB · ${w}×${h} · ${fps} fps · ${fmt(total, 2)} s</small>`;
    $('result').textContent = ''; $('result').appendChild(a);
    a.click();
  } catch (err) {
    if (err.name !== 'AbortError') { console.error(err); say('Export non riuscito: ' + err.message, true); }
  } finally {
    exporting = false; $('progRow').hidden = true; E.reset(); t = 0; last = 0;
  }
});
$('cancel').onclick = () => abort && abort.abort();
async function feedExact(ct, w, h, preview) {
  for (const k of ['A', 'B']) {
    const c = clips[k]; if (!c) { E.setClip(k, null); continue; }
    const tc = k === 'A' ? ct.a : Math.max(0, ct.b);
    E.setClip(k, preview ? c.previewFrame(tc, Math.min(w, 1080), Math.round(Math.min(w, 1080)*h/w)) : await c.exactFrame(tc, w, h));
  }
}

// ---- progetti ----------------------------------------------------------------------------------
const PKEY = 'aporia-lab-progetti';
const loadPresets = () => { try { return JSON.parse(localStorage.getItem(PKEY) || '[]'); } catch (e) { return []; } };
function renderPresets() {
  const box = $('presets'); box.textContent = '';
  for (const [k, p] of loadPresets().entries()) {
    const r = document.createElement('div'); r.className = 'preset';
    const open = document.createElement('button'); open.type = 'button'; open.textContent = p.name;
    open.onclick = () => { P = merge(DEFAULT, p.project); save(); refreshAll(); t = 0; changed(); $('pMsg').textContent = `Aperto «${p.name}»`; };
    const del = document.createElement('button'); del.type = 'button'; del.textContent = '✕'; del.setAttribute('aria-label', `Elimina ${p.name}`);
    del.onclick = () => { const L = loadPresets(); L.splice(k, 1); localStorage.setItem(PKEY, JSON.stringify(L)); renderPresets(); };
    r.append(open, del); box.appendChild(r);
  }
}
$('pSave').onclick = () => {
  const name = $('pName').value.trim() || `Progetto ${new Date().toLocaleString('it-IT')}`;
  const L = loadPresets().filter(p => p.name !== name); L.unshift({ name, project: clone(P) });
  try { localStorage.setItem(PKEY, JSON.stringify(L)); $('pMsg').textContent = `Salvato «${name}»`; $('pName').value = ''; }
  catch (e) { $('pMsg').textContent = 'Spazio pieno: le immagini e i caratteri caricati occupano molto. Usa «Scarica .json».'; }
  renderPresets();
};
$('pLink').onclick = async () => {
  const q = clone(P);
  let lost = false;
  for (const s of q.forma.shapes) { if (s.src || s.fontData) lost = true; delete s.src; delete s.fontData; }
  const url = location.origin + location.pathname + '#' + btoa(unescape(encodeURIComponent(JSON.stringify(q))));
  try { await navigator.clipboard.writeText(url); $('pMsg').textContent = 'Link copiato' + (lost ? ' (senza le immagini e i caratteri caricati: per quelli usa il .json)' : ''); }
  catch (e) { prompt('Copia il link', url); }
};
$('pExport').onclick = () => {
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([JSON.stringify(P, null, 1)], { type: 'application/json' }));
  a.download = fileName() + '.json'; a.click();
};
$('pImport').onchange = async e => {
  const f = e.target.files[0]; if (!f) return;
  try { P = merge(DEFAULT, JSON.parse(await f.text())); save(); refreshAll(); changed(); $('pMsg').textContent = `Aperto ${f.name}`; }
  catch (err) { $('pMsg').textContent = 'Il file non è un progetto valido'; }
  e.target.value = '';
};
$('pReset').onclick = () => { P = clone(DEFAULT); save(); refreshAll(); t = 0; changed(); $('pMsg').textContent = 'Tornato all’intro originale'; };

refreshAll(); renderPresets();
if (E) rebuild();
window.addEventListener('resize', () => sizeCanvas());
