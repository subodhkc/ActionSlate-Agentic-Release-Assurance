# ActionSlate — Agentic Release Assurance

ActionSlate demonstrates a control boundary for consequential media agents:

> The agent can execute more than the available evidence authorizes.

The P0 uses the **Eclipse Protocol** release scenario to turn a producer's
compound request into a structured plan, compare every consequential argument
with evidence, preserve the supported subset, and issue a simulation-only
Greenlight Receipt.

## Live flow

```text
Producer request
  → Google Gen AI SDK
  → Gemini on Vertex AI
  → typed action interpretation
  → seeded evidence lookup
  → deterministic Greenlight evaluation
  → Greenlight Diff
  → Safe Executable Plan
  → simulated execution
  → Greenlight Receipt
```

Gemini performs semantic discovery and decomposition. It does **not** authorize
actions. The final ALLOW, REVIEW, BLOCK, and UNKNOWN boundary is ordinary,
inspectable Python logic in `app/assurance.py`. UNKNOWN is never treated as
approval.

## P0 evidence pack

The demonstration intentionally uses only the evidence needed for one clear
scenario:

- V12 is the approved release master; V13 remains internal review.
- US and Canada are currently authorized.
- France, Spain, and GLOBAL distribution are outside the current window.
- Tonight is outside the current release/embargo window.
- Ava's trailer-specific digital voice use is not established.
- Autonomous campaign spend is limited to $5,000.
- Generated and localized derivatives require provenance.

The safe plan stages V12, constrains the release plan to US and Canada, and
caps the campaign envelope at $5,000. It excludes unsupported territories,
assets, voice use, and spend. Execution is simulated; no publishing, voice
generation, or ad buying occurs.

## Google runtime

- SDK: `google-genai`
- Model: `gemini-2.5-flash`
- Vertex AI mode: enabled
- Project: `actionslate`
- Location: `global`
- Authentication: `GOOGLE_API_KEY` from Replit Secrets
- Structured output: Pydantic response schema

The API key is never returned to the browser, logged, or committed.

## Run on Replit

Add this Replit Secret:

```text
GOOGLE_API_KEY
```

Then start the configured workflow or run:

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 5000
```

Open the web preview. The one-page experience runs the Eclipse assurance
scenario through Gemini and renders the Greenlight Diff. Select **Apply safe
plan** to produce the simulation-only receipt.

## API checks

Health:

```bash
curl http://localhost:5000/health
```

Full assurance flow:

```bash
curl -X POST http://localhost:5000/api/assure \
  -H 'content-type: application/json' \
  -d '{"producer_request":"Launch the Eclipse Protocol trailer worldwide tonight. Localize it for France and Spain using Ava'\''s voice, then maximize paid reach."}'
```

Simulated safe-plan execution:

```bash
curl -X POST http://localhost:5000/api/execute \
  -H 'content-type: application/json' \
  -d '{"plan_id":"eclipse-safe-plan"}'
```

Tests:

```bash
uv run python -m unittest discover -s tests -v
```

## Scope and compliance boundary

ActionSlate is a standalone clean-room project. It does not import or depend on
HAIEC code, packages, datasets, or runtime artifacts. P0 intentionally excludes
databases, user accounts, real publishing, real ad buying, real voice
generation, C2PA cryptographic integration, and additional scenarios.

## License

MIT. See `LICENSE`.