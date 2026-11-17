"""Test suite for Streamlit navigation state management in ReUseAI."""

import unittest
from streamlit.testing.v1 import AppTest


class TestStreamlitNavigation(unittest.TestCase):

    def test_navigation_flow(self):
        """Verify seamless navigation between sidebar and in-page CTA buttons."""
        at = AppTest.from_file("../app.py", default_timeout=10)
        at.run(timeout=10)
        self.assertFalse(at.exception, f"Initial run raised exception: {at.exception}")
        self.assertEqual(at.session_state["selected_page"], "Home")

        # Step 1: Click 'Start Analyzing' CTA button on Home
        at.button[0].click().run(timeout=10)
        self.assertFalse(at.exception, f"Clicking Start Analyzing raised exception: {at.exception}")
        self.assertEqual(at.session_state["selected_page"], "Analyze Waste")

        # Step 2: Switch via sidebar radio to 'About'
        at.sidebar.radio[0].set_value("About").run(timeout=10)
        self.assertFalse(at.exception, f"Sidebar switch to About raised exception: {at.exception}")
        self.assertEqual(at.session_state["selected_page"], "About")

        # Step 3: Switch via sidebar radio to 'Analysis Results'
        at.sidebar.radio[0].set_value("Analysis Results").run(timeout=10)
        self.assertFalse(at.exception, f"Sidebar switch to Results raised exception: {at.exception}")
        self.assertEqual(at.session_state["selected_page"], "Analysis Results")

        # Step 4: Click 'Go to Analyze Waste' button on the empty results page
        at.button[0].click().run(timeout=10)
        self.assertFalse(at.exception, f"Navigating back from Results raised exception: {at.exception}")
        self.assertEqual(at.session_state["selected_page"], "Analyze Waste")

        # Step 5: Switch back to Home via sidebar
        at.sidebar.radio[0].set_value("Home").run(timeout=10)
        self.assertFalse(at.exception, f"Sidebar switch back to Home raised exception: {at.exception}")
        self.assertEqual(at.session_state["selected_page"], "Home")


if __name__ == "__main__":
    unittest.main()
