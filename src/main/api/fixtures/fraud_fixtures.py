import json
import logging
import re
import socket
import threading
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, List, Optional

import pytest


logger = logging.getLogger(__name__)


@dataclass
class FraudMockConfig:
    port: int = 8080
    endpoint: str = r"/.*"
    response_body: Dict[str, Any] = field(default_factory=dict)


def _load_fraud_mock_config(request: pytest.FixtureRequest) -> Optional[FraudMockConfig]:
    marker = request.node.get_closest_marker("fraud_check_mock")
    if marker is None:
        return None

    kwargs = dict(marker.kwargs or {})
    port = int(kwargs.pop("port", 8080))
    endpoint = str(kwargs.pop("endpoint", r"/.*"))
    return FraudMockConfig(port=port, endpoint=endpoint, response_body=kwargs)


class _ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True

    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        super().server_bind()


def _build_handler(cfg: FraudMockConfig):
    pattern = re.compile(cfg.endpoint)
    body_bytes = json.dumps(cfg.response_body).encode("utf-8")

    class _Handler(BaseHTTPRequestHandler):
        def _respond(self):
            if not pattern.search(self.path):
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error":"path not matched"}')
                return

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body_bytes)))
            self.end_headers()
            self.wfile.write(body_bytes)

        def do_POST(self):
            try:
                length = int(self.headers.get("Content-Length") or 0)
                if length:
                    self.rfile.read(length)
            except Exception:
                pass
            self._respond()

        def do_GET(self):
            self._respond()

        def log_message(self, format, *args):
            logger.debug("FraudMock %s - %s", self.address_string(), format % args)

    return _Handler


@pytest.fixture(autouse=True, scope="function")
def fraud_check_mock_server(request: pytest.FixtureRequest):
    cfg = _load_fraud_mock_config(request)
    if cfg is None:
        yield
        return

    handler_cls = _build_handler(cfg)
    servers: List[_ReusableHTTPServer] = []
    threads: List[threading.Thread] = []

    ports_to_try = []
    for p in (cfg.port, 8080, 8089):
        if p not in ports_to_try:
            ports_to_try.append(p)

    for p in ports_to_try:
        try:
            srv = _ReusableHTTPServer(("0.0.0.0", int(p)), handler_cls)
        except OSError as e:
            logger.warning("FraudMock: cannot bind port %s: %s", p, e)
            continue
        t = threading.Thread(
            target=srv.serve_forever,
            name=f"fraud-mock-{p}",
            daemon=True,
        )
        t.start()
        servers.append(srv)
        threads.append(t)
        logger.info("FraudMock listening on port %s", p)

    if not servers:
        raise RuntimeError(
            f"FraudMock: failed to bind any of the ports {ports_to_try}"
        )

    try:
        yield cfg
    finally:
        for srv in servers:
            try:
                srv.shutdown()
                srv.server_close()
            except Exception as e:
                logger.warning("FraudMock: error during shutdown: %s", e)
        for t in threads:
            t.join(timeout=2)
