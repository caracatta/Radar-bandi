"""Compone i risultati della misura sui siti dei comuni del campione.

I campi di giudizio (stato di lettura, gestionali, avvisi trovati, difficoltà)
sono stati compilati A MANO il 2026-10-06 leggendo le pagine scaricate dagli
script di questa cartella; qui sono raccolti in dizionari con la motivazione.
Gli URL, le date, i CIG, le scadenze ANAC e tutte le statistiche sono invece
calcolati dai dati (cache in data/raw/comuni/, anac_campione.csv).

Uso: python3 scripts/misura_comuni/risultati.py
Scrive: data/misura_comuni/comuni_risultati.csv, avvisi_trovati.csv,
        docs/misura_siti_comuni.md
"""
import collections
import csv
import json
import pathlib
import re
import statistics
import sys
import urllib.parse

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import lib  # noqa: E402
import analisi_lombardia as A  # noqa: E402

ROOT = lib.ROOT
OUT = ROOT / "data" / "misura_comuni"
OGGI = "2026-10-06"

# --- giudizi compilati a mano -------------------------------------------------
# stato: "completo" = albo + sezione bandi leggibili; "parziale" = solo alcune
# pagine; "robots" = robots.txt vieta tutto; "irraggiungibile".
MUNI = "Municipium (Maggioli)"
MYC = "MyCity (asset mycity.s3...ovh)"
JC = "J-City Gov / Albo online (Maggioli)"
RB = "robots.txt vieta ogni accesso"
D = {
    "Leno": ("completo", MUNI, JC, JC, ""),
    "Mazzano": ("completo", "SecovalWEB - Modello Comuni", JC,
                "etrasparenza.it (elenco procedure in HTML)",
                "robots.txt con Crawl-delay 10 s, rispettato"),
    "Ospitaletto": ("parziale", "Drupal 9 (footer Halley)",
                    "Drupal in sito: albo senza elenco in HTML",
                    "Drupal in sito: modulo Bandi e gare fermo al 2022",
                    "albo pretorio e trasparenza non mostrano elenchi in HTML; "
                    "connessioni resettate su alcune pagine"),
    "Sarezzo": ("completo", MYC, JC, "in sito (sezioni senza elenco in HTML)",
                ""),
    "Olgiate Comasco": ("completo", MYC, JC,
                        "portaletrasparenza.net (elenco in HTML)", ""),
    "Borgo Virgilio": ("parziale", MUNI, "Halley (halleyweb.com)",
                       "Halley (halleyweb.com)",
                       "halleyweb.com non raggiungibile da qui (errore TLS/503)"),
    "Cormano": ("completo", MUNI, JC, JC, ""),
    "Locate di Triulzi": ("parziale", "non identificato", "OpenWeb (servizi.*/openweb)",
                          "OpenWeb (servizi.*/openweb)",
                          "albo e trasparenza rispondono HTTP 403 al programma"),
    "Magenta": ("completo", "WordPress", JC, JC, ""),
    "Pieve Emanuele": ("completo", MUNI, JC, JC, "nessuna lista 'Pubblicazione' nel menu trasparenza"),
    "Bernareggio": ("completo", MUNI, JC, JC, ""),
    "Cornate d'Adda": ("completo", MUNI, JC, JC, ""),
    "Giussano": ("parziale", MUNI, JC + " su albo.comune.giussano.mb.it",
                 JC + " su albo.comune.giussano.mb.it",
                 "certificato TLS non valido sul sottodominio dell'albo: non letto"),
    "Seveso": ("completo", MUNI, JC, JC, ""),
    "Vimercate": ("completo", MUNI, JC + " (percorso /web/jiride)", JC,
                  "nessuna lista 'Pubblicazione' nel menu trasparenza"),
    "Mortara": ("robots", RB, RB, RB, "robots.txt: Disallow: /"),
    "Sondrio": ("parziale", "WordPress (bandi come tipo di contenuto)",
                "OpenWeb (sondrio.soluzionipa.it)", "in sito (elenco in HTML)",
                "albo HTTP 403 al programma; elenco 'Bandi in corso' solo con filtro JS"),
    "Caronno Pertusella": ("completo", MUNI, JC, JC, ""),
    "Gerenzano": ("completo", MUNI, JC, JC, "lista 'Pubblicazione' vuota"),
    "Varese": ("robots", RB, RB, RB, "robots.txt: Disallow: /"),
    "Bonate Sotto": ("robots", RB, RB, RB, "robots.txt: Disallow: /"),
    "Brembate di Sopra": ("completo", MUNI, JC, JC, ""),
    "Grumello del Monte": ("parziale", "Drupal 9 (Halley)", "Halley (halleyweb.com)",
                           "Halley (halleyweb.com)",
                           "halleyweb.com non raggiungibile da qui (HTTP 503)"),
    "Sirmione": ("completo", MUNI, JC, JC, ""),
    "Arosio": ("robots", RB, RB, RB, "robots.txt: Disallow: /"),
    "Cabiate": ("completo", "OpenCity Italia (Opencontent)", JC, JC,
                "albo senza voce di menu: letto dall'export della pagina"),
    "Lurago d'Erba": ("completo", MUNI, JC, JC, ""),
    "San Fermo della Battaglia": ("robots", RB, RB, RB, "robots.txt: Disallow: /"),
    "Pandino": ("completo", MYC, JC, JC + " (atti vecchi ricaricati nel 2026)",
                "la lista 'Pubblicazione' contiene atti del 2024-25 ripubblicati a settembre 2026"),
    "Spino d'Adda": ("parziale", MYC, "Halley (halleyweb.com)", "Halley (halleyweb.com)",
                     "halleyweb.com non raggiungibile da qui (TLS/503)"),
    "Lodi Vecchio": ("parziale", "eCOMUNE (Pacchetto PNRR)", "Hypersic (servizionline.hspromilaprod)",
                     "etrasparenza.it", "pagina Avvisi vuota senza JavaScript"),
    "Poggio Rusco": ("parziale", MYC, "ServiziOnLine (servizi.comune.*)",
                     "ServiziOnLine (servizi.comune.*)",
                     "connessione resettata dal server dell'albo"),
    "Rodigo": ("parziale", "WordPress (Datagraph)", "DG eGov (dgegovpa.it)",
               "DG eGov (dgegovpa.it)", "dgegovpa.it: robots.txt vieta l'accesso"),
    "Casorezzo": ("robots", RB, RB, RB, "robots.txt: Disallow: /"),
    "Cuggiono": ("parziale", MYC, "DG eGov (dgegovpa.it)", "DG eGov (dgegovpa.it)",
                 "dgegovpa.it: robots.txt vieta l'accesso"),
    "Robecco sul Naviglio": ("irraggiungibile", "-", "-", "-",
                             "errore TLS (EOF) su tutti i domini provati"),
    "San Colombano al Lambro": ("completo", MUNI, JC, JC, ""),
    "Vaprio d'Adda": ("parziale", MUNI, "Halley eGov (halleyegov.it) / Urbi",
                      "Halley eGov / Urbi",
                      "albo e trasparenza: robots.txt vieta l'accesso"),
    "Arcisate": ("parziale", MYC, "Urbi / PA Digitale (servizi.comune.*/urbi)",
                 "Urbi / PA Digitale", "albo e trasparenza: robots.txt vieta l'accesso"),
    "Ispra": ("completo", "WordPress", JC, JC, ""),
}
LEGG = {
    "completo": "HTML testo; albo e liste bandi ricavate dall'export CSV "
                "(OpenFormat) che la pagina offre; allegati PDF non raggiunti",
    "parziale": "HTML testo solo per le pagine novità/avvisi (e dove indicato "
                "albo/bandi); albo e trasparenza non leggibili (vedi difficoltà)",
    "robots": "non letto: robots.txt vieta ogni accesso",
    "irraggiungibile": "non letto: sito irraggiungibile",
}


