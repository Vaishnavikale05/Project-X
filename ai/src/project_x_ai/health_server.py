"""Minimal service liveness endpoint; this process performs no video analysis."""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/health":
            self.send_error(404)
            return
        body = json.dumps({"service": "project-x-ai", "status": "ok"}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        # Keep default request logging minimal and avoid logging query strings.
        super().log_message("%s", self.path.split("?", maxsplit=1)[0])


def main() -> None:
    port = int(os.environ.get("AI_SERVICE_PORT", "8010"))
    ThreadingHTTPServer(("0.0.0.0", port), HealthHandler).serve_forever()


if __name__ == "__main__":
    main()
