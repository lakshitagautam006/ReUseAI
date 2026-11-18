"""End-to-end integration tests for the complete ReUseAI workflow (Phase 8).

Verifies the full pipeline without live Groq API calls:
image input -> validation & preprocessing -> mocked Groq Vision API ->
MaterialDetector -> ReuseEngine -> ResourceMatchingEngine ->
exact 6-field standardized JSON schema -> database persistence -> retrieval.
"""

import json
import unittest
from io import BytesIO
from unittest.mock import MagicMock, patch

from src.database import repository
from src.models.schemas import WasteAnalysisResult
from src.services.analyzer import WasteAnalyzer
from src.utils.image_processor import image_to_bytes
from src.utils.sample_generator import (
    create_sample_cardboard_box,
    create_sample_glass_jar,
    create_sample_plastic_bottle,
)


def _make_mock_groq_completion(payload: dict) -> MagicMock:
    """Build a mock Groq chat completion response returning JSON text."""
    completion = MagicMock()
    message = MagicMock()
    message.content = json.dumps(payload)
    choice = MagicMock()
    choice.message = message
    completion.choices = [choice]
    return completion


class _InMemoryAnalysisStore:
    """Lightweight in-memory store mocking PostgreSQL cursor behavior for full-pipeline tests."""

    def __init__(self):
        self.next_id = 1
        self.analyses = {}
        self.reuse_suggestions = []
        self.matched_opportunities = []

    def make_connection(self):
        store = self
        last_fetchone = {"value": None}

        cursor = MagicMock()

        def execute_side_effect(sql, params=None):
            normalized_sql = " ".join(sql.split()).upper()
            if normalized_sql.startswith("INSERT INTO ANALYSES"):
                analysis_id = store.next_id
                store.next_id += 1
                store.analyses[analysis_id] = {
                    "id": analysis_id,
                    "material_type": params[0],
                    "primary_category": params[1],
                    "sub_category": params[2],
                    "confidence_score": params[3],
                    "cleanliness_level": params[4],
                    "physical_condition": params[5],
                    "recyclability_score": params[6],
                    "full_result": json.loads(params[7]),
                }
                last_fetchone["value"] = (analysis_id,)
            elif normalized_sql.startswith("INSERT INTO REUSE_SUGGESTIONS"):
                store.reuse_suggestions.append(
                    {"analysis_id": params[0], "suggestion_data": json.loads(params[1])}
                )
                last_fetchone["value"] = None
            elif normalized_sql.startswith("INSERT INTO MATCHED_OPPORTUNITIES"):
                store.matched_opportunities.append(
                    {"analysis_id": params[0], "opportunity_data": json.loads(params[1])}
                )
                last_fetchone["value"] = None
            elif normalized_sql.startswith("SELECT FULL_RESULT FROM ANALYSES"):
                record = store.analyses.get(params[0])
                last_fetchone["value"] = (record["full_result"],) if record else None

        cursor.execute.side_effect = execute_side_effect
        cursor.fetchone.side_effect = lambda: last_fetchone["value"]

        conn = MagicMock()
        conn.__enter__.return_value = conn
        conn.__exit__.return_value = False
        conn.cursor.return_value.__enter__.return_value = cursor
        conn.cursor.return_value.__exit__.return_value = False
        return conn


