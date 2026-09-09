# Threat Model

## Project Overview

ActionSlate is a public, single-scenario FastAPI demonstration of a control
boundary for consequential media agents. A browser sends one fixed producer
command to a server-side Gemini 2.5 Flash interpreter through `google-genai`.
Typed model output is passed to deterministic Python evidence evaluation. The
resulting safe subset can only create a simulation receipt; the project has no
external publishing, advertising, voice-generation, database, account, upload,
or payment integration.

## Assets

- **Google API credential and quota** — the server-side key must remain secret,
  and public traffic must not be able to consume unbounded model quota.
- **Assurance integrity** — Gemini output must not determine authorization or
  convert missing evidence into approval.
- **Demo availability** — a judge must be able to complete the live
  request-to-receipt flow despite accidental or hostile replay traffic.
- **Browser integrity** — model-generated text must not execute as HTML,
  JavaScript, URLs, or browser capabilities.
- **Simulation boundary** — no code path may create a real external side effect.

## Trust Boundaries

- **Public browser to FastAPI** — all client input is untrusted. Read-only UI
  controls are not security controls; the API enforces the fixed request.
- **FastAPI to Gemini** — model output is untrusted semantic data even when it
  conforms to JSON structure.
- **Gemini interpretation to deterministic assurance** — the model proposes
  actions and provenance; it never supplies evidence or policy decisions.
- **Safe plan to simulation receipt** — a short-lived, signed capability binds
  the request to a successful assurance response. Its only effect is generating
  an in-memory, explicitly simulated receipt.
- **Runtime to Replit Secrets** — credentials are read server-side and must
  never cross into responses, logs, source control, or prompts.

## Scan Anchors

- Production entry point: `app/main.py`
- Highest-risk boundary: `app/agent.py` and `POST /api/assure`
- Deterministic authorization and simulation boundary: `app/assurance.py`
- Untrusted model-output rendering: `app/static/app.js`
- Public surfaces: `/`, `/static/*`, `/health`, `/api/demo`, `/api/assure`,
  `/api/execute`, and generated API documentation
- There are no authenticated or administrative surfaces.

## Threat Categories

### Spoofing and Access Control

The demo intentionally has no user identity and no privileged operation. Public
callers therefore cannot impersonate an account or gain access to user data.
The absence of authentication MUST NOT be interpreted as suitable for a real
execution adapter. Any future non-simulated action MUST introduce server-side
identity, authorization, and assurance-run binding before it is reachable.

### Tampering and Prompt Injection

A caller may bypass the read-only browser and send arbitrary API bodies. The
server MUST reject every producer command except the exact instrumented
scenario before constructing a model client. The producer command MUST be
passed as data under a separate system instruction. Function calling MUST
remain disabled. Gemini output MUST be schema-validated, size-bounded, and
treated as untrusted; it MUST NOT modify evidence or choose ALLOW, REVIEW,
BLOCK, or UNKNOWN.

### Information Disclosure

Provider exceptions, credentials, and internal authentication details MUST NOT
be returned to the browser. Public runtime metadata MAY identify the SDK,
model, project label, and location because these are intentional demo evidence,
but MUST NOT contain keys or tokens. Dynamic model strings MUST be escaped
before HTML rendering. Browser policy headers MUST deny unnecessary device and
network capabilities.

### Denial of Service and Unbounded Consumption

The live model call is the principal cost and availability risk. The endpoint
MUST enforce per-client and global replay limits before invoking Gemini, bound
concurrent model calls, cap model output, limit retries, and apply both provider
and server timeouts. These in-process controls reset on restart and apply per
instance; provider quotas and deployment-level controls remain the final backstop
against distributed traffic.

### Elevation of Privilege and Excessive Agency

Gemini has no tools and no action adapters. Deterministic code owns the
authorization boundary. `UNKNOWN` MUST never be treated as approval, and every
unsupported action MUST remain outside the safe subset. `/api/execute` MUST
require a current, integrity-protected capability bound to the assured plan and
MUST remain simulation-only. Any real adapter would additionally require user
identity, action-level authorization, one-time consumption, and durable audit.

### Repudiation and Receipt Semantics

Receipts are demonstrative, not durable audit records. They prove what the
simulation returned in one response but are not stored or cryptographically
signed. Product copy MUST continue to identify them as `SIMULATED` and state
that no external side effects occurred.

## OWASP LLM Application Coverage

- **Prompt injection:** exact server-side input allowlist, separated system
  instruction, no tools.
- **Sensitive information disclosure:** server-only secrets and sanitized
  errors.
- **Supply chain:** lockfile-controlled dependencies and a dated manual
  dependency audit documented in `security_assessment.md`.
- **Data/model poisoning:** no retrieval, uploads, fine-tuning, or mutable
  evidence source exists in this demo.
- **Improper output handling:** typed validation, bounded output, HTML escaping,
  client shape checks, and CSP.
- **Excessive agency:** interpretation-only model; deterministic authorization;
  signed assurance capability; simulation-only endpoint.
- **System prompt leakage:** the instruction contains no secrets or privileged
  capabilities; leaking it would not grant authority.
- **Vector/embedding weaknesses:** not applicable because there is no retrieval
  or vector store.
- **Misinformation/overreliance:** model statements are proposals with visible
  provenance, not evidence; deterministic policy sets the final boundary.
- **Unbounded consumption:** replay limits, concurrency cap, token limit,
  bounded retries, and layered timeouts.

## Required Security Guarantees

1. Only the fixed Eclipse command can trigger Gemini.
2. No model output can create evidence or authorize an action.
3. `UNKNOWN` can never enter the safe executable subset.
4. No endpoint can cause publishing, ad spend, voice generation, or any other
   external side effect.
5. Secrets and raw provider errors never reach clients or logs.
6. Model calls and outputs remain bounded under replay and concurrency.
7. Model-derived browser content is rendered as text, never executable markup.
8. A simulation receipt requires an unexpired capability signed by the server
   and bound to the expected safe plan.