# Nota sulle fonti: campi disponibili e prove di accesso

Verifica eseguita il 2026-10-06 da un container cloud (tramite proxy HTTPS).
Le percentuali di compilazione dei campi sono in `output/report.md`, sezione 4.

## Raggiungibilità

| Fonte | Esito | Note |
|---|---|---|
| dati.anticorruzione.it (ANAC) | **Raggiungibile, con un accorgimento** | Il WAF (F5) rifiuta la home e `/opendata/` (403 "Request Rejected") e qualsiasi richiesta con lo User-Agent di default di curl/urllib. Con uno User-Agent da browser funzionano l'API CKAN (`/opendata/api/3/action/...`) e i download (`/opendata/download/dataset/...`). Ci sono comunque dei 403 intermittenti: lo script ritenta fino a 4 volte con attese crescenti. |
| ted.europa.eu | Raggiungibile | La home risponde 202 (challenge anti-bot), ma non serve: si usa l'API. |
| api.ted.europa.eu | Raggiungibile | API di ricerca v3 (`POST /v3/notices/search`), anonima, nessuna chiave. |
| dati.lombardia.it | Raggiungibile | API Socrata (SODA) su `www.dati.lombardia.it`. Alcuni endpoint di metadati sono lenti (timeout a 25 s). |
| www.sintel.regione.lombardia.it | Raggiungibile ma **inutilizzabile** | La home è un redirect `meta refresh` verso `www.arca.regione.lombardia.it`, che a sua volta porta a `www.ariaspa.it`, un'applicazione JavaScript. Non c'è un elenco bandi né un'API pubblica scaricabile; i vecchi percorsi `/eprocdata/...` rispondono 404. Nessun dato usato. |
| www.istat.it (in più) | Raggiungibile | Serve solo per la tabella comune → provincia (`Elenco-comuni-italiani.csv`). |

## Dataset usati e campi chiave

### ANAC – fonte principale

- **`cig`**: file mensili *incrementali* (`AAAAMM01-cig_csv.zip`). Ogni file contiene i CIG creati o modificati nel mese precedente, comprese righe vecchie aggiornate (es. un esito arrivato dopo). Abbiamo usato agosto, settembre e ottobre 2026; il file di ottobre, pubblicato il 2026-10-05, arriva fino al **2026-10-01**, e quel giorno è parziale (2.298 CIG contro i circa 5.500 di un giorno feriale normale). Una riga corrisponde a un CIG (lotto); i CIG di una stessa gara sono legati da `numero_gara`.

  | Campo richiesto | Campo ANAC | Note |
  |---|---|---|
  | Scadenza offerta | `data_scadenza_offerta` | Compilata nel 90% circa delle procedure competitive. Integrata con `SCADENZA_INVITO` del dataset `pubblicazioni`. |
  | Comune dell'ente | **assente nel CIG** | Il CIG ha solo `cf_amministrazione_appaltante`. Il comune viene dall'anagrafica `stazioni-appaltanti` (`citta_codice` ISTAT / `citta_nome`). |
  | Provincia | `provincia`, `luogo_istat` | Si riferiscono al **luogo di esecuzione**, non alla sede dell'ente. Non usati per la provincia del conteggio. |
  | Importo | `importo_lotto`, `importo_complessivo_gara` | Sempre compilati per le procedure competitive. |
  | CPV | `cod_cpv`, `descrizione_cpv`, `flag_prevalente` | Sempre compilato; abbiamo usato il CPV prevalente. |
  | Tipo di procedura | `tipo_scelta_contraente` | Usato per escludere gli affidamenti diretti. |
  | Stato | `ESITO`, `DATA_CANCELLAZIONE` | Usati per escludere le gare già aggiudicate, revocate, deserte o cancellate. |
  | Data pubblicazione | `data_pubblicazione` | Usata per la finestra dei 60 giorni. |

- **`pubblicazioni`** (stessa cadenza mensile): `cig`, `data_creazione`, `data_albo`, `data_guri`, `data_guce`, `data_bore`, `SCADENZA_INVITO`, `DATA_LETTERA_INVITO`. Serve solo a recuperare la scadenza quando `data_scadenza_offerta` è vuota (31 gare su 351).
- **`stazioni-appaltanti`** (anagrafica, ultimo aggiornamento 2026-08-06): `codice_fiscale`, `denominazione`, `provincia_codice` (es. `IT-MI`), `provincia_nome` (spesso vuoto), `citta_codice` (ISTAT), `citta_nome`. Su 48.040 enti: 45.309 hanno codice e nome del comune, 2.521 solo il nome, 210 nessuno dei due.
- Altri dataset presenti nel catalogo (70 in tutto) ma **non usati**: `smartcig` (affidamenti sotto soglia, esclusi per definizione), `aggiudicazioni`, `aggiudicatari`, i file annuali `cig-AAAA`.

### TED (api.ted.europa.eu) – solo per confronto

Bandi di gara (`notice-type` cn-standard, cn-social, cn-desg) con `buyer-country=ITA` pubblicati nella finestra. Copre **solo le gare sopra soglia UE**.

| Campo richiesto | Campo TED | Note |
|---|---|---|
| Scadenza offerta | `deadline-receipt-tender-date-lot` | Per lotto. |
| Comune dell'ente | `buyer-city` | Testo libero: a volte contiene un indirizzo, il nome in inglese (*Milan*) o in tedesco. La provincia si ricava confrontando il nome con la tabella ISTAT. Il filtro per NUTS del committente non è disponibile nell'API (`organisation-nuts-buyer` dà "Unknown search field"). |
| Importo | `estimated-value-lot`, `estimated-value-proc` | |
| CPV | `classification-cpv` | |
| CIG | **assente** | `internal-identifier-lot` contiene identificativi interni (`LOT-0001`, numeri di pratica). Il confronto con ANAC è quindi approssimato (stessa provincia e stessa data di scadenza). |

