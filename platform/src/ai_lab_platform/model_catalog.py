"""Machine-readable model catalog and profiles. Weights are not in Git and are not pulled from here."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class PullRefused(RuntimeError):
    """Raised when any code path tries to download weights."""


class ProfileError(LookupError):
    """Unknown profile or unresolved local model."""


class LocalModelUnavailable(RuntimeError):
    """Requested local Studio model is not installed / Ollama unreachable.

    Callers must not fall back to a usage-billed provider.
    """


def catalog_path() -> Path:
    return Path(__file__).resolve().parents[3] / "models" / "catalog.json"


def load_catalog(path: Path | None = None) -> dict[str, Any]:
    target = path or catalog_path()
    data = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("catalog root must be an object")
    models = data.get("models")
    if not isinstance(models, list):
        raise ValueError("catalog.models must be a list")
    for item in models:
        if not isinstance(item, dict) or not item.get("id"):
            raise ValueError("each catalog model needs an id")
        if item.get("pull_authorized") is True:
            raise ValueError(
                f"{item['id']}: pull_authorized must stay false until a human ADR/work order says otherwise"
            )
        status = str(item.get("status") or "")
        if status in {"pulled", "ready", "live"}:
            raise ValueError(f"{item['id']}: catalog must not claim status={status!r} from Git alone")
    profiles = data.get("profiles")
    if profiles is not None:
        if not isinstance(profiles, list):
            raise ValueError("catalog.profiles must be a list when present")
        seen: set[str] = set()
        for item in profiles:
            if not isinstance(item, dict) or not item.get("id"):
                raise ValueError("each catalog profile needs an id")
            pid = str(item["id"])
            if pid in seen:
                raise ValueError(f"duplicate profile id: {pid}")
            seen.add(pid)
            bc = str(item.get("billing_class") or "")
            if bc not in {"local", "usage_billed_api", "subscription_authorized_client"}:
                raise ValueError(f"profile {pid}: invalid billing_class {bc!r}")
            backend = str(item.get("backend") or "")
            if not backend:
                raise ValueError(f"profile {pid}: backend required")
    return data


def listed_ids(path: Path | None = None) -> list[str]:
    data = load_catalog(path)
    return [str(item["id"]) for item in data.get("models") or []]


def refuse_pull(model_id: str = "") -> None:
    suffix = f" ({model_id})" if model_id else ""
    raise PullRefused(
        f"Refusing to pull weights{suffix}. Use docs/runbooks/adding-a-model.md after human authorization."
    )


def catalog_models_by_id(path: Path | None = None) -> dict[str, dict[str, Any]]:
    data = load_catalog(path)
    return {str(m["id"]): m for m in (data.get("models") or []) if isinstance(m, dict) and m.get("id")}


def catalog_profiles(path: Path | None = None) -> list[dict[str, Any]]:
    data = load_catalog(path)
    return [p for p in (data.get("profiles") or []) if isinstance(p, dict)]


def pull_names_for_model(entry: dict[str, Any]) -> list[str]:
    names: list[str] = []
    primary = entry.get("pull_name")
    if primary:
        names.append(str(primary))
    for alt in entry.get("alternate_pull_names") or []:
        names.append(str(alt))
    return names


def ollama_tag_matches(installed: str, candidate: str) -> bool:
    """True if an Ollama /api/tags name satisfies a catalog pull_name."""
    inst = installed.strip()
    cand = candidate.strip()
    if not inst or not cand:
        return False
    if inst == cand:
        return True
    # Same family:tag prefix (e.g. qwen3-coder:30b vs qwen3-coder:30b-a3b-q4_K_M)
    if inst.startswith(cand + "-") or inst.startswith(cand + ":"):
        return True
    # Tagless family match when candidate has no variant suffix beyond :tag
    inst_base, _, inst_tag = inst.partition(":")
    cand_base, _, cand_tag = cand.partition(":")
    if inst_base == cand_base and cand_tag and (
        inst_tag == cand_tag or inst_tag.startswith(cand_tag + "-") or cand_tag == "latest"
    ):
        return True
    if inst_base == cand_base and not cand_tag:
        return True
    return False


def find_installed_match(installed: list[str], candidates: list[str]) -> str | None:
    for cand in candidates:
        for name in installed:
            if ollama_tag_matches(name, cand):
                return name
    return None


@dataclass(frozen=True)
class ResolvedProfile:
    profile_id: str
    label: str
    billing_class: str
    backend: str
    model: str
    catalog_model_id: str | None
    available: bool
    reason: str | None = None
    intended_use: str = ""


def resolve_profile(
    profile_id: str,
    *,
    installed_ollama: list[str] | None = None,
    cloud_enabled: dict[str, bool] | None = None,
    path: Path | None = None,
) -> ResolvedProfile:
    """Resolve a profile id to backend + model. Local profiles need an installed tag to be available."""
    profiles = {str(p["id"]): p for p in catalog_profiles(path)}
    if profile_id not in profiles:
        raise ProfileError(f"unknown profile: {profile_id}")
    p = profiles[profile_id]
    label = str(p.get("label") or profile_id)
    billing = str(p.get("billing_class") or "local")
    backend = str(p.get("backend") or "ollama")
    intended = str(p.get("intended_use") or "")
    catalog_id = p.get("catalog_model_id")
    catalog_id_s = str(catalog_id) if catalog_id else None
    installed = list(installed_ollama or [])
    cloud = cloud_enabled or {}

    if billing == "local" or backend == "ollama":
        model_name = str(p.get("model") or "")
        candidates: list[str] = []
        if catalog_id_s:
            entry = catalog_models_by_id(path).get(catalog_id_s)
            if entry:
                candidates.extend(pull_names_for_model(entry))
                if not model_name:
                    model_name = str(entry.get("pull_name") or "")
        if p.get("model"):
            candidates.insert(0, str(p["model"]))
        if not candidates and model_name:
            candidates = [model_name]
        matched = find_installed_match(installed, candidates) if installed else None
        if matched:
            return ResolvedProfile(
                profile_id=profile_id,
                label=label,
                billing_class="local",
                backend="ollama",
                model=matched,
                catalog_model_id=catalog_id_s,
                available=True,
                reason=None,
                intended_use=intended,
            )
        display = candidates[0] if candidates else model_name or "?"
        if installed_ollama is None:
            reason = "availability_unknown"
        elif not installed:
            reason = "ollama_unreachable_or_empty"
        else:
            reason = "not_installed_on_studio"
        return ResolvedProfile(
            profile_id=profile_id,
            label=label,
            billing_class="local",
            backend="ollama",
            model=display,
            catalog_model_id=catalog_id_s,
            available=False,
            reason=reason,
            intended_use=intended,
        )

    # usage-billed / other
    model_name = str(p.get("model") or "gpt-4.1")
    enabled = bool(cloud.get(backend, False))
    return ResolvedProfile(
        profile_id=profile_id,
        label=label,
        billing_class=billing,
        backend=backend,
        model=model_name,
        catalog_model_id=catalog_id_s,
        available=enabled,
        reason=None if enabled else "provider_disabled_or_unauthorized",
        intended_use=intended,
    )


def require_local_available(resolved: ResolvedProfile) -> ResolvedProfile:
    """Raise if a local profile cannot run. Never suggests a cloud substitute."""
    if resolved.billing_class == "local" and not resolved.available:
        raise LocalModelUnavailable(
            f"local profile {resolved.profile_id!r} model {resolved.model!r} is unavailable "
            f"({resolved.reason or 'unknown'}). Install on Studio Ollama or pick another local "
            "model — will not fall back to a usage-billed API."
        )
    if resolved.billing_class != "local" and not resolved.available:
        raise LocalModelUnavailable(
            f"profile {resolved.profile_id!r} unavailable ({resolved.reason}). "
            "Authorize usage-billed spend and configure keys before use."
        )
    return resolved


def list_studio_choices(
    installed_ollama: list[str],
    *,
    path: Path | None = None,
) -> list[dict[str, Any]]:
    """Build UI choices: every installed Ollama model, annotated with matching profile when any."""
    profiles = catalog_profiles(path)
    by_id = catalog_models_by_id(path)
    annotated: list[dict[str, Any]] = []
    claimed: set[str] = set()

    # Prefer profile order for preferred matches
    for p in profiles:
        if str(p.get("billing_class")) != "local" or str(p.get("backend")) != "ollama":
            continue
        resolved = resolve_profile(str(p["id"]), installed_ollama=installed_ollama, path=path)
        if not resolved.available:
            continue
        if resolved.model in claimed:
            continue
        claimed.add(resolved.model)
        annotated.append(
            {
                "backend": "ollama",
                "model": resolved.model,
                "profile_id": resolved.profile_id,
                "label": resolved.label,
                "billing_class": "local",
                "available": True,
                "intended_use": resolved.intended_use,
            }
        )

    for name in installed_ollama:
        if name in claimed:
            continue
        # Attach catalog role hint if pull_name matches
        hint_label = name
        profile_id = None
        for mid, entry in by_id.items():
            if find_installed_match([name], pull_names_for_model(entry)):
                hint_label = f"{mid} · {name}"
                break
        annotated.append(
            {
                "backend": "ollama",
                "model": name,
                "profile_id": profile_id,
                "label": hint_label,
                "billing_class": "local",
                "available": True,
                "intended_use": "Installed on Studio Ollama (no profile match)",
            }
        )
    return annotated


def summarize_profiles(
    *,
    installed_ollama: list[str] | None = None,
    cloud_enabled: dict[str, bool] | None = None,
    path: Path | None = None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for p in catalog_profiles(path):
        resolved = resolve_profile(
            str(p["id"]),
            installed_ollama=installed_ollama,
            cloud_enabled=cloud_enabled,
            path=path,
        )
        out.append(
            {
                "id": resolved.profile_id,
                "label": resolved.label,
                "billing_class": resolved.billing_class,
                "backend": resolved.backend,
                "model": resolved.model,
                "catalog_model_id": resolved.catalog_model_id,
                "available": resolved.available,
                "reason": resolved.reason,
                "intended_use": resolved.intended_use,
            }
        )
    return out


@dataclass(frozen=True)
class CatalogSummary:
    schema_version: int
    host: str
    model_count: int
    pulled_in_git: bool = False
