"""ActionSlate FastAPI application."""

from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .agent import ActionSlateInterpreter, AgentRuntimeError
from .assurance import ECLIPSE_REQUEST, build_assurance_response, simulated_receipt
from .config import RuntimeConfigurationError, get_settings
from .models import (
    AssuranceResponse,
    ExecuteRequest,
    ExecutionReceipt,
    InterpretRequest,
)
from .security import (
    assurance_slots,
    enforce_assurance_rate_limit,
    issue_execution_token,
    verify_execution_token,
)


app = FastAPI(
    title="ActionSlate — Agentic Release Assurance",
    description="Deterministic release assurance around a live Gemini interpretation.",
    version="0.2.0",
)
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
    )
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    if request.url.path == "/":
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; "
            "style-src 'self' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; connect-src 'self'; object-src 'none'; "
            "base-uri 'none'; form-action 'none'; "
            "frame-ancestors 'self' https://replit.com https://*.replit.com "
            "https://*.replit.dev"
        )
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> FileResponse:
    return FileResponse(STATIC_DIR / "favicon.svg", media_type="image/svg+xml")


@app.get("/health")
async def health() -> dict[str, object]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": "actionslate",
        "google_runtime_configured": settings.has_google_credentials,
        "google_cloud_project": settings.google_cloud_project,
        "google_cloud_location": settings.google_cloud_location,
        "gemini_model": settings.gemini_model,
        "assurance_engine": "deterministic",
    }


@app.get("/api/demo")
async def demo_context() -> dict[str, str]:
    return {"request": ECLIPSE_REQUEST}


@app.post("/api/assure", response_model=AssuranceResponse)
async def assure(
    request: InterpretRequest,
    _rate_limit: None = Depends(enforce_assurance_rate_limit),
) -> AssuranceResponse:
    if request.producer_request.strip() != ECLIPSE_REQUEST:
        raise HTTPException(
            status_code=400,
            detail=(
                "This live demo is instrumented for the fixed Eclipse Protocol "
                "producer command."
            ),
        )

    settings = get_settings()
    if not settings.session_secret:
        raise HTTPException(
            status_code=503,
            detail="The execution guardrail is temporarily unavailable.",
        )
    acquired_slot = False
    try:
        await asyncio.wait_for(assurance_slots.acquire(), timeout=1)
        acquired_slot = True
        interpretation = await asyncio.wait_for(
            ActionSlateInterpreter(settings).interpret(ECLIPSE_REQUEST),
            timeout=45,
        )
        response = build_assurance_response(
            producer_request=ECLIPSE_REQUEST,
            interpretation=interpretation,
            runtime={
                "sdk": "google-genai",
                "model": settings.gemini_model,
                "project": settings.google_cloud_project,
                "location": settings.google_cloud_location,
                "verified": "true",
            },
        )
        response.execution_token = issue_execution_token(
            settings.session_secret,
            "eclipse-safe-plan",
        )
        return response
    except TimeoutError as exc:
        if not acquired_slot:
            raise HTTPException(
                status_code=503,
                detail="Live assurance is busy. Please retry shortly.",
            ) from exc
        raise HTTPException(
            status_code=504,
            detail="The live Google call timed out. Please retry.",
        ) from exc
    except RuntimeConfigurationError as exc:
        raise HTTPException(
            status_code=503,
            detail="The live Google runtime is temporarily unavailable.",
        ) from exc
    except AgentRuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail="Gemini did not return a valid structured interpretation. Please retry.",
        ) from exc
    finally:
        if acquired_slot:
            assurance_slots.release()


@app.post("/api/execute", response_model=ExecutionReceipt)
async def execute(request: ExecuteRequest) -> ExecutionReceipt:
    if request.plan_id != "eclipse-safe-plan":
        raise HTTPException(status_code=400, detail="Unknown safe plan.")
    settings = get_settings()
    if not settings.session_secret:
        raise HTTPException(
            status_code=503,
            detail="The execution guardrail is temporarily unavailable.",
        )
    if not verify_execution_token(
        request.execution_token,
        settings.session_secret,
        request.plan_id,
    ):
        raise HTTPException(
            status_code=403,
            detail="A current assurance capability is required.",
        )
    return simulated_receipt()