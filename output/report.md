# Bandi aperti in Lombardia per provincia e settore

Data di riferimento: **2026-10-06**. Finestra di pubblicazione: **2026-08-07 → 2026-10-06** (60 giorni). Download fonti: 2026-10-06T11:21:38. Ultima data di pubblicazione presente nei dati ANAC: **2026-10-01**.

Fonte principale: ANAC open data (dataset `cig` incrementali mensili + `pubblicazioni` + anagrafica `stazioni-appaltanti`). Unità di conteggio: **gara** (`numero_gara` per stazione appaltante); una gara a più lotti conta 1, i lotti sono riportati a parte. Metodo e limiti in fondo e in `docs/nota_fonti.md`.

## 1. Gare aperte per provincia

Provincia = provincia del comune della **stazione appaltante** (anagrafica ANAC → tabella comuni ISTAT), non del luogo di esecuzione. Le colonne "Con …" contano le gare con quel campo compilato; "Sotto 40.000 €" usa l'importo complessivo della gara.

| Provincia | Gare aperte | Lotti (CIG) aperti | Con importo | Con scadenza | Con comune SA | Sotto 40.000 € | Gare pubblicate nei 60 gg (anche già scadute) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Milano | 146 | 210 | 146 | 146 | 146 | 15 | 471 |
| Bergamo | 44 | 78 | 44 | 44 | 44 | 0 | 157 |
| Pavia | 28 | 37 | 28 | 28 | 28 | 3 | 79 |
| Brescia | 24 | 26 | 24 | 24 | 24 | 3 | 165 |
| Varese | 23 | 40 | 23 | 23 | 23 | 0 | 117 |
| Como | 20 | 36 | 20 | 20 | 20 | 1 | 77 |
| Monza e della Brianza | 16 | 18 | 16 | 16 | 16 | 1 | 67 |
| Lecco | 15 | 24 | 15 | 15 | 15 | 0 | 30 |
| Cremona | 11 | 20 | 11 | 11 | 11 | 2 | 40 |
| Sondrio | 9 | 12 | 9 | 9 | 9 | 0 | 63 |
| Mantova | 8 | 24 | 8 | 8 | 8 | 1 | 46 |
| Lodi | 7 | 53 | 7 | 7 | 7 | 0 | 21 |
| **Totale Lombardia** | 351 | 578 | 351 | 351 | 351 | 26 | 1333 |

## 2. Gare aperte per provincia × macro-categoria CPV

Macro-categoria assegnata dal CPV prevalente del lotto aperto di importo maggiore. Mappatura completa in `config/cpv_macro.csv` (riportata in fondo).

| Provincia | Edilizia, lavori e manutenzioni | Impianti ed energia | Verde e ambiente | Pulizie, sanificazione e rifiuti | Sanità e servizi alla persona | Servizi tecnici, IT e professionali | Trasporti e altri servizi | Forniture di beni | Totale |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Milano | 41 | 12 | 2 | 6 | 24 | 30 | 0 | 31 | 146 |
| Bergamo | 24 | 2 | 0 | 1 | 8 | 5 | 0 | 4 | 44 |
| Pavia | 7 | 1 | 0 | 5 | 7 | 4 | 0 | 4 | 28 |
| Brescia | 10 | 1 | 0 | 1 | 5 | 1 | 0 | 6 | 24 |
| Varese | 2 | 0 | 0 | 1 | 10 | 4 | 1 | 5 | 23 |
| Como | 6 | 0 | 1 | 3 | 4 | 1 | 0 | 5 | 20 |
| Monza e della Brianza | 9 | 0 | 0 | 0 | 5 | 1 | 0 | 1 | 16 |
| Lecco | 3 | 3 | 0 | 3 | 3 | 2 | 0 | 1 | 15 |
| Cremona | 2 | 1 | 0 | 0 | 6 | 2 | 0 | 0 | 11 |
| Sondrio | 4 | 1 | 0 | 3 | 0 | 1 | 0 | 0 | 9 |
| Mantova | 1 | 0 | 0 | 0 | 2 | 2 | 1 | 2 | 8 |
| Lodi | 4 | 0 | 0 | 1 | 2 | 0 | 0 | 0 | 7 |
| **Totale** | 113 | 21 | 3 | 24 | 76 | 53 | 2 | 59 | 351 |

## 3. Come si arriva al numero (ANAC)

