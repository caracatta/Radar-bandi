"""Lettura con browser headless (Chromium) per le pagine che si compongono con
JavaScript. Stesse regole di cortesia di lib.py: robots.txt rispettato anche
per le richieste secondarie, al massimo una richiesta al secondo per host,
niente login, immagini/font/video/CSS non scaricati. Strumento di misura,
non è uno scraper di produzione.
"""
import sys
import time
import urllib.parse

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
import lib  # noqa: E402

BLOCCA = {"image", "media", "font", "stylesheet"}
EXE = "/opt/pw-browsers/chromium"


class Browser:
    def __init__(self):
        self._pw = sync_playwright().start()
        self.b = self._pw.chromium.launch(executable_path=EXE)
        self.ctx = self.b.new_context(user_agent=lib.UA, locale="it-IT",
                                      viewport={"width": 1280, "height": 900})
        self.ctx.route("**/*", self._route)
        self.richieste = 0
        self.bloccate_robots = []

    def _route(self, route):
        req = route.request
        if req.resource_type in BLOCCA:
            return route.abort()
        url = req.url
        if not url.startswith("http"):
            return route.continue_()
        host = urllib.parse.urlsplit(url).netloc
        rp, info = lib.robots(url)
        if not rp.can_fetch(lib.UA, url):
            self.bloccate_robots.append(url)
            return route.abort()
        pausa = max(lib.PAUSA, float(info.get("crawl_delay") or 0))
        lib._attendi(host, pausa)
        self.richieste += 1
        route.continue_()

    def pagina(self):
        return self.ctx.new_page()

    def vai(self, page, url, timeout=240000):
        rp, info = lib.robots(url)
        if not rp.can_fetch(lib.UA, url):
            return {"ok": False, "errore": "robots.txt vieta l'accesso"}
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            try:
                page.wait_for_load_state("networkidle", timeout=120000)
            except Exception:
                pass
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "errore": repr(e)[:200]}

    def chiudi(self):
        self.b.close()
        self._pw.stop()
