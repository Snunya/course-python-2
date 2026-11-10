"""Model-based state machine tests for SQLite ORM layer."""

import os
import threading
import time
from http.server import HTTPServer
from hypothesis import settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, initialize, rule
from pony.orm import db_session
from src.client import ApiClient
from src.server import ApiRequestHandler
from src.storage.orm_storage import PonyOrmStorage


class OrmHandler(ApiRequestHandler):
    """Handler bound to PonyORM storage."""


class OrmServerManager:
    """Manages test server instance lifecycle for ORM tests."""

    server = None
    port = None
    storage = None
    db_file = None

    @classmethod
    def ensure_started(cls):
        """Starts server once on OS assigned free port with file db."""
        if cls.server is None:
            cls.db_file = os.path.abspath(".test_orm.db")
            if os.path.exists(cls.db_file):
                try:
                    os.remove(cls.db_file)
                except OSError:
                    pass
            cls.storage = PonyOrmStorage(cls.db_file)
            OrmHandler.storage = cls.storage
            OrmHandler.test_mode = True
            cls.server = HTTPServer(("127.0.0.1", 0), OrmHandler)
            cls.port = cls.server.server_address[1]
            thread = threading.Thread(
                target=cls.server.serve_forever, daemon=True
            )
            thread.start()


class OrmModelTest(RuleBasedStateMachine):
    """Hypothesis state machine testing PonyORM SQLite layer."""

    @initialize()
    def setup_system(self):
        """Configures server with PonyOrm backend."""
        OrmServerManager.ensure_started()
        self.storage = OrmServerManager.storage
        self._reset_database()

        proto = "http"
        host = "127.0.0.1"
        self.client = ApiClient(f"{proto}://{host}:{OrmServerManager.port}")
        self.sessions = set()
        self.instructions = set()

    def _reset_database(self):
        """Purges existing rows between test iterations."""
        with db_session:
            self.storage.db.execute("DELETE FROM response")
            self.storage.db.execute("DELETE FROM instruction")
            self.storage.db.execute("DELETE FROM session")

    @rule(uid=st.integers(min_value=1, max_value=200))
    def create_session(self, uid):
        """Rule testing session submit with ORM."""
        payload = {"created": int(time.time())}
        resp = self.client.session_submit(uid, payload)
        assert resp["uid"] == uid
        self.sessions.add(uid)

    @rule(uid=st.integers(min_value=1, max_value=200))
    def delete_session(self, uid):
        """Rule testing session delete with ORM."""
        deleted = self.client.session_pop(uid)
        if uid in self.sessions:
            assert deleted is True
            self.sessions.remove(uid)

    @rule()
    def search_sessions(self):
        """Rule testing session query search."""
        items = self.client.session_search({})
        assert isinstance(items, list)

    @rule(uid=st.integers(min_value=1, max_value=200))
    def adjust_session(self, uid):
        """Rule testing session adjust POST."""
        payload = {"uid": uid, "created": int(time.time())}
        res = self.client.session_adjust(payload)
        assert isinstance(res, (dict, type(None)))

    @rule(
        uid=st.integers(min_value=1, max_value=200),
        session_id=st.integers(min_value=1, max_value=200),
    )
    def create_instruction(self, uid, session_id):
        """Rule testing instruction submit PUT."""
        data = {
            "created": int(time.time()),
            "payload": "sample.docx",
            "session": session_id,
            "description": "text conversion",
            "tags": "doc,md",
        }
        res = self.client.instruction_submit(uid, data)
        assert res["uid"] == uid
        self.instructions.add(uid)

    @rule(uid=st.integers(min_value=1, max_value=200))
    def delete_instruction(self, uid):
        """Rule testing instruction pop DELETE."""
        deleted = self.client.instruction_pop(uid)
        if uid in self.instructions:
            assert deleted is True
            self.instructions.remove(uid)

    @rule(session_id=st.integers(min_value=1, max_value=200))
    def search_instructions(self, session_id):
        """Rule testing instruction search GET."""
        items = self.client.instruction_search(session_id, {})
        assert isinstance(items, list)

    @rule(uid=st.integers(min_value=1, max_value=200))
    def adjust_instruction(self, uid):
        """Rule testing instruction adjust POST."""
        payload = {"uid": uid, "description": "updated description"}
        res = self.client.instruction_adjust(payload)
        assert isinstance(res, (dict, type(None)))

    @rule(instruction_id=st.integers(min_value=1, max_value=200))
    def search_responses(self, instruction_id):
        """Rule testing response search GET."""
        items = self.client.response_search(instruction_id, {})
        assert isinstance(items, list)

    @rule()
    def query_report(self):
        """Rule checking relational join query."""
        report = self.client.report_search()
        assert isinstance(report, list)


TestOrmApp = OrmModelTest.TestCase
TestOrmApp.settings = settings(max_examples=30, deadline=None)
