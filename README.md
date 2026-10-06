# Radar bandi – Lombardia

Conteggio dei bandi di gara aperti delle stazioni appaltanti lombarde, per
provincia e macro-settore CPV. Serve a scegliere l'area di partenza di un
servizio di newsletter sui bandi.

- Risultati: [`output/report.md`](output/report.md). Dati in
  `output/tabella_provincia.csv`, `output/tabella_provincia_macro.csv` e
  l'elenco delle gare in `output/bandi_lombardia_aperti.csv`.
- Approfondimenti (aperte vs invito, importi, scadenze, ritardo dei dati,
  servizi tecnici, sanità, manifestazioni di interesse, affidamenti diretti):
  [`output/approfondimenti.md`](output/approfondimenti.md)
- **Misura sui siti dei comuni** (campione di 40, avvisi aperti, famiglie di
  gestionale, confronto con ANAC): [`docs/misura_siti_comuni.md`](docs/misura_siti_comuni.md),
  campione in [`docs/campione_comuni.md`](docs/campione_comuni.md), dati in
  `data/misura_comuni/`
- Fonti, campi e limiti: [`docs/nota_fonti.md`](docs/nota_fonti.md)
- Mappatura CPV → macro-categoria: [`config/cpv_macro.csv`](config/cpv_macro.csv)
- Tabella comune → provincia (ISTAT): `data/comuni_province.csv`

## Rigenerare

```sh
python3 scripts/scarica_fonti.py --oggi 2026-10-06 --giorni 60   # ~700 MB in data/raw/ (non versionata)
python3 scripts/analisi_lombardia.py --oggi 2026-10-06 --giorni 60
python3 scripts/approfondimenti.py --oggi 2026-10-06 --giorni 60
```

Solo libreria standard di Python 3. Lo script di download riusa i file ANAC
già presenti in `data/raw/anac/`.

## Misura sui siti dei comuni (esplorativa)

```sh
python3 scripts/campione_comuni.py                 # estrae il campione (seme fisso)
python3 scripts/misura_comuni/risolvi_siti.py      # trova i siti (rispetta robots.txt)
python3 scripts/misura_comuni/esplora.py           # scarica home e pagine bandi/albo
python3 scripts/misura_comuni/jcity_tutti.py       # albo e liste dei comuni su J-City (export CSV)
python3 scripts/misura_comuni/anac_campione.py     # CIG dei 40 comuni dai file ANAC
python3 scripts/misura_comuni/risultati.py         # tabelle e report
```

Non è uno scraper di produzione: richieste con User-Agent identificato, robots.txt
rispettato, al massimo una richiesta ogni 1,3 s per sito, niente login. `browser.py`
(Chromium headless, richiede `pip install playwright`) serve solo a documentare un
tentativo scartato.
