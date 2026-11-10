"""SQLite relational storage backend implemented with PonyORM."""

import time
from typing import Any
from pony.orm import (
    Database,
    Optional,
    PrimaryKey,
    Required,
    db_session,
    select,
)
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

    def __init__(self, db_path: str = ".test_orm.db"):
        """Initializes database binding and mapping."""
        self.db = Database()
        build_entities(self.db)
        self.db.bind(provider='sqlite', filename=db_path, create_db=True)
        self.db.generate_mapping(create_tables=True)

    @db_session
    def session_submit(self, uid: int, data: dict[str, Any]) -> dict[str, Any]:
        """Creates session row in SQLite."""
        session_cls = getattr(self.db, "Session")
        created = data.get("created", int(time.time()))
        existing = session_cls.get(uid=uid)
        if existing:
            existing.created = created
            return {"uid": existing.uid, "created": existing.created}
        item = session_cls(uid=uid, created=created)
        return {"uid": item.uid, "created": item.created}

    @db_session
    def session_pop(self, uid: int) -> bool:
        """Deletes session row."""
        item = getattr(self.db, "Session").get(uid=uid)
        if item:
            item.delete()
            return True
        return False

    @db_session
    def session_search(self, filters: dict[str, Any]) -> list[dict[str, Any]]:
        """Queries session rows."""
        session_cls = getattr(self.db, "Session")
        query = select(s for s in session_cls)
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
        item = getattr(self.db, "Session").get(uid=uid)
        if not item:
            return None
        if "created" in data:
            item.created = data["created"]
        return {"uid": item.uid, "created": item.created}

    @db_session
    def instruction_submit(
        self, uid: int, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Creates instruction entity and linked response."""
        inst_cls = getattr(self.db, "Instruction")
        resp_cls = getattr(self.db, "Response")
        created = data.get("created", int(time.time()))
        payload = data.get("payload", "")
        session = data.get("session", 0)
        description = data.get("description", "")
        tags = data.get("tags", "")
        existing = inst_cls.get(uid=uid)
        if existing:
            existing.created = created
            existing.payload = payload
            existing.session = session
            existing.description = description
            existing.tags = tags
        else:
            inst_cls(
                uid=uid,
                created=created,
                payload=payload,
                session=session,
                description=description,
                tags=tags,
            )
        if not resp_cls.get(uid=uid):
            resp_cls(
                uid=uid,
                created=created,
                output=f"{payload}.md",
                stage="done",
                error="",
                instruction=uid,
                cache_hit=1,
            )
        return {
            "uid": uid,
            "created": created,
            "payload": payload,
            "session": session,
            "description": description,
            "tags": tags,
        }

    @db_session
    def instruction_pop(self, uid: int) -> bool:
        """Removes instruction row."""
        item = getattr(self.db, "Instruction").get(uid=uid)
        if item:
            item.delete()
            return True
        return False

    @db_session
    def instruction_search(
        self, session_id: int, filters: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Finds instructions by session relation."""
        inst_cls = getattr(self.db, "Instruction")
        items = select(i for i in inst_cls if i.session == session_id)
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
        item = getattr(self.db, "Instruction").get(uid=uid)
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
        resp_cls = getattr(self.db, "Response")
        items = select(r for r in resp_cls if r.instruction == instruction_id)
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
        inst_cls = getattr(self.db, "Instruction")
        resp_cls = getattr(self.db, "Response")
        records = select(
            (i.description, r.cache_hit)
            for i in inst_cls
            for r in resp_cls
            if i.uid == r.instruction and r.created > cutoff and r.stage != ""
        )
        return [
            {"description": desc, "cache_hit": hit} for desc, hit in records
        ]
