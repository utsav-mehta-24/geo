"""Real-time GEO personalization server (standard library only).

Every request runs the pipeline live: parse the query → rank all pages →
regenerate the best-fit page personalized to the intent → re-rank → serve.

    python server.py            # http://127.0.0.1:8000
    python server.py --port 9000

Routes
  GET /                         live console: type a query, see ranking + page
  GET /api/personalize?q=...    JSON report (before/after ranking, delta, caveat)
  GET /page/<id>?q=...          the product page as served for that query
  GET /page/<id>                the seeded "before" page (no personalization)
  GET /health                   liveness check

Personalized variants keep <link rel="canonical"> on the base product URL, so
answer engines and crawlers treat them as one page, not duplicates.
"""
import argparse
import html
import json
import pathlib
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, urlparse

import ai
from pipeline import BEFORE_PAGES, BY_ID, run

MAX_QUERY = 300
IMG_RE = re.compile(r"^/page/img/([a-z0-9-]+)-(pack|hero|ingredients|lifestyle|texture|prep)\.jpg$")
PAGE_RE = re.compile(r"^/page/([a-z0-9-]+)/?$")
VARIANT_LABEL = {"pack": "Packaging shot", "hero": "Beverage hero shot",
                 "ingredients": "Ingredient story", "lifestyle": "Mood / lifestyle",
                 "texture": "Texture shot", "prep": "Preparation visual"}


def placeholder_svg(pid: str, variant: str) -> bytes:
    """Stand-in for the six-part visual standard until real assets exist."""
    name = html.escape(BY_ID[pid]["name"]) if pid in BY_ID else "KATHAI"
    label = VARIANT_LABEL[variant]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300">
<rect width="300" height="300" fill="#e8dccb"/>
<text x="150" y="140" text-anchor="middle" font-family="Georgia,serif" font-size="22" fill="#3b2314">{name}</text>
<text x="150" y="172" text-anchor="middle" font-family="Georgia,serif" font-size="14" fill="#8a6a4a">{label}</text>
<text x="150" y="196" text-anchor="middle" font-family="Georgia,serif" font-size="11" fill="#a08a72">placeholder asset</text>
</svg>""".encode("utf-8")


def flavour_art(pid: str) -> bytes | None:
    """Return the bespoke flavour illustration used across that product's image slots."""
    path = pathlib.Path(__file__).parent / "static" / "flavours" / f"{pid}.svg"
    return path.read_bytes() if path.is_file() else None


class Handler(BaseHTTPRequestHandler):
    server_version = "KathaiGEO/1.0"

    def _send(self, code: int, body: bytes, ctype: str, extra: dict | None = None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, code: int, obj: dict):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def _query(self, url) -> str:
        q = parse_qs(url.query).get("q", [""])[0].strip()
        return q[:MAX_QUERY]

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        url = urlparse(self.path)
        path = url.path

        if path in ("/", "/index.html"):
            # Read per request so console edits apply without a restart.
            return self._send(200, CONSOLE.read_bytes(), "text/html; charset=utf-8")

        if path == "/health":
            return self._json(200, {"ok": True, "products": len(BY_ID)})

        if path == "/api/personalize":
            q = self._query(url)
            if not q:
                return self._json(400, {"error": "missing query parameter q"})
            # mode=before: the console's before view — never spends on AI
            before_only = parse_qs(url.query).get("mode", [""])[0] == "before"
            report, _ = run(q, use_ai=not before_only)
            report["page_url"] = (f"/page/{report['refresh_target']}?q={quote(q)}"
                                  if report["refreshed"] else None)
            return self._json(200, report)

        m = IMG_RE.match(path)
        if m:
            art = flavour_art(m.group(1))
            if art:
                return self._send(200, art, "image/svg+xml; charset=utf-8")
            return self._send(200, placeholder_svg(*m.groups()), "image/svg+xml")

        m = PAGE_RE.match(path)
        if m:
            pid = m.group(1)
            if pid not in BY_ID:
                return self._json(404, {"error": f"unknown product '{pid}'"})
            q = self._query(url)
            if q:
                report, pages = run(q)
                personalized = report["refresh_target"] == pid
                headers = {"X-Kathai-Intent": ",".join(report["parsed_intent_facets"]) or "none",
                           "X-Kathai-Personalized": "yes" if personalized else "no",
                           "X-Kathai-Render-Ms": str(report["timing_ms"]),
                           "X-Kathai-Content": report["content"]["source"]}
                return self._send(200, pages[pid].encode("utf-8"),
                                  "text/html; charset=utf-8", headers)
            return self._send(200, BEFORE_PAGES[pid].encode("utf-8"),
                              "text/html; charset=utf-8",
                              {"X-Kathai-Personalized": "no"})

        return self._json(404, {"error": "not found"})

    def log_message(self, fmt, *args):
        # Log path only, not the query string (queries are user input).
        print(f"{self.address_string()} {self.command} {urlparse(self.path).path} "
              f"{args[1] if len(args) > 1 else ''}")


CONSOLE = pathlib.Path(__file__).parent / "static" / "console.html"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    for stream in (sys.stdout, sys.stderr):   # Windows consoles default to cp1252
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    srv =ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"KATHAI GEO live server → http://{args.host}:{args.port}  (Ctrl+C to stop)")
    print("AI: " + (f"on\n  text models:  {', '.join(ai.TEXT_MODELS)}\n"
                    if ai.enabled() else "off (no OPENROUTER_API_KEY) — template content"))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
