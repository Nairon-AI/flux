#!/usr/bin/env python3
"""Unit tests for flux-auth.py (device-flow auth)."""

import argparse
import http.server
import importlib
import io
import json
import os
import stat
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(__file__))
flux_auth: Any = importlib.import_module("flux-auth")


class TestAuthFile(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.auth_file = Path(self.tmpdir) / "universe-auth.json"
        self.orig_auth_file = flux_auth.AUTH_FILE
        flux_auth.AUTH_FILE = self.auth_file

    def tearDown(self):
        flux_auth.AUTH_FILE = self.orig_auth_file
        if self.auth_file.exists():
            self.auth_file.unlink()
        os.rmdir(self.tmpdir)

    def test_save_and_load(self):
        flux_auth.save_auth({
            "accessToken": "test-token",
            "tokenType": "Bearer",
            "user": {"handle": "alice", "email": "alice@example.com"},
        })
        data = flux_auth.load_auth()
        self.assertIsNotNone(data)
        self.assertEqual(data["accessToken"], "test-token")
        self.assertEqual(data["user"]["handle"], "alice")
        self.assertEqual(data["schemaVersion"], flux_auth.SCHEMA_VERSION)

    def test_permissions_0600(self):
        flux_auth.save_auth({"accessToken": "t", "user": {}})
        mode = self.auth_file.stat().st_mode
        self.assertEqual(stat.S_IMODE(mode), 0o600)

    def test_atomic_write_no_temp_left(self):
        flux_auth.save_auth({"accessToken": "t", "user": {}})
        files = [p.name for p in Path(self.tmpdir).iterdir()]
        self.assertEqual(files, ["universe-auth.json"])

    def test_load_corrupt_returns_none(self):
        self.auth_file.write_text("{{bad")
        self.assertIsNone(flux_auth.load_auth())

    def test_schema_mismatch_returns_none(self):
        self.auth_file.write_text(json.dumps({"schemaVersion": 999, "accessToken": "x"}))
        self.assertIsNone(flux_auth.load_auth())

    def test_delete_idempotent(self):
        flux_auth.delete_auth()
        flux_auth.delete_auth()


class TestLogoutAndStatus(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.auth_file = Path(self.tmpdir) / "universe-auth.json"
        self.orig_auth_file = flux_auth.AUTH_FILE
        flux_auth.AUTH_FILE = self.auth_file

    def tearDown(self):
        flux_auth.AUTH_FILE = self.orig_auth_file
        if self.auth_file.exists():
            self.auth_file.unlink()
        os.rmdir(self.tmpdir)

    def test_logout_connected(self):
        flux_auth.save_auth({"accessToken": "tok", "user": {"handle": "alice"}})
        result = flux_auth.cmd_logout(argparse.Namespace())
        self.assertEqual(result, 0)
        self.assertFalse(self.auth_file.exists())

    def test_logout_disconnected(self):
        result = flux_auth.cmd_logout(argparse.Namespace())
        self.assertEqual(result, 0)

    def test_status_connected_text(self):
        flux_auth.save_auth({"accessToken": "tok", "user": {"handle": "alice"}})
        out = io.StringIO()
        with patch("sys.stdout", out):
            result = flux_auth.cmd_status(argparse.Namespace(format="text"))
        self.assertEqual(result, 0)
        self.assertIn("Connected to Universe as @alice", out.getvalue())

    def test_status_disconnected_text(self):
        out = io.StringIO()
        with patch("sys.stdout", out):
            result = flux_auth.cmd_status(argparse.Namespace(format="text"))
        self.assertEqual(result, 0)
        self.assertIn("Not connected", out.getvalue())

    def test_status_json(self):
        flux_auth.save_auth({"accessToken": "tok", "user": {"handle": "alice"}})
        out = io.StringIO()
        with patch("sys.stdout", out):
            result = flux_auth.cmd_status(argparse.Namespace(format="json"))
        self.assertEqual(result, 0)
        data = json.loads(out.getvalue())
        self.assertTrue(data["connected"])
        self.assertEqual(data["user"]["handle"], "alice")
        self.assertNotIn("accessToken", data)

    def test_status_corrupt_treated_as_disconnected(self):
        self.auth_file.write_text("bad-json")
        out = io.StringIO()
        with patch("sys.stdout", out):
            result = flux_auth.cmd_status(argparse.Namespace(format="text"))
        self.assertEqual(result, 0)
        self.assertIn("Not connected", out.getvalue())


class MockHandler(http.server.BaseHTTPRequestHandler):
    mock_responses: dict[str, tuple[int, dict[str, Any]]] = {}
    mock_poll_queue: list[tuple[int, dict[str, Any]]] = []

    def _send_json(self, status: int, body: dict[str, Any]):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else b"{}"

        if self.path == "/api/flux/device/poll" and self.mock_poll_queue:
            status, resp_body = self.mock_poll_queue.pop(0)
            self._send_json(status, resp_body)
            return

        key = f"POST {self.path}"
        if key in self.mock_responses:
            status, resp_body = self.mock_responses[key]
            self._send_json(status, resp_body)
            return

        self._send_json(404, {"error": "not found", "body": body.decode("utf-8")})

    def log_message(self, format, *args):
        pass


class TestDeviceLogin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.HTTPServer(("127.0.0.1", 0), MockHandler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.auth_file = Path(self.tmpdir) / "universe-auth.json"
        self.orig_auth_file = flux_auth.AUTH_FILE
        self.orig_api_url = os.environ.get("FLUX_UNIVERSE_API_URL")
        flux_auth.AUTH_FILE = self.auth_file
        os.environ["FLUX_UNIVERSE_API_URL"] = f"http://127.0.0.1:{self.port}"
        MockHandler.mock_responses = {}
        MockHandler.mock_poll_queue = []

    def tearDown(self):
        flux_auth.AUTH_FILE = self.orig_auth_file
        if self.orig_api_url is None:
            os.environ.pop("FLUX_UNIVERSE_API_URL", None)
        else:
            os.environ["FLUX_UNIVERSE_API_URL"] = self.orig_api_url
        if self.auth_file.exists():
            self.auth_file.unlink()
        os.rmdir(self.tmpdir)

    def _mock_device_start(self):
        MockHandler.mock_responses["POST /api/flux/device/start"] = (
            200,
            {
                "deviceCode": "secret-device-code",
                "userCode": "ABCD-EFGH",
                "verificationUri": "https://universe.naironai.com/auth/device",
                "verificationUriComplete": "https://universe.naironai.com/auth/device?user_code=ABCD-EFGH",
                "expiresIn": 60,
                "interval": 1,
            },
        )

    def test_login_success_pending_then_approved(self):
        self._mock_device_start()
        MockHandler.mock_poll_queue = [
            (202, {"status": "pending"}),
            (200, {"status": "approved", "accessToken": "flux_tok_1", "tokenType": "Bearer", "username": "luka"}),
        ]

        with patch("time.sleep", return_value=None), patch("webbrowser.open", return_value=True):
            result = flux_auth.cmd_login(argparse.Namespace())

        self.assertEqual(result, 0)
        auth = flux_auth.load_auth()
        self.assertIsNotNone(auth)
        self.assertEqual(auth["accessToken"], "flux_tok_1")
        self.assertEqual(auth["user"]["handle"], "luka")

    def test_login_denied(self):
        self._mock_device_start()
        MockHandler.mock_poll_queue = [(400, {"status": "denied"})]

        with patch("time.sleep", return_value=None):
            result = flux_auth.cmd_login(argparse.Namespace())

        self.assertEqual(result, 1)
        self.assertIsNone(flux_auth.load_auth())

    def test_login_expired(self):
        self._mock_device_start()
        MockHandler.mock_poll_queue = [(400, {"status": "expired"})]

        with patch("time.sleep", return_value=None):
            result = flux_auth.cmd_login(argparse.Namespace())

        self.assertEqual(result, 1)

    def test_browser_open_failure_is_non_fatal(self):
        self._mock_device_start()
        MockHandler.mock_poll_queue = [(200, {"status": "approved", "accessToken": "flux_tok_2", "username": "alice"})]

        with patch("time.sleep", return_value=None), patch("webbrowser.open", side_effect=RuntimeError("no browser")):
            result = flux_auth.cmd_login(argparse.Namespace())

        self.assertEqual(result, 0)

    def test_reauth_replaces_existing_token(self):
        flux_auth.save_auth({"accessToken": "old", "user": {"handle": "olduser"}})
        self._mock_device_start()
        MockHandler.mock_poll_queue = [(200, {"status": "approved", "accessToken": "new", "username": "newuser"})]

        with patch("time.sleep", return_value=None):
            result = flux_auth.cmd_login(argparse.Namespace())

        self.assertEqual(result, 0)
        auth = flux_auth.load_auth()
        self.assertEqual(auth["accessToken"], "new")
        self.assertEqual(auth["user"]["handle"], "newuser")

    def test_login_does_not_prompt_for_credentials(self):
        self._mock_device_start()
        MockHandler.mock_poll_queue = [(200, {"status": "approved", "accessToken": "tok", "username": "u"})]

        with patch("time.sleep", return_value=None), patch("builtins.input", side_effect=AssertionError("input should not be called")):
            result = flux_auth.cmd_login(argparse.Namespace())

        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
