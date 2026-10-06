"""Scarica le fonti per il conteggio dei bandi lombardi.

Uso: python3 scripts/scarica_fonti.py [--oggi AAAA-MM-GG] [--giorni 60]

Scrive i file grezzi in data/raw/ (non versionata) e un log di
raggiungibilità in data/raw/fonti_log.json.
"""
import argparse
import datetime as dt
import json
import pathlib
import time
import urllib.parse
import urllib.request
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

# Il WAF di dati.anticorruzione.it rifiuta lo User-Agent di default di
# curl/urllib: serve un UA da browser.
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
ANAC = "https://dati.anticorruzione.it/opendata"
LOMBARDIA = "https://www.dati.lombardia.it/resource/k6cb-4hbm.json"
TED = "https://api.ted.europa.eu/v3/notices/search"
ISTAT = ("https://www.istat.it/storage/codici-unita-amministrative/"
         "Elenco-comuni-italiani.csv")

log = []


def fetch(url, data=None, headers=None, tentativi=4):
    h = {"User-Agent": UA, "Accept": "*/*", "Accept-Language": "it-IT,it"}
    h.update(headers or {})
    for i in range(tentativi):
        try:
            req = urllib.request.Request(url, data=data, headers=h)
            with urllib.request.urlopen(req, timeout=600) as r:
                body = r.read()
            log.append({"url": url, "esito": 200, "byte": len(body)})
            return body
        except Exception as e:  # il WAF ANAC dà 403 intermittenti
            err = getattr(e, "code", None) or repr(e)
            if i == tentativi - 1:
                log.append({"url": url, "esito": str(err)})
                raise
            time.sleep(2 ** (i + 1))


def anac_risorse(pacchetto):
    url = f"{ANAC}/api/3/action/package_show?id={pacchetto}"
    return json.loads(fetch(url))["result"]["resources"]


def scarica_zip_anac(pacchetto, nome_risorsa):
    out = RAW / "anac" / f"{nome_risorsa}.csv"
    if out.exists():
        return out
    res = [r for r in anac_risorse(pacchetto) if r["name"] == nome_risorsa]
    if not res:
        log.append({"url": f"{pacchetto}/{nome_risorsa}", "esito": "assente"})
        return None
    zpath = RAW / "anac" / f"{nome_risorsa}.zip"
    zpath.write_bytes(fetch(res[0]["url"]))
    with zipfile.ZipFile(zpath) as z:
        nomi = [n for n in z.namelist() if n.endswith(".csv")]
        out.write_bytes(z.read(nomi[0]))
    zpath.unlink()
    return out


def mesi_incrementali(oggi, giorni):
    """File mensili ANAC (AAAAMM01) che possono contenere CIG pubblicati
    nella finestra: dal mese di inizio finestra fino al mese corrente."""
    inizio = oggi - dt.timedelta(days=giorni)
    m = dt.date(inizio.year, inizio.month, 1)
    out = []
    while m <= oggi:
        out.append(m.strftime("%Y%m01"))
        m = dt.date(m.year + (m.month == 12), m.month % 12 + 1, 1)
    return out


def scarica_lombardia(inizio):
    rows, offset = [], 0
    where = (f"data_pubblicazione >= '{inizio}' OR "
             f"data_presentazioni_offerte >= '{inizio}'")
    while True:
        q = urllib.parse.urlencode({"$where": where, "$limit": 50000,
                                    "$offset": offset, "$order": ":id"})
        page = json.loads(fetch(f"{LOMBARDIA}?{q}"))
        rows += page
        if len(page) < 50000:
            break
        offset += 50000
    (RAW / "lombardia_k6cb-4hbm.json").write_text(
        json.dumps(rows, ensure_ascii=False))


def scarica_ted(inizio):
    campi = ["publication-number", "publication-date", "notice-type",
             "buyer-name", "buyer-city", "classification-cpv",
             "deadline-receipt-tender-date-lot", "estimated-value-lot",
             "estimated-value-proc", "procedure-type", "place-of-performance"]
    query = (f"buyer-country=ITA AND publication-date>={inizio:%Y%m%d} AND "
             "notice-type IN (cn-standard cn-social cn-desg)")
    notices, token = [], None
    while True:
        body = {"query": query, "fields": campi, "limit": 250,
                "paginationMode": "ITERATION"}
        if token:
            body["iterationNextToken"] = token
        d = json.loads(fetch(TED, data=json.dumps(body).encode(),
                             headers={"Content-Type": "application/json"}))
        notices += d["notices"]
        token = d.get("iterationNextToken")
        if not token or not d["notices"]:
            break
    for n in notices:
        n.pop("links", None)
    (RAW / "ted_cn_italia.json").write_text(
        json.dumps(notices, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oggi", default=dt.date.today().isoformat())
    ap.add_argument("--giorni", type=int, default=60)
    a = ap.parse_args()
    oggi = dt.date.fromisoformat(a.oggi)
    inizio = oggi - dt.timedelta(days=a.giorni)
    (RAW / "anac").mkdir(parents=True, exist_ok=True)

    passi = [("istat", lambda: (RAW / "istat_comuni.csv").write_bytes(
                 fetch(ISTAT))),
             ("anac stazioni", lambda: scarica_zip_anac(
                 "stazioni-appaltanti", "stazioni-appaltanti_csv"))]
    for m in mesi_incrementali(oggi, a.giorni):
        passi.append((f"anac cig {m}", lambda m=m: scarica_zip_anac(
            "cig", f"{m}-cig_csv")))
        passi.append((f"anac pubblicazioni {m}", lambda m=m: scarica_zip_anac(
            "pubblicazioni", f"{m}-pubblicazioni_csv")))
    passi += [("lombardia", lambda: scarica_lombardia(inizio)),
              ("ted", lambda: scarica_ted(inizio))]
    for nome, f in passi:
        try:
            f()
            print("ok   ", nome)
        except Exception as e:
            print("ERRORE", nome, e)
    (RAW / "fonti_log.json").write_text(json.dumps(
        {"eseguito": dt.datetime.now().isoformat(timespec="seconds"),
         "oggi": a.oggi, "giorni": a.giorni, "richieste": log}, indent=1))


if __name__ == "__main__":
    main()