def difficolta(stato, nota):
    base = {"completo": "elenchi non presenti nell'HTML: serve seguire il "
                        "link 'Esporta in OpenFormat' e una sessione; la "
                        "scadenza non è nell'elenco ma negli allegati",
            "parziale": "", "robots": "", "irraggiungibile": ""}[stato]
    return (nota + ("; " if nota and base else "") + base).strip("; ")


# --- avvisi (compilati a mano; URL, date, CIG ricavati dai dati) --------------
def cerca(comune, rx, lista=None):
    siti = {r["comune"]: r["codice_istat"] for r in csv.DictReader(open(
        ROOT / "data" / "comuni_siti.csv", encoding="utf-8"))}
    o = json.load(open(lib.CACHE / f"jcity_{siti[comune]}.json"))
    out = []
    for l in o["liste"]:
        if lista and lista not in l["risorsa"]:
            continue
        for r in l["righe"]:
            if re.search(rx, r.get("Oggetto") or "", re.I):
                out.append((l["risorsa"], r))
    return out


def anac(cig):
    for r in csv.DictReader(open(OUT / "anac_campione.csv",
                                 encoding="utf-8")):
        if r["cig"] == cig:
            return r
    return None


def data_it(s):
    m = re.match(r"(\d\d)/(\d\d)/(\d{4})", s or "")
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else ""


