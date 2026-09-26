// Esporta i fotogrammi del motore in un file, tutto nel browser (niente server, niente Python):
//   mp4   H.264 su fondo pieno: va in ogni app (CapCut, InShot, Instagram, TikTok, PowerPoint...)
//   webm  VP9 con trasparenza: Canva, siti web, OBS, Premiere/DaVinci (con il plug-in WebM)
//   png   sequenza di PNG trasparenti in uno ZIP: Premiere, After Effects, Final Cut, DaVinci
// I video si codificano con WebCodecs (tramite Mediabunny); dove WebCodecs manca si registra
// l'anteprima in tempo reale con MediaRecorder.
import * as MB from '../vendor/mediabunny.min.mjs';
import { Zip, ZipPassThrough } from '../vendor/fflate.mjs';

export async function support(w = 1080, h = 1920) {
  const wc = typeof VideoEncoder !== 'undefined';
  const out = { webcodecs: wc, mp4: false, webm: false, png: typeof OffscreenCanvas !== 'undefined', recorder: typeof MediaRecorder !== 'undefined' };
  if (wc) {
    try { out.mp4 = await MB.canEncodeVideo('avc', { width: w, height: h, bitrate: 8e6 }); } catch (e) {}
    try { out.webm = await MB.canEncodeVideo('vp9', { width: w, height: h, bitrate: 8e6, alpha: 'keep' }); } catch (e) {}
    if (!out.webm) try { out.webmOpaque = await MB.canEncodeVideo('vp9', { width: w, height: h, bitrate: 8e6 }); } catch (e) {}
  }
  return out;
}

// frame(i) -> Promise<Uint8Array RGBA, righe dall'alto>; ritorna { blob, name }
export async function encode({ kind, w, h, fps, frames, frame, onProgress, signal, name }) {
  const check = () => { if (signal && signal.aborted) throw new DOMException('annullato', 'AbortError'); };
  if (kind === 'png') return encodePng({ w, h, frames, frame, onProgress, check, name });
  const isMp4 = kind === 'mp4';
  const output = new MB.Output({
    format: isMp4 ? new MB.Mp4OutputFormat({ fastStart: 'in-memory' }) : new MB.WebMOutputFormat(),
    target: new MB.BufferTarget(),
  });
  // la polvere è piena di dettaglio fine: serve un bitrate alto per non impastarla
  const bitrate = Math.round(Math.min(40e6, w*h*fps*(isMp4 ? 0.16 : 0.12)));
  const src = new MB.VideoSampleSource({ codec: isMp4 ? 'avc' : 'vp9', bitrate, keyFrameInterval: 1, alpha: isMp4 ? 'discard' : 'keep', latencyMode: 'quality' });
  output.addVideoTrack(src, { frameRate: fps });
  await output.start();
  for (let i = 0; i < frames; i++) {
    check();
    const px = await frame(i);
    const s = new MB.VideoSample(px, { format: 'RGBA', codedWidth: w, codedHeight: h, timestamp: i/fps, duration: 1/fps });
    await src.add(s); s.close();
    onProgress && onProgress((i + 1)/frames);
  }
  await output.finalize();
  const type = isMp4 ? 'video/mp4' : 'video/webm';
  return { blob: new Blob([output.target.buffer], { type }), name: `${name}.${isMp4 ? 'mp4' : 'webm'}` };
}

async function encodePng({ w, h, frames, frame, onProgress, check, name }) {
  const parts = [];
  let done, fail; const finished = new Promise((a, b) => { done = a; fail = b; });
  const zip = new Zip((err, dat, final) => { if (err) return fail(err); parts.push(dat); if (final) done(); });
  const cv = new OffscreenCanvas(w, h), g = cv.getContext('2d');
  for (let i = 0; i < frames; i++) {
    check();
    const px = await frame(i);
    g.putImageData(new ImageData(new Uint8ClampedArray(px.buffer, px.byteOffset, w*h*4), w, h), 0, 0);
    const png = new Uint8Array(await (await cv.convertToBlob({ type: 'image/png' })).arrayBuffer());
    const f = new ZipPassThrough(`${name}/${name}-${String(i).padStart(4, '0')}.png`);
    zip.add(f); f.push(png, true);
    onProgress && onProgress((i + 1)/frames);
  }
  zip.end(); await finished;
  return { blob: new Blob(parts, { type: 'application/zip' }), name: `${name}-png.zip` };
}

