"""Offline CLI and streaming tests: no model download or running server required."""

import json
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from openai import OpenAIError

from local_chat import local_chat

BASE_URL = "http://localhost:12345/v1"
ARGS = ["--base-url", BASE_URL, "--model", "test-model"]


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    monkeypatch.delenv("LOCAL_CHAT_BASE_URL", raising=False)
    monkeypatch.delenv("LOCAL_CHAT_MODEL", raising=False)


def test_environment_defaults_and_cli_precedence(monkeypatch):
    monkeypatch.setenv("LOCAL_CHAT_BASE_URL", BASE_URL)
    monkeypatch.setenv("LOCAL_CHAT_MODEL", "env-model")
    assert local_chat.parse_args([]).model == "env-model"
    assert local_chat.parse_args(ARGS).model == "test-model"
    assert local_chat.parse_args([]).base_url == BASE_URL


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["--base-url", BASE_URL],
        ["--model", "test-model"],
        ["--base-url", "not-a-url", "--model", "test-model"],
        ["--base-url", "http://localhost:invalid/v1", "--model", "test-model"],
        ["--base-url", "http://user:secret@localhost/v1", "--model", "test-model"],
        [*ARGS, "--prompt", " "],
        [*ARGS, "--model", " "],
    ],
)
def test_invalid_config_fails_before_client_creation(argv, monkeypatch):
    client = MagicMock()
    monkeypatch.setattr(local_chat, "OpenAI", client)
    with pytest.raises(SystemExit) as exc:
        local_chat.main(argv)
    assert exc.value.code == 2
    client.assert_not_called()


def test_help_needs_no_endpoint(capsys):
    with pytest.raises(SystemExit) as exc:
        local_chat.main(["--help"])
    assert exc.value.code == 0
    assert "--base-url" in capsys.readouterr().out


def test_streams_content_and_closes_resources(monkeypatch, capsys):
    factory = MagicMock()
    monkeypatch.setattr(local_chat, "OpenAI", factory)
    client = factory.return_value.__enter__.return_value
    response = client.chat.completions.create.return_value
    response.__enter__.return_value = [
        SimpleNamespace(choices=[]),
        SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=None))]),
        SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="Hello"))]),
        SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=" world"))]),
    ]
    assert local_chat.main([*ARGS, "--prompt", "Say hello"]) == 0
    assert capsys.readouterr().out == "Hello world\n"
    factory.assert_called_once_with(base_url=BASE_URL, api_key="not-needed")
    client.chat.completions.create.assert_called_once_with(
        model="test-model", messages=[{"role": "user", "content": "Say hello"}], stream=True
    )
    response.__exit__.assert_called_once()
    factory.return_value.__exit__.assert_called_once()


@pytest.mark.parametrize("error, expected", [(OpenAIError("test"), 1), (KeyboardInterrupt(), 130)])
def test_request_failure_and_cancellation(monkeypatch, caplog, error, expected):
    factory = MagicMock(side_effect=error)
    monkeypatch.setattr(local_chat, "OpenAI", factory)
    with caplog.at_level("INFO"):
        assert local_chat.main(ARGS) == expected
    assert "Chat" in caplog.text


def test_module_streams_through_real_sdk():
    """Exercise the installed module and SDK against an ephemeral loopback SSE server."""
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802 - standard-library HTTP handler hook
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append((self.path, body))
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            chunk = {"choices": [{"index": 0, "delta": {"content": "Local smoke test"}}]}
            self.wfile.write(f"data: {json.dumps(chunk)}\n\ndata: [DONE]\n\n".encode())

        def log_message(self, fmt, *args):
            pass  # Keep the synthetic test server quiet.

    with HTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "local_chat",
                    "--base-url",
                    f"http://127.0.0.1:{server.server_port}/v1",
                    "--model",
                    "test-model",
                    "--prompt",
                    "Hello",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
        finally:
            server.shutdown()
            thread.join(timeout=5)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "Local smoke test\n"
    assert requests == [
        (
            "/v1/chat/completions",
            {
                "model": "test-model",
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": True,
            },
        )
    ]
