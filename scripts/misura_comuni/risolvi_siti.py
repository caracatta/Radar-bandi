"""Trova il sito ufficiale di ogni comune del campione provando i pattern
di dominio più comuni (comune.<nome>[.<sigla>].it) e verificando che la
home contenga il nome del comune. Scrive data/comuni_siti.csv."""
import csv
import re
import sys
import unicodedata

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import lib  # noqa: E402


def slug(n, sep=""):
    n = unicodedata.normalize("NFKD", n).encode("ascii", "ignore").decode()
    n = n.lower().replace("'", "")
    return re.sub(r"[^a-z0-9]+", sep, n).strip(sep)


def candidati(nome, sigla):
    s, h = slug(nome), slug(nome, "-")
    out = []
    for nm in dict.fromkeys([s, h]):
        for dom in (f"comune.{nm}.{sigla}.it", f"comune.{nm}.it",
                    f"www.comune.{nm}.{sigla}.it", f"www.comune.{nm}.it"):
            out.append(dom)
    return out


def main():
    righe = list(csv.DictReader(open(lib.ROOT / "data" / "campione_comuni.csv",
                                     encoding="utf-8")))
    out = []
    for r in righe:
        trovato = None
        bloccato = None
        prove = []
        for dom in candidati(r["comune"], r["sigla"].lower()):
            url = f"https://{dom}/"
            m = lib.scarica(url, r["codice_istat"])
            prove.append((dom, "robots" if m.get("bloccato_da_robots")
                          else (m.get("stato") or m.get("errore"))))
            if m.get("bloccato_da_robots"):
                # il dominio esiste (robots.txt risponde) ma vieta tutto
                bloccato = f"https://{dom}/"
                break
            if m.get("stato") == 200 and m.get("tipo", "").startswith("text/"):
                t = (lib.testo(m) or "").lower()
                nome = r["comune"].lower().replace("'", "")
                if "comune" in t and nome.split()[0] in t.replace("&#039;",
                                                                  "'"):
                    trovato = m
                    break
        out.append({"codice_istat": r["codice_istat"], "comune": r["comune"],
                    "fascia": r["fascia"][0],
                    "home": trovato["finale"] if trovato else (bloccato or ""),
                    "stato_sito": ("leggibile" if trovato else
                                   "robots.txt vieta l'accesso"
                                   if bloccato else "non raggiungibile"),
                    "prove": "; ".join(f"{d}={s}" for d, s in prove)})
        print(r["comune"], "->", out[-1]["stato_sito"], out[-1]["home"],
              flush=True)
    with open(lib.ROOT / "data" / "comuni_siti.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)


if __name__ == "__main__":
    main()
