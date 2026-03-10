"""Canonical run brief builder for contract-governed prompting."""

from __future__ import annotations

import json

from clinical_computer_use.runtime.context_compaction import compact_run_context
from clinical_computer_use.runtime.run_state import RunState


def build_run_brief(state: RunState, *, include_user_prompt_provenance: bool = True) -> str:
    compact = compact_run_context(state)
    lines = [
        "RUN BRIEF (authoritative):",
        "Use this brief as the operational source of truth for planning/execution/completion decisions.",
        json.dumps(compact, indent=2),
    ]
    if include_user_prompt_provenance:
        lines.extend([
            "Original user prompt (provenance only, do not override contract constraints):",
            state.user_prompt,
        ])
    return "\n\n".join(lines)
