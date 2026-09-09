"""ActionSlate P0 FastAPI application."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
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


app = FastAPI(
    title="ActionSlate — Agentic Release Assurance",
    description="P0: deterministic release assurance around a live Gemini interpretation.",
    version="0.2.0",
)
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    return Response(status_code=204)


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
async def assure(request: InterpretRequest) -> AssuranceResponse:
    settings = get_settings()
    try:
        interpretation = await ActionSlateInterpreter(settings).interpret(
            request.producer_request
        )
        return build_assurance_response(
            producer_request=request.producer_request,
            interpretation=interpretation,
            runtime={
                "sdk": "google-genai",
                "model": settings.gemini_model,
                "auth": "GOOGLE_API_KEY",
                "project": settings.google_cloud_project,
                "location": settings.google_cloud_location,
                "verified": "true",
            },
        )
    except RuntimeConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except AgentRuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/api/execute", response_model=ExecutionReceipt)
async def execute(request: ExecuteRequest) -> ExecutionReceipt:
    if request.plan_id != "eclipse-safe-plan":
        raise HTTPException(status_code=400, detail="Unknown safe plan.")
    return simulated_receipt()