"""Mostra, per ogni comune J-City letto, le righe candidate a essere avvisi
aperti per le imprese (filtro per parole chiave, poi lettura manuale).
Uso: python3 jcity_analisi.py "Comune" [--tutte]"""
import argparse
import csv
import json
import re
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import lib  # noqa: E402

DA, OGGI = "2026-07-15", "2026-10-06"  # finestra larga: conta ciò che è aperto oggi
CHIUSE = re.compile(r"DELIBER|ORDINANZ|MATRIMONI|VARIAZIONE ANAGRAF|"
                    r"DEPOSITO ATTI|CONCORSO|MOBILIT|NOTIFICA|"
                    r"CONVOCAZIONE|ELEZION|CONSIGLIO COMUNALE", re.I)
RILEVANTI = re.compile(
    r"manifestazion\w* di interesse|indagin\w* (di|esplorativ)|avviso "
    r"(pubblico )?(esplorativo|di (gara|procedura|indizione|asta))|"
    r"procedura (aperta|negoziata|ristretta)|bando di gara|"
    r"gara (d.appalto|a procedura|pubblica)|disciplinare|lettera di invito|"
    r"richiesta di (offert|preventiv)|\bRDO\b|elenco (degli |dei |di )?"
    r"(operatori|fornitori|professionisti|imprese)|albo (dei |degli |di )?"
    r"(fornitori|operatori|professionisti|imprese)|istruttoria pubblica|"
    r"co-?progettazione|concessione (in uso|del servizio|di gestione|di "
    r"servizi|di spazi|di aree)|affidamento in concessione|asta pubblica|"
    r"alienazion|locazione|affitto|sponsoriz|bando|gara", re.I)
ESCLUDI = re.compile(
    r"selezione pubblica|concorso|mobilit|graduatoria|personale|alloggi|"
    r"\bSAP\b|contribut|borse? di studio|cambio del (nome|cognome)|"
    r"scrutator|presidente di seggio|rapporti comunicati|patrocinio|"
    r"esproprio|immissione nel possesso|asilo nido|iscrizion\w+ ai servizi|"
    r"deposito atti|deposito ai sensi|ritrovamento|onorificenze|"
    r"commissioni e sottocommissioni|cancellazione elettorale",
    re.I)
AWARD = re.compile(r"affidamento diretto|affidamento (del servizio|dei "
                   r"lavori|della fornitura|incarico)|liquidazione|impegno "
                   r"di spesa|approvazione (verbale|graduatoria)|"
                   r"aggiudicazione|esito|proroga|incarico", re.I)
APERTA = re.compile(r"procedura (aperta|negoziata|ristretta)|manifestazion|"
                    r"indagin|avviso|bando|concession|gara\b|asta", re.I)


def data_it(s):
    m = re.match(r"(\d\d)/(\d\d)/(\d{4})", s or "")
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("comune")
    ap.add_argument("--tutte", action="store_true")
    ap.add_argument("--award", action="store_true")
    ap.add_argument("--avvisi", action="store_true")
    a = ap.parse_args()
    siti = {r["comune"]: r for r in csv.DictReader(open(
        lib.ROOT / "data" / "comuni_siti.csv", encoding="utf-8"))}
    cod = siti[a.comune]["codice_istat"]
    o = json.load(open(lib.CACHE / f"jcity_{cod}.json"))
    print(f"## {a.comune}  root={o.get('root')}")
    for l in o["liste"]:
        albo = l["risorsa"].lower().startswith("albo")
        righe = l["righe"]
        skipped = [0]
        print(f"\n### {l['risorsa'][-75:]} | dichiarati {l['n_dichiarati']} "
              f"righe {len(righe)} {l.get('nota') or ''}")
        for r in righe:
            ini = data_it(r.get("Data inizio pubblicazione"))
            fine = data_it(r.get("Data fine pubblicazione"))
            ogg = (r.get("Oggetto") or "").replace("\n", " ")
            cat = (r.get("Titolo categoria") or "")[:28]
            sub = (r.get("Titolo sottocategoria") or "")[:28]
            if not a.tutte:
                if not ini or ini < DA:
                    continue
                if albo and fine and fine < OGGI:
                    continue
                if CHIUSE.search(cat + " " + sub) and not re.search(
                        r"gara|bando|manifestazion", ogg, re.I):
                    continue
                if ESCLUDI.search(ogg):
                    continue
                avv = re.search(r"avviso pubblico", ogg, re.I) and re.search(
                    r"operatori|ditte|imprese|affidamento|servizi[oi]|"
                    r"fornitur|lavori|gestione|noleggio|appalto", ogg, re.I)
                if not RILEVANTI.search(ogg) and not avv and not (
                        a.avvisi and re.search(r"AVVIS|BAND|GAR", cat + sub)):
                    continue
            tag = "AWARD?" if (AWARD.search(ogg) and not APERTA.search(ogg)
                               ) else "      "
            if tag == "AWARD?" and not (a.award or a.tutte):
                skipped[0] += 1
                continue
            print(f" {tag} {ini}→{fine} [{cat}|{sub}] {ogg[:150]}"
                  f" | {r.get('Url atto','')[-45:]}")
        if skipped[0]:
            print(f"   (+{skipped[0]} righe di affidamento/esito omesse)")


if __name__ == "__main__":
    main()
