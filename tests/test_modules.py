"""Unit and integration test suite for ReUseAI subsystem 1.
Tests image processing, material detection, reuse suggestion generation,
and end-to-end analyzer pipelines.
"""

import unittest
from unittest.mock import patch
from PIL import Image
import json

from src.utils.image_processor import (
    validate_image,
    preprocess_image,
    image_to_bytes,
    get_image_metadata,
)
from src.utils.sample_generator import create_sample_plastic_bottle
from src.services.material_detector import MaterialDetector
from src.services.reuse_engine import ReuseEngine
from src.services.analyzer import WasteAnalyzer
from src.models.schemas import WasteAnalysisResult, MaterialAnalysis, ReuseSuggestion


class TestReUseAISubsystem(unittest.TestCase):

    def setUp(self):
        self.sample_img = create_sample_plastic_bottle()

    def test_image_validation_valid(self):
        """Test that a valid PIL image passes validation."""
        is_valid, msg = validate_image(self.sample_img)
        self.assertTrue(is_valid)
        self.assertEqual(msg, "")

    def test_image_preprocessing(self):
        """Test image mode normalization and size constraints."""
        rgba_large = Image.new("RGBA", (2000, 1500), (255, 0, 0, 255))
        processed = preprocess_image(rgba_large, max_dim=800)

        self.assertEqual(processed.mode, "RGB")
        w, h = processed.size
        self.assertLessEqual(max(w, h), 800)

    def test_image_metadata(self):
        """Test metadata extraction from image."""
        meta = get_image_metadata(self.sample_img)
        self.assertIn("width", meta)
        self.assertIn("height", meta)
        self.assertIn("aspect_ratio", meta)
        self.assertEqual(meta["width"], 400)
        self.assertEqual(meta["height"], 500)

    def test_image_to_bytes(self):
        """Test byte serialization."""
        b = image_to_bytes(self.sample_img, format_name="JPEG")
        self.assertIsInstance(b, bytes)
        self.assertGreater(len(b), 0)

    def test_material_detector(self):
        """Test material detection and recyclability penalty calculation."""
        detector = MaterialDetector()
        mock_raw = {
            "material_type": "PET Bottle",
            "primary_category": "Plastics",
            "sub_category": "PET #1",
            "confidence_score": 0.92,
            "cleanliness_level": "Heavily Contaminated",
            "physical_condition": "Crushed/Fragmented",
            "recyclability_score": 90,
            "detected_features": ["Plastic cap", "Crushed body"],
            "hazardous_elements": ["None"],
        }
        material = detector.evaluate(mock_raw)
        self.assertIsInstance(material, MaterialAnalysis)
        self.assertEqual(material.material_type, "PET Bottle")
        # Penalties: -30 for heavily contaminated, -15 for crushed: 90 - 45 = 45
        self.assertEqual(material.recyclability_score, 45)

    def test_reuse_engine(self):
        """Test reuse suggestions and industrial matches generation."""
        engine = ReuseEngine()
        material = MaterialAnalysis(
            material_type="PET Bottle",
            primary_category="Plastics",
            sub_category="PET #1",
            confidence_score=0.9,
            cleanliness_level="Clean",
            physical_condition="Intact",
            recyclability_score=85,
        )
        suggestions = engine.generate_suggestions([], material)
        self.assertGreater(len(suggestions), 0)
        self.assertIsInstance(suggestions[0], ReuseSuggestion)

        industry_matches = engine.get_industry_matches(material)
        self.assertIsInstance(industry_matches, list)
        self.assertGreater(len(industry_matches), 0)

    def test_end_to_end_analyzer(self):
        """Test full WasteAnalyzer pipeline with mocked vision output."""
        analyzer = WasteAnalyzer()
        mock_ai_output = {
            "material_type": "Polyethylene Terephthalate (PET Plastic)",
            "primary_category": "Plastics",
            "sub_category": "Rigid Bottle (Type #1)",
            "confidence_score": 0.95,
            "cleanliness_level": "Clean",
            "physical_condition": "Intact",
            "recyclability_score": 90,
            "detected_features": ["Clear body", "Neck thread"],
            "hazardous_elements": ["None"],
            "handling_instructions": ["Rinse residues"],
            "summary": "Clear PET container in pristine condition.",
            "reuse_suggestions": [
                {
                    "title": "Sub-irrigated planter",
                    "category": "DIY / Household",
                    "difficulty": "Easy",
                    "estimated_time": "15 mins",
                    "tools_required": ["Scissors"],
                    "step_by_step_guide": ["Cut bottle", "Plant seed"],
                    "environmental_benefit": "Reuses plastic directly.",
                    "carbon_offset_rating": "Medium",
                }
            ],
            "potential_industry_matches": ["rPET fiber spinners"],
            "is_demo_mode": False,
            "metadata": {"latency_seconds": 0.5},
        }

        with patch.object(analyzer.ai_client, "analyze_image", return_value=mock_ai_output):
            result = analyzer.analyze(self.sample_img)

            self.assertIsInstance(result, WasteAnalysisResult)
            self.assertIsInstance(result.material, MaterialAnalysis)
            self.assertEqual(result.material.primary_category, "Plastics")
            self.assertGreater(len(result.reuse_suggestions), 0)
            self.assertGreater(len(result.potential_industry_matches), 0)

            # Test JSON serialization and round-trip
            json_output = result.to_json()
            self.assertIsInstance(json_output, str)
            parsed = json.loads(json_output)
            self.assertEqual(parsed["material"]["primary_category"], result.material.primary_category)

            # Test from_dict reconstructor
            reconstructed = WasteAnalysisResult.from_dict(parsed)
            self.assertEqual(reconstructed.material.material_type, result.material.material_type)


if __name__ == "__main__":
    unittest.main()
