# Security Assessment Record

## Assessment

- **Project:** ActionSlate — Agentic Release Assurance
- **Assessment date:** September 9, 2026
- **Scope:** Python dependencies, FastAPI server, Gemini adapter, deterministic
  assurance logic, browser rendering, API boundaries, execution capability,
  security headers, tests, and the fixed Eclipse scenario
- **Architecture reviewed:** public simulation-only demonstration with no
  accounts, database, uploads, retrieval system, or real external action adapter

This is a point-in-time pre-submission assessment. It is committed as evidence
of the checks performed; it is not a claim of continuous monitoring or proof
that future revisions have no vulnerabilities.

## Replit security scans

The following scans were run from the Replit security environment against the
security-hardened source:

| Scan | Result |
|---|---|
| Replit dependency audit (`runDependencyAudit`) | 0 critical, 0 high, 0 moderate, 0 low, 0 informational |
| Replit static application security scan (`runSastScan`) | 0 findings |
| Replit HoundDog security/privacy dataflow scan (`runHoundDogScan`) | 0 findings |

The scanners are Replit-managed capabilities rather than repository command-line
dependencies, so they do not run in GitHub Actions. They should be rerun from
Replit after security-relevant code or dependency changes.

## OWASP AI/LLM review

An adversarial architecture review examined:

- prompt injection and instruction/data separation;
- sensitive information disclosure;
- model and dependency supply chain;
- improper model-output handling and browser injection;
- excessive agency and model overreliance;
- system-prompt leakage;
- retrieval and vector-store exposure;
- unbounded model consumption and denial of service;
- execution authorization and replay;
- simulation-boundary integrity.

The final review reported **PASS — no remaining concrete blocker** for the
current fixed-scenario, simulation-only architecture.

Important residual risks remain documented rather than hidden:

- process-local rate limits do not provide distributed edge DDoS protection;
- receipts are demonstrative and are not durable or cryptographically signed;
- the execution capability is appropriate for simulation, not a future real
  action adapter;
- any real adapter would require authenticated identity, action-level
  authorization, one-time capability consumption, shared replay protection,
  durable audit, and a new independent security assessment.

## Reproducible repository checks

Local development runs:

```bash
uv sync --locked
uv run python -m unittest discover -s tests -v
node --check app/static/app.js
```

Verified result at assessment time:

- 15 of 15 Python tests passed;
- JavaScript syntax passed;
- the locked dependency installation succeeded.

The tests cover deterministic `UNKNOWN` handling, safe-plan exclusion,
simulation-only receipts, structured interpretation, one bounded retry after a
transient invalid structured response, canonical request rejection, rate
limiting, output bounds, sanitized failures, browser security headers, HMAC
capability integrity, plan binding, tamper rejection, expiry, forged execution
rejection, and valid capability-gated simulation.

## Manual live validation

The following checks require the configured Replit secrets and therefore do not
run as part of the secret-free repository validation commands:

- real Gemini 2.5 Flash interpretation through Vertex AI;
- seven deterministic Eclipse evidence facts;
- Ava voice decision remains `UNKNOWN`;
- no credential fields in the response;
- forged execution capability returns `403`;
- valid assurance-bound execution returns `200`;
- receipt remains `SIMULATED` with no external side effects;
- browser flow completes without JavaScript or CSP errors;
- desktop and mobile layouts have no horizontal overflow.

## Related documentation

- [`README.md`](README.md) — product, architecture, usage, and verification
- [`threat_model.md`](threat_model.md) — assets, trust boundaries, threats, and
  required guarantees
- The commands above are the reproducible test and syntax-validation path.