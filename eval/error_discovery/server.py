"""Error discovery review server (Python stdlib only, local machine only).

    python eval/error_discovery/server.py [--port 8790]

Serves app.html and keeps every file in eval/error_discovery/error_discovery_data/:
records (built), samples, annotations (the reviewer's notes), graph, patterns (the failure-mode taxonomy)
and suggestions (agent proposals the reviewer accepts or dismisses).
"""
import json
import os
import sys
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "error_discovery_data")
LOCK = threading.Lock()
DEFAULTS = {
    "records.json": [],
    "samples.json": {"ids": [], "batches": []},
    "annotations.json": {"annotations": [], "reviewed": {}},
    "graph.json": {"points": []},
    "patterns.json": {"modes": [], "updated_at": None},
    "suggestions.json": {"suggestions": []},
}


def read(name):
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        return json.loads(json.dumps(DEFAULTS[name]))
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def write(name, obj):
    p = os.path.join(DATA, name)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, p)


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, code, body, kind):
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_json(self, obj, code=200):
        self.send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def payload(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        route = urlparse(self.path).path
        if route in ("/", "/index.html"):
            with open(os.path.join(HERE, "app.html"), "rb") as f:
                return self.send(200, f.read(), "text/html; charset=utf-8")
        with LOCK:
            if route == "/api/samples":
                s = read("samples.json")
                recs = {r["id"]: r for r in read("records.json")}
                return self.send_json({**s, "records": [recs[i] for i in s["ids"] if i in recs], "total": len(recs)})
            files = {"/api/annotations": "annotations.json", "/api/graph": "graph.json",
                     "/api/patterns": "patterns.json", "/api/suggestions": "suggestions.json"}
            if route in files:
                return self.send_json(read(files[route]))
        self.send_json({"error": "not found"}, 404)

    def do_POST(self):
        route = urlparse(self.path).path
        try:
            data = self.payload()
        except ValueError:
            return self.send_json({"error": "invalid JSON"}, 400)
        with LOCK:
            if route == "/api/samples":
                s = read("samples.json")
                known = {r["id"] for r in read("records.json")}
                new = [i for i in data.get("ids", []) if i in known and i not in s["ids"]]
                if new:
                    s["ids"] += new
                    s["batches"].append({"at": now(), "reason": data.get("reason", ""), "ids": new})
                    write("samples.json", s)
                return self.send_json({"added": new})
            if route == "/api/annotations":
                write("annotations.json", {"annotations": data.get("annotations", []), "reviewed": data.get("reviewed", {})})
                return self.send_json({"ok": True})
            if route == "/api/patterns":
                data["updated_at"] = now()
                write("patterns.json", data)
                return self.send_json({"ok": True})
            if route == "/api/suggestions":
                cur = read("suggestions.json")
                by_id = {x["id"]: x for x in cur["suggestions"]}
                for x in data.get("suggestions", []):
                    by_id[x["id"]] = {**by_id.get(x["id"], {}), **x}
                cur["suggestions"] = list(by_id.values())
                write("suggestions.json", cur)
                return self.send_json({"ok": True, "count": len(cur["suggestions"])})
        self.send_json({"error": "not found"}, 404)


if __name__ == "__main__":
    port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 8790
    os.makedirs(DATA, exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Error discovery app: http://127.0.0.1:{port}", flush=True)
    server.serve_forever()
