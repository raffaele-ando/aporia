// Motore della polvere su GPU (WebGL2): la stessa fisica di src/sim_video.py, ma calcolata dal
// vivo nel browser, così ogni modifica (forma, colore, vento, formato) si vede subito e si esporta
// senza passare da Python.
//
// Due modi:
//   'forma'        la polvere portata dal vento forma una sequenza di forme (fino a 3: per esempio
//                  la A, poi il logo), resta, poi il vento la riporta via.
//   'transizione'  ogni pixel della clip A diventa un granello (milioni), il vento li porta via su
//                  tutto lo schermo e li ricompone nella clip B. Con 'copertura' non servono clip:
//                  un muro di polvere copre tutto lo schermo nel momento del taglio.
//
// Unità: la simulazione lavora nello "spazio del vento" (x lungo il vento, y di traverso), in unità
// del logo originale (il riquadro del logo è 1254 unità), centrato sul centro del fotogramma.

export const SIM_HZ = 120;                  // passi di simulazione al secondo (60 fps: 2 per fotogramma)
const TEXW = 2048;                          // larghezza delle texture dei granelli
export const KEXP = 2.2;                    // luce = 1 - exp(-K·densità), come nel video originale

// ---- GLSL ------------------------------------------------------------------------------------
const SIMPLEX = `
vec3 m289(vec3 x){ return x - floor(x*(1./289.))*289.; }
vec4 m289(vec4 x){ return x - floor(x*(1./289.))*289.; }
vec4 perm(vec4 x){ return m289(((x*34.) + 10.)*x); }
vec4 tis(vec4 r){ return 1.79284291400159 - 0.85373472095314*r; }
// simplex 3D (Ashima/McEwan, MIT) con il gradiente analitico: vec4(valore, d/dx, d/dy, d/dz)
vec4 snoiseD(vec3 v){
  const vec2 C = vec2(1./6., 1./3.); const vec4 D = vec4(0., .5, 1., 2.);
  vec3 i = floor(v + dot(v, C.yyy)); vec3 x0 = v - i + dot(i, C.xxx);
  vec3 g = step(x0.yzx, x0.xyz); vec3 l = 1. - g;
  vec3 i1 = min(g.xyz, l.zxy); vec3 i2 = max(g.xyz, l.zxy);
  vec3 x1 = x0 - i1 + C.xxx; vec3 x2 = x0 - i2 + C.yyy; vec3 x3 = x0 - D.yyy;
  i = m289(i);
  vec4 p = perm(perm(perm(i.z + vec4(0., i1.z, i2.z, 1.)) + i.y + vec4(0., i1.y, i2.y, 1.)) + i.x + vec4(0., i1.x, i2.x, 1.));
  vec3 ns = 0.142857142857*D.wyz - D.xzx;
  vec4 j = p - 49.*floor(p*ns.z*ns.z);
  vec4 x_ = floor(j*ns.z); vec4 y_ = floor(j - 7.*x_);
  vec4 x = x_*ns.x + ns.yyyy; vec4 y = y_*ns.x + ns.yyyy; vec4 h = 1. - abs(x) - abs(y);
  vec4 b0 = vec4(x.xy, y.xy); vec4 b1 = vec4(x.zw, y.zw);
  vec4 s0 = floor(b0)*2. + 1.; vec4 s1 = floor(b1)*2. + 1.; vec4 sh = -step(h, vec4(0.));
  vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy; vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww;
  vec3 p0 = vec3(a0.xy, h.x); vec3 p1 = vec3(a0.zw, h.y); vec3 p2 = vec3(a1.xy, h.z); vec3 p3 = vec3(a1.zw, h.w);
  vec4 nr = tis(vec4(dot(p0,p0), dot(p1,p1), dot(p2,p2), dot(p3,p3)));
  p0 *= nr.x; p1 *= nr.y; p2 *= nr.z; p3 *= nr.w;
  vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.);
  vec4 m2 = m*m; vec4 m4 = m2*m2;
  vec4 pd = vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3));
  vec4 tmp = m2*m*pd;
  vec3 gr = -8.*(tmp.x*x0 + tmp.y*x1 + tmp.z*x2 + tmp.w*x3) + m4.x*p0 + m4.y*p1 + m4.z*p2 + m4.w*p3;
  return 42.*vec4(dot(m4, pd), gr);
}`;

