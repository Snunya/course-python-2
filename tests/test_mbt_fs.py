"""Model-based state machine tests for FS storage layer."""

import shutil
import threading
import time
from http.server import HTTPServer
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, initialize, rule
from src.client import ApiClient
from src.server import ApiRequestHandler
from src.storage.fs_storage import FileSystemStorage


class ServerModelTest(RuleBasedStateMachine):
    """Hypothesis state machine verifying HTTP API against client model."""

    @initialize()
    def setup_system(self):
        """Spins up test HTTP server and client."""
        self.db_dir = ".test_db_fs"
        shutil.rmtree(self.db_dir, ignore_errors=True)
        self.storage = FileSystemStorage(self.db_dir)
        ApiRequestHandler.storage = self.storage
        ApiRequestHandler.test_mode = True

        self.server = HTTPServer(("127.0.0.1", 8991), ApiRequestHandler)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()

        self.client = ApiClient("[http://127.0.0.1:8991](http://127.0.0.1:8991)")
        self.sessions = set()

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
    def query_report(self):
        """Rule verifying report generator endpoint."""
        report = self.client.report_search()
        assert isinstance(report, list)

    def teardown(self):
        """Terminates test HTTP server."""
        self.server.shutdown()
        self.server.server_close()
        shutil.rmtree(self.db_dir, ignore_errors=True)


TestFsApp = ServerModelTest.TestCase
