"""Prompts must exist as ar+en files, render from config, and stay compliant."""

from __future__ import annotations

import pytest

import agent.prompt_loader as prompt_loader
from agent.config import SUPPORTED_LANGUAGES
from agent.prompt_loader import (
    prompt_path,
    render_bilingual_greeting,
    render_greeting,
    render_greetings,
    render_prompt,
    render_system_prompt,
)

PROMPT_NAMES = ("system", "greeting")


@pytest.mark.parametrize("name", PROMPT_NAMES)
@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_prompt_files_exist(name: str, lang: str) -> None:
    assert prompt_path(name, lang).exists(), f"missing prompt file {name}_{lang}.txt"


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_system_prompt_renders_business_facts(business_config, lang: str) -> None:
    prompt = render_system_prompt(business_config, lang)
    assert business_config.name(lang) in prompt
    assert business_config.human_phone in prompt
    assert "{business_name}" not in prompt, "unrendered placeholder left in prompt"


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_system_prompt_grounds_facts_in_both_languages(business_config, lang: str) -> None:
    """Milestone 1 DoD: FAQ answers reach the prompt — and in BOTH languages,
    whichever language variant of the template is used."""
    prompt = render_system_prompt(business_config, lang)
    assert business_config.faq[0].answer_en in prompt
    assert business_config.faq[0].answer_ar in prompt
    assert business_config.services[0].name_en in prompt
    assert business_config.services[0].name_ar in prompt
    assert business_config.hours_text("ar").splitlines()[0] in prompt


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_greeting_discloses_ai(business_config, lang: str) -> None:
    """Compliance default #1: the greeting always discloses this is an AI."""
    greeting = render_greeting(business_config, lang)
    disclosure = "مساعد ذكاء اصطناعي" if lang == "ar" else "AI assistant"
    assert disclosure in greeting
    assert business_config.name(lang) in greeting


@pytest.mark.parametrize("lang", SUPPORTED_LANGUAGES)
def test_greeting_offers_human_path(business_config, lang: str) -> None:
    """Compliance default #2: the greeting offers a path to a human."""
    greeting = render_greeting(business_config, lang)
    human_word = "الموظفين" if lang == "ar" else "team"
    assert human_word in greeting


def test_greetings_one_per_language_default_first(business_config) -> None:
    greetings = render_greetings(business_config)
    assert len(greetings) == len(business_config.languages)
    # Default language (Arabic in the example config) speaks first, and each
    # greeting is a single-language utterance carrying its own disclosure.
    assert "مساعد ذكاء اصطناعي" in greetings[0]
    assert "AI assistant" in greetings[1]
    assert "AI assistant" not in greetings[0]


def test_bilingual_greeting_joins_all_languages(business_config) -> None:
    greeting = render_bilingual_greeting(business_config)
    assert "مساعد ذكاء اصطناعي" in greeting
    assert "AI assistant" in greeting


def test_no_hardcoded_business_facts_in_prompt_files() -> None:
    """Prompt templates must reference config placeholders, never real facts."""
    for name in PROMPT_NAMES:
        for lang in SUPPORTED_LANGUAGES:
            raw = prompt_path(name, lang).read_text(encoding="utf-8")
            assert "{business_name}" in raw
            assert "Al Shifa" not in raw and "الشفاء" not in raw


def test_rendering_tolerates_unknown_placeholders_and_braces(
    business_config, tmp_path, monkeypatch
) -> None:
    """Contributor-added templates with JSON braces or unknown placeholders
    must render (untouched) instead of crashing at call time."""
    (tmp_path / "weird_en.txt").write_text(
        'Name: {business_name}. Example: {"a": 1}. Unknown: {not_a_placeholder}.',
        encoding="utf-8",
    )
    monkeypatch.setattr(prompt_loader, "PROMPTS_DIR", tmp_path)
    rendered = render_prompt("weird", "en", business_config)
    assert business_config.name_en in rendered
    assert '{"a": 1}' in rendered
    assert "{not_a_placeholder}" in rendered
