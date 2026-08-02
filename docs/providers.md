# Swapping AI providers

Open Receptionist never calls a vendor SDK from pipeline logic. Each vendor
sits behind one of three interfaces in `agent/providers/base.py`:

- `STTProvider.create_service(language=...)`
- `LLMProvider.create_service(model=...)`
- `TTSProvider.create_service(voice=...)`

Selection is env-driven (see `.env.example`):

```bash
STT_PROVIDER=deepgram
LLM_PROVIDER=anthropic
TTS_PROVIDER=elevenlabs
```

## Adding a provider

1. Create `agent/providers/<vendor>.py` implementing the right interface.
   Import the vendor's pipecat service **inside** `create_service` (lazy), so
   the package imports cleanly without that vendor's extras installed.
2. Register it in `agent/providers/registry.py` (or call
   `register_stt_provider("myvendor", MyVendorSTT)` from your own code).
3. Add any new env variables to `.env.example` with comments.
4. Add a test in `tests/test_providers.py` (a fake service class in
   `tests/fakes.py` keeps it keyless).
5. For bilingual quality: STT must support Arabic + English (ideally
   code-switching); TTS needs a multilingual voice/model.

That's the whole definition of done — one file, one registry line, env docs,
one test.
