# Running the demo

## Dependencies

```bash
pip install fastapi uvicorn pypdf reportlab
# plus an OpenAI-compatible client if you want LLM extraction
pip install openai python-dotenv
```

Provider keys go in `.env` (gitignored). Auto-detect order:

1. `NVIDIA_API_KEY`
2. `OPENROUTER_API_KEY`
3. `ANTHROPIC_API_KEY`

Without a key, the deterministic parser still runs and the demo works.

## Private credit (primary)

```bash
python3 credit_corpus.py     # build synthetic agreement + notice traffic
python3 app.py               # → http://localhost:8000
```

CLI, no server:

```bash
python3 facility.py
```

## LP-side fund ops (second surface)

Out of the primary demo UI on purpose — one product on screen.

```bash
python3 app_alts_lp.py
```

## Notes on the corpus

`credit_corpus.py` generates **synthetic** documents with a real pricing grid, CSA tiers, Actual/360, and deliberately seeded defects. It is a test harness, not customer paper. Real credit agreements are confidential.
