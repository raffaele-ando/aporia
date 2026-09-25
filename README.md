# Aporia — apertura del sito

Animazione d'ingresso del sito, circa 5 secondi: dal nero il vento porta la polvere, che si posa
e costruisce una A pulita; una raffica la attraversa, solleva la polvere del fiume e la trascina
nella bandiera (il resto vola via), fino a ottenere il logo dust; l'ultima raffica lo porta via
e resta la home, che per ora mostra solo la scritta **Aporia**.

## File

| File | Cosa contiene |
|---|---|
| `index.html` | la pagina: video d'apertura, poi la home "Aporia" |
| `assets/intro-portrait.mp4` / `.webm` | video verticale 1080×1920 (telefoni, tablet in verticale) |
| `assets/intro-landscape.mp4` / `.webm` | video orizzontale 1920×1080 (computer, tablet in orizzontale) |
| `intro-canvas.html` | versione precedente, calcolata dal vivo nel browser (tenuta come riferimento) |
| `preview/` | fotogrammi di controllo (telefono e desktop) |
| `src/` | script che generano tutto |

## Perché un video

La polvere è una vera simulazione fisica fatta in anticipo (`src/sim_video.py`): circa 450.000
granelli spinti da un vento turbolento (raffiche che attraversano lo schermo più vortici senza
divergenza, come l'aria vera), ognuno con il suo peso. Nessun telefono potrebbe calcolarla dal vivo,
ma riprodurre un video lo sa fare qualsiasi dispositivo: fluido ovunque, identico su Android,
iPhone, iPad e computer. Ogni video pesa circa 2,5 MB (H.264) o 1,7 MB (WebM).

- La pagina sceglie da sola il video verticale o orizzontale e il formato adatto al browser
  (H.264 per Safari, iPad, Android, Chrome; WebM VP9 dove H.264 non c'è).
- La home compare mentre l'ultima polvere si sta ancora disperdendo.
- Tocco, click o un tasto durante il video: si salta alla home. Doppio click su "Aporia": si rivede.
- Se il video non parte (per esempio in risparmio energetico su iPhone) si va comunque alla home
  dopo 2,5 secondi. Con "riduci movimento" attivo si va direttamente alla home.

## Come si rigenera

1. `python src/render_logo.py` — fotografa il logo dust (`../agora_loghi_svg`).
2. `python src/prep_morph.py` — prepara la A pulita e la divisione del logo (polvere che resta /
   polvere che arriva col vento).
3. `python src/sim_video.py portrait` e `python src/sim_video.py landscape` — simulazione e video
   (circa 4 minuti ciascuno; `--preview` per una prova veloce a metà risoluzione).
4. Compressione per il web: vedi i comandi `ffmpeg` in fondo a questo file.
5. `python src/build.py` — rigenera `index.html` (e `intro-canvas.html`).

In `src/sim_video.py` si regolano i tempi (`tc` A pulita, `tv_` raffica del fiume, `te` uscita),
le raffiche (`GUSTS`), la turbolenza (`OCT`, `amp`) e il numero di granelli.

```
ffmpeg -i master.mp4 -c:v libx264 -preset veryslow -crf 29 -pix_fmt yuv420p -movflags +faststart -an intro-portrait.mp4
ffmpeg -i master.mp4 -c:v libvpx-vp9 -b:v 0 -crf 52 -row-mt 1 -pix_fmt yuv420p -an intro-portrait.webm
```
