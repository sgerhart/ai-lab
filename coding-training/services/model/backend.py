"""Model backend interface and test stub."""

from __future__ import annotations

import ast
import re
from typing import Protocol

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
        # Fallback: remove any standalone backticks
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
    """Deterministic mock model backend for unit testing and CI."""

    def __init__(self, responses: dict[str, str] | None = None):
        self.loaded_model: str | None = None
        self.responses = responses or {}
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
        # Return canned response if present, otherwise a deterministic stub
        raw_output = self.responses.get(
            prompt,
            "```python\ndef solution(*args, **kwargs):\n    return True\n```",
        )
        extracted, valid = extract_python_code(raw_output)
        
        return GenerationResult(
            raw_text=raw_output,
            extracted_code=extracted,
            syntax_valid=valid,
            prompt_tokens=len(prompt.split()),
            completion_tokens=len(raw_output.split()),
            latency_ms=15,
            model_version=self.loaded_model or "mock-v1",
            stop_reason="stop",
        )

    def capabilities(self) -> ModelCapabilities:
        return self._capabilities

    def health(self) -> HealthStatus:
        return HealthStatus(healthy=True, status="ok", details={"mock": True})
