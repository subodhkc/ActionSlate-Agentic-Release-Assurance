import unittest

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


if __name__ == "__main__":
    unittest.main()