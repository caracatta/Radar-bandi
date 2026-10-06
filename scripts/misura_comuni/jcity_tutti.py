"""Esegue jcity.leggi_comune per i comuni del campione con albo J-City e
salva le righe in data/raw/comuni/jcity_<codice>.json (non versionato)."""
import csv
import json
import sys
import traceback

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import lib  # noqa: E402
import jcity  # noqa: E402

JC = ["Caronno Pertusella", "Gerenzano", "Olgiate Comasco", "Cormano",
      "Magenta", "Pieve Emanuele", "Brembate di Sopra", "Leno", "Mazzano",
      "Sarezzo", "Sirmione", "Bernareggio", "Seveso", "Vimercate",
      "Cornate d'Adda", "Giussano", "Cabiate", "Lurago d'Erba",
      "San Colombano al Lambro", "Pandino", "Ispra"]


def main():
    siti = {r["comune"]: r for r in csv.DictReader(open(
        lib.ROOT / "data" / "comuni_siti.csv", encoding="utf-8"))}
    for n in (sys.argv[1:] or JC):
        cod = siti[n]["codice_istat"]
        dest = lib.CACHE / f"jcity_{cod}.json"
        if dest.exists():
            continue
        try:
            o = jcity.leggi_comune(n)
        except Exception:
            traceback.print_exc()
            o = {"comune": n, "errore": traceback.format_exc()[-300:],
                 "liste": []}
        dest.write_text(json.dumps(o, ensure_ascii=False))
        print(n, [(l["risorsa"][-40:], l["n_dichiarati"], len(l["righe"]))
                  for l in o["liste"]], flush=True)


if __name__ == "__main__":
    main()
