# Open Receptionist

[![CI](https://github.com/HaithamAlMaamari/Open-Receptionist/actions/workflows/ci.yml/badge.svg)](https://github.com/HaithamAlMaamari/Open-Receptionist/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](pyproject.toml)

Open-source **bilingual (Arabic + English)** AI phone receptionist + chatbot for small businesses. It answers calls, chats with customers, books appointments, and always offers a path to a human — with compliance-safe defaults out of the box.

> **Status: Milestone 1, code complete — pending first live run.** The browser-mic demo (bilingual greeting, answers grounded in your business config) is built and unit-tested offline; it has not yet been exercised against live STT/LLM/TTS keys, so expect rough edges until the first-light checklist below is done. Real phone numbers (Twilio), Cal.com booking, WhatsApp, and the admin dashboard land in the next milestones — see the [roadmap](docs/ROADMAP.md).

## Why

There is no polished, Arabic-first, self-hostable AI receptionist. English-only proprietary tools dominate. Open Receptionist is provider-agnostic (swap STT/LLM/TTS via `.env`), config-driven (all business facts in one YAML), and ships compliant defaults: the agent **always discloses it is an AI**, **always offers a human**, and **always logs the transcript**.

## Quickstart (local, ~5 minutes)

Requirements: Python 3.11+, API keys for Deepgram, Anthropic, and ElevenLabs.

```bash
git clone https://github.com/HaithamAlMaamari/Open-Receptionist.git && cd Open-Receptionist
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

cp .env.example .env         # fill in the three API keys + a voice id
cp config/business.example.yaml config/business.yaml   # optional: edit your business

python agent/bot.py
```

Open **http://localhost:7860/client**, allow the microphone, and say hello — in Arabic, English, or both in the same sentence.

## Quickstart (Docker)

```bash
cp .env.example .env   # fill in keys
docker compose up
```

## Run the tests (no API keys needed)

```bash
pip install -e ".[dev]"
pytest
ruff check .
```

The unit suite runs fully offline against a fake pipecat runtime — useful for fast, keyless CI, but it cannot prove live-call behavior. On a machine with `pipecat-ai` installed, `RUN_PIPECAT_INTEGRATION=1 pytest` additionally smoke-tests the real pipecat import surface (CI runs both jobs on every push).

### First-light checklist (closing Milestone 1)

1. Fill the three keys + voice id in `.env`, then `python -m agent.bot`.
2. Open `http://localhost:7860/client`, speak Arabic, then English, then a mixed sentence.
3. Confirm: the greeting discloses the AI in both languages; answers match your `business.yaml`; a transcript JSONL with both `caller` and `agent` lines appears under `logs/transcripts/`.
4. Pin the exact working `pipecat-ai` version in `pyproject.toml`.

## Configure your business

Everything the agent may say about your business lives in `config/business.yaml` (see the dental-clinic example in `config/business.example.yaml`): name, hours, services, FAQ — all in Arabic **and** English. Prompts live in `agent/prompts/` as `_ar`/`_en` file pairs and only ever reference config placeholders.

## Swap providers

Set `STT_PROVIDER` / `LLM_PROVIDER` / `TTS_PROVIDER` in `.env`. Every vendor sits behind an interface in `agent/providers/` — adding a provider is one small file plus a registry entry (see [docs/providers.md](docs/providers.md)).

## Compliance defaults (non-negotiable)

1. The greeting always discloses the agent is an AI assistant (EU AI Act transparency obligations apply from Aug 2026; the US FCC treats AI voices as artificial under robocall rules). It is spoken verbatim from the prompt files — never LLM-generated — so it cannot be paraphrased away.
2. Callers can always reach a human (the number is required config — the agent will not start without one).
3. Both sides of every conversation are transcript-logged (JSONL in Milestone 1, Postgres from Milestone 2). Transcripts contain personal data: obtain any consent required for call recording/transcription in your jurisdiction, disclose it to callers where mandated, and set a retention policy. Never commit transcripts or audio.
4. Inbound + missed-call text-back only. No outbound cold-calling features — ever.

## License

[MIT](LICENSE)
