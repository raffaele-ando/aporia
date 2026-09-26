# Aporia — apertura del sito

Animazione d'ingresso del sito, circa 4,7 secondi. Un solo vento da sinistra verso destra: una
raffica rapida porta la polvere dal nero e la sbatte sul logo granello per granello; mentre arriva la polvere
passa dalla forma della A e scivola, sempre nel verso del vento, fino al logo dust definitivo,
che è il momento più pieno. Poi il vento rinforza e lo porta via, da sinistra a destra, e resta
la home, che per ora mostra solo la scritta **Aporia**.

**Sito:** https://raffaele-ando.github.io/aporia/ — un solo link per tutto:

| Pagina | Cosa c'è |
|---|---|
| [Home](https://raffaele-ando.github.io/aporia/) | l'apertura (versione 10), poi la home "Aporia"; in basso i link alle altre pagine |
| [Versioni](https://raffaele-ando.github.io/aporia/versioni.html) | tutte le animazioni di apertura fatte finora, da toccare in alto |
| [Laboratorio](https://raffaele-ando.github.io/aporia/laboratorio.html) | lo strumento completo: la polvere calcolata dal vivo nel browser; forme e scritte, transizioni tra clip, teoria dei colori, export dei video |
| [Download](https://raffaele-ando.github.io/aporia/download.html) | tutti i file pronti, con l'anteprima e quale usare in quale app |

Il sito è pubblicato da GitHub Pages dal ramo `gh-pages`, che l'azione `.github/workflows/sito.yml`
riallinea a `main` a ogni push: basta lavorare su `main`.

## File

| File | Cosa contiene |
|---|---|
| `index.html` | la home: video d'apertura, poi "Aporia" e i link alle altre pagine |
| `versioni.html` | il selettore di tutte le versioni |
| `laboratorio.html` | prova colori, fondi e formati; anteprima come transizione tra due clip |
| `download.html` | i file pronti da scaricare (letti da `export/pacchetto.json`) |
| `assets/sito.css` | la barra di navigazione comune alle pagine |
| `assets/intro-portrait.mp4` / `.webm` | video verticale 1080×1920 (telefoni, tablet in verticale) |
| `assets/intro-landscape.mp4` / `.webm` | video orizzontale 1920×1080 (computer, tablet in orizzontale) |
| `versioni/` | tutte le animazioni di apertura fatte finora: pagine originali v1–v7 e video di tutte in `media/` |
| `intro-canvas.html` | versione precedente, calcolata dal vivo nel browser (tenuta come riferimento) |
| `preview/` | fotogrammi di controllo (telefono e desktop) |
| `export/` | l'animazione pronta da usare in video, social e presentazioni (vedi sotto) |
| `src/master/` | la simulazione v10 salvata come "luce" (bianco su nero, 60 fps): la base di ogni export |
| `loghi/` | i loghi di Aporia in SVG (pulito, polvere, inverso, tracciato fedele), il laboratorio `aporia-dust-lab.html` e gli script che li generano, con tutto il loro storico: vedi `loghi/README.md` |
| `src/` | script che generano tutto |

## Laboratorio (tutto nel browser)

`laboratorio.html` + `assets/studio/`: la stessa fisica di `src/sim_video.py` calcolata dalla scheda
grafica (WebGL2), quindi ogni modifica si vede subito e si scarica senza Python.

- **Forma e scritte**: fino a 3 forme in fila (la A, il logo, una scritta con qualsiasi carattere,
  anche caricato, o un'immagine PNG/SVG/foto). Ogni forma ha grandezza, posizione e tenuta (0 = solo
  di passaggio, come la A originale); tra una forma e l'altra i granelli scivolano sottovento.
- **Transizione tra clip**: ogni pixel della clip A è un granello (fino a 8 milioni), il vento li
  porta su tutto lo schermo e li posa nella clip B; a metà la polvere può formare la A, il logo o una
  scritta. Oppure "muro di polvere" senza clip, che copre tutto lo schermo nel momento del taglio.
- **Teoria dei colori** (`colors.js`, OKLCH): dal fondo i colori migliori per la polvere, o dalla
  polvere i fondi più compatibili, per 8 teorie, con il contrasto WCAG.
- **Export** (`exporter.js`, Mediabunny + fflate in `assets/vendor/`): MP4 H.264, WebM VP9 con
  trasparenza, ZIP di PNG trasparenti; 720p–1440p, 30/60 fps, fotogrammi esatti.
- Le impostazioni si salvano da sole; progetti con nome, link e file `.json`.

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

**Come transizione:** metti l'animazione a cavallo del taglio e passa dalla clip A alla clip B
intorno a 1,4 s, quando la raffica ha portato la polvere al centro; il logo poi vola via sopra la clip nuova.

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

Il modo più semplice: nel [laboratorio](https://raffaele-ando.github.io/aporia/laboratorio.html) scegli
colore, fondo e formato e guarda l'anteprima (anche come transizione tra due clip). Se quel file è già
pronto compare il pulsante per scaricarlo, altrimenti c'è il comando da copiare.
`python src/pack.py` rifà tutto il pacchetto di `export/` con le anteprime e `export/pacchetto.json`.

- La trasparenza nasce dalla luce della polvere: dove la polvere è piena il colore è pieno, dove
  è rada è semitrasparente, quindi i bordi restano morbidi su qualsiasi fondo.
- I `.mov` pesano 35–45 MB (ProRes 4444, 30 fps, trasparenza a 8 bit come la luce di partenza).
- I file trasparenti non hanno fondo: in un'anteprima con fondo bianco (per esempio su iPhone) la
  polvere bianca non si vede, e il WebM su iPhone può mostrare solo il bianco. Nei programmi di
  montaggio stanno sopra le clip; nella pagina Download sono mostrati sopra una scacchiera.
- Non c'è una versione HEVC con trasparenza (quella che usano iPhone e iMovie): lo strumento
  usato qui non la sa creare. Su iPhone si usa l'MP4 su nero con la fusione Scherma.

## Selettore delle animazioni (versioni.html)

In alto c'è una fila di pulsanti, uno per ogni animazione di apertura fatta finora (01–10, la
● è quella attuale), tutti visibili insieme senza dover scorrere. Toccandone uno parte subito a
tutto schermo e sotto i pulsanti compare una riga che la descrive; per le v1–v7 c'è anche il link
all'originale animato dal vivo.

Tutte le versioni sono video, perché così si riproducono uguali ovunque, anche sui telefoni vecchi:
- **v1–v7** erano animate dal vivo nel browser: `src/record_versions.py` le registra fotogramma
  per fotogramma a 60 fps, con l'orologio del browser fermo e fatto avanzare a mano, a partire
  dalle pagine originali recuperate dallo storico git (`versioni/v*.html`; `src/build_versions.py`
  le aveva estratte dal repository personale in cui il progetto è nato, e sono già salvate qui).
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
  dopo 4 secondi. Con "riduci movimento" attivo si va direttamente alla home.

## Come si rigenera

1. `python src/render_logo.py` — fotografa il logo dust (`loghi/aporia-logo-dust-static.svg`).
2. `python src/prep_morph.py` — prepara la forma della A e il logo come immagini.
3. `python src/sim_video.py portrait` e `python src/sim_video.py landscape` — simulazione e video
   già compressi per il web (circa 7 minuti ciascuno; `--preview` per una prova veloce).
   Scrivono anche i master in `src/master/`.
4. `python src/pack.py` — rifà i file pronti di `export/` nei vari colori e formati.
5. `python src/build.py` — rigenera `intro-canvas.html` (le altre pagine si modificano direttamente).

In `src/sim_video.py` si regolano i tempi di ogni granello (`tcap` quando si posa, `tmor` quando
scivola dalla A al logo, `trel` quando il vento se lo riprende), il vento (`wind_speed`, `OCT`),
la grandezza del logo nell'inquadratura (`BOX`) e il numero di granelli.
