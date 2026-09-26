// Teoria dei colori per la polvere e il fondo.
// Si ragiona in OKLCH (luminosità, croma, tinta percepite in modo uniforme): le armonie classiche
// (complementare, triadica, ...) si fanno ruotando la tinta, poi per ogni tinta si sceglie la
// luminosità e la saturazione che rendono la polvere più leggibile sul fondo (contrasto WCAG).

const clamp01 = x => Math.min(1, Math.max(0, x));
export function hexToRgb(h) { h = h.replace('#', ''); if (h.length === 3) h = [...h].map(c => c + c).join(''); return [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16)/255); }
export function rgbToHex(rgb) { return '#' + rgb.map(v => Math.round(clamp01(v)*255).toString(16).padStart(2, '0')).join(''); }
const toLin = c => c <= 0.04045 ? c/12.92 : ((c + 0.055)/1.055)**2.4;
const toGam = c => c <= 0.0031308 ? 12.92*c : 1.055*c**(1/2.4) - 0.055;

export function rgbToOklch([r, g, b]) {
  r = toLin(r); g = toLin(g); b = toLin(b);
  const l = Math.cbrt(0.4122214708*r + 0.5363325363*g + 0.0514459929*b);
  const m = Math.cbrt(0.2119034982*r + 0.6806995451*g + 0.1073969566*b);
  const s = Math.cbrt(0.0883024619*r + 0.2817188376*g + 0.6299787005*b);
  const L = 0.2104542553*l + 0.7936177850*m - 0.0040720468*s;
  const A = 1.9779984951*l - 2.4285922050*m + 0.4505937099*s;
  const B = 0.0259040371*l + 0.7827717662*m - 0.8086757660*s;
  return [L, Math.hypot(A, B), (Math.atan2(B, A)*180/Math.PI + 360) % 360];
}
function oklchToLinear(L, C, h) {
  const A = C*Math.cos(h*Math.PI/180), B = C*Math.sin(h*Math.PI/180);
  const l = (L + 0.3963377774*A + 0.2158037573*B)**3, m = (L - 0.1055613458*A - 0.0638541728*B)**3, s = (L - 0.0894841775*A - 1.2914855480*B)**3;
  return [4.0767416621*l - 3.3077115913*m + 0.2309699292*s, -1.2684380046*l + 2.6097574011*m - 0.3413193965*s, -0.0041960863*l - 0.7034186147*m + 1.7076147010*s];
}
const inGamut = lin => lin.every(v => v >= -1e-4 && v <= 1 + 1e-4);
export function maxChroma(L, h) { let lo = 0, hi = 0.4; for (let k = 0; k < 22; k++) { const m = (lo + hi)/2; if (inGamut(oklchToLinear(L, m, h))) lo = m; else hi = m; } return lo; }
export function oklchToHex(L, C, h) { const c = Math.min(C, maxChroma(L, h)); return rgbToHex(oklchToLinear(L, c, h).map(v => toGam(clamp01(v)))); }

export function luminance(hex) { const [r, g, b] = hexToRgb(hex).map(toLin); return 0.2126*r + 0.7152*g + 0.0722*b; }
export function contrast(a, b) { const x = luminance(a), y = luminance(b); return (Math.max(x, y) + 0.05)/(Math.min(x, y) + 0.05); }
export function contrastLabel(r) { return r >= 7 ? 'ottimo' : r >= 4.5 ? 'buono' : r >= 3 ? 'debole' : 'scarso'; }

// le teorie: rotazioni della tinta (gradi) rispetto al colore di partenza
export const THEORIES = [
  { id: 'complementare', name: 'Complementare', offs: [180], desc: 'la tinta opposta sul cerchio: il contrasto di colore più forte' },
  { id: 'divisi', name: 'Complementari divisi', offs: [150, 210], desc: 'i due vicini dell’opposto: forte ma meno aggressivo' },
  { id: 'triadica', name: 'Triadica', offs: [120, 240], desc: 'tre tinte a 120°: vivace ed equilibrata' },
  { id: 'tetradica', name: 'Tetradica (quadrato)', offs: [90, 180, 270], desc: 'quattro tinte a 90°: ricca, serve un colore dominante' },
  { id: 'rettangolo', name: 'Doppio complementare', offs: [60, 180, 240], desc: 'due coppie di complementari: molto varia' },
  { id: 'analoga', name: 'Analoga', offs: [30, -30], desc: 'tinte vicine: armonia morbida, il contrasto viene dalla luce' },
  { id: 'monocromatica', name: 'Monocromatica', offs: [0], desc: 'la stessa tinta, più chiara o più scura: elegante e sobria' },
  { id: 'neutra', name: 'Neutra', offs: [0], neutral: true, desc: 'quasi bianco o quasi nero, appena tinto: si legge sempre' },
];

// il colore più leggibile di una tinta su un altro colore
function bestOn(other, h, { chromaCap = 0.3, neutral = false, calm = false } = {}) {
  const oL = rgbToOklch(hexToRgb(other))[0];
  let best = null;
  for (let L = 0.1; L <= 0.985; L += 0.0125) {
    // un fondo deve restare calmo: poca saturazione e luce lontana da quella della polvere
    const cap = neutral ? 0.018 : calm ? Math.min(chromaCap, 0.13) : chromaCap;
    const C = Math.min(maxChroma(L, h)*(calm ? 0.7 : 0.92), cap);
    const hex = oklchToHex(L, C, h), cr = contrast(hex, other);
    // basta un contrasto pieno (7:1, "ottimo"); oltre conta quanto il colore si vede davvero
    const score = neutral ? Math.min(cr, 12)/12 : Math.min(cr, 7)/7*0.62 + Math.min(C, calm ? 0.1 : 0.25)/(calm ? 0.1 : 0.25)*0.38
      - (cr < 4.5 ? 0.25 : 0) - (Math.abs(L - oL) < 0.25 ? 0.3 : 0);
    if (!best || score > best.score) best = { hex, cr, score, L, C };
  }
  return best;
}

// a partire dal fondo: i colori migliori per la polvere (la A), per ogni teoria
export function inksForBackground(bg) {
  const [, C, h] = rgbToOklch(hexToRgb(bg));
  const neutralBg = C < 0.025;
  const ref = neutralBg ? 70 : h;                      // fondo neutro: si parte da un oro caldo
  return THEORIES.map(t => {
    const cols = t.offs.map(o => bestOn(bg, (ref + o + 360) % 360, { neutral: t.neutral, chromaCap: t.id === 'monocromatica' ? 0.12 : 0.3 }));
    const main = cols.reduce((a, b) => (b.score > a.score ? b : a));
    return { ...t, colors: cols.map(c => c.hex), main: main.hex, cr: main.cr, score: main.score,
      note: neutralBg && !t.neutral ? 'fondo neutro: tinte calcolate a partire da un oro caldo' : '' };
  });
}

// a partire dalla polvere: i fondi più compatibili, per ogni teoria
export function backgroundsForInk(ink) {
  const [, C, h] = rgbToOklch(hexToRgb(ink));
  const neutralInk = C < 0.025, ref = neutralInk ? 250 : h;
  return THEORIES.map(t => {
    const cols = t.offs.map(o => bestOn(ink, (ref + o + 360) % 360, { neutral: t.neutral, calm: true }));
    const main = cols.reduce((a, b) => (b.score > a.score ? b : a));
    return { ...t, colors: cols.map(c => c.hex), main: main.hex, cr: main.cr, score: main.score,
      note: neutralInk && !t.neutral ? 'polvere neutra: tinte calcolate a partire da un blu notte' : '' };
  });
}
