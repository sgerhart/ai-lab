"""Model backend interface, implementations, and HTTP client."""

from __future__ import annotations

import ast
import json
import re
import time
from typing import Any, Callable, Protocol
import urllib.error
import urllib.request

from packages.contracts import (
    GenerationConfig,
    GenerationResult,
    HealthStatus,
    ModelCapabilities,
)


def extract_python_code(raw_text: str) -> tuple[str, bool]:
    """Extracts a clean Python code snippet from raw model output.
    
    Returns (cleaned_code, is_syntax_valid).
    """
    text = raw_text.strip()
    
    # Check for markdown code fences
    fence_pattern = r"```(?:python)?\s*\n(.*?)\n```"
    matches = re.findall(fence_pattern, text, re.DOTALL)
    if matches:
        candidate = matches[0].strip()
    else:
        # Fallback: remove any standalone backticks and markdown fences
        candidate = text.replace("```python", "").replace("```", "").strip()

    # Verify AST syntax
    try:
        ast.parse(candidate)
        return candidate, True
    except SyntaxError:
        return candidate, False


class ModelBackend(Protocol):
    """Protocol for local model inference and training."""

    def load(self, model_id: str, revision: str) -> None: ...

    def generate(self, prompt: str, seed: int, config: GenerationConfig) -> GenerationResult: ...

    def capabilities(self) -> ModelCapabilities: ...

    def health(self) -> HealthStatus: ...


class MockModelBackend:
    """Deterministic mock model backend for testing, CI, and baseline dry-runs."""

    def __init__(
        self,
        responses: dict[str, str] | None = None,
        task_solutions: dict[str, str] | None = None,
        generator_fn: Callable[[str, int, GenerationConfig], str] | None = None,
    ):
        self.loaded_model: str | None = None
        self.responses = responses or {}
        self.task_solutions = task_solutions or {}
        self.generator_fn = generator_fn
        self._capabilities = ModelCapabilities(
            supports_inference=True,
            supports_sft=True,
            supports_lora=True,
            supports_qlora=False,
            supports_grpo=False,
            supports_logprobs=False,
            device_arch="mock_cpu",
        )

    def load(self, model_id: str, revision: str) -> None:
        self.loaded_model = f"{model_id}@{revision}"

    def generate(self, prompt: str, seed: int, config: GenerationConfig) -> GenerationResult:
        start_time = time.monotonic()
        
        # 1. Check exact prompt response
        if prompt in self.responses:
            raw_output = self.responses[prompt]
        # 2. Check generator function
        elif self.generator_fn:
            raw_output = self.generator_fn(prompt, seed, config)
        # 3. Check task solutions by searching for entry point in prompt
        else:
            raw_output = None
            for key, code in self.task_solutions.items():
                if (
                    key in prompt
                    or f"def {key}(" in prompt
                    or f"`{key}`" in prompt
                    or f" {key}(" in prompt
                ):
                    raw_output = f"```python\n{code}\n```"
                    break
                # Check function name defined in solution code
                m = re.search(r"def\s+([a-zA-Z0-9_]+)\s*\(", code)
                if m and (f"def {m.group(1)}(" in prompt or f"{m.group(1)}(" in prompt):
                    raw_output = f"```python\n{code}\n```"
                    break
            
            if raw_output is None:
                # Default minimal dummy solution
                raw_output = "```python\ndef solution(*args, **kwargs):\n    return True\n```"

        extracted, valid = extract_python_code(raw_output)
        latency_ms = max(1, int((time.monotonic() - start_time) * 1000))
        
        return GenerationResult(
            raw_text=raw_output,
            extracted_code=extracted,
            syntax_valid=valid,
            prompt_tokens=len(prompt.split()),
            completion_tokens=len(raw_output.split()),
            latency_ms=latency_ms,
            model_version=self.loaded_model or "mock-v1",
            stop_reason="stop",
        )

    def capabilities(self) -> ModelCapabilities:
        return self._capabilities

    def health(self) -> HealthStatus:
        return HealthStatus(
            healthy=True,
            status="ok",
            details={
                "mock": True,
                "loaded_model": self.loaded_model,
                "configured_responses": len(self.responses),
                "configured_solutions": len(self.task_solutions),
            },
        )


