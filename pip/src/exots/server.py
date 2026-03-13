from __future__ import annotations

import argparse
import inspect
import json
import os
import signal
import socket
import sys
import threading
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from socketserver import ThreadingMixIn, UnixStreamServer
from typing import Any, Callable


class _RPCHandler(BaseHTTPRequestHandler):
    server: _UnixHTTPServer

    def _method_not_allowed(self) -> None:
        self.send_response(405)
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        self._method_not_allowed()

    def do_PUT(self) -> None:  # noqa: N802
        self._method_not_allowed()

    def do_DELETE(self) -> None:  # noqa: N802
        self._method_not_allowed()

    def do_HEAD(self) -> None:  # noqa: N802
        self._method_not_allowed()

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._method_not_allowed()

    def do_PATCH(self) -> None:  # noqa: N802
        self._method_not_allowed()

    def do_POST(self) -> None:
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            request = json.loads(body)
            result = self.server.rpc_handle(request)

            if result is not None:
                response_body = json.dumps(result).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(response_body)))
                self.end_headers()
                self.wfile.write(response_body)
            else:
                self.send_response(204)
                self.end_headers()
        except Exception:
            self.send_response(400)
            self.end_headers()

    def log_message(self, fmt: str, *args: Any) -> None:
        # Keep parity with Node server's silent request handling.
        return


class _UnixHTTPServer(ThreadingMixIn, UnixStreamServer):
    daemon_threads = True

    def __init__(self, socket_path: str, methods: dict[str, Callable[..., Any]]) -> None:
        self.methods = methods
        super().__init__(socket_path, _RPCHandler)

    def rpc_handle(self, request: dict[str, Any]) -> dict[str, Any] | None:
        request_id = request.get("id")
        method_name = request.get("method")
        params = request.get("params", [])

        if method_name not in self.methods:
            if request_id is None:
                return None
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": "Method not found"},
                "id": request_id,
            }

        try:
            fn = self.methods[method_name]
            result = fn(*params)
            if inspect.isawaitable(result):
                import asyncio

                result = asyncio.run(result)

            if request_id is None:
                return None
            return {
                "jsonrpc": "2.0",
                "result": result,
                "id": request_id,
            }
        except Exception as exc:
            if request_id is None:
                return None
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": str(exc)},
                "id": request_id,
            }


class Server:
    def __init__(self, methods: dict[str, Callable[..., Any]]) -> None:
        self._methods = methods
        self._http_server: _UnixHTTPServer | None = None
        self._socket_path: str | None = None
        self._pid_file: str | None = None
        self._is_closing = False

    def run(self, argv: list[str] | None = None) -> None:
        if argv is None:
            argv = sys.argv

        parser = argparse.ArgumentParser()
        parser.add_argument("--socket", default=os.environ.get("EXOTS_SOCKET"))
        parser.add_argument("--pid", default=os.environ.get("EXOTS_PID"))
        args = parser.parse_args(argv[1:])

        socket_path = args.socket
        if not socket_path:
            print("Socket path required via --socket or EXOTS_SOCKET", file=sys.stderr)
            sys.exit(1)

        try:
            self.listen(socket=socket_path, pid=args.pid)
        except Exception as exc:
            print(exc, file=sys.stderr)
            sys.exit(1)

    def listen(self, *, socket: str, pid: str | None = None) -> None:
        self._socket_path = socket
        self._pid_file = pid

        sock_path = Path(self._socket_path)
        if sock_path.exists():
            if self._is_socket_active(self._socket_path):
                raise RuntimeError(f"Socket {self._socket_path} in use")
            sock_path.unlink()

        self._http_server = _UnixHTTPServer(self._socket_path, self._methods)

        if self._pid_file:
            try:
                Path(self._pid_file).write_text(str(os.getpid()), encoding="utf-8")
            except OSError:
                pass

        signal.signal(signal.SIGINT, lambda *_: self._signal_stop())
        signal.signal(signal.SIGTERM, lambda *_: self._signal_stop())

        self._http_server.serve_forever()

    def _signal_stop(self) -> None:
        threading.Thread(target=self.stop, daemon=True).start()

    def stop(self) -> None:
        if self._is_closing:
            return
        self._is_closing = True

        if self._http_server is not None:
            self._http_server.shutdown()
            self._http_server.server_close()

        if self._socket_path and Path(self._socket_path).exists():
            try:
                Path(self._socket_path).unlink()
            except OSError:
                pass

        if self._pid_file and Path(self._pid_file).exists():
            try:
                Path(self._pid_file).unlink()
            except OSError:
                pass

    @staticmethod
    def _is_socket_active(path: str) -> bool:
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(path)
            sock.close()
            return True
        except (ConnectionRefusedError, FileNotFoundError, OSError):
            return False
