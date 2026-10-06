"""Estrae i comuni lombardi per fascia di popolazione e sorteggia il
campione per la misura sugli avvisi dei siti comunali.

Uso: python3 scripts/campione_comuni.py [--seme 20261006] [--n 20]

Input:  data/comuni_province.csv (ISTAT, già generato da analisi_lombardia.py)
        data/raw/istat_pop/POSAS_2026_it_Comuni.csv (popolazione residente
        al 1° gennaio 2026, ISTAT, da demo.istat.it)
Output: data/comuni_lombardi_fasce.csv (tutti i comuni delle due fasce)
        data/campione_comuni.csv       (il campione)
        docs/campione_comuni.md        (come è stato estratto)

Regola di estrazione: random.Random(seme).sample() di n comuni per fascia,
sull'elenco ordinato per codice ISTAT. Il sorteggio è accettato solo se ogni
fascia copre almeno 8 province; altrimenti si ripete con seme+1, e così via.
Tutti i tentativi sono scritti nel documento.
"""
import argparse
import collections
import csv
import pathlib
import random

ROOT = pathlib.Path(__file__).resolve().parent.parent
POP = ROOT / "data" / "raw" / "istat_pop" / "POSAS_2026_it_Comuni.csv"
MIN_PROVINCE = 8


def popolazione():
    pop = collections.Counter()
    nome = {}
    with open(POP, encoding="utf-8-sig") as f:
        f.readline()  # titolo
        for r in csv.DictReader(f, delimiter=";"):
            if r["Età"] == "999":  # riga del totale di tutte le età
                pop[r["Codice comune"]] = int(r["Totale"])
                nome[r["Codice comune"]] = r["Comune"]
    return pop, nome


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seme", type=int, default=20261006)
    ap.add_argument("--n", type=int, default=20)
    a = ap.parse_args()

    pop, nome_pop = popolazione()
    comuni = list(csv.DictReader(open(ROOT / "data" / "comuni_province.csv",
                                      encoding="utf-8")))
    lomb = [c for c in comuni if c["regione"] == "Lombardia"]
    senza_pop = [c["comune"] for c in lomb if c["codice_istat"] not in pop]
    righe = []
    for c in sorted(lomb, key=lambda c: c["codice_istat"]):
        p = pop.get(c["codice_istat"])
        if p is None:
            continue
        fascia = ("A: oltre 10.000" if p > 10000 else
                  "B: 5.000-10.000" if p >= 5000 else None)
        if fascia:
            righe.append({"codice_istat": c["codice_istat"],
                          "comune": c["comune"], "provincia": c["provincia"],
                          "sigla": c["sigla"], "popolazione_2026": p,
                          "fascia": fascia})
    with open(ROOT / "data" / "comuni_lombardi_fasce.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(righe[0]))
        w.writeheader()
        w.writerows(righe)

    per_fascia = {k: [r for r in righe if r["fascia"] == k]
                  for k in ("A: oltre 10.000", "B: 5.000-10.000")}
    tentativi, seme = [], a.seme
    while True:
        rng = random.Random(seme)
        camp = {k: rng.sample(v, a.n) for k, v in per_fascia.items()}
        prov = {k: len({r["provincia"] for r in v}) for k, v in camp.items()}
        tentativi.append((seme, prov))
        if all(p >= MIN_PROVINCE for p in prov.values()):
            break
        seme += 1
    with open(ROOT / "data" / "campione_comuni.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(righe[0]))
        w.writeheader()
        for k, v in camp.items():
            w.writerows(sorted(v, key=lambda r: (r["provincia"],
                                                 r["comune"])))

    tot_pop = sum(len(v) for v in per_fascia.values())
    md = ["# Campione di comuni: come è stato estratto", "",
          "Fonti: elenco dei comuni ISTAT con provincia "
          "(`data/comuni_province.csv`) e popolazione residente al "
          "1° gennaio 2026 (ISTAT, `POSAS_2026_it_Comuni`, somma per età).",
          "",
          f"Comuni lombardi nell'elenco ISTAT: {len(lomb)}; senza "
          f"popolazione nel file 2026: {len(senza_pop)}"
          + (f" ({', '.join(senza_pop[:10])})" if senza_pop else "") + ".", "",
          "| Fascia | Comuni in Lombardia | Estratti |", "|---|---:|---:|"]
    for k, v in per_fascia.items():
        md.append(f"| {k} abitanti | {len(v)} | {a.n} |")
    md += ["", f"Fascia A = popolazione > 10.000; fascia B = da 5.000 a "
           f"10.000 inclusi. In totale {tot_pop} comuni.", "",
           "## Regola di sorteggio", "",
           f"Per ogni fascia: `random.Random(seme).sample(elenco, {a.n})` "
           "(Python), con l'elenco ordinato per codice ISTAT. Un sorteggio "
           f"vale solo se ogni fascia copre almeno {MIN_PROVINCE} province; "
           "altrimenti si ripete con seme+1. Nessun comune scelto a mano.",
           "", "| Seme | Province fascia A | Province fascia B | Esito |",
           "|---:|---:|---:|---|"]
    for s, p in tentativi:
        ok = all(x >= MIN_PROVINCE for x in p.values())
        md.append(f"| {s} | {p['A: oltre 10.000']} | {p['B: 5.000-10.000']} "
                  f"| {'accettato' if ok else 'scartato'} |")
    md += ["", "## Province coperte", "",
           "| Provincia | Fascia A | Fascia B | Totale A in Lombardia | "
           "Totale B in Lombardia |", "|---|---:|---:|---:|---:|"]
    provs = sorted({r["provincia"] for r in righe})
    for pr in provs:
        ca = sum(1 for r in camp["A: oltre 10.000"] if r["provincia"] == pr)
        cb = sum(1 for r in camp["B: 5.000-10.000"] if r["provincia"] == pr)
        ta = sum(1 for r in per_fascia["A: oltre 10.000"]
                 if r["provincia"] == pr)
        tb = sum(1 for r in per_fascia["B: 5.000-10.000"]
                 if r["provincia"] == pr)
        md.append(f"| {pr} | {ca} | {cb} | {ta} | {tb} |")
    md += ["", "## Il campione", "",
           "| Fascia | Comune | Provincia | Abitanti |", "|---|---|---|---:|"]
    for k, v in camp.items():
        for r in sorted(v, key=lambda r: (r["provincia"], r["comune"])):
            md.append(f"| {k[0]} | {r['comune']} | {r['provincia']} | "
                      f"{r['popolazione_2026']:,} |".replace(",", "."))
    (ROOT / "docs" / "campione_comuni.md").write_text("\n".join(md) + "\n",
                                                      encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
