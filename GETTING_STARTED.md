# Getting Started

A step-by-step guide to setting up and running the Multi-Agent Research
Assistant on your machine. No prior experience with the project needed.

## What this project does

You give it a research question. Four AI agents then work on it in sequence,
each handing its output to the next:

1. **SearchAgent** — runs several live web searches and collects sources
2. **SummarizeAgent** — organizes the findings into sections with citations
3. **FactCheckAgent** — verifies every claim, re-searching the web for
   anything that looks doubtful, and flags what it can't confirm
4. **DraftAgent** — writes the final research report in Markdown, citing
   only verified claims

You get back a cited report plus a JSON trace showing exactly what every
agent found, claimed, verified, and flagged.

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.10+ | Check with `python --version` |
| An Anthropic API key | Sign up at [platform.claude.com](https://platform.claude.com), add billing, and create a key under **API Keys**. Keys look like `sk-ant-...` |
| Internet connection | Web search runs through Anthropic's servers |

There is **no separate search API to sign up for** — web search is built into
the Claude API and billed by Anthropic alongside token usage.

## Setup (one time)

Open a terminal (PowerShell on Windows) in the project folder and run:

```powershell
# 1. Create a virtual environment
python -m venv .venv

# 2. Activate it
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt
```

Then create a file named `.env` in the project root (same folder as
`main.py`) with your API key:

```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Optional settings you can also put in `.env`:

```
CLAUDE_MODEL=claude-sonnet-5   # cheaper/faster than the default claude-opus-4-8
MAX_TOKENS=16000               # max output tokens per agent call
MAX_TOOL_TURNS=6               # max resume attempts per agent turn
```

> ⚠️ Never commit `.env` or share your key. The included `.gitignore`
> already excludes it.

## Running a research task

From the project folder, with the virtual environment activated:

```powershell
python main.py "What are the latest advances in solid-state batteries?"
```

Or run it without arguments and type your topic when prompted:

```powershell
python main.py
```

(If you didn't activate the venv, use `.venv\Scripts\python main.py ...`
instead of `python main.py ...`.)

### What you'll see

The terminal shows each hand-off as it happens:

```
+---------------------------------------------------+
| Research topic: ...                               |
+---------------------------------------------------+
-> running SearchAgent...
SearchAgent -> SummarizeAgent: Collected 6 sources via 4 search calls.
-> running SummarizeAgent...
SummarizeAgent -> FactCheckAgent: Produced 4 summary sections.
-> running FactCheckAgent...
FactCheckAgent -> DraftAgent: Verified 14 claims, flagged 2.
-> running DraftAgent...
DraftAgent -> User: Final report written.
```

followed by the full report rendered in the terminal.

### Where output is saved

Every run writes two files into the `reports/` folder:

| File | Contents |
|---|---|
| `<topic>-<timestamp>.md` | The final research report (Markdown, with a Sources section) |
| `<topic>-<timestamp>.trace.json` | Full pipeline trace: every source, summary section, fact-check verdict, and hand-off note |

The trace file is the audit trail — if a claim in the report looks off, you
can see which source it came from and what the fact-checker said about it.

## How it works (for the curious)

- Each agent is a separate Claude conversation with its own system prompt
  (see `src/multi_research_agent/agents.py`).
- Agents pass structured JSON between each other — not free text — so each
  stage can be validated and inspected (`state.py` holds the shared state).
- Search and fact-check agents use Anthropic's **server-side web search
  tool**: searches execute on Anthropic's infrastructure and results come
  back in the same API response (`tools.py`, `runtime.py`).
- The orchestrator (`orchestrator.py`) runs the pipeline in order, logs each
  hand-off, and saves the report + trace.

## Typical cost per run

A run makes 4+ API calls (one per agent, more if turns pause and resume) and
a handful of web searches. With the default Opus model expect roughly
$0.10–$0.50 per research task depending on topic depth; using
`CLAUDE_MODEL=claude-sonnet-5` roughly halves token costs. Web searches are
billed separately per search by Anthropic.

## Troubleshooting

| Problem | Fix |
|---|---|
| `Error: ANTHROPIC_API_KEY is not set` | Create/edit `.env` in the project root; make sure the line is `ANTHROPIC_API_KEY=sk-ant-...` with no quotes and no spaces around `=` |
| `authentication_error` (401) | The key is wrong or revoked — generate a new one in the Anthropic Console |
| `rate_limit_error` (429) | You're sending requests too fast or hit a usage cap — wait a minute and retry, or check your plan limits |
| `No JSON found in agent response` | An agent answered in prose instead of JSON (rare) — re-run the task; if it persists for one topic, try rephrasing it |
| Report seems thin / few sources | Try a more specific topic, or raise `max_uses` in `src/multi_research_agent/tools.py` to allow more searches |
| `python` not found on Windows | Install Python from python.org and check "Add to PATH", or use the full path to `.venv\Scripts\python.exe` |

## Extending the project

- **Add a fifth agent** (e.g. a critic or an outline planner): write a
  `run_x_agent(state) -> state` function in `agents.py`, then add it to
  `PIPELINE` in `orchestrator.py`.
- **Use different models per agent**: pass `model="claude-haiku-4-5"` (for
  example) to `run_agent()` inside any agent function — cheap models for
  search, strong ones for drafting.
- **Change how many searches agents may run**: edit `max_uses` in
  `tools.py`.
