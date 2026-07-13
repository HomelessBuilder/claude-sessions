#!/usr/bin/env python3
"""Local web viewer for claude-sessions transcripts.

Stdlib-only (http.server) so it has no dependency beyond pyte, which
render.py already needs. Deliberately plain Python + server-rendered HTML,
no framework, so lifting the list/render logic into ai-dev-platform's
FastAPI backend later is a straightforward port, not a rewrite.

Binds to 127.0.0.1 only — raw/ can contain secrets typed at a shell prompt,
this must never be exposed beyond localhost.
"""

import html
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

sys.path.insert(0, str(Path(__file__).parent))
from render import render  # noqa: E402

RAW_DIR = Path(__file__).parent.parent / "raw"
HOST = "127.0.0.1"
PORT = 8787

PAGE_STYLE = """
body { font-family: -apple-system, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; background: #1e1e1e; color: #ddd; }
a { color: #6cb6ff; }
h1 { font-size: 1.3rem; }
ul { list-style: none; padding: 0; }
li { padding: 0.4rem 0; border-bottom: 1px solid #333; }
pre { background: #111; padding: 1rem; overflow-x: auto; white-space: pre; font-size: 0.85rem; line-height: 1.4; border-radius: 6px; }
.meta { color: #888; font-size: 0.85rem; }
"""


def list_sessions():
    files = sorted(RAW_DIR.glob("*.typescript"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files


def index_page():
    rows = []
    for f in list_sessions():
        name = html.escape(f.name)
        rows.append(f'<li><a href="/session/{name}">{name}</a></li>')
    body = "\n".join(rows) if rows else "<p>No captured sessions yet.</p>"
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>claude-sessions viewer</title><style>{PAGE_STYLE}</style></head>
<body><h1>Captured terminal sessions</h1>
<p class="meta">{len(list_sessions())} session(s) in raw/ — served from 127.0.0.1 only.</p>
<ul>{body}</ul></body></html>"""


def session_page(filename):
    path = RAW_DIR / filename
    if not path.exists() or path.suffix != ".typescript" or path.parent != RAW_DIR:
        return None
    transcript = html.escape(render(path))
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>{html.escape(filename)}</title><style>{PAGE_STYLE}</style></head>
<body><p><a href="/">&larr; all sessions</a></p>
<h1>{html.escape(filename)}</h1>
<pre>{transcript}</pre></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        if path == "/":
            self._send_html(index_page())
        elif path.startswith("/session/"):
            filename = path[len("/session/"):]
            page = session_page(filename)
            if page is None:
                self._send_html("<h1>404</h1>", status=404)
            else:
                self._send_html(page)
        else:
            self._send_html("<h1>404</h1>", status=404)

    def _send_html(self, body, status=200):
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, fmt, *args):
        pass


def main():
    RAW_DIR.mkdir(exist_ok=True)
    server = HTTPServer((HOST, PORT), Handler)
    print(f"claude-sessions viewer running at http://{HOST}:{PORT}/  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