| Passo | Conteggio |
|---|---:|
| 1. CIG pubblicati nella finestra da SA lombarde | 23565 |
| 2. ... di cui procedure aperte/ristrette/negoziate | 1872 |
| 3. ... non cancellati e senza esito (aggiudicazione, revoca, deserta) | 1696 |
| 4. ... con scadenza offerte >= oggi (lotti conteggiati) | 578 |
|    (scartati: scadenza non compilata) | 29 |
| 5. Gare (numero_gara) conteggiate | 351 |

Procedure escluse (CIG nella finestra, SA lombarde):

| Tipo scelta contraente | CIG |
|---|---:|
| AFFIDAMENTO DIRETTO | 21126 |
| AFFIDAMENTO DIRETTO A SOCIETA' IN HOUSE | 200 |
| ALTRA PROCEDURA A FASE UNICA | 141 |
| ALTRA PROCEDURA A PIU' FASI | 111 |
| AFFIDAMENTO DIRETTO IN ADESIONE AD ACCORDO QUADRO/CONVENZIONE | 75 |
| ND | 32 |
| PROCEDURA DI GARA | 8 |

Procedure nelle gare conteggiate: Negoziata (invito) 162, Aperta 159, Negoziata (bando) 21, Ristretta 9.

Origine della scadenza: ANAC cig 320, ANAC pubblicazioni 31.

Come è stata ricavata la provincia: codice ISTAT 349, sigla provincia 2.

## 4. Completezza dei campi chiave

ANAC, sui 1872 CIG di procedure aperte/ristrette/negoziate pubblicati nella finestra da SA lombarde (prima del filtro sulla scadenza):

| Campo | Compilato | % |
|---|---:|---|
| scadenza offerta (data_scadenza_offerta) | 1677 | 89.6 |
| scadenza offerta o invito (+ pubblicazioni.SCADENZA_INVITO) | 1841 | 98.3 |
| importo lotto > 0 | 1872 | 100.0 |
| importo complessivo gara > 0 | 1872 | 100.0 |
| CPV (cod_cpv) | 1872 | 100.0 |
| comune della SA (anagrafica stazioni-appaltanti) | 1872 | 100.0 |
| luogo di esecuzione (luogo_istat) | 1872 | 100.0 |
| provincia (campo del CIG) | 1872 | 100.0 |

TED, sui 2549 bandi italiani nella finestra:

| Campo | Compilato | % |
|---|---:|---|
| scadenza offerta | 2519 | 98.8 |
| città del committente | 2546 | 99.9 |
| CPV | 2549 | 100.0 |
| importo stimato (lotto o procedura) | 2529 | 99.2 |

Regione Lombardia (k6cb-4hbm), sui 98 bandi distinti scaricati:

| Campo | Compilato | % |
|---|---:|---|
| scadenza offerta | 98 | 100.0 |
| comune | 59 | 60.2 |
| provincia | 61 | 62.2 |
| importo | 98 | 100.0 |
| CPV | 98 | 100.0 |
| data pubblicazione | 13 | 13.3 |

## 5. Confronto con le altre fonti

**TED (api.ted.europa.eu)** – solo gare sopra soglia UE. Bandi (cn-standard/cn-social/cn-desg) di committenti italiani pubblicati nella finestra: 2549; con città del committente in Lombardia: 296; con scadenza >= oggi: **182**. Città non riconducibili a un comune univoco: 81 (es. Bolzano / Bozen 6, Via Montello 118 6, Italia 4, Brussels 4, Reggio Calabria 3).

| Provincia | Bandi TED aperti |
|---|---:|
| Milano | 86 |
| Varese | 19 |
| Pavia | 14 |
| Bergamo | 12 |
| Monza e della Brianza | 11 |
| Lecco | 10 |
| Como | 9 |
| Cremona | 8 |
| Brescia | 4 |
| Lodi | 3 |
| Mantova | 3 |
| Sondrio | 3 |

Verifica di copertura ANAC: un bando TED aperto si considera presente in ANAC se esiste una gara ANAC conteggiata nella stessa provincia con la stessa data di scadenza (confronto approssimato, TED non riporta il CIG).

| Bandi TED aperti | Esito | N |
|---|---|---:|
| pubblicati dopo l'ultimo dato ANAC | non trovati | 16 |
| pubblicati dopo l'ultimo dato ANAC | trovati in ANAC | 12 |
| pubblicati entro l'ultimo dato ANAC | non trovati | 19 |
| pubblicati entro l'ultimo dato ANAC | trovati in ANAC | 135 |