class MLXModelBackend:
    """Apple Silicon MLX and MLX-LM native model backend.
    
    Provides high-performance local inference on Mac Studio unified memory.
    Gracefully falls back to mock dry-run or provides explicit diagnostics
    when MLX is not installed.
    """

    def __init__(self, dry_run_fallback: bool = True):
        self.loaded_model_id: str | None = None
        self.loaded_revision: str | None = None
        self.model = None
        self.tokenizer = None
        self.dry_run_fallback = dry_run_fallback
        self._mlx_available = False
        
        try:
            import mlx.core as mx  # noqa: F401
            import mlx_lm  # noqa: F401
            self._mlx_available = True
        except ImportError:
            self._mlx_available = False

    @property
    def is_mlx_available(self) -> bool:
        return self._mlx_available

    def load(self, model_id: str, revision: str) -> None:
        self.loaded_model_id = model_id
        self.loaded_revision = revision
        
        if not self._mlx_available:
            if self.dry_run_fallback:
                return
            raise RuntimeError(
                f"MLX framework is not installed on this host. Cannot load {model_id}@{revision}"
            )

        import mlx_lm
        self.model, self.tokenizer = mlx_lm.load(
            model_id,
            revision=revision,
            tokenizer_config={"trust_remote_code": True},
        )

    def generate(self, prompt: str, seed: int, config: GenerationConfig) -> GenerationResult:
        start_time = time.monotonic()
        
        if not self._mlx_available or self.model is None or self.tokenizer is None:
            if self.dry_run_fallback:
                raw_text = (
                    f"```python\n# MLX Dry-run output (seed={seed})\n"
                    f"def solve(*args, **kwargs):\n    return None\n```"
                )
                extracted, valid = extract_python_code(raw_text)
                return GenerationResult(
                    raw_text=raw_text,
                    extracted_code=extracted,
                    syntax_valid=valid,
                    prompt_tokens=len(prompt.split()),
                    completion_tokens=len(raw_text.split()),
                    latency_ms=10,
                    model_version=f"{self.loaded_model_id or 'dry-run'}@{self.loaded_revision or 'latest'}",
                    stop_reason="stop",
                )
            raise RuntimeError("MLX model is not loaded or MLX is unavailable.")

        import mlx.core as mx
        import mlx_lm

        # Seed Apple Silicon PRNG for determinism
        mx.random.seed(seed)
        
        raw_text = mlx_lm.generate(
            self.model,
            self.tokenizer,
            prompt=prompt,
            temp=config.temperature,
            top_p=config.top_p,
            max_tokens=config.max_completion_tokens,
            verbose=False,
        )
        
        latency_ms = max(1, int((time.monotonic() - start_time) * 1000))
        extracted, valid = extract_python_code(raw_text)
        
        prompt_tokens = len(self.tokenizer.encode(prompt))
        completion_tokens = len(self.tokenizer.encode(raw_text))

        return GenerationResult(
            raw_text=raw_text,
            extracted_code=extracted,
            syntax_valid=valid,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
            model_version=f"{self.loaded_model_id}@{self.loaded_revision}",
            stop_reason="stop",
        )

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(
            supports_inference=True,
            supports_sft=self._mlx_available,
            supports_lora=self._mlx_available,
            supports_qlora=self._mlx_available,
            supports_grpo=False,
            supports_logprobs=False,
            device_arch="apple_silicon" if self._mlx_available else "mock_cpu",
        )

    def health(self) -> HealthStatus:
        return HealthStatus(
            healthy=True,
            status="ok" if self._mlx_available else "dry_run",
            details={
                "mlx_available": self._mlx_available,
                "loaded_model": self.loaded_model_id,
                "revision": self.loaded_revision,
            },
        )


class HttpModelBackend:
    """HTTP client communicating with the Mac Studio ModelWorker service."""

    def __init__(self, base_url: str = "http://mac-studio:8090", timeout_seconds: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as e:
            raise ConnectionError(f"Failed to communicate with ModelWorker at {url}: {e}") from e

    def _get(self, path: str) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as e:
            raise ConnectionError(f"Failed to communicate with ModelWorker at {url}: {e}") from e

    def load(self, model_id: str, revision: str) -> None:
        self._post("/v1/models/load", {"model_id": model_id, "revision": revision})

    def generate(self, prompt: str, seed: int, config: GenerationConfig) -> GenerationResult:
        payload = {
            "prompt": prompt,
            "seed": seed,
            "config": config.model_dump(),
        }
        res = self._post("/v1/generate", payload)
        return GenerationResult(**res)

    def capabilities(self) -> ModelCapabilities:
        res = self._get("/v1/capabilities")
        return ModelCapabilities(**res)

    def health(self) -> HealthStatus:
        res = self._get("/v1/health")
        return HealthStatus(**res)
