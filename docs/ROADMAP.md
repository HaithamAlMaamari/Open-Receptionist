# Roadmap

## Milestone 1 — Browser voice demo *(current)*

Talk to the receptionist from your browser: bilingual (Arabic + English)
greeting with AI disclosure, answers grounded in your `business.yaml`,
transcripts logged for both sides. Code complete; pending first live
verification against real STT/LLM/TTS keys.

## Milestone 2 — Real phone + booking

- Twilio number answers real calls (8 kHz mulaw transport)
- `book_appointment` via Cal.com, with spoken confirmation before committing
- `take_message`, `transfer_to_human`, `check_hours` tools
- Call logs and transcripts move from JSONL to Postgres
- FastAPI server joins docker-compose

## Milestone 3 — Chat widget, WhatsApp, admin

- Embeddable web chat widget (same brain, over WebSocket)
- WhatsApp transport
- Admin page: calls, leads, bookings
- Missed call → automatic SMS/WhatsApp text-back (inbound recovery only)

## Milestone 4 — Arabic QA + v0.1.0 release

- Full Arabic test suite: dialect detection (Gulf/Egyptian/MSA),
  code-switching, entity extraction (names, numbers, dates, times),
  politeness, fallback-to-human — with a published scorecard
- Fresh-clone-to-working-demo in under 10 minutes, verified
- Demo video, CHANGELOG, tagged release, contributor guide

## Principles that don't change

- Provider-agnostic: every STT/LLM/TTS vendor stays swappable via `.env`
- Config-driven: all business facts live in one YAML file
- Compliance by default: AI disclosure, human escape route, transcript
  logging — non-negotiable
- Inbound only: no outbound cold-calling features, ever
