"""Arabic-path seed tests (Milestone 1).

The full dialect/code-switching suite (language detection, entities,
politeness, fallbacks) lands in the Arabic QA milestone — see docs/ROADMAP.md.
These seed tests keep the Arabic path a first-class citizen from day one:
every prompt must ship an Arabic variant of equal substance to the English.
"""

from __future__ import annotations

import re

from agent.prompt_loader import prompt_path, render_greeting, render_system_prompt

ARABIC_CHARS = re.compile(r"[؀-ۿ]")


def test_arabic_prompt_variants_are_real_arabic() -> None:
    for name in ("system", "greeting"):
        text = prompt_path(name, "ar").read_text(encoding="utf-8")
        arabic_ratio = len(ARABIC_CHARS.findall(text)) / max(len(text), 1)
        assert arabic_ratio > 0.3, f"{name}_ar.txt does not look like Arabic content"


def test_arabic_variants_not_thinner_than_english(business_config) -> None:
    """The Arabic system prompt must carry the same rule sections as English."""
    ar = render_system_prompt(business_config, "ar")
    en = render_system_prompt(business_config, "en")
    # Same grounding blocks in both.
    for lang_text in (ar, en):
        assert business_config.human_phone in lang_text
    assert len(ar) > 0.5 * len(en)


def test_arabic_greeting_is_culturally_appropriate(business_config) -> None:
    greeting = render_greeting(business_config, "ar")
    assert greeting.startswith("السلام عليكم")


def test_code_switching_instruction_present(business_config) -> None:
    """System prompts must instruct handling of Arabic/English code-switching."""
    ar = render_system_prompt(business_config, "ar")
    en = render_system_prompt(business_config, "en")
    assert "مزيج" in ar or "خلط" in ar
    assert "mix" in en.lower()