const COMMON = `#version 300 es
precision highp float; precision highp int; precision highp sampler2D;
#define TEXW ${TEXW}
uniform float uT;          // tempo (s)
uniform int uMode;         // 0 forma, 1 transizione con clip, 2 copertura
uniform float uAdv;        // quanto ha viaggiato l'aria (i vortici viaggiano con lei)
uniform float uTurb;       // intensità dei vortici (1 = come l'originale)
uniform float uWindU;      // velocità del vento adesso (unità/s)
uniform vec2 uExt;         // mezza larghezza/altezza del fotogramma nello spazio del vento
uint pcg(uint v){ uint s = v*747796405u + 2891336453u; uint w = ((s >> ((s >> 28u) + 4u)) ^ s)*277803737u; return (w >> 22u) ^ w; }
float rnd(uint i, uint k){ return float(pcg(i ^ pcg(k*0x9E3779B9u + 0x2545F491u)) >> 8u)/16777216.; }
float gss(uint i, uint k){ float a = max(rnd(i, k), 1e-7), b = rnd(i, k + 101u); return sqrt(-2.*log(a))*cos(6.2831853*b); }
float sm(float a, float b, float t){ float q = clamp((t - a)/(b - a), 0., 1.); return q*q*(3. - 2.*q); }
${SIMPLEX}
// vortici senza divergenza (come l'aria vera): rotore di un potenziale di rumore, tre ottave come
// in sim_video.py (L = 300, 90, 30 unità); calibrato perché abbia la stessa ampiezza e grana
vec2 curl1(vec2 q, float L, float off){
  vec4 n = snoiseD(vec3((q.x - uAdv)/(10.*L), q.y/(10.*L), uT*0.216 + off));
  return vec2(n.z, -n.y)*0.268;
}
vec2 turb(vec2 q){ return (curl1(q, 300., 0.) + 0.55*curl1(q, 90., 17.3) + 0.25*curl1(q, 30., 41.7))*uTurb; }

// ---- forma: i tempi di ogni granello (come sim_video.py) ----
uniform int uNShape;       // granelli della forma; gli altri sono polvere nell'aria
uniform vec2 uFx;          // minimo e ampiezza della forma finale lungo il vento
uniform vec3 uCap;         // arrivo: inizio, fronte, casuale
uniform vec4 uMor;         // tenuta forma 1, tenuta forma 2, durata dello scivolamento, fronte
uniform vec2 uRel;         // uscita: inizio (1e9 = resta), fronte
struct PT { float tcap, dcap, tmor, dmor, tmor2, dmor2, trel, tau, fx; };
PT timing(uint i, vec2 p2){
  PT o; o.fx = clamp((p2.x - uFx.x)/uFx.y, 0., 1.);
  float r0 = rnd(i, 0u), r1 = rnd(i, 1u), r2 = rnd(i, 2u), r3 = rnd(i, 3u), r4 = rnd(i, 4u);
  o.tcap = uCap.x + uCap.y*o.fx + uCap.z*pow(r0, 1.4);        // la raffica lo sbatte sulla forma
  o.dcap = 0.18 + 0.22*r1;                                     // si ferma quasi di colpo
  o.tmor = max(o.tcap + 0.05 + 0.25*r2, uMor.x + uMor.w*o.fx + 0.15*r2);   // scivola alla forma dopo
  o.dmor = (0.35 + 0.3*r3)*uMor.z;
  o.tmor2 = max(o.tmor + o.dmor + 0.05 + 0.25*r4, uMor.y + uMor.w*o.fx + 0.15*r4);
  o.dmor2 = (0.35 + 0.3*r3)*uMor.z;
  o.trel = uRel.x + uRel.y*o.fx + 0.14*r4;                     // il vento se lo riprende
  o.tau = clamp(exp(log(0.11) + 0.45*gss(i, 6u)), 0.035, 0.4);
  return o;
}

// ---- transizione: ogni granello è un pixel della clip ----
uniform ivec2 uGrid;       // griglia dei granelli (colonne, righe)
uniform vec2 uFrame;       // fotogramma in pixel
uniform float uS;          // pixel per unità
uniform vec2 uDir;         // direzione del vento sullo schermo
uniform vec4 uTr;          // partenze: inizio, fronte; arrivi: inizio; casuale
uniform float uLandF;      // fronte degli arrivi
uniform vec2 uWrap;        // periodo dello schermo (x, y) nello spazio del vento
uniform vec4 uMid;         // forma a metà: quota, presa, rilascio, fronte
uniform float uD;          // durata della transizione
vec2 toWind(vec2 px){ vec2 d = (px - 0.5*uFrame)/uS; return vec2(dot(d, uDir), dot(d, vec2(-uDir.y, uDir.x))); }
vec2 toScreen(vec2 q){ return 0.5*uFrame + uS*(uDir*q.x + vec2(-uDir.y, uDir.x)*q.y); }
vec2 homePx(uint i){
  uint gw = uint(uGrid.x);
  return (vec2(float(i % gw), float(i / gw)) + vec2(rnd(i, 20u), rnd(i, 21u)))/vec2(uGrid)*uFrame;
}
bool isMid(uint i){ return rnd(i, 30u) < uMid.x; }
struct TT { float tdep, tland, dcap, tsc, tsr, lap; };
TT ttiming(uint i, vec2 hq, vec2 sq){
  TT o;
  float pr = clamp((hq.x + uExt.x)/(2.*uExt.x), 0., 1.);
  float lf = snoiseD(vec3(hq.y/420., hq.x/900., 3.1)).x;     // il fronte non è una riga dritta
  o.tdep = uTr.x + uTr.y*clamp(pr + 0.1*lf, 0., 1.) + uTr.w*rnd(i, 23u);
  o.tland = uTr.z + uLandF*clamp(pr - 0.1*lf, 0., 1.) + uTr.w*rnd(i, 22u);
  o.lap = o.tland - o.tdep;
  o.dcap = uD*(0.06 + 0.05*rnd(i, 24u));
  o.tsc = 1e9; o.tsr = 1e9;
  if (isMid(i)) {
    float fs = clamp((sq.x + uExt.x)/(2.*uExt.x), 0., 1.);
    o.tsc = uMid.y + uMid.w*fs + 0.04*uD*rnd(i, 25u);
    o.tsr = uMid.z + uMid.w*fs + 0.03*uD*rnd(i, 26u);
    // il ritorno non dipende da dove sta sulla forma: così il fondo sa quando il suo granello è arrivato
    o.tland = max(o.tland, uMid.z + uMid.w + 0.17*uD + 0.04*uD*rnd(i, 27u));
  }
  return o;
}
// quanto è "posato": sulla clip A, sulla forma a metà, sulla clip B
vec3 tattach(TT T, float t){
  if (uMode == 2) return vec3(0.);
  return vec3(1. - sm(T.tdep, T.tdep + 0.1, t), sm(T.tsc, T.tsc + 0.1*uD, t)*(1. - sm(T.tsr, T.tsr + 0.1, t)), sm(T.tland, T.tland + T.dcap, t));
}
`;

const QUAD_VS = `#version 300 es
in vec2 p; out vec2 vUv;
void main(){ vUv = p*0.5 + 0.5; gl_Position = vec4(p, 0., 1.); }`;

