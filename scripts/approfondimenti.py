"""Approfondimenti sui bandi lombardi (aperte vs invito, importi, scadenze,
ritardo dei dati ANAC, servizi tecnici, sanità, manifestazioni di interesse,
affidamenti diretti).

Uso: python3 scripts/approfondimenti.py [--oggi AAAA-MM-GG] [--giorni 60]

Richiede i file in data/raw/ (scripts/scarica_fonti.py). Scrive
output/approfondimenti.md e alcuni CSV in output/.
"""
import argparse
import collections
import csv
import datetime as dt
import json
import pathlib
import re
import statistics

import analisi_lombardia as A
import scarica_fonti as S

ROOT = A.ROOT
OUT = A.OUT
RAW = A.RAW

# Procedure a cui chiunque può candidarsi (anche solo con richiesta di
# invito, nelle ristrette e nelle negoziate con bando) vs negoziate su invito.
CANDIDABILI = {"Aperta", "Ristretta", "Negoziata (bando)"}
INVITO = {"Negoziata (invito)"}
DIRETTI = {
    "AFFIDAMENTO DIRETTO": "Affidamento diretto",
    "AFFIDAMENTO DIRETTO A SOCIETA' IN HOUSE": "Affidamento in house",
    "AFFIDAMENTO DIRETTO IN ADESIONE AD ACCORDO QUADRO/CONVENZIONE":
        "Adesione ad accordo quadro/convenzione",
}
FASCE = [("< 150.000 €", lambda x: x < 150_000),
         ("150.000 – 1.000.000 €", lambda x: 150_000 <= x <= 1_000_000),
         ("> 1.000.000 €", lambda x: x > 1_000_000)]

SANITA = [  # prefissi CPV a 2 cifre della macro "Sanità e servizi alla persona"
    ("Farmaci e apparecchiature mediche", {"33"}),
    ("Servizi di assistenza e personale", {"85", "98"}),
    ("Ristorazione, mense e servizi alberghieri", {"55"}),
    ("Altro (istruzione e formazione, cultura e sport)", {"80", "92"}),
]
ENTE_SANITARIO = re.compile(
    r"\b(ASST|ASL|ATS|AZIENDA SOCIO|AZIENDA OSPEDAL|OSPEDAL|IRCCS|POLICLINICO|"
    r"A\.S\.S\.T|FONDAZIONE .*(OSPEDAL|IRCCS)|ISTITUTO .*(OSPEDAL|CURA)|"
    r"AZIENDA TERRITORIALE)\b", re.I)
PROGETTAZIONE = re.compile(
    r"progettazione|direzione (dei )?lavori|direzione dell.esecuzione|"
    r"collaudo|coordinamento (per )?(della )?sicurezza|\bDL\b|\bCSE\b|\bCSP\b|"
    r"verifica (della )?progett|studio di fattibilit|rilievi", re.I)
MANIFESTAZIONE = re.compile(
    r"manifestazion[ei] di interesse|indagin[ei] di mercato|"
    r"avviso (pubblico )?esplorativo|consultazione preliminare|"
    r"(elenco|albo) (di |degli |dei )?(operatori|fornitori|professionisti)|"
    r"(istituzione|costituzione|formazione|aggiornamento) (di |dell.)?"
    r"(un )?(elenco|albo)|ricognizione di mercato", re.I)


def eur(x):
    return f"{x:,.0f}".replace(",", ".")


def quartili(v):
    if not v:
        return None
    if len(v) == 1:
        return v[0], v[0], v[0]
    q1, med, q3 = statistics.quantiles(v, n=4, method="inclusive")
    return med, q1, q3


def riga_importi(nome, gs):
    v = sorted(g["importo_gara"] for g in gs if g["importo_gara"])
    q = quartili(v)
    fasce = [sum(1 for x in v if f(x)) for _, f in FASCE]
    senza = len(gs) - len(v)
    if not q:
        return [nome, len(gs), "-", "-", "-"] + fasce + [senza]
    return [nome, len(gs), eur(q[0]), eur(q[1]), eur(q[2])] + fasce + [senza]


INTEST_IMPORTI = ["", "Gare", "Mediana €", "1° quartile €", "3° quartile €",
                  "< 150.000", "150.000 – 1 M", "> 1 M", "Senza importo"]


