"""Generic Claude agent runner, shared by every agent role.

Search-capable agents get Anthropic's server-side web_search tool: searches
run on Anthropic's side and results arrive in the same response, so the only
loop handling needed here is resuming `pause_turn` (the server-side tool loop
hit its iteration limit mid-turn).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

import anthropic

from . import config
from .tools import WEB_SEARCH_SERVER_TOOL

_client: anthropic.Anthropic | None = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        if not config.ANTHROPIC_API_KEY:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Add it to the .env file in the project root."
            )
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


@dataclass
class AgentResult:
    text: str
    tool_calls_made: int = 0
    transcript: list[dict[str, Any]] = field(default_factory=list)


def run_agent(
    system_prompt: str,
    user_message: str,
    use_web_search: bool = False,
    model: str | None = None,
    max_turns: int | None = None,
) -> AgentResult:
    """Run a single agent to completion.

    With use_web_search=True the model can call the server-side web_search
    tool; a turn that pauses (stop_reason "pause_turn") is resumed until the
    model produces a final answer or max_turns is exhausted.
    """
    client = get_client()
    model = model or config.CLAUDE_MODEL
    max_turns = max_turns or config.MAX_TOOL_TURNS

    messages: list[dict[str, Any]] = [{"role": "user", "content": user_message}]
    searches_made = 0

    kwargs: dict[str, Any] = dict(
        model=model,
        max_tokens=config.MAX_TOKENS,
        system=system_prompt,
        thinking={"type": "adaptive"},
        messages=messages,
    )
    if use_web_search:
        kwargs["tools"] = [WEB_SEARCH_SERVER_TOOL]

    for _ in range(max_turns):
        response = client.messages.create(**kwargs)

        searches_made += sum(
            1 for block in response.content if block.type == "server_tool_use"
        )

        if response.stop_reason == "pause_turn":
            # Server-side tool loop paused mid-turn; re-send to resume.
            messages.append({"role": "assistant", "content": response.content})
            kwargs["messages"] = messages
            continue

        if response.stop_reason == "refusal":
            return AgentResult(
                text="[Agent stopped: the request was refused for safety reasons.]",
                tool_calls_made=searches_made,
                transcript=messages,
            )

        final_text = "".join(
            block.text for block in response.content if block.type == "text"
        )
        messages.append({"role": "assistant", "content": response.content})
        return AgentResult(
            text=final_text,
            tool_calls_made=searches_made,
            transcript=messages,
        )

    return AgentResult(
        text="[Agent stopped: max turns reached before a final answer.]",
        tool_calls_made=searches_made,
        transcript=messages,
    )


def extract_json(text: str) -> Any:
    """Pull the first JSON object/array out of a model response.

    Agents are instructed to answer with a fenced ```json block; this also
    falls back to scanning for the first balanced {...} if fencing is missing.
    """
    fenced = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else None

    if candidate is None:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text[start : end + 1]

    if candidate is None:
        raise ValueError(f"No JSON found in agent response:\n{text}")

    return json.loads(candidate)
