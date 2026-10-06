"""Lettura delle liste "J-City Gov / Albo online" (Maggioli, host
*.trasparenza-valutazione-merito.it) tramite il link "Esporta in OpenFormat"
(CSV) che la pagina stessa offre a chiunque, senza login.

Per un comune: albo pretorio + sezioni di "Bandi di gara e contratti" utili
a trovare avvisi aperti. Uso: python3 jcity.py "Nome comune"
"""
import csv
import io
import json
import re
import sys
import urllib.parse
import hashlib
import os

from bs4 import BeautifulSoup

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import lib  # noqa: E402

SEL = re.compile(r"Contratti con bandi e avvisi pubblicati dopo il 1 gennaio "
                 r"2024 - Pubblicazione$|Avvisi e bandi - SETTORI ORDINARI-"
                 r"SOTTOSOGLIA|Avvisi e bandi - SETTORI ORDINARI-SOPRASOGLIA|"
                 r"Avvisi di preinformazione$|Elenchi ufficiali|"
                 r"Avvisi pubblici|Avvisi$|Bandi di gara$", re.I)


def fresco(url, sub):
    """Scarica ignorando la cache (serve la sessione per l'export)."""
    k = hashlib.sha1(url.encode()).hexdigest()[:16]
    for ext in ("json", "html", "pdf"):
        p = lib.CACHE / sub / f"{k}.{ext}"
        if p.exists():
            p.unlink()
    return lib.scarica(url, sub)


def menu(root_url, sub):
    m = lib.scarica(root_url, sub)
    if not m.get("file"):
        return m, []
    s = BeautifulSoup(lib.testo(m), "lxml")
    voci, visti = [], set()
    for a in s.find_all("a", attrs={"data-mainurl": True}):
        res, u = a.get("data-resource") or "", a["data-mainurl"]
        if u and (res, u) not in visti:
            visti.add((res, u))
            voci.append((res, urllib.parse.urljoin(m["finale"], u)))
    return m, voci


def esporta(grid_url, sub):
    g = fresco(grid_url, sub)
    if g.get("stato") != 200:
        return None, g
    s = BeautifulSoup(lib.testo(g), "lxml")
    n = None
    t = " ".join(s.get_text(" ").split())
    mm = re.search(r"Sono stati trovati (\d+) risultat", t)
    if mm:
        n = int(mm.group(1))
    link = [urllib.parse.urljoin(g["finale"], a["href"])
            for a in s.find_all("a", href=True)
            if "OpenFormat" in a.get_text()]
    if not link:
        return {"n_dichiarati": n, "righe": [], "nota": "nessun export"}, g
    e = fresco(link[0], sub)
    if e.get("stato") != 200 or not e.get("file"):
        return {"n_dichiarati": n, "righe": [], "nota": "export non riuscito"}, g
    txt = (lib.ROOT / e["file"]).read_bytes().decode("utf-8", "replace")
    righe = list(csv.DictReader(io.StringIO(txt.lstrip("﻿"))))
    return {"n_dichiarati": n, "righe": righe, "nota": ""}, g


def leggi_comune(nome, root_trasp=None):
    siti = list(csv.DictReader(open(lib.ROOT / "data" / "comuni_siti.csv",
                                    encoding="utf-8")))
    r = [x for x in siti if x["comune"] == nome][0]
    sub = r["codice_istat"]
    d = json.load(open(lib.CACHE / "riassunti" / f"{sub}.json"))
    if root_trasp is None:
        for p in d["pagine"]:
            if (p["stato"] == 200 and "trasparenza-valutazione-merito" in
                    p["url"] and p["url"].rstrip("/").endswith("/trasparenza")):
                root_trasp = p["url"]
                break
    hosts = []
    for u in [c["url"] for c in d["candidati"]] + [p["url"] for p in
                                                      d["pagine"]]:
        h = urllib.parse.urlsplit(u).netloc
        if ("trasparenza-valutazione-merito" in h or h.startswith("albo.")) \
                and h not in hosts:
            hosts.append(h)
    if root_trasp is None and hosts:
        root_trasp = f"https://{hosts[0]}/web/trasparenza/trasparenza"
    out = {"comune": nome, "root": root_trasp, "liste": []}
    host = urllib.parse.urlsplit(root_trasp).netloc
    m, voci = menu(root_trasp, sub)
    out["menu_voci"] = len(voci)
    # albo: la voce di menu si trova nella pagina dell'albo
    voci_albo = []
    cand_albo = [f"https://{host}/web/trasparenza/albo-pretorio"] + [
        c["url"] for c in d["candidati"] if c["cat"] == "albo"
        and host in c["url"]]
    for ua in dict.fromkeys(cand_albo):
        _, va = menu(ua, sub)
        voci_albo += va
        if any(re.match(r"Albo", rs, re.I) and "papca-ap" in u
               for rs, u in va):
            break
    albo = [(rs, u) for rs, u in voci_albo + voci
            if re.match(r"Albo", rs, re.I) and "papca-ap" in u][:1]
    prior = [r"Contratti con bandi e avvisi pubblicati dopo il 1 gennaio "
             r"2024 - Pubblicazione$",
             r"Avvisi e bandi - SETTORI ORDINARI-SOTTOSOGLIA",
             r"Avvisi e bandi - SETTORI ORDINARI-SOPRASOGLIA",
             r"Avvisi di preinformazione$", r"Elenchi ufficiali"]
    gare = []
    for rx in prior:
        for rs, u in voci:
            if (rs.startswith("Bandi di gara e contratti") and re.search(
                    rx, rs, re.I) and "/papca-g/" in u
                    and (rs, u) not in gare):
                gare.append((rs, u))
    gare = gare[:3]
    if not albo:  # albo senza voce di menu: uso la pagina dell'albo stessa
        for ua in dict.fromkeys(cand_albo):
            ris, g = esporta(ua, sub)
            if ris and ris["righe"]:
                albo = [("Albo pretorio (pagina principale)", ua)]
                break
    for rs, u in albo + gare:
        ris, g = esporta(u, sub)
        out["liste"].append({"risorsa": rs, "url": u,
                             "stato": g.get("stato"),
                             "n_dichiarati": (ris or {}).get("n_dichiarati"),
                             "nota": (ris or {}).get("nota"),
                             "righe": (ris or {}).get("righe", [])})
    return out


if __name__ == "__main__":
    o = leggi_comune(sys.argv[1])
    print(o["comune"], o["root"], "voci menu:", o["menu_voci"])
    for l in o["liste"]:
        print(" -", l["risorsa"][:110], "| stato", l["stato"], "| dichiarati",
              l["n_dichiarati"], "| righe", len(l["righe"]), l["nota"])
        for r in l["righe"][:3]:
            print("     ", {k: (v or "")[:60] for k, v in r.items()
                            if k in ("Oggetto", "Titolo categoria",
                                     "Data inizio pubblicazione",
                                     "Data fine pubblicazione")})
