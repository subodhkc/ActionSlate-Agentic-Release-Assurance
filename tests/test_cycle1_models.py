import asyncio
import json
import unittest
from types import SimpleNamespace

from app.agent import ActionSlateInterpreter
from app.models import ActionSlateInterpretation


class Cycle1ModelTests(unittest.TestCase):
    def test_structured_interpretation_accepts_consequential_action(self):
        result = ActionSlateInterpretation.model_validate(
            {
                "request_summary": "Release the approved trailer and promote it.",
                "consequential_actions": [
                    {
                        "action_id": "publish_trailer",
                        "action_type": "publish",
                        "description": "Publish the trailer to selected territories.",
                        "arguments": {
                            "asset": "ECLIPSE_TRAILER_V12_COLOR",
                            "territory": ["US", "Canada"],
                        },
                        "argument_provenance": {
                            "asset": "AGENT_INFERRED",
                            "territory": "UNKNOWN",
                        },
                        "required_evidence": ["asset_identity", "territory"],
                        "uncertainties": ["Territory was not explicit."],
                    }
                ],
                "interpretation_notes": ["The request implies distribution."],
            }
        )

        self.assertEqual(result.consequential_actions[0].action_type, "publish")
        self.assertEqual(
            result.consequential_actions[0].argument_provenance["territory"],
            "UNKNOWN",
        )

    def test_interpreter_retries_one_invalid_structured_response(self):
        valid_payload = {
            "request_summary": "Release the approved trailer.",
            "consequential_actions": [
                {
                    "action_id": "publish",
                    "action_type": "publish",
                    "description": "Publish the approved trailer.",
                    "arguments": {"asset": "V12"},
                    "argument_provenance": {"asset": "USER_EXPLICIT"},
                    "required_evidence": ["asset approval"],
                    "uncertainties": [],
                }
            ],
            "interpretation_notes": [],
        }

        class FakeModels:
            def __init__(self):
                self.calls = 0

            async def generate_content(self, **_kwargs):
                self.calls += 1
                if self.calls == 1:
                    return SimpleNamespace(text='{"request_summary":"incomplete"}')
                return SimpleNamespace(text=json.dumps(valid_payload))

        fake_models = FakeModels()
        interpreter = ActionSlateInterpreter.__new__(ActionSlateInterpreter)
        interpreter.settings = SimpleNamespace(gemini_model="gemini-2.5-flash")
        interpreter.client = SimpleNamespace(aio=SimpleNamespace(models=fake_models))

        result = asyncio.run(interpreter.interpret("Release the approved trailer."))

        self.assertEqual(result.request_summary, "Release the approved trailer.")
        self.assertEqual(fake_models.calls, 2)


if __name__ == "__main__":
    unittest.main()