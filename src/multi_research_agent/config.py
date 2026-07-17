import os

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-4-8")

MAX_TOOL_TURNS = int(os.environ.get("MAX_TOOL_TURNS", "6"))
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "16000"))