**Regione Lombardia – Osservatorio (dati.lombardia.it, k6cb-4hbm)** – righe nella finestra: 242, bandi distinti: 98, non affidamenti diretti con scadenza >= oggi: **4**. Copertura molto parziale (poche SA lo alimentano): usato solo come confronto.

| Provincia | Bandi aperti |
|---|---:|
| Milano | 3 |
| Varese | 1 |

**Sintel (www.sintel.regione.lombardia.it)** – raggiungibile, ma la home reindirizza al portale ARIA (applicazione JavaScript) e non espone un elenco o un'API pubblica scaricabile: nessun dato usato.

## 6. Mappatura CPV → macro-categoria

Regola: si applica il prefisso più lungo che corrisponde; le divisioni 03-44 non elencate vanno in "Forniture di beni".

| Prefisso CPV | Macro-categoria | Contenuto |
|---|---|---|
| 45 | Edilizia, lavori e manutenzioni | Lavori di costruzione (tranne 453 impianti) |
| 50 | Edilizia, lavori e manutenzioni | Servizi di riparazione e manutenzione (tranne 507 impianti) |
| 453 | Impianti ed energia | Lavori di installazione impianti (elettrici, idraulici, termici, ascensori) |
| 507 | Impianti ed energia | Riparazione e manutenzione di impianti di edifici |
| 09 | Impianti ed energia | Prodotti petroliferi, combustibili, elettricità |
| 65 | Impianti ed energia | Servizi di pubblica utilità (gas, acqua, energia) |
| 31 | Impianti ed energia | Macchine e apparecchi elettrici, illuminazione |
| 77 | Verde e ambiente | Servizi agricoli, forestali, orticoli, manutenzione del verde |
| 907 | Verde e ambiente | Servizi ambientali (bonifiche, monitoraggio) |
| 03 | Verde e ambiente | Prodotti dell'agricoltura, orticoltura, silvicoltura |
| 90 | Pulizie, sanificazione e rifiuti | Servizi fognari, rifiuti, pulizia e igiene (tranne 907) |
| 39830 | Pulizie, sanificazione e rifiuti | Prodotti per la pulizia |
| 33 | Sanità e servizi alla persona | Apparecchi medicali, farmaci, prodotti per la cura personale |
| 85 | Sanità e servizi alla persona | Servizi sanitari e di assistenza sociale |
| 80 | Sanità e servizi alla persona | Servizi di istruzione e formazione |
| 55 | Sanità e servizi alla persona | Servizi alberghieri, di ristorazione e mense |
| 92 | Sanità e servizi alla persona | Servizi ricreativi, culturali e sportivi |
| 98 | Sanità e servizi alla persona | Altri servizi di comunità, sociali e personali |
| 71 | Servizi tecnici, IT e professionali | Servizi architettonici, di ingegneria, di ispezione |
| 72 | Servizi tecnici, IT e professionali | Servizi informatici (consulenza, software, internet) |
| 48 | Servizi tecnici, IT e professionali | Pacchetti software e sistemi di informazione |
| 73 | Servizi tecnici, IT e professionali | Servizi di ricerca e sviluppo |
| 79 | Servizi tecnici, IT e professionali | Servizi per le imprese (legali, contabili, marketing, vigilanza, stampa) |
| 66 | Servizi tecnici, IT e professionali | Servizi finanziari e assicurativi |
| 70 | Servizi tecnici, IT e professionali | Servizi immobiliari |
| 75 | Servizi tecnici, IT e professionali | Servizi della pubblica amministrazione, difesa, previdenza |
| 76 | Servizi tecnici, IT e professionali | Servizi connessi all'industria petrolifera e del gas |
| 64 | Servizi tecnici, IT e professionali | Servizi di poste e telecomunicazioni |
| 60 | Trasporti e altri servizi | Servizi di trasporto (escluso trasporto rifiuti) |
| 63 | Trasporti e altri servizi | Servizi di supporto e ausiliari nel campo dei trasporti, agenzie di viaggio |
| 51 | Trasporti e altri servizi | Servizi di installazione (escluso software) |
| 01-44 | Forniture di beni | Tutte le altre divisioni CPV di forniture (03-44) non elencate sopra: materiali da costruzione, alimentari, arredi, veicoli, hardware IT, abbigliamento, carta, ecc. |
