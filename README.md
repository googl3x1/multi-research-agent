# Multi-Agent Research Assistant

Four Claude-powered agents divide a research task and hand off to each other
in sequence:

```
SearchAgent -> SummarizeAgent -> FactCheckAgent -> DraftAgent
```

- **SearchAgent** runs multiple live web searches (Anthropic's built-in
  server-side `web_search` tool) and hands off a structured list of sources
  + key points.
- **SummarizeAgent** organizes those into sectioned, cited claims.
- **FactCheckAgent** verifies each claim (re-searching when a claim looks
  risky) and splits them into verified vs. flagged.
- **DraftAgent** writes the final cited Markdown report from the verified
  (and clearly-labeled flagged) claims.

Each hand-off is a structured JSON payload passed to the next agent, and every
run's full trace (sources, summary, verdicts, hand-off log) is saved alongside
the final report for auditability.

Web search runs entirely on Anthropic's infrastructure — no separate search
API or key needed. Search usage is billed by Anthropic per search on top of
token costs.

> 📖 New here? See **[GETTING_STARTED.md](GETTING_STARTED.md)** for a full
> step-by-step walkthrough, troubleshooting, and cost notes.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Then create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=sk-ant-...
# CLAUDE_MODEL=claude-opus-4-8   # optional; set claude-sonnet-5 for cheaper runs
```

The only required key is `ANTHROPIC_API_KEY` (from the Anthropic Console).

## Run

```bash
python main.py "What are the latest advances in solid-state batteries?"
```

or run it interactively:

```bash
python main.py
```

Output goes to `reports/<slug>-<timestamp>.md` (the report) and
`reports/<slug>-<timestamp>.trace.json` (full pipeline trace: every source,
summary section, fact-check verdict, and hand-off note).

## Project layout

```
main.py                                CLI entry point
src/multi_research_agent/
  config.py       Env var loading (API key, model, tuning knobs)
  tools.py        Server-side web_search tool definition
  runtime.py      Claude agent runner (pause_turn resume, JSON extraction)
  state.py        ResearchState — the shared object passed between agents
  agents.py       The 4 agent system prompts + run_* functions
  orchestrator.py Wires the pipeline together, logs, saves output
```

## Extending

- **Add an agent**: write a `run_x_agent(state) -> state` function in
  `agents.py` with its own system prompt, then insert it into `PIPELINE` in
  `orchestrator.py`.
- **Swap the model per agent**: `run_agent()` in `runtime.py` accepts a
  `model=` override if you want, e.g., a cheaper/faster model for search and
  a stronger one for drafting. Default model is `claude-opus-4-8`; set
  `CLAUDE_MODEL=claude-sonnet-5` in `.env` for cheaper runs (both support
  the `web_search_20260209` tool).
- **Add a client-side tool**: define a schema + implementation and handle
  `stop_reason == "tool_use"` in `runtime.py`'s loop (server-side web search
  needs no such handling — its results arrive in the same response).

## License

MIT © 2026 Muzammil Abbas — see [LICENSE](LICENSE).
