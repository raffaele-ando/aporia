# Aporia — apertura del sito

Animazione d'ingresso del sito, circa 5 secondi. Un solo vento, continuo, da sinistra verso
destra: porta la polvere dal nero e la deposita granello per granello; mentre arriva la polvere
passa dalla forma della A e scivola, sempre nel verso del vento, fino al logo dust definitivo,
che è il momento più pieno. Poi il vento rinforza e lo porta via, da sinistra a destra, e resta
la home, che per ora mostra solo la scritta **Aporia**.

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

La polvere è una simulazione fatta in anticipo (`src/sim_video.py`), con circa 450.000 granelli.
- **Il vento** è un unico flusso continuo, con vortici senza divergenza (come l'aria vera) che
  viaggiano insieme all'aria; verso la fine rinforza.
- **Ogni granello ha una sola destinazione nel logo definitivo.** Mentre si posa, la sua
  destinazione scivola dalla A al logo nel verso del vento (abbinamento "sottovento" tra la A e il
  logo). La lettera non si divide in parti e la A non si ferma mai: si vede solo di passaggio.
- **La luce del logo finale** è calibrata per essere esattamente quella del logo dust. I granelli
  posati continuano a vibrare appena con l'aria.
- **All'uscita** ogni granello parte quando il fronte del vento lo raggiunge, con il suo peso.

Riprodurre un video lo sa fare qualsiasi dispositivo: fluido ovunque, identico su Android, iPhone,
iPad e computer. Pesi: verticale 1 MB (MP4) / 0,4 MB (WebM), orizzontale 0,6 / 0,25 MB.

- **Schermo sempre pieno, niente bande nere**: il video riempie lo schermo (si ritaglia ai lati o
  sopra/sotto) e il logo sta nella zona centrale, che resta intera su qualsiasi proporzione,
  da un telefono lungo a uno schermo ultrawide (`preview/formati-schermo.png`).
- La pagina sceglie da sola il video verticale o orizzontale e il formato adatto al browser
  (H.264 per Safari, iPad, Android, Chrome; WebM VP9 dove H.264 non c'è).
- La home compare mentre l'ultima polvere si sta ancora disperdendo.
- Tocco, click o un tasto durante il video: si salta alla home. Doppio click su "Aporia": si rivede.
- Se il video non parte (per esempio in risparmio energetico su iPhone) si va comunque alla home
  dopo 2,5 secondi. Con "riduci movimento" attivo si va direttamente alla home.

## Come si rigenera

1. `python src/render_logo.py` — fotografa il logo dust (`../agora_loghi_svg`).
2. `python src/prep_morph.py` — prepara la forma della A e il logo come immagini.
3. `python src/sim_video.py portrait` e `python src/sim_video.py landscape` — simulazione e video
   già compressi per il web (circa 7 minuti ciascuno; `--preview` per una prova veloce).
4. `python src/build.py` — rigenera `index.html` (e `intro-canvas.html`).

In `src/sim_video.py` si regolano i tempi di ogni granello (`tcap` quando si posa, `tmor` quando
scivola dalla A al logo, `trel` quando il vento se lo riprende), il vento (`wind_speed`, `OCT`),
la grandezza del logo nell'inquadratura (`BOX`) e il numero di granelli.
