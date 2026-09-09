import unittest

from app.assurance import build_assurance_response, simulated_receipt
from app.models import ActionSlateInterpretation


class DeterministicAssuranceTests(unittest.TestCase):
    def setUp(self):
        self.interpretation = ActionSlateInterpretation.model_validate(
            {
                "request_summary": "Release and localize the Eclipse trailer.",
                "consequential_actions": [
                    {
                        "action_id": "publish-trailer",
                        "action_type": "publish",
                        "description": "Publish the trailer worldwide tonight.",
                        "arguments": {"territory": "GLOBAL", "time": "tonight"},
                        "argument_provenance": {
                            "territory": "USER_EXPLICIT",
                            "time": "USER_EXPLICIT",
                        },
                        "required_evidence": ["asset", "territory", "timing"],
                        "uncertainties": [],
                    }
                ],
                "interpretation_notes": [],
            }
        )

    def test_unknown_is_not_treated_as_approval(self):
        result = build_assurance_response(
            "Release the trailer.",
            self.interpretation,
            {"verified": "true"},
        )

        voice = next(item for item in result.evaluations if item.id == "voice-gap")
        self.assertEqual(voice.status, "UNKNOWN")
        self.assertNotEqual(result.overall_status, "ALLOW")
        self.assertTrue(result.capability_exceeds_greenlight)

    def test_safe_plan_excludes_unsupported_scope(self):
        result = build_assurance_response(
            "Release the trailer.",
            self.interpretation,
            {"verified": "true"},
        )

        ready_steps = [step.title for step in result.safe_plan.steps if step.status == "READY"]
        self.assertIn("Stage V12 approved master", ready_steps)
        self.assertIn("Constrain distribution to US + Canada", ready_steps)
        self.assertIn("France and Spain release", result.safe_plan.blocked_items)

    def test_receipt_is_explicitly_simulated(self):
        receipt = simulated_receipt()

        self.assertEqual(receipt.status, "SIMULATED")
        self.assertEqual(receipt.external_side_effects, "None — simulation only")


if __name__ == "__main__":
    unittest.main()