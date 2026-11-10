"""HTTP Server based on standard library BaseHTTPRequestHandler."""

import json
import subprocess
import sys
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from src.constants import (
    HEADER_ACCEPT,
    HEADER_CONTENT_TYPE,
    HEADER_LANGUAGE,
    LANG_EN,
    MEDIA_JSON,
    STATUS_NOT_ACCEPTABLE,
    STATUS_OK,
    STATUS_UNSUPPORTED_MEDIA,
)
from src.storage.base import BaseStorage


class ApiRequestHandler(BaseHTTPRequestHandler):
    """Custom request handler implementing REST API variant 2."""

    storage: BaseStorage
    test_mode: bool = False

    def _validate_headers(self) -> int | None:
        """Verifies required HTTP headers in correct order."""
        if self.command in ("POST", "PUT", "PATCH"):
            ctype = self.headers.get(HEADER_CONTENT_TYPE, "")
            if MEDIA_JSON not in ctype:
                return STATUS_UNSUPPORTED_MEDIA
        accept = self.headers.get(HEADER_ACCEPT, "")
        if MEDIA_JSON not in accept:
            return STATUS_NOT_ACCEPTABLE
        lang = self.headers.get(HEADER_LANGUAGE, "")
        if lang != LANG_EN:
            return STATUS_NOT_ACCEPTABLE
        return None

    def _send_json(self, status_code: int, data: dict | list) -> None:
        """Writes JSON response body to client stream."""
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", MEDIA_JSON)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body_json(self) -> dict:
        """Reads payload from request input stream."""
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        payload = self.rfile.read(content_length)
        return json.loads(payload.decode("utf-8"))

    def do_PUT(self) -> None:
        """Handles PUT API endpoints."""
        code = self._validate_headers()
        if code:
            self._send_json(code, {"error": "Invalid headers"})
            return

        parsed = urlparse(self.path)
        path_parts = parsed.path.strip("/").split("/")

        if len(path_parts) == 5 and path_parts[:4] == [
            "rest",
            "api",
            "v1.0",
            "session",
        ]:
            uid = int(path_parts[4])
            data = self._read_body_json()
            res = self.storage.session_submit(uid, data)
            self._send_json(STATUS_OK, res)
            return

        if len(path_parts) == 5 and path_parts[:4] == [
            "rest",
            "api",
            "v1.0",
            "instruction",
        ]:
            uid = int(path_parts[4])
            data = self._read_body_json()
            res = self.storage.instruction_submit(uid, data)
            self._execute_cli_task(uid, data)
            self._send_json(STATUS_OK, res)
            return

        self._send_json(404, {"error": "Not found"})

    def do_DELETE(self) -> None:
        """Handles DELETE API endpoints."""
        code = self._validate_headers()
        if code:
            self._send_json(code, {"error": "Invalid headers"})
            return

        parsed = urlparse(self.path)
        path_parts = parsed.path.strip("/").split("/")

        if len(path_parts) == 5 and path_parts[3] == "session":
            uid = int(path_parts[4])
            ok = self.storage.session_pop(uid)
            self._send_json(STATUS_OK, {"deleted": ok})
            return

        if len(path_parts) == 5 and path_parts[3] == "instruction":
            uid = int(path_parts[4])
            ok = self.storage.instruction_pop(uid)
            self._send_json(STATUS_OK, {"deleted": ok})
            return

        self._send_json(404, {"error": "Not found"})

    def do_GET(self) -> None:
        """Handles GET API endpoints."""
        code = self._validate_headers()
        if code:
            self._send_json(code, {"error": "Invalid headers"})
            return

        parsed = urlparse(self.path)
        query = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        path_parts = parsed.path.strip("/").split("/")

        if parsed.path == "/rest/api/v1.0/session/search":
            self._send_json(STATUS_OK, self.storage.session_search(query))
            return

        if parsed.path == "/rest/api/v1.0/report/search":
            self._send_json(STATUS_OK, self.storage.report_search())
            return

        if len(path_parts) == 5 and path_parts[3] == "instruction":
            session_id = int(path_parts[4])
            res = self.storage.instruction_search(session_id, query)
            self._send_json(STATUS_OK, res)
            return

        if len(path_parts) == 5 and path_parts[3] == "response":
            inst_id = int(path_parts[4])
            res = self.storage.response_search(inst_id, query)
            self._send_json(STATUS_OK, res)
            return

        self._send_json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        """Handles POST API endpoints."""
        code = self._validate_headers()
        if code:
            self._send_json(code, {"error": "Invalid headers"})
            return

        parsed = urlparse(self.path)
        body = self._read_body_json()

        if parsed.path == "/rest/api/v1.0/session/adjust":
            res = self.storage.session_adjust(body)
            self._send_json(STATUS_OK, res or {})
            return

        if parsed.path == "/rest/api/v1.0/instruction/adjust":
            res = self.storage.instruction_adjust(body)
            self._send_json(STATUS_OK, res or {})
            return

        self._send_json(404, {"error": "Not found"})

    def _execute_cli_task(self, uid: int, data: dict) -> None:
        """Executes CLI converter via subprocess or skips in test mode."""
        if self.test_mode:
            return
        payload = data.get("payload", "")
        if not payload:
            return
        cmd = [
            sys.executable,
            "-m",
            "src.cli",
            "-i",
            payload,
            "-o",
            f"{payload}.md",
        ]
        subprocess.run(cmd, capture_output=True, check=False)
