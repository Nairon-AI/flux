#!/usr/bin/env python3
"""Unit tests for flux-score Universe sync behavior."""

import http.server
import importlib
import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(__file__))
flux_score = importlib.import_module("flux-score")


class SyncMockHandler(http.server.BaseHTTPRequestHandler):
    next_status = 200
    last_path = ""
    last_auth = ""
    last_body = {}

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(content_length) if content_length else b"{}"
        SyncMockHandler.last_path = self.path
        SyncMockHandler.last_auth = self.headers.get("Authorization", "")
        SyncMockHandler.last_body = json.loads(raw.decode("utf-8"))

        self.send_response(SyncMockHandler.next_status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": SyncMockHandler.next_status == 200}).encode("utf-8"))

    def log_message(self, format, *args):
        pass


class TestFluxScoreSync(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.HTTPServer(("127.0.0.1", 0), SyncMockHandler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.home = Path(self.tmpdir)
        (self.home / ".flux").mkdir(parents=True, exist_ok=True)

        self.orig_api_url = os.environ.get("FLUX_UNIVERSE_API_URL")
        os.environ["FLUX_UNIVERSE_API_URL"] = f"http://127.0.0.1:{self.port}"
        SyncMockHandler.last_path = ""
        SyncMockHandler.last_auth = ""
        SyncMockHandler.last_body = {}

    def tearDown(self):
        if self.orig_api_url is None:
            os.environ.pop("FLUX_UNIVERSE_API_URL", None)
        else:
            os.environ["FLUX_UNIVERSE_API_URL"] = self.orig_api_url
        for p in (self.home / ".flux").glob("*"):
            p.unlink()
        (self.home / ".flux").rmdir()
        self.home.rmdir()

    def _score(self):
        return flux_score.FluxScore(
            period_start="all-time",
            period_end="now",
            sessions_analyzed=3,
            interview_depth=80,
            pushback_ratio=75,
            prompt_quality=82,
            iteration_efficiency=70,
            tool_breadth=90,
            score=80,
            grade="A",
            strengths=[],
            growth_areas=[],
            raw_metrics={"tools_used": ["Read", "Bash"], "estimated_tokens": 1234},
        )

    def test_sync_skips_when_no_auth_file(self):
        with patch("pathlib.Path.home", return_value=self.home):
            self.assertFalse(flux_score.sync_to_universe(self._score()))

    def test_sync_posts_flux_endpoint_with_contract_payload(self):
        auth = {
            "schemaVersion": 1,
            "accessToken": "flux_token_abc",
            "tokenType": "Bearer",
            "user": {"handle": "luka"},
        }
        (self.home / ".flux" / "universe-auth.json").write_text(json.dumps(auth))
        SyncMockHandler.next_status = 200

        with patch("pathlib.Path.home", return_value=self.home):
            ok = flux_score.sync_to_universe(self._score())

        self.assertTrue(ok)
        self.assertEqual(SyncMockHandler.last_path, "/api/flux/sync")
        self.assertEqual(SyncMockHandler.last_auth, "Bearer flux_token_abc")
        self.assertEqual(SyncMockHandler.last_body["sessionsCount"], 3)
        self.assertEqual(SyncMockHandler.last_body["totalTokens"], 1234)
        self.assertEqual(SyncMockHandler.last_body["toolsUsed"], ["Bash", "Read"])
        self.assertIn("sentAt", SyncMockHandler.last_body)
        self.assertEqual(SyncMockHandler.last_body["sourceVersion"], "0.1.0")

    def test_sync_returns_false_on_unauthorized(self):
        auth = {
            "schemaVersion": 1,
            "accessToken": "flux_bad_token",
            "tokenType": "Bearer",
            "user": {"handle": "luka"},
        }
        (self.home / ".flux" / "universe-auth.json").write_text(json.dumps(auth))
        SyncMockHandler.next_status = 401

        with patch("pathlib.Path.home", return_value=self.home):
            ok = flux_score.sync_to_universe(self._score())

        self.assertFalse(ok)

    def test_sync_skips_when_another_sync_lock_exists(self):
        auth = {
            "schemaVersion": 1,
            "accessToken": "flux_token_abc",
            "tokenType": "Bearer",
            "user": {"handle": "luka"},
        }
        (self.home / ".flux" / "universe-auth.json").write_text(json.dumps(auth))
        (self.home / ".flux" / ".universe-sync.lock").write_text("locked")
        SyncMockHandler.next_status = 200

        with patch("pathlib.Path.home", return_value=self.home):
            ok = flux_score.sync_to_universe(self._score())

        self.assertFalse(ok)
        self.assertEqual(SyncMockHandler.last_path, "")


if __name__ == "__main__":
    unittest.main()
