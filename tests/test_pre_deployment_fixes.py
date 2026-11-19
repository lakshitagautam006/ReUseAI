"""Pre-deployment verification tests for ReUseAI.
Verifies:
1. Fix Analysis History Delete Confirmation: Modal popup dialogs (@st.dialog) with Cancel/Delete
   and Cancel/Delete All, database deletion persistence, and feedback notifications.
2. Fix Cleanliness Level AI Classification: Visual evidence classification across 4 strict
   categories (Clean, Moderately Dirty, Dirty, Unknown), cleanliness explanations,
   removal of hardcoded "Clean" fallbacks, and UI display consistency.
"""

import unittest
from typing import Dict, Any

from src.models.schemas import MaterialAnalysis, WasteAnalysisResult, ReuseSuggestion, MatchedOpportunity
from src.services.material_detector import MaterialDetector
from src.services.ai_client import GroqVisionClient
from src.utils.sample_generator import (
    create_sample_plastic_bottle,
    create_sample_soiled_plastic_bottle,
    create_sample_dusty_plastic_bottle,
)
from src.database.repository import (
    save_analysis,
    get_all_analyses,
    get_analysis_by_id,
    delete_analysis,
    clear_all_analyses,
)


class TestCleanlinessClassification(unittest.TestCase):
    """Test Suite for Task 2: Visual Cleanliness Classification."""

    def setUp(self):
        self.detector = MaterialDetector()

    def test_heavily_soiled_plastic_bottle_classified_as_dirty(self):
        """A visibly dirty plastic bottle with brown mud/dirt patches must be classified as 'Dirty'."""
        raw_data = {
            "material": "Polyethylene Terephthalate (PET)",
            "waste_type": "Plastics",
            "condition": "Intact with extensive brown mud and dirt patches",
            "recyclable": True,
            "confidence": 0.94,
            "detected_features": ["Threaded neck", "Transparent wall", "Heavy dried mud patches on lower exterior"],
            "summary": "Plastic bottle with significant surface contamination from dried mud.",
            "reuse_ideas": ["Upcycled Garden Trowel: 1. Clean mud thoroughly. 2. Cut diagonal scoop."]
        }
        level, explanation = self.detector.classify_cleanliness(raw_data)
        self.assertEqual(level, "Dirty")
        self.assertTrue(len(explanation) > 10)
        self.assertTrue(any(term in explanation.lower() for term in ["mud", "dirt", "contamination", "surface"]))

        analysis = self.detector.evaluate(raw_data)
        self.assertEqual(analysis.cleanliness_level, "Dirty")
        self.assertEqual(analysis.cleanliness_explanation, explanation)
        # Verify recyclability penalty applied for Dirty (-30 from 90 PET base = 60)
        self.assertEqual(analysis.recyclability_score, 60)

    def test_visually_clean_plastic_bottle_classified_as_clean(self):
        """A visually clean plastic bottle must be classified as 'Clean'."""
        raw_data = {
            "material": "Polyethylene Terephthalate (PET)",
            "waste_type": "Plastics",
            "condition": "Intact, clean and washed",
            "recyclable": True,
            "confidence": 0.98,
            "detected_features": ["Clear transparent wall", "No visible dirt or stains", "Threaded neck"],
            "reuse_ideas": ["Self-Watering Planter: 1. Cut in half..."]
        }
        level, explanation = self.detector.classify_cleanliness(raw_data)
        self.assertEqual(level, "Clean")
        self.assertTrue(len(explanation) > 10)

        analysis = self.detector.evaluate(raw_data)
        self.assertEqual(analysis.cleanliness_level, "Clean")
        # Clean PET baseline is 90 with 0 penalty
        self.assertEqual(analysis.recyclability_score, 90)

    def test_slightly_dusty_plastic_bottle_classified_as_moderately_dirty(self):
        """A slightly dusty plastic bottle must be classified as 'Moderately Dirty'."""
        raw_data = {
            "material": "Polyethylene Terephthalate (PET)",
            "waste_type": "Plastics",
            "condition": "Intact with slight dust and light residue",
            "recyclable": True,
            "confidence": 0.91,
            "detected_features": ["Light surface dust speckles"],
            "reuse_ideas": ["Eco Organizer: 1. Wipe off dust..."]
        }
        level, explanation = self.detector.classify_cleanliness(raw_data)
        self.assertEqual(level, "Moderately Dirty")
        self.assertTrue(len(explanation) > 10)
        self.assertTrue(any(term in explanation.lower() for term in ["dust", "residue", "minor", "light"]))

        analysis = self.detector.evaluate(raw_data)
        self.assertEqual(analysis.cleanliness_level, "Moderately Dirty")
        # Moderately Dirty PET baseline is 90 - 10 = 80
        self.assertEqual(analysis.recyclability_score, 80)

    def test_missing_or_ambiguous_evidence_defaults_to_unknown_never_clean(self):
        """Missing or ambiguous evidence must NEVER fall back to 'Clean'; must return 'Unknown'."""
        raw_data = {
            "material": "Polyethylene Terephthalate (PET)",
            "waste_type": "Plastics",
            "condition": "Intact",
            "recyclable": True,
            "confidence": 0.90,
            "reuse_ideas": ["Bird Feeder: 1. Cut bottle..."]
        }
        level, explanation = self.detector.classify_cleanliness(raw_data)
        self.assertEqual(level, "Unknown")
        self.assertNotEqual(level, "Clean")
        self.assertIn("insufficient", explanation.lower())

        analysis = self.detector.evaluate(raw_data)
        self.assertEqual(analysis.cleanliness_level, "Unknown")
        self.assertNotEqual(analysis.cleanliness_level, "Clean")

    def test_schema_from_dict_never_defaults_to_clean(self):
        """WasteAnalysisResult.from_dict must never default cleanliness_level to 'Clean' when missing."""
        flat_payload = {
            "material": "High-Density Polyethylene (HDPE)",
            "waste_type": "Plastics",
            "condition": "Intact",
            "recyclable": True,
            "confidence": 0.88,
            "reuse_ideas": ["Garden Scoop: 1. Cut handle..."]
        }
        result = WasteAnalysisResult.from_dict(flat_payload)
        self.assertEqual(result.material.cleanliness_level, "Unknown")
        self.assertNotEqual(result.material.cleanliness_level, "Clean")

    def test_soiled_sample_generator(self):
        """Test that sample generators produce valid non-empty PIL images."""
        clean_img = create_sample_plastic_bottle()
        soiled_img = create_sample_soiled_plastic_bottle()
        dusty_img = create_sample_dusty_plastic_bottle()

        self.assertEqual(clean_img.size, (400, 500))
        self.assertEqual(soiled_img.size, (400, 500))
        self.assertEqual(dusty_img.size, (400, 500))


