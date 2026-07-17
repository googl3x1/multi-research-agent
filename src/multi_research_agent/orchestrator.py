"""Coordinates the sequential hand-off pipeline: Search -> Summarize ->
Fact-check -> Draft, logging each hand-off and persisting the result.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from .agents import (
    run_draft_agent,
    run_factcheck_agent,
    run_search_agent,
    run_summarize_agent,
)
from .state import ResearchState

console = Console()

PIPELINE = [
    ("SearchAgent", run_search_agent),
    ("SummarizeAgent", run_summarize_agent),
    ("FactCheckAgent", run_factcheck_agent),
    ("DraftAgent", run_draft_agent),
]


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:60] or "research"


def run_pipeline(topic: str, output_dir: Path | None = None) -> ResearchState:
    state = ResearchState(topic=topic)
    output_dir = output_dir or Path("reports")
    output_dir.mkdir(parents=True, exist_ok=True)

    console.print(Panel(f"[bold]Research topic:[/bold] {topic}", style="cyan"))

    for name, step in PIPELINE:
        console.print(f"[dim]-> running {name}...[/dim]")
        state = step(state)
        last = state.handoffs[-1]
        console.print(
            f"[green]{last.from_agent}[/green] -> [green]{last.to_agent}[/green]: {last.note}"
        )

    console.print(Panel(Markdown(state.draft_markdown), title="Final Report", style="magenta"))

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    slug = _slugify(topic)

    report_path = output_dir / f"{slug}-{timestamp}.md"
    trace_path = output_dir / f"{slug}-{timestamp}.trace.json"

    report_path.write_text(state.draft_markdown, encoding="utf-8")
    trace_path.write_text(
        json.dumps(state.to_trace_dict(), indent=2), encoding="utf-8"
    )

    console.print(f"\n[bold]Report saved:[/bold] {report_path}")
    console.print(f"[bold]Trace saved:[/bold] {trace_path}")

    return state