def tabella_importi(gruppi):
    righe = [riga_importi(n, gs) for n, gs in gruppi]
    return A.md_tabella(INTEST_IMPORTI, righe), righe


def macro_gruppi(gs, tot="**Totale**"):
    out = [(m, [g for g in gs if g["macro_categoria"] == m])
           for m in A.MACRO]
    out = [(m, x) for m, x in out if x]
    return out + [(tot, gs)]


def scrivi_csv(nome, intest, righe):
    with open(OUT / nome, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(intest)
        w.writerows([[str(c).strip("*") for c in r] for r in righe])


# --- 1. tabelle sulle sole procedure candidabili ---------------------------

def tabelle_provincia(gs, prefisso_file):
    prov = collections.defaultdict(list)
    for g in gs:
        prov[g["provincia"] or "(non risolta)"].append(g)
    ordine = sorted(prov, key=lambda p: -len(prov[p]))
    intest_p = ["Provincia", "Gare", "Lotti (CIG)", "Sotto 40.000 €"]
    righe_p = []
    for p in ordine + [None]:
        x = prov[p] if p else gs
        righe_p.append([p or "**Totale Lombardia**", len(x),
                        sum(g["n_lotti_aperti"] for g in x),
                        sum(1 for g in x if g["importo_gara"]
                            and g["importo_gara"] < A.SOGLIA)])
    macro_usate = [m for m in A.MACRO
                   if any(g["macro_categoria"] == m for g in gs)]
    intest_m = ["Provincia"] + macro_usate + ["Totale"]
    righe_m = []
    for p in ordine + [None]:
        x = prov[p] if p else gs
        c = collections.Counter(g["macro_categoria"] for g in x)
        righe_m.append([p or "**Totale**"] + [c[m] for m in macro_usate]
                       + [len(x)])
    scrivi_csv(f"{prefisso_file}_provincia.csv", intest_p, righe_p)
    scrivi_csv(f"{prefisso_file}_provincia_macro.csv", intest_m, righe_m)
    return (A.md_tabella(intest_p, righe_p), A.md_tabella(intest_m, righe_m))


# --- 4. ritardo e frequenza di aggiornamento ANAC ---------------------------

def release_storico():
    """Date di pubblicazione dei file mensili 'cig' ricavate dal log ANAC."""
    p = RAW / "anac_cig_log.csv"
    if not p.exists():
        p.write_bytes(S.fetch(f"{S.ANAC}/download/dataset/cig/filesystem/"
                              "cig_csv_logCsv.csv"))
    ultimo = {}
    for r in csv.DictReader(open(p, encoding="utf-8", errors="replace"),
                            delimiter=";"):
        n = r["nome_risorsa"]
        if n.endswith("-cig_csv.csv") and r["ultimaModifica"]:
            ultimo[n[:8]] = max(ultimo.get(n[:8], ""), r["ultimaModifica"])
    return {k: v for k, v in sorted(ultimo.items())}


def analisi_ritardo(sa, oggi):
    files = A.file_mensili("cig")
    nomi = [f.name[:8] for f in files]
    rel = release_storico()
    primo, max_pub, per_giorno = {}, {}, {}
    for f in files:
        mx, giorni = "", collections.Counter()
        for r in csv.DictReader(open(f, encoding="utf-8", errors="replace"),
                                delimiter=";"):
            d = r["data_pubblicazione"]
            if d > mx:
                mx = d
            giorni[d] += 1
            s = sa.get(r["cf_amministrazione_appaltante"])
            if s and s["regione"] == "Lombardia" and d >= "2026-07-01":
                primo.setdefault(r["cig"], (f.name[:8], d,
                                            r["tipo_scelta_contraente"]))
        max_pub[f.name[:8]] = mx
        per_giorno[f.name[:8]] = giorni
    d = lambda s: dt.date.fromisoformat(s[:10])
    out = {"rel": rel, "max_pub": max_pub, "per_giorno": per_giorno,
           "nomi": nomi}
    # ritardo per i CIG la cui prima comparsa è nel file di riferimento
    lag, tardivi = collections.defaultdict(list), {}
    # Per il primo file non conosco il precedente: uso come limite
    # inferiore il rilascio del file del mese prima (07-08), perché i CIG
    # pubblicati prima potrebbero essere già comparsi in quello.
    mese0 = dt.date(int(nomi[0][:4]), int(nomi[0][4:6]), 1)
    prev0 = (mese0 - dt.timedelta(days=1)).strftime("%Y%m01")
    lo0 = rel[prev0][:10]
    for i, n in enumerate(nomi):
        prec = max_pub[nomi[i - 1]] if i else None
        lo = max_pub[nomi[i - 2]] if i > 1 else lo0
        for cig, (fn, pub, _) in primo.items():
            if fn != n:
                continue
            if (prec is None and pub > lo0) or (prec and pub > prec):
                lag[n].append((d(rel[n]) - d(pub)).days)
        if prec:
            # CIG già "coperti" dal file precedente per data, ma comparsi dopo
            nuovi = [pub for (fn, pub, _) in primo.values()
                     if fn == n and lo < pub <= prec]
            tot_prec = sum(1 for (fn, pub, _) in primo.values()
                           if lo < pub <= prec)
            tardivi[n] = (len(nuovi), tot_prec,
                          [(d(prec) - d(x)).days for x in nuovi])
    out["lag"], out["tardivi"] = lag, tardivi
    return out


def md_ritardo(r, oggi):
    righe_rel = [[k, v[:10], (d := dt.date.fromisoformat(v[:10])).day,
                  (d - dt.date(int(k[:4]), int(k[4:6]), 1)).days]
                 for k, v in r["rel"].items() if k >= "20240101"]
    giorni = [x[2] for x in righe_rel]
    out = ["Date di rilascio dei file mensili `cig` (dal registro ANAC "
           "`cig_csv_logCsv.csv`, ultima modifica del file), da gennaio 2024:",
           "",
           A.md_tabella(["File", "Rilasciato il", "Giorno del mese",
                         "Giorni dal 1° del mese"], righe_rel),
           "",
           f"Il registro ha dei buchi (mancano alcuni mesi, per esempio "
           "gennaio e marzo 2024 e da ottobre 2025 a marzo 2026): sono righe assenti "
           "dal log, non necessariamente file non rilasciati.", "",
           f"Frequenza: **un file al mese**, rilasciato tra il giorno "
           f"{min(giorni)} e il giorno {max(giorni)} (mediana: giorno "
           f"{statistics.median(giorni):.0f}). Ogni file è incrementale: "
           "contiene i CIG nuovi del periodo più i CIG precedenti che sono "
           "stati modificati (esiti, cancellazioni). Il dataset "
           "`stazioni-appaltanti` (anagrafica) invece è fermo al 2026-08-06.",
           "",
           "Fino a che data di pubblicazione arriva ciascun file:",
           ""]
    righe = []
    for n in r["nomi"]:
        pg = r["per_giorno"][n]
        mx = r["max_pub"][n]
        rel = r["rel"][n][:10]
        ult = [pg[(dt.date.fromisoformat(mx) - dt.timedelta(days=k))
                  .isoformat()] for k in range(0, 5)]
        righe.append([n, rel, mx,
                      (dt.date.fromisoformat(rel)
                       - dt.date.fromisoformat(mx)).days,
                      " / ".join(str(x) for x in ult)])
    out += [A.md_tabella(["File", "Rilasciato", "Ultima data di pubblicazione",
                          "Giorni di scarto", "CIG negli ultimi 5 giorni "
                          "(dal più recente)"], righe), "",
            "L'ultimo giorno di ogni file è spesso incompleto (vedi i CIG "
            "per giorno): quello di ottobre ha 2.298 CIG contro i circa "
            "5.500 di un giorno feriale normale.", "",
            "Ritardo con cui una gara compare nei dati, misurato sui CIG "
            "delle stazioni appaltanti lombarde alla loro **prima comparsa** "
            "(giorni tra la data di pubblicazione e il rilascio del file in "
            "cui compaiono per la prima volta):", ""]
    righe = []
    tutti = []
    for n in r["nomi"]:
        v = sorted(r["lag"].get(n, []))
        if not v:
            continue
        tutti += v
        p90 = v[int(0.9 * (len(v) - 1))]
        righe.append([n, len(v), min(v), f"{statistics.median(v):g}", p90,
                      max(v)])
    mediana = statistics.median(tutti)
    righe.append(["Tutti", len(tutti), min(tutti), f"{mediana:g}",
                  sorted(tutti)[int(0.9 * (len(tutti) - 1))], max(tutti)])
    out += [A.md_tabella(["File", "CIG", "Min", "Mediana", "90° percentile",
                          "Max"], righe), "",
            "Arrivi tardivi: CIG con data di pubblicazione *anteriore* "
            "all'ultima data già coperta dal file precedente, ma comparsi "
            "solo nel file successivo (pubblicati con ritardo nella BDNCP):",
            ""]
    righe = []
    for n, (k, tot, dist) in r["tardivi"].items():
        dist.sort()
        oltre3 = sum(1 for x in dist if x > 3)
        righe.append([n, k, tot, f"{100 * k / tot:.1f}" if tot else "-",
                      oltre3])
    out += [A.md_tabella(["File", "CIG tardivi", "CIG del periodo",
                          "% tardivi", "di cui pubblicati più di 3 giorni "
                          "prima della chiusura del file precedente"],
                         righe), "",
            "La maggior parte dei \"tardivi\" è il completamento dell'ultimo "
            "giorno, che il file precedente aveva solo in parte; gli "
            "arrivi davvero in ritardo (ultima colonna) sono pochi.", "",
            "In sintesi: una gara pubblicata il giorno D compare nei dati "
            "ANAC nel primo file rilasciato dopo D+1/D+4 giorni, quindi con "
            f"un ritardo che va da pochi giorni a oltre un mese (mediana "
            f"{mediana:g} giorni). Per una newsletter sulle gare *aperte* "
            "i dati ANAC sono quindi utili per misurare il flusso, non per "
            "segnalare le gare in tempo reale."]
    return "\n".join(out)


# --- main -------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oggi", default=dt.date.today().isoformat())
    ap.add_argument("--giorni", type=int, default=60)
    a = ap.parse_args()
    oggi = a.oggi
    inizio = (dt.date.fromisoformat(oggi)
              - dt.timedelta(days=a.giorni)).isoformat()
    tra15 = (dt.date.fromisoformat(oggi) + dt.timedelta(days=15)).isoformat()

    geo = A.Geo()
    sa = A.carica_stazioni(geo)
    macro = A.carica_cpv()
    gare, imbuto, _, _, _ = A.analisi_anac(inizio, oggi, geo, sa, macro)
    cand = [g for g in gare if g["procedura"] in CANDIDABILI]
    inv = [g for g in gare if g["procedura"] in INVITO]
    aperta = [g for g in gare if g["procedura"] == "Aperta"]
    assert len(cand) + len(inv) == len(gare)
    proc = collections.Counter(g["procedura"] for g in gare)

    R = [f"# Approfondimenti sui bandi lombardi aperti",
         "",
         f"Data di riferimento **{oggi}**, finestra {inizio} → {oggi}. "
         "Stessi dati e stesse regole di `report.md`: qui si guarda dentro "
         f"le {len(gare)} gare aperte e agli affidamenti diretti. "
         "Unità = gara (CIG raggruppati per `numero_gara`), salvo dove "
         "indicato.", ""]

    # 1 ----
    R += ["## 1. Aperte a tutti o su invito?", "",
          f"Delle **{len(gare)}** gare aperte:", "",
          A.md_tabella(["Tipo di procedura", "Gare", "Candidabili da "
                        "chiunque?"],
                       [["Procedura aperta", proc["Aperta"], "sì"],
                        ["Procedura ristretta", proc["Ristretta"],
                         "sì, con richiesta di invito"],
                        ["Negoziata con bando / indizione (settori speciali)",
                         proc["Negoziata (bando)"],
                         "sì, con richiesta di invito"],
                        ["Negoziata senza previa pubblicazione (su invito)",
                         proc["Negoziata (invito)"], "no, solo invitati"]]),
          "",
          f"- **{len(inv)} su {len(gare)} ({100 * len(inv) / len(gare):.0f}%) "
          f"sono su invito**, quindi non sono candidabili liberamente.",
          f"- **{len(cand)} ({100 * len(cand) / len(gare):.0f}%)** sono "
          f"aperte a candidature (di cui {len(aperta)} procedure aperte "
          f"in senso stretto).",
          "- Attenzione: nelle negoziate su invito spesso l'invito è "
          "preceduto da un avviso di manifestazione di interesse che il "
          "CIG non distingue (vedi punto 7): una parte dei 162 casi era "
          "quindi candidabile *prima* dell'invito, ma nei dati non si "
          "vede.", ""]
    t_p, t_m = tabelle_provincia(cand, "aperte_candidabili")
    R += [f"### Gare candidabili ({len(cand)}) per provincia", "", t_p, "",
          f"### Gare candidabili ({len(cand)}) per provincia × macro-categoria",
          "", t_m, ""]
    tprov_i, tm_i = tabelle_provincia(inv, "aperte_su_invito")
    R += [f"### Per confronto: gare su invito ({len(inv)}) per provincia", "",
          tprov_i, ""]

    # 2 ----
    R += ["## 2. Distribuzione degli importi per macro-categoria", "",
          "Importo = `importo_complessivo_gara` (base d'asta di tutta la "
          "gara, non del singolo lotto; per gli accordi quadro è il "
          "massimale). Quartili con il metodo inclusivo.", "",
          f"### Gare candidabili ({len(cand)})", ""]
    md, righe = tabella_importi(macro_gruppi(cand))
    R += [md, ""]
    scrivi_csv("importi_candidabili_macro.csv", INTEST_IMPORTI, righe)
    R += [f"### Tutte le gare aperte ({len(gare)})", ""]
    md, righe = tabella_importi(macro_gruppi(gare))
    R += [md, ""]
    scrivi_csv("importi_tutte_macro.csv", INTEST_IMPORTI, righe)

    # 3 ----
    R += [f"## 3. Gare con scadenza ad almeno 15 giorni da oggi", "",
          f"Scadenza di presentazione ≥ **{tra15}** (per le gare a più "
          "lotti, la scadenza più lontana tra i lotti aperti).", ""]
    righe = []
    for m, gs in macro_gruppi(gare):
        c = [g for g in gs if g["procedura"] in CANDIDABILI]
        i = [g for g in gs if g["procedura"] in INVITO]
        f15 = lambda x: sum(1 for g in x if g["scadenza"] >= tra15)
        righe.append([m, len(gs), f15(gs), len(c), f15(c), len(i), f15(i)])
    intest = ["Macro-categoria", "Tutte", "≥ 15 gg", "Candidabili",
              "≥ 15 gg ", "Su invito", "≥ 15 gg  "]
    R += [A.md_tabella(intest, righe), ""]
    scrivi_csv("scadenza_15gg_macro.csv", intest, righe)
    tot, t15 = righe[-1][1], righe[-1][2]
    R += [f"In totale {t15} gare su {tot} ({100 * t15 / tot:.0f}%) hanno "
          f"almeno 15 giorni davanti; tra le candidabili {righe[-1][4]} su "
          f"{righe[-1][3]}.", ""]

    # 4 ----
    R += ["## 4. Aggiornamento dei dati ANAC e ritardo", "",
          md_ritardo(analisi_ritardo(sa, oggi), oggi), ""]

    cig = A.carica_cig(inizio, oggi)
    lomb = {k: r for k, r in cig.items()
            if (sa.get(r["cf_amministrazione_appaltante"]) or {}
                ).get("regione") == "Lombardia"}
    dir_cig = [r for r in lomb.values()
               if r["tipo_scelta_contraente"] in DIRETTI
               and not r["DATA_CANCELLAZIONE"]]

    # 5 ----
    tec = "Servizi tecnici, IT e professionali"
    R += ["## 5. Servizi tecnici: progettazione, direzione lavori, collaudo",
          "",
          "Dentro la macro-categoria \"Servizi tecnici, IT e "
          "professionali\", i servizi di ingegneria e architettura sono il "
          "CPV 71xxxxxx. Colonna \"con parole chiave\": l'oggetto cita "
          "progettazione, direzione lavori, collaudo, coordinamento della "
          "sicurezza, verifica del progetto, rilievi.", ""]
    righe = []
    for nome, gs in [("Tutte le gare aperte", gare),
                     ("Candidabili", cand), ("Su invito", inv)]:
        t = [g for g in gs if g["macro_categoria"] == tec]
        s71 = [g for g in t if g["cpv"].startswith("71")]
        kw = [g for g in s71 if PROGETTAZIONE.search(g["oggetto"])]
        righe.append([nome, len(gs), len(t), len(s71), len(kw),
                      len(t) - len(s71)])
    R += [A.md_tabella(["Insieme", "Gare", "Servizi tecnici/IT",
                        "di cui CPV 71", "CPV 71 con parole chiave",
                        "Altri servizi tecnici/IT (non 71)"], righe), ""]
    s71 = [g for g in gare if g["cpv"].startswith("71")]
    c71 = collections.Counter((g["cpv"], g["descrizione_cpv"]) for g in s71)
    kw_tutte = [g for g in gare if PROGETTAZIONE.search(g["oggetto"])]
    kw_macro = collections.Counter(g["macro_categoria"] for g in kw_tutte)
    kw_71 = sum(1 for g in kw_tutte if g["cpv"].startswith("71"))
    d71 = [r for r in dir_cig if r["cod_cpv"].startswith("71")]
    R += [f"Controllo incrociato: le gare aperte con parole chiave di "
          f"progettazione/DL/collaudo nell'oggetto, **qualunque sia il "
          f"CPV**, sono {len(kw_tutte)} (di cui {kw_71} con CPV 71); le "
          "altre sono lavori o forniture che citano la progettazione "
          "(per esempio appalti integrati): " + ", ".join(
              f"{m} {n}" for m, n in kw_macro.most_common()) + ". "
          f"Per confronto, gli **affidamenti diretti** con CPV 71 nella "
          f"finestra sono {len(d71)} CIG (il CPV 71 include anche prove e "
          "laboratori, quindi non sono tutti progettazione): i servizi "
          "tecnici passano in larga parte da affidamento diretto, non da "
          "gare aperte.", ""]
    R += ["CPV 71 delle gare aperte, dettaglio:", "",
          A.md_tabella(["CPV", "Descrizione", "Gare"],
                       [[c, d, n] for (c, d), n in c71.most_common()]), "",
          "Il CPV è quello del lotto di importo maggiore: una gara mista "
          "(lavori + progettazione) può quindi cadere in un'altra "
          "categoria. Le gare 71 senza parole chiave nell'oggetto sono "
          "per lo più verifiche, indagini e servizi tecnici di altra "
          "natura.", ""]
    R += ["Gare CPV 71 *senza* parole chiave (controllo a campione, primi "
          "10):", ""]
    senza = [g for g in s71 if not PROGETTAZIONE.search(g["oggetto"])][:10]
    R += [A.md_tabella(["CPV", "Procedura", "Oggetto"],
                       [[g["cpv"], g["procedura"],
                         g["oggetto"][:110].replace("|", "/")]
                        for g in senza]), ""]

    # 6 ----
    san = "Sanità e servizi alla persona"
    R += ["## 6. Sanità e servizi alla persona, divisa in sotto-gruppi", "",
          "La macro-categoria contiene i CPV 33 (apparecchi medicali e "
          "farmaci), 85 e 98 (assistenza sanitaria e sociale, servizi alla "
          "persona), 55 (ristorazione e alberghi), 80 (istruzione), 92 "
          "(cultura e sport). **La pulizia (CPV 90) non è nella sanità ma "
          "in \"Pulizie, sanificazione e rifiuti\"**: il terzo gruppo "
          "richiesto (\"pulizia, mense e servizi di supporto\") qui contiene "
          "quindi solo mense e ristorazione (55); la pulizia degli enti "
          "sanitari è nella riga a parte sotto. I CPV 80 e 92 non rientrano "
          "in nessuno dei tre gruppi e sono in una riga \"Altro\".", ""]
    sg = [(n, [g for g in gare if g["macro_categoria"] == san
               and g["cpv"][:2] in pref]) for n, pref in SANITA]
    tot_san = [g for g in gare if g["macro_categoria"] == san]
    for nome, base in [(f"Tutte le gare aperte ({len(gare)})", gare),
                       (f"Gare candidabili ({len(cand)})", cand)]:
        ids = [(n, _IdSet(x)) for n, x in sg]
        sub = [(n, [g for g in base if g in i]) for n, i in ids]
        R += [f"### {nome}", "",
              tabella_importi(sub + [("**Totale sanità**",
                                      [g for g in base
                                       if g["macro_categoria"] == san])])[0],
              ""]
    pul = [g for g in gare if g["macro_categoria"]
           == "Pulizie, sanificazione e rifiuti"
           and ENTE_SANITARIO.search(g["stazione_appaltante"])]
    pul_c = [g for g in pul if g["procedura"] in CANDIDABILI]
    R += ["Pulizia, sanificazione e rifiuti acquistati da enti sanitari "
          "(nome dell'ente con ASST, ASL, ATS, IRCCS, ospedale, "
          "policlinico), fuori dalla macro sanità:", "",
          tabella_importi([("Tutte", pul), ("Candidabili", pul_c)])[0], "",
          "Riconoscimento degli enti sanitari dal solo nome "
          "dell'ente: può mancarne qualcuno.", ""]
    ent = [g for g in gare if ENTE_SANITARIO.search(g["stazione_appaltante"])]
    righe = []
    for m, gs in macro_gruppi(ent):
        c = [g for g in gs if g["procedura"] in CANDIDABILI]
        righe.append([m, len(gs), len(c), len(gs) - len(c)])
    R += ["Vista per **ente**: gare aperte bandite da enti sanitari "
          "(ASST, ASL, ATS, IRCCS, ospedali, policlinici, riconosciuti dal "
          "nome), per macro-categoria CPV:", "",
          A.md_tabella(["Macro-categoria", "Gare", "Candidabili",
                        "Su invito"], righe), ""]
    scrivi_csv("importi_sanita_sottogruppi.csv", INTEST_IMPORTI,
               tabella_importi(sg + [("Totale sanità", tot_san)])[1])

    # 7 + 8 ----
    kw_tipo = collections.Counter()
    esempi = []
    for r in lomb.values():
        t = f'{r["oggetto_gara"]} {r["oggetto_lotto"]}'
        if MANIFESTAZIONE.search(t):
            kw_tipo[r["tipo_scelta_contraente"]] += 1
            if r["tipo_scelta_contraente"] not in DIRETTI and len(esempi) < 6:
                esempi.append((r["tipo_scelta_contraente"],
                               t[:120].replace("|", "/")))
    kw_gare = collections.Counter()
    for g in gare:
        if MANIFESTAZIONE.search(g["oggetto"]):
            kw_gare[g["procedura"]] += 1
    campi = ["cod_tipo_scelta_contraente / tipo_scelta_contraente",
             "cod_modalita_realizzazione / modalita_realizzazione",
             "COD_MODALITA_INDIZIONE_SPECIALI / _SERVIZI",
             "COD_STRUMENTO_SVOLGIMENTO / STRUMENTO_SVOLGIMENTO",
             "TIPO_APPALTO_RISERVATO", "FLAG_URGENZA", "COD_ESITO / ESITO"]
    n_lomb = len(lomb)
    R += ["## 7. Manifestazioni di interesse, indagini di mercato, "
          "elenchi fornitori", "",
          "**Nei dati ANAC non esiste un campo che li distingua.** Ho "
          "controllato tutti i campi del dataset `cig`:", "",
          "- " + "\n- ".join(campi), "",
          "I valori di `tipo_scelta_contraente` sono solo: affidamento "
          "diretto (3 varianti), procedura aperta, ristretta, negoziata "
          "senza previa pubblicazione, negoziata previa pubblicazione, "
          "negoziata con indizione (settori speciali), altra procedura a "
          "fase unica, altra procedura a più fasi, procedura di gara, ND. "
          "I campi `MODALITA_INDIZIONE_*` e `STRUMENTO_SVOLGIMENTO` sono "
          "quasi sempre vuoti (nel file di ottobre, sulle circa 16.900 righe "
          "lombarde della finestra, ne sono valorizzate rispettivamente 1 e "
          "42). Nessuna categoria \"avviso\", "
          "\"manifestazione di interesse\", \"indagine di mercato\" o "
          "\"elenco operatori\". Un avviso di manifestazione di interesse "
          "viene registrato solo se genera un CIG, e con il tipo della "
          "procedura che segue (di solito negoziata senza previa "
          "pubblicazione o \"altra procedura a più fasi\").", "",
          "Come **stima per difetto** ho cercato nell'oggetto della gara le "
          "diciture \"manifestazione di interesse\", \"indagine di "
          "mercato\", \"avviso esplorativo\", \"consultazione "
          "preliminare\", \"elenco/albo operatori/fornitori\", "
          "\"istituzione di un elenco\". Dipende dal testo scritto "
          "dall'ente: non è un campo strutturato.", "",
          f"CIG delle stazioni appaltanti lombarde pubblicati nella finestra "
          f"({n_lomb}), con queste diciture nell'oggetto, per tipo di "
          "procedura:", "",
          A.md_tabella(["Tipo di procedura", "CIG con la dicitura"],
                       kw_tipo.most_common()
                       + [["**Totale**", sum(kw_tipo.values())]]), "",
          "Tra le **gare aperte conteggiate** nel report: " + (
              ", ".join(f"{k} {v}" for k, v in kw_gare.most_common())
              or "nessuna") + f" (totale {sum(kw_gare.values())} su "
          f"{len(gare)}).", "",
          "Esempi di oggetti trovati (fuori dagli affidamenti diretti):", "",
          A.md_tabella(["Procedura", "Oggetto"], [list(e) for e in esempi]),
          "",
          "Gli avvisi che non hanno generato un CIG (per esempio quelli "
          "pubblicati sui portali dei singoli enti) non sono nei dati ANAC "
          "e quindi non sono contati.", ""]

    # 8
    prov = collections.defaultdict(list)
    for r in dir_cig:
        s = sa[r["cf_amministrazione_appaltante"]]
        prov[s["provincia"] or "(non risolta)"].append(
            (macro(r["cod_cpv"]), r))
    ordine = sorted(prov, key=lambda p: -len(prov[p]))
    macro_usate = [m for m in A.MACRO
                   if any(x[0] == m for v in prov.values() for x in v)]
    intest = ["Provincia"] + macro_usate + ["Totale", "di cui < 40.000 €"]
    righe = []
    for p in ordine + [None]:
        v = prov[p] if p else [x for vv in prov.values() for x in vv]
        c = collections.Counter(m for m, _ in v)
        sotto = sum(1 for _, r in v if A.num(r["importo_lotto"]) is not None
                    and A.num(r["importo_lotto"]) < A.SOGLIA)
        righe.append([p or "**Totale**"] + [c[m] for m in macro_usate]
                     + [len(v), sotto])
    scrivi_csv("affidamenti_diretti_provincia_macro.csv", intest, righe)
    per_tipo = collections.Counter(DIRETTI[r["tipo_scelta_contraente"]]
                                   for r in dir_cig)
    senza_imp = sum(1 for r in dir_cig if A.num(r["importo_lotto"]) is None)
    R += ["## 8. Affidamenti diretti (solo informativo)", "",
          f"Affidamenti diretti delle stazioni appaltanti lombarde "
          f"pubblicati negli ultimi {a.giorni} giorni, esclusi i cancellati. "
          "**Unità = CIG** (un affidamento diretto ha di norma un solo "
          "lotto). **Non sono nelle tabelle delle gare aperte.** Sono "
          "atti già assegnati: servono a misurare il mercato sotto soglia, "
          "non a segnalare opportunità. La macro-categoria è assegnata dal "
          "CPV del CIG. L'importo è quello del lotto.", "",
          A.md_tabella(["Tipo", "CIG"], per_tipo.most_common()
                       + [["**Totale**", len(dir_cig)]]), "",
          A.md_tabella(intest, righe), "",
          f"CIG senza importo: {senza_imp}.", ""]

    (OUT / "approfondimenti.md").write_text("\n".join(R), encoding="utf-8")
    print("\n".join(R))


class _IdSet:
    """Insieme di gare confrontate per identità (i dict non sono hashable)."""
    def __init__(self, gs):
        self.ids = {id(g) for g in gs}

    def __contains__(self, g):
        return id(g) in self.ids


if __name__ == "__main__":
    main()
