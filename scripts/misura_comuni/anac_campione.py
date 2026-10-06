"""Estrae dai file ANAC già scaricati (data/raw/anac/*-cig_csv.csv) tutti i CIG
dei comuni del campione pubblicati dal 2026-06-01, per il confronto con
quanto visto sui siti. Scrive data/misura_comuni/anac_campione.csv."""
import collections
import csv
import pathlib
import re
import unicodedata
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
csv.field_size_limit(10**9)


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Z0-9]+", " ", s.upper()).strip()


def cf_comuni():
    camp = list(csv.DictReader(open(ROOT / "data" / "campione_comuni.csv",
                                    encoding="utf-8")))
    sa = list(csv.DictReader(open(ROOT / "data" / "raw" / "anac" /
                                  "stazioni-appaltanti_csv.csv",
                                  encoding="utf-8", errors="replace"),
                             delimiter=";"))
    out = {}
    for c in camp:
        n = norm(c["comune"])
        cand = [r for r in sa if norm(r["denominazione"]) == f"COMUNE DI {n}"]
        cand = [r for r in cand if r["citta_codice"] == c["codice_istat"]] \
            or cand
        for r in cand:
            out[r["codice_fiscale"]] = c["comune"]
    return out


def main():
    cfs = cf_comuni()
    righe = {}
    for f in sorted((ROOT / "data" / "raw" / "anac").glob("*-cig_csv.csv")):
        for r in csv.DictReader(open(f, encoding="utf-8", errors="replace"),
                                delimiter=";"):
            cf = r["cf_amministrazione_appaltante"]
            if cf in cfs and r["data_pubblicazione"] >= "2026-06-01":
                righe[r["cig"]] = {
                    "comune": cfs[cf], "cig": r["cig"],
                    "numero_gara": r["numero_gara"],
                    "oggetto": r["oggetto_gara"][:200],
                    "tipo_scelta": r["tipo_scelta_contraente"],
                    "data_pubblicazione": r["data_pubblicazione"],
                    "data_scadenza_offerta": r["data_scadenza_offerta"],
                    "importo_lotto": r["importo_lotto"],
                    "esito": r["ESITO"], "cancellato": r["DATA_CANCELLAZIONE"],
                    "cpv": r["cod_cpv"], "file": f.name[:8]}
    dest = ROOT / "data" / "misura_comuni"
    dest.mkdir(parents=True, exist_ok=True)
    with open(dest / "anac_campione.csv", "w", newline="",
              encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(next(iter(righe.values()))))
        w.writeheader()
        w.writerows(sorted(righe.values(), key=lambda r: (
            r["comune"], r["data_pubblicazione"])))
    print(len(righe), "CIG;", len(cfs), "CF")
    c = collections.Counter((r["tipo_scelta"][:30]) for r in righe.values())
    print(c.most_common(8))


if __name__ == "__main__":
    main()
