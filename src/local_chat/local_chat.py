"""Stream a response from a local model; importing this module makes no requests."""

import argparse
import logging
import os
from collections.abc import Sequence
from urllib.parse import urlsplit

from openai import OpenAI, OpenAIError

LOGGER = logging.getLogger(__name__)
DEFAULT_PROMPT = "Summarize this contract clause in 3 bullets: ..."


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Read configuration here only; command-line options override the environment."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default=os.environ.get("LOCAL_CHAT_BASE_URL"),
        help="Local endpoint including /v1 (or LOCAL_CHAT_BASE_URL).",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("LOCAL_CHAT_MODEL"),
        help="Model ID (or LOCAL_CHAT_MODEL).",
    )
    parser.add_argument("--prompt", default=DEFAULT_PROMPT, help="Text to send to the model.")
    args = parser.parse_args(argv)
    if not args.base_url or not args.base_url.strip():
        parser.error("set --base-url or LOCAL_CHAT_BASE_URL to your local endpoint, including /v1")
    try:
        url = urlsplit(args.base_url)
        valid_url = (
            url.scheme in {"http", "https"}
            and bool(url.hostname)
            and not (url.username or url.password or url.query or url.fragment)
        )
        _ = url.port  # Validate the optional port before constructing a network client.
    except ValueError:
        valid_url = False
    if not valid_url:
        parser.error("--base-url must be an HTTP(S) URL without credentials, query, or fragment")
    if not args.model or not args.model.strip():
        parser.error("set --model or LOCAL_CHAT_MODEL to a model available on your endpoint")
    if not args.prompt.strip():
        parser.error("--prompt must not be empty")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    """Run one streaming chat request and return a process exit code."""
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        with (
            OpenAI(base_url=args.base_url, api_key="not-needed") as client,
            client.chat.completions.create(
                model=args.model,
                messages=[{"role": "user", "content": args.prompt}],
                stream=True,
            ) as stream,
        ):
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    print(chunk.choices[0].delta.content, end="", flush=True)
        print()  # Model output belongs on stdout; diagnostics use logging.
    except OpenAIError:
        LOGGER.error(
            "Chat request failed. Check that the local endpoint is running and model exists."
        )
        return 1
    except KeyboardInterrupt:
        LOGGER.info("Chat cancelled.")
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
