"""Google Gen AI adapter for ActionSlate's semantic interpretation step."""

from __future__ import annotations

import asyncio

from google import genai
from google.genai import types

from .config import Settings, configure_google_runtime
from .models import ActionSlateInterpretation


ACTIONSLATE_INSTRUCTION = """
You are ActionSlate's media-release interpretation agent.

Perform semantic discovery only. Decompose the producer's natural-language
request into every consequential media action an autonomous system might
attempt. Capture exact arguments such as asset version, territory, channel,
time, performer or replica use, intended use, provenance, and spend. Mark
whether each argument was explicit, inferred, a default, or unknown.

Do not decide whether an action is allowed. Do not invent evidence. The
deterministic ActionSlate Greenlight Engine will compare your proposal with
evidence and decide ALLOW, REVIEW, BLOCK, or UNKNOWN.
""".strip()


class AgentRuntimeError(RuntimeError):
    """Raised when Google cannot produce a valid structured result."""


class ActionSlateInterpreter:
    """Real Google Gen AI client used by the live demo runtime."""

    def __init__(self, settings: Settings) -> None:
        configure_google_runtime(settings)
        self.settings = settings
        self.client = genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
            api_key=settings.google_api_key,
        )

    async def interpret(self, producer_request: str) -> ActionSlateInterpretation:
        """Run Gemini and validate its structured output."""

        prompt = f"""{ACTIONSLATE_INSTRUCTION}

Producer request:
{producer_request}
"""
        try:
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ActionSlateInterpretation,
                    temperature=0.1,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(
                        disable=True
                    ),
                ),
            )
            return ActionSlateInterpretation.model_validate_json(response.text)
        except Exception as exc:
            raise AgentRuntimeError(
                "Google Gen AI returned no valid ActionSlate interpretation. "
                f"{type(exc).__name__}: {exc}"
            ) from exc