// stato iniziale di ogni granello
const INIT_FS = COMMON + `
uniform sampler2D uP01, uP2;
out vec4 o;
void main(){
  ivec2 tc = ivec2(gl_FragCoord.xy); uint i = uint(tc.y*TEXW + tc.x);
  if (uMode == 0) {
    if (int(i) >= uNShape) {                     // polvere nell'aria: attraversa tutto lo schermo
      o = vec4(mix(-uExt.x - 400., uExt.x, rnd(i, 12u)), mix(-uExt.y - 60., uExt.y + 60., rnd(i, 13u)), 950., 0.);
      return;
    }
    vec2 p0 = texelFetch(uP01, tc, 0).xy; PT T = timing(i, texelFetch(uP2, tc, 0).xy);
    // già nel vento, sopravento rispetto a dove si poserà: arriva da fuori schermo
    o = vec4(p0.x - 950.*T.tcap - 700.*pow(rnd(i, 11u), 0.8), p0.y + 150.*gss(i, 10u), 950., 0.);
  } else {
    vec2 hq = toWind(homePx(i));
    if (uMode == 2) o = vec4(hq.x - uWrap.x*(1.05 + 0.1*rnd(i, 14u)), hq.y, 0., 0.);   // tutta sopravento, fuori schermo
    else o = vec4(hq, 0., 0.);                                                        // ferma sul suo pixel
  }
}`;

// un passo di simulazione
const SIM_FS = COMMON + `
uniform sampler2D uState, uP01, uP2;
uniform float uDt;
out vec4 o;
void main(){
  ivec2 tc = ivec2(gl_FragCoord.xy); uint i = uint(tc.y*TEXW + tc.x);
  vec4 st = texelFetch(uState, tc, 0); vec2 x = st.xy, v = st.zw;
  float t = uT, dt = uDt;
  vec2 tu = turb(x);
  float a = 170. + 0.28*uWindU;
  vec2 w = vec2(uWindU + tu.x*a, -0.06*uWindU + tu.y*a);
  if (uMode == 1) {
    // ognuno col suo passo: i granelli si mescolano e riempiono tutto lo schermo
    w.x = uWindU*(0.72 + 0.56*rnd(i, 32u)) + tu.x*a;
    w.y += (rnd(i, 33u) - 0.5)*0.2*uWindU;
  } else if (uMode == 2) w.x = uWindU*(0.93 + 0.14*rnd(i, 32u)) + tu.x*a;
  if (uMode == 0) {
    if (int(i) >= uNShape) {                     // polvere nell'aria
      float at = clamp(exp(log(0.09) + 0.5*gss(i, 8u)), 0.03, 0.35);
      v += (w - v)/at*dt; x += v*dt;
      uint k = uint(t*997.);
      if (x.x > uExt.x + 60.) { x.x = -uExt.x - 60. - 250.*rnd(i, 40u + k); x.y = mix(-uExt.y - 60., uExt.y + 60., rnd(i, 41u + k)); }
      if (abs(x.y) > uExt.y + 120.) x.y = mix(-uExt.y, uExt.y, rnd(i, 42u + k));
      o = vec4(x, v); return;
    }
    vec4 p01 = texelFetch(uP01, tc, 0); vec2 p2 = texelFetch(uP2, tc, 0).xy;
    PT T = timing(i, p2);
    float c = sm(T.tcap, T.tcap + T.dcap, t)*(1. - sm(T.trel, T.trel + 0.12, t));   // quanto è posato
    float m1 = sm(T.tmor, T.tmor + T.dmor, t), m2 = sm(T.tmor2, T.tmor2 + T.dmor2, t);
    vec2 tg = mix(mix(p01.xy, p01.zw, m1), p2, m2) + tu*1.4*c;                     // posato: vibra appena con l'aria
    float fr = (1. - c)*(1. - c), c2 = c*c;
    bool rel = t > T.trel;
    float r1 = rnd(i, 1u), r2 = rnd(i, 2u), r3 = rnd(i, 3u);
    float tt = rel ? T.tau*(0.6 + 1.6*r1) : T.tau;
    float lift = rel ? -(40. + 120.*r2) : 0.;
    vec2 ac = (w + vec2(0., lift) - v)/tt*fr + (tg - x)*420.*c2 - v*40.*c2;
    if (rel && t - T.trel < dt) { v.x += 250. + 500.*r3; v.y += (r2 - 0.6)*380.; }   // strappo
    v += ac*dt; x += v*dt;
    o = vec4(x, v); return;
  }
  // transizione: la posizione non si "avvolge" mai; lo schermo è periodico solo quando si disegna
  vec2 hq = toWind(homePx(i));
  vec2 sq = texelFetch(uP2, tc, 0).xy;
  TT T = ttiming(i, hq, sq);
  vec3 ca = tattach(T, t);
  float c = min(ca.x + ca.y + ca.z, 1.);
  vec2 tg = ca.y > 0. ? sq : hq;
  // l'immagine periodica della destinazione che il granello ha davanti (mai indietro controvento)
  // l'immagine periodica più vicina, di preferenza davanti (poco controvento)
  tg.x += uWrap.x*floor((x.x - tg.x)/uWrap.x + 0.7);
  tg.y += uWrap.y*floor((x.y - tg.y)/uWrap.y + 0.5);
  tg += tu*1.2*c;
  float fr = (1. - c)*(1. - c), c2 = c*c;
  float tau = clamp(exp(log(0.07) + 0.4*gss(i, 6u)), 0.025, 0.25);
  vec2 ac = (w - v)/tau*fr + (tg - x)*520.*c2 - v*46.*c2;
  v += ac*dt; x += v*dt;
  o = vec4(x, v);
}`;

