# Campione di comuni: come è stato estratto

Fonti: elenco dei comuni ISTAT con provincia (`data/comuni_province.csv`) e popolazione residente al 1° gennaio 2026 (ISTAT, `POSAS_2026_it_Comuni`, somma per età).

Comuni lombardi nell'elenco ISTAT: 1502; senza popolazione nel file 2026: 0.

| Fascia | Comuni in Lombardia | Estratti |
|---|---:|---:|
| A: oltre 10.000 abitanti | 196 | 20 |
| B: 5.000-10.000 abitanti | 278 | 20 |

Fascia A = popolazione > 10.000; fascia B = da 5.000 a 10.000 inclusi. In totale 474 comuni.

## Regola di sorteggio

Per ogni fascia: `random.Random(seme).sample(elenco, 20)` (Python), con l'elenco ordinato per codice ISTAT. Un sorteggio vale solo se ogni fascia copre almeno 8 province; altrimenti si ripete con seme+1. Nessun comune scelto a mano.

| Seme | Province fascia A | Province fascia B | Esito |
|---:|---:|---:|---|
| 20261006 | 8 | 8 | accettato |

## Province coperte

| Provincia | Fascia A | Fascia B | Totale A in Lombardia | Totale B in Lombardia |
|---|---:|---:|---:|---:|
| Bergamo | 0 | 3 | 19 | 56 |
| Brescia | 4 | 1 | 33 | 39 |
| Como | 1 | 4 | 7 | 27 |
| Cremona | 0 | 2 | 3 | 10 |
| Lecco | 0 | 0 | 5 | 12 |
| Lodi | 0 | 1 | 4 | 4 |
| Mantova | 1 | 2 | 10 | 19 |
| Milano | 4 | 5 | 60 | 41 |
| Monza e della Brianza | 5 | 0 | 26 | 19 |
| Pavia | 1 | 0 | 6 | 19 |
| Sondrio | 1 | 0 | 2 | 4 |
| Varese | 3 | 2 | 21 | 28 |

## Il campione

| Fascia | Comune | Provincia | Abitanti |
|---|---|---|---:|
| A | Leno | Brescia | 14.474 |
| A | Mazzano | Brescia | 12.715 |
| A | Ospitaletto | Brescia | 14.969 |
| A | Sarezzo | Brescia | 13.309 |
| A | Olgiate Comasco | Como | 12.184 |
| A | Borgo Virgilio | Mantova | 15.052 |
| A | Cormano | Milano | 21.036 |
| A | Locate di Triulzi | Milano | 10.360 |
| A | Magenta | Milano | 25.066 |
| A | Pieve Emanuele | Milano | 15.846 |
| A | Bernareggio | Monza e della Brianza | 11.706 |
| A | Cornate d'Adda | Monza e della Brianza | 11.134 |
| A | Giussano | Monza e della Brianza | 26.509 |
| A | Seveso | Monza e della Brianza | 23.982 |
| A | Vimercate | Monza e della Brianza | 26.341 |
| A | Mortara | Pavia | 15.934 |
| A | Sondrio | Sondrio | 21.495 |
| A | Caronno Pertusella | Varese | 18.556 |
| A | Gerenzano | Varese | 11.065 |
| A | Varese | Varese | 79.100 |
| B | Bonate Sotto | Bergamo | 6.645 |
| B | Brembate di Sopra | Bergamo | 8.068 |
| B | Grumello del Monte | Bergamo | 7.675 |
| B | Sirmione | Brescia | 8.454 |
| B | Arosio | Como | 5.227 |
| B | Cabiate | Como | 7.404 |
| B | Lurago d'Erba | Como | 5.587 |
| B | San Fermo della Battaglia | Como | 7.770 |
| B | Pandino | Cremona | 8.988 |
| B | Spino d'Adda | Cremona | 7.013 |
| B | Lodi Vecchio | Lodi | 7.717 |
| B | Poggio Rusco | Mantova | 6.255 |
| B | Rodigo | Mantova | 5.174 |
| B | Casorezzo | Milano | 5.721 |
| B | Cuggiono | Milano | 8.198 |
| B | Robecco sul Naviglio | Milano | 6.794 |
| B | San Colombano al Lambro | Milano | 7.591 |
| B | Vaprio d'Adda | Milano | 9.723 |
| B | Arcisate | Varese | 9.859 |
| B | Ispra | Varese | 5.358 |