class TestEndToEndWorkflow(unittest.TestCase):
    """Verify full analysis-to-persistence pipeline with mocked external API and DB."""

    EXPECTED_SCHEMA_KEYS = {
        "material",
        "waste_type",
        "condition",
        "recyclable",
        "confidence",
        "reuse_ideas",
    }

    def test_full_pipeline_plastic_bottle_bytes_to_db_roundtrip(self):
        """Image bytes -> Groq Vision mock -> Detector -> Reuse -> Matcher -> DB save & retrieve."""
        raw_jpeg_bytes = image_to_bytes(create_sample_plastic_bottle(), format_name="JPEG")
        groq_payload = {
            "material": "Polyethylene Terephthalate / PET Plastic Bottle",
            "waste_type": "Plastics",
            "condition": "Intact, Clean",
            "recyclable": True,
            "confidence": 0.96,
            "reuse_ideas": [
                "Sub-Irrigated Self-Watering Herb Planter: 1. Wash bottle. 2. Cut top third. 3. Invert neck. 4. Thread cotton wick. 5. Fill with soil and herbs.",
                "Precision 1.75mm 3D Printer Filament Feedstock: 1. Clean PET bottle. 2. Cut continuous ribbon. 3. Extrude through heated nozzle. 4. Spool cooled filament.",
            ],
        }

        analyzer = WasteAnalyzer(api_key="mock_gsk_test_key", model_name="qwen/qwen3.8-27b")
        stages_seen = []
        store = _InMemoryAnalysisStore()

        with patch.object(
            analyzer.ai_client.client.chat.completions,
            "create",
            return_value=_make_mock_groq_completion(groq_payload),
        ) as mock_api:
            result = analyzer.analyze(
                BytesIO(raw_jpeg_bytes),
                progress_callback=lambda stage, _msg: stages_seen.append(stage),
            )

        mock_api.assert_called_once()
        self.assertEqual(
            stages_seen,
            ["preprocessing", "vision_ai", "diagnostics", "reuse_engine", "matching", "complete"],
        )

        # Verify material detection, reuse suggestions, and resource matching
        self.assertIsInstance(result, WasteAnalysisResult)
        self.assertEqual(result.material.primary_category, "Plastics")
        self.assertTrue(result.recyclable)
        self.assertGreaterEqual(len(result.reuse_suggestions), 2)
        for sugg in result.reuse_suggestions:
            self.assertGreaterEqual(len(sugg.step_by_step_guide), 4)
            self.assertLessEqual(len(sugg.step_by_step_guide), 6)

        self.assertGreaterEqual(len(result.matched_opportunities), 1)
        scores = [opp.match_score for opp in result.matched_opportunities]
        self.assertEqual(scores, sorted(scores, reverse=True))

        # Verify exact 6-field standardized JSON schema contract
        schema_dict = result.to_schema_dict()
        self.assertEqual(set(schema_dict.keys()), self.EXPECTED_SCHEMA_KEYS)
        self.assertIsInstance(schema_dict["material"], str)
        self.assertIsInstance(schema_dict["waste_type"], str)
        self.assertIsInstance(schema_dict["condition"], str)
        self.assertIsInstance(schema_dict["recyclable"], bool)
        self.assertIsInstance(schema_dict["confidence"], float)
        self.assertIsInstance(schema_dict["reuse_ideas"], list)

        # Persist through repository layer and retrieve back
        with patch.object(repository, "get_connection", side_effect=store.make_connection):
            analysis_id = repository.save_analysis(result)
            retrieved = repository.get_analysis_by_id(analysis_id)
            missing = repository.get_analysis_by_id(999999)

        self.assertEqual(analysis_id, 1)
        self.assertIsNotNone(retrieved)
        self.assertIsNone(missing)
        self.assertEqual(len(store.reuse_suggestions), len(result.reuse_suggestions))
        self.assertEqual(len(store.matched_opportunities), len(result.matched_opportunities))
        self.assertEqual(retrieved["material"]["material_type"], result.material.material_type)
        self.assertEqual(retrieved["waste_type"], "Plastics")

        # Verify retrieved full_result reconstructs cleanly back to WasteAnalysisResult
        reconstructed = WasteAnalysisResult.from_dict(retrieved)
        self.assertEqual(reconstructed.to_schema_dict(), schema_dict)

    def test_full_pipeline_cardboard_and_glass_streams(self):
        """Verify end-to-end mocked workflow across cardboard and glass waste streams."""
        cases = [
            (
                create_sample_cardboard_box(),
                {
                    "material": "Corrugated Cardboard Box",
                    "waste_type": "Cardboard & Paper",
                    "condition": "Intact, Clean",
                    "recyclable": True,
                    "confidence": 0.93,
                    "reuse_ideas": [
                        "Biodegradable Permaculture Sheet Mulch: Flatten box, strip tape, soak, lay under woodchips.",
                        "Modular Interlocking Drawer Dividers: Measure drawer, cut slotted cardboard strips, assemble grid.",
                    ],
                },
                "Cardboard & Paper",
            ),
            (
                create_sample_glass_jar(),
                {
                    "material": "Clear Silica Glass Jar",
                    "waste_type": "Glass",
                    "condition": "Intact, Clean",
                    "recyclable": True,
                    "confidence": 0.97,
                    "reuse_ideas": [
                        "Zero-Waste Pantry Bulk Storage Jar: Soak label off, sterilize in boiling water, dry, label tare weight.",
                        "Miniature Closed Terrarium: Layer gravel, charcoal, moss, soil, and small fern.",
                    ],
                },
                "Glass",
            ),
        ]

        analyzer = WasteAnalyzer(api_key="mock_gsk_test_key", model_name="qwen/qwen3.8-27b")
        store = _InMemoryAnalysisStore()

        for sample_img, payload, expected_category in cases:
            with self.subTest(category=expected_category):
                with patch.object(
                    analyzer.ai_client.client.chat.completions,
                    "create",
                    return_value=_make_mock_groq_completion(payload),
                ):
                    result = analyzer.analyze(sample_img)

                self.assertEqual(result.waste_type, expected_category)
                self.assertGreaterEqual(len(result.reuse_suggestions), 2)
                self.assertGreaterEqual(len(result.matched_opportunities), 1)
                self.assertEqual(set(result.to_schema_dict().keys()), self.EXPECTED_SCHEMA_KEYS)

                with patch.object(repository, "get_connection", side_effect=store.make_connection):
                    saved_id = repository.save_analysis(result)
                    fetched = repository.get_analysis_by_id(saved_id)
                    self.assertEqual(fetched["waste_type"], expected_category)

        self.assertEqual(len(store.analyses), 2)

    def test_invalid_image_aborts_before_api_or_database(self):
        """Corrupted or non-image input must fail validation without invoking Groq API."""
        analyzer = WasteAnalyzer(api_key="mock_gsk_test_key", model_name="qwen/qwen3.8-27b")

        with patch.object(analyzer.ai_client.client.chat.completions, "create") as mock_api:
            with self.assertRaises(ValueError) as ctx:
                analyzer.analyze(b"this is definitely not an image")
            self.assertIn("validation failed", str(ctx.exception).lower())
            mock_api.assert_not_called()

    def test_malformed_vision_response_raises_without_db_write(self):
        """Malformed model JSON must raise ValueError cleanly before any DB persistence."""
        analyzer = WasteAnalyzer(api_key="mock_gsk_test_key", model_name="qwen/qwen3.8-27b")
        bad_completion = MagicMock()
        bad_completion.choices = [MagicMock(message=MagicMock(content="not valid json"))]

        with (
            patch.object(
                analyzer.ai_client.client.chat.completions,
                "create",
                return_value=bad_completion,
            ),
            patch.object(repository, "save_analysis") as mock_save,
        ):
            with self.assertRaises(ValueError):
                analyzer.analyze(create_sample_plastic_bottle())
            mock_save.assert_not_called()


if __name__ == "__main__":
    unittest.main()
