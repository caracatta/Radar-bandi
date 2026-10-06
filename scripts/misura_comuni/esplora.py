"""Esplorazione di misura dei siti dei comuni del campione (NON è lo scraper
definitivo): scarica la home e le pagine verso albo pretorio, amministrazione
trasparente, bandi/avvisi/gare e riconosce il gestionale. Salva per ogni
comune un riassunto leggibile in data/raw/comuni/riassunti/<comune>.md, che
poi viene letto a mano per contare gli avvisi aperti.

Uso: python3 scripts/misura_comuni/esplora.py [--solo "Nome comune"] [--budget 14]
"""
import argparse
import csv
import json
import re
import sys
import urllib.parse

from bs4 import BeautifulSoup

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import lib  # noqa: E402

OGGI = "2026-10-06"
DA = "2026-09-06"  # ultimi 30 giorni
MESI = {m: i + 1 for i, m in enumerate(
    "gennaio febbraio marzo aprile maggio giugno luglio agosto settembre "
    "ottobre novembre dicembre".split())}
DATA_RE = re.compile(
    r"(\b\d{1,2})[/.\-](\d{1,2})[/.\-](20\d\d)\b|"
    r"\b(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|"
    r"agosto|settembre|ottobre|novembre|dicembre)\s+(20\d\d)\b|"
    r"\b(20\d\d)-(\d\d)-(\d\d)\b", re.I)

# (categoria, regex su testo del link o sul percorso, priorità: più basso prima)
LINK = [
    ("bandi_contratti", r"bandi di gara e contratti|bandi e contratti|"
                        r"gare e contratti|gare e appalti|bandi di gara|"
                        r"procedure di gara|bandi,? gare|bandi e gare", 1),
    ("avvisi_bandi", r"^\s*(avvisi|bandi|gare|appalti|contratti|"
                     r"avvisi e bandi|bandi e avvisi|bandi di concorso)\s*$|"
                     r"avvisi pubblici|manifestazion\w+ di interesse|"
                     r"indagin\w+ di mercato|elenco (degli )?operatori|"
                     r"elenco fornitori|albo fornitori|gare in corso|"
                     r"bandi in corso|avvisi in corso", 2),
    ("albo", r"albo pretorio|albo online|albo on-?line|albo informatico|"
             r"albo digitale", 3),
    ("trasparenza", r"amministrazione trasparente|trasparenza", 4),
    ("piattaforma", r"piattaforma|e-?procurement|gare telematiche|"
                    r"portale (gare|appalti)|tuttogare|appalti ?&? ?contratti|"
                    r"acquisti", 3),
]
HOST_PIATTAFORME = re.compile(
    r"tuttogare|traspare|appaltiamo|sintel|ariaspa|acquistinretepa|"
    r"asmecomm|garetelematiche|appalti\.|gare\.|pleiade|stazioneunica|"
    r"cuc\.|centraleunica|albofornitori|ngt|stella\.regione|"
    r"mercato-elettronico|net4market|digitalpa|ecosistema|startpa", re.I)

FIRME = [
    ("WordPress", r"wp-content|wp-includes|wordpress"),
    ("Drupal", r"drupal|sites/default/files|/sites/all/"),
    ("Joomla", r"joomla|/media/jui/|com_content"),
    ("Plone", r"plone|@@"),
    ("Liferay", r"liferay"),
    ("Design Comuni Italia (AgID)", r"design-comuni|bootstrap-italia|"
                                    r"comuni-italia|italia\.it"),
    ("OpenCity / Opencontent", r"opencity|opencontent|openpa|comunweb|"
                               r"/it/openpa"),
    ("Halley", r"halley"),
    ("Maggioli", r"maggioli|sicraweb|jserviziweb|municipium"),
    ("Dedagroup / Civilia", r"civilia|dedagroup|ditech"),
    ("Urbi / PA Digitale", r"urbi\b|cloud\.urbi|padigitale|paDigitale"),
    ("Hypersic / Entranext", r"hypersic|entranext|nextportal"),
    ("Sito Ufficio Stampa / Municipium", r"municipium"),
    ("Studio K", r"studiok"),
    ("Gruppo Soluzione1", r"soluzione1|soluzione-1"),
    ("Tecnologie e Servizi ?(TSD)", r"tsdweb|tsdsrl"),
    ("J-Albo / Jcity (Gruppo Maggioli?)", r"j-albo|jalbo|jcity"),
    ("Servizi online Halley/ApSystems", r"apsystems|ap-systems"),
    ("Digital Hub / Wedo", r"wedo|digital-hub"),
]


