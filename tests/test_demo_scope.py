import asyncio
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app.main import assure, favicon
from app.models import InterpretRequest


class DemoScopeTests(unittest.TestCase):
    def test_assure_rejects_requests_outside_instrumented_scenario(self):
        request = InterpretRequest(
            producer_request="Publish an unrelated cooking video tomorrow."
        )

        with patch("app.main.ActionSlateInterpreter") as interpreter:
            with self.assertRaises(HTTPException) as context:
                asyncio.run(assure(request))

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("fixed Eclipse Protocol", context.exception.detail)
        interpreter.assert_not_called()

    def test_favicon_is_served(self):
        response = asyncio.run(favicon())

        self.assertEqual(response.media_type, "image/svg+xml")
        self.assertTrue(str(response.path).endswith("favicon.svg"))


if __name__ == "__main__":
    unittest.main()