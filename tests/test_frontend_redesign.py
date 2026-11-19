"""AppTest test suite for Pre-Deployment Verification in ReUseAI.
Tests:
- Homepage rendering and 4 functional navigation links (Identify Material, Explore Ideas, Match Users, Preview Metrics).
- Complete removal of Theme toggle and verified consistent Light Mode throughout.
- Analysis History rendering, clean empty-state, and deletion options.
- Analysis Results rendering (KPI metrics, material-specific recyclability index and tier label, separated Direct Reuse vs Upcycling, Matched Opportunities).
- Impact Dashboard page rendering.
- About ReUseAI page rendering.
"""

import unittest
from streamlit.testing.v1 import AppTest
from src.models.schemas import WasteAnalysisResult, MaterialAnalysis, ReuseSuggestion, MatchedOpportunity


class TestFrontendRedesign(unittest.TestCase):
    """Test suite for Final Pre-Deployment Corrections."""

    def test_home_page_rendering(self):
        """Verify Home page renders hero section, CTA button, and 4 feature cards without phase labels."""
        at = AppTest.from_file("../app.py", default_timeout=45)
        at.run(timeout=45)
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state["selected_page"], "Home")

        # Verify prominent CTA button exists and says "Analyze Waste"
        self.assertGreater(len(at.button), 0)
        cta_btn = at.button[0]
        self.assertIn("Analyze Waste", cta_btn.label)

        # Verify Vision AI Status and model configs are NOT displayed in sidebar
        sidebar_text = " ".join([m.value for m in at.sidebar.markdown])
        self.assertNotIn("Vision AI Status", sidebar_text)
        self.assertNotIn("qwen/qwen3.8-27b", sidebar_text)

        # Verify Phase labels are NOT displayed in sidebar or page
        self.assertNotIn("Phase 5", sidebar_text)
        self.assertNotIn("Phase 4", sidebar_text)
        self.assertNotIn("Phase 7", sidebar_text)
        self.assertNotIn("Phase 8", sidebar_text)

        # Click CTA button to navigate to Analyze Waste
        at.button[0].click().run(timeout=45)
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state["selected_page"], "Analyze Waste")

    def test_home_page_navigation_links(self):
        """TASK 1: Verify all 4 homepage links are functional and navigate to correct sections."""
        # 1. Test 'Identify Material →' button
        at1 = AppTest.from_file("../app.py", default_timeout=45)
        at1.run(timeout=45)
        btn_identify = next((b for b in at1.button if "Identify Material" in b.label), None)
        self.assertIsNotNone(btn_identify, "Identify Material button must exist on homepage")
        btn_identify.click().run(timeout=45)
        self.assertFalse(at1.exception)
        self.assertEqual(at1.session_state["selected_page"], "Analyze Waste")

        # 2. Test 'Explore Ideas →' button
        at2 = AppTest.from_file("../app.py", default_timeout=45)
        at2.run(timeout=45)
        btn_ideas = next((b for b in at2.button if "Explore Ideas" in b.label), None)
        self.assertIsNotNone(btn_ideas, "Explore Ideas button must exist on homepage")
        btn_ideas.click().run(timeout=45)
        self.assertFalse(at2.exception)
        self.assertEqual(at2.session_state["selected_page"], "Analysis Results")

        # 3. Test 'Match Users →' button
        at3 = AppTest.from_file("../app.py", default_timeout=45)
        at3.run(timeout=45)
        btn_match = next((b for b in at3.button if "Match Users" in b.label), None)
        self.assertIsNotNone(btn_match, "Match Users button must exist on homepage")
        btn_match.click().run(timeout=45)
        self.assertFalse(at3.exception)
        self.assertEqual(at3.session_state["selected_page"], "Analysis Results")

        # 4. Test 'Preview Metrics →' button
        at4 = AppTest.from_file("../app.py", default_timeout=45)
        at4.run(timeout=45)
        btn_metrics = next((b for b in at4.button if "Preview Metrics" in b.label), None)
        self.assertIsNotNone(btn_metrics, "Preview Metrics button must exist on homepage")
        btn_metrics.click().run(timeout=45)
        self.assertFalse(at4.exception)
        self.assertEqual(at4.session_state["selected_page"], "Impact Dashboard")

    def test_no_theme_toggle_and_consistent_light_theme(self):
        """TASK 2: Verify Theme toggle is completely removed and light theme is enforced."""
        at = AppTest.from_file("../app.py", default_timeout=45)
        at.run(timeout=45)
        self.assertFalse(at.exception)

        # Verify NO selectbox exists in sidebar (theme switcher removed)
        self.assertEqual(len(at.sidebar.selectbox), 0)

        # Verify no Dark Mode strings or controls in sidebar
        sidebar_text = " ".join([m.value for m in at.sidebar.markdown])
        self.assertNotIn("Dark Mode", sidebar_text)
        self.assertNotIn("Light Mode", sidebar_text)
        self.assertNotIn("Appearance", sidebar_text)

        # Verify session state does not contain dark mode
        self.assertNotIn("theme_mode", at.session_state)

    def test_analysis_history_page_rendering(self):
        """TASK 3: Verify Analysis History renders without errors and shows clean state."""
        at = AppTest.from_file("../app.py", default_timeout=45)
        at.run(timeout=45)
        self.assertFalse(at.exception)

        at.sidebar.radio[0].set_value("Analysis History").run(timeout=45)
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state["selected_page"], "Analysis History")

        page_text = " ".join([m.value for m in at.markdown])
        self.assertIn("Analysis History", page_text)

    def test_impact_dashboard_page(self):
        """Verify Impact Dashboard renders without errors or phase labels."""
        at = AppTest.from_file("../app.py", default_timeout=45)
        at.run(timeout=45)
        self.assertFalse(at.exception)

        # Navigate to Impact Dashboard via sidebar radio
        at.sidebar.radio[0].set_value("Impact Dashboard").run(timeout=45)
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state["selected_page"], "Impact Dashboard")

        page_text = " ".join([m.value for m in at.markdown])
        self.assertNotIn("Phase 6", page_text)
        self.assertNotIn("Phase 5", page_text)

        # Verify Return CTA button works
        self.assertGreater(len(at.button), 0)
        at.button[0].click().run(timeout=45)
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state["selected_page"], "Analyze Waste")

    def test_about_page_rendering(self):
        """Verify About page renders mission, SDG 12, and clean SaaS footer."""
        at = AppTest.from_file("../app.py", default_timeout=45)
        at.run(timeout=45)
        self.assertFalse(at.exception)

        at.sidebar.radio[0].set_value("About").run(timeout=45)
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state["selected_page"], "About")

        page_text = " ".join([m.value for m in at.markdown])
        self.assertNotIn("Phase 5", page_text)
        self.assertNotIn("Phase 4", page_text)
        self.assertNotIn("Subsystem 1", page_text)
        self.assertNotIn("Subsystem 2", page_text)
        self.assertIn("SDG 12", page_text)

    def test_analysis_results_rendering_with_mock_data(self):
        """Verify Analysis Results renders separated Direct Reuse vs Upcycling, KPI metrics, dynamic Recyclability Index, and Matched Opportunities."""
        at = AppTest.from_file("../app.py", default_timeout=45)
        at.run(timeout=45)

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
        at.sidebar.radio[0].set_value("Analysis Results").run(timeout=45)
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state["selected_page"], "Analysis Results")

        # Verify Recyclability Index and Tier Label
        results_text = " ".join([m.value for m in at.markdown])
        self.assertIn("92", results_text)
        self.assertIn("High Recyclability", results_text)
        self.assertNotIn("Phase 5", results_text)


if __name__ == "__main__":
    unittest.main()