def pulisci(s):
    return re.sub(r"\s+", " ", s or "").strip()


def firma(html, soup):
    f = []
    gen = soup.find("meta", attrs={"name": re.compile("generator", re.I)})
    if gen and gen.get("content"):
        f.append("generator=" + gen["content"])
    low = html.lower()
    for nome, rx in FIRME:
        if re.search(rx, low):
            f.append(nome)
    # crediti nel footer
    foot = soup.find("footer")
    if foot:
        for a in foot.find_all("a", href=True):
            t = pulisci(a.get_text())
            if re.search(r"realizzat|sviluppat|powered|credit|design|"
                         r"maggioli|halley|gruppo|software", t + a["href"],
                         re.I):
                f.append(f"footer:{t[:40]}→{urllib.parse.urlsplit(a['href']).netloc}")
    return list(dict.fromkeys(f))


def link_candidati(base, soup):
    out = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        url = urllib.parse.urljoin(base, href).split("#")[0]
        testo = pulisci(a.get_text()) or pulisci(a.get("title", ""))
        host = urllib.parse.urlsplit(url).netloc
        for cat, rx, pr in LINK:
            if re.search(rx, testo, re.I) or re.search(
                    rx.replace("^\\s*", "").replace("\\s*$", ""),
                    urllib.parse.urlsplit(url).path.replace("-", " ")
                    .replace("_", " "), re.I) and cat != "avvisi_bandi":
                out.append({"cat": cat, "pr": pr, "testo": testo[:80],
                            "url": url})
                break
        else:
            if HOST_PIATTAFORME.search(host):
                out.append({"cat": "piattaforma", "pr": 3,
                            "testo": testo[:80], "url": url})
    visti, uniq = set(), []
    for c in sorted(out, key=lambda c: c["pr"]):
        if c["url"] not in visti:
            visti.add(c["url"])
            uniq.append(c)
    return uniq


def date_in(txt):
    out = []
    for m in DATA_RE.finditer(txt):
        g = m.groups()
        try:
            if g[0]:
                d = f"{g[2]}-{int(g[1]):02d}-{int(g[0]):02d}"
            elif g[3]:
                d = f"{g[5]}-{MESI[g[4].lower()]:02d}-{int(g[3]):02d}"
            else:
                d = f"{g[6]}-{g[7]}-{g[8]}"
        except (KeyError, ValueError):
            continue
        out.append(d)
    return out


def righe_pagina(soup):
    """Elementi di lista/tabella con almeno una data recente (>= 2026-08-01),
    ridotti a testo e al primo link."""
    righe, visti = [], set()
    for el in soup.find_all(["tr", "li", "article", "div"]):
        if el.name == "div" and not re.search(
                r"card|item|row|list|result|news|avviso|bando|riga",
                " ".join(el.get("class", [])), re.I):
            continue
        t = pulisci(el.get_text(" "))
        if not (25 < len(t) < 700):
            continue
        ds = date_in(t)
        if not ds or max(ds) < "2026-08-01":
            continue
        # evita contenitori che includono altre righe già prese
        if any(t in v or v in t for v in visti):
            continue
        visti.add(t)
        a = el.find("a", href=True)
        righe.append({"testo": t, "date": sorted(set(ds)),
                      "href": a["href"] if a else None})
    return righe


def pagina(meta):
    t = lib.testo(meta)
    return BeautifulSoup(t, "lxml") if t else None


