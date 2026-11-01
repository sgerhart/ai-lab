"""FastAPI HTTP service for SandboxWorker daemon on isolated Linux VM."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from packages.contracts import (
    ExecutionRequest,
    ExecutionResult,
    HealthStatus,
    WorkerAttestation,
)
from .worker import SandboxWorker

app = FastAPI(
    title="AI Lab Sandbox Worker",
    version="1.0.0",
    description="Isolated execution jail for model-generated candidate code",
)

# Global worker instance (default safe enforcement)
worker = SandboxWorker()


@app.post("/v1/execute", response_model=ExecutionResult)
def execute_candidate(request: ExecutionRequest) -> ExecutionResult:
    """Executes candidate code inside isolated disposable jail."""
    try:
        return worker.execute(request)
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Worker unexpected error: {err}") from err


@app.get("/v1/health", response_model=HealthStatus)
def get_health() -> HealthStatus:
    """Returns worker health and jail status."""
    return worker.health()


@app.get("/v1/attest", response_model=WorkerAttestation)
def get_attestation() -> WorkerAttestation:
    """Returns cryptographic worker attestation."""
    return worker.attest()
