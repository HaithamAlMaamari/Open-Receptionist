"""Business configuration loading and validation.

All business-specific data (name, hours, services, FAQ, greeting text
placeholders) lives in ``config/*.yaml`` — never hardcoded in prompts or
code. This module loads and validates that YAML into typed models the rest
of the agent consumes. Validation is strict (unknown keys rejected, human
phone required) so a typo cannot silently weaken a compliance default.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILENAME = "business.yaml"
EXAMPLE_FILENAME = "business.example.yaml"

SUPPORTED_LANGUAGES = ("ar", "en")

Weekday = Literal["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]

DAY_NAMES_AR: dict[str, str] = {
    "sunday": "الأحد",
    "monday": "الاثنين",
    "tuesday": "الثلاثاء",
    "wednesday": "الأربعاء",
    "thursday": "الخميس",
    "friday": "الجمعة",
    "saturday": "السبت",
}


class DayHours(BaseModel):
    """Opening hours for a single day of the week."""

    model_config = ConfigDict(extra="forbid")

    day: Weekday
    open: str | None = None
    close: str | None = None
    closed: bool = False

    @field_validator("day", mode="before")
    @classmethod
    def _normalize_day(cls, v: str) -> str:
        return v.strip().lower() if isinstance(v, str) else v


class Service(BaseModel):
    """A bookable/answerable service the business offers."""

    model_config = ConfigDict(extra="forbid")

    name_en: str = Field(min_length=1)
    name_ar: str = Field(min_length=1)
    description_en: str = ""
    description_ar: str = ""
    duration_minutes: int | None = None


class FaqEntry(BaseModel):
    """A frequently asked question in both languages."""

    model_config = ConfigDict(extra="forbid")

    question_en: str = Field(min_length=1)
    question_ar: str = Field(min_length=1)
    answer_en: str = Field(min_length=1)
    answer_ar: str = Field(min_length=1)


class BusinessConfig(BaseModel):
    """Validated, bilingual description of the business the agent represents."""

    model_config = ConfigDict(extra="forbid")

    name_en: str = Field(min_length=1)
    name_ar: str = Field(min_length=1)
    description_en: str = ""
    description_ar: str = ""
    timezone: str = "Asia/Dubai"
    default_language: str = "ar"
    languages: list[str] = Field(default_factory=lambda: list(SUPPORTED_LANGUAGES))
    # Required and non-empty: the path-to-a-human compliance default depends
    # on this number existing.
    human_phone: str = Field(min_length=5)
    hours: list[DayHours] = Field(default_factory=list)
    services: list[Service] = Field(default_factory=list)
    faq: list[FaqEntry] = Field(default_factory=list)

    @field_validator("default_language")
    @classmethod
    def _check_language(cls, v: str) -> str:
        if v not in SUPPORTED_LANGUAGES:
            raise ValueError(f"default_language must be one of {SUPPORTED_LANGUAGES}, got {v!r}")
        return v

    @field_validator("languages")
    @classmethod
    def _check_languages(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("languages must not be empty")
        unknown = [lang for lang in v if lang not in SUPPORTED_LANGUAGES]
        if unknown:
            raise ValueError(f"unsupported languages {unknown}; supported: {SUPPORTED_LANGUAGES}")
        return v

    @model_validator(mode="after")
    def _check_default_in_languages(self) -> BusinessConfig:
        if self.default_language not in self.languages:
            raise ValueError(
                f"default_language {self.default_language!r} must be listed in "
                f"languages {self.languages}"
            )
        return self

    def name(self, lang: str) -> str:
        return self.name_ar if lang == "ar" else self.name_en

    def description(self, lang: str) -> str:
        return self.description_ar if lang == "ar" else self.description_en

    def hours_text(self, lang: str) -> str:
        """Render opening hours as a plain-text block for prompt injection."""
        lines: list[str] = []
        for d in self.hours:
            day_name = DAY_NAMES_AR[d.day] if lang == "ar" else d.day
            if d.closed or not d.open or not d.close:
                lines.append(f"{day_name}: {'مغلق' if lang == 'ar' else 'closed'}")
            elif lang == "ar":
                lines.append(f"{day_name}: من {d.open} إلى {d.close}")
            else:
                lines.append(f"{day_name}: {d.open} to {d.close}")
        return "\n".join(lines)

    def services_text(self, lang: str) -> str:
        """Render the service list as a plain-text block for prompt injection."""
        lines: list[str] = []
        for s in self.services:
            name = s.name_ar if lang == "ar" else s.name_en
            desc = s.description_ar if lang == "ar" else s.description_en
            lines.append(f"- {name}" + (f": {desc}" if desc else ""))
        return "\n".join(lines)

    def faq_text(self, lang: str) -> str:
        """Render the FAQ as question/answer pairs for prompt injection."""
        q_label, a_label = ("السؤال", "الجواب") if lang == "ar" else ("Q", "A")
        lines: list[str] = []
        for f in self.faq:
            q = f.question_ar if lang == "ar" else f.question_en
            a = f.answer_ar if lang == "ar" else f.answer_en
            lines.append(f"{q_label}: {q}\n{a_label}: {a}")
        return "\n\n".join(lines)

    def bilingual_block(self, render: str) -> str:
        """Both language variants of a fact block, English then Arabic.

        ``render`` is one of ``hours``/``services``/``faq``. The system prompt
        grounds the LLM in BOTH languages so a caller in either language gets
        facts verbatim rather than machine-translated on the fly.
        """
        fn = {"hours": self.hours_text, "services": self.services_text, "faq": self.faq_text}[
            render
        ]
        en, ar = fn("en"), fn("ar")
        if not en and not ar:
            return ""
        return f"{en}\n\n{ar}"


def resolve_config_path(path: str | os.PathLike[str] | None = None) -> Path:
    """Resolve which business config file to load.

    Priority: explicit argument > $BUSINESS_CONFIG > business.yaml (current
    directory, then repo root) > business.example.yaml (same order, so the
    demo works out of the box).
    """
    if path is not None:
        return Path(path)
    env_path = os.getenv("BUSINESS_CONFIG")
    if env_path:
        return Path(env_path)
    candidates = [
        Path("config") / CONFIG_FILENAME,
        REPO_ROOT / "config" / CONFIG_FILENAME,
        Path("config") / EXAMPLE_FILENAME,
        REPO_ROOT / "config" / EXAMPLE_FILENAME,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[-1]


def load_business_config(path: str | os.PathLike[str] | None = None) -> BusinessConfig:
    """Load and validate the business YAML config."""
    resolved = resolve_config_path(path)
    if not resolved.exists():
        raise FileNotFoundError(
            f"Business config not found at {resolved}. "
            "Copy config/business.example.yaml to config/business.yaml and edit it."
        )
    with open(resolved, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"Business config at {resolved} is not a YAML mapping.")
    return BusinessConfig.model_validate(data)
