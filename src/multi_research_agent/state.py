"""Shared state object that agents read from and hand off to each other."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class HandoffEvent:
    from_agent: str
    to_agent: str
    note: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class ResearchState:
    topic: str

    # SearchAgent -> SummarizeAgent
    sources: list[dict[str, Any]] = field(default_factory=list)
    raw_notes: str = ""
    search_tool_calls: int = 0

    # SummarizeAgent -> FactCheckAgent
    summary_sections: list[dict[str, Any]] = field(default_factory=list)

    # FactCheckAgent -> DraftAgent
    verified_claims: list[dict[str, Any]] = field(default_factory=list)
    flagged_claims: list[dict[str, Any]] = field(default_factory=list)
    factcheck_tool_calls: int = 0

    # DraftAgent output
    draft_markdown: str = ""

    handoffs: list[HandoffEvent] = field(default_factory=list)

    def log_handoff(self, from_agent: str, to_agent: str, note: str) -> None:
        self.handoffs.append(HandoffEvent(from_agent, to_agent, note))

    def to_trace_dict(self) -> dict[str, Any]:
        return {
            "topic": self.topic,
            "sources": self.sources,
            "raw_notes": self.raw_notes,
            "summary_sections": self.summary_sections,
            "verified_claims": self.verified_claims,
            "flagged_claims": self.flagged_claims,
            "draft_markdown": self.draft_markdown,
            "handoffs": [
                {
                    "from": h.from_agent,
                    "to": h.to_agent,
                    "note": h.note,
                    "timestamp": h.timestamp,
                }
                for h in self.handoffs
            ],
        }
