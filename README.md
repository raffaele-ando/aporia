# Agorà — loghi SVG

Ricostruzione vettoriale dei due loghi Agorà a partire dalle immagini caricate.
Entrambi i file sono SVG puri: nessuna immagine raster incorporata, nessuna dipendenza esterna.

## File

| File | Cosa contiene |
|---|---|
| `agora-logo.svg` | Logo pulito (la "A" con il fiume). Ritagliato sulla forma, fondo trasparente, `fill="currentColor"` |
| `agora-logo-dust.svg` | Versione polvere, animata. Stessa inquadratura quadrata dell'immagine originale (1254×1254) |
| `agora-logo-dust-static.svg` | Identica alla precedente ma senza animazioni (per stampa/export) |
| `agora-logo-dust-tight.svg` | Versione polvere ritagliata sulla forma (per usarla dentro un layout) |
| `agora-dust-lab.html` | Laboratorio interattivo: modifica dal vivo ogni parametro della polvere ed esporta SVG/PNG |
| `preview/` | Anteprime PNG dei tre file |

### Logo pulito

Il tracciato è un unico `<path>` chiuso di 74 segmenti: i bordi dritti sono rette esatte,
le curve del fiume sono Bézier cubiche, le punte arrotondate sono raccordi dedicati.
Le basi dei due piedi, la sommità e le punte verticali sono allineate esattamente
(stessa `y`, stessa `x`), come nel disegno originale.

Usa `currentColor`, quindi prende il colore del testo del contenitore:

```html
<span style="color:#111"><!-- incolla qui l'SVG --></span>
```

## La polvere: come è fatta

La versione dust è costruita a strati, tutti vettoriali:

1. **Campo luminoso** — 19 tracciati annidati (isolivelli di luminosità) dentro `#agoraShaded`,
   ritagliati sulla sagoma con `#agoraClip` e ammorbiditi da `#agoraSoften`.
   È questa la "luce" del logo: il chiaro in basso a sinistra, il buio in alto a destra,
   la lama luminosa lungo il fiume.
2. **Alone** (`#agoraGlow`) — la frangia luminosa che esce dalla sagoma, sfocata da `#agoraBloom`.
3. **Motore polvere** (`#agoraDust`) — il filtro che genera e muove la polvere:
   - `#agoraGrainNoise` → grana fine (`feTurbulence`), fusa in **overlay**: forte nei mezzitoni,
     assente nei bianchi e nei neri puri, esattamente come nell'originale;
   - `#agoraSpeckNoise` → granelli sparsi che brillano nelle zone scure, fusi in **screen**;
   - `#agoraFlowNoise` + `#agoraDisplace` → campo di flusso che deforma superficie e polvere;
   - `#agoraGrainShift` → scorrimento della grana (`feOffset`).

### Parametri (cosa toccare per ottenere cosa)

| Nodo / attributo | Effetto |
|---|---|
| `#agoraGrainNoise` `baseFrequency` | dimensione del grano: più basso = grana più grossa (0.45 = originale) |
| `#agoraGrainNoise` `numOctaves` | ricchezza/struttura della grana (1 = pulita, 3-4 = più "sporca") |
| `#agoraGrainNoise` `seed` | cambia il disegno della grana lasciando invariata la statistica |
| `feColorMatrix result="grain"` | il primo valore della matrice è l'**intensità** della grana (1.65) |
| `#agoraSpeckNoise` `baseFrequency` | dimensione dei granelli sparsi |
| `feComponentTransfer` → `slope` / `intercept` | densità e soglia dei granelli (3.0 / −1.8) |
| `#agoraDisplace` `scale` | quanta turbolenza deforma il logo (0 = fermo, 3-6 = respiro, 20+ = dissolve) |
| `#agoraFlowNoise` `baseFrequency` | scala del vortice di flusso (basso = onde ampie) |
| `#agoraGrainShift` `dx` / `dy` | sposta la polvere sulla superficie |
| `#agoraSoften` `stdDeviation` | morbidezza dei passaggi di luce |
| `#agoraBloom` `stdDeviation` | quanto si diffonde l'alone fuori dalla sagoma |

