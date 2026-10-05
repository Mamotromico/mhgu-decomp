"""The model client for the reconstruction loop: an endpoint that returns C++ from a prompt.

Deliberately dependency-light — the standard library only (``urllib``), no ``requests`` and no
framework (``docs/llm-harness-design.md`` → *The harness*). It speaks the OpenAI-compatible
``/v1/chat/completions`` shape that local servers expose (llama.cpp, Ollama, LM Studio, vLLM),
so switching engines is a config change, not a code change. A provider that does not use the
``/v1`` path (some hosted APIs) sets an explicit full ``endpoint`` in the config instead of a
``base_url``.

The client never writes source and never claims a match; it returns text, and the harness
extracts a candidate and hands it to the byte gate. ``strip_fences`` bridges the one common
formatting quirk (a model wrapping its answer in a Markdown code fence).

No secret is hardcoded: an API key, if one is needed, is read from the environment variable
named by ``api_key_env`` in the config. Routing is never decided implicitly — the ``proxy``
setting is ``none`` (direct, the default), ``env`` (honor ``http_proxy``/``https_proxy``), or
an explicit ``http(s)://`` URL — so a stray environment proxy cannot silently reroute a
request (and its key).

Usage::

    # smoke test connectivity/format against the configured endpoint
    python3 tools/loop/model.py --smoke
    python3 tools/loop/model.py --prompt "Reply with exactly: OK"
    python3 tools/loop/model.py --prompt-file prompt.txt --raw
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

REPO = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO / "config" / "model.json"

SYSTEM_PROMPT = (
    "You reconstruct C++ functions from ARM disassembly for a matching decompilation. "
    "Reply with the function body only — no prose, no Markdown fences."
)


class ModelError(Exception):
    """A transport or protocol failure talking to the model."""


@dataclass
class Completion:
    """One model response and its accounting."""

    text: str
    model: str = ""
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    latency_s: float = 0.0


class Model(Protocol):
    def complete(self, prompt: str, *, system: str | None = None) -> Completion: ...


# --- pure helpers (unit-tested) -------------------------------------------------------

def proxy_handler(spec: str) -> urllib.request.ProxyHandler | None:
    """Resolve the ``proxy`` setting to a urllib handler, or ``None`` for the stock default.

    * ``"none"`` — never proxy; connect directly (an explicit *empty* handler cancels the
      environment's ``http_proxy``/``https_proxy``).
    * ``"env"`` — honor the environment (stock urllib behaviour).
    * any other string is a proxy URL applied to both ``http`` and ``https``.
    """
    spec = (spec or "none").strip()
    if spec == "env":
        return None
    if spec == "none":
        return urllib.request.ProxyHandler({})
    if not spec.startswith(("http://", "https://")):
        raise ValueError(f"proxy must be 'none', 'env', or a http(s):// URL — got {spec!r}")
    return urllib.request.ProxyHandler({"http": spec, "https": spec})


def chat_endpoint(base_url: str) -> str:
    """Derive the chat-completions URL from a base URL, tolerating common shapes."""
    base = base_url.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    if base.endswith("/v1"):
        return base + "/chat/completions"
    return base + "/v1/chat/completions"


def build_payload(model: str, prompt: str, system: str | None, temperature: float | None,
                  max_tokens: int | None, seed: int | None = None) -> dict:
    """The OpenAI-compatible request body.

    ``temperature`` and ``seed`` are sent only when set, so omitting one leaves the server's
    own default (e.g. a router preset) in force rather than overriding it with a client value.
    """
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload: dict = {"model": model, "messages": messages, "stream": False}
    if temperature is not None:
        payload["temperature"] = temperature
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if seed is not None:
        payload["seed"] = seed
    return payload


def parse_response(data: dict, latency_s: float) -> Completion:
    """Extract the assistant text and usage from a chat-completions response."""
    try:
        choices = data["choices"]
        text = choices[0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise ModelError(f"unexpected response shape: {e}") from e
    usage = data.get("usage") or {}
    return Completion(
        text=text,
        model=data.get("model", ""),
        prompt_tokens=usage.get("prompt_tokens"),
        completion_tokens=usage.get("completion_tokens"),
        latency_s=latency_s,
    )


def strip_fences(text: str) -> str:
    """Return the contents of the first Markdown code fence, or the trimmed text."""
    fence = text.find("```")
    if fence < 0:
        return text.strip()
    rest = text[fence + 3:]
    newline = rest.find("\n")
    if newline < 0:
        return text.strip()
    body = rest[newline + 1:]
    end = body.find("```")
    if end >= 0:
        body = body[:end]
    return body.strip("\n")


# --- the HTTP client ------------------------------------------------------------------

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Refuse redirects, so the endpoint — and any API key — cannot be bounced elsewhere."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class HttpModel:
    """An OpenAI-compatible chat-completions client over ``urllib``.

    The request URL is either an explicit ``endpoint`` (used verbatim) or derived from
    ``base_url``; redirects are never followed.
    """

    def __init__(self, base_url: str = "", model: str = "", *, endpoint: str | None = None,
                 api_key: str | None = None, proxy: str = "none", timeout_s: float = 120.0,
                 temperature: float | None = None, max_tokens: int | None = None,
                 seed: int | None = None, system: str | None = SYSTEM_PROMPT):
        if endpoint:
            self.endpoint = endpoint
        elif base_url:
            self.endpoint = chat_endpoint(base_url)
        else:
            raise ValueError("HttpModel needs a base_url or an explicit endpoint")
        handlers: list = [_NoRedirect]
        handler = proxy_handler(proxy)
        if handler is not None:
            handlers.append(handler)
        self._opener = urllib.request.build_opener(*handlers)
        self.model = model
        self.api_key = api_key
        self.timeout_s = timeout_s
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.seed = seed
        self.system = system

    def complete(self, prompt: str, *, system: str | None = None) -> Completion:
        payload = build_payload(self.model, prompt,
                                self.system if system is None else system,
                                self.temperature, self.max_tokens, self.seed)
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(
            self.endpoint, data=json.dumps(payload).encode(), headers=headers, method="POST")
        start = time.monotonic()
        try:
            with self._opener.open(request, timeout=self.timeout_s) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:400]
            hint = ""
            if e.code in (401, 403) and not self.api_key:
                hint = " — this endpoint requires a key; set the env var named by api_key_env"
            raise ModelError(f"HTTP {e.code} from {self.endpoint}: {detail}{hint}") from e
        except TimeoutError as e:
            # A read timeout (e.g. a cold model still loading) — surface it cleanly.
            raise ModelError(
                f"timed out after {self.timeout_s:.0f}s waiting for {self.endpoint} "
                f"(a first call that loads the model can take a while; raise --timeout)") from e
        except urllib.error.URLError as e:
            raise ModelError(
                f"cannot reach {self.endpoint}: {e.reason} — is the model server running?") from e
        latency = time.monotonic() - start
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ModelError(f"non-JSON response from {self.endpoint}: {e}") from e
        return parse_response(data, latency)


# --- config ---------------------------------------------------------------------------

def from_config(path: Path, *, override_base_url: str | None = None,
                override_model: str | None = None,
                override_endpoint: str | None = None,
                override_proxy: str | None = None,
                override_timeout: float | None = None,
                override_temperature: float | None = None,
                override_seed: int | None = None) -> HttpModel:
    """Build the configured client; the API key comes from the environment, never the file.

    URL precedence: an explicit ``endpoint`` (config or override) wins over ``base_url``; a
    ``base_url`` is then completed to ``/v1/chat/completions``.
    """
    cfg = json.loads(path.read_text()) if path.exists() else {}
    if override_endpoint:
        endpoint, base_url = override_endpoint, ""
    elif override_base_url:
        endpoint, base_url = None, override_base_url
    else:
        endpoint = cfg.get("endpoint") or None
        base_url = cfg.get("base_url", "http://127.0.0.1:8080")
    model = override_model or cfg.get("model", "local-model")
    proxy = override_proxy if override_proxy is not None else cfg.get("proxy", "none")
    key_env = cfg.get("api_key_env")
    api_key = os.environ.get(key_env) if key_env else None
    temperature = (override_temperature if override_temperature is not None
                   else cfg.get("temperature"))
    seed = override_seed if override_seed is not None else cfg.get("seed")
    return HttpModel(
        base_url=base_url, model=model, endpoint=endpoint, api_key=api_key, proxy=proxy,
        timeout_s=float(override_timeout if override_timeout is not None
                        else cfg.get("timeout_s", 120)),
        temperature=None if temperature is None else float(temperature),
        max_tokens=cfg.get("max_tokens"),
        seed=None if seed is None else int(seed),
    )


# --- CLI ------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    ap.add_argument("--base-url", default=None, help="override the configured base URL")
    ap.add_argument("--endpoint", default=None,
                    help="full chat-completions URL (overrides base_url and any config endpoint)")
    ap.add_argument("--model", default=None, help="override the configured model name")
    ap.add_argument("--proxy", default=None,
                    help="'none' (direct, default), 'env', or a http(s):// proxy URL")
    ap.add_argument("--timeout", type=float, default=None,
                    help="request timeout in seconds (default: the config's timeout_s)")
    ap.add_argument("--temperature", type=float, default=None,
                    help="sampling temperature (omit to use the server/preset default)")
    ap.add_argument("--seed", type=int, default=None, help="sampling seed (optional)")
    ap.add_argument("--prompt", default=None)
    ap.add_argument("--prompt-file", type=Path, default=None)
    ap.add_argument("--smoke", action="store_true",
                    help="send a trivial prompt to check connectivity and format")
    ap.add_argument("--raw", action="store_true", help="print the raw response verbatim")
    args = ap.parse_args(argv)

    if args.smoke:
        prompt = "Reply with exactly: OK"
    elif args.prompt_file is not None:
        prompt = args.prompt_file.read_text()
    elif args.prompt is not None:
        prompt = args.prompt
    else:
        ap.error("one of --smoke / --prompt / --prompt-file is required")

    if not args.config.exists() and args.base_url is None and args.endpoint is None:
        print(f"error: missing {args.config} (or pass --base-url/--endpoint)", file=sys.stderr)
        return 2

    try:
        model = from_config(args.config, override_base_url=args.base_url,
                            override_model=args.model, override_endpoint=args.endpoint,
                            override_proxy=args.proxy, override_timeout=args.timeout,
                            override_temperature=args.temperature, override_seed=args.seed)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"error: bad model config: {e}", file=sys.stderr)
        return 2
    print(f"endpoint: {model.endpoint}  model: {model.model}")
    try:
        result = model.complete(prompt)
    except ModelError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    text = result.text if args.raw else strip_fences(result.text)
    print(f"latency: {result.latency_s:.2f}s"
          + (f"  tokens: {result.prompt_tokens}->{result.completion_tokens}"
             if result.completion_tokens is not None else ""))
    print("---")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
