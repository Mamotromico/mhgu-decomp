#!/usr/bin/env python3
"""Tests for the model client: pure helpers, plus the HTTP client against a fake server.

No real model and no network beyond loopback. Run with::

    python3 tests/loop/test_model.py
"""

from __future__ import annotations

import http.server
import json
import os
import socket
import sys
import tempfile
import threading
import time
import unittest
import urllib.request
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "loop"))

from model import (
    SYSTEM_PROMPT,
    HttpModel,
    ModelError,
    build_payload,
    chat_endpoint,
    from_config,
    parse_response,
    proxy_handler,
    strip_fences,
)


@contextmanager
def fake_server(response: dict, status: int = 200, extra_headers: dict | None = None):
    """Run a one-shot-style JSON endpoint on loopback; yield (base_url, captured)."""
    captured: dict = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            captured["body"] = json.loads(self.rfile.read(n))
            captured["headers"] = dict(self.headers)
            captured["path"] = self.path
            body = json.dumps(response).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            for k, v in (extra_headers or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):  # silence
            pass

    srv = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{srv.server_address[1]}", captured
    finally:
        srv.shutdown()
        srv.server_close()


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class ChatEndpointTests(unittest.TestCase):
    def test_bare_base(self):
        self.assertEqual(chat_endpoint("http://h:8080"),
                         "http://h:8080/v1/chat/completions")

    def test_trailing_slash_and_v1(self):
        self.assertEqual(chat_endpoint("http://h:8080/"), "http://h:8080/v1/chat/completions")
        self.assertEqual(chat_endpoint("http://h:8080/v1"),
                         "http://h:8080/v1/chat/completions")

    def test_full_endpoint_passthrough(self):
        self.assertEqual(chat_endpoint("http://h/v1/chat/completions"),
                         "http://h/v1/chat/completions")


class PayloadTests(unittest.TestCase):
    def test_system_and_temperature(self):
        p = build_payload("m", "hi", "sys", 0.0, None)
        self.assertEqual([m["role"] for m in p["messages"]], ["system", "user"])
        self.assertEqual(p["temperature"], 0.0)
        self.assertFalse(p["stream"])
        self.assertNotIn("max_tokens", p)

    def test_max_tokens_included_when_set(self):
        self.assertEqual(build_payload("m", "hi", None, 0.0, 256)["max_tokens"], 256)


class ParseResponseTests(unittest.TestCase):
    def test_text_and_usage(self):
        c = parse_response({"choices": [{"message": {"content": "ok"}}], "model": "m",
                            "usage": {"prompt_tokens": 5, "completion_tokens": 7}}, 1.5)
        self.assertEqual((c.text, c.model, c.prompt_tokens, c.completion_tokens),
                         ("ok", "m", 5, 7))
        self.assertEqual(c.latency_s, 1.5)

    def test_bad_shape_raises(self):
        with self.assertRaises(ModelError):
            parse_response({"nope": True}, 0.0)


class StripFencesTests(unittest.TestCase):
    def test_fenced_with_language(self):
        self.assertEqual(strip_fences("```cpp\nint f() {}\n```"), "int f() {}")

    def test_fenced_without_language(self):
        self.assertEqual(strip_fences("```\nint f() {}\n```"), "int f() {}")

    def test_no_fence_is_trimmed(self):
        self.assertEqual(strip_fences("  int f() {}  "), "int f() {}")

    def test_prose_around_fence(self):
        self.assertEqual(strip_fences("Here:\n```\nx\n```\nhope that helps"),
                         "x")


