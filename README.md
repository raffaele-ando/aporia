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
| `preview/` | Anteprime PNG e confronti |

## 1. La lettera prima di tutto

L'immagine di partenza aveva una irregolarità misurabile: la **gamba destra si svasava**
(bordo esterno con pendenza 0.500, bordo interno 0.450 → non paralleli) e pesava
**157→165 px** contro i **152.4 px costanti** dell'asta sinistra.

Nel logo di questo repo la gamba destra è stata resa **parallela e dello stesso peso (152 px)**;
il resto dello scheletro era già corretto e non è stato toccato:

- i due diagonali esterni sono simmetrici: **63.0°** a sinistra, **63.4°** a destra;
- basi dei piedi e sommità perfettamente orizzontali, sulla stessa linea;
- punte arrotondate come raccordi veri, non come spigoli approssimati.

Vedi `preview/confronto-geometria.png` (in rosso il materiale tolto).
La stessa lettera corretta è usata **anche sotto la polvere**: nella versione dust i bordi
hanno pendenza esatta ±0.500 anche dopo grana, alone e turbolenza.

Se preferisci il disegno esattamente com'era nell'immagine, usa `agora-logo-tracciato-fedele.svg`.

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

1. **Campo luminoso** — 19 tracciati annidati (isolivelli) dentro `#agoraField`, ritagliati
   sulla lettera e ammorbiditi da `#agoraSoften`. È la "luce" del logo.
2. **Alone** (`#agoraGlowField`) — la frangia luminosa che esce dalla sagoma, sfocata da `#agoraBloom`.
3. **Motore polvere** (`#agoraDustFx`) — il filtro che genera e muove la polvere.

| Nodo / attributo | Effetto |
|---|---|
| `#agoraGrainNoise` `baseFrequency` | dimensione del grano: più basso = grana più grossa (0.45 = originale) |
| `#agoraGrainNoise` `numOctaves` | ricchezza della grana (1 = pulita, 3-4 = più "sporca") |
| `#agoraGrainNoise` `seed` | cambia il disegno della grana a parità di statistica |
| `feColorMatrix result="grain"` | il primo numero della matrice è l'**intensità** della grana (1.65) |
| `#agoraSpeckNoise` + `slope`/`intercept` | dimensione, densità e soglia dei granelli sparsi |
| `#agoraDisplace` `scale` | turbolenza che deforma il logo (0 fermo · 3-6 respiro · 20+ dissolve) |
| `#agoraFlowNoise` `baseFrequency` | scala del vortice di flusso |
| `#agoraGrainShift` `dx`/`dy` | scorrimento della polvere sulla superficie |
| `feComponentTransfer result="toned"` | contrasto ed esposizione del chiaroscuro |
| `#agoraSoften` / `#agoraBloom` `stdDeviation` | morbidezza della luce · diffusione dell'alone |

### Animazioni

Cinque `<animate>` SMIL, ognuna con id, dentro `#agoraDustFx`:

| id | Cosa fa | Durata |
|---|---|---|
| `#agoraBoil` | la grana "vive" (come la grana pellicola) | 1.1 s |
| `#agoraDriftX` / `#agoraDriftY` | la polvere scorre sulla superficie | 26 s / 37 s |
| `#agoraSwirl` | turbolenza che deforma dolcemente | 17 s |
| `#agoraFlow` | il campo di flusso cambia forma | 23 s |

Per fermarle: usa il file `-static`, elimina i tag `<animate>`, oppure da JS
`document.querySelector('#agoraBoil').endElement()`. Chi ha attivo "riduci movimento"
nel sistema operativo vede già la versione ferma.

### Laboratorio

`agora-dust-lab.html`, doppio click, funziona offline: tinta o gradiente a 3 colori con
angolo, inversione chiaro/scuro, fondo (anche trasparente), tutti i parametri della polvere,
velocità e interruttori delle animazioni, export SVG e PNG 2048.

## Fedeltà rispetto alle immagini caricate

Render in Chromium alla stessa risoluzione delle immagini, confronto pixel per pixel.

**Logo pulito** — errore medio **0.67/255** (0.26%), IoU **0.997** sul tracciato fedele;
la versione corretta si discosta solo dove la gamba è stata raddrizzata (voluto).

**Logo dust** — errore medio **~3/255** (1.2%), distribuzione della luce (dopo sfocatura)
errore **0.006** su scala 0-1 dentro la sagoma. Statistica della grana per fascia di luminosità:

| luminosità | 0.1 | 0.2 | 0.4 | 0.5 | 0.7 | 0.8 | 0.95 |
|---|---|---|---|---|---|---|---|
| originale | 0.084 | 0.125 | 0.158 | 0.179 | 0.139 | 0.077 | 0.021 |
| SVG | 0.090 | 0.106 | 0.148 | 0.188 | 0.145 | 0.078 | 0.024 |

La polvere è generata proceduralmente (per questo si muove e si ricolora): non è una copia
pixel per pixel, ma ha grana, intensità per fascia e densità di granelli dell'originale.

## Come sono stati ricostruiti

1. Contorno sub-pixel dalle immagini (marching squares), 4937 punti.
2. Spigoli e raccordi riconosciuti su più scale; ogni tratto classificato retta o curva.
3. Rette per minimi quadrati totali, vertici come intersezione esatta, curve con catene
   di Bézier G1 ottimizzate (errore max ~0.2 px).
4. Correzione della gamba destra e propagazione della stessa geometria alla versione dust
   (deformazione thin-plate-spline del campo luminoso, residuo medio 0.03 px).
5. Polvere ricostruita misurando autocorrelazione, spettro e statistica del rumore dell'originale.
6. Ogni passaggio verificato rendendo l'SVG in Chromium e confrontandolo con l'immagine.

Script, immagini sorgente e dati geometrici in `src/`.
