"""Task and dataset manifest schemas."""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class Split(str, Enum):
    """Dataset partition split."""
    TRAIN = "train"
    VAL = "val"
    TEST = "test"


class TestBundleRef(BaseModel):
    """Cryptographic reference to an immutable test bundle."""
    bundle_id: str
    sha256: str = Field(min_length=64, max_length=64, description="SHA-256 hexadecimal digest")
    storage_path: str = Field(description="Content-addressed storage path or URI")
    test_count: int = Field(ge=1, description="Number of test assertions inside the bundle")


class Task(BaseModel):
    """Programming challenge definition and test boundary."""
    task_id: str = Field(description="Unique task identifier, e.g. py-fib-001")
    version: str = Field(default="1.0")
    language: str = Field(default="python")
    prompt: str = Field(description="Prompt given to the model (docstring/function signature)")
    function_contract: str = Field(description="Function signature and type contract")
    difficulty: str = Field(default="medium")
    license: str = Field(default="Apache-2.0")
    source_provenance: str = Field(description="Origin/authoring metadata")
    split: Split = Field(description="Partition split: train, val, test")
    family_id: str = Field(description="Task family for disjoint stratification")
    test_bundle_ref: str = Field(description="Reference ID of the test bundle")
    test_bundle_sha256: str = Field(min_length=64, max_length=64)
    tags: list[str] = Field(default_factory=list)


class DatasetManifest(BaseModel):
    """Immutable catalog manifest for a versioned task dataset."""
    dataset_id: str
    name: str
    version: str
    manifest_hash: str = Field(min_length=64, max_length=64)
    tasks_count: int = Field(ge=1)
    splits: dict[str, int]
    license_review_status: str = Field(default="approved")