// disegno dei granelli
const DRAW_VS = COMMON + `
uniform sampler2D uState, uP2, uA, uB;
uniform int uTR; uniform float uDtF;      // campioni lungo il moto (scia) e durata del fotogramma
uniform vec2 uRes; uniform float uRS;      // bersaglio di disegno e pixel di disegno per pixel del fotogramma
uniform float uPt;                          // grandezza del punto (pixel di disegno)
uniform float uWN, uVis, uAir;              // forma: peso di un granello posato, visibilità, polvere nell'aria
uniform float uWT;                          // transizione: peso di un granello
uniform vec3 uInk; uniform float uTint, uMidDim;
uniform int uHasA, uHasB;
out float vW; out vec3 vC;
void main(){
  int id = gl_VertexID; ivec2 tc = ivec2(id % TEXW, id / TEXW); uint i = uint(id);
  vec4 st = texelFetch(uState, tc, 0);
  float q = (float(gl_InstanceID) + 0.5)/float(uTR);
  vec2 x = st.xy - st.zw*uDtF*(1. - q);
  float w = 0.; vec3 col = vec3(1.);
  vec2 p;
  if (uMode == 0) {
    if (id >= uNShape) w = (0.3 + 0.7*rnd(i, 9u))*uWN*1.1*uVis*uAir;
    else {
      PT T = timing(i, texelFetch(uP2, tc, 0).xy);
      float c = sm(T.tcap, T.tcap + T.dcap, uT)*(1. - sm(T.trel, T.trel + 0.12, uT));
      bool rel = uT > T.trel;
      float vf = rnd(i, 5u) < 0.16 ? 2.8 : 0.1;              // in volo: pochi granelli ben visibili, niente nebbia
      w = uWN*uVis*(c + (1. - c)*(rel ? max(vf, 0.6) : vf));
      if (rel) w *= 1. - sm(T.trel + 0.35, T.trel + 1.25, uT);
    }
    p = 0.5*uFrame + uS*(uDir*x.x + vec2(-uDir.y, uDir.x)*x.y);
  } else {
    vec2 hp = homePx(i), hq = toWind(hp);
    vec2 sq = texelFetch(uP2, tc, 0).xy;
    TT T = ttiming(i, hq, sq);
    vec3 ca = tattach(T, uT);
    // posati su A o B: li disegna già il fondo (la clip stessa); si disegnano quelli in volo e sulla forma
    w = uWT*clamp(1. - ca.x - ca.z, 0., 1.);
    float k = sm(T.tdep + 0.1*uD, T.tland - 0.05*uD, uT);
    vec2 uv = hp/uFrame;
    if (uMode == 2) {
      col = uInk*(0.72 + 0.56*rnd(i, 31u));
      if (x.x < -uExt.x - 30. || x.x > uExt.x + 30.) w = 0.;   // copertura: niente schermo periodico
    } else {
      vec3 cA = uHasA == 1 ? texture(uA, uv).rgb : uInk;
      vec3 cB = uHasB == 1 ? texture(uB, uv).rgb : uInk;
      col = mix(cA, cB, k);
      col = mix(col, uInk*(0.8 + 0.4*rnd(i, 31u)), uTint*4.*k*(1. - k));
      float mb = sm(uMid.y, uMid.y + 0.12*uD, uT)*(1. - sm(uMid.z, uMid.z + 0.12*uD, uT));
      if (isMid(i)) col = mix(col, uInk, max(ca.y, mb*0.6));
      else col *= 1. - uMidDim*mb;
      x.x = mod(x.x + 0.5*uWrap.x, uWrap.x) - 0.5*uWrap.x;
      x.y = mod(x.y + 0.5*uWrap.y, uWrap.y) - 0.5*uWrap.y;
    }
    p = toScreen(x);
  }
  vec2 rp = p*uRS;
  gl_Position = vec4(rp/uRes*2. - 1., 0., 1.);
  gl_PointSize = uPt;
  vW = w/float(uTR); vC = col;
  if (w <= 0.) gl_Position = vec4(2., 2., 2., 1.);
}`;

const DRAW_FS = `#version 300 es
precision highp float; precision highp int;
uniform int uMode; uniform float uPt, uSig;
in float vW; in vec3 vC; out vec4 o;
void main(){
  if (uMode == 0) {                               // polvere di luce: nucleo gaussiano, integrale 1
    vec2 d = (gl_PointCoord - 0.5)*uPt;
    float k = exp(-dot(d, d)/(2.*uSig*uSig))/(6.2831853*uSig*uSig);
    o = vec4(vW*k, 0., 0., 0.);
  } else o = vec4(vC*vW, vW);                     // granelli colorati: somma pesata dei colori
}`;

