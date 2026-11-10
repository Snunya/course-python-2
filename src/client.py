"""HTTP API Client matching backend storage function names."""

from typing import Any
import requests
from src.constants import (
    HEADER_ACCEPT,
    HEADER_CONTENT_TYPE,
    HEADER_LANGUAGE,
    LANG_EN,
    MEDIA_JSON,
)


class ApiClient:
    """Client communicating with the BaseHTTPRequestHandler service."""

    def __init__(self, base_url: str):
        """Initializes client with host url."""
        self.base_url = base_url.rstrip("/")
        self.headers = {
            HEADER_CONTENT_TYPE: MEDIA_JSON,
            HEADER_ACCEPT: MEDIA_JSON,
            HEADER_LANGUAGE: LANG_EN,
        }

    def session_submit(self, uid: int, data: dict[str, Any]) -> dict[str, Any]:
        """Calls PUT /rest/api/v1.0/session/submit/:uid."""
        url = f"{self.base_url}/rest/api/v1.0/session/submit/{uid}"
        resp = requests.put(url, json=data, headers=self.headers, timeout=5)
        return resp.json()

    def session_pop(self, uid: int) -> bool:
        """Calls DELETE /rest/api/v1.0/session/pop/:uid."""
        url = f"{self.base_url}/rest/api/v1.0/session/pop/{uid}"
        resp = requests.delete(url, headers=self.headers, timeout=5)
        return resp.json().get("deleted", False)

    def session_search(self, filters: dict[str, Any]) -> list[dict[str, Any]]:
        """Calls GET /rest/api/v1.0/session/search."""
        url = f"{self.base_url}/rest/api/v1.0/session/search"
        resp = requests.get(
            url, params=filters, headers=self.headers, timeout=5
        )
        return resp.json()

    def session_adjust(self, data: dict[str, Any]) -> dict[str, Any] | None:
        """Calls POST /rest/api/v1.0/session/adjust."""
        url = f"{self.base_url}/rest/api/v1.0/session/adjust"
        resp = requests.post(url, json=data, headers=self.headers, timeout=5)
        return resp.json()

    def instruction_submit(
        self, uid: int, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Calls PUT /rest/api/v1.0/instruction/submit/:uid."""
        url = f"{self.base_url}/rest/api/v1.0/instruction/submit/{uid}"
        resp = requests.put(url, json=data, headers=self.headers, timeout=5)
        return resp.json()

    def instruction_pop(self, uid: int) -> bool:
        """Calls DELETE /rest/api/v1.0/instruction/pop/:uid."""
        url = f"{self.base_url}/rest/api/v1.0/instruction/pop/{uid}"
        resp = requests.delete(url, headers=self.headers, timeout=5)
        return resp.json().get("deleted", False)

    def instruction_search(
        self, session_id: int, filters: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Calls GET /rest/api/v1.0/instruction/search/:session."""
        url = f"{self.base_url}/rest/api/v1.0/instruction/search/{session_id}"
        resp = requests.get(
            url, params=filters, headers=self.headers, timeout=5
        )
        return resp.json()

    def instruction_adjust(
        self, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Calls POST /rest/api/v1.0/instruction/adjust."""
        url = f"{self.base_url}/rest/api/v1.0/instruction/adjust"
        resp = requests.post(url, json=data, headers=self.headers, timeout=5)
        return resp.json()

    def response_search(
        self, instruction_id: int, filters: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Calls GET /rest/api/v1.0/response/search/:instruction."""
        url = f"{self.base_url}/rest/api/v1.0/response/search/{instruction_id}"
        resp = requests.get(
            url, params=filters, headers=self.headers, timeout=5
        )
        return resp.json()

    def report_search(self) -> list[dict[str, Any]]:
        """Calls GET /rest/api/v1.0/report/search."""
        url = f"{self.base_url}/rest/api/v1.0/report/search"
        resp = requests.get(url, headers=self.headers, timeout=5)
        return resp.json()
