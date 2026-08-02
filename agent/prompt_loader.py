"""Load and render prompt templates from ``agent/prompts/``.

Prompts live as files (ar + en variants), never as inline strings. Templates
use ``{placeholder}`` markers filled exclusively from the business config, so
no business fact is ever hardcoded in a prompt file. Rendering is tolerant:
only known placeholders are substituted, and any other braces in a template
(JSON examples, emphasis, contributor additions) pass through untouched
instead of crashing at call time.
"""

from __future__ import annotations

import re
from pathlib import Path

from agent.config import BusinessConfig

PROMPTS_DIR = Path(__file__).parent / "prompts"

_PLACEHOLDER = re.compile(r"\{([a-z_]+)\}")


def prompt_path(name: str, lang: str) -> Path:
    """Path to a prompt file, e.g. ``prompt_path('greeting', 'ar')``."""
    return PROMPTS_DIR / f"{name}_{lang}.txt"


def _substitutions(config: BusinessConfig, lang: str) -> dict[str, str]:
    return {
        "business_name": config.name(lang),
        "business_name_en": config.name_en,
        "business_name_ar": config.name_ar,
        "business_description": config.description(lang),
        # Fact blocks are ALWAYS bilingual: the LLM must be able to answer a
        # caller in either language from verbatim facts, not translations.
        "hours": config.bilingual_block("hours"),
        "services": config.bilingual_block("services"),
        "faq": config.bilingual_block("faq"),
        "human_phone": config.human_phone,
    }


def render_prompt(name: str, lang: str, config: BusinessConfig) -> str:
    """Read a prompt template and fill known placeholders from the config."""
    template = prompt_path(name, lang).read_text(encoding="utf-8")
    values = _substitutions(config, lang)

    def replace(match: re.Match[str]) -> str:
        return values.get(match.group(1), match.group(0))

    return _PLACEHOLDER.sub(replace, template)


def render_system_prompt(config: BusinessConfig, lang: str | None = None) -> str:
    """The system prompt for the LLM, in the business's default language
    variant, grounded with bilingual fact blocks."""
    return render_prompt("system", lang or config.default_language, config)


def render_greeting(config: BusinessConfig, lang: str | None = None) -> str:
    """The spoken greeting. MUST disclose the agent is an AI assistant."""
    return render_prompt("greeting", lang or config.default_language, config)


def render_greetings(config: BusinessConfig) -> list[str]:
    """Greetings for every configured language, default language first.

    Returned as separate utterances (one TTS frame each) so a multilingual
    voice never has to switch script mid-utterance.
    """
    ordered = [config.default_language] + [
        lang for lang in config.languages if lang != config.default_language
    ]
    return [render_greeting(config, lang) for lang in ordered]


def render_bilingual_greeting(config: BusinessConfig) -> str:
    """All greetings joined into one string (used for text/chat surfaces)."""
    return " ".join(render_greetings(config))