// ripiego senza WebCodecs: registra il canvas in tempo reale
export async function record({ canvas, fps, seconds, drawAt, onProgress, signal, name }) {
  const types = ['video/mp4;codecs=avc1', 'video/mp4', 'video/webm;codecs=vp9', 'video/webm'];
  const mime = types.find(t => MediaRecorder.isTypeSupported(t)) || '';
  const stream = canvas.captureStream(fps);
  const rec = new MediaRecorder(stream, { mimeType: mime, videoBitsPerSecond: 16e6 });
  const chunks = []; rec.ondataavailable = e => e.data.size && chunks.push(e.data);
  const stopped = new Promise(r => rec.onstop = r);
  rec.start();
  const t0 = performance.now();
  await new Promise(res => {
    const tick = () => {
      const t = (performance.now() - t0)/1000;
      if (t >= seconds || (signal && signal.aborted)) return res();
      drawAt(t); onProgress && onProgress(t/seconds); requestAnimationFrame(tick);
    };
    tick();
  });
  rec.stop(); await stopped; stream.getTracks().forEach(t => t.stop());
  const ext = mime.includes('mp4') ? 'mp4' : 'webm';
  return { blob: new Blob(chunks, { type: mime || 'video/webm' }), name: `${name}.${ext}` };
}

// ---- le clip della transizione (video o immagini) -------------------------------------------
// anteprima: un <video> che scorre; export: fotogrammi esatti decodificati con Mediabunny
export class Clip {
  static async fromFile(file) {
    const c = new Clip(); c.file = file; c.name = file.name;
    c.url = URL.createObjectURL(file);
    if (file.type.startsWith('image/')) {
      c.kind = 'image';
      c.img = await new Promise((res, rej) => { const im = new Image(); im.onload = () => res(im); im.onerror = () => rej(new Error('Immagine non leggibile')); im.src = c.url; });
      c.duration = Infinity;
    } else {
      c.kind = 'video';
      const v = document.createElement('video');
      v.muted = true; v.playsInline = true; v.preload = 'auto'; v.src = c.url;
      await new Promise((res, rej) => { v.onloadeddata = res; v.onerror = () => rej(new Error('Video non leggibile in questo browser')); });
      c.video = v; c.duration = v.duration || 0;
    }
    return c;
  }
  // disegna il fotogramma "a riempire" (come object-fit: cover) in un canvas w×h
  _cover(src, sw, sh, w, h) {
    if (!this.cv || this.cv.width !== w || this.cv.height !== h) { this.cv = document.createElement('canvas'); this.cv.width = w; this.cv.height = h; this.g = this.cv.getContext('2d'); }
    const k = Math.max(w/sw, h/sh), dw = sw*k, dh = sh*k;
    this.g.drawImage(src, (w - dw)/2, (h - dh)/2, dw, dh);
    return this.cv;
  }
  // anteprima: tiene il video vicino al tempo t (secondi della clip) e ne ritorna il fotogramma
  previewFrame(t, w, h, rate = 1) {
    if (this.kind === 'image') return this._cover(this.img, this.img.naturalWidth, this.img.naturalHeight, w, h);
    const v = this.video, tt = Math.min(Math.max(0, t), Math.max(0, this.duration - 0.05));
    if (Math.abs(v.currentTime - tt) > 0.25 || (v.paused && t < this.duration - 0.05)) {
      if (Math.abs(v.currentTime - tt) > 0.25) v.currentTime = tt;
      if (rate > 0) { v.playbackRate = rate; if (t >= 0 && t < this.duration - 0.05) v.play().catch(() => {}); }
    }
    if (t >= this.duration - 0.05 || t < 0) v.pause();
    if (v.readyState < 2) return this.cv || null;
    return this._cover(v, v.videoWidth, v.videoHeight, w, h);
  }
  pause() { if (this.video) this.video.pause(); }
  // export: il fotogramma esatto al tempo t
  async exactFrame(t, w, h) {
    if (this.kind === 'image') return this._cover(this.img, this.img.naturalWidth, this.img.naturalHeight, w, h);
    if (!this.sink || this.sinkSize !== w + 'x' + h) {
      this.input = new MB.Input({ source: new MB.BlobSource(this.file), formats: MB.ALL_FORMATS });
      const track = await this.input.getPrimaryVideoTrack();
      if (!track || !(await track.canDecode())) throw new Error(`Non riesco a leggere i fotogrammi di “${this.name}” in questo browser`);
      this.sink = new MB.CanvasSink(track, { width: w, height: h, fit: 'cover', poolSize: 2 });
      this.sinkSize = w + 'x' + h;
      this.first = await track.getFirstTimestamp?.() ?? 0;
    }
    const tt = Math.min(Math.max(0, t), Math.max(0, this.duration - 1/120)) + (this.first || 0);
    const r = await this.sink.getCanvas(tt);
    return r ? r.canvas : this.cv;
  }
  dispose() { this.pause(); URL.revokeObjectURL(this.url); }
}
