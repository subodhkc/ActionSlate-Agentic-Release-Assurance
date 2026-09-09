import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException
from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import Response

from app.agent import AgentRuntimeError
from app.main import add_security_headers, assure, execute
from app.models import (
    ActionSlateInterpretation,
    ExecuteRequest,
    InterpretRequest,
)
from app.security import (
    SlidingWindowLimiter,
    issue_execution_token,
    verify_execution_token,
)


class SecurityGuardrailTests(unittest.TestCase):
    def test_rate_limiter_rejects_replay_burst(self):
        async def exercise():
            limiter = SlidingWindowLimiter(
                per_client=2,
                global_limit=10,
                window_seconds=60,
            )
            self.assertEqual(await limiter.retry_after("client-a", now=100), 0)
            self.assertEqual(await limiter.retry_after("client-a", now=101), 0)
            self.assertEqual(await limiter.retry_after("client-a", now=102), 58)
            self.assertEqual(await limiter.retry_after("client-a", now=161), 0)

        asyncio.run(exercise())

    def test_global_rate_limit_applies_across_clients(self):
        async def exercise():
            limiter = SlidingWindowLimiter(
                per_client=5,
                global_limit=2,
                window_seconds=60,
            )
            self.assertEqual(await limiter.retry_after("client-a", now=100), 0)
            self.assertEqual(await limiter.retry_after("client-b", now=101), 0)
            self.assertGreater(await limiter.retry_after("client-c", now=102), 0)

        asyncio.run(exercise())

    def test_oversized_prompt_is_rejected_by_schema(self):
        with self.assertRaises(ValidationError):
            InterpretRequest(producer_request="x" * 257)

    def test_excessive_action_count_is_rejected(self):
        action = {
            "action_id": "publish",
            "action_type": "publish",
            "description": "Publish one asset.",
            "arguments": {"asset": "V12"},
            "argument_provenance": {"asset": "USER_EXPLICIT"},
            "required_evidence": ["asset"],
            "uncertainties": [],
        }
        with self.assertRaises(ValidationError):
            ActionSlateInterpretation.model_validate(
                {
                    "request_summary": "Too many actions.",
                    "consequential_actions": [action] * 13,
                    "interpretation_notes": [],
                }
            )

    def test_execution_token_is_bound_and_expires(self):
        token = issue_execution_token(
            "test-secret",
            "eclipse-safe-plan",
            now=1_000,
            ttl_seconds=300,
        )

        self.assertTrue(
            verify_execution_token(
                token,
                "test-secret",
                "eclipse-safe-plan",
                now=1_100,
            )
        )
        self.assertFalse(
            verify_execution_token(
                token,
                "test-secret",
                "different-plan",
                now=1_100,
            )
        )
        self.assertFalse(
            verify_execution_token(
                token + "tampered",
                "test-secret",
                "eclipse-safe-plan",
                now=1_100,
            )
        )
        self.assertFalse(
            verify_execution_token(
                token,
                "test-secret",
                "eclipse-safe-plan",
                now=1_300,
            )
        )

    def test_security_headers_and_api_no_store(self):
        async def exercise(path):
            request = Request(
                {
                    "type": "http",
                    "method": "GET",
                    "scheme": "https",
                    "path": path,
                    "raw_path": path.encode(),
                    "query_string": b"",
                    "headers": [],
                    "client": ("test-client", 1234),
                    "server": ("testserver", 443),
                }
            )

            async def call_next(_request):
                return Response()

            return await add_security_headers(request, call_next)

        page = asyncio.run(exercise("/"))
        self.assertIn("default-src 'self'", page.headers["content-security-policy"])
        self.assertEqual(page.headers["x-content-type-options"], "nosniff")

        api = asyncio.run(exercise("/api/demo"))
        self.assertEqual(api.headers["cache-control"], "no-store")

    def test_provider_failure_is_sanitized(self):
        class FailingInterpreter:
            def __init__(self, _settings):
                pass

            async def interpret(self, _request):
                raise AgentRuntimeError("provider-internal-secret-detail")

        settings = SimpleNamespace(
            session_secret="test-secret",
            gemini_model="gemini-2.5-flash",
            google_cloud_project="actionslate",
            google_cloud_location="global",
        )
        request = InterpretRequest(
            producer_request=(
                "Launch the Eclipse Protocol trailer worldwide tonight. "
                "Localize it for France and Spain using Ava's voice, then "
                "maximize paid reach."
            )
        )
        with (
            patch("app.main.get_settings", return_value=settings),
            patch("app.main.ActionSlateInterpreter", FailingInterpreter),
            self.assertRaises(HTTPException) as context,
        ):
            asyncio.run(assure(request))

        self.assertEqual(context.exception.status_code, 502)
        self.assertNotIn("provider-internal", context.exception.detail)

    def test_execute_requires_valid_assurance_capability(self):
        settings = SimpleNamespace(session_secret="test-secret")
        invalid = ExecuteRequest(
            plan_id="eclipse-safe-plan",
            execution_token="invalid-token-that-is-long-enough-for-validation-000",
        )
        with (
            patch("app.main.get_settings", return_value=settings),
            self.assertRaises(HTTPException) as context,
        ):
            asyncio.run(execute(invalid))
        self.assertEqual(context.exception.status_code, 403)

        token = issue_execution_token("test-secret", "eclipse-safe-plan")
        valid = ExecuteRequest(
            plan_id="eclipse-safe-plan",
            execution_token=token,
        )
        with patch("app.main.get_settings", return_value=settings):
            receipt = asyncio.run(execute(valid))
        self.assertEqual(receipt.status, "SIMULATED")


if __name__ == "__main__":
    unittest.main()