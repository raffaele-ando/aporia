# Aporia — apertura del sito

Animazione d'ingresso del sito, circa 4,7 secondi. Un solo vento da sinistra verso destra: una
raffica rapida porta la polvere dal nero e la sbatte sul logo granello per granello; mentre arriva la polvere
passa dalla forma della A e scivola, sempre nel verso del vento, fino al logo dust definitivo,
che è il momento più pieno. Poi il vento rinforza e lo porta via, da sinistra a destra, e resta
la home, che per ora mostra solo la scritta **Aporia**.

## File

| File | Cosa contiene |
|---|---|
| `index.html` | la pagina: video d'apertura, poi la home "Aporia" |
| `assets/intro-portrait.mp4` / `.webm` | video verticale 1080×1920 (telefoni, tablet in verticale) |
| `assets/intro-landscape.mp4` / `.webm` | video orizzontale 1920×1080 (computer, tablet in orizzontale) |
| `versioni/` | tutte le animazioni di apertura fatte finora: pagine originali v1–v7 e video di tutte in `media/` |
| `intro-canvas.html` | versione precedente, calcolata dal vivo nel browser (tenuta come riferimento) |
| `preview/` | fotogrammi di controllo (telefono e desktop) |
| `laboratorio.html` | prova colori, fondi e formati; anteprima come transizione tra due clip |
| `export/` | l'animazione pronta da usare in video, social e presentazioni (vedi sotto) |
| `src/master/` | la simulazione v10 salvata come "luce" (bianco su nero, 60 fps): la base di ogni export |
| `src/` | script che generano tutto |

## Usare l'animazione fuori dal sito

La versione 10 si può usare da sola in un video, come transizione tra clip sui social o in una
presentazione, con il colore che vuoi e senza fondo nero. I file pronti sono in `export/`
(nome: `aporia-intro-<formato>-<colore>-<tipo>`):

| Dove la usi | File | Come |
|---|---|---|
| CapCut, InShot, app sul telefono | `…-ffffff-su-nero.mp4` | mettila sopra la clip come sovrapposizione, fusione **Scherma** (o Schiarisci): il nero sparisce |
| Stesse app, su fondo chiaro | `…-101014-su-f2efe9.mp4` | fusione **Moltiplica**: sparisce il chiaro, resta la polvere scura |
| Premiere, Final Cut, DaVinci, After Effects, Keynote, CapCut desktop | `…-trasparente.mov` | ProRes 4444 con trasparenza vera, 30 fps; basta metterla sopra |
| Canva, siti web, OBS | `…-trasparente.webm` | WebM VP9 con trasparenza, leggero |
| PowerPoint, Google Presentazioni | `…-su-nero.mp4` | su una slide nera (non gestiscono i video trasparenti) |

**Come transizione:** la polvere copre di più intorno a 1,4 s; taglia lì dalla clip A alla clip B
e il passaggio resta nascosto dietro il logo che si forma e poi vola via.

Formati: 9:16 (Reel, Storie, TikTok), 4:5 e 1:1 (post), 16:9 (YouTube, presentazioni). Ci sono già
bianco, scuro `#101014` e un gradiente arancio-rosa-blu.

**Altri colori** senza rifare la simulazione:

```
python src/export.py --color "#d9b56a" --format 9:16
python src/export.py --gradient "#ff8a3d,#ff2e63,#4d5bff" --angle 45 --format 16:9
python src/export.py --color "#101014" --bg "#f2efe9" --types mp4
python src/export.py --types mov --fps 30        # per i programmi di montaggio
python src/export.py --types png                 # sequenza di PNG trasparenti
```

Il modo più semplice: apri `laboratorio.html`, scegli colore, fondo e formato, guarda l'anteprima
(anche come transizione tra due clip) e copia il comando che compare in fondo.

- La trasparenza nasce dalla luce della polvere: dove la polvere è piena il colore è pieno, dove
  è rada è semitrasparente, quindi i bordi restano morbidi su qualsiasi fondo.
- I `.mov` pesano 70–95 MB e non sono nel repository (`.gitignore`): si rigenerano con
  `python src/export.py --types mov --fps 30 --format 9:16` (e `16:9`).
- Non c'è una versione HEVC con trasparenza (quella che usano iPhone e iMovie): lo strumento
  usato qui non la sa creare. Su iPhone si usa l'MP4 su nero con la fusione Scherma.

## Selettore delle animazioni

In alto c'è una fila di pulsanti, uno per ogni animazione di apertura fatta finora (01–10, la
● è quella attuale), tutti visibili insieme senza dover scorrere. Toccandone uno parte subito a
tutto schermo e sotto i pulsanti compare una riga che la descrive.

Tutte le versioni sono video, perché così si riproducono uguali ovunque (la pagina in cui gira il
sito non permette di incorporare altre pagine):
- **v1–v7** erano animate dal vivo nel browser: `src/record_versions.py` le registra fotogramma
  per fotogramma a 60 fps, con l'orologio del browser fermo e fatto avanzare a mano, a partire
  dalle pagine originali recuperate dallo storico git (`src/build_versions.py` → `versioni/v*.html`).
  La v1 è molto lenta da registrare (circa 40 minuti) perché ricalcola i filtri SVG del logo.
- **v8–v9** sono i video precedenti; **v10** è quello attuale (`assets/`).
- I video in `versioni/media/` sono solo MP4 (H.264: iPhone, iPad, Android, Chrome, Safari).

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
iPad e computer. Pesi: verticale 0,6 MB (MP4) / 0,25 MB (WebM), orizzontale 0,4 / 0,16 MB.

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
