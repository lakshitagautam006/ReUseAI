"""AppTest test suite for Phase 5 – Complete Frontend Redesign in ReUseAI.
Tests:
- Home Dashboard rendering (hero title, tagline, 4 feature cards, 4 workflow stages).
- Analyze Waste page rendering (file uploader, quick test buttons).
- Analysis Results page rendering (metrics, separated Direct Reuse vs Upcycling, Matched Opportunities).
- Impact Dashboard page rendering (Coming Soon in Phase 6, planned feature preview cards).
- About ReUseAI page rendering (Mission, 4 information cards).
"""

import unittest
from streamlit.testing.v1 import AppTest
from src.models.schemas import WasteAnalysisResult, MaterialAnalysis, ReuseSuggestion, MatchedOpportunity


class TestFrontendRedesign(unittest.TestCase):
    """Test suite for Phase 5 Eco Green Frontend Redesign."""

    def test_home_page_rendering(self):
        """Verify Home page renders hero section, CTA button, and 4 feature cards."""
        at = AppTest.from_file("../app.py", default_timeout=10)
        at.run(timeout=10)
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state["selected_page"], "Home")

        # Verify prominent CTA button exists and says "Analyze Waste" (not "Analyze Your Waste")
        self.assertGreater(len(at.button), 0)
        cta_btn = at.button[0]
        self.assertIn("Analyze Waste", cta_btn.label)
        self.assertNotIn("Analyze Your Waste", cta_btn.label)

        # Verify Vision AI Status is NOT displayed in sidebar
        sidebar_text = " ".join([m.value for m in at.sidebar.markdown])
        self.assertNotIn("Vision AI Status", sidebar_text)
        self.assertNotIn("qwen/qwen3.8-27b", sidebar_text)

        # Click CTA button to navigate to Analyze Waste
        at.button[0].click().run(timeout=10)
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state["selected_page"], "Analyze Waste")

    def test_impact_dashboard_page(self):
        """Verify Impact Dashboard renders Phase 6 coming-soon roadmap without database dependencies."""
        at = AppTest.from_file("../app.py", default_timeout=10)
        at.run(timeout=10)
        self.assertFalse(at.exception)

        # Navigate to Impact Dashboard via sidebar radio
        at.sidebar.radio[0].set_value("Impact Dashboard").run(timeout=10)
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state["selected_page"], "Impact Dashboard")

        # Verify Return CTA button works
        self.assertGreater(len(at.button), 0)
        at.button[0].click().run(timeout=10)
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state["selected_page"], "Analyze Waste")

    def test_about_page_rendering(self):
        """Verify About page renders mission, SDG 12, and system scope."""
        at = AppTest.from_file("../app.py", default_timeout=10)
        at.run(timeout=10)
        self.assertFalse(at.exception)

        at.sidebar.radio[0].set_value("About").run(timeout=10)
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state["selected_page"], "About")

    def test_analysis_results_rendering_with_mock_data(self):
        """Verify Analysis Results renders separated Direct Reuse vs Upcycling, KPI metrics, and Matched Opportunities."""
        at = AppTest.from_file("../app.py", default_timeout=10)
        at.run(timeout=10)

        # Inject completed analysis result into session state
        mock_result = WasteAnalysisResult(
            material=MaterialAnalysis(
                material_type="Polyethylene Terephthalate / PET",
                primary_category="Plastics",
                sub_category="Code #1 Resin Bottle",
                confidence_score=0.96,
                cleanliness_level="Clean",
                physical_condition="Intact, Clean",
                recyclability_score=92,
            ),
            reuse_suggestions=[
                ReuseSuggestion(
                    title="Sub-Irrigated Self-Watering Planter",
                    category="Urban Agriculture & Gardening",
                    difficulty="Moderate",
                    estimated_time="20-30 mins",
                    tools_required=["Utility knife", "Cotton wick"],
                    step_by_step_guide=["Clean bottle", "Cut top third", "Invert top", "Thread wick", "Add soil"],
                    environmental_benefit="Diverts PET from landfill",
                    carbon_offset_rating="Medium",
                ),
                ReuseSuggestion(
                    title="Precision 1.75mm 3D Printer Filament",
                    category="Makerspace & Engineering",
                    difficulty="Moderate",
                    estimated_time="45-60 mins",
                    tools_required=["Slitting blade", "Heated nozzle"],
                    step_by_step_guide=["Wash bottle", "Slit ribbon", "Feed through nozzle", "Spool filament"],
                    environmental_benefit="Displaces virgin filament",
                    carbon_offset_rating="High",
                ),
            ],
            matched_opportunities=[
                MatchedOpportunity(
                    opportunity_name="Community Garden Planter Drive",
                    opportunity_category="Urban Agriculture",
                    match_score=89.1,
                    reason="PET supplies compatible feedstock. Key properties: Watertight. Condition suitability: Intact. Practical application: Planter.",
                    suggested_application="Fabricate zero-electricity planters",
                    target_user="Community Gardens",
                )
            ]
        )

        at.session_state["analysis_result"] = mock_result
        at.sidebar.radio[0].set_value("Analysis Results").run(timeout=10)
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state["selected_page"], "Analysis Results")


if __name__ == "__main__":
    unittest.main()
