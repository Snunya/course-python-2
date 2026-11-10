"""Model-based state machine tests for SQLite ORM layer."""

import threading
import time
from http.server import HTTPServer
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, initialize, rule
from src.client import ApiClient
from src.server import ApiRequestHandler
from src.storage.orm_storage import PonyOrmStorage


class OrmModelTest(RuleBasedStateMachine):
    """Hypothesis state machine testing PonyORM SQLite layer."""

    @initialize()
    def setup_system(self):
        """Configures server with PonyOrm backend."""
        self.storage = PonyOrmStorage(":memory:")
        ApiRequestHandler.storage = self.storage
        ApiRequestHandler.test_mode = True

        self.server = HTTPServer(("127.0.0.1", 8992), ApiRequestHandler)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()

        self.client = ApiClient("[http://127.0.0.1:8992](http://127.0.0.1:8992)")
        self.sessions = set()

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
    def query_report(self):
        """Rule checking relational join query."""
        report = self.client.report_search()
        assert isinstance(report, list)

    def teardown(self):
        """Terminates test HTTP server."""
        self.server.shutdown()
        self.server.server_close()


TestOrmApp = OrmModelTest.TestCase
