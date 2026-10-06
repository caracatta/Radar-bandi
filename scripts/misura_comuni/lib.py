"""Scaricatore rispettoso per la misura sui siti dei comuni (esplorativo).

- identifica il programma nello User-Agent (nessun finto browser);
- legge robots.txt e non scarica ciò che vieta; rispetta Crawl-delay;
- al massimo una richiesta al secondo per host (qui 1,3 s);
- niente login, niente invio di form, solo GET;
- cache su disco in data/raw/comuni/ (non versionata).
"""
import hashlib
import json
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
import http.cookiejar

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CACHE = ROOT / "data" / "raw" / "comuni"
UA = "radar-bandi-misura/0.1 (test di fattibilita, non uno scraper; caracatta@gmail.com)"
PAUSA = 1.3
MAX_BYTE = 6_000_000
_ultimo = {}
_robots = {}
# Cookie di sessione come farebbe un browser (alcuni gestionali tengono lo
# stato della ricerca in sessione); nessun login, nessun dato personale.
_opener = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def _attendi(host, pausa=PAUSA):
    t = time.time() - _ultimo.get(host, 0)
    if t < pausa:
        time.sleep(pausa - t)
    _ultimo[host] = time.time()


def _grezzo(url, timeout=25):
    """GET senza cache e senza robots (solo per robots.txt)."""
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept": "*/*",
                                               "Accept-Language": "it"})
    with _opener.open(req, timeout=timeout) as r:
        return r.status, r.geturl(), r.headers, r.read(MAX_BYTE)


def robots(base):
    p = urllib.parse.urlsplit(base)
    host = p.netloc
    if host in _robots:
        return _robots[host]
    rp = urllib.robotparser.RobotFileParser()
    info = {"url": f"{p.scheme}://{host}/robots.txt", "stato": None,
            "crawl_delay": None}
    try:
        _attendi(host)
        st, fin, h, body = _grezzo(info["url"])
        info["stato"] = st
        txt = body.decode("utf-8", "replace")
        if "<html" in txt[:500].lower():  # pagina d'errore con 200
            rp.parse([])
            info["nota"] = "robots.txt è una pagina HTML: ignorato"
        else:
            rp.parse(txt.splitlines())
            info["crawl_delay"] = rp.crawl_delay(UA) or rp.crawl_delay("*")
    except urllib.error.HTTPError as e:
        info["stato"] = e.code
        rp.parse([])  # 404 ecc.: nessuna restrizione
    except Exception as e:
        info["stato"] = repr(e)[:100]
        rp.parse([])
    _robots[host] = (rp, info)
    return _robots[host]


def scarica(url, sottocartella, timeout=25):
    """Restituisce dict {url, finale, stato, tipo, byte, file, errore,
    bloccato_da_robots}. I file vanno in CACHE/<sottocartella>/."""
    d = CACHE / sottocartella
    d.mkdir(parents=True, exist_ok=True)
    chiave = hashlib.sha1(url.encode()).hexdigest()[:16]
    meta_p = d / f"{chiave}.json"
    if meta_p.exists():
        return json.loads(meta_p.read_text())
    host = urllib.parse.urlsplit(url).netloc
    rp, info = robots(url)
    meta = {"url": url, "stato": None, "tipo": None, "byte": 0,
            "file": None, "errore": None, "bloccato_da_robots": False}
    if not rp.can_fetch(UA, url):
        meta["bloccato_da_robots"] = True
        meta_p.write_text(json.dumps(meta))
        return meta
    pausa = max(PAUSA, float(info.get("crawl_delay") or 0))
    try:
        _attendi(host, pausa)
        st, fin, h, body = _grezzo(url, timeout)
        meta.update(stato=st, finale=fin, tipo=h.get_content_type(),
                    byte=len(body))
        ext = {"application/pdf": "pdf"}.get(meta["tipo"], "html")
        f = d / f"{chiave}.{ext}"
        f.write_bytes(body)
        meta["file"] = str(f.relative_to(ROOT))
    except urllib.error.HTTPError as e:
        meta.update(stato=e.code, errore=f"HTTP {e.code}")
    except Exception as e:
        meta["errore"] = repr(e)[:150]
    meta_p.write_text(json.dumps(meta))
    return meta


def testo(meta):
    """Contenuto testuale del file scaricato (HTML grezzo) o None."""
    if not meta.get("file"):
        return None
    b = (ROOT / meta["file"]).read_bytes()
    for enc in ("utf-8", "latin-1"):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            continue
