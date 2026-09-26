// Dalle forme (lettere, frasi, immagini, la A e il logo di Aporia) ai granelli.
//
// Ogni forma diventa una mappa di densità grande come il fotogramma; i granelli della forma finale
// si campionano da lì. Le forme prima (per esempio la A prima del logo) si ottengono "all'indietro":
// ogni granello ha UNA destinazione per forma, abbinate "sottovento" (da una forma alla successiva
// ci si sposta nel verso del vento, poco controvento), come in src/sim_video.py.
import { formaTimeline, transTimeline, KEXP } from './engine.js';

export const FORMATS = {
  '9:16': [1080, 1920], '4:5': [1080, 1350], '1:1': [1080, 1080], '16:9': [1920, 1080],
};

// il riquadro del logo nel fotogramma, come nei video originali (resta intero con qualsiasi ritaglio)
export function unitScale(W, H) { return (W <= H ? 0.8*W : 0.68*H)/1254; }

// ---- immagini della A e del logo originali -----------------------------------------------------
const META = { u0: 196, v0: 196, u1: 1044, v1: 996 };     // dove stanno nel riquadro del logo (1254)
const imgCache = new Map();
function loadImage(src) {
  if (imgCache.has(src)) return imgCache.get(src);
  const p = new Promise((res, rej) => { const im = new Image(); im.decoding = 'async'; im.onload = () => res(im); im.onerror = () => rej(new Error('immagine non caricata: ' + src.slice(0, 60))); im.src = src; });
  imgCache.set(src, p); return p;
}
const base = new URL('.', import.meta.url).href;
export const BUILTIN = {
  'aporia-a': ['forma-a.webp'],
  'aporia-logo': ['logo-fermo.webp', 'logo-vento.webp'],
};

// ---- rumore per la grana della polvere --------------------------------------------------------
function mulberry(seed) { let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0)/4294967296; }; }
function lowNoise(w, h, cell, rand) {
  const gw = Math.ceil(w/cell) + 2, gh = Math.ceil(h/cell) + 2, g = new Float32Array(gw*gh);
  for (let k = 0; k < g.length; k++) g[k] = rand();
  const out = new Float32Array(w*h);
  for (let y = 0; y < h; y++) {
    const fy = y/cell, iy = Math.floor(fy), ty = fy - iy, sy = ty*ty*(3 - 2*ty);
    for (let x = 0; x < w; x++) {
      const fx = x/cell, ix = Math.floor(fx), tx = fx - ix, sx = tx*tx*(3 - 2*tx);
      const a = g[iy*gw + ix], b = g[iy*gw + ix + 1], c = g[(iy + 1)*gw + ix], d = g[(iy + 1)*gw + ix + 1];
      out[y*w + x] = (a + (b - a)*sx) + ((c + (d - c)*sx) - (a + (b - a)*sx))*sy;
    }
  }
  return out;
}

