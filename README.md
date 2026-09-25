# Aporia — apertura del sito

Animazione d'ingresso del sito: nero, compare la polvere, arrivano delle folate di vento,
la polvere si raccoglie nel logo, il logo si sgretola nel vento e resta la home, che per ora
mostra solo la scritta **Aporia**.

Apri `index.html` nel browser: è un file unico (circa 500 KB), senza dipendenze (il logo è incorporato;
l'unica risorsa esterna è il carattere Italiana da Google Fonts, con ripiego su Didot/Bodoni/serif).

## Sequenza (circa 8,5 s)

| tempo | cosa succede |
|---|---|
| 0 – 0,7 s | nero |
| 0,7 – 2,2 s | la polvere compare dal nero, sospesa e in lento movimento |
| 1,5 s | prima folata di vento |
| 2,5 s | seconda folata, più forte: la polvere nell'aria viene trascinata verso il centro |
| 2,4 – 4,7 s | la polvere si posa granello per granello e il logo si costruisce da sinistra a destra |
| 4,5 – 5,8 s | il logo resta, la sua polvere continua a muoversi; una folata leggera |
| 5,8 – 7,3 s | ultima folata: il logo si sgretola da sinistra a destra con un fronte frastagliato e la polvere vola via |
| 7,1 – 8,4 s | compare la home: "Aporia" |

- Click, tocco o un tasto qualsiasi durante l'intro: si salta subito alla home.
- Doppio click sulla scritta "Aporia": si rivede l'apertura.
- Con "riduci movimento" attivo nel sistema: solo dissolvenze (logo → home), niente vento.
- Su schermi piccoli il vento è scalato alle dimensioni dello schermo.

Anteprime dei fotogrammi in `preview/` (`formazione-telefono.png`: la costruzione del logo, un fotogramma ogni 0,2 s).

## Cosa si può regolare

Tutto in `src/template.html`, in cima allo script:

- `T`: i tempi di ogni fase (secondi).
- `GUSTS`: le folate (inizio, durata, forza, angolo, tempo per attraversare lo schermo).
- `--night`, `--paper` nel CSS: colori del nero e della scritta.

Dopo una modifica: `python src/build.py` rigenera `index.html`.

## Come funziona

- **Il logo è un'immagine, non un SVG "vivo".** `src/render_logo.py` fotografa il logo dust vero
  (`../agora_loghi_svg/agora-logo-dust-static.svg`) in due fotogrammi con grana diversa, che
  nell'intro si alternano piano. Durante l'animazione non c'è nessun filtro SVG da calcolare.
  Prima c'era, ed era la causa del blocco sui telefoni (ogni fotogramma ricalcolava decine di
  filtri) e del tremolio su Safari/iPad, che quei filtri li calcola in modo diverso.
- **Polvere e vento**: un canvas con qualche migliaio di granelli. Ogni granello segue un campo di
  turbolenza (rumore) più le folate, che attraversano lo schermo da sinistra a destra. La scia è
  data dal fotogramma precedente che sbiadisce invece di cancellarsi, come fumo.
- **Formazione del logo: si costruisce dalla polvere.** Il logo resta invisibile e si "accende"
  solo dove un granello si è posato: ogni granello, arrivando al suo punto (i punti sono presi
  dall'immagine del logo, più fitti dove è chiaro), lascia uno sbuffo in una maschera di accumulo.
  I granelli arrivano col vento da sinistra verso destra, quindi il logo si completa nello stesso
  verso; negli ultimi istanti la maschera si chiude del tutto. Metà dei granelli viene dalla
  polvere già nell'aria, metà arriva con la folata.
- **Stesso effetto su telefono e desktop**: il vento si adatta allo schermo, ma le folate restano
  lunghe e setose anche sul telefono.
- **Uscita**: una maschera con fronte frastagliato scorre sul logo; lungo il fronte ogni punto del
  logo diventa un granello con un suo peso (i più leggeri volano via prima), quindi la polvere si
  allunga e si disperde invece di muoversi a blocco.
- **Fluidità su ogni dispositivo**:
  - il tempo dell'animazione avanza al massimo di 1/20 s per fotogramma, quindi su un dispositivo
    lento rallenta un attimo ma non salta mai delle fasi;
  - la quantità di polvere si adatta ai fotogrammi reali: se il dispositivo fatica si usa meno
    polvere e, all'avvio, una risoluzione più bassa;
  - le immagini del logo vengono decodificate all'avvio, a schermo ancora nero.

Se cambia il logo: `python src/render_logo.py` (rifà i fotogrammi) e poi `python src/build.py`.
