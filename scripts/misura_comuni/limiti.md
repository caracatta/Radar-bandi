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
