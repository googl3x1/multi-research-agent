"""The four research agents. Each reads the shared state, does its job with
its own system prompt (and tools, where relevant), and hands off structured
output to the next agent in the pipeline.
"""

from __future__ import annotations

from .runtime import extract_json, run_agent
from .state import ResearchState

# ---------------------------------------------------------------------------
# 1. Search agent
# ---------------------------------------------------------------------------

SEARCH_SYSTEM_PROMPT = """\
You are the Search Agent in a multi-agent research pipeline. Your only job is \
to gather raw material on the user's research topic using the web_search tool, \
then hand off structured findings to a Summarize Agent.

Guidelines:
- Issue several distinct search queries (different phrasings, subtopics, or \
angles) rather than one broad query. Aim for 2-5 tool calls.
- Prefer primary sources and recent, credible material.
- Do not summarize or analyze yet -- that is the next agent's job. Just collect.

When you are done searching, respond with ONLY a fenced ```json block matching \
this schema, and nothing else:

{
  "sources": [
    {"id": "S1", "title": "...", "url": "...", "key_points": ["...", "..."]}
  ],
  "raw_notes": "Any additional context or caveats about the search coverage, \
e.g. gaps or conflicting info."
}

Each source must get a short unique id (S1, S2, ...) so later agents can cite it.\
"""


def run_search_agent(state: ResearchState) -> ResearchState:
    user_message = f"Research topic: {state.topic}"
    result = run_agent(SEARCH_SYSTEM_PROMPT, user_message, use_web_search=True)
    data = extract_json(result.text)

    state.sources = data.get("sources", [])
    state.raw_notes = data.get("raw_notes", "")
    state.search_tool_calls = result.tool_calls_made
    state.log_handoff(
        "SearchAgent",
        "SummarizeAgent",
        f"Collected {len(state.sources)} sources via {result.tool_calls_made} search calls.",
    )
    return state


# ---------------------------------------------------------------------------
# 2. Summarize agent
# ---------------------------------------------------------------------------

SUMMARIZE_SYSTEM_PROMPT = """\
You are the Summarize Agent in a multi-agent research pipeline. You receive raw \
sources and key points collected by a Search Agent. Your job is to organize them \
into a clear, well-structured summary grouped by subtopic, with every claim \
traceable to a source id.

Guidelines:
- Group related points into named sections (e.g. "Background", "Current State", \
"Risks", "Outlook") -- whatever sections fit the topic.
- Every bullet point must cite the source id(s) it came from, e.g. [S1], [S2].
- Do not invent facts not present in the provided sources or raw notes.
- Be concise. This is an intermediate artifact for a fact-checker, not prose.

Respond with ONLY a fenced ```json block matching this schema, and nothing else:

{
  "summary_sections": [
    {
      "heading": "...",
      "points": [
        {"claim": "...", "source_ids": ["S1", "S2"]}
      ]
    }
  ]
}\
"""


def run_summarize_agent(state: ResearchState) -> ResearchState:
    user_message = (
        f"Research topic: {state.topic}\n\n"
        f"Sources (JSON):\n{state.sources}\n\n"
        f"Search agent's raw notes:\n{state.raw_notes or '(none)'}"
    )
    result = run_agent(SUMMARIZE_SYSTEM_PROMPT, user_message)
    data = extract_json(result.text)

    state.summary_sections = data.get("summary_sections", [])
    state.log_handoff(
        "SummarizeAgent",
        "FactCheckAgent",
        f"Produced {len(state.summary_sections)} summary sections.",
    )
    return state


# ---------------------------------------------------------------------------
# 3. Fact-check agent
# ---------------------------------------------------------------------------

FACTCHECK_SYSTEM_PROMPT = """\
You are the Fact-Check Agent in a multi-agent research pipeline. You receive a \
structured summary (claims + cited source ids) built by a Summarize Agent, along \
with the original sources. Your job is to verify each claim.

Guidelines:
- For claims that look uncertain, surprising, or high-stakes, use the web_search \
tool to independently verify them before deciding.
- A claim is "verified" if it is well-supported by its cited sources (and, if you \
searched, corroborated elsewhere).
- A claim is "flagged" if it is unsupported by its cited source, contradicted by \
other evidence you find, outdated, or overly speculative. Explain why.
- Do not rewrite the draft -- that is the next agent's job. Just judge each claim.

Respond with ONLY a fenced ```json block matching this schema, and nothing else:

{
  "verified_claims": [
    {"claim": "...", "source_ids": ["S1"], "confidence": "high|medium"}
  ],
  "flagged_claims": [
    {"claim": "...", "source_ids": ["S1"], "issue": "why this is flagged"}
  ]
}\
"""


def run_factcheck_agent(state: ResearchState) -> ResearchState:
    user_message = (
        f"Research topic: {state.topic}\n\n"
        f"Sources (JSON):\n{state.sources}\n\n"
        f"Summary to verify (JSON):\n{state.summary_sections}"
    )
    result = run_agent(FACTCHECK_SYSTEM_PROMPT, user_message, use_web_search=True)
    data = extract_json(result.text)

    state.verified_claims = data.get("verified_claims", [])
    state.flagged_claims = data.get("flagged_claims", [])
    state.factcheck_tool_calls = result.tool_calls_made
    state.log_handoff(
        "FactCheckAgent",
        "DraftAgent",
        f"Verified {len(state.verified_claims)} claims, flagged {len(state.flagged_claims)}.",
    )
    return state


# ---------------------------------------------------------------------------
# 4. Draft agent
# ---------------------------------------------------------------------------

DRAFT_SYSTEM_PROMPT = """\
You are the Draft Agent, the last step in a multi-agent research pipeline. You \
receive verified claims, flagged claims, and the original sources. Your job is \
to write the final research report for the end user.

Guidelines:
- Write clear, well-organized Markdown with headings.
- Build the report primarily from verified claims. You may mention a flagged \
claim only if it is important context, and you must note that it is disputed \
or unverified and why.
- Cite sources inline like [S1] and include a "Sources" section at the end \
listing each source id with its title and URL.
- Do not use JSON for this response -- respond with plain Markdown only.\
"""


def run_draft_agent(state: ResearchState) -> ResearchState:
    user_message = (
        f"Research topic: {state.topic}\n\n"
        f"Verified claims (JSON):\n{state.verified_claims}\n\n"
        f"Flagged claims (JSON):\n{state.flagged_claims}\n\n"
        f"Sources (JSON):\n{state.sources}"
    )
    result = run_agent(DRAFT_SYSTEM_PROMPT, user_message)

    state.draft_markdown = result.text.strip()
    state.log_handoff("DraftAgent", "User", "Final report written.")
    return state
