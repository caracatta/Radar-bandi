# Radar bandi – Lombardia

Conteggio dei bandi di gara aperti delle stazioni appaltanti lombarde, per
provincia e macro-settore CPV. Serve a scegliere l'area di partenza di un
servizio di newsletter sui bandi.

- Risultati: [`output/report.md`](output/report.md). Dati in
  `output/tabella_provincia.csv`, `output/tabella_provincia_macro.csv` e
  l'elenco delle gare in `output/bandi_lombardia_aperti.csv`.
- Fonti, campi e limiti: [`docs/nota_fonti.md`](docs/nota_fonti.md)
- Mappatura CPV → macro-categoria: [`config/cpv_macro.csv`](config/cpv_macro.csv)
- Tabella comune → provincia (ISTAT): `data/comuni_province.csv`

## Rigenerare

```sh
python3 scripts/scarica_fonti.py --oggi 2026-10-06 --giorni 60   # ~700 MB in data/raw/ (non versionata)
python3 scripts/analisi_lombardia.py --oggi 2026-10-06 --giorni 60
```

Solo libreria standard di Python 3. Lo script di download riusa i file ANAC
già presenti in `data/raw/anac/`.
