"""The business config must load, validate strictly, and expose bilingual data."""

from __future__ import annotations

import pytest

from agent.config import (
    SUPPORTED_LANGUAGES,
    BusinessConfig,
    load_business_config,
    resolve_config_path,
)
from tests.conftest import EXAMPLE_CONFIG

VALID_MINIMAL = {
    "name_en": "X Clinic",
    "name_ar": "عيادة س",
    "human_phone": "+971 4 555 0100",
}


def test_example_config_loads(business_config: BusinessConfig) -> None:
    assert business_config.name_en
    assert business_config.name_ar
    assert business_config.default_language in SUPPORTED_LANGUAGES
    assert set(business_config.languages) == set(SUPPORTED_LANGUAGES)
    assert business_config.human_phone


def test_example_config_is_bilingual_everywhere(business_config: BusinessConfig) -> None:
    """Every service and FAQ entry must have both Arabic and English text."""
    assert business_config.services, "example config should ship with services"
    assert business_config.faq, "example config should ship with FAQ entries"
    for service in business_config.services:
        assert service.name_en and service.name_ar
    for entry in business_config.faq:
        assert entry.question_en and entry.question_ar
        assert entry.answer_en and entry.answer_ar


def test_hours_cover_every_day(business_config: BusinessConfig) -> None:
    days = {h.day for h in business_config.hours}
    assert len(days) == 7, f"expected all 7 days configured, got {sorted(days)}"


def test_text_renderers_are_localized(business_config: BusinessConfig) -> None:
    for lang in SUPPORTED_LANGUAGES:
        assert business_config.hours_text(lang)
        assert business_config.services_text(lang)
        assert business_config.faq_text(lang)
    ar_hours = business_config.hours_text("ar")
    en_hours = business_config.hours_text("en")
    # Arabic day names and connectors in the Arabic block — no raw English
    # weekday tokens, no en-dash (poor TTS token / RTL-LTR trap).
    assert "الأحد" in ar_hours and "الجمعة" in ar_hours
    assert "sunday" not in ar_hours
    assert "مغلق" in ar_hours and "إلى" in ar_hours
    assert "closed" in en_hours and " to " in en_hours
    assert "–" not in ar_hours and "–" not in en_hours


def test_bilingual_block_contains_both_languages(business_config: BusinessConfig) -> None:
    faq_block = business_config.bilingual_block("faq")
    assert business_config.faq[0].answer_en in faq_block
    assert business_config.faq[0].answer_ar in faq_block


def test_invalid_default_language_rejected() -> None:
    with pytest.raises(ValueError):
        BusinessConfig(**VALID_MINIMAL, default_language="fr")


def test_default_language_must_be_in_languages() -> None:
    with pytest.raises(ValueError, match="must be listed in"):
        BusinessConfig(**VALID_MINIMAL, default_language="ar", languages=["en"])


def test_unknown_keys_rejected() -> None:
    """A typo like `human_phon` must fail loudly, not silently weaken the
    path-to-a-human compliance default."""
    bad = dict(VALID_MINIMAL)
    bad["human_phon"] = bad.pop("human_phone")
    with pytest.raises(ValueError):
        BusinessConfig(**bad)


def test_human_phone_required_non_empty() -> None:
    bad = dict(VALID_MINIMAL, human_phone="")
    with pytest.raises(ValueError):
        BusinessConfig(**bad)


def test_invalid_weekday_rejected() -> None:
    with pytest.raises(ValueError):
        BusinessConfig(**VALID_MINIMAL, hours=[{"day": "sundy", "closed": True}])


def test_missing_config_raises_helpful_error(tmp_path) -> None:
    with pytest.raises(FileNotFoundError, match="business.example.yaml"):
        load_business_config(tmp_path / "nope.yaml")


def test_resolve_path_env_override(monkeypatch, tmp_path) -> None:
    target = tmp_path / "custom.yaml"
    monkeypatch.setenv("BUSINESS_CONFIG", str(target))
    assert resolve_config_path() == target


def test_explicit_path_wins(monkeypatch) -> None:
    monkeypatch.setenv("BUSINESS_CONFIG", "somewhere/else.yaml")
    assert resolve_config_path(EXAMPLE_CONFIG) == EXAMPLE_CONFIG


def test_resolve_finds_example_from_any_cwd(monkeypatch, tmp_path) -> None:
    """Config discovery must not depend on the process working directory."""
    monkeypatch.delenv("BUSINESS_CONFIG", raising=False)
    monkeypatch.chdir(tmp_path)
    resolved = resolve_config_path()
    assert resolved.exists(), f"expected repo-anchored fallback, got {resolved}"
    assert resolved.name in ("business.yaml", "business.example.yaml")