// ---- da una forma a una mappa di densità (0..1) grande rw×rh ------------------------------------
// spec: { kind: 'aporia-a' | 'aporia-logo' | 'testo' | 'immagine', text, font, weight, italic, spacing,
//         size (1 = normale), dx, dy (spostamento, frazione del fotogramma), grain (0..1), src, invert }
export async function rasterize(spec, W, H, rs) {
  const rw = Math.round(W*rs), rh = Math.round(H*rs);
  const cv = new OffscreenCanvas(rw, rh), g = cv.getContext('2d', { willReadFrequently: true });
  const s = unitScale(W, H)*rs, size = spec.size ?? 1;
  const cx = rw/2 + (spec.dx || 0)*rw, cy = rh/2 + (spec.dy || 0)*rh;
  let useAlpha = true, grain = spec.grain ?? 0.5;
  if (spec.kind === 'aporia-a' || spec.kind === 'aporia-logo') {
    const ims = await Promise.all(BUILTIN[spec.kind].map(f => loadImage(base + f)));
    const bw = (META.u1 - META.u0)*s*size, bh = (META.v1 - META.v0)*s*size;
    const x0 = cx + (META.u0 - 627)*s*size, y0 = cy + (META.v0 - 627)*s*size;
    g.globalCompositeOperation = 'lighter';           // logo = parte ferma + parte portata dal vento
    for (const im of ims) g.drawImage(im, x0, y0, bw, bh);
    grain = 0;                                         // hanno già la loro grana
  } else if (spec.kind === 'testo') {
    const fam = spec.font || 'Italiana';
    const font = px => `${spec.italic ? 'italic ' : ''}${spec.weight || 400} ${px}px "${fam}", serif`;
    try { await document.fonts.load(font(100), spec.text || 'A'); } catch (e) {}
    const lines = String(spec.text || 'A').split('\n');
    const probe = 200;
    g.font = font(probe); g.textBaseline = 'alphabetic';
    const sp = (spec.spacing || 0);
    if ('letterSpacing' in g) g.letterSpacing = `${sp*probe}px`;
    const ms = lines.map(l => g.measureText(l || ' '));
    const lh = probe*(spec.lineHeight || 1.08);
    const asc = Math.max(...ms.map(m => m.actualBoundingBoxAscent)), desc = Math.max(...ms.map(m => m.actualBoundingBoxDescent));
    const tw = Math.max(...ms.map(m => m.actualBoundingBoxLeft + m.actualBoundingBoxRight));
    const th = asc + desc + lh*(lines.length - 1);
    const box = unitScale(W, H)*1254*rs;
    const maxW = 0.86*rw*size, maxH = 0.6*box*size*(lines.length > 1 ? 1.5 : 1);
    const k = Math.min(maxW/tw, maxH/th);
    const px = probe*k;
    g.font = font(px); if ('letterSpacing' in g) g.letterSpacing = `${sp*px}px`;
    g.fillStyle = '#fff'; g.textAlign = 'left';
    let y = cy - th*k/2 + asc*k;
    lines.forEach((l, j) => {
      const m = ms[j], lw = (m.actualBoundingBoxLeft + m.actualBoundingBoxRight)*k;
      g.fillText(l, cx - lw/2 + m.actualBoundingBoxLeft*k, y);
      y += lh*k;
    });
  } else if (spec.kind === 'immagine' && spec.src) {
    const im = await loadImage(spec.src);
    const box = unitScale(W, H)*1254*rs*0.72*size;
    const k = Math.min(box/im.naturalWidth, box/im.naturalHeight, 0.9*rw/im.naturalWidth);
    const iw = im.naturalWidth*k, ih = im.naturalHeight*k;
    g.drawImage(im, cx - iw/2, cy - ih/2, iw, ih);
    // se l'immagine non ha trasparenza si usa la luminosità (chiaro = polvere, o il contrario)
    const d = g.getImageData(0, 0, rw, rh).data;
    let transp = 0, lum = 0, cnt = 0;
    const x0 = Math.max(0, Math.floor(cx - iw/2)), x1 = Math.min(rw, Math.ceil(cx + iw/2));
    const y0 = Math.max(0, Math.floor(cy - ih/2)), y1 = Math.min(rh, Math.ceil(cy + ih/2));
    for (let yy = y0; yy < y1; yy += 3) for (let xx = x0; xx < x1; xx += 3) {
      const o = (yy*rw + xx)*4; if (d[o + 3] < 250) transp++; lum += (d[o]*0.299 + d[o + 1]*0.587 + d[o + 2]*0.114)/255; cnt++;
    }
    useAlpha = transp > cnt*0.02;
    spec._lumInvert = !useAlpha && (spec.invert ?? (lum/cnt > 0.5));
    spec._box = [x0, y0, x1, y1];
  }
  const d = g.getImageData(0, 0, rw, rh).data;
  const out = new Float32Array(rw*rh);
  if (useAlpha) for (let k = 0; k < out.length; k++) out[k] = d[k*4 + 3]/255;
  else {
    const [x0, y0, x1, y1] = spec._box;
    for (let yy = y0; yy < y1; yy++) for (let xx = x0; xx < x1; xx++) {
      const o = yy*rw + xx, L = (d[o*4]*0.299 + d[o*4 + 1]*0.587 + d[o*4 + 2]*0.114)/255;
      out[o] = spec._lumInvert ? 1 - L : L;
    }
  }
  if (grain > 0) {
    // la stessa idea della A originale: luce morbida che varia piano, più granelli chiari sparsi
    const rand = mulberry(11), lo = lowNoise(rw, rh, Math.max(8, 38*rs*2), rand);
    for (let k = 0; k < out.length; k++) if (out[k] > 0) {
      const sp = rand(); out[k] *= Math.min(1, 1 - grain*(0.16 - 0.12*lo[k]) + grain*(sp > 0.985 ? 0.25 : (sp - 0.5)*0.14));
    }
  }
  return { rw, rh, rs, a: out };
}

