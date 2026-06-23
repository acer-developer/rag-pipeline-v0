"""
A tiny local web viewer for the Chroma vector store. Stdlib only.

Run:  python view_db.py
Then open http://localhost:8000 in your browser.

  - Home page lists every chunk in the collection (id, source, preview).
  - The search box runs a live semantic (vector) search and shows ranked hits.
"""
from __future__ import annotations

import html
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

import chromadb

import config

PORT = 8000

client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))


def page(body: str) -> bytes:
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>Chroma Viewer — {html.escape(config.COLLECTION_NAME)}</title>
<style>
 body{{font-family:system-ui,Segoe UI,Arial;margin:2rem;max-width:1000px;color:#1a1a1a}}
 h1{{font-size:1.3rem}} .muted{{color:#666;font-size:.85rem}}
 form{{margin:1rem 0}} input[type=text]{{width:60%;padding:.5rem;font-size:1rem}}
 button{{padding:.5rem 1rem;font-size:1rem;cursor:pointer}}
 table{{border-collapse:collapse;width:100%;margin-top:1rem}}
 th,td{{border:1px solid #ddd;padding:.5rem;text-align:left;vertical-align:top;font-size:.9rem}}
 th{{background:#f4f4f4}} code{{background:#f0f0f0;padding:1px 4px;border-radius:3px}}
 .dist{{font-variant-numeric:tabular-nums;white-space:nowrap}}
</style></head><body>{body}</body></html>""".encode("utf-8")


def home(query: str | None) -> bytes:
    try:
        col = client.get_collection(config.COLLECTION_NAME)
    except Exception:
        return page("<h1>No collection found</h1><p>Run <code>python ingest.py</code> first.</p>")

    search_box = f"""
      <h1>Chroma Viewer — collection <code>{html.escape(col.name)}</code></h1>
      <p class="muted">{col.count()} chunk(s) · store: {html.escape(str(config.CHROMA_DIR))}</p>
      <form method="get">
        <input type="text" name="q" placeholder="semantic search…" value="{html.escape(query or '')}">
        <button type="submit">Search</button>
        {'<a href="/">clear</a>' if query else ''}
      </form>"""

    rows = []
    if query:
        res = col.query(query_texts=[query], n_results=config.TOP_K)
        triples = zip(res["ids"][0], res["metadatas"][0], res["documents"][0], res["distances"][0])
        rows.append("<tr><th>rank</th><th>distance</th><th>id</th><th>source</th><th>text</th></tr>")
        for rank, (cid, meta, doc, dist) in enumerate(triples, 1):
            rows.append(
                f"<tr><td>{rank}</td><td class='dist'>{dist:.3f}</td>"
                f"<td><code>{html.escape(cid)}</code></td>"
                f"<td>{html.escape(str(meta.get('source','')))}</td>"
                f"<td>{html.escape(doc)}</td></tr>"
            )
        heading = f"<h2>Top {config.TOP_K} matches for “{html.escape(query)}”</h2>"
    else:
        data = col.get(include=["documents", "metadatas"])
        rows.append("<tr><th>id</th><th>source</th><th>chunk</th><th>chars</th><th>text</th></tr>")
        for cid, meta, doc in zip(data["ids"], data["metadatas"], data["documents"]):
            rows.append(
                f"<tr><td><code>{html.escape(cid)}</code></td>"
                f"<td>{html.escape(str(meta.get('source','')))}</td>"
                f"<td>{meta.get('chunk','')}</td><td>{len(doc)}</td>"
                f"<td>{html.escape(doc)}</td></tr>"
            )
        heading = "<h2>All chunks</h2>"

    return page(search_box + heading + "<table>" + "".join(rows) + "</table>")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if urlparse(self.path).path != "/":
            self.send_error(404)
            return
        q = parse_qs(urlparse(self.path).query).get("q", [None])[0]
        body = home(q)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # quiet console
        pass


if __name__ == "__main__":
    url = f"http://localhost:{PORT}"
    print(f"Chroma viewer running at {url}  (press Ctrl-C to stop)")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
