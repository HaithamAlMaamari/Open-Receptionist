# Quickstart

## 1. Prerequisites

- Python 3.11+ (or Docker)
- API keys: [Deepgram](https://console.deepgram.com/) (STT), [Anthropic](https://console.anthropic.com/) (LLM), [ElevenLabs](https://elevenlabs.io/) (TTS)
- An ElevenLabs **voice id** for a voice that handles Arabic and English well (the multilingual model is the default)

## 2. Configure

```bash
cp .env.example .env                                   # add your keys
cp config/business.example.yaml config/business.yaml   # describe your business
```

`config/business.yaml` is the single source of truth for everything the agent may claim about the business — name, hours, services, FAQ, human phone number — in both Arabic and English. If it doesn't exist, the shipped dental-clinic example is used so the demo works immediately.

## 3. Run

Local:

```bash
pip install -e ".[dev]"
python agent/bot.py
```

Docker:

```bash
docker compose up
```

Then open <http://localhost:7860/client>, allow microphone access, and talk. The agent greets in Arabic then English (order follows `default_language`), discloses that it is an AI, and answers only from your config.

## 4. Verify

```bash
pytest          # unit suite — needs no API keys, no pipecat install
ruff check .    # lint
```

## Troubleshooting

- **No greeting audio** — check `ELEVENLABS_VOICE_ID` is set and valid.
- **Docker: client connects but no audio** — WebRTC media runs over UDP, which Docker Desktop (Windows/macOS) does not forward with a plain port mapping. Run the agent directly on the host (`python -m agent.bot`) for local demos, or on Linux use `network_mode: host` in `docker-compose.yml`.
- **Agent doesn't understand Arabic** — Deepgram Nova-3 supports Arabic; the default is code-switching mode (`language=multi`). If your dialect underperforms, set `DEEPGRAM_LANGUAGE=ar` in `.env` and re-test with real callers before launch.
- **Wrong business facts** — the agent only knows what's in your `business.yaml`; edit it and restart.
- **Port in use** — the dev runner defaults to 7860; pass `--port` (and `--host`) to `python -m agent.bot`.