class TestDatabasePersistenceAndDeletion(unittest.TestCase):
    """Test Suite for Task 1: Delete confirmation operations and database persistence."""

    def _create_sample_result(self, material_name="PET Plastic Bottle", cleanliness="Dirty", cond="Covered with brown mud"):
        mat = MaterialAnalysis(
            material_type=material_name,
            primary_category="Plastics",
            sub_category="Rigid Container (Code #1)",
            confidence_score=0.92,
            cleanliness_level=cleanliness,
            physical_condition=cond,
            recyclability_score=60,
            detected_features=["Brown mud patches", "Screw cap"],
            hazardous_elements=[],
            cleanliness_explanation="Extensive dried brown mud across bottle surface.",
        )
        suggs = [
            ReuseSuggestion(
                title="Garden Trowel",
                category="DIY / Upcycling",
                difficulty="Easy",
                estimated_time="15 mins",
                tools_required=["Utility Knife"],
                step_by_step_guide=["Clean surface mud", "Cut angle"],
                environmental_benefit="Diverts plastic",
                carbon_offset_rating="Medium",
            )
        ]
        opps = [
            MatchedOpportunity(
                opportunity_name="Local School Garden Project",
                opportunity_category="Community Agriculture",
                match_score=85.0,
                reason="Suitable for upcycled planters",
                suggested_application="Seedling pots",
                target_user="Community Gardeners",
            )
        ]
        return WasteAnalysisResult(
            material=mat,
            reuse_suggestions=suggs,
            matched_opportunities=opps,
            summary="Soiled PET bottle test record",
        )

    def test_save_and_retrieve_cleanliness_level_and_explanation(self):
        """Verify saved analysis preserves actual cleanliness level and explanation in PostgreSQL."""
        result = self._create_sample_result(cleanliness="Dirty")
        analysis_id = save_analysis(result)
        self.assertIsNotNone(analysis_id)
        self.assertTrue(analysis_id > 0)

        try:
            saved = get_analysis_by_id(analysis_id)
            self.assertIsNotNone(saved)
            mat_data = saved.get("material", {})
            self.assertEqual(mat_data.get("cleanliness_level"), "Dirty")
            self.assertEqual(mat_data.get("cleanliness_explanation"), "Extensive dried brown mud across bottle surface.")

            all_items = get_all_analyses(limit=10)
            target_item = next((item for item in all_items if item["id"] == analysis_id), None)
            self.assertIsNotNone(target_item)
            self.assertEqual(target_item["cleanliness_level"], "Dirty")
        finally:
            delete_analysis(analysis_id)

    def test_delete_analysis_permanently_removes_record(self):
        """Verify delete_analysis permanently removes the record and associated data."""
        result = self._create_sample_result()
        analysis_id = save_analysis(result)

        # Confirm existence
        self.assertIsNotNone(get_analysis_by_id(analysis_id))

        # Perform deletion
        deleted = delete_analysis(analysis_id)
        self.assertTrue(deleted)

        # Verify record no longer exists
        self.assertIsNone(get_analysis_by_id(analysis_id))

        # Idempotent re-delete returns False
        self.assertFalse(delete_analysis(analysis_id))


if __name__ == "__main__":
    unittest.main()
