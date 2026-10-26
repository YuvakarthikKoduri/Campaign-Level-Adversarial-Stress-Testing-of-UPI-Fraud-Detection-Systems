"""Localhost-only HTTP API. Never accepts a shell command or executable path."""
import argparse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.metadata
import io
import json
import mimetypes
import os
from pathlib import Path
import platform
import re
import secrets
import subprocess
from urllib.parse import parse_qs, urlsplit
import xml.etree.ElementTree as ET

from .records import Catalog, LIMITATION, csv_export, load, require
from .runner import Jobs, build

REPO = Path(__file__).resolve().parents[1]
STATIC = Path(__file__).resolve().parent/"static"


def test_counts(path):
    suites = list(ET.parse(path).getroot().iter("testsuite"))
    counts = {k: sum(int(s.get(k, 0)) for s in suites)
              for k in ("tests", "failures", "errors", "skipped")}
    counts["passed"] = counts["tests"]-counts["failures"]-counts["errors"]-counts["skipped"]
    counts["deselected"] = 0
    counts["timestamp"] = suites[0].get("timestamp") if suites else None
    return counts


class Application:
    def __init__(self, repo=REPO, retained=None, state=None):
        self.repo = Path(repo).resolve()
        bundled = self.repo/".local/retained"
        self.retained = Path(retained or (bundled if bundled.exists() else self.repo.parent/"retained")).resolve()
        self.state = Path(state or self.repo/".local/dashboard-state").resolve()
        self.state.mkdir(parents=True, exist_ok=True)
        self.catalog = Catalog(self.retained, self.repo, self.state)
        self.jobs = Jobs(self.repo, self.state, self.catalog)
        self.token = secrets.token_urlsafe(32)

    def bootstrap(self):
        def git(*args):
            r = subprocess.run(["git", *args], cwd=self.repo, timeout=5,
                env=dict(PATH=os.defpath, GIT_OPTIONAL_LOCKS="0"),
                capture_output=True, text=True)
            return r.stdout.strip() if r.returncode == 0 else "Unavailable"
        packages = {}
        for name in ("numpy", "pandas", "scikit-learn", "xgboost", "pytest"):
            try:
                packages[name] = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:
                packages[name] = "Unavailable"
        prior = []
        for name in ("prior-regression.xml", "prior-rl.xml"):
            path = self.retained/name
            if path.exists():
                prior.append(dict(name=name, counts=test_counts(path),
                                  source=self.catalog.register(path), retained=True))
        return dict(csrf=self.token, project="UPI Fraud Stress Lab",
            branch=git("branch", "--show-current"), commit=git("rev-parse", "HEAD"),
            runs=self.catalog.list(), jobs=self.jobs.list(), prior_tests=prior,
            environment=dict(python=platform.python_version(), packages=packages,
                status="Packages available" if "Unavailable" not in packages.values() else "Missing packages",
                note="Package presence, not a fresh installation or compatibility audit."),
            limitation=LIMITATION, gate_c="HOLD")


