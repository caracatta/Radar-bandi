"""Legge una pagina (HTML o PDF) con le stesse regole di cortesia della
misura e ne stampa il testo e i link. Strumento di consultazione manuale.

Uso: python3 scripts/misura_comuni/leggi.py CODICE_ISTAT URL [--links] [--max N]
     python3 scripts/misura_comuni/leggi.py CODICE_ISTAT URL --grep REGEX
"""
import argparse
import re
import subprocess
import sys
import urllib.parse

from bs4 import BeautifulSoup

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import lib  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("codice")
    ap.add_argument("url")
    ap.add_argument("--links", action="store_true")
    ap.add_argument("--max", type=int, default=3500)
    ap.add_argument("--grep")
    a = ap.parse_args()
    if not a.codice.isdigit():  # nome del comune invece del codice ISTAT
        import csv
        for r in csv.DictReader(open(lib.ROOT / "data" / "comuni_siti.csv",
                                     encoding="utf-8")):
            if r["comune"] == a.codice:
                a.codice = r["codice_istat"]
    m = lib.scarica(a.url, a.codice)
    print(f"# {a.url}\n# stato={m.get('stato')} tipo={m.get('tipo')} "
          f"byte={m.get('byte')} err={m.get('errore')} "
          f"robots_vieta={m.get('bloccato_da_robots')} finale={m.get('finale')}")
    if not m.get("file"):
        return
    path = lib.ROOT / m["file"]
    if m["tipo"] == "application/pdf":
        out = subprocess.run(["pdftotext", "-layout", str(path), "-"],
                             capture_output=True, text=True).stdout
        txt = " ".join(out.split())
        print(f"# PDF testuale: {'sì' if len(txt) > 200 else 'NO (probabile scansione)'}"
              f" ({len(txt)} caratteri)")
        print(txt[:a.max])
        return
    s = BeautifulSoup(lib.testo(m), "lxml")
    if a.links:
        for l in s.find_all("a", href=True):
            t = " ".join(l.get_text().split())[:90]
            if t:
                print(f"- {t} → {urllib.parse.urljoin(m['finale'], l['href'])}")
        return
    for t in s(["script", "style", "noscript"]):
        t.decompose()
    txt = " ".join(s.get_text(" ").split())
    if a.grep:
        for mm in re.finditer(a.grep, txt, re.I):
            print("…", txt[max(0, mm.start() - 150):mm.end() + 250], "…")
        return
    print(txt[:a.max])


if __name__ == "__main__":
    main()