// ---- campionamento dei granelli ---------------------------------------------------------------
// densità del campionamento: -ln(1 - B), così quando tutti i granelli sono posati la luce
// 1 - exp(-K·densità) è esattamente la forma
function densityOf(r) {
  const G = new Float32Array(r.a.length); let sum = 0;
  for (let k = 0; k < G.length; k++) { const b = Math.min(r.a[k], 0.965); const v = b > 0.004 ? -Math.log(1 - b) : 0; G[k] = v; sum += v; }
  return { G, sum };
}
// campionamento stratificato: n punti (x, y in pixel del fotogramma), ordine rimescolato
function samplePoints(r, dens, n, rand) {
  const { G, sum } = dens, out = new Float32Array(n*2);
  if (sum <= 0) { for (let k = 0; k < n; k++) { out[2*k] = r.rw/2/r.rs; out[2*k + 1] = r.rh/2/r.rs; } return out; }
  const step = sum/n; let acc = 0, next = rand()*step, j = 0;
  for (let p = 0; p < G.length && j < n; p++) {
    acc += G[p];
    while (next < acc && j < n) {
      const x = p % r.rw, y = (p - x)/r.rw;
      out[2*j] = (x + rand())/r.rs; out[2*j + 1] = (y + rand())/r.rs; j++; next += step;
    }
  }
  for (; j < n; j++) { out[2*j] = out[0]; out[2*j + 1] = out[1]; }
  // rimescola (Fisher-Yates a coppie)
  for (let k = n - 1; k > 0; k--) {
    const m = Math.floor(rand()*(k + 1));
    const ax = out[2*k], ay = out[2*k + 1]; out[2*k] = out[2*m]; out[2*k + 1] = out[2*m + 1]; out[2*m] = ax; out[2*m + 1] = ay;
  }
  return out;
}

// ---- abbinamento sottovento tra due forme (trasporto ottimo "a fette", su rappresentanti) ------
function argsortInto(proj, n, keys, idx) {
  let mn = Infinity, mx = -Infinity;
  for (let k = 0; k < n; k++) { const v = proj[k]; if (v < mn) mn = v; if (v > mx) mx = v; }
  const sc = (2**30 - 1)/Math.max(mx - mn, 1e-9);
  for (let k = 0; k < n; k++) keys[k] = Math.floor((proj[k] - mn)*sc)*16384 + k;
  keys.sort();
  for (let k = 0; k < n; k++) idx[k] = keys[k] % 16384;
}
// from: posizioni (u) dei granelli nella forma dopo; to: punti campionati nella forma prima.
// ritorna, per ogni rappresentante, il suo punto nella forma prima
function matchDownwind(Rb, Ra, n, width, rand) {
  const dl = 0.07*width;                               // spinge l'abbinamento a muoversi col vento
  const X = new Float32Array(n*2), Y = new Float32Array(n*2);
  for (let k = 0; k < n; k++) { X[2*k] = Rb[2*k]; X[2*k + 1] = Rb[2*k + 1]*1.3; Y[2*k] = Ra[2*k] + dl; Y[2*k + 1] = Ra[2*k + 1]*1.3; }
  const px = new Float32Array(n), py = new Float32Array(n), kx = new Float64Array(n), ky = new Float64Array(n);
  const ix = new Uint32Array(n), iy = new Uint32Array(n);
  const ITER = 110;
  for (let it = 0; it < ITER; it++) {
    const th = it*2.39996323 + rand()*0.3, dx = Math.cos(th), dy = Math.sin(th);
    for (let k = 0; k < n; k++) { px[k] = X[2*k]*dx + X[2*k + 1]*dy; py[k] = Y[2*k]*dx + Y[2*k + 1]*dy; }
    argsortInto(px, n, kx, ix); argsortInto(py, n, ky, iy);
    const st = it < ITER - 20 ? 1 : 0.6;
    for (let k = 0; k < n; k++) { const a = ix[k], d = (py[iy[k]] - px[a])*st; X[2*a] += d*dx; X[2*a + 1] += d*dy; }
  }
  // abbinamento esatto: ciascuno al punto libero più vicino (griglia)
  const cell = Math.max(1, Math.sqrt(width*width/n)*1.5);
  const grid = new Map(), key = (i, j) => i*100003 + j;
  for (let k = 0; k < n; k++) { const K = key(Math.floor(Y[2*k]/cell), Math.floor(Y[2*k + 1]/cell)); let a = grid.get(K); if (!a) grid.set(K, a = []); a.push(k); }
  const used = new Uint8Array(n), res = new Float32Array(n*2), order = new Uint32Array(n);
  for (let k = 0; k < n; k++) order[k] = k;
  for (let k = n - 1; k > 0; k--) { const m = Math.floor(rand()*(k + 1)); const t = order[k]; order[k] = order[m]; order[m] = t; }
  for (const a of order) {
    const gx = Math.floor(X[2*a]/cell), gy = Math.floor(X[2*a + 1]/cell);
    let best = -1, bd = Infinity;
    for (let r = 0; r < 60 && best < 0; r++) {
      for (let i = gx - r; i <= gx + r; i++) for (let j = gy - r; j <= gy + r; j++) {
        if (r > 0 && i > gx - r && i < gx + r && j > gy - r && j < gy + r) continue;
        const L = grid.get(key(i, j)); if (!L) continue;
        for (const b of L) if (!used[b]) { const d = (Y[2*b] - X[2*a])**2 + (Y[2*b + 1] - X[2*a + 1])**2; if (d < bd) { bd = d; best = b; } }
      }
    }
    if (best < 0) best = a;
    used[best] = 1;
    res[2*a] = Y[2*best] - dl; res[2*a + 1] = Y[2*best + 1]/1.3;
  }
  return res;
}
// estende l'abbinamento dei rappresentanti a tutti i granelli (vicino più prossimo + scarto locale)
function extend(P, n, Rb, RA, nr, width) {
  const cell = Math.max(1, Math.sqrt(width*width/nr)*1.2);
  const grid = new Map(), key = (i, j) => i*100003 + j;
  for (let k = 0; k < nr; k++) { const K = key(Math.floor(Rb[2*k]/cell), Math.floor(Rb[2*k + 1]/cell)); let a = grid.get(K); if (!a) grid.set(K, a = []); a.push(k); }
  const out = new Float32Array(n*2);
  for (let p = 0; p < n; p++) {
    const x = P[2*p], y = P[2*p + 1], gx = Math.floor(x/cell), gy = Math.floor(y/cell);
    let best = 0, bd = Infinity;
    for (let r = 0; r < 80; r++) {
      for (let i = gx - r; i <= gx + r; i++) for (let j = gy - r; j <= gy + r; j++) {
        if (r > 0 && i > gx - r && i < gx + r && j > gy - r && j < gy + r) continue;
        const L = grid.get(key(i, j)); if (!L) continue;
        for (const b of L) { const d = (Rb[2*b] - x)**2 + (Rb[2*b + 1] - y)**2; if (d < bd) { bd = d; best = b; } }
      }
      if (bd < (r*cell)**2) break;
    }
    out[2*p] = RA[2*best] + (x - Rb[2*best]); out[2*p + 1] = RA[2*best + 1] + (y - Rb[2*best + 1]);
  }
  return out;
}