def avvisi():
    macro = A.carica_cpv()
    av = []
    # 1. Leno
    (_, alb), = cerca("Leno", r"distributori automatici", "Albo")[:1]
    (_, pub), = cerca("Leno", r"distributori automatici", "Pubblicazione")[:1]
    a = anac("BCC7BCB593")
    av.append(dict(
        categoria="A - conteggiato", comune="Leno",
        tipo="concessione di servizio, procedura negoziata previa pubblicazione "
             "(sotto 40.000 €)",
        oggetto="Concessione del servizio di somministrazione di alimenti e "
                "bevande mediante distributori automatici, 3 anni",
        settore=macro(a["cpv"]), pubblicazione="2026-08-27",
        scadenza=a["data_scadenza_offerta"], scadenza_fonte="ANAC",
        importo=a["importo_lotto"], cig="BCC7BCB593", in_anac="sì",
        url=pub["Url atto"] + " ; " + alb["Url atto"],
        note="sul sito: elenco trasparenza (27/08) e determina all'albo "
             "(22/09-07/10); scadenza e importo non nell'elenco, letti da ANAC"))
    # 2. Caronno
    (_, c), = cerca("Caronno Pertusella", r"ALL RISKS", "Pubblicazione")[:1]
    a = anac("BCFEB740B9")
    av.append(dict(
        categoria="A - conteggiato", comune="Caronno Pertusella",
        tipo="procedura aperta (art. 71 d.lgs. 36/2023)",
        oggetto="Affidamento copertura assicurativa All Risks, "
                "31/12/2026-30/06/2029",
        settore=macro(a["cpv"]), pubblicazione="2026-08-07",
        scadenza=a["data_scadenza_offerta"], scadenza_fonte="ANAC",
        importo=a["importo_lotto"], cig="BCFEB740B9", in_anac="sì",
        url=c["Url atto"],
        note="sul sito solo la determina a contrarre (06/08, elenco trasparenza); "
             "scadenza e importo letti da ANAC"))
    # 3. Cormano
    (_, c), = cerca("Cormano", r"distributori automatici", "Pubblicazione")[:1]
    av.append(dict(
        categoria="A - non verificato", comune="Cormano",
        tipo="concessione di servizio, procedura negoziata ex art. 187 con "
             "avviso di manifestazione di interesse",
        oggetto="Affidamento in concessione del servizio di somministrazione di "
                "bevande e alimenti mediante distributori automatici presso le "
                "sedi comunali (determina 638/2026)",
        settore=macro(anac("BCC7BCB593")["cpv"]) + " (per analogia con Leno)",
        pubblicazione="2026-09-14",
        scadenza="non letta", scadenza_fonte="-", importo="non letto "
        "(allegato 'Stima PEF')", cig="assente sul sito", in_anac="no (ANAC "
        "arriva al 2026-10-01; il CIG potrebbe essere stato creato dopo)",
        url=c["Url atto"],
        note="gli allegati (avviso, domanda, capitolato) non sono raggiungibili "
             "con link semplici; una seconda scheda identica è 'annullata'"))
    # altri avvisi non conteggiati tra gli appalti
    def una(comune, rx, lista=None):
        r = cerca(comune, rx, lista)
        return r[0][1] if r else None
    s = una("Sarezzo", r"POSTEGGI VACANTI")
    av.append(dict(
        categoria="B - altro, non conteggiato", comune="Sarezzo",
        tipo="bando di selezione per posteggi vacanti nei mercati "
             "(operatori commerciali su aree pubbliche)",
        oggetto="Bando di selezione per il rilascio di autorizzazioni e "
                "concessioni in posteggi vacanti nei mercati",
        settore="commercio su aree pubbliche (non appalto)",
        pubblicazione=data_it(s["Data inizio pubblicazione"]),
        scadenza=data_it(s["Data fine pubblicazione"]) + " (fine pubblicazione)",
        scadenza_fonte="albo", importo="-", cig="-", in_anac="n/a",
        url=s["Url atto"], note="rilevante per imprese, ma non è una gara"))
    s = una("Sirmione", r"SPIAGGIA ATTREZZATA")
    av.append(dict(
        categoria="B - altro, non conteggiato", comune="Sirmione",
        tipo="bando di gara di altro ente (Autorità di bacino laghi Garda e "
             "Idro) per concessione demaniale",
        oggetto="Bando per concessione demaniale di spiaggia attrezzata e "
                "deposito pedalò, canoe, sup (altro comune)",
        settore="turismo/demanio (non appalto del comune)",
        pubblicazione=data_it(s["Data inizio pubblicazione"]),
        scadenza=data_it(s["Data fine pubblicazione"]) + " (fine pubblicazione)",
        scadenza_fonte="albo", importo="-", cig="-", in_anac="n/a",
        url=s["Url atto"], note="pubblicato all'albo del comune per conto "
                                "di un altro ente"))
    av.append(dict(
        categoria="B - altro, non conteggiato", comune="Pieve Emanuele",
        tipo="asta pubblica per vendita di immobile comunale",
        oggetto="Vendita immobile comunale in Piazza Puccini: avviso di asta "
                "pubblica", settore="alienazione immobiliare (non appalto)",
        pubblicazione="2026-09-30", scadenza="non letta", scadenza_fonte="-",
        importo="non letto", cig="-", in_anac="n/a",
        url="https://comune.pieveemanuele.mi.it/it/news?type=3",
        note="visto solo nell'elenco novità; non aperta la scheda"))
    av.append(dict(
        categoria="B - altro, non conteggiato", comune="Lodi Vecchio",
        tipo="indizio: la delibera di giunta 114 del 09/09/2026 approva lo "
             "schema di avviso per manifestazione di interesse alla "
             "sponsorizzazione di eventi",
        oggetto="Avviso pubblico per manifestazione di interesse alla "
                "sponsorizzazione di eventi (avviso non trovato)",
        settore="sponsorizzazioni (non appalto)", pubblicazione="2026-09-09",
        scadenza="non letta", scadenza_fonte="-", importo="-", cig="-",
        in_anac="n/a",
        url="https://servizionline.hspromilaprod.hypersicapp.net/cmslodivecchio/"
            "portale/albopretorio/albopretorioconsultazione.aspx?&P=400&S=200&U=1",
        note="nell'albo c'è solo la delibera; la pagina Avvisi del sito è "
             "vuota senza JavaScript"))
    # esclusi
    for comune, rx, motivo in [
        ("Lurago d'Erba", r"CENTRO ANZIANI",
         "manifestazione di interesse riservata ad associazioni del Terzo "
         "settore, non imprese"),
        ("Cormano", r"ALBO DELLE ASSOCIAZIONI",
         "albo associazioni: non rilevante per imprese"),
        ("Olgiate Comasco", r"PREFETTURA DI COMO",
         "aste di locazione abitazioni del Fondo edifici di culto, altro ente"),
        ("Cabiate", r"LOCAZIONE DI UN APPARTAMENTO",
         "aste di locazione abitazioni del Fondo edifici di culto, altro ente"),
    ]:
        r = cerca(comune, rx)
        if r:
            x = r[0][1]
            av.append(dict(
                categoria="escluso", comune=comune, tipo=motivo,
                oggetto=(x["Oggetto"] or "")[:160], settore="-",
                pubblicazione=data_it(x["Data inizio pubblicazione"]),
                scadenza=data_it(x["Data fine pubblicazione"]) + " (fine pubblicazione)",
                scadenza_fonte="albo", importo="-", cig="-", in_anac="n/a",
                url=x["Url atto"], note=""))
    return av


