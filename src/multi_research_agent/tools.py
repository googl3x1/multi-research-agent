"""Tool definitions available to agents.

Web search uses Anthropic's server-side web_search tool: it executes on
Anthropic's infrastructure and its results arrive as content blocks in the
same response, so there is no client-side implementation or API key needed.
"""

WEB_SEARCH_SERVER_TOOL = {
    "type": "web_search_20260209",
    "name": "web_search",
    "max_uses": 8,
}
