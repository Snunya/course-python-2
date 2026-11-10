"""JSON file-system based storage implementation for Stage 2."""

import json
import os
import time
from typing import Any
from src.constants import REPORT_TIME_WINDOW_SEC
from src.storage.base import BaseStorage


class FileSystemStorage(BaseStorage):
    """File storage persisting entities as JSON records on disk."""

    def __init__(self, directory: str = ".db_store"):
        """Initializes storage directories."""
        self.root = directory
        os.makedirs(self.root, exist_ok=True)
        for folder in ("sessions", "instructions", "responses"):
            os.makedirs(os.path.join(self.root, folder), exist_ok=True)

    def _file_path(self, folder: str, uid: int) -> str:
        """Calculates path to entity record file."""
        return os.path.join(self.root, folder, f"{uid}.json")

    def session_submit(self, uid: int, data: dict[str, Any]) -> dict[str, Any]:
        """Saves a session to disk."""
        record = {
            "uid": uid,
            "created": data.get("created", int(time.time())),
        }
        with open(self._file_path("sessions", uid), "w", encoding="utf-8") as f:
            json.dump(record, f)
        return record

    def session_pop(self, uid: int) -> bool:
        """Deletes session file."""
        path = self._file_path("sessions", uid)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def session_search(self, filters: dict[str, Any]) -> list[dict[str, Any]]:
        """Queries stored session documents."""
        folder = os.path.join(self.root, "sessions")
        results = []
        for filename in os.listdir(folder):
            if filename.endswith(".json"):
                with open(os.path.join(folder, filename), "r") as f:
                    item = json.load(f)
                    if all(item.get(k) == v for k, v in filters.items()):
                        results.append(item)
        return results

    def session_adjust(self, data: dict[str, Any]) -> dict[str, Any] | None:
        """Modifies existing session attributes."""
        uid = data.get("uid")
        if uid is None:
            return None
        path = self._file_path("sessions", uid)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            record = json.load(f)
        record.update(data)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(record, f)
        return record

    def instruction_submit(
        self, uid: int, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Saves instruction to disk."""
        record = {
            "uid": uid,
            "created": data.get("created", int(time.time())),
            "payload": data.get("payload", ""),
            "session": data.get("session", 0),
            "description": data.get("description", ""),
            "tags": data.get("tags", ""),
        }
        with open(
            self._file_path("instructions", uid), "w", encoding="utf-8"
        ) as f:
            json.dump(record, f)
        return record

    def instruction_pop(self, uid: int) -> bool:
        """Removes instruction from disk."""
        path = self._file_path("instructions", uid)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def instruction_search(
        self, session_id: int, filters: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Searches instructions by session."""
        folder = os.path.join(self.root, "instructions")
        results = []
        for filename in os.listdir(folder):
            if filename.endswith(".json"):
                with open(os.path.join(folder, filename), "r") as f:
                    item = json.load(f)
                    if item.get("session") == session_id and all(
                        item.get(k) == v for k, v in filters.items()
                    ):
                        results.append(item)
        return results

    def instruction_adjust(
        self, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Updates instruction attributes."""
        uid = data.get("uid")
        if uid is None:
            return None
        path = self._file_path("instructions", uid)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            record = json.load(f)
        record.update(data)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(record, f)
        return record

    def response_search(
        self, instruction_id: int, filters: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Finds responses by linked instruction."""
        folder = os.path.join(self.root, "responses")
        results = []
        for filename in os.listdir(folder):
            if filename.endswith(".json"):
                with open(os.path.join(folder, filename), "r") as f:
                    item = json.load(f)
                    if item.get("instruction") == instruction_id and all(
                        item.get(k) == v for k, v in filters.items()
                    ):
                        results.append(item)
        return results

    def report_search(self) -> list[dict[str, Any]]:
        """Generates report based on Relational Formula 2."""
        now = int(time.time())
        cutoff = now - REPORT_TIME_WINDOW_SEC
        responses_folder = os.path.join(self.root, "responses")
        instructions_folder = os.path.join(self.root, "instructions")

        valid_responses = []
        for r_name in os.listdir(responses_folder):
            if r_name.endswith(".json"):
                with open(os.path.join(responses_folder, r_name), "r") as f:
                    resp = json.load(f)
                    if resp.get("created", 0) > cutoff and resp.get("stage"):
                        valid_responses.append(resp)

        report = []
        for resp in valid_responses:
            inst_path = os.path.join(
                instructions_folder, f"{resp.get('instruction')}.json"
            )
            if os.path.exists(inst_path):
                with open(inst_path, "r", encoding="utf-8") as f:
                    inst = json.load(f)
                    report.append(
                        {
                            "description": inst.get("description", ""),
                            "cache_hit": resp.get("cache_hit", 0),
                        }
                    )
        return report
