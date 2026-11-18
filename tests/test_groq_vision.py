"""Test suite for Groq Vision API integration and standardized schema validation in ReUseAI.
Tests the official Groq SDK client wrapper, base64 image encoding,
the 6-field JSON schema (material, waste_type, condition, recyclable, confidence, reuse_ideas),
and error/quota/timeout handling.
"""

import os
import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO
import json
import base64
from PIL import Image

from src.config import GROQ_API_KEY, DEFAULT_MODEL
from src.services.ai_client import GroqVisionClient
from src.services.analyzer import WasteAnalyzer
from src.models.schemas import WasteAnalysisResult, MaterialAnalysis
from src.utils.sample_generator import create_sample_plastic_bottle
from src.utils.image_processor import preprocess_image, image_to_bytes


class TestGroqVisionIntegration(unittest.TestCase):
    """Test suite verifying all Groq Vision API requirements."""

    def setUp(self):
        self.sample_img = create_sample_plastic_bottle()
        self.client = GroqVisionClient(api_key="mock_gsk_key", model_name="qwen/qwen3.8-27b")

    def test_client_configuration_and_model(self):
        """Requirement 1 & 2: Verify official SDK client initialization and model name."""
        self.assertEqual(self.client.model_name, "qwen/qwen3.8-27b")
        self.assertTrue(self.client.is_ready())

    def test_base64_image_input_preparation(self):
        """Requirement 4: Verify preprocessed images are correctly encoded to base64."""
        prep_img = preprocess_image(self.sample_img)
        raw_bytes = image_to_bytes(prep_img, format_name="JPEG", quality=90)
        b64_str = base64.b64encode(raw_bytes).decode("utf-8")

        self.assertIsInstance(b64_str, str)
        self.assertGreater(len(b64_str), 100)
        # Verify decoding back yields valid JPEG
        decoded = base64.b64decode(b64_str)
        reconstructed = Image.open(BytesIO(decoded))
        self.assertEqual(reconstructed.format, "JPEG")

    def test_exact_json_schema_normalization(self):
        """Requirement 7: Verify exact schema enforcement:
        material, waste_type, condition, recyclable, confidence, reuse_ideas.
        """
        raw_response = {
            "material": "Polyethylene Terephthalate / PET",
            "waste_type": "Plastics",
            "condition": "Intact, Clean",
            "recyclable": True,
            "confidence": 0.98,
            "reuse_ideas": [
                "Self-Watering Planter: Cut bottle in half, invert top, add wick.",
                "Bird Feeder: Cut seed ports, add hanging loop."
            ]
        }

        normalized = self.client._normalize_schema(raw_response)
        required_keys = ["material", "waste_type", "condition", "recyclable", "confidence", "reuse_ideas"]
        for key in required_keys:
            self.assertIn(key, normalized)

        self.assertEqual(normalized["material"], "Polyethylene Terephthalate / PET")
        self.assertEqual(normalized["waste_type"], "Plastics")
        self.assertEqual(normalized["condition"], "Intact, Clean")
        self.assertTrue(normalized["recyclable"])
        self.assertEqual(normalized["confidence"], 0.98)
        self.assertEqual(len(normalized["reuse_ideas"]), 2)

    def test_schema_backward_compatibility_fallback(self):
        """Requirement 7: Verify schema normalizer maps legacy or alternative keys to the 6 schema keys."""
        legacy_data = {
            "material_type": "Corrugated Cardboard",
            "primary_category": "Cardboard & Paper",
            "physical_condition": "Slightly Damaged",
            "confidence_score": 0.88,
            "recyclability_score": 85,
            "reuse_suggestions": [
                {
                    "title": "Shipping Box Organizer",
                    "step_by_step_guide": ["Cut flaps", "Use as drawer dividers"]
                }
            ]
        }

        normalized = self.client._normalize_schema(legacy_data)
        self.assertEqual(normalized["material"], "Corrugated Cardboard")
        self.assertEqual(normalized["waste_type"], "Cardboard & Paper")
        self.assertEqual(normalized["condition"], "Slightly Damaged")
        self.assertTrue(normalized["recyclable"])
        self.assertEqual(normalized["confidence"], 0.88)
        self.assertGreater(len(normalized["reuse_ideas"]), 0)

    def test_malformed_json_extraction(self):
        """Requirement 8: Verify robust extraction from code fences or dirty text."""
        # Case A: Fenced with ```json
        fenced = '```json\n{"material": "Glass", "waste_type": "Glass", "condition": "Intact", "recyclable": true, "confidence": 0.9, "reuse_ideas": ["Vase"]}\n```'
        parsed_fenced = self.client._extract_json(fenced)
        self.assertEqual(parsed_fenced["material"], "Glass")

        # Case B: Trailing/leading text around JSON
        dirty = 'Here is the analysis:\n{"material": "Aluminum Can", "waste_type": "Metals", "condition": "Crushed", "recyclable": true, "confidence": 0.95, "reuse_ideas": ["Pencil Holder"]}\nHope this helps!'
        parsed_dirty = self.client._extract_json(dirty)
        self.assertEqual(parsed_dirty["material"], "Aluminum Can")

        # Case C: Completely malformed
        with self.assertRaises(ValueError):
            self.client._extract_json("Not a JSON object at all.")

    def test_error_handling_rate_limit_and_auth(self):
        """Requirement 8: Verify graceful handling and clear messages on Groq exceptions."""
        from groq import AuthenticationError, RateLimitError

        # Test AuthenticationError
        mock_response = MagicMock()
        mock_response.status_code = 401
        with patch.object(self.client.client.chat.completions, "create", side_effect=AuthenticationError(message="Invalid API Key", response=mock_response, body=None)):
            with self.assertRaises(PermissionError) as ctx:
                self.client.analyze_image(self.sample_img)
            self.assertIn("GROQ_API_KEY", str(ctx.exception))

        # Test RateLimitError
        mock_rate_response = MagicMock()
        mock_rate_response.status_code = 429
        with patch.object(self.client.client.chat.completions, "create", side_effect=RateLimitError(message="Rate limit exceeded", response=mock_rate_response, body=None)):
            with self.assertRaises(RuntimeError) as ctx:
                self.client.analyze_image(self.sample_img)
            self.assertIn("rate limit or quota", str(ctx.exception).lower())

    def test_error_handling_timeout_connection_and_empty_response(self):
        """Verify timeout, network connection, and empty model responses produce clear errors."""
        from groq import APITimeoutError, APIConnectionError

        with patch.object(
            self.client.client.chat.completions,
            "create",
            side_effect=APITimeoutError(request=MagicMock()),
        ):
            with self.assertRaises(TimeoutError) as ctx:
                self.client.analyze_image(self.sample_img)
            self.assertIn("timed out", str(ctx.exception).lower())

        with patch.object(
            self.client.client.chat.completions,
            "create",
            side_effect=APIConnectionError(request=MagicMock()),
        ):
            with self.assertRaises(ConnectionError) as ctx:
                self.client.analyze_image(self.sample_img)
            self.assertIn("connect", str(ctx.exception).lower())

        empty_completion = MagicMock()
        empty_completion.choices = []
        with patch.object(
            self.client.client.chat.completions,
            "create",
            return_value=empty_completion,
        ):
            with self.assertRaises(ValueError) as ctx:
                self.client.analyze_image(self.sample_img)
            self.assertIn("empty", str(ctx.exception).lower())

    def test_schema_legacy_low_recyclability_and_confidence_clamping(self):
        """Verify legacy recyclability_score < 50 maps to recyclable=False and confidence is clamped."""
        normalized = self.client._normalize_schema(
            {
                "material_type": "Contaminated Styrofoam",
                "primary_category": "Plastics",
                "physical_condition": "Fragmented",
                "recyclability_score": 20,
                "confidence_score": 1.45,
                "reuse_ideas": ["Packing filler"],
            }
        )
        self.assertFalse(normalized["recyclable"])
        self.assertEqual(normalized["confidence"], 1.0)

        normalized_low = self.client._normalize_schema(
            {
                "material": "Unknown Scrap",
                "waste_type": "Other",
                "condition": "Damaged",
                "recyclable": False,
                "confidence": -0.25,
                "reuse_ideas": ["Inspect for safe disposal"],
            }
        )
        self.assertFalse(normalized_low["recyclable"])
        self.assertEqual(normalized_low["confidence"], 0.0)

    def test_end_to_end_analyzer_with_exact_schema(self):
        """Requirements 6 & 7: Verify full single-request analyzer with the 6-field schema."""
        analyzer = WasteAnalyzer(api_key="mock_key")

        mock_groq_json = {
            "material": "Polyethylene Terephthalate / PET",
            "waste_type": "Plastics",
            "condition": "Intact, Clean",
            "recyclable": True,
            "confidence": 0.96,
            "reuse_ideas": [
                "Self-Watering Planter: Cut bottle in half, invert top, add wick string.",
                "Bird Feeder: Cut feed holes, add perch dowel and hanging wire."
            ],
            "metadata": {
                "timings": {
                    "api_request_seconds": 0.45,
                    "parsing_seconds": 0.002
                }
            }
        }

        with patch.object(analyzer.ai_client, "analyze_image", return_value=mock_groq_json):
            result = analyzer.analyze(self.sample_img)

            self.assertIsInstance(result, WasteAnalysisResult)
            self.assertEqual(result.material.material_type, "Polyethylene Terephthalate / PET")
            self.assertEqual(result.waste_type, "Plastics")
            self.assertEqual(result.condition, "Intact, Clean")
            self.assertTrue(result.recyclable)
            self.assertEqual(result.confidence, 0.96)
            self.assertEqual(len(result.reuse_suggestions), 2)

            # Test exact 6-field schema export
            schema_dict = result.to_schema_dict()
            expected_keys = {"material", "waste_type", "condition", "recyclable", "confidence", "reuse_ideas"}
            self.assertEqual(set(schema_dict.keys()), expected_keys)
            self.assertIsInstance(schema_dict["reuse_ideas"], list)

            # Test JSON export round-trip
            schema_json = result.to_schema_json()
            parsed_json = json.loads(schema_json)
            self.assertEqual(set(parsed_json.keys()), expected_keys)

            # Verify data types of all six standardized fields
            self.assertIsInstance(parsed_json["material"], str)
            self.assertIsInstance(parsed_json["waste_type"], str)
            self.assertIsInstance(parsed_json["condition"], str)
            self.assertIsInstance(parsed_json["recyclable"], bool)
            self.assertIsInstance(parsed_json["confidence"], float)
            self.assertIsInstance(parsed_json["reuse_ideas"], list)

            self.assertTrue(
                all(isinstance(idea, str) for idea in parsed_json["reuse_ideas"])
            )

            # Verify flat six-field JSON reconstruction
            reconstructed = WasteAnalysisResult.from_dict(parsed_json)

            self.assertEqual(
                reconstructed.material.material_type,
                parsed_json["material"]
            )
            self.assertEqual(reconstructed.waste_type, parsed_json["waste_type"])
            self.assertEqual(reconstructed.condition, parsed_json["condition"])
            self.assertEqual(reconstructed.recyclable, parsed_json["recyclable"])
            self.assertEqual(reconstructed.confidence, parsed_json["confidence"])
            self.assertEqual(
                reconstructed.to_schema_dict().keys(),
                expected_keys
            )


    def test_live_groq_vision_if_key_available(self):
        """Opt-in live integration test against Groq Vision API (set RUN_LIVE_GROQ_TESTS=1)."""
        if os.getenv("RUN_LIVE_GROQ_TESTS", "").strip() != "1":
            self.skipTest("Live Groq API test skipped by default; set RUN_LIVE_GROQ_TESTS=1 to run.")
        if not GROQ_API_KEY or GROQ_API_KEY.startswith("your_"):
            self.skipTest("No active GROQ_API_KEY configured in environment.")

        live_client = GroqVisionClient()
        self.assertTrue(live_client.is_ready())

        prep = preprocess_image(self.sample_img)
        output = live_client.analyze_image(prep)

        self.assertIn("material", output)
        self.assertIn("waste_type", output)
        self.assertIn("condition", output)
        self.assertIn("recyclable", output)
        self.assertIn("confidence", output)
        self.assertIn("reuse_ideas", output)
        self.assertGreater(len(output["reuse_ideas"]), 0)


if __name__ == "__main__":
    unittest.main()
