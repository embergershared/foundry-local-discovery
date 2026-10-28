# Getting started

## Prerequisites

- Python 3.13, matching the repository's version file.
- A running local OpenAI-compatible model server. Note its actual endpoint URL (including
	`/v1`) and loaded model ID. This example does not install a server or download models.
- Access to the approved package feed; see [supply-chain.md](supply-chain.md).

## Install

**PowerShell (workstation)**, from your clone's root:

```powershell
Set-Location <path-to-clone>
py -3.13 -m venv .venv
.venv\Scripts\python -m pip install --index-url https://packagefeedproxy.microsoft.io/pypi/simple/ --require-hashes -r requirements-dev.lock
.venv\Scripts\python -m pip install --no-deps --no-build-isolation -e .
```

The first install provides locked runtime, test, lint, and build dependencies. The second
installs this project's editable package and `local-chat` command without fetching additional
dependencies. Activation is optional: all commands below use the virtual environment directly.
Select `.venv` with **Python: Select Interpreter** in VS Code too.

## Run

**PowerShell (workstation)**, from the clone's root; replace the sample port and model ID
with the values reported by your local server:

```powershell
Set-Location <path-to-clone>
.venv\Scripts\local-chat --base-url http://localhost:12345/v1 --model '<model-id>' --prompt "Explain local inference in three bullets."
# Equivalent module entry point:
.venv\Scripts\python -m local_chat --base-url http://localhost:12345/v1 --model '<model-id>' --prompt "Hello"
```

Alternatively set `LOCAL_CHAT_BASE_URL` and `LOCAL_CHAT_MODEL` in your shell. Explicit CLI
options take precedence. No environment file is automatically loaded. The demo sends the
placeholder API key `not-needed`; it is intended for a local server that needs no authentication,
not an authenticated cloud endpoint. Prompts can be visible in shell history: use only synthetic,
non-sensitive text in this demo.

Use `--help` without a server to see all options. Model text streams to stdout; errors go to
stderr. Exit codes: `0` success, `1` request failure, `2` invalid arguments, `130` cancellation.
Missing endpoint/model settings fail before any request. Importing the package sends nothing.

## Verify and build

**PowerShell (workstation)**, from the clone's root:

```powershell
Set-Location <path-to-clone>
.venv\Scripts\python -m pytest
.venv\Scripts\python -m ruff check .
.venv\Scripts\python -m ruff format --check .
.venv\Scripts\python -m pip check
.venv\Scripts\python -m pip wheel --no-deps --no-build-isolation --wheel-dir artifacts .
```

Tests run offline: unit tests stub the SDK, and a subprocess smoke test uses the real SDK
against an ephemeral loopback streaming server. They cover configuration, streaming, resource
cleanup, and error exits; they do not prove that a particular local model is installed or healthy.
There is no separately configured type checker.

## Refresh dependency locks

Edit [requirements.in](../requirements.in) or [requirements-dev.in](../requirements-dev.in),
then run the existing lock generator. Never edit generated locks by hand.

**PowerShell (workstation)**, from the clone's root:

```powershell
Set-Location <path-to-clone>
$env:PIP_INDEX_URL = 'https://packagefeedproxy.microsoft.io/pypi/simple/'
.venv\Scripts\python scripts/lock_requirements.py
.venv\Scripts\python -m pip install --index-url https://packagefeedproxy.microsoft.io/pypi/simple/ --require-hashes -r requirements-dev.lock
```

The generator verifies release age, yank status, and hashes; it needs PyPI metadata access
as well as the approved download feed. See [supply-chain.md](supply-chain.md) for details.