### Regione Lombardia – "Bandi di gara Osservatorio Regionale" (`k6cb-4hbm`) – solo per confronto

Elenco dei bandi inseriti dalle stazioni appaltanti nel portale dell'Osservatorio regionale. Campi: `codice_bando`, `stazione_appaltante`, `codice_fiscale`, `provincia`, `comune`, `procedura_gara`, `stato_bando`, `importo_complessivo_base`, `importo_lotto`, `data_pubblicazione`, `data_presentazioni_offerte` (scadenza), `codice_cpv`, `cig`, `cup`.

- **Copertura molto bassa**: 98 bandi distinti in 60 giorni, di cui 4 non affidamenti diretti con scadenza futura. Molte SA lombarde evidentemente non lo alimentano più.
- `comune` e `provincia` sono vuoti in circa il 40% dei casi, e `data_pubblicazione` nell'87%. Per questo la finestra è stata applicata su pubblicazione **o** scadenza.

## Scelte di metodo

1. **SA lombarda** significa che il comune della sede nell'anagrafica ANAC è in Lombardia, secondo la tabella ISTAT (`data/comuni_province.csv`). Sono quindi inclusi anche gli enti con `sezione_regionale` "CENTRALE" ma sede in Lombardia (es. Università degli Studi di Brescia). Sono esclusi gli enti con sede altrove che fanno gare in Lombardia (es. Consip, Invitalia).
2. **Comune → provincia**: si usa prima il codice ISTAT del comune; in mancanza, il nome normalizzato; per comuni soppressi o fusi si ripiega sulla sigla di provincia dell'anagrafica (2 gare su 351).
3. **Procedure tenute**: procedura aperta, ristretta, negoziata senza previa pubblicazione (cioè con invito: art. 50 sottosoglia e art. 76), negoziata previa pubblicazione, negoziata con indizione (settori speciali). **Escluse**: tutti gli affidamenti diretti (anche in house e in adesione ad accordo quadro), "altra procedura a fase unica / a più fasi" (tipicamente rilanci su accordi quadro e sistemi dinamici), "procedura di gara" generica, ND.
4. **Ancora aperta** vuol dire: senza esito, non cancellata, e con scadenza (offerta o invito) ≥ 2026-10-06. I lotti senza alcuna scadenza (29) sono **scartati**, non stimati.
5. **Unità di conteggio**: la gara (`numero_gara` + CF dell'ente). La macro-categoria e il CPV sono quelli del lotto aperto di importo maggiore. "Sotto 40.000 €" si basa su `importo_complessivo_gara`.
6. Nelle tabelle 1 e 2 le colonne "Con importo / scadenza / comune" sono al 100% **per costruzione**: senza scadenza la gara non entra nel conteggio, e importo e comune risultano sempre compilati. La completezza reale, misurata prima dei filtri, è nella sezione 4 del report.

## Limiti noti

- **Ritardo ANAC**: l'ultimo dato è del 2026-10-01, giornata parziale (file pubblicato il 2026-10-05). Le gare pubblicate dal 2 al 6 ottobre mancano. Il confronto con TED lo conferma: dei 28 bandi TED lombardi aperti pubblicati dopo il 1° ottobre, 16 non si trovano in ANAC.
- Il conteggio "aperte" è una **fotografia** al 2026-10-06. Le negoziate hanno scadenze brevi, quindi sono sotto-rappresentate rispetto al flusso. Per stimare il volume di una newsletter è più indicativa la colonna "Gare pubblicate nei 60 gg", che conta le procedure competitive pubblicate, anche se già scadute.
- Nella finestra, 19 bandi TED lombardi aperti non hanno una corrispondenza ANAC con lo stesso criterio. Il confronto è approssimato: possono pesare scadenze diverse tra le due fonti o rettifiche pubblicate come nuovo avviso; tra questi ci sono anche 2 avvisi di istituzioni UE con sede a Ispra (VA), che non sono stazioni appaltanti italiane.

## Aggiunte (approfondimenti)

- **Campo per manifestazioni di interesse, indagini di mercato, elenchi fornitori: non esiste** nel dataset `cig`. `tipo_scelta_contraente` distingue solo affidamenti diretti, aperta, ristretta, negoziate e due voci generiche ("altra procedura a fase unica / a più fasi"); `MODALITA_INDIZIONE_*` e `STRUMENTO_SVOLGIMENTO` sono quasi sempre vuoti. Si può solo cercare nell'oggetto del CIG: è una stima per difetto, dettagli in `output/approfondimenti.md`, sezione 7.
- **Frequenza di aggiornamento**: un file `cig` e un file `pubblicazioni` al mese, rilasciati tra il giorno 2 e il giorno 27 del mese (di norma entro i primi 10 giorni). Il file contiene i CIG fino a 1-4 giorni prima del rilascio. Ritardo misurato dalla pubblicazione alla prima comparsa: mediana 16 giorni, 90° percentile 28, massimo 33 (sezione 4 di `output/approfondimenti.md`).
- **Procedure "su invito"**: la negoziata senza previa pubblicazione non distingue le procedure precedute da un avviso pubblico di manifestazione di interesse da quelle con inviti diretti.
