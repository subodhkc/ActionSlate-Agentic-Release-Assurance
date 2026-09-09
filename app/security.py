"""Small in-process abuse controls for the public live-demo endpoint."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import math
import secrets
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request


class SlidingWindowLimiter:
    """Bound request bursts without storing user data or requiring accounts."""

    def __init__(
        self,
        *,
        per_client: int = 5,
        global_limit: int = 20,
        window_seconds: int = 60,
    ) -> None:
        self.per_client = per_client
        self.global_limit = global_limit
        self.window_seconds = window_seconds
        self._clients: dict[str, deque[float]] = defaultdict(deque)
        self._global: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def retry_after(self, client_key: str, *, now: float | None = None) -> int:
        current = time.monotonic() if now is None else now
        cutoff = current - self.window_seconds
        async with self._lock:
            while self._global and self._global[0] <= cutoff:
                self._global.popleft()

            client_requests = self._clients[client_key]
            while client_requests and client_requests[0] <= cutoff:
                client_requests.popleft()

            blocked_until: list[float] = []
            if len(client_requests) >= self.per_client:
                blocked_until.append(client_requests[0] + self.window_seconds)
            if len(self._global) >= self.global_limit:
                blocked_until.append(self._global[0] + self.window_seconds)

            if blocked_until:
                return max(1, math.ceil(max(blocked_until) - current))

            client_requests.append(current)
            self._global.append(current)
            return 0


assurance_limiter = SlidingWindowLimiter()
assurance_slots = asyncio.Semaphore(2)


async def enforce_assurance_rate_limit(request: Request) -> None:
    """Reject replay bursts before they can consume Gemini quota."""

    client_key = request.client.host if request.client else "unknown"
    retry_after = await assurance_limiter.retry_after(client_key)
    if retry_after:
        raise HTTPException(
            status_code=429,
            detail="Live assurance rate limit reached. Please retry shortly.",
            headers={"Retry-After": str(retry_after)},
        )


def issue_execution_token(
    secret: str,
    plan_id: str,
    *,
    now: int | None = None,
    ttl_seconds: int = 300,
) -> str:
    """Issue a short-lived capability bound to one assured plan."""

    issued_at = int(time.time()) if now is None else now
    payload = {
        "plan": plan_id,
        "iat": issued_at,
        "exp": issued_at + ttl_seconds,
        "nonce": secrets.token_urlsafe(12),
    }
    encoded = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    ).decode().rstrip("=")
    signature = hmac.new(secret.encode(), encoded.encode(), hashlib.sha256).digest()
    encoded_signature = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    return f"{encoded}.{encoded_signature}"


def verify_execution_token(
    token: str,
    secret: str,
    plan_id: str,
    *,
    now: int | None = None,
) -> bool:
    """Verify capability integrity, plan binding, and expiry."""

    try:
        encoded, encoded_signature = token.split(".", 1)
        expected_signature = hmac.new(
            secret.encode(), encoded.encode(), hashlib.sha256
        ).digest()
        supplied_signature = base64.urlsafe_b64decode(
            encoded_signature + "=" * (-len(encoded_signature) % 4)
        )
        if not hmac.compare_digest(expected_signature, supplied_signature):
            return False

        payload = json.loads(
            base64.urlsafe_b64decode(
                encoded + "=" * (-len(encoded) % 4)
            ).decode()
        )
        current = int(time.time()) if now is None else now
        return (
            payload.get("plan") == plan_id
            and isinstance(payload.get("iat"), int)
            and isinstance(payload.get("exp"), int)
            and payload["iat"] <= current
            and current < payload["exp"]
        )
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return False