// dall'accumulo al fotogramma
const RESOLVE_FS = COMMON + `
in vec2 vUv; out vec4 o;
uniform sampler2D uAcc, uA, uB;
uniform float uDens, uGlow, uGlowLod;
uniform int uInkMode; uniform vec3 uC0, uC1, uC2; uniform vec2 uGDir; uniform vec3 uGBox;
uniform vec4 uBg; uniform int uStraight, uFlip, uHasA, uHasB;
uniform float uBlurLod, uMidDim, uCover;
vec3 inkAt(vec2 px){
  if (uInkMode == 0) return uC0;
  float t = clamp(dot(px - uGBox.xy, uGDir)/uGBox.z + 0.5, 0., 1.)*2.;
  return t < 1. ? mix(uC0, uC1, t) : mix(uC1, uC2, t - 1.);
}
void main(){
  vec2 uv = vec2(vUv.x, uFlip == 1 ? vUv.y : 1. - vUv.y);   // uv con l'origine in alto a sinistra
  vec2 px = uv*uFrame;
  vec3 rgb; float a;
  if (uMode == 0) {
    float D = texture(uAcc, uv).r*uDens;
    float L = 1. - exp(-${KEXP.toFixed(2)}*D);
    float G = 1. - exp(-${KEXP.toFixed(2)}*textureLod(uAcc, uv, uGlowLod).r*uDens);
    a = clamp(L + uGlow*G, 0., 1.);
    rgb = inkAt(px);
  } else {
    vec4 s = texture(uAcc, uv);
    float cov = 1. - exp(-2.6*s.a);
    vec3 pc = s.rgb/max(s.a, 1e-4);
    if (uMode == 2) {
      // copertura: nel momento del taglio lo schermo è pieno per forza
      float full = sm(0.40*uD, 0.47*uD, uT)*(1. - sm(0.53*uD, 0.60*uD, uT));
      a = max(cov, full*uCover);
      rgb = mix(inkAt(px), pc, cov/max(a, 1e-4));
    } else {
      // il fondo: la clip A dove il suo granello non è ancora partito, la B dove è già arrivato,
      // in mezzo una versione sfocata e scura delle due clip
      ivec2 cell = ivec2(clamp(floor(uv*vec2(uGrid)), vec2(0.), vec2(uGrid) - 1.));
      uint i = uint(cell.y*uGrid.x + cell.x);
      vec2 hq = toWind(homePx(i));
      TT T = ttiming(i, hq, vec2(0.));          // la forma a metà non tocca il fondo
      vec3 ca = tattach(T, uT);
      vec3 A = uHasA == 1 ? texture(uA, uv).rgb : vec3(0.), B = uHasB == 1 ? texture(uB, uv).rgb : vec3(0.);
      float g = sm(uTr.x + uTr.y, uTr.z + uLandF, uT);
      vec3 bA = uHasA == 1 ? textureLod(uA, uv, uBlurLod).rgb : vec3(0.), bB = uHasB == 1 ? textureLod(uB, uv, uBlurLod).rgb : vec3(0.);
      float mb = sm(uMid.y, uMid.y + 0.12*uD, uT)*(1. - sm(uMid.z, uMid.z + 0.12*uD, uT));
      vec3 back = mix(bA, bB, g)*0.8*(1. - 0.85*uMidDim*mb);
      float wA = ca.x, wB = ca.z;
      vec3 base = A*wA + B*wB + back*max(1. - wA - wB, 0.);
      rgb = mix(base, pc, cov); a = 1.;
      if (uHasA == 0 && uHasB == 0) { a = cov; rgb = pc; }
    }
  }
  if (uBg.a > 0. && a < 1.) { rgb = mix(uBg.rgb, rgb, a); a = 1.; }
  o = uStraight == 1 ? vec4(rgb, a) : vec4(rgb*a, a);
}`;

// ---- utilità WebGL ---------------------------------------------------------------------------
function compile(gl, type, src) {
  const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
  if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
    const log = gl.getShaderInfoLog(s);
    const lines = src.split('\n').map((l, k) => `${k + 1}: ${l}`).join('\n');
    throw new Error('shader: ' + log + '\n' + lines.slice(0, 200));
  }
  return s;
}
function program(gl, vs, fs) {
  const p = gl.createProgram();
  gl.attachShader(p, compile(gl, gl.VERTEX_SHADER, vs)); gl.attachShader(p, compile(gl, gl.FRAGMENT_SHADER, fs));
  gl.bindAttribLocation(p, 0, 'p'); gl.linkProgram(p);
  if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error('link: ' + gl.getProgramInfoLog(p));
  const u = {}; const n = gl.getProgramParameter(p, gl.ACTIVE_UNIFORMS);
  for (let k = 0; k < n; k++) { const info = gl.getActiveUniform(p, k); u[info.name] = gl.getUniformLocation(p, info.name); }
  return { p, u };
}
const smooth = (a, b, t) => { const q = Math.min(1, Math.max(0, (t - a)/(b - a))); return q*q*(3 - 2*q); };
export const hexRgb = h => { h = (h || '#ffffff').replace('#', ''); if (h.length === 3) h = [...h].map(c => c + c).join(''); return [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16)/255); };

// ---- il motore -------------------------------------------------------------------------------
export class DustEngine {
  constructor(canvas) {
    this.canvas = canvas;
    const gl = canvas.getContext('webgl2', { alpha: true, premultipliedAlpha: true, antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
    if (!gl) throw new Error('WebGL2 non disponibile');
    if (!gl.getExtension('EXT_color_buffer_float')) throw new Error('EXT_color_buffer_float non disponibile');
    // accumulo in float32 solo se si può sia sommare sia filtrare; altrimenti half float (va ovunque)
    this.floatBlend = !!gl.getExtension('EXT_float_blend') && !!gl.getExtension('OES_texture_float_linear');
    this.gl = gl;
    this.maxTex = gl.getParameter(gl.MAX_TEXTURE_SIZE);
    this.P = {
      init: program(gl, QUAD_VS, INIT_FS), sim: program(gl, QUAD_VS, SIM_FS),
      draw: program(gl, DRAW_VS, DRAW_FS), resolve: program(gl, QUAD_VS, RESOLVE_FS),
    };
    this.quad = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, this.quad);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    this.vao = gl.createVertexArray(); gl.bindVertexArray(this.vao);
    gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
    this.emptyVao = gl.createVertexArray();
    this.state = [null, null]; this.fbState = [null, null]; this.cur = 0;
    this.acc = null; this.accFb = null; this.accSize = [0, 0];
    this.out = null; this.outFb = null; this.outSize = [0, 0];
    this.clipTex = { A: this._tex2d(), B: this._tex2d() };
    this.has = { A: false, B: false };
    this.dataTex = { P01: null, P2: null };
    this.cfg = null; this.t = 0; this.step = 0; this.adv = 0;
    this.dummy = this._floatTex(1, 1, gl.RGBA32F, new Float32Array(4));
  }

  _tex2d() {
    const gl = this.gl, t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([0, 0, 0, 255]));
    return t;
  }
  _floatTex(w, h, fmt, data) {
    const gl = this.gl, t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    const f = fmt === gl.RG32F ? gl.RG : gl.RGBA;
    gl.texImage2D(gl.TEXTURE_2D, 0, fmt, w, h, 0, f, gl.FLOAT, data || null);
    return t;
  }
  _fb(tex) {
    const gl = this.gl, fb = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, fb);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
    return fb;
  }
  _del() {
    const gl = this.gl;
    for (const k of [0, 1]) { if (this.state[k]) gl.deleteTexture(this.state[k]); if (this.fbState[k]) gl.deleteFramebuffer(this.fbState[k]); }
    for (const k in this.dataTex) if (this.dataTex[k]) gl.deleteTexture(this.dataTex[k]);
    this.state = [null, null]; this.fbState = [null, null]; this.dataTex = { P01: null, P2: null };
  }

  // Prepara i granelli. data (da shapes.js):
  //   forma:       { n, nShape, P01: Float32Array(4n), P2: Float32Array(4n) }  posizioni nello spazio del vento
  //   transizione: { n, grid:[gw,gh], P2: Float32Array(4n) | null }             P2 = forma a metà (se c'è)
  load(cfg, data) {
    const gl = this.gl; this._del();
    this.cfg = cfg; this.data = data;
    const n = data.n, h = Math.ceil(n/TEXW);
    this.texH = h; this.n = n;
    for (const k of [0, 1]) { this.state[k] = this._floatTex(TEXW, h, gl.RGBA32F); this.fbState[k] = this._fb(this.state[k]); }
    const pad = a => { if (!a) return null; if (a.length === TEXW*h*4) return a; const b = new Float32Array(TEXW*h*4); b.set(a.subarray(0, Math.min(a.length, b.length))); return b; };
    this.dataTex.P01 = data.P01 ? this._floatTex(TEXW, h, gl.RGBA32F, pad(data.P01)) : null;
    this.dataTex.P2 = data.P2 ? this._floatTex(TEXW, h, gl.RGBA32F, pad(data.P2)) : null;
    this.reset();
  }

  // parametri che non richiedono di rifare i granelli (colore, fondo, bagliore) si cambiano al volo
  setLook(look) { this.look = look; }

  _windSpeed(t) {
    const c = this.cfg, W = c.wind;
    if (c.mode === 'forma') {
      const T = c.T;   // tempi calcolati da timeline()
      return W.strength*(330 + 650*(1 - smooth(T.gust0, T.gust1, t)) + 60*Math.sin(t*0.9)
        + (T.rel < 1e8 ? 750*Math.pow(Math.min(1, Math.max(0, (t - (T.rel - 0.1))/0.9)), 1.5) : 0));
    }
    // transizione: un giro dello schermo in 'lap' secondi, un po' più forte al centro
    const T = c.T;
    return W.strength*T.U*(1 + 0.18*Math.sin(Math.PI*Math.min(1, Math.max(0, t/c.dur))));
  }

  _common(prog) {
    const gl = this.gl, u = prog.u, c = this.cfg, T = c.T;
    const set1f = (n, v) => u[n] && gl.uniform1f(u[n], v);
    gl.uniform1i(u.uMode ?? null, c.mode === 'forma' ? 0 : c.cover ? 2 : 1);
    set1f('uT', this.t); set1f('uAdv', this.adv); set1f('uTurb', c.wind.turb); set1f('uWindU', this._windSpeed(this.t));
    u.uExt && gl.uniform2f(u.uExt, T.ex, T.ey);
    u.uFrame && gl.uniform2f(u.uFrame, c.W, c.H);
    set1f('uS', T.s);
    u.uDir && gl.uniform2f(u.uDir, Math.cos(c.wind.angle), Math.sin(c.wind.angle));
    if (c.mode === 'forma') {
      u.uNShape && gl.uniform1i(u.uNShape, this.data.nShape);
      u.uFx && gl.uniform2f(u.uFx, T.fx0, T.fxR);
      u.uCap && gl.uniform3f(u.uCap, T.cap0, T.capF, T.capR);
      u.uMor && gl.uniform4f(u.uMor, T.hold0, T.hold1, T.morK, T.morF);
      u.uRel && gl.uniform2f(u.uRel, T.rel, T.relF);
    } else {
      u.uGrid && gl.uniform2i(u.uGrid, this.data.grid[0], this.data.grid[1]);
      u.uTr && gl.uniform4f(u.uTr, T.t0, T.sweep, T.land0, T.jit);
      set1f('uLandF', T.landF);
      u.uWrap && gl.uniform2f(u.uWrap, T.wx, T.wy);
      u.uMid && gl.uniform4f(u.uMid, T.midFrac, T.midCap, T.midRel, T.midF);
      set1f('uD', c.dur);
    }
  }

  _bindData(prog, unit0) {
    const gl = this.gl, u = prog.u;
    const bind = (name, tex, k) => { if (!u[name]) return; gl.activeTexture(gl.TEXTURE0 + k); gl.bindTexture(gl.TEXTURE_2D, tex || this.dummy); gl.uniform1i(u[name], k); };
    bind('uP01', this.dataTex.P01, unit0); bind('uP2', this.dataTex.P2, unit0 + 1);
  }

  reset() {
    const gl = this.gl, P = this.P.init;
    this.t = 0; this.step = 0; this.adv = 0; this.cur = 0;
    gl.useProgram(P.p); this._common(P); this._bindData(P, 0);
    gl.bindFramebuffer(gl.FRAMEBUFFER, this.fbState[0]); gl.viewport(0, 0, TEXW, this.texH);
    gl.disable(gl.BLEND); gl.bindVertexArray(this.vao); gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  }

  // avanza la simulazione fino al tempo t (a passi fissi di 1/120 s: identica a qualsiasi fps)
  advanceTo(t) {
    const gl = this.gl, P = this.P.sim, dt = 1/SIM_HZ;
    const target = Math.round(t*SIM_HZ);
    if (target < this.step) this.reset();
    if (target === this.step) return;
    gl.useProgram(P.p); gl.disable(gl.BLEND); gl.bindVertexArray(this.vao); gl.viewport(0, 0, TEXW, this.texH);
    this._bindData(P, 1);
    gl.uniform1f(P.u.uDt, dt);
    while (this.step < target) {
      this.adv += this._windSpeed(this.t)*dt;
      this.step++; this.t = this.step*dt;
      this._common(P);
      gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, this.state[this.cur]); gl.uniform1i(P.u.uState, 0);
      gl.bindFramebuffer(gl.FRAMEBUFFER, this.fbState[1 - this.cur]);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      this.cur = 1 - this.cur;
    }
  }

  // carica il fotogramma attuale di una clip (video, immagine, VideoFrame, canvas)
  setClip(which, source) {
    const gl = this.gl;
    if (!source) { this.has[which] = false; return; }
    gl.bindTexture(gl.TEXTURE_2D, this.clipTex[which]);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, source);
    gl.generateMipmap(gl.TEXTURE_2D);
    this.has[which] = true;
  }

  _ensureAcc(w, h) {
    const gl = this.gl;
    if (this.accSize[0] === w && this.accSize[1] === h) return;
    if (this.acc) { gl.deleteTexture(this.acc); gl.deleteFramebuffer(this.accFb); }
    this.acc = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, this.acc);
    const fmt = this.floatBlend ? gl.RGBA32F : gl.RGBA16F;
    this.accFloat32 = this.floatBlend;
    const levels = Math.floor(Math.log2(Math.max(w, h))) + 1;
    gl.texStorage2D(gl.TEXTURE_2D, levels, fmt, w, h);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    this.accFb = this._fb(this.acc);
    this.accSize = [w, h];
  }

  // disegna il fotogramma al tempo attuale: sul canvas (anteprima) o in un bersaglio RGBA8 (export)
  render({ width, height, toOutput = false } = {}) {
    const gl = this.gl, c = this.cfg, L = this.look, T = c.T;
    const w = width || this.canvas.width, h = height || this.canvas.height;
    const rs = w/c.W;                                  // pixel di disegno per pixel del fotogramma
    this._ensureAcc(w, h);
    // 1) accumulo dei granelli
    gl.bindFramebuffer(gl.FRAMEBUFFER, this.accFb); gl.viewport(0, 0, w, h);
    gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
    gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE); gl.blendEquation(gl.FUNC_ADD);
    const D = this.P.draw; gl.useProgram(D.p); this._common(D);
    gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, this.state[this.cur]); gl.uniform1i(D.u.uState, 0);
    this._bindData(D, 1);
    gl.activeTexture(gl.TEXTURE3); gl.bindTexture(gl.TEXTURE_2D, this.clipTex.A); D.u.uA && gl.uniform1i(D.u.uA, 3);
    gl.activeTexture(gl.TEXTURE4); gl.bindTexture(gl.TEXTURE_2D, this.clipTex.B); D.u.uB && gl.uniform1i(D.u.uB, 4);
    D.u.uHasA && gl.uniform1i(D.u.uHasA, this.has.A ? 1 : 0); D.u.uHasB && gl.uniform1i(D.u.uHasB, this.has.B ? 1 : 0);
    const TR = c.mode === 'forma' ? (L.trail ?? 3) : (L.trail ?? 2);
    gl.uniform1i(D.u.uTR, TR); gl.uniform1f(D.u.uDtF, 1/(L.fps || 60));
    gl.uniform2f(D.u.uRes, w, h); gl.uniform1f(D.u.uRS, rs);
    const ink = hexRgb(L.ink.mode === 'solid' ? L.ink.c : L.ink.g[1]);
    gl.uniform3f(D.u.uInk, ...ink);
    let pt, sig = 0;
    if (c.mode === 'forma') {
      sig = Math.max(0.75*rs, 0.55); pt = Math.max(3, 2*Math.ceil(sig*2.6) + 1);
      const vis = smooth(0, 0.25, this.t)*(1 - smooth(c.dur - 0.5, c.dur, this.t));
      gl.uniform1f(D.u.uWN, this.data.wN); gl.uniform1f(D.u.uVis, vis); gl.uniform1f(D.u.uAir, L.air ?? 1);
    } else {
      const cell = Math.sqrt(c.W*c.H/this.n)*rs;       // grandezza di un granello in pixel di disegno
      pt = Math.max(1, Math.round(cell*(c.grain || 1.7)));
      gl.uniform1f(D.u.uWT, cell*cell/(pt*pt));
      gl.uniform1f(D.u.uTint, L.tint ?? 0.35); gl.uniform1f(D.u.uMidDim, T.midFrac > 0 ? 0.75 : 0);
    }
    gl.uniform1f(D.u.uPt, pt); D.u.uSig && gl.uniform1f(D.u.uSig, sig || 1);
    gl.bindVertexArray(this.emptyVao);
    gl.drawArraysInstanced(gl.POINTS, 0, this.n, TR);
    gl.disable(gl.BLEND);
    gl.bindTexture(gl.TEXTURE_2D, this.acc); gl.generateMipmap(gl.TEXTURE_2D);
    // 2) risoluzione: luce -> colore e trasparenza, oppure clip + granelli
    let target = null;
    if (toOutput) {
      if (this.outSize[0] !== w || this.outSize[1] !== h) {
        if (this.out) { gl.deleteTexture(this.out); gl.deleteFramebuffer(this.outFb); }
        this.out = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, this.out);
        gl.texStorage2D(gl.TEXTURE_2D, 1, gl.RGBA8, w, h); this.outFb = this._fb(this.out); this.outSize = [w, h];
      }
      target = this.outFb;
    }
    gl.bindFramebuffer(gl.FRAMEBUFFER, target); gl.viewport(0, 0, w, h);
    const R = this.P.resolve; gl.useProgram(R.p); this._common(R);
    gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, this.acc); gl.uniform1i(R.u.uAcc, 0);
    gl.activeTexture(gl.TEXTURE3); gl.bindTexture(gl.TEXTURE_2D, this.clipTex.A); R.u.uA && gl.uniform1i(R.u.uA, 3);
    gl.activeTexture(gl.TEXTURE4); gl.bindTexture(gl.TEXTURE_2D, this.clipTex.B); R.u.uB && gl.uniform1i(R.u.uB, 4);
    R.u.uHasA && gl.uniform1i(R.u.uHasA, this.has.A ? 1 : 0); R.u.uHasB && gl.uniform1i(R.u.uHasB, this.has.B ? 1 : 0);
    gl.uniform1f(R.u.uDens, rs*rs);
    R.u.uGlow && gl.uniform1f(R.u.uGlow, L.glow ?? 0.08);
    R.u.uGlowLod && gl.uniform1f(R.u.uGlowLod, Math.max(0, 3.5 + Math.log2(rs)));
    R.u.uBlurLod && gl.uniform1f(R.u.uBlurLod, 5.5);
    R.u.uMidDim && gl.uniform1f(R.u.uMidDim, T.midFrac > 0 ? 0.75 : 0);
    R.u.uCover && gl.uniform1f(R.u.uCover, 1);
    const I = L.ink;
    gl.uniform1i(R.u.uInkMode, I.mode === 'solid' ? 0 : 1);
    const cols = I.mode === 'solid' ? [I.c, I.c, I.c] : I.g;
    gl.uniform3f(R.u.uC0, ...hexRgb(cols[0])); gl.uniform3f(R.u.uC1, ...hexRgb(cols[1])); gl.uniform3f(R.u.uC2, ...hexRgb(cols[2]));
    const an = (I.angle ?? 45)*Math.PI/180; gl.uniform2f(R.u.uGDir, Math.cos(an), -Math.sin(an));
    const gb = c.gbox || [c.W/2, c.H/2, Math.min(c.W, c.H)*0.8];
    gl.uniform3f(R.u.uGBox, gb[0], gb[1], gb[2]);
    const bg = L.bg && L.bg !== 'transparent' ? [...hexRgb(L.bg), 1] : [0, 0, 0, 0];
    gl.uniform4f(R.u.uBg, ...bg);
    gl.uniform1i(R.u.uStraight, toOutput ? 1 : 0);
    gl.uniform1i(R.u.uFlip, toOutput ? 1 : 0);          // export: righe dall'alto, pronte per VideoFrame
    gl.bindVertexArray(this.vao); gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    return target;
  }

  // legge il fotogramma esportato (RGBA, righe dall'alto)
  readOutput(buf) {
    const gl = this.gl, [w, h] = this.outSize;
    gl.bindFramebuffer(gl.FRAMEBUFFER, this.outFb);
    const px = buf || new Uint8Array(w*h*4);
    gl.readPixels(0, 0, w, h, gl.RGBA, gl.UNSIGNED_BYTE, px);
    return px;
  }

  // media della luce sul fotogramma: per le prove automatiche
  probe() { const px = this.readOutput(); let s = 0; for (let k = 3; k < px.length; k += 4) s += px[k]; return s/(px.length/4)/255; }
}

// ---- tempi della forma (servono sia al motore sia all'interfaccia per la durata) ---------------
// o: { shapes: numero di forme (1-3), arrive (secondi della raffica), hold: [tenuta forma 1, forma 2],
//      final (tenuta della forma finale), morph (durata dello scivolamento), exit (true/false), stay }
export function formaTimeline(o) {
  const a = o.arrive ?? 1;                             // 1 = come l'originale
  const cap0 = 0.3*a, capF = 0.6*a, capR = 0.45*a;
  const capLast = cap0 + capF + capR;                   // l'ultimo granello comincia a posarsi
  const morK = o.morph ?? 1, morF = 0.5*a;
  const ns = o.shapes;
  const hold = o.hold || [0, 0];
  // tenuta 0 = la forma si vede solo di passaggio (come la A dell'originale)
  const hold0 = ns > 1 && hold[0] > 0 ? capLast + 0.4 + hold[0] : -1e9;
  const end1 = ns > 1 ? Math.max(capLast + 0.3, hold0 + morF + 0.15) + 0.65*morK : capLast + 0.4;
  const hold1 = ns > 2 && hold[1] > 0 ? end1 + hold[1] : -1e9;
  const end2 = ns > 2 ? Math.max(end1 + 0.3, hold1 + morF + 0.15) + 0.65*morK : end1;
  const complete = end2;
  const fin = o.final ?? 0.75;
  const rel = o.exit === false ? 1e9 : complete + fin;
  const relF = 0.8*(o.exitSpread ?? 1);
  const dur = o.exit === false ? complete + fin : rel + relF + 0.14 + 0.75;
  return { cap0, capF, capR, hold0, hold1, morK, morF, rel, relF, dur, complete, gust0: 0.9*a, gust1: 2.1*a + (complete - 2.3)*0.5 };
}

