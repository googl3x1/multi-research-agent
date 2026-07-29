import os

from dotenv import dotenv_values, load_dotenv

load_dotenv()

# Values as they appear in .env, kept separately so a blank environment
# variable cannot shadow a real setting: load_dotenv() leaves existing
# variables alone, so an exported-but-empty ANTHROPIC_API_KEY would
# otherwise win over the key the user actually configured.
_FILE_VALUES = dotenv_values()


def _setting(name: str, default: str = "") -> str:
    """Read a setting, treating a blank environment variable as unset."""
    from_env = os.environ.get(name, "").strip()
    if from_env:
        return from_env
    return (_FILE_VALUES.get(name) or "").strip() or default


ANTHROPIC_API_KEY = _setting("ANTHROPIC_API_KEY")
CLAUDE_MODEL = _setting("CLAUDE_MODEL", "claude-opus-4-8")

MAX_TOOL_TURNS = int(_setting("MAX_TOOL_TURNS", "6"))
MAX_TOKENS = int(_setting("MAX_TOKENS", "16000"))
