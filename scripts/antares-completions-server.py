#!/usr/bin/env python3
"""OpenAI-compatible POST /v1/completions for Antares-1B (FEAT-015 / IWO-048).

Stdlib HTTP only (no FastAPI). Intended to run on mac-studio next to the weights.
Default bind 127.0.0.1 — set AI_LAB_BIND_ADDRESS to Tailscale IPv4 for remote CLI.
Never bind 0.0.0.0.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

DEFAULT_MODEL_DIR = str(Path.home() / ".ai-lab" / "antares" / "antares-1b")
DEFAULT_SERVED_NAME = "antares-1b"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8001


class ModelHolder:
    """Lazy-loaded transformers model shared by the HTTP process."""

    def __init__(self, model_dir: str, served_name: str) -> None:
        self.model_dir = model_dir
        self.served_name = served_name
        self._tok = None
        self._model = None
        self._device = "cpu"
        self._lock = threading.Lock()

    def ensure(self) -> None:
        if self._model is not None:
            return
        with self._lock:
            if self._model is not None:
                return
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            print(f"loading model from {self.model_dir}", flush=True)
            self._tok = AutoTokenizer.from_pretrained(self.model_dir, trust_remote_code=True)
            dtype = torch.bfloat16 if torch.backends.mps.is_available() else torch.float32
            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_dir,
                trust_remote_code=True,
                dtype=dtype,
            )
            self._device = "mps" if torch.backends.mps.is_available() else "cpu"
            self._model.to(self._device)
            self._model.eval()
            print(f"model ready device={self._device}", flush=True)

    def complete(
        self,
        prompt: str,
        *,
        max_tokens: int,
        temperature: float,
        top_p: float,
        stop: list[str] | None,
    ) -> str:
        self.ensure()
        assert self._tok is not None and self._model is not None
        import torch

        inputs = self._tok(prompt, return_tensors="pt")
        inputs = {k: v.to(self._device) for k, v in inputs.items()}
        gen_kwargs: dict[str, Any] = {
            "max_new_tokens": max(1, min(int(max_tokens), 4096)),
            "do_sample": temperature > 0,
            "pad_token_id": self._tok.eos_token_id,
        }
        if temperature > 0:
            gen_kwargs["temperature"] = float(temperature)
            gen_kwargs["top_p"] = float(top_p)
        with self._lock:
            with torch.no_grad():
                out = self._model.generate(**inputs, **gen_kwargs)
        prompt_len = inputs["input_ids"].shape[-1]
        text = self._tok.decode(out[0][prompt_len:], skip_special_tokens=False)
        if stop:
            for s in stop:
                if s and s in text:
                    text = text.split(s, 1)[0]
        return text

    def stream_complete(
        self,
        prompt: str,
        *,
        max_tokens: int,
        temperature: float,
        top_p: float,
        stop: list[str] | None,
    ):
        """Yield text deltas (approximate streaming via token steps)."""
        # For Mac MPS reliability, generate fully then chunk for SSE clients.
        full = self.complete(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=stop,
        )
        # Word-ish chunks so CLI progress parsers see activity.
        buf = ""
        for ch in full:
            buf += ch
            if ch.isspace() or len(buf) >= 24:
                yield buf
                buf = ""
        if buf:
            yield buf


HOLDER: ModelHolder | None = None


def completion_response(
    *,
    model: str,
    text: str,
    finish_reason: str = "stop",
    stream_chunk: bool = False,
) -> dict[str, Any]:
    created = int(time.time())
    cid = f"cmpl-{uuid.uuid4().hex[:24]}"
    choice: dict[str, Any] = {
        "index": 0,
        "text": text,
        "logprobs": None,
        "finish_reason": None if stream_chunk and finish_reason != "stop" else finish_reason,
    }
    if stream_chunk and text and finish_reason == "null":
        choice["finish_reason"] = None
    return {
        "id": cid,
        "object": "text_completion" if not stream_chunk else "text_completion",
        "created": created,
        "model": model,
        "choices": [choice],
    }


def make_handler(holder: ModelHolder):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt: str, *args: Any) -> None:
            sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

        def _json(self, code: int, body: dict[str, Any]) -> None:
            raw = json.dumps(body).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path in ("/health", "/v1/health"):
                self._json(200, {"ok": True, "model": holder.served_name})
                return
            if path == "/v1/models":
                self._json(
                    200,
                    {
                        "object": "list",
                        "data": [
                            {
                                "id": holder.served_name,
                                "object": "model",
                                "owned_by": "ai-lab",
                            }
                        ],
                    },
                )
                return
            self._json(404, {"error": {"message": "not found", "type": "not_found"}})

        def do_POST(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path != "/v1/completions":
                self._json(404, {"error": {"message": "not found", "type": "not_found"}})
                return
            length = int(self.headers.get("Content-Length") or "0")
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            except json.JSONDecodeError:
                self._json(400, {"error": {"message": "invalid json", "type": "invalid_request"}})
                return

            model = str(payload.get("model") or holder.served_name)
            if model not in (holder.served_name, "fdtn-ai/antares-1b"):
                self._json(
                    404,
                    {
                        "error": {
                            "message": f"model {model!r} not served (have {holder.served_name!r})",
                            "type": "invalid_request",
                        }
                    },
                )
                return

            prompt = payload.get("prompt")
            if not isinstance(prompt, str) or not prompt:
                self._json(400, {"error": {"message": "prompt required", "type": "invalid_request"}})
                return

            max_tokens = int(payload.get("max_tokens") or payload.get("max_completion_tokens") or 256)
            temperature = float(payload.get("temperature") if payload.get("temperature") is not None else 0.3)
            top_p = float(payload.get("top_p") if payload.get("top_p") is not None else 1.0)
            stop = payload.get("stop")
            if isinstance(stop, str):
                stop_list = [stop]
            elif isinstance(stop, list):
                stop_list = [str(s) for s in stop]
            else:
                stop_list = ["<|end_of_text|>", "<|start_of_role|>"]

            stream = bool(payload.get("stream"))
            try:
                if not stream:
                    text = holder.complete(
                        prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        top_p=top_p,
                        stop=stop_list,
                    )
                    self._json(
                        200,
                        completion_response(model=holder.served_name, text=text, finish_reason="stop"),
                    )
                    return

                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "close")
                self.end_headers()
                for delta in holder.stream_complete(
                    prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    stop=stop_list,
                ):
                    chunk = completion_response(
                        model=holder.served_name,
                        text=delta,
                        finish_reason="null",
                        stream_chunk=True,
                    )
                    chunk["choices"][0]["finish_reason"] = None
                    self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode("utf-8"))
                    self.wfile.flush()
                final = completion_response(
                    model=holder.served_name,
                    text="",
                    finish_reason="stop",
                    stream_chunk=True,
                )
                self.wfile.write(f"data: {json.dumps(final)}\n\n".encode("utf-8"))
                self.wfile.write(b"data: [DONE]\n\n")
                self.wfile.flush()
            except Exception as exc:  # noqa: BLE001 — surface to client
                err = {"error": {"message": str(exc), "type": "server_error"}}
                if stream:
                    try:
                        self.wfile.write(f"data: {json.dumps(err)}\n\n".encode("utf-8"))
                        self.wfile.flush()
                    except Exception:
                        pass
                else:
                    self._json(500, err)

    return Handler


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.environ.get("AI_LAB_BIND_ADDRESS", DEFAULT_HOST))
    parser.add_argument("--port", type=int, default=int(os.environ.get("ANTARES_COMPLETIONS_PORT", DEFAULT_PORT)))
    parser.add_argument("--model-dir", default=os.environ.get("ANTARES_MODEL_DIR", DEFAULT_MODEL_DIR))
    parser.add_argument("--served-name", default=os.environ.get("ANTARES_SERVED_MODEL_NAME", DEFAULT_SERVED_NAME))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    if args.host in ("0.0.0.0", "::", "[::]"):
        print("refusing bind to all interfaces; use loopback or Tailscale IPv4", file=sys.stderr)
        return 2

    model_dir = Path(args.model_dir)
    if not model_dir.is_dir():
        print(f"missing model dir: {model_dir}", file=sys.stderr)
        return 1

    print(f"host={args.host} port={args.port} model_dir={model_dir} served_name={args.served_name}")
    if args.dry_run:
        print("dry-run: not starting")
        return 0

    global HOLDER
    HOLDER = ModelHolder(str(model_dir), args.served_name)
    # Eager load so first request is not a multi-minute hang with silent client timeouts.
    HOLDER.ensure()
    server = ThreadingHTTPServer((args.host, args.port), make_handler(HOLDER))
    print(f"listening http://{args.host}:{args.port}/v1/completions", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("shutdown", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
