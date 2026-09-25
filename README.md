# Agorà — loghi SVG

Ricostruzione vettoriale dei due loghi Agorà a partire dalle immagini caricate.
SVG puri: nessuna immagine raster incorporata, nessuna dipendenza esterna.

## File

| File | Cosa contiene |
|---|---|
| `agora-logo.svg` | Logo pulito, lettera corretta. Ritagliato sulla forma, fondo trasparente, `fill="currentColor"` |
| `agora-logo-dust.svg` | Versione polvere, animata, **fondo trasparente** e colore/gradiente liberi (1254×1254) |
| `agora-logo-dust-static.svg` | Come sopra ma senza animazioni (stampa, export) |
| `agora-logo-dust-inverted.svg` | Versione polvere già impostata scura su fondo chiaro |
| `agora-logo-dust-tight.svg` | Versione polvere ritagliata sulla forma |
| `agora-logo-tracciato-fedele.svg` | Tracciato fedele al pixel dell'immagine caricata (senza correzione della lettera) |
| `agora-dust-lab.html` | Laboratorio: colore, gradiente, polarità, polvere e animazioni dal vivo, con export |
| `preview/` | Anteprime PNG e tavola di costruzione |

## 1. La lettera prima di tutto

La A è costruita con uno scheletro esattamente simmetrico rispetto all'asse centrale
(tavola in `preview/costruzione.png`). Valori nel file `agora-logo.svg`:

| Elemento | Sinistra | Destra |
|---|---|---|
| base | a 0° (tutti i punti a y = 671,870) | a 0° |
| cima | a 0° (y = 0), larga 151,20 | — |
| cima: distanza dall'asse | 75,600 | 75,600 |
| piede: larghezza | 170,037 | 170,037 |
| piede: bordo esterno dall'asse | 401,375 | 401,375 |
| piede: bordo interno dall'asse | 231,338 | 231,338 |
| angolo del diagonale esterno | 64,13° | 64,13° |
| spessore dell'asta (perpendicolare) | 153 | 153 |

Rispetto all'immagine di partenza sono state corrette due cose che si misuravano:
la gamba destra si svasava ed era più spessa (157→165 contro 152), e la cima era
spostata di 15,6 a destra rispetto al centro della base, per cui la lettera sembrava
inclinata. Ora cima, piedi, angoli e spessori sono identici dalle due parti.
Il fiume e la "bandiera" a destra restano asimmetrici: sono il disegno del logo.