class Handler(BaseHTTPRequestHandler):
    server_version = "ResearchWorkstation/1"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    @property
    def app(self):
        return self.server.app

    def security(self, write=False):
        port = self.server.server_port
        allowed = {f"127.0.0.1:{port}", f"localhost:{port}"}
        require(self.headers.get("Host") in allowed, "Host is not an approved loopback origin")
        origin = self.headers.get("Origin")
        require(origin is None or origin in {"http://"+h for h in allowed}, "Cross-origin request rejected")
        if write:
            require(self.headers.get("X-Research-Token") == self.app.token, "Session token required")
            require(origin in {"http://"+h for h in allowed}, "Same-origin request required")

    def send(self, payload, status=200, content_type="application/json", filename=None):
        body = (json.dumps(payload, allow_nan=False).encode() if content_type == "application/json"
                else payload if isinstance(payload, bytes) else payload.encode())
        self.send_response(status)
        self.send_header("Content-Type", content_type + ("" if content_type.startswith("image/") else "; charset=utf-8"))
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; img-src 'self' blob: data:; font-src 'self'; "
            "connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        try:
            self.security()
            parsed = urlsplit(self.path)
            q = {k: v[0] for k, v in parse_qs(parsed.query).items()}
            filters = {k: q.get(k, "") for k in ("detector", "strategy", "family", "block", "outcome")}
            path = parsed.path
            if path == "/api/bootstrap":
                return self.send(self.app.bootstrap())
            if path == "/api/runs":
                return self.send(self.app.catalog.list())
            if path == "/api/summary":
                return self.send(self.app.catalog.view(q.get("run"), filters))
            if path == "/api/campaigns":
                offset = int(q.get("offset", 0))
                require(0 <= offset <= 1_000_000, "Invalid pagination offset")
                return self.send(self.app.catalog.campaigns(q.get("run"), filters, offset))
            if path == "/api/campaign":
                data = self.app.catalog.dataset(q.get("run"))
                index = int(q.get("index", -1))
                require(0 <= index < len(data["records"]), "Campaign index unavailable")
                return self.send(dict(record=data["records"][index], config=data["config"],
                    manifest=self.app.catalog.register(data["descriptor"]["path"]/"manifest.json")))
            if path == "/api/models":
                return self.send(self.app.catalog.models(q.get("run")))
            if path == "/api/datasets":
                return self.send(self.app.catalog.datasets(q.get("run")))
            if path == "/api/jobs":
                return self.send(dict(jobs=self.app.jobs.list(), active=self.app.jobs.active,
                    events=list(reversed(self.app.jobs.events[-100:]))))
            if path == "/api/logs":
                return self.send(self.app.jobs.logs(q.get("job"), max(0, int(q.get("cursor", 0)))))
            if path == "/api/log-download":
                identifier = q.get("job")
                require(identifier in self.app.jobs.jobs, "Unknown job")
                p = self.app.state/"jobs"/(identifier+".jsonl")
                return self.send(p.read_bytes() if p.exists() else b"", content_type="application/x-ndjson",
                                 filename="execution-log.jsonl")
            if path == "/api/reports":
                paths = sorted((self.app.retained.parent/"reports").glob("*.md"))
                paths += sorted((self.app.repo/"docs").glob("*.md"))
                paths += sorted((self.app.repo/"docs/history").glob("*.md"))
                guide = self.app.repo/"docs/DASHBOARD_GUIDE.md"
                if guide.exists():
                    paths.append(guide)
                return self.send([self.app.catalog.register(p) for p in paths])
            if path == "/api/export":
                view = self.app.catalog.view(q.get("run"), filters)
                self.app.jobs.event("report_exported", run=q.get("run"), format=q.get("format", "csv"))
                if q.get("format") == "markdown":
                    lines = [f"# Research snapshot: {view['run']}", "",
                        "Generated UTC: "+datetime.now(timezone.utc).isoformat(),
                        "\nFilters: "+json.dumps(filters), "\n"+LIMITATION,
                        "\nGross transfer is simulated source debit, not actual victim loss.",
                        "\nImported software verification is not scientific validation.",
                        "\n```csv", csv_export(view["groups"]), "```",
                        "\n## Benign controls", json.dumps(view["benign"], indent=2),
                        "\n## Evidence", json.dumps(view["sources"], indent=2), "\nGate C: HOLD"]
                    return self.send("\n".join(lines), content_type="text/markdown", filename="research-snapshot.md")
                return self.send(csv_export(view["groups"]), content_type="text/csv", filename="filtered-results.csv")
            if path.startswith("/api/files/"):
                identifier = path.rsplit("/", 1)[-1]
                require(identifier in self.app.catalog.files, "Artifact not registered")
                p = self.app.catalog.files[identifier]
                # Files are opaque IDs, never browser-supplied paths. Recheck before read.
                require(not p.is_symlink(), "Artifact symlink rejected")
                suffix = p.suffix.lower()
                require(suffix in (".md", ".json", ".jsonl", ".csv", ".xml", ".log", ".txt", ".svg",
                                   ".stdout", ".stderr"), "Artifact type is not served")
                require(p.stat().st_size <= 40_000_000, "Artifact is too large for browser download")
                return self.send(p.read_bytes(), content_type="application/octet-stream", filename=p.name)
            require(path in ("/", "/app.js", "/style.css") or re.fullmatch(
                r"/vendor/[A-Za-z0-9_.-]+", path), "Unknown route")
            p = STATIC/("index.html" if path == "/" else path[1:])
            require(p.is_file(), "Static asset unavailable")
            return self.send(p.read_bytes(), content_type=mimetypes.guess_type(p)[0] or "application/octet-stream")
        except (ValueError, KeyError, TypeError, OSError) as exc:
            return self.send(dict(error=str(exc)), status=400)
        except Exception:
            return self.send(dict(error="Unexpected server error; inspect local server logs"), status=500)

    def do_POST(self):
        try:
            self.security(write=True)
            require(self.headers.get("Content-Type", "").split(";")[0] == "application/json",
                    "JSON content type required")
            size = int(self.headers.get("Content-Length", 0))
            require(0 < size <= 16384, "Request body exceeds limit")
            data = json.loads(self.rfile.read(size))
            if self.path == "/api/preview":
                return self.send(build(data, self.app.repo, self.app.state, self.app.catalog))
            if self.path == "/api/jobs":
                return self.send(self.app.jobs.submit(data), status=201)
            if self.path == "/api/cancel":
                require(isinstance(data, dict), "Expected JSON object")
                return self.send(self.app.jobs.cancel(data.get("job")))
            raise ValueError("Unknown write route")
        except (ValueError, KeyError, TypeError, OSError) as exc:
            return self.send(dict(error=str(exc)), status=400)
        except Exception:
            return self.send(dict(error="Unexpected server error"), status=500)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--retained", type=Path, default=None)
    parser.add_argument("--state", type=Path, default=None)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("Use a nonprivileged port from 1024 to 65535")
    if os.name != "posix":
        parser.error("Safe process-group execution currently requires Linux/macOS or WSL2")
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    server.daemon_threads = True
    server.app = Application(retained=args.retained, state=args.state)
    print(f"UPI research workstation: http://127.0.0.1:{args.port}", flush=True)
    print("Loopback only. Synthetic evidence. Gate C HOLD.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        if server.app.jobs.active:
            server.app.jobs.cancel(server.app.jobs.active)
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
