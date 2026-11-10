"""SQLite relational storage backend implemented with PonyORM."""

import time
from typing import Any
from pony.orm import Database, Optional, PrimaryKey, Required, db_session, select
from src.constants import REPORT_TIME_WINDOW_SEC
from src.storage.base import BaseStorage


def build_entities(db: Database) -> None:
    """Defines relational entities for PonyORM."""

    class Session(db.Entity):
        _table_ = "session"
        uid = PrimaryKey(int, auto=False)
        created = Required(int)

    class Instruction(db.Entity):
        _table_ = "instruction"
        uid = PrimaryKey(int, auto=False)
        created = Required(int)
        payload = Required(str)
        session = Required(int)
        description = Optional(str, default="")
        tags = Optional(str, default="")

    class Response(db.Entity):
        _table_ = "response"
        uid = PrimaryKey(int, auto=False)
        created = Required(int)
        output = Optional(str, default="")
        stage = Required(str)
        error = Optional(str, default="")
        instruction = Required(int)
        cache_hit = Required(int, default=0)


class PonyOrmStorage(BaseStorage):
    """PonyORM SQLite implementation of the data layer."""

    def __init__(self, db_path: str = ":memory:"):
        """Initializes database binding and mapping."""
        self.db = Database()
        build_entities(self.db)
        if db_path == ":memory:":
            self.db.bind(provider="sqlite", filename=":memory:", create_db=True)
        else:
            self.db.bind(provider="sqlite", filename=db_path, create_db=True)
        self.db.generate_mapping(create_tables=True)

    @db_session
    def session_submit(self, uid: int, data: dict[str, Any]) -> dict[str, Any]:
        """Creates session row in SQLite."""
        session_cls = self.db.Session
        created = data.get("created", int(time.time()))
        item = session_cls(uid=uid, created=created)
        return {"uid": item.uid, "created": item.created}

    @db_session
    def session_pop(self, uid: int) -> bool:
        """Deletes session row."""
        item = self.db.Session.get(uid=uid)
        if item:
            item.delete()
            return True
        return False

    @db_session
    def session_search(self, filters: dict[str, Any]) -> list[dict[str, Any]]:
        """Queries session rows."""
        query = select(s for s in self.db.Session)
        results = []
        for s in query:
            d = {"uid": s.uid, "created": s.created}
            if all(d.get(k) == v for k, v in filters.items()):
                results.append(d)
        return results

    @db_session
    def session_adjust(self, data: dict[str, Any]) -> dict[str, Any] | None:
        """Adjusts session attributes."""
        uid = data.get("uid")
        if uid is None:
            return None
        item = self.db.Session.get(uid=uid)
        if not item:
            return None
        if "created" in data:
            item.created = data["created"]
        return {"uid": item.uid, "created": item.created}

    @db_session
    def instruction_submit(
        self, uid: int, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Creates instruction entity."""
        inst = self.db.Instruction(
            uid=uid,
            created=data.get("created", int(time.time())),
            payload=data.get("payload", ""),
            session=data.get("session", 0),
            description=data.get("description", ""),
            tags=data.get("tags", ""),
        )
        return {
            "uid": inst.uid,
            "created": inst.created,
            "payload": inst.payload,
            "session": inst.session,
            "description": inst.description,
            "tags": inst.tags,
        }

    @db_session
    def instruction_pop(self, uid: int) -> bool:
        """Removes instruction row."""
        item = self.db.Instruction.get(uid=uid)
        if item:
            item.delete()
            return True
        return False

    @db_session
    def instruction_search(
        self, session_id: int, filters: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Finds instructions by session relation."""
        items = select(
            i for i in self.db.Instruction if i.session == session_id
        )
        out = []
        for i in items:
            d = {
                "uid": i.uid,
                "created": i.created,
                "payload": i.payload,
                "session": i.session,
                "description": i.description,
                "tags": i.tags,
            }
            if all(d.get(k) == v for k, v in filters.items()):
                out.append(d)
        return out

    @db_session
    def instruction_adjust(
        self, data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Updates instruction attributes."""
        uid = data.get("uid")
        if uid is None:
            return None
        item = self.db.Instruction.get(uid=uid)
        if not item:
            return None
        for key in ("payload", "description", "tags"):
            if key in data:
                setattr(item, key, data[key])
        return {
            "uid": item.uid,
            "created": item.created,
            "payload": item.payload,
            "session": item.session,
            "description": item.description,
            "tags": item.tags,
        }

    @db_session
    def response_search(
        self, instruction_id: int, filters: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Finds responses linked to instruction."""
        items = select(
            r for r in self.db.Response if r.instruction == instruction_id
        )
        out = []
        for r in items:
            d = {
                "uid": r.uid,
                "created": r.created,
                "output": r.output,
                "stage": r.stage,
                "error": r.error,
                "instruction": r.instruction,
                "cache_hit": r.cache_hit,
            }
            if all(d.get(k) == v for k, v in filters.items()):
                out.append(d)
        return out

    @db_session
    def report_search(self) -> list[dict[str, Any]]:
        """Evaluates relational query formula 2 using SQL join."""
        cutoff = int(time.time()) - REPORT_TIME_WINDOW_SEC
        records = select(
            (i.description, r.cache_hit)
            for i in self.db.Instruction
            for r in self.db.Response
            if i.uid == r.instruction and r.created > cutoff and r.stage != ""
        )
        return [
            {"description": desc, "cache_hit": hit} for desc, hit in records
        ]
