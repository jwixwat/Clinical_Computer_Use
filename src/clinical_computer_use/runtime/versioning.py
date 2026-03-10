"""Run-level version linkage metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
import subprocess

from clinical_computer_use.config import (
    OPENAI_MODEL,
    POLICY_BUNDLE_VERSION,
    PROMPT_BUNDLE_VERSION,
    TOOL_SURFACE_VERSION,
)


@dataclass
class RunVersionBundle:
    model: str = OPENAI_MODEL
    prompt_bundle_version: str = PROMPT_BUNDLE_VERSION
    policy_bundle_version: str = POLICY_BUNDLE_VERSION
    tool_surface_version: str = TOOL_SURFACE_VERSION
    git_commit: str = "unknown"
    role_config: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "model": self.model,
            "prompt_bundle_version": self.prompt_bundle_version,
            "policy_bundle_version": self.policy_bundle_version,
            "tool_surface_version": self.tool_surface_version,
            "git_commit": self.git_commit,
            "role_config": self.role_config,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "RunVersionBundle":
        role_config = payload.get("role_config", {})
        return cls(
            model=str(payload.get("model", OPENAI_MODEL)),
            prompt_bundle_version=str(payload.get("prompt_bundle_version", PROMPT_BUNDLE_VERSION)),
            policy_bundle_version=str(payload.get("policy_bundle_version", POLICY_BUNDLE_VERSION)),
            tool_surface_version=str(payload.get("tool_surface_version", TOOL_SURFACE_VERSION)),
            git_commit=str(payload.get("git_commit", "unknown")),
            role_config=role_config if isinstance(role_config, dict) else {},
        )


def resolve_git_commit() -> str:
    try:
        output = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True)
        return output.strip() or "unknown"
    except Exception:
        return "unknown"


def build_run_version_bundle(*, role_config: dict[str, object] | None = None) -> RunVersionBundle:
    return RunVersionBundle(
        model=OPENAI_MODEL,
        prompt_bundle_version=PROMPT_BUNDLE_VERSION,
        policy_bundle_version=POLICY_BUNDLE_VERSION,
        tool_surface_version=TOOL_SURFACE_VERSION,
        git_commit=resolve_git_commit(),
        role_config=role_config or {},
    )

