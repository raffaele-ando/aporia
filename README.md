# Aporia — apertura del sito

Animazione d'ingresso del sito: nero, compare la polvere, arrivano delle folate di vento,
la polvere si raccoglie nel logo, il logo si sgretola nel vento e resta la home, che per ora
mostra solo la scritta **Aporia**.

Apri `index.html` nel browser: è un file unico, senza dipendenze (il logo è incorporato;
l'unica risorsa esterna è il carattere Italiana da Google Fonts, con ripiego su Didot/Bodoni/serif).

## Sequenza (circa 8,5 s)

| tempo | cosa succede |
|---|---|
| 0 – 0,7 s | nero |
| 0,7 – 2,2 s | la polvere compare dal nero, sospesa e in lento movimento |
| 1,5 s | prima folata di vento |
| 2,5 s | seconda folata, più forte: la polvere nell'aria viene trascinata verso il centro |
| 3,1 – 4,5 s | la polvere si posa e il logo si forma (la deformazione del logo si scioglie) |
| 4,5 – 5,8 s | il logo resta, la sua polvere continua a muoversi; una folata leggera |
| 5,8 – 7,3 s | ultima folata: il logo si sgretola da sinistra a destra con un fronte frastagliato e la polvere vola via |
| 7,1 – 8,4 s | compare la home: "Aporia" |

- Click, tocco o un tasto qualsiasi durante l'intro: si salta subito alla home.
- Doppio click sulla scritta "Aporia": si rivede l'apertura.
- Con "riduci movimento" attivo nel sistema: solo dissolvenze (logo → home), niente vento.
- Su schermi piccoli il vento è scalato alle dimensioni dello schermo.

Anteprime dei fotogrammi in `preview/`.

## Cosa si può regolare

Tutto in `src/template.html`, in cima allo script:

- `T`: i tempi di ogni fase (secondi).
- `GUSTS`: le folate (inizio, durata, forza, angolo, tempo per attraversare lo schermo).
- `--dust`, `--night`, `--paper` nel CSS: colori di polvere, nero e scritta.

Dopo una modifica: `python src/build.py` rigenera `index.html` (legge il logo da
`../agora_loghi_svg/agora-logo-dust.svg`, quindi ogni aggiornamento del logo entra qui).

## Come funziona

- **Polvere e vento**: un canvas con qualche migliaio di granelli. Ogni granello segue un campo di
  turbolenza (rumore) più le folate, che attraversano lo schermo da sinistra a destra. La scia è
  data dal fotogramma precedente che si scurisce invece di cancellarsi, come fumo.
- **Formazione del logo**: i punti di arrivo sono presi dall'immagine del logo stesso (più punti
  dove il logo è chiaro). Metà dei granelli viene dall'aria, metà arriva con la folata; si posano
  senza rimbalzi mentre il logo vero compare e la sua deformazione (`#agoraDisplace`) scende a zero.
- **Uscita**: una maschera con fronte frastagliato scorre sul logo; lungo il fronte ogni punto del
  logo diventa un granello con un suo peso (i più leggeri volano via prima), quindi la polvere si
  allunga e si disperde invece di muoversi a blocco.
