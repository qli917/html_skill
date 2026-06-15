#!/usr/bin/env python3
"""Receive manually picked selector JSON and merge it into the Codex cache."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


CACHE_PATH = Path.home() / ".codex" / "html_main_selectors.json"


def load_cache() -> dict:
    if not CACHE_PATH.exists():
        return {"version": 1, "rules": []}
    return json.loads(CACHE_PATH.read_text(encoding="utf-8"))


def save_rule(rule: dict) -> None:
    required = ["kind", "netloc", "selector"]
    missing = [key for key in required if not rule.get(key)]
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")
    if rule.get("kind") == "url" and rule.get("classes"):
        rule["scope"] = "domain_class"
        rule["class_selector"] = "." + ".".join(rule["classes"])
    cache = load_cache()
    rules = cache.setdefault("rules", [])
    rules[:] = [
        item
        for item in rules
        if not (
            item.get("kind") == rule.get("kind")
            and item.get("netloc") == rule.get("netloc")
            and (
                (
                    rule.get("scope") == "domain_class"
                    and item.get("scope") == "domain_class"
                )
                or item.get("path_prefix") == rule.get("path_prefix")
            )
        )
    ]
    rules.append(rule)
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_cors()
        self.end_headers()

    def do_POST(self) -> None:
        if self.path != "/save":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            save_rule(payload)
        except Exception as exc:
            self.send_response(400)
            self.send_cors()
            self.end_headers()
            self.wfile.write(str(exc).encode("utf-8"))
            return
        self.send_response(200)
        self.send_cors()
        self.end_headers()
        self.wfile.write(f"saved to {CACHE_PATH}\n".encode("utf-8"))

    def send_cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "content-type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")

    def log_message(self, fmt: str, *args) -> None:
        print(fmt % args, flush=True)


def main() -> int:
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print(f"selector receiver listening on http://127.0.0.1:8765, cache={CACHE_PATH}", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
