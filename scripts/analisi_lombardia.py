"""Conteggio dei bandi lombardi aperti per provincia e macro-categoria CPV.

Uso: python3 scripts/analisi_lombardia.py [--oggi AAAA-MM-GG] [--giorni 60]

Legge i file scaricati da scripts/scarica_fonti.py in data/raw/ e scrive:
  data/comuni_province.csv          tabella comune -> provincia (ISTAT)
  output/bandi_lombardia_aperti.csv elenco delle gare conteggiate (ANAC)
  output/tabella_provincia.csv
  output/tabella_provincia_macro.csv
  output/report.md
"""
import argparse
import collections
import csv
import datetime as dt
import json
import pathlib
import re
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "output"
csv.field_size_limit(10**9)

# Procedure tenute: aperte, ristrette, negoziate (con bando o con invito).
PROCEDURE = {
    "PROCEDURA APERTA": "Aperta",
    "PROCEDURA RISTRETTA": "Ristretta",
    "PROCEDURA NEGOZIATA SENZA PREVIA PUBBLICAZIONE": "Negoziata (invito)",
    "PROCEDURA NEGOZIATA PREVIA PUBBLICAZIONE": "Negoziata (bando)",
    "PROCEDURA NEGOZIATA CON PREVIA INDIZIONE DI GARA (SETTORI SPECIALI)":
        "Negoziata (bando)",
}
SOGLIA = 40000.0


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore")
    s = re.sub(r"\(.*?\)", " ", s.decode().upper())
    return re.sub(r"[^A-Z0-9]+", " ", s).strip()


def num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


# --- Tabella comune -> provincia -------------------------------------------

