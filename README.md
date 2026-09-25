# Aporia — apertura del sito

Animazione d'ingresso del sito: nero, compare la polvere, arrivano delle folate di vento,
la polvere si raccoglie nel logo, il logo si sgretola nel vento e resta la home, che per ora
mostra solo la scritta **Aporia**.

Apri `index.html` nel browser: è un file unico (circa 560 KB), senza dipendenze (il logo è incorporato;
l'unica risorsa esterna è il carattere Italiana da Google Fonts, con ripiego su Didot/Bodoni/serif).

## Sequenza (circa 11 s)

Il logo dust è una A di polvere in cui il vento ha scavato il fiume e trascinato la polvere a
destra (la "bandiera"). L'intro racconta proprio questo:

| tempo | cosa succede |
|---|---|
| 0 – 0,7 s | nero |
| 0,7 – 2,2 s | la polvere compare dal nero, sospesa e in lento movimento |
| 1,5 s | prima folata di vento |
| 2,5 – 4,7 s | seconda folata: la polvere si posa granello per granello e costruisce una **A pulita**, da sinistra a destra |
| 4,7 – 5,0 s | la A pulita resta un istante |
| 5,0 – 7,2 s | una folata attraversa la lettera: dove passa, la polvere del fiume e delle ombre si solleva e vola a destra; una parte si deposita nella bandiera e sui bordi del fiume, il resto viene portato via. Il risultato è esattamente il logo |
| 7,2 – 8,3 s | il logo resta |
| 8,3 – 9,8 s | ultima folata: il logo si sgretola da sinistra a destra e la polvere vola via |
| 9,6 – 10,9 s | compare la home: "Aporia" |

- Click, tocco o un tasto qualsiasi durante l'intro: si salta subito alla home.
- Doppio click sulla scritta "Aporia": si rivede l'apertura.
- Con "riduci movimento" attivo nel sistema: solo dissolvenze (logo → home), niente vento.
- Su schermi piccoli il vento è scalato alle dimensioni dello schermo.

Anteprime dei fotogrammi in `preview/` (`fiume-scavato-dal-vento.png`: la folata che trasforma la A pulita nel logo).

## Cosa si può regolare

Tutto in `src/template.html`, in cima allo script:

- `T`: i tempi di ogni fase (secondi).
- `GUSTS`: le folate (inizio, durata, forza, angolo, tempo per attraversare lo schermo).
- `--night`, `--paper` nel CSS: colori del nero e della scritta.

Dopo una modifica: `python src/build.py` rigenera `index.html`.

## Come funziona

- **Il logo è un'immagine, non un SVG "vivo".** `src/render_logo.py` fotografa il logo dust vero
  (`../agora_loghi_svg/agora-logo-dust-static.svg`) in immagini pronte. Durante l'animazione non c'è nessun filtro SVG da calcolare.
  Prima c'era, ed era la causa del blocco sui telefoni (ogni fotogramma ricalcolava decine di
  filtri) e del tremolio su Safari/iPad, che quei filtri li calcola in modo diverso.
- **Polvere e vento**: un canvas con qualche migliaio di granelli. Ogni granello segue un campo di
  turbolenza (rumore) più le folate, che attraversano lo schermo da sinistra a destra. La scia è
  data dal fotogramma precedente che sbiadisce invece di cancellarsi, come fumo.
- **Formazione della A pulita**: la A resta invisibile e si "accende" solo dove un granello si è
  posato (ogni granello, arrivando, lascia uno sbuffo in una maschera di accumulo). I granelli
  arrivano col vento da sinistra verso destra, quindi la lettera si completa nello stesso verso.
- **Il vento scava il fiume** (`src/prep_morph.py` prepara tutto in anticipo):
  - `S` è la A pulita di polvere;
  - il logo è diviso in `Bstay`, la polvere che nella A c'è già e resta, e `Bmove`, la polvere
    che arriva col vento (bandiera, bordi chiari del fiume);
  - circa 2600 granelli vanno da dove il vento solleva la polvere (fiume, ombre) a dove la
    deposita, abbinati in modo che il vento li porti sempre verso destra; quelli senza posto
    vengono portati via e si disperdono.

  Nel browser, lungo il fronte della folata la A pulita diventa `Bstay` e i granelli partono.
  Dove si posano compare `Bmove`, quindi alla fine `S` è diventata esattamente il logo.
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

Se cambia il logo: `python src/render_logo.py` (fotografa il logo), `python src/prep_morph.py`
(A pulita, divisione e granelli) e poi `python src/build.py`.