// ---- tempi della transizione -----------------------------------------------------------------
// o: { dur, W, H, s, angle, mid (forma a metà), cover (copertura senza clip) }
export function transTimeline(o) {
  const D = o.dur, ca = Math.abs(Math.cos(o.angle)), sa = Math.abs(Math.sin(o.angle));
  const ex = (ca*o.W/2 + sa*o.H/2)/o.s, ey = (sa*o.W/2 + ca*o.H/2)/o.s;
  const m = 90, wx = 2*ex + 2*m, wy = 2*ey + 2*m;
  const T = { ex, ey, wx, wy, s: o.s, t0: 0.04*D, jit: 0.03*D, midFrac: 0, midCap: 1e9, midRel: 1e9, midF: 0 };
  if (o.cover) {
    // un muro di polvere entra da sopravento, copre tutto a metà, esce sottovento
    Object.assign(T, { sweep: 0, land0: 1e9, landF: 0, U: wx*1.12/(0.5*D) });
    return T;
  }
  // partenze rapide (il fotogramma si sgretola), tutti in volo a metà, arrivi con un fronte più lento
  Object.assign(T, { sweep: 0.15*D, land0: 0.55*D, landF: 0.22*D, U: wx/(0.45*D) });
  if (o.mid) Object.assign(T, { sweep: 0.12*D, land0: 0.6*D, landF: 0.2*D, midFrac: o.midFrac ?? 0.22, midCap: 0.24*D, midRel: 0.5*D, midF: 0.08*D });
  return T;
}
