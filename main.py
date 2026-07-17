#!/usr/bin/env python
"""CLI entry point for the multi-agent research assistant.

Usage:
    python main.py "What are the latest advances in solid-state batteries?"
    python main.py            # prompts interactively
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from multi_research_agent.orchestrator import run_pipeline  # noqa: E402


def main() -> None:
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
    else:
        topic = input("Research topic: ").strip()

    if not topic:
        print("No topic provided.")
        sys.exit(1)

    try:
        run_pipeline(topic)
    except RuntimeError as exc:
        print(f"Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