def carica_istat():
    righe = list(csv.reader(
        open(RAW / "istat_comuni.csv", encoding="latin-1"), delimiter=";"))
    comuni = []
    for r in righe[1:]:
        if len(r) < 16 or not r[4]:
            continue
        comuni.append({"codice_istat": r[4], "comune": r[6],
                       "sigla": r[14], "provincia": r[11],
                       "regione": r[10]})
    with open(ROOT / "data" / "comuni_province.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(comuni[0]))
        w.writeheader()
        w.writerows(comuni)
    per_codice = {c["codice_istat"]: c for c in comuni}
    per_nome = collections.defaultdict(list)
    for c in comuni:
        per_nome[norm(c["comune"])].append(c)
    # Nomi in uso nei dati (inglese su TED, forme brevi).
    for alias, nome in [("MILAN", "MILANO"), ("MANTUA", "MANTOVA"),
                        ("MONZA", "MONZA")]:
        per_nome.setdefault(alias, per_nome[nome])
    sigle = {c["sigla"]: c["provincia"] for c in comuni}
    regioni = {c["sigla"]: c["regione"] for c in comuni}
    return per_codice, per_nome, sigle, regioni


class Geo:
    def __init__(self):
        self.per_codice, self.per_nome, self.sigle, self.regioni = \
            carica_istat()

    def da_nome(self, nome, sigla=None):
        cand = self.per_nome.get(norm(nome), [])
        if sigla:
            cand = [c for c in cand if c["sigla"] == sigla] or cand
        return cand[0] if len(cand) == 1 else None

    def risolvi(self, codice, nome, sigla):
        """Restituisce (provincia, regione, metodo)."""
        if codice in self.per_codice:
            c = self.per_codice[codice]
            return c["provincia"], c["regione"], "codice ISTAT"
        if nome:
            c = self.da_nome(nome, sigla)
            if c:
                return c["provincia"], c["regione"], "nome comune"
        if sigla in self.sigle:  # comune soppresso/rinominato
            return self.sigle[sigla], self.regioni[sigla], "sigla provincia"
        return None, None, "non risolto"


def carica_stazioni(geo):
    sa = {}
    for r in csv.DictReader(open(RAW / "anac" / "stazioni-appaltanti_csv.csv",
                                 encoding="utf-8", errors="replace"),
                            delimiter=";"):
        sigla = r["provincia_codice"].replace("IT-", "")
        prov, reg, metodo = geo.risolvi(r["citta_codice"], r["citta_nome"],
                                        sigla)
        sa[r["codice_fiscale"]] = {
            "denominazione": r["denominazione"], "comune": r["citta_nome"],
            "provincia": prov, "regione": reg, "metodo": metodo}
    return sa


# --- CPV -> macro-categoria -----------------------------------------------

def carica_cpv():
    regole = []
    for r in csv.DictReader(open(ROOT / "config" / "cpv_macro.csv",
                                 encoding="utf-8")):
        if r["prefisso_cpv"].isdigit():
            regole.append((r["prefisso_cpv"], r["macro_categoria"]))
    regole.sort(key=lambda x: -len(x[0]))

    def macro(cpv):
        cpv = re.sub(r"\D", "", cpv or "")
        if len(cpv) < 2:
            return "CPV mancante"
        for pref, cat in regole:
            if cpv.startswith(pref):
                return cat
        if int(cpv[:2]) <= 44:
            return "Forniture di beni"
        return "Trasporti e altri servizi"
    return macro


# --- ANAC -------------------------------------------------------------------

def file_mensili(prefisso):
    return sorted((RAW / "anac").glob(f"*-{prefisso}_csv.csv"))


def carica_cig(inizio, oggi):
    """Ultima versione di ogni CIG pubblicato nella finestra; i file mensili
    sono incrementali, quindi quelli più recenti sovrascrivono (anche quando
    la nuova versione cade fuori finestra)."""
    cig, file_di = {}, {}
    for f in file_mensili("cig"):
        for r in csv.DictReader(open(f, encoding="utf-8", errors="replace"),
                                delimiter=";"):
            k = r["cig"]
            if file_di.get(k) == f.name and r["flag_prevalente"] != "1":
                continue  # più righe CPV per CIG: tengo la prevalente
            file_di[k] = f.name
            cig[k] = r if inizio <= r["data_pubblicazione"] <= oggi else None
    return {k: r for k, r in cig.items() if r}


def carica_pubblicazioni():
    scad = {}
    for f in file_mensili("pubblicazioni"):
        for r in csv.DictReader(open(f, encoding="utf-8", errors="replace"),
                                delimiter=";"):
            if r["SCADENZA_INVITO"]:
                scad[r["cig"]] = r["SCADENZA_INVITO"][:10]
    return scad


def analisi_anac(inizio, oggi, geo, sa, macro):
    cig = carica_cig(inizio, oggi)
    scad_invito = carica_pubblicazioni()
    imbuto = collections.Counter()
    compl = collections.Counter()
    flusso = collections.defaultdict(set)  # gare competitive pubblicate
    proc_escluse = collections.Counter()
    gare = {}
    for r in cig.values():
        s = sa.get(r["cf_amministrazione_appaltante"])
        if not s or s["regione"] != "Lombardia":
            continue
        imbuto["1. CIG pubblicati nella finestra da SA lombarde"] += 1
        proc = PROCEDURE.get(r["tipo_scelta_contraente"])
        if not proc:
            proc_escluse[r["tipo_scelta_contraente"] or "(vuoto)"] += 1
            continue
        imbuto["2. ... di cui procedure aperte/ristrette/negoziate"] += 1
        flusso[s["provincia"]].add((r["cf_amministrazione_appaltante"],
                                    r["numero_gara"] or r["cig"]))
        for campo, ok in [
                ("scadenza offerta (data_scadenza_offerta)",
                 r["data_scadenza_offerta"]),
                ("scadenza offerta o invito (+ pubblicazioni.SCADENZA_INVITO)",
                 r["data_scadenza_offerta"] or scad_invito.get(r["cig"])),
                ("importo lotto > 0", num(r["importo_lotto"])),
                ("importo complessivo gara > 0",
                 num(r["importo_complessivo_gara"])),
                ("CPV (cod_cpv)", r["cod_cpv"]),
                ("comune della SA (anagrafica stazioni-appaltanti)",
                 s["comune"]),
                ("luogo di esecuzione (luogo_istat)", r["luogo_istat"]),
                ("provincia (campo del CIG)", r["provincia"])]:
            compl[campo] += bool(ok)
        if r["DATA_CANCELLAZIONE"] or r["ESITO"]:
            continue
        imbuto["3. ... non cancellati e senza esito (aggiudicazione, "
               "revoca, deserta)"] += 1
        scad = r["data_scadenza_offerta"][:10]
        fonte_scad = "ANAC cig" if scad else None
        if not scad and r["cig"] in scad_invito:
            scad, fonte_scad = scad_invito[r["cig"]], "ANAC pubblicazioni"
        if not scad:
            imbuto["   (scartati: scadenza non compilata)"] += 1
            continue
        if scad < oggi:
            continue
        imbuto["4. ... con scadenza offerte >= oggi (lotti conteggiati)"] += 1
        chiave = (r["cf_amministrazione_appaltante"],
                  r["numero_gara"] or r["cig"])
        g = gare.setdefault(chiave, {
            "numero_gara": r["numero_gara"], "cig": [],
            "stazione_appaltante": r["denominazione_amministrazione_appaltante"],
            "cf_sa": r["cf_amministrazione_appaltante"],
            "comune_sa": s["comune"], "provincia": s["provincia"],
            "metodo_provincia": s["metodo"],
            "procedura": proc, "oggetto": r["oggetto_gara"],
            "tipo_contratto": r["oggetto_principale_contratto"],
            "importo_gara": num(r["importo_complessivo_gara"]),
            "data_pubblicazione": r["data_pubblicazione"],
            "scadenza": scad, "fonte_scadenza": fonte_scad,
            "luogo_istat": r["luogo_istat"],
            "_lotto_max": -1.0, "cpv": "", "descrizione_cpv": ""})
        g["cig"].append(r["cig"])
        g["scadenza"] = max(g["scadenza"], scad)
        imp = num(r["importo_lotto"]) or 0.0
        if imp > g["_lotto_max"]:
            g["_lotto_max"] = imp
            g["cpv"], g["descrizione_cpv"] = r["cod_cpv"], r["descrizione_cpv"]
    for g in gare.values():
        g["macro_categoria"] = macro(g["cpv"])
        g["n_lotti_aperti"] = len(g["cig"])
        g["cig"] = " ".join(g["cig"])
        del g["_lotto_max"]
    imbuto["5. Gare (numero_gara) conteggiate"] = len(gare)
    compl["_base"] = imbuto["2. ... di cui procedure aperte/ristrette/"
                            "negoziate"]
    return list(gare.values()), imbuto, proc_escluse, compl, flusso


# --- Fonti di confronto ----------------------------------------------------

def analisi_ted(oggi, geo, gare):
    # Verifica di copertura: un bando TED aperto "trova" una gara ANAC
    # se coincidono provincia e una data di scadenza.
    anac = {(g["provincia"], g["scadenza"]) for g in gare}
    ultimo_anac = max((g["data_pubblicazione"] for g in gare), default="")
    trovati = collections.Counter()
    notices = json.loads((RAW / "ted_cn_italia.json").read_text())
    per_prov = collections.Counter()
    non_risolti = collections.Counter()
    tot = aperti = 0
    compl = collections.Counter()
    for n in notices:
        for campo, k in [("scadenza offerta", "deadline-receipt-tender-date-lot"),
                         ("città del committente", "buyer-city"),
                         ("CPV", "classification-cpv")]:
            compl[campo] += bool(n.get(k))
        compl["importo stimato (lotto o procedura)"] += bool(
            n.get("estimated-value-lot") or n.get("estimated-value-proc"))
        citta = next(iter((n.get("buyer-city") or {}).values()), [""])[0]
        c = geo.da_nome(citta)
        if not c:
            non_risolti[citta] += 1
            continue
        if c["regione"] != "Lombardia":
            continue
        tot += 1
        scad = [d[:10] for d in n.get("deadline-receipt-tender-date-lot", [])]
        if scad and max(scad) >= oggi:
            aperti += 1
            per_prov[c["provincia"]] += 1
            dopo = n["publication-date"][:10] > ultimo_anac
            ok = any((c["provincia"], d) in anac for d in scad)
            trovati[("pubblicati dopo l'ultimo dato ANAC" if dopo else
                     "pubblicati entro l'ultimo dato ANAC",
                     "trovati in ANAC" if ok else "non trovati")] += 1
    return {"avvisi_italia": len(notices), "lombardi": tot,
            "lombardi_aperti": aperti, "per_provincia": per_prov,
            "completezza": compl, "verifica": trovati,
            "citta_non_risolte": sum(non_risolti.values()),
            "esempi_non_risolte": non_risolti.most_common(8)}


def analisi_lombardia(oggi, sa):
    rows = json.loads((RAW / "lombardia_k6cb-4hbm.json").read_text())
    bandi = {}
    for r in rows:
        bandi.setdefault(r.get("codice_bando"), r)
    per_prov = collections.Counter()
    proc = collections.Counter()
    compl = collections.Counter()
    for r in bandi.values():
        for campo, k in [("scadenza offerta", "data_presentazioni_offerte"),
                         ("comune", "comune"), ("provincia", "provincia"),
                         ("importo", "importo_complessivo_base"),
                         ("CPV", "codice_cpv"),
                         ("data pubblicazione", "data_pubblicazione")]:
            compl[campo] += bool(r.get(k))
        if (r.get("procedura_gara") or "").lower().startswith("affidamento"):
            continue
        if (r.get("data_presentazioni_offerte") or "")[:10] < oggi:
            continue
        proc[r.get("procedura_gara")] += 1
        s = sa.get(r.get("codice_fiscale"), {})
        per_prov[s.get("provincia") or "(non risolta)"] += 1
    return {"righe": len(rows), "bandi": len(bandi),
            "aperti_non_diretti": sum(per_prov.values()),
            "per_provincia": per_prov, "procedure": proc,
            "completezza": compl}


# --- Output -----------------------------------------------------------------

MACRO = ["Edilizia, lavori e manutenzioni", "Impianti ed energia",
         "Verde e ambiente", "Pulizie, sanificazione e rifiuti", "Sanità e servizi alla persona",
         "Servizi tecnici, IT e professionali", "Trasporti e altri servizi",
         "Forniture di beni", "CPV mancante"]


def md_tabella(intest, righe):
    numerica = [all(isinstance(r[i], (int, float)) for r in righe)
                for i in range(len(intest))]
    out = ["| " + " | ".join(intest) + " |",
           "|" + "|".join("---:" if n else "---" for n in numerica) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in righe]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oggi", default=dt.date.today().isoformat())
    ap.add_argument("--giorni", type=int, default=60)
    a = ap.parse_args()
    oggi = a.oggi
    inizio = (dt.date.fromisoformat(oggi)
              - dt.timedelta(days=a.giorni)).isoformat()

    geo = Geo()
    sa = carica_stazioni(geo)
    macro = carica_cpv()
    gare, imbuto, proc_escluse, compl, flusso = analisi_anac(inizio, oggi, geo, sa, macro)
    gare.sort(key=lambda g: (g["provincia"] or "", g["scadenza"]))
    OUT.mkdir(exist_ok=True)

    campi = ["provincia", "comune_sa", "stazione_appaltante", "cf_sa",
             "numero_gara", "oggetto", "procedura", "tipo_contratto",
             "macro_categoria", "cpv", "descrizione_cpv", "importo_gara",
             "data_pubblicazione", "scadenza", "fonte_scadenza",
             "n_lotti_aperti", "cig", "luogo_istat", "metodo_provincia"]
    with open(OUT / "bandi_lombardia_aperti.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campi)
        w.writeheader()
        w.writerows(gare)

    prov = collections.defaultdict(list)
    for g in gare:
        prov[g["provincia"] or "(non risolta)"].append(g)
    ordine = sorted(prov, key=lambda p: -len(prov[p]))

    def stats(gs):
        con_imp = [g for g in gs if g["importo_gara"]]
        return [len(gs), sum(g["n_lotti_aperti"] for g in gs),
                len(con_imp), sum(1 for g in gs if g["scadenza"]),
                sum(1 for g in gs if g["comune_sa"]),
                sum(1 for g in con_imp if g["importo_gara"] < SOGLIA)]

    intest_p = ["Provincia", "Gare aperte", "Lotti (CIG) aperti",
                "Con importo", "Con scadenza", "Con comune SA",
                "Sotto 40.000 €"]
    intest_p.append("Gare pubblicate nei 60 gg (anche già scadute)")
    righe_p = [[p] + stats(prov[p]) + [len(flusso[p])] for p in ordine]
    righe_p.append(["**Totale Lombardia**"] + stats(gare)
                   + [sum(len(v) for v in flusso.values())])
    with open(OUT / "tabella_provincia.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(intest_p)
        w.writerows([[str(c).strip("*") for c in r] for r in righe_p])

    macro_usate = [m for m in MACRO if any(g["macro_categoria"] == m
                                           for g in gare)]
    intest_m = ["Provincia"] + macro_usate + ["Totale"]
    righe_m = []
    for p in ordine + [None]:
        gs = prov[p] if p else gare
        c = collections.Counter(g["macro_categoria"] for g in gs)
        righe_m.append([p or "**Totale**"] + [c[m] for m in macro_usate]
                       + [len(gs)])
    with open(OUT / "tabella_provincia_macro.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(intest_m)
        w.writerows([[str(c).strip("*") for c in r] for r in righe_m])

    proc_c = collections.Counter(g["procedura"] for g in gare)
    fonte_scad = collections.Counter(g["fonte_scadenza"] for g in gare)
    metodo = collections.Counter(g["metodo_provincia"] for g in gare)
    ted = analisi_ted(oggi, geo, gare)
    lomb = analisi_lombardia(oggi, sa)
    log = json.loads((RAW / "fonti_log.json").read_text())
    ultimo = max(g["data_pubblicazione"] for g in gare) if gare else "-"

    r = [f"# Bandi aperti in Lombardia per provincia e settore",
         "",
         f"Data di riferimento: **{oggi}**. Finestra di pubblicazione: "
         f"**{inizio} → {oggi}** ({a.giorni} giorni). Download fonti: "
         f"{log['eseguito']}. Ultima data di pubblicazione presente nei dati "
         f"ANAC: **{ultimo}**.",
         "",
         "Fonte principale: ANAC open data (dataset `cig` incrementali "
         "mensili + `pubblicazioni` + anagrafica `stazioni-appaltanti`). "
         "Unità di conteggio: **gara** (`numero_gara` per stazione "
         "appaltante); una gara a più lotti conta 1, i lotti sono riportati "
         "a parte. Metodo e limiti in fondo e in `docs/nota_fonti.md`.",
         "",
         "## 1. Gare aperte per provincia",
         "",
         "Provincia = provincia del comune della **stazione appaltante** "
         "(anagrafica ANAC → tabella comuni ISTAT), non del luogo di "
         "esecuzione. Le colonne \"Con …\" contano le gare con quel campo "
         "compilato; \"Sotto 40.000 €\" usa l'importo complessivo della gara.",
         "",
         md_tabella(intest_p, righe_p),
         "",
         "## 2. Gare aperte per provincia × macro-categoria CPV",
         "",
         "Macro-categoria assegnata dal CPV prevalente del lotto aperto di "
         "importo maggiore. Mappatura completa in `config/cpv_macro.csv` "
         "(riportata in fondo).",
         "",
         md_tabella(intest_m, righe_m),
         "",
         "## 3. Come si arriva al numero (ANAC)",
         "",
         md_tabella(["Passo", "Conteggio"], list(imbuto.items())),
         "",
         "Procedure escluse (CIG nella finestra, SA lombarde):",
         "",
         md_tabella(["Tipo scelta contraente", "CIG"],
                    proc_escluse.most_common()),
         "",
         "Procedure nelle gare conteggiate: " + ", ".join(
             f"{k} {v}" for k, v in proc_c.most_common()) + ".",
         "",
         "Origine della scadenza: " + ", ".join(
             f"{k} {v}" for k, v in fonte_scad.most_common()) + ".",
         "",
         "Come è stata ricavata la provincia: " + ", ".join(
             f"{k} {v}" for k, v in metodo.most_common()) + ".",
         "",
         "## 4. Completezza dei campi chiave",
         "",
         f"ANAC, sui {compl['_base']} CIG di procedure aperte/ristrette/"
         "negoziate pubblicati nella finestra da SA lombarde (prima del "
         "filtro sulla scadenza):",
         "",
         md_tabella(["Campo", "Compilato", "%"], [
             [k, v, f"{100 * v / compl['_base']:.1f}"]
             for k, v in compl.items() if k != "_base"]),
         "",
         f"TED, sui {ted['avvisi_italia']} bandi italiani nella finestra:",
         "",
         md_tabella(["Campo", "Compilato", "%"], [
             [k, v, f"{100 * v / ted['avvisi_italia']:.1f}"]
             for k, v in ted["completezza"].items()]),
         "",
         f"Regione Lombardia (k6cb-4hbm), sui {lomb['bandi']} bandi distinti "
         "scaricati:",
         "",
         md_tabella(["Campo", "Compilato", "%"], [
             [k, v, f"{100 * v / lomb['bandi']:.1f}"]
             for k, v in lomb["completezza"].items()]),
         "",
         "## 5. Confronto con le altre fonti",
         "",
         f"**TED (api.ted.europa.eu)** – solo gare sopra soglia UE. Bandi "
         f"(cn-standard/cn-social/cn-desg) di committenti italiani pubblicati "
         f"nella finestra: {ted['avvisi_italia']}; con città del committente "
         f"in Lombardia: {ted['lombardi']}; con scadenza >= oggi: "
         f"**{ted['lombardi_aperti']}**. Città non riconducibili a un comune "
         f"univoco: {ted['citta_non_risolte']} (es. "
         + ", ".join(f"{c or '(vuota)'} {n}"
                     for c, n in ted['esempi_non_risolte'][:5]) + ").",
         "",
         md_tabella(["Provincia", "Bandi TED aperti"],
                    ted["per_provincia"].most_common()),
         "",
         "Verifica di copertura ANAC: un bando TED aperto si considera "
         "presente in ANAC se esiste una gara ANAC conteggiata nella stessa "
         "provincia con la stessa data di scadenza (confronto approssimato, "
         "TED non riporta il CIG).",
         "",
         md_tabella(["Bandi TED aperti", "Esito", "N"],
                    [list(k) + [v] for k, v in sorted(
                        ted["verifica"].items())]),
         "",
         f"**Regione Lombardia – Osservatorio (dati.lombardia.it, "
         f"k6cb-4hbm)** – righe nella finestra: {lomb['righe']}, bandi "
         f"distinti: {lomb['bandi']}, non affidamenti diretti con scadenza "
         f">= oggi: **{lomb['aperti_non_diretti']}**. Copertura molto "
         f"parziale (poche SA lo alimentano): usato solo come confronto.",
         "",
         md_tabella(["Provincia", "Bandi aperti"],
                    lomb["per_provincia"].most_common()),
         "",
         "**Sintel (www.sintel.regione.lombardia.it)** – raggiungibile, ma "
         "la home reindirizza al portale ARIA (applicazione JavaScript) e non "
         "espone un elenco o un'API pubblica scaricabile: nessun dato usato.",
         "",
         "## 6. Mappatura CPV → macro-categoria",
         "",
         "Regola: si applica il prefisso più lungo che corrisponde; le "
         "divisioni 03-44 non elencate vanno in \"Forniture di beni\".",
         "",
         md_tabella(["Prefisso CPV", "Macro-categoria", "Contenuto"],
                    [[x["prefisso_cpv"], x["macro_categoria"],
                      x["descrizione_prefisso"]] for x in csv.DictReader(
                        open(ROOT / "config" / "cpv_macro.csv",
                             encoding="utf-8"))]),
         ""]
    (OUT / "report.md").write_text("\n".join(r), encoding="utf-8")
    print("\n".join(r[:40]))


if __name__ == "__main__":
    main()
