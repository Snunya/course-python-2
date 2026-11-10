"""Model-based state machine tests for FS storage layer."""

import os
import shutil
import threading
import time
from http.server import HTTPServer
from hypothesis import settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, initialize, rule
from src.client import ApiClient
from src.server import ApiRequestHandler
from src.storage.fs_storage import FileSystemStorage


class FsHandler(ApiRequestHandler):
    """Handler bound to filesystem storage."""


class FsServerManager:
    """Manages test server instance lifecycle."""

    server = None
    port = None
    storage = None

    @classmethod
    def ensure_started(cls):
        """Starts server once on OS assigned free port."""
        if cls.server is None:
            db_dir = os.path.abspath(".test_db_fs")
            shutil.rmtree(db_dir, ignore_errors=True)
            cls.storage = FileSystemStorage(db_dir)
            FsHandler.storage = cls.storage
            FsHandler.test_mode = True

            cls.server = HTTPServer(("127.0.0.1", 0), FsHandler)
            cls.port = cls.server.server_address[1]
            thread = threading.Thread(
                target=cls.server.serve_forever, daemon=True
            )
            thread.start()


class ServerModelTest(RuleBasedStateMachine):
    """Hypothesis state machine verifying HTTP API against client model."""

    @initialize()
    def setup_system(self):
        """Prepares test client and storage."""
        FsServerManager.ensure_started()
        self.storage = FsServerManager.storage
        self._reset_storage()

        proto = "http"
        host = "127.0.0.1"
        self.client = ApiClient(f"{proto}://{host}:{FsServerManager.port}")
        self.sessions = set()
        self.instructions = set()

    def _reset_storage(self):
        """Purges stored JSON records between test iterations."""
        for folder in ("sessions", "instructions", "responses"):
            target = os.path.join(self.storage.root, folder)
            if os.path.exists(target):
                for fname in os.listdir(target):
                    if fname.endswith(".json"):
                        os.remove(os.path.join(target, fname))

    @rule(uid=st.integers(min_value=1, max_value=200))
    def create_session(self, uid):
        """Rule generating session submit requests."""
        payload = {"created": int(time.time())}
        resp = self.client.session_submit(uid, payload)
        assert resp["uid"] == uid
        self.sessions.add(uid)

    @rule(uid=st.integers(min_value=1, max_value=200))
    def delete_session(self, uid):
        """Rule testing session deletion."""
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
        """Rule verifying report generator endpoint."""
        report = self.client.report_search()
        assert isinstance(report, list)


TestFsApp = ServerModelTest.TestCase
TestFsApp.settings = settings(max_examples=30, deadline=None)