def esplora(r, budget):
    cod = r["codice_istat"]
    home = r["home"]
    ris = {"comune": r["comune"], "fascia": r["fascia"], "home": home,
           "robots": None, "firme": [], "pagine": [], "candidati": []}
    rp, info = lib.robots(home)
    ris["robots"] = {"stato": info["stato"], "crawl_delay": info["crawl_delay"]}
    m = lib.scarica(home, cod)
    if m.get("bloccato_da_robots") or not m.get("file"):
        ris["errore"] = ("robots.txt vieta l'accesso"
                         if m.get("bloccato_da_robots")
                         else m.get("errore") or m.get("stato"))
        return ris
    soup = pagina(m)
    ris["firme"] = firma(lib.testo(m), soup)
    host = urllib.parse.urlsplit(m["finale"]).netloc
    cand = link_candidati(m["finale"], soup)
    ris["candidati"] = cand
    coda = [c for c in cand][:]
    visitati = {m["finale"]}
    speso = 0
    while coda and speso < budget:
        c = coda.pop(0)
        if c["url"] in visitati:
            continue
        visitati.add(c["url"])
        h = urllib.parse.urlsplit(c["url"]).netloc
        speso += 1
        mm = lib.scarica(c["url"], cod)
        pg = {"cat": c["cat"], "testo_link": c["testo"], "url": c["url"],
              "stato": mm.get("stato"), "tipo": mm.get("tipo"),
              "byte": mm.get("byte"), "errore": mm.get("errore"),
              "robots": mm.get("bloccato_da_robots"), "righe": [],
              "esterno": h != host}
        if mm.get("file") and (mm.get("tipo") or "").startswith("text/html"):
            s2 = pagina(mm)
            pg["titolo"] = pulisci(s2.title.get_text()) if s2.title else ""
            pg["righe"] = righe_pagina(s2)
            pg["firme"] = firma(lib.testo(mm), s2)
            # un secondo livello solo da pagine di trasparenza/bandi
            if c["cat"] in ("trasparenza", "bandi_contratti",
                            "avvisi_bandi") and len(visitati) < budget + 3:
                for c2 in link_candidati(mm["finale"], s2):
                    if c2["cat"] in ("bandi_contratti", "avvisi_bandi",
                                     "albo") and c2["url"] not in visitati:
                        coda.append(c2)
                coda.sort(key=lambda c: c["pr"])
        ris["pagine"].append(pg)
    return ris


def scrivi(ris, dest):
    L = [f"# {ris['comune']} (fascia {ris['fascia']})", "",
         f"Home: {ris['home']}  | robots: {ris['robots']}",
         f"Firme gestionale/CMS: {', '.join(ris['firme']) or '-'}", ""]
    if ris.get("errore"):
        L.append(f"**ERRORE: {ris['errore']}**")
    L += ["## Link candidati dalla home", ""]
    for c in ris["candidati"][:30]:
        L.append(f"- [{c['cat']}] {c['testo']} → {c['url']}")
    L += ["", "## Pagine visitate", ""]
    for p in ris["pagine"]:
        L.append(f"### [{p['cat']}] {p['url']}")
        L.append(f"stato={p['stato']} tipo={p['tipo']} byte={p['byte']} "
                 f"err={p['errore']} robots_vieta={p['robots']} "
                 f"titolo={p.get('titolo', '')!r} firme={p.get('firme')}")
        for r in p["righe"][:25]:
            L.append(f"  - {r['date']} | {r['testo'][:300]} | {r['href']}")
        L.append("")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(L), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo")
    ap.add_argument("--budget", type=int, default=14)
    a = ap.parse_args()
    siti = list(csv.DictReader(open(lib.ROOT / "data" / "comuni_siti.csv",
                                    encoding="utf-8")))
    for r in siti:
        if a.solo and r["comune"] != a.solo:
            continue
        if not r["home"] or r["stato_sito"] != "leggibile":
            continue
        ris = esplora(r, a.budget)
        scrivi(ris, lib.CACHE / "riassunti" /
               f"{r['codice_istat']}_{r['comune'].replace(' ', '_')}.md")
        (lib.CACHE / "riassunti" /
         f"{r['codice_istat']}.json").write_text(json.dumps(ris))
        print(r["comune"], len(ris["pagine"]), "pagine", ris["firme"][:3],
              flush=True)


if __name__ == "__main__":
    main()