def pagine_usate(comune, cod):
    out = []
    p = lib.CACHE / "riassunti" / f"{cod}.json"
    if p.exists():
        d = json.load(open(p))
        out.append(d["home"])
        for x in d["pagine"]:
            if x["stato"] == 200 and (x["tipo"] or "").startswith("text/html"):
                u = x["url"]
                if len(u) > 110:
                    u = u.split("?")[0]
                out.append(u)
    j = lib.CACHE / f"jcity_{cod}.json"
    if j.exists():
        for l in json.load(open(j))["liste"]:
            out.append(l["url"].split("?")[0] + " [export CSV]")
    return list(dict.fromkeys(out))[:10]


def main():
    camp = list(csv.DictReader(open(ROOT / "data" / "campione_comuni.csv",
                                    encoding="utf-8")))
    siti = {r["comune"]: r for r in csv.DictReader(open(
        ROOT / "data" / "comuni_siti.csv", encoding="utf-8"))}
    av = avvisi()
    conteggio = collections.Counter()
    nonver = collections.Counter()
    altri = collections.Counter()
    for a in av:
        if a["categoria"] == "A - conteggiato":
            conteggio[a["comune"]] += 1
        elif a["categoria"] == "A - non verificato":
            nonver[a["comune"]] += 1
        elif a["categoria"].startswith("B"):
            altri[a["comune"]] += 1
    anac_righe = list(csv.DictReader(open(OUT / "anac_campione.csv",
                                          encoding="utf-8")))
    rows = []
    for c in camp:
        n = c["comune"]
        stato, cms, albo, tras, nota = D[n]
        rec = dict(
            fascia=c["fascia"][0], comune=n, provincia=c["provincia"],
            abitanti=c["popolazione_2026"], sito=siti[n]["home"],
            stato_lettura=stato, cms_sito=cms, gestionale_albo=albo,
            gestionale_trasparenza=tras, leggibilita=LEGG[stato],
            avvisi_aperti_confermati=conteggio[n],
            avvisi_aperti_non_verificati=nonver[n],
            altri_avvisi_non_appalti=altri[n],
            difficolta=difficolta(stato, nota),
            pagine_usate=" | ".join(pagine_usate(n, c["codice_istat"])))
        rows.append(rec)
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "comuni_risultati.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    with open(OUT / "avvisi_trovati.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(av[0]))
        w.writeheader()
        w.writerows(av)

    # ---- tabelle ----
    def stats(fascia):
        r = [x for x in rows if x["fascia"] == fascia]
        letti = [x for x in r if x["stato_lettura"] in ("completo", "parziale")]
        compl = [x for x in r if x["stato_lettura"] == "completo"]
        def tab(gruppo, chiave):
            v = [x[chiave] + x["avvisi_aperti_non_verificati"]
                 if chiave == "avvisi_aperti_confermati" else x[chiave]
                 for x in gruppo]
            return v
        v_letti = tab(letti, "avvisi_aperti_confermati")
        v_compl = tab(compl, "avvisi_aperti_confermati")
        return dict(
            n=len(r), completi=len(compl),
            parziali=sum(1 for x in r if x["stato_lettura"] == "parziale"),
            robots=sum(1 for x in r if x["stato_lettura"] == "robots"),
            irr=sum(1 for x in r if x["stato_lettura"] == "irraggiungibile"),
            letti=len(letti), tot=sum(v_letti),
            media_letti=statistics.mean(v_letti), med_letti=statistics.median(v_letti),
            media_compl=statistics.mean(v_compl), med_compl=statistics.median(v_compl),
            zero=sum(1 for v in v_letti if v == 0),
            almeno1=sum(1 for v in v_letti if v >= 1),
            zero_c=sum(1 for v in v_compl if v == 0),
            almeno1_c=sum(1 for v in v_compl if v >= 1),
            tot_c=sum(v_compl),
            altri=sum(x["altri_avvisi_non_appalti"] for x in letti))
    SA, SB = stats("A"), stats("B")

    fam_albo = collections.defaultdict(list)
    fam_cms = collections.defaultdict(list)
    for x in rows:
        fam_albo[x["gestionale_albo"].split(" su ")[0].split(" (")[0]
                 if x["stato_lettura"] not in ("robots", "irraggiungibile")
                 else "non determinabile (sito non letto)"].append(x["comune"])
        fam_cms[x["cms_sito"] if x["stato_lettura"] not in
                ("robots", "irraggiungibile")
                else "non determinabile (sito non letto)"].append(x["comune"])

    # ---- ANAC ----
    comp = [r for r in anac_righe if "DIRETTO" not in r["tipo_scelta"]
            and r["tipo_scelta"] != "ND"]
    aperte = [r for r in comp if r["data_scadenza_offerta"] >= OGGI]
    senza_scad = [r for r in comp if not r["data_scadenza_offerta"]
                  and r["data_pubblicazione"] >= "2026-09-01"]
    dirette = [r for r in anac_righe if "DIRETTO" in r["tipo_scelta"]]
    stato_di = {x["comune"]: x["stato_lettura"] for x in rows}
    n_req = sum(1 for f in lib.CACHE.glob("*/*.json")
                if not f.parent.name.startswith(("riassunti",)))
    hosts = set()
    for f in lib.CACHE.glob("*/*.json"):
        try:
            hosts.add(urllib.parse.urlsplit(json.load(open(f))["url"]).netloc)
        except Exception:
            pass

    def fmt(x):
        return f"{x:.2f}".replace(".", ",")

    M = []
    M.append("# Misura: avvisi aperti sui siti dei comuni lombardi\n")
    M.append(f"Data della misura: **{OGGI}**. Finestra: ultimi 30 giorni di "
             "pubblicazione, ma contando come \"aperto\" tutto ciò che a oggi è "
             "ancora in corso. È un test di misura sul campione "
             "(`docs/campione_comuni.md`), non uno scraper di produzione; "
             "script in `scripts/misura_comuni/`, dati in `data/misura_comuni/`.\n")
    M.append("## Come ho misurato\n")
    M.append("- Programma identificato nello User-Agent, **robots.txt rispettato** "
             "(anche il Crawl-delay: Mazzano chiede 10 s), al massimo una "
             f"richiesta ogni 1,3 secondi per sito, solo GET, **nessun login**, "
             f"nessun aggiramento di blocchi. Circa {n_req} richieste di pagina "
             f"(comprese quelle fallite o bloccate da robots.txt) su "
             f"{len(hosts)} host, più un robots.txt per host.\n"
             "- Per ogni comune: home, albo pretorio, Amministrazione trasparente "
             "(Bandi di gara e contratti), pagine Avvisi/Bandi/Gare e le piattaforme "
             "collegate, nei limiti di ciò che il sito lascia leggere.\n"
             "- **Avviso aperto** = manifestazione di interesse, indagine di mercato, "
             "elenco fornitori, bando sotto soglia o gara aperta a cui un'impresa può "
             "rispondere, non ancora scaduto al 6 ottobre. Esclusi concorsi, contributi, "
             "avvisi ai cittadini, affidamenti già assegnati. Le aste di vendita, i "
             "bandi per posteggi e simili sono riportati a parte (categoria B) e non "
             "contati.\n"
             "- \"Confermato\" = scadenza non passata, letta dal sito o da ANAC "
             "(quando l'elenco del sito non la riporta). \"Non verificato\" = trovato "
             "ma scadenza non leggibile.\n")
    M.append("## 1. Risultato per fascia\n")
    M.append("| | Fascia A (> 10.000 ab.) | Fascia B (5.000-10.000 ab.) |\n|---|---:|---:|")
    def riga(lbl, a, b):
        M.append(f"| {lbl} | {a} | {b} |")
    riga("Comuni nel campione", SA["n"], SB["n"])
    riga("Comuni in Lombardia nella fascia", 196, 278)
    riga("Letti con albo e sezione bandi (\"completo\")", SA["completi"], SB["completi"])
    riga("Letti solo in parte (poche pagine)", SA["parziali"], SB["parziali"])
    riga("Non letti: robots.txt vieta tutto", SA["robots"], SB["robots"])
    riga("Non letti: sito irraggiungibile", SA["irr"], SB["irr"])
    riga("**Avvisi aperti trovati** (confermati + non verificati)",
         f"**{SA['tot']}**", f"**{SB['tot']}**")
    riga("Avvisi per comune, media (comuni letti completi+parziali)",
         fmt(SA["media_letti"]), fmt(SB["media_letti"]))
    riga("Avvisi per comune, mediana (idem)", fmt(SA["med_letti"]), fmt(SB["med_letti"]))
    riga("Comuni con zero avvisi (letti completi+parziali)", SA["zero"], SB["zero"])
    riga("Comuni con almeno un avviso (idem)", SA["almeno1"], SB["almeno1"])
    riga("Media sui soli comuni \"completi\"", fmt(SA["media_compl"]), fmt(SB["media_compl"]))
    riga("Zero / almeno uno nei soli \"completi\"",
         f"{SA['zero_c']} / {SA['almeno1_c']}", f"{SB['zero_c']} / {SB['almeno1_c']}")
    riga("Altri avvisi aperti non appalto (categoria B)", SA["altri"], SB["altri"])
    M.append("\nI comuni non letti **non** sono contati come zero: sono fuori dai "
             "denominatori delle righe \"comuni letti\". Per i 13 comuni letti "
             "solo in parte, lo zero significa \"niente di visibile "
             "lì\", non \"niente\".\n")
    M.append("### Avvisi aperti trovati\n")
    M.append("| Comune | Esito | Oggetto | Settore | Scadenza (fonte) | Importo | CIG | In ANAC |\n|---|---|---|---|---|---:|---|---|")
    for a in av:
        if a["categoria"].startswith("A"):
            M.append(f"| {a['comune']} | {a['categoria'][4:]} | {a['oggetto']} | "
                     f"{a['settore']} | {a['scadenza']} ({a['scadenza_fonte']}) | "
                     f"{a['importo']} | {a['cig']} | {a['in_anac'][:2]} |")
    M.append("\nTipo di procedura e URL di ciascuno sono in "
             "`data/misura_comuni/avvisi_trovati.csv`, insieme agli avvisi di "
             "categoria B ed esclusi:\n")
    for a in av:
        if a["categoria"].startswith("B"):
            M.append(f"- **{a['comune']}** (B, non contato): {a['oggetto']}; "
                     f"{a['note'] or a['tipo']}.")
    for a in av:
        if a["categoria"] == "escluso":
            M.append(f"- {a['comune']} (escluso): {a['tipo']}.")
    M.append("\n## 2. Famiglie di gestionale\n")
    M.append("Sono due livelli distinti: il **CMS del sito** (vetrina) e il "
             "**gestionale dell'albo/trasparenza**, dove stanno davvero gli atti.\n")
    M.append("### Gestionale dell'albo pretorio\n")
    M.append("| Famiglia | Comuni | Elenco |\n|---|---:|---|")
    for k, v in sorted(fam_albo.items(), key=lambda x: -len(x[1])):
        M.append(f"| {k} | {len(v)} | {', '.join(sorted(v))} |")
    M.append("\n### CMS del sito\n")
    M.append("| Famiglia | Comuni | Elenco |\n|---|---:|---|")
    for k, v in sorted(fam_cms.items(), key=lambda x: -len(x[1])):
        M.append(f"| {k} | {len(v)} | {', '.join(sorted(v))} |")
    n_albo = len([k for k in fam_albo if not k.startswith("non determ")])
    n_cms = len([k for k in fam_cms if not k.startswith("non determ")])
    M.append(f"\n**{n_albo} famiglie di albo** e **{n_cms} famiglie di CMS** "
             "tra i 33 siti di cui ho potuto vedere qualcosa. Un solo gestionale "
             "(J-City Gov di Maggioli) copre 21 comuni su 33 (20 letti; Giussano ha "
             "un certificato non valido) e ha un'uscita CSV standard che "
             "funziona allo stesso modo ovunque. Gli altri 12 sono singoli o "
             "a coppie e solo uno (Lodi Vecchio, Hypersic) ha un albo "
             "leggibile in HTML; Sondrio ha l'elenco bandi leggibile nel sito. "
             "Il resto vieta l'accesso automatico, risponde 403 o non risponde.\n")
    M.append("## 3. Confronto con ANAC\n")
    trov = [a for a in av if a["categoria"].startswith("A")]
    con_cig = [a for a in trov if a["cig"].startswith("B")]
    M.append(f"**Dagli avvisi trovati verso ANAC.** Dei {len(trov)} avvisi aperti "
             f"trovati sui siti, {len(con_cig)} riportano un CIG e **compaiono in "
             "ANAC** (Leno e Caronno Pertusella); 1 non ha CIG sul sito e non è in "
             "ANAC (Cormano: pubblicato il 14/09, i dati ANAC arrivano al 01/10 e "
             "una manifestazione di interesse spesso non ha ancora il CIG). Gli "
             "avvisi di categoria B non hanno CIG e non sono appalti.\n")
    M.append("**Da ANAC verso i siti (il controllo inverso, più informativo).** "
             f"Per i 40 comuni, ANAC ha {len(comp)} procedure competitive "
             f"(non affidamenti diretti) pubblicate dal 1° giugno e {len(dirette)} "
             f"affidamenti diretti. Quelle **ancora aperte al {OGGI}** "
             f"(scadenza offerte ≥ oggi) sono {len(aperte)}:\n")
    M.append("| Comune | Procedura | Scadenza | Importo € | Sito leggibile? | Trovata sul sito? |\n|---|---|---|---:|---|---|")
    trovate = {"BCC7BCB593": "sì (albo + trasparenza)",
               "BCFEB740B9": "sì (solo determina a contrarre)"}
    for r in aperte:
        st = stato_di[r["comune"]]
        t = trovate.get(r["cig"])
        if t is None:
            t = ("non verificabile (robots.txt)" if st == "robots"
                 else "**no**, non nelle liste lette")
        M.append(f"| {r['comune']} | {r['tipo_scelta'][10:42].title()} - "
                 f"{r['oggetto'][:55].capitalize()} | {r['data_scadenza_offerta']} | "
                 f"{float(r['importo_lotto'] or 0):,.0f} | "
                 f"{'no (robots.txt)' if st == 'robots' else 'sì'} | {t} |"
                 .replace(",", "."))
    leggibili = [r for r in aperte if stato_di[r["comune"]] != "robots"]
    M.append(f"\nSu {len(aperte)} procedure aperte note ad ANAC, "
             f"{len(aperte) - len(leggibili)} sono di comuni che vietano l'accesso "
             f"(non verificabili); delle {len(leggibili)} su comuni leggibili ne ho "
             "ritrovate sul sito **2**; la terza (Seveso, appalto integrato per la "
             "scuola dell'infanzia, 3,57 milioni, scadenza 08/10) **non** compare "
             "nelle liste dell'albo e della trasparenza che ho letto. "
             f"Inoltre {len(senza_scad)} procedure di settembre ("
             + ", ".join(f"{n} {c}" for n, c in collections.Counter(
                 r["comune"] for r in senza_scad).items())
             + ") non hanno ancora una scadenza in ANAC; per Sirmione non ho "
             "trovato corrispondenza sul sito: sono verosimilmente procedure su "
             "invito (non lo posso confermare).\n")
    M.append(f"**Cosa dice il confronto sul volume.** Le {len(comp)} "
             "procedure competitive di ANAC in 4 mesi su 40 comuni (circa 16 al mese, "
             "0,4 per comune al mese, comprese le negoziate su invito) e le "
             f"sole {len(aperte)} ancora aperte oggi (di cui 3 su siti non leggibili) "
             "sono coerenti con il flusso basso visto sui siti. Non ho prove "
             "su dove si pubblichino le gare che non trovo sui siti: la mia ipotesi, "
             "da verificare, è che passino da piattaforme di acquisto (Sintel, "
             "ecc.).\n")
    M.append("### Leggibilità automatica (40 comuni, una sola riga ciascuno)\n")
    M.append("| Modalità | Comuni |\n|---|---:|")
    M.append("| J-City Gov: elenchi non nell'HTML, ma leggibili dal CSV \"OpenFormat\" del portale (20 letti, più Giussano con certificato non valido) | 20 |")
    M.append("| Altri: elenco in HTML leggibile (Sondrio: bandi; Lodi Vecchio: albo) | 2 |")
    M.append("| Elenchi assenti dall'HTML senza JavaScript (Ospitaletto) | 1 |")
    M.append("| Solo pagine novità/avvisi leggibili; albo e trasparenza bloccati (robots.txt, 403, TLS/503, reset) | 10 |")
    M.append("| Non letti: robots.txt vieta tutto | 6 |")
    M.append("| Non letti: sito irraggiungibile | 1 |")
    M.append("\nPDF: ne ho letto uno (Vaprio d'Adda, testuale, non pertinente); "
             "nessun PDF scansionato incontrato; nessun sito \"solo piattaforma con "
             "login\" osservato. Gli allegati dei bandi dei portali J-City non "
             "sono raggiungibili con link semplici, quindi non li ho aperti.\n")
    M.append("## 4. Comune per comune\n")
    M.append("Dettaglio completo (pagine usate, gestionali, avvisi) in "
             "`data/misura_comuni/comuni_risultati.csv`.\n")
    M.append("| F | Comune | Lettura | Albo (gestionale) | Aperti | Difficoltà |\n|---|---|---|---|---:|---|")
    for x in rows:
        ap = x["avvisi_aperti_confermati"] + x["avvisi_aperti_non_verificati"]
        ap = ("-" if x["stato_lettura"] in ("robots", "irraggiungibile") else ap)
        M.append(f"| {x['fascia']} | {x['comune']} | {x['stato_lettura']} | "
                 f"{x['gestionale_albo'][:42]} | {ap} | {x['difficolta'][:110]} |")
    M.append("\n## 5. Limiti e cosa non ho potuto verificare\n")
    M.append(open(HERE / "limiti.md", encoding="utf-8").read())
    (ROOT / "docs" / "misura_siti_comuni.md").write_text("\n".join(M) + "\n",
                                                          encoding="utf-8")
    print("\n".join(M[:60]))


if __name__ == "__main__":
    main()