class HttpModelTests(unittest.TestCase):
    def response(self, content="int f() {}"):
        return {"choices": [{"message": {"content": content}}], "model": "local-model",
                "usage": {"prompt_tokens": 3, "completion_tokens": 9}}

    def test_success_path_and_request(self):
        with fake_server(self.response()) as (base, captured):
            m = HttpModel(base, "local-model", api_key="secret")
            c = m.complete("write f")
        self.assertEqual(c.text, "int f() {}")
        self.assertEqual(c.completion_tokens, 9)
        self.assertEqual(captured["path"], "/v1/chat/completions")
        self.assertEqual(captured["body"]["messages"][0]["role"], "system")
        self.assertEqual(captured["body"]["messages"][0]["content"], SYSTEM_PROMPT)
        self.assertEqual(captured["body"]["messages"][-1]["content"], "write f")
        self.assertEqual(captured["headers"].get("Authorization"), "Bearer secret")

    def test_no_api_key_means_no_auth_header(self):
        with fake_server(self.response()) as (base, captured):
            HttpModel(base, "m", api_key=None).complete("x")
        self.assertIsNone(captured["headers"].get("Authorization"))

    def test_http_error_raises_model_error(self):
        with fake_server({"error": "boom"}, status=500) as (base, _):
            with self.assertRaises(ModelError):
                HttpModel(base, "m").complete("x")

    def test_connection_refused_raises_model_error(self):
        m = HttpModel(f"http://127.0.0.1:{free_port()}", "m", timeout_s=2.0)
        with self.assertRaises(ModelError):
            m.complete("x")

    def test_explicit_endpoint_used_verbatim(self):
        m = HttpModel(endpoint="http://h:9/custom/chat/completions", model="m")
        self.assertEqual(m.endpoint, "http://h:9/custom/chat/completions")

    def test_missing_url_raises(self):
        with self.assertRaises(ValueError):
            HttpModel(model="m")

    def test_redirect_is_refused(self):
        with fake_server({"choices": []}, status=302,
                         extra_headers={"Location": "http://evil.invalid/next"}) as (base, _):
            with self.assertRaises(ModelError):
                HttpModel(base, "m").complete("x")

    def test_401_without_key_suggests_env(self):
        with fake_server({"error": "unauthorized"}, status=401) as (base, _):
            with self.assertRaises(ModelError) as ctx:
                HttpModel(base, "m", api_key=None).complete("x")
        self.assertIn("requires a key", str(ctx.exception))

    def test_read_timeout_raises_model_error(self):
        class SlowHandler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                time.sleep(1.0)  # longer than the client's timeout
                body = b"{}"
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *a):
                pass

        srv = http.server.HTTPServer(("127.0.0.1", 0), SlowHandler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            model = HttpModel(f"http://127.0.0.1:{srv.server_address[1]}", "m", timeout_s=0.2)
            with self.assertRaises(ModelError) as ctx:
                model.complete("x")
        finally:
            srv.shutdown()
            srv.server_close()
        self.assertIn("timed out", str(ctx.exception))

    def test_non_json_raises(self):
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                body = b"not json"
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *a):
                pass

        srv = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            with self.assertRaises(ModelError):
                HttpModel(f"http://127.0.0.1:{srv.server_address[1]}", "m").complete("x")
        finally:
            srv.shutdown()
            srv.server_close()


class ProxyHandlerTests(unittest.TestCase):
    def test_none_is_an_explicit_empty_handler(self):
        h = proxy_handler("none")
        self.assertIsInstance(h, urllib.request.ProxyHandler)
        self.assertEqual(h.proxies, {})

    def test_env_defers_to_stock_behaviour(self):
        self.assertIsNone(proxy_handler("env"))

    def test_url_applies_to_both_schemes(self):
        h = proxy_handler("http://p:3128")
        self.assertEqual(h.proxies, {"http": "http://p:3128", "https": "http://p:3128"})

    def test_scheme_less_is_rejected(self):
        with self.assertRaises(ValueError):
            proxy_handler("p:3128")


class OpenerRoutingTests(unittest.TestCase):
    def handler_names(self, model_: HttpModel) -> list[str]:
        return [type(h).__name__ for h in model_._opener.handlers]

    def test_proxy_none_ignores_the_environment(self):
        with mock.patch.dict(os.environ, {"http_proxy": "http://p:1"}):
            names = self.handler_names(HttpModel("http://h:9", "m", proxy="none"))
        self.assertNotIn("ProxyHandler", names)

    def test_proxy_env_honors_the_environment(self):
        with mock.patch.dict(os.environ, {"http_proxy": "http://p:1"}):
            names = self.handler_names(HttpModel("http://h:9", "m", proxy="env"))
        self.assertIn("ProxyHandler", names)

    def test_explicit_proxy_url_is_used(self):
        names = self.handler_names(HttpModel("http://h:9", "m", proxy="http://p:3128"))
        self.assertIn("ProxyHandler", names)


class FromConfigTests(unittest.TestCase):
    def write(self, cfg: dict) -> Path:
        path = Path(tempfile.mkdtemp()) / "model.json"
        path.write_text(json.dumps(cfg))
        return path

    def test_endpoint_wins_over_base_url(self):
        path = self.write({"base_url": "http://x",
                           "endpoint": "http://y/paas/v4/chat/completions"})
        self.assertEqual(from_config(path).endpoint, "http://y/paas/v4/chat/completions")

    def test_base_url_is_completed(self):
        self.assertEqual(from_config(self.write({"base_url": "http://h:8080"})).endpoint,
                         "http://h:8080/v1/chat/completions")

    def test_override_endpoint_without_config_file(self):
        missing = Path(tempfile.mkdtemp()) / "nope.json"
        m = from_config(missing, override_endpoint="http://z/v1/chat/completions")
        self.assertEqual(m.endpoint, "http://z/v1/chat/completions")

    def test_timeout_from_config_and_override(self):
        path = self.write({"base_url": "http://h:8080", "timeout_s": 45})
        self.assertEqual(from_config(path).timeout_s, 45.0)
        self.assertEqual(from_config(path, override_timeout=3.0).timeout_s, 3.0)


if __name__ == "__main__":
    unittest.main()