### Variabili CSS (nessun JavaScript)

```css
#agoraDustLogo {
  --dust-bg: #000;        /* colore di fondo                          */
  --dust-glow: 1;         /* 0..1.5 intensità alone                   */
  --dust-contrast: 1;     /* contrasto generale                       */
  --dust-brightness: 1;   /* luminosità generale                      */
  --dust-amount: 1;       /* 0 = superficie pulita, 1 = polvere piena */
}
```

### Animazioni

Sono cinque `<animate>` SMIL, ognuna con un id, dentro `#agoraDust`:

| id | Cosa fa | Durata |
|---|---|---|
| `#agoraBoil` | la grana "vive" (cambia seme a scatti, come la grana pellicola) | 1.1 s |
| `#agoraDriftX` / `#agoraDriftY` | la polvere scorre lentamente sulla superficie | 26 s / 37 s |
| `#agoraSwirl` | turbolenza che deforma dolcemente il logo | 17 s |
| `#agoraFlow` | il campo di flusso cambia forma | 23 s |

- Per fermare tutto: usa `agora-logo-dust-static.svg`, oppure elimina i tag `<animate>`.
- Da JavaScript: `document.querySelector('#agoraBoil').endElement()` per fermare,
  `.beginElement()` per far ripartire, o cambia `dur` per la velocità.
- Chi ha attivo "riduci movimento" nel sistema operativo vede la versione ferma
  (`prefers-reduced-motion` è già gestito).

### Laboratorio

Apri `agora-dust-lab.html` in un browser (basta doppio click, funziona offline):
slider per ogni parametro, interruttori per le animazioni, esportazione SVG e PNG 2048px
dello stato corrente. È il modo più rapido per cercare una variante e portarsela via.

## Fedeltà rispetto alle immagini originali

Misure fatte rendendo gli SVG in Chromium alla stessa risoluzione delle immagini caricate
e confrontando pixel per pixel:

**Logo pulito** (1402×1122)
- errore medio per pixel: **0.67 / 255** (0.26%)
- sovrapposizione delle forme (IoU): **0.997**
- differenze residue: solo antialiasing sui bordi

**Logo dust** (1254×1254)
- errore medio per pixel: **2.8 / 255** (1.1%)
- distribuzione della luce (dopo sfocatura): errore **0.006** su scala 0-1 all'interno della sagoma
- statistica della grana per fascia di luminosità, rispetto all'originale:

  | luminosità | 0.1 | 0.2 | 0.4 | 0.5 | 0.7 | 0.8 | 0.95 |
  |---|---|---|---|---|---|---|---|
  | originale | 0.084 | 0.125 | 0.158 | 0.179 | 0.139 | 0.077 | 0.021 |
  | SVG | 0.090 | 0.106 | 0.148 | 0.188 | 0.145 | 0.078 | 0.024 |

La polvere non è una copia pixel per pixel (è generata proceduralmente, ed è per questo
che si può muovere): ha la stessa dimensione del grano, la stessa intensità per ogni fascia
di luminosità e la stessa densità di granelli sparsi dell'originale.

## Come sono stati ricostruiti

1. Contorno sub-pixel dalle immagini (marching squares), 4937 punti.
2. Riconoscimento di spigoli e raccordi su più scale; ogni tratto classificato come retta o curva.
3. Rette ricavate per minimi quadrati totali, vertici come intersezione esatta delle rette,
   curve fittate con catene di Bézier G1 ottimizzate (errore massimo ~0.2 px).
4. La sagoma della versione dust è la stessa geometria, adattata ai bordi realmente
   visibili nell'immagine originale (scarto mediano 0.04 px).
5. Campo luminoso estratto per isolivelli e vettorizzato; polvere ricostruita misurando
   autocorrelazione, spettro e statistica del rumore dell'immagine originale.
6. Ogni passaggio verificato rendendo l'SVG in Chromium e confrontandolo con l'originale.

Gli script di ricostruzione, le immagini sorgente e i dati geometrici sono in `src/`.
