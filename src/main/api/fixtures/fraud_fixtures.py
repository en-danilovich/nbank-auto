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


@dataclass
class FraudMockServer:
    """Yielded by the fraud_check_mock_server fixture. Exposes the call log so
    tests can assert the backend did (or did not) reach out to the fraud service."""

    cfg: FraudMockConfig
    _calls: List[Dict[str, Any]] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def record(self, method: str, path: str, body: bytes, matched: bool) -> None:
        with self._lock:
            self._calls.append({"method": method, "path": path, "body": body, "matched": matched})

    @property
    def calls(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._calls)

    @property
    def call_count(self) -> int:
        with self._lock:
            return len(self._calls)


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


def _read_chunked_body(rfile) -> bytes:
    """Read an HTTP/1.1 chunked-transfer body. Spring's WebClient sends fraud-check
    payloads chunked with no Content-Length, so the simpler read(Content-Length) path
    yields an empty body."""
    body = b""
    while True:
        line = rfile.readline()
        if not line:
            break
        size_token = line.strip().split(b";", 1)[0]
        if not size_token:
            continue
        size = int(size_token, 16)
        if size == 0:
            rfile.readline()
            break
        body += rfile.read(size)
        rfile.readline()
    return body


def _build_handler(cfg: FraudMockConfig, server: "FraudMockServer"):
    pattern = re.compile(cfg.endpoint)
    body_bytes = json.dumps(cfg.response_body).encode("utf-8")

    class _Handler(BaseHTTPRequestHandler):
        def _respond(self, method: str, body: bytes):
            matched = bool(pattern.search(self.path))
            server.record(method=method, path=self.path, body=body, matched=matched)
            if not matched:
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
            body = b""
            try:
                if (self.headers.get("Transfer-Encoding") or "").lower() == "chunked":
                    body = _read_chunked_body(self.rfile)
                else:
                    length = int(self.headers.get("Content-Length") or 0)
                    if length:
                        body = self.rfile.read(length)
            except Exception:
                pass
            self._respond("POST", body)

        def do_GET(self):
            self._respond("GET", b"")

        def log_message(self, format, *args):
            logger.debug("FraudMock %s - %s", self.address_string(), format % args)

    return _Handler


@pytest.fixture(autouse=True, scope="function")
def fraud_check_mock_server(request: pytest.FixtureRequest):
    cfg = _load_fraud_mock_config(request)
    if cfg is None:
        yield
        return

    mock_server = FraudMockServer(cfg=cfg)
    handler_cls = _build_handler(cfg, mock_server)
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
        yield mock_server
    finally:
        for srv in servers:
            try:
                srv.shutdown()
                srv.server_close()
            except Exception as e:
                logger.warning("FraudMock: error during shutdown: %s", e)
        for t in threads:
            t.join(timeout=2)