// pixel del fotogramma -> spazio del vento (unità del logo, centrato)
function toWind(pts, n, W, H, s, ang) {
  const c = Math.cos(ang), sn = Math.sin(ang), out = new Float32Array(n*2);
  for (let k = 0; k < n; k++) {
    const dx = (pts[2*k] - W/2)/s, dy = (pts[2*k + 1] - H/2)/s;
    out[2*k] = dx*c + dy*sn; out[2*k + 1] = -dx*sn + dy*c;
  }
  return out;
}

const tick = () => new Promise(r => setTimeout(r, 0));

// ---- costruisce tutto per il motore -----------------------------------------------------------
// project: vedi laboratorio.html (DEFAULT). Ritorna { cfg, data } per DustEngine.load()
export async function build(project, { onStage } = {}) {
  const [W, H] = FORMATS[project.format] || FORMATS['9:16'];
  const s = unitScale(W, H), ang = (project.wind.angle || 0)*Math.PI/180;
  const rs = Math.min(1, 2048/Math.max(W, H));
  const rand = mulberry(project.seed || 1);
  const wind = { angle: ang, strength: project.wind.strength ?? 1, turb: project.wind.turb ?? 1 };
  if (project.mode === 'forma') {
    const F = project.forma, shapes = F.shapes.slice(0, 3);
    const total = Math.max(20000, Math.round(project.particles));
    const nShape = Math.round(total/1.1), n = total;
    onStage && onStage('forme');
    const rasters = [];
    for (const sp of shapes) rasters.push(await rasterize({ ...sp, size: (sp.size ?? 1)*(F.size ?? 1), dy: (sp.dy ?? 0) + (F.dy ?? 0) }, W, H, rs));
    await tick();
    const dens = rasters.map(densityOf);
    // forma finale: i granelli si campionano da lei
    const last = rasters.length - 1;
    const Pf = toWind(samplePoints(rasters[last], dens[last], nShape, rand), nShape, W, H, s, ang);
    const chain = [Pf];
    // bbox della forma finale (per il fronte del vento e per il gradiente)
    let mn = Infinity, mx = -Infinity;
    for (let k = 0; k < nShape; k++) { const v = Pf[2*k]; if (v < mn) mn = v; if (v > mx) mx = v; }
    const width = Math.max(50, mx - mn);
    for (let j = last - 1; j >= 0; j--) {
      onStage && onStage('abbinamento');
      await tick();
      const nr = Math.min(12000, nShape);
      const Rb = new Float32Array(nr*2), next = chain[0];
      for (let k = 0; k < nr; k++) { const m = Math.floor(rand()*nShape); Rb[2*k] = next[2*m]; Rb[2*k + 1] = next[2*m + 1]; }
      const Ra = toWind(samplePoints(rasters[j], dens[j], nr, rand), nr, W, H, s, ang);
      const RA = matchDownwind(Rb, Ra, nr, width, rand);
      chain.unshift(extend(next, nShape, Rb, RA, nr, width));
    }
    while (chain.length < 3) chain.splice(1, 0, chain[chain.length === 1 ? 0 : 1]);
    // [P0, P1, P2]: con due forme P1 = P2 (lo scivolamento è uno solo)
    const [P0, P1, P2] = shapes.length === 1 ? [chain[0], chain[0], chain[0]] : shapes.length === 2 ? [chain[0], chain[2], chain[2]] : chain;
    const P01 = new Float32Array(n*4), P2t = new Float32Array(n*4);
    for (let k = 0; k < nShape; k++) {
      P01[4*k] = P0[2*k]; P01[4*k + 1] = P0[2*k + 1]; P01[4*k + 2] = P1[2*k]; P01[4*k + 3] = P1[2*k + 1];
      P2t[4*k] = P2[2*k]; P2t[4*k + 1] = P2[2*k + 1];
    }
    // peso di un granello posato: la luce della forma finale è esattamente quella della forma
    const wN = dens[last].sum/(rs*rs)/nShape/KEXP;
    const T = formaTimeline({ shapes: shapes.length, arrive: F.arrive, hold: F.hold, final: F.final, morph: F.morph, exit: F.exit });
    Object.assign(T, { fx0: mn, fxR: width });
    // riquadro del gradiente: la forma finale sullo schermo
    let bx0 = Infinity, by0 = Infinity, bx1 = -Infinity, by1 = -Infinity;
    const c = Math.cos(ang), sn = Math.sin(ang);
    for (let k = 0; k < nShape; k += 7) {
      const x = W/2 + s*(c*P2[2*k] - sn*P2[2*k + 1]), y = H/2 + s*(sn*P2[2*k] + c*P2[2*k + 1]);
      if (x < bx0) bx0 = x; if (x > bx1) bx1 = x; if (y < by0) by0 = y; if (y > by1) by1 = y;
    }
    const cfg = { mode: 'forma', W, H, wind, T: { ...T, ex: (Math.abs(c)*W/2 + Math.abs(sn)*H/2)/s, ey: (Math.abs(sn)*W/2 + Math.abs(c)*H/2)/s, s },
      dur: T.dur, gbox: [(bx0 + bx1)/2, (by0 + by1)/2, Math.max(bx1 - bx0, by1 - by0)*0.9] };
    return { cfg, data: { n, nShape, P01, P2: P2t, wN } };
  }
  // transizione
  const X = project.transizione;
  const n = Math.max(20000, Math.round(project.particles));
  const gw = Math.max(1, Math.round(Math.sqrt(n*W/H))), gh = Math.ceil(n/gw);
  const N = gw*gh;
  const mid = !X.cover && X.mid && X.mid.kind && X.mid.kind !== 'nessuna';
  let P2 = null;
  if (mid) {
    onStage && onStage('forme');
    const r = await rasterize(X.mid, W, H, rs), d = densityOf(r);
    const pts = toWind(samplePoints(r, d, N, rand), N, W, H, s, ang);
    P2 = new Float32Array(N*4);
    for (let k = 0; k < N; k++) { P2[4*k] = pts[2*k]; P2[4*k + 1] = pts[2*k + 1]; }
  }
  const T = transTimeline({ dur: X.dur, W, H, s, angle: ang, mid, cover: X.cover, midFrac: X.midFrac });
  const cfg = { mode: 'transizione', cover: !!X.cover, W, H, wind, T, dur: X.dur, grain: X.grain ?? 1.35, gbox: [W/2, H/2, Math.max(W, H)] };
  return { cfg, data: { n: N, grid: [gw, gh], P2 } };
}
