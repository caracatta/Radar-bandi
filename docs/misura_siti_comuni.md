# Misura: avvisi aperti sui siti dei comuni lombardi

Data della misura: **2026-10-06**. Finestra: ultimi 30 giorni di pubblicazione, ma contando come "aperto" tutto ciò che a oggi è ancora in corso. È un test di misura sul campione (`docs/campione_comuni.md`), non uno scraper di produzione; script in `scripts/misura_comuni/`, dati in `data/misura_comuni/`.

## Come ho misurato

- Programma identificato nello User-Agent, **robots.txt rispettato** (anche il Crawl-delay: Mazzano chiede 10 s), al massimo una richiesta ogni 1,3 secondi per sito, solo GET, **nessun login**, nessun aggiramento di blocchi. Circa 448 richieste di pagina (comprese quelle fallite o bloccate da robots.txt) su 129 host, più un robots.txt per host.
- Per ogni comune: home, albo pretorio, Amministrazione trasparente (Bandi di gara e contratti), pagine Avvisi/Bandi/Gare e le piattaforme collegate, nei limiti di ciò che il sito lascia leggere.
- **Avviso aperto** = manifestazione di interesse, indagine di mercato, elenco fornitori, bando sotto soglia o gara aperta a cui un'impresa può rispondere, non ancora scaduto al 6 ottobre. Esclusi concorsi, contributi, avvisi ai cittadini, affidamenti già assegnati. Le aste di vendita, i bandi per posteggi e simili sono riportati a parte (categoria B) e non contati.
- "Confermato" = scadenza non passata, letta dal sito o da ANAC (quando l'elenco del sito non la riporta). "Non verificato" = trovato ma scadenza non leggibile.

## 1. Risultato per fascia

| | Fascia A (> 10.000 ab.) | Fascia B (5.000-10.000 ab.) |
|---|---:|---:|
| Comuni nel campione | 20 | 20 |
| Comuni in Lombardia nella fascia | 196 | 278 |
| Letti con albo e sezione bandi ("completo") | 13 | 7 |
| Letti solo in parte (poche pagine) | 5 | 8 |
| Non letti: robots.txt vieta tutto | 2 | 4 |
| Non letti: sito irraggiungibile | 0 | 1 |
| **Avvisi aperti trovati** (confermati + non verificati) | **3** | **0** |
| Avvisi per comune, media (comuni letti completi+parziali) | 0,17 | 0,00 |
| Avvisi per comune, mediana (idem) | 0,00 | 0,00 |
| Comuni con zero avvisi (letti completi+parziali) | 15 | 15 |
| Comuni con almeno un avviso (idem) | 3 | 0 |
| Media sui soli comuni "completi" | 0,23 | 0,00 |
| Zero / almeno uno nei soli "completi" | 10 / 3 | 7 / 0 |
| Altri avvisi aperti non appalto (categoria B) | 2 | 2 |

I comuni non letti **non** sono contati come zero: sono fuori dai denominatori delle righe "comuni letti". Per i 13 comuni letti solo in parte, lo zero significa "niente di visibile lì", non "niente".

### Avvisi aperti trovati

| Comune | Esito | Oggetto | Settore | Scadenza (fonte) | Importo | CIG | In ANAC |
|---|---|---|---|---|---:|---|---|
| Leno | conteggiato | Concessione del servizio di somministrazione di alimenti e bevande mediante distributori automatici, 3 anni | Forniture di beni | 2026-10-12 (ANAC) | 29436.0 | BCC7BCB593 | sì |
| Caronno Pertusella | conteggiato | Affidamento copertura assicurativa All Risks, 31/12/2026-30/06/2029 | Servizi tecnici, IT e professionali | 2026-10-22 (ANAC) | 180780.0 | BCFEB740B9 | sì |
| Cormano | non verificato | Affidamento in concessione del servizio di somministrazione di bevande e alimenti mediante distributori automatici presso le sedi comunali (determina 638/2026) | Forniture di beni (per analogia con Leno) | non letta (-) | non letto (allegato 'Stima PEF') | assente sul sito | no |

Tipo di procedura e URL di ciascuno sono in `data/misura_comuni/avvisi_trovati.csv`, insieme agli avvisi di categoria B ed esclusi:

- **Sarezzo** (B, non contato): Bando di selezione per il rilascio di autorizzazioni e concessioni in posteggi vacanti nei mercati; rilevante per imprese, ma non è una gara.
- **Sirmione** (B, non contato): Bando per concessione demaniale di spiaggia attrezzata e deposito pedalò, canoe, sup (altro comune); pubblicato all'albo del comune per conto di un altro ente.
- **Pieve Emanuele** (B, non contato): Vendita immobile comunale in Piazza Puccini: avviso di asta pubblica; visto solo nell'elenco novità; non aperta la scheda.
- **Lodi Vecchio** (B, non contato): Avviso pubblico per manifestazione di interesse alla sponsorizzazione di eventi (avviso non trovato); nell'albo c'è solo la delibera; la pagina Avvisi del sito è vuota senza JavaScript.
- Lurago d'Erba (escluso): manifestazione di interesse riservata ad associazioni del Terzo settore, non imprese.
- Cormano (escluso): albo associazioni: non rilevante per imprese.
- Olgiate Comasco (escluso): aste di locazione abitazioni del Fondo edifici di culto, altro ente.
- Cabiate (escluso): aste di locazione abitazioni del Fondo edifici di culto, altro ente.

## 2. Famiglie di gestionale

Sono due livelli distinti: il **CMS del sito** (vetrina) e il **gestionale dell'albo/trasparenza**, dove stanno davvero gli atti.

### Gestionale dell'albo pretorio

| Famiglia | Comuni | Elenco |
|---|---:|---|
| J-City Gov / Albo online | 21 | Bernareggio, Brembate di Sopra, Cabiate, Caronno Pertusella, Cormano, Cornate d'Adda, Gerenzano, Giussano, Ispra, Leno, Lurago d'Erba, Magenta, Mazzano, Olgiate Comasco, Pandino, Pieve Emanuele, San Colombano al Lambro, Sarezzo, Seveso, Sirmione, Vimercate |
| non determinabile (sito non letto) | 7 | Arosio, Bonate Sotto, Casorezzo, Mortara, Robecco sul Naviglio, San Fermo della Battaglia, Varese |
| Halley | 3 | Borgo Virgilio, Grumello del Monte, Spino d'Adda |
| OpenWeb | 2 | Locate di Triulzi, Sondrio |
| DG eGov | 2 | Cuggiono, Rodigo |
| Drupal in sito: albo senza elenco in HTML | 1 | Ospitaletto |
| Hypersic | 1 | Lodi Vecchio |
| ServiziOnLine | 1 | Poggio Rusco |
| Halley eGov | 1 | Vaprio d'Adda |
| Urbi / PA Digitale | 1 | Arcisate |

### CMS del sito

| Famiglia | Comuni | Elenco |
|---|---:|---|
| Municipium (Maggioli) | 16 | Bernareggio, Borgo Virgilio, Brembate di Sopra, Caronno Pertusella, Cormano, Cornate d'Adda, Gerenzano, Giussano, Leno, Lurago d'Erba, Pieve Emanuele, San Colombano al Lambro, Seveso, Sirmione, Vaprio d'Adda, Vimercate |
| MyCity (asset mycity.s3...ovh) | 7 | Arcisate, Cuggiono, Olgiate Comasco, Pandino, Poggio Rusco, Sarezzo, Spino d'Adda |
| non determinabile (sito non letto) | 7 | Arosio, Bonate Sotto, Casorezzo, Mortara, Robecco sul Naviglio, San Fermo della Battaglia, Varese |
| WordPress | 2 | Ispra, Magenta |
| SecovalWEB - Modello Comuni | 1 | Mazzano |
| Drupal 9 (footer Halley) | 1 | Ospitaletto |
| non identificato | 1 | Locate di Triulzi |
| WordPress (bandi come tipo di contenuto) | 1 | Sondrio |
| Drupal 9 (Halley) | 1 | Grumello del Monte |
| OpenCity Italia (Opencontent) | 1 | Cabiate |
| eCOMUNE (Pacchetto PNRR) | 1 | Lodi Vecchio |
| WordPress (Datagraph) | 1 | Rodigo |

**9 famiglie di albo** e **11 famiglie di CMS** tra i 33 siti di cui ho potuto vedere qualcosa. Un solo gestionale (J-City Gov di Maggioli) copre 21 comuni su 33 (20 letti; Giussano ha un certificato non valido) e ha un'uscita CSV standard che funziona allo stesso modo ovunque. Gli altri 12 sono singoli o a coppie e solo uno (Lodi Vecchio, Hypersic) ha un albo leggibile in HTML; Sondrio ha l'elenco bandi leggibile nel sito. Il resto vieta l'accesso automatico, risponde 403 o non risponde.

## 3. Confronto con ANAC

**Dagli avvisi trovati verso ANAC.** Dei 3 avvisi aperti trovati sui siti, 2 riportano un CIG e **compaiono in ANAC** (Leno e Caronno Pertusella); 1 non ha CIG sul sito e non è in ANAC (Cormano: pubblicato il 14/09, i dati ANAC arrivano al 01/10 e una manifestazione di interesse spesso non ha ancora il CIG). Gli avvisi di categoria B non hanno CIG e non sono appalti.

**Da ANAC verso i siti (il controllo inverso, più informativo).** Per i 40 comuni, ANAC ha 63 procedure competitive (non affidamenti diretti) pubblicate dal 1° giugno e 603 affidamenti diretti. Quelle **ancora aperte al 2026-10-06** (scadenza offerte ≥ oggi) sono 6:

| Comune | Procedura | Scadenza | Importo € | Sito leggibile? | Trovata sul sito? |
|---|---|---|---:|---|---|
| Caronno Pertusella | Aperta - Affidamento copertura assicurativa all risks (dalle ore | 2026-10-22 | 180.780 | sì | sì (solo determina a contrarre) |
| Leno | Negoziata Previa Pubblicazione - Concessione del servizio di somministrazione di aliment | 2026-10-12 | 29.436 | sì | sì (albo + trasparenza) |
| Mortara | Negoziata Senza Previa Pubblicaz - Fornitura di libri per la biblioteca del comune di mort | 2026-10-22 | 16.000 | no (robots.txt) | non verificabile (robots.txt) |
| Seveso | Aperta - Procedura aperta per l'affidamento della progettazione  | 2026-10-08 | 3.573.743 | sì | **no**. non nelle liste lette |
| Varese | Aperta - Procedura aperta per l'affidamento in appalto del servi | 2026-10-16 | 142.244.091 | no (robots.txt) | non verificabile (robots.txt) |
| Varese | Negoziata Senza Previa Pubblicaz - Servizio di comunicazione istituzionale finalizzato all | 2026-10-06 | 180.000 | no (robots.txt) | non verificabile (robots.txt) |

Su 6 procedure aperte note ad ANAC, 3 sono di comuni che vietano l'accesso (non verificabili); delle 3 su comuni leggibili ne ho ritrovate sul sito **2**; la terza (Seveso, appalto integrato per la scuola dell'infanzia, 3,57 milioni, scadenza 08/10) **non** compare nelle liste dell'albo e della trasparenza che ho letto. Inoltre 7 procedure di settembre (Locate di Triulzi 1, Rodigo 1, Sirmione 5) non hanno ancora una scadenza in ANAC; per Sirmione non ho trovato corrispondenza sul sito: sono verosimilmente procedure su invito (non lo posso confermare).

**Cosa dice il confronto sul volume.** Le 63 procedure competitive di ANAC in 4 mesi su 40 comuni (circa 16 al mese, 0,4 per comune al mese, comprese le negoziate su invito) e le sole 6 ancora aperte oggi (di cui 3 su siti non leggibili) sono coerenti con il flusso basso visto sui siti. Non ho prove su dove si pubblichino le gare che non trovo sui siti: la mia ipotesi, da verificare, è che passino da piattaforme di acquisto (Sintel, ecc.).

### Leggibilità automatica (40 comuni, una sola riga ciascuno)

| Modalità | Comuni |
|---|---:|
| J-City Gov: elenchi non nell'HTML, ma leggibili dal CSV "OpenFormat" del portale (20 letti, più Giussano con certificato non valido) | 20 |
| Altri: elenco in HTML leggibile (Sondrio: bandi; Lodi Vecchio: albo) | 2 |
| Elenchi assenti dall'HTML senza JavaScript (Ospitaletto) | 1 |
| Solo pagine novità/avvisi leggibili; albo e trasparenza bloccati (robots.txt, 403, TLS/503, reset) | 10 |
| Non letti: robots.txt vieta tutto | 6 |
| Non letti: sito irraggiungibile | 1 |

PDF: ne ho letto uno (Vaprio d'Adda, testuale, non pertinente); nessun PDF scansionato incontrato; nessun sito "solo piattaforma con login" osservato. Gli allegati dei bandi dei portali J-City non sono raggiungibili con link semplici, quindi non li ho aperti.

## 4. Comune per comune

Dettaglio completo (pagine usate, gestionali, avvisi) in `data/misura_comuni/comuni_risultati.csv`.

| F | Comune | Lettura | Albo (gestionale) | Aperti | Difficoltà |
|---|---|---|---|---:|---|
| A | Leno | completo | J-City Gov / Albo online (Maggioli) | 1 | elenchi non presenti nell'HTML: serve seguire il link 'Esporta in OpenFormat' e una sessione; la scadenza non  |
| A | Mazzano | completo | J-City Gov / Albo online (Maggioli) | 0 | robots.txt con Crawl-delay 10 s, rispettato; elenchi non presenti nell'HTML: serve seguire il link 'Esporta in |
| A | Ospitaletto | parziale | Drupal in sito: albo senza elenco in HTML | 0 | albo pretorio e trasparenza non mostrano elenchi in HTML; connessioni resettate su alcune pagine |
| A | Sarezzo | completo | J-City Gov / Albo online (Maggioli) | 0 | elenchi non presenti nell'HTML: serve seguire il link 'Esporta in OpenFormat' e una sessione; la scadenza non  |
| A | Olgiate Comasco | completo | J-City Gov / Albo online (Maggioli) | 0 | elenchi non presenti nell'HTML: serve seguire il link 'Esporta in OpenFormat' e una sessione; la scadenza non  |
| A | Borgo Virgilio | parziale | Halley (halleyweb.com) | 0 | halleyweb.com non raggiungibile da qui (errore TLS/503) |
| A | Cormano | completo | J-City Gov / Albo online (Maggioli) | 1 | elenchi non presenti nell'HTML: serve seguire il link 'Esporta in OpenFormat' e una sessione; la scadenza non  |
| A | Locate di Triulzi | parziale | OpenWeb (servizi.*/openweb) | 0 | albo e trasparenza rispondono HTTP 403 al programma |
| A | Magenta | completo | J-City Gov / Albo online (Maggioli) | 0 | elenchi non presenti nell'HTML: serve seguire il link 'Esporta in OpenFormat' e una sessione; la scadenza non  |
| A | Pieve Emanuele | completo | J-City Gov / Albo online (Maggioli) | 0 | nessuna lista 'Pubblicazione' nel menu trasparenza; elenchi non presenti nell'HTML: serve seguire il link 'Esp |
| A | Bernareggio | completo | J-City Gov / Albo online (Maggioli) | 0 | elenchi non presenti nell'HTML: serve seguire il link 'Esporta in OpenFormat' e una sessione; la scadenza non  |
| A | Cornate d'Adda | completo | J-City Gov / Albo online (Maggioli) | 0 | elenchi non presenti nell'HTML: serve seguire il link 'Esporta in OpenFormat' e una sessione; la scadenza non  |
| A | Giussano | parziale | J-City Gov / Albo online (Maggioli) su alb | 0 | certificato TLS non valido sul sottodominio dell'albo: non letto |
| A | Seveso | completo | J-City Gov / Albo online (Maggioli) | 0 | elenchi non presenti nell'HTML: serve seguire il link 'Esporta in OpenFormat' e una sessione; la scadenza non  |
| A | Vimercate | completo | J-City Gov / Albo online (Maggioli) (perco | 0 | nessuna lista 'Pubblicazione' nel menu trasparenza; elenchi non presenti nell'HTML: serve seguire il link 'Esp |
| A | Mortara | robots | robots.txt vieta ogni accesso | - | robots.txt: Disallow: / |
| A | Sondrio | parziale | OpenWeb (sondrio.soluzionipa.it) | 0 | albo HTTP 403 al programma; elenco 'Bandi in corso' solo con filtro JS |
| A | Caronno Pertusella | completo | J-City Gov / Albo online (Maggioli) | 1 | elenchi non presenti nell'HTML: serve seguire il link 'Esporta in OpenFormat' e una sessione; la scadenza non  |
| A | Gerenzano | completo | J-City Gov / Albo online (Maggioli) | 0 | lista 'Pubblicazione' vuota; elenchi non presenti nell'HTML: serve seguire il link 'Esporta in OpenFormat' e u |
| A | Varese | robots | robots.txt vieta ogni accesso | - | robots.txt: Disallow: / |
| B | Bonate Sotto | robots | robots.txt vieta ogni accesso | - | robots.txt: Disallow: / |
| B | Brembate di Sopra | completo | J-City Gov / Albo online (Maggioli) | 0 | elenchi non presenti nell'HTML: serve seguire il link 'Esporta in OpenFormat' e una sessione; la scadenza non  |
| B | Grumello del Monte | parziale | Halley (halleyweb.com) | 0 | halleyweb.com non raggiungibile da qui (HTTP 503) |
| B | Sirmione | completo | J-City Gov / Albo online (Maggioli) | 0 | elenchi non presenti nell'HTML: serve seguire il link 'Esporta in OpenFormat' e una sessione; la scadenza non  |
| B | Arosio | robots | robots.txt vieta ogni accesso | - | robots.txt: Disallow: / |
| B | Cabiate | completo | J-City Gov / Albo online (Maggioli) | 0 | albo senza voce di menu: letto dall'export della pagina; elenchi non presenti nell'HTML: serve seguire il link |
| B | Lurago d'Erba | completo | J-City Gov / Albo online (Maggioli) | 0 | elenchi non presenti nell'HTML: serve seguire il link 'Esporta in OpenFormat' e una sessione; la scadenza non  |
| B | San Fermo della Battaglia | robots | robots.txt vieta ogni accesso | - | robots.txt: Disallow: / |
| B | Pandino | completo | J-City Gov / Albo online (Maggioli) | 0 | la lista 'Pubblicazione' contiene atti del 2024-25 ripubblicati a settembre 2026; elenchi non presenti nell'HT |
| B | Spino d'Adda | parziale | Halley (halleyweb.com) | 0 | halleyweb.com non raggiungibile da qui (TLS/503) |
| B | Lodi Vecchio | parziale | Hypersic (servizionline.hspromilaprod) | 0 | pagina Avvisi vuota senza JavaScript |
| B | Poggio Rusco | parziale | ServiziOnLine (servizi.comune.*) | 0 | connessione resettata dal server dell'albo |
| B | Rodigo | parziale | DG eGov (dgegovpa.it) | 0 | dgegovpa.it: robots.txt vieta l'accesso |
| B | Casorezzo | robots | robots.txt vieta ogni accesso | - | robots.txt: Disallow: / |
| B | Cuggiono | parziale | DG eGov (dgegovpa.it) | 0 | dgegovpa.it: robots.txt vieta l'accesso |
| B | Robecco sul Naviglio | irraggiungibile | - | - | errore TLS (EOF) su tutti i domini provati |
| B | San Colombano al Lambro | completo | J-City Gov / Albo online (Maggioli) | 0 | elenchi non presenti nell'HTML: serve seguire il link 'Esporta in OpenFormat' e una sessione; la scadenza non  |
| B | Vaprio d'Adda | parziale | Halley eGov (halleyegov.it) / Urbi | 0 | albo e trasparenza: robots.txt vieta l'accesso |
| B | Arcisate | parziale | Urbi / PA Digitale (servizi.comune.*/urbi) | 0 | albo e trasparenza: robots.txt vieta l'accesso |
| B | Ispra | completo | J-City Gov / Albo online (Maggioli) | 0 | elenchi non presenti nell'HTML: serve seguire il link 'Esporta in OpenFormat' e una sessione; la scadenza non  |

## 5. Limiti e cosa non ho potuto verificare

**Il campione è piccolo e sbilanciato.** 40 comuni su 474 (8,4%), estratti a caso
con seme fisso. Tra i 40 ci sono 6 comuni che vietano l'accesso con robots.txt e
1 irraggiungibile, 13 letti solo in parte: i numeri per fascia
poggiano su 15-18 comuni ciascuna. Con 3 avvisi trovati in totale, ogni stima
di media o proporzione ha un'incertezza enorme: la differenza tra le due fasce
(3 contro 0) **non è statisticamente distinguibile**.

**Il conteggio è un limite inferiore.**
- Il gestionale più diffuso (J-City Gov, 21 comuni su 33) non mette l'elenco nell'HTML: l'ho
  letto dal file CSV ("Esporta in OpenFormat") che la pagina stessa propone, ma
  contiene solo ciò che è pubblicato in quelle sezioni, e per l'albo solo ciò che è in
  pubblicazione oggi (di solito 15-30 giorni).
- **Un appalto vero mi è sfuggito**: a Seveso ANAC mostra una procedura aperta da
  3,57 milioni (scadenza 08/10) che non compare nell'albo né nella sezione "Pubblicazione"
  della trasparenza. Sarà su una piattaforma di gara o in una sezione che non ho trovato.
  Quindi anche nei comuni "completi" il recall non è del 100%.
- Le date dei portali non sono affidabili per filtrare: a Pandino la lista "Pubblicazione"
  riporta come pubblicate a settembre 2026 determine del 2024-25 (ricaricate per la
  trasparenza). Per questo ho usato il CIG e ANAC per capire se un avviso è
  davvero aperto, non solo la data di pubblicazione.
- Non ho aperto gli allegati (bando, disciplinare): nei portali J-City i link agli
  allegati non sono link semplici. Quindi **scadenza e importo** degli avvisi trovati
  vengono da ANAC, non dal sito, tranne Cormano (non verificato).
- Nessun PDF scansionato incontrato, ma anche pochissimi PDF letti (uno, testuale).

**Cosa non ho potuto verificare.**
- I 6 comuni con `Disallow: /` per tutti (Varese, Mortara, Bonate Sotto, Arosio, San Fermo
  della Battaglia, Casorezzo): non ho letto nulla. Due di essi (Varese, Mortara) hanno
  procedure aperte in ANAC. Non ho aggirato il divieto.
- Gli albi su Halley (halleyweb.com: 503/errore TLS da questo ambiente), DG eGov (robots.txt),
  Urbi e Halley eGov (robots.txt), OpenWeb (HTTP 403 al programma) e ServiziOnLine (connessione
  resettata): 10 comuni dove vedo solo le pagine novità. Alcuni errori potrebbero essere legati
  a questo ambiente (proxy, IP del data center) e non al sito.
- Le piattaforme di acquisto (Sintel/ARIA, ASMECOMM, ecc.): solo Olgiate Comasco ne cita una
  nella home; non ho cercato di accedervi, e comunque le gare vere si vedono lì, non sui siti.
- Gli avvisi pubblicati dopo il 1° ottobre: ANAC non li ha ancora e sui siti li ho cercati
  solo con parole chiave.
- La classificazione "avviso aperto a un'impresa" è stata fatta da me leggendo gli oggetti,
  con un filtro per parole chiave: possibili falsi negativi. L'ho verificata contro ANAC
  solo per le procedure con CIG.

**Cose che ho provato e scartato.** Un browser headless (Chromium) per leggere gli
albi che si compongono in JavaScript: una sola pagina ha richiesto 193 richieste e
254 secondi con il limite di una al secondo, e l'elenco non compariva comunque senza
interazione. Per questo è un dato di misura utile per il monitoraggio giornaliero.

**Verso una decisione.** Questi dati dicono che, sui siti dei comuni, gli avvisi
aperti per le imprese sono pochi (circa uno ogni 10 comuni letti nei 30 giorni) e
mal esposti: un monitoraggio giornaliero dei siti darebbe poco e richiederebbe un lavoro
per gestionale. Non dicono che le opportunità siano poche: quelle vere
(ANAC: 351 gare aperte in Lombardia al 6 ottobre) passano da altri canali.