La stessa lettera è usata sotto la polvere (anche lì base e cima a 0° e simmetria
dall'asse, verificate sul file).

Se ti serve il disegno esattamente com'era nell'immagine caricata, usa
`agora-logo-tracciato-fedele.svg`.

## 2. Colore, gradiente, trasparenza

La versione dust non è più "grigi su fondo nero": il disegno è una **maschera**
(il chiaroscuro diventa canale alpha) e sopra ci passi il colore che vuoi.

```html
<!-- bianco su fondo trasparente: funziona su qualsiasi sfondo scuro -->
<div style="background:#12141a">…svg incollato…</div>

<!-- tinta piatta -->
<style> #agoraDustLogo { --ink: #ff4d2e; } </style>

<!-- gradiente a 3 colori (già presente nel file) -->
<style> #agoraDustLogo { --ink: url(#agoraGradient); --c1:#ff8a3d; --c2:#ff2e63; --c3:#4d5bff; } </style>

<!-- da chiaro-su-scuro a scuro-su-chiaro: una riga -->
<style> #agoraDustLogo { --mask: url(#agoraMaskDark); --ink:#101014; --bg:#f2efe9; } </style>
```

| Variabile | Cosa fa | Default |
|---|---|---|
| `--ink` | colore del logo: tinta piatta o `url(#agoraGradient)` (o un tuo gradiente) | `#ffffff` |
| `--bg` | fondo: `transparent`, un colore, o un altro paint | `transparent` |
| `--mask` | polarità: `url(#agoraMaskLight)` chiaro su scuro, `url(#agoraMaskDark)` scuro su chiaro | light |
| `--c1` `--c2` `--c3` | i tre colori del gradiente pronto | arancio/rosa/blu |
| `--glow` | 0…1.5 intensità dell'alone sui bordi | `1` |
| `--dust` | 0 = superficie pulita, 1 = polvere piena | `1` |

Il gradiente è un normale `<linearGradient id="agoraGradient">`: puoi cambiarne i colori,
l'angolo, o sostituirlo con un gradiente radiale o conico tuo.

## 3. La polvere: com'è fatta e cosa toccare

Strati, tutti vettoriali:

1. **Campo luminoso** (`#agoraFieldRaw`): 45 tracciati annidati (isolivelli), fitti sia nelle
   ombre sia nei bianchi così le sfumature non fanno gradini, ammorbiditi da `#agoraSoften`.
   È la "luce" del logo.
2. **Sagoma** (`#agoraEdgeSource` → `#agoraSurface`): la lettera (rosso) più una mappa di
   morbidezza del bordo (verde). Il filtro `#agoraEdge` rende il bordo netto su lati, cima e base
   e sempre più sfumato verso fiume e bandiera, senza salti: dove il lato della cima entra
   nella bandiera il bordo curva e si scioglie piano, invece di fare un angolo.
3. **Alone** (`#agoraGlowField`): la frangia luminosa che esce dalla sagoma, sfocata da `#agoraBloom`.
4. **Mappe** (`#agoraGrainMap`, `#agoraDragMap`): dicono al filtro quanta grana mettere e dove
   la polvere è trascinata. L'intensità è misurata sull'originale: grana piena sul corpo della A,
   polvere liscia e a scie nel fiume.
5. **Motore polvere** (`#agoraDustFx`): il filtro che genera e muove la polvere.

| Nodo / attributo | Effetto |
|---|---|
| `#agoraGrainNoise` `baseFrequency` | dimensione del grano: più basso = grana più grossa |
| `#agoraGrainNoise` `numOctaves` / `seed` | ricchezza della grana / disegno della grana a parità di statistica |
| `feColorMatrix result="grain"` | il primo numero della matrice è l'**intensità** della grana (1.8) |
| `#agoraStreakNoise` `baseFrequency` | forma delle scie (x basso = scie lunghe, y alto = scie sottili) |
| `feColorMatrix result="streak"` | intensità delle scie (1.2) |
| `#agoraSweep` `scale` | quanto la grana viene piegata e trascinata dal flusso |
| `#agoraGrainMapBlur` `stdDeviation` | morbidezza del passaggio tra zone granulose e zone lisce |
| `#agoraSpeckNoise` + `slope`/`intercept` | dimensione, densità e soglia dei granelli sparsi |
| `#agoraSpeckGain` `slope` | luminosità dei granelli (0 = spenti) |
| `#agoraHalo` `stdDeviation` | quanto i granelli si disperdono oltre la luce (solo nella zona morbida) |
| `#agoraDisplace` `scale` | turbolenza che deforma il logo (0 fermo · 3-6 respiro · 20+ dissolve) |
| `#agoraFlowNoise` `baseFrequency` | scala del vortice di flusso |
| `#agoraGrainShift` `dx`/`dy` · `#agoraStreakShift` `dx` | scorrimento di grana e scie |
| `#agoraTone` `tableValues` | curva di tono (esposizione/contrasto): nero e bianco restano fermi, il fondo resta trasparente |
| `#agoraHighlight` `tableValues` | quanta polvere per fascia di luce, dal nero al bianco: sui bianchi si dirada piano |
| `#agoraEdge` / `#agoraEdgeShape` `stdDeviation` | morbidezza del bordo, dal netto (0.6) al più sfumato |
| `#agoraSoften` / `#agoraBloom` `stdDeviation` | morbidezza della luce · diffusione dell'alone |

### Animazioni

Sei `<animate>` SMIL, ognuna con id, dentro `#agoraDustFx`. Le due polarità (chiaro su scuro,
scuro su chiaro) usano lo stesso filtro: animazioni e parametri valgono per entrambe.

| id | Cosa fa | Durata |
|---|---|---|
| `#agoraBoil` | la grana "vive" (come la grana pellicola) | 1.1 s |
| `#agoraDriftX` / `#agoraDriftY` | la polvere scorre sulla superficie | 26 s / 37 s |
| `#agoraStream` | le scie scorrono lungo il fiume | 19 s |
| `#agoraSwirl` | la polvere si piega nel flusso | 17 s |
| `#agoraFlow` | il campo di flusso cambia forma | 23 s |

Per fermarle: usa il file `-static`, elimina i tag `<animate>`, oppure da JS
`document.querySelector('#agoraBoil').endElement()`. Chi ha attivo "riduci movimento"
nel sistema operativo vede già la versione ferma.

### Laboratorio

`agora-dust-lab.html`, doppio click, funziona offline: tinta o gradiente a 3 colori con
angolo, inversione chiaro/scuro, fondo (anche trasparente), tutti i parametri della polvere
(grana, scie, trascinamento, granelli e loro dispersione), velocità e interruttori delle
animazioni, export SVG e PNG 2048.

## Fedeltà rispetto alle immagini caricate

Render in Chromium alla stessa risoluzione delle immagini, confronto pixel per pixel.

**Logo pulito** — errore medio **0.67/255** (0.26%), IoU **0.997** sul tracciato fedele;
la versione corretta se ne discosta dove la lettera è stata resa simmetrica (voluto).

**Logo dust**: errore medio **3,6/255** (1,4%) rispetto all'immagine; la differenza in più è
la correzione voluta della lettera. Luce dopo sfocatura (σ 8): scarto quadratico **0,034** su
scala 0-1. Grana per fascia di luminosità (deviazione standard del dettaglio fine):

| luminosità | 0.1 | 0.2 | 0.4 | 0.5 | 0.7 | 0.8 | 0.95 |
|---|---|---|---|---|---|---|---|
| originale | 0.073 | 0.140 | 0.190 | 0.179 | 0.140 | 0.077 | 0.021 |
| SVG | 0.059 | 0.126 | 0.179 | 0.165 | 0.124 | 0.099 | 0.044 |

La polvere è generata proceduralmente (per questo si muove e si ricolora): non è una copia
pixel per pixel, ma ha grana, intensità per zona e scie dell'originale.

### Polvere v4: cosa è stato corretto

- **Linee nere/grigie tra polvere e bianco.** Venivano da tre cose: la luce prolungata oltre la
  sagoma anche dove nell'originale sfuma (fiume, bandiera), che creava bande grigie tagliate
  di netto; la grana del filtro che si mescolava ai bordi semitrasparenti e disegnava un filo
  grigio lungo il contorno; un filo chiaro lungo la base tra le gambe. Ora la luce viene
  prolungata solo sui bordi netti della A e la superficie è resa opaca prima della grana.
  Il filo lungo la base non c'è più.
- **Macchia scura netta al centro** (sotto la traversa): i livelli di luce erano troppo radi
  negli scuri. Ora i livelli sono più fitti nelle ombre e la luce è più morbida.
- **Troppo netto, poco naturale.** La grana era uguale ovunque, quindi sembrava rumore. Ora è
  piena sul corpo della A e diventa polvere liscia, trascinata a scie lungo il fiume, come
  nell'originale. I granelli escono dalla lettera solo dove la luce sfuma, non dai bordi netti.
- `--dust: 0` ora dà davvero la superficie pulita (prima faceva sparire il logo).
- **Sfumature che finivano di colpo** (gamba sinistra, cima): i livelli di luce erano radi nei
  bianchi e facevano "terrazze" con un bordo; ora sono fitti anche lì e la polvere si dirada
  gradualmente verso il bianco.
- **Angolo al posto della curva** dove il lato della cima entra nella bandiera: il bordo passava
  di colpo da netto a sfumato; ora la morbidezza cambia gradualmente lungo il contorno.
- **Bordino scuro nella versione su fondo chiaro**: la luce veniva tagliata due volte dallo
  stesso bordo sfumato e al centro della sfumatura restava un filo scuro. Ora il bordo lo
  decide solo la sagoma. I bordi esterni sono netti come nell'originale.
- **Le correzioni tengono con qualsiasi impostazione.** Verificato nel laboratorio con gradiente,
  scuro su chiaro, fondo trasparente, grana, scie, morbidezza, alone, dispersione, deformazione,
  esposizione e contrasto ai valori estremi. Due cose sistemate in questa verifica: in "scuro su
  chiaro" cursori e animazioni non avevano effetto (ora c'è un solo filtro per le due polarità);
  esposizione e contrasto spostavano anche il nero (fondo grigio) e tagliavano i bianchi. Ora sono
  una curva che lascia fermi nero e bianco.

## Come sono stati ricostruiti

1. Contorno sub-pixel dalle immagini (marching squares), 4937 punti.
2. Spigoli e raccordi riconosciuti su più scale; ogni tratto classificato retta o curva.
3. Rette per minimi quadrati totali, vertici come intersezione esatta, curve con catene
   di Bézier G1 ottimizzate (errore max ~0.2 px).
4. Lettera resa simmetrica con una trasformazione analitica (shear + correzione della gamba),
   tratti dritti e spigoli riportati su rette e coordinate esatte, stessa trasformazione
   applicata al campo luminoso della versione dust.
5. Polvere ricostruita misurando autocorrelazione, spettro e statistica del rumore dell'originale;
   la luce corretta viene deformata come immagine (non come tracciati) per non creare pieghe,
   e l'intensità della grana è misurata zona per zona (`src/light_v4.py`, `src/kmap_v4.py`,
   `src/emit_v4.py`, `src/build_v4.py`).
6. Ogni passaggio verificato rendendo l'SVG in Chromium e confrontandolo con l'immagine.

Script, immagini sorgente e dati geometrici in `src/`.
