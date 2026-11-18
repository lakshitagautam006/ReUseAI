"""Unit and UI tests for Phase 7 – Impact Dashboard analytics and rendering.

Covers:
- Read-only database aggregation functions in src/database/repository.py (populated and empty results).
- Impact Dashboard rendering in app.py under populated, single-day, empty-database, and database-error states.
- Navigation from the Impact Dashboard to Analyze Waste and Analysis History.
"""

from contextlib import ExitStack, contextmanager
from datetime import date
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch
from streamlit.testing.v1 import AppTest

from src.database import connection as db_connection
from src.database import repository

APP_PATH = str(Path(__file__).resolve().parents[1] / "app.py")
APP_TIMEOUT = 10


def _mock_db_connection(fetchone_results=None, fetchall_results=None):
    """Create a context-manager-compatible mock connection and cursor."""
    cursor = MagicMock()
    if fetchone_results is not None:
        cursor.fetchone.side_effect = list(fetchone_results)
    if fetchall_results is not None:
        cursor.fetchall.side_effect = list(fetchall_results)

    conn = MagicMock()
    conn.__enter__.return_value = conn
    conn.__exit__.return_value = False
    conn.cursor.return_value.__enter__.return_value = cursor
    conn.cursor.return_value.__exit__.return_value = False
    return conn, cursor


def _sample_populated_payload():
    """Return representative mocked aggregation outputs for a populated database."""
    return {
        "summary": {
            "total_analyses": 6,
            "unique_categories": 3,
            "recyclable_count": 5,
            "recyclable_rate": 83.3,
            "high_viability_count": 4,
            "avg_recyclability_score": 82.5,
            "avg_confidence_score": 0.93,
            "total_reuse_suggestions": 14,
            "avg_suggestions_per_analysis": 2.3,
            "total_matched_opportunities": 11,
            "avg_match_score": 87.4,
        },
        "categories": [
            {
                "primary_category": "Plastics",
                "count": 3,
                "avg_recyclability_score": 85.0,
                "avg_confidence_score": 0.94,
            },
            {
                "primary_category": "Glass",
                "count": 2,
                "avg_recyclability_score": 92.0,
                "avg_confidence_score": 0.95,
            },
            {
                "primary_category": "Metals",
                "count": 1,
                "avg_recyclability_score": 56.0,
                "avg_confidence_score": 0.88,
            },
        ],
        "daily": [
            {"date": date(2026, 11, 17), "count": 2},
            {"date": date(2026, 11, 18), "count": 4},
        ],
        "qual": {
            "conditions": [
                {"physical_condition": "Intact", "count": 4},
                {"physical_condition": "Slightly Damaged", "count": 2},
            ],
            "cleanliness": [
                {"cleanliness_level": "Clean", "count": 5},
                {"cleanliness_level": "Lightly Soiled", "count": 1},
            ],
        },
        "reuse_opp": {
            "carbon_offset_ratings": [
                {"rating": "High", "count": 8},
                {"rating": "Medium", "count": 6},
            ],
            "difficulty_levels": [
                {"difficulty": "Easy", "count": 9},
                {"difficulty": "Moderate", "count": 5},
            ],
            "opportunity_categories": [
                {
                    "opportunity_category": "Urban Agriculture",
                    "count": 6,
                    "avg_match_score": 89.0,
                },
                {
                    "opportunity_category": "Makerspace",
                    "count": 5,
                    "avg_match_score": 85.5,
                },
            ],
        },
        "top_materials": [
            {
                "material_type": "PET Bottle",
                "primary_category": "Plastics",
                "count": 3,
                "avg_recyclability_score": 85.0,
                "avg_confidence_score": 0.94,
            },
            {
                "material_type": "Clear Glass Jar",
                "primary_category": "Glass",
                "count": 2,
                "avg_recyclability_score": 92.0,
                "avg_confidence_score": 0.95,
            },
        ],
    }


class TestRepositoryAggregations(unittest.TestCase):
    """Test read-only aggregation functions in src/database/repository.py."""

    def test_get_impact_summary_populated(self):
        conn, cursor = _mock_db_connection(
            fetchone_results=[
                (10, 4, 8, 6, 78.45, 0.91234),
                (25,),
                (18, 84.67),
            ]
        )
        with patch.object(repository, "get_connection", return_value=conn):
            summary = repository.get_impact_summary()

        self.assertEqual(summary["total_analyses"], 10)
        self.assertEqual(summary["unique_categories"], 4)
        self.assertEqual(summary["recyclable_count"], 8)
        self.assertEqual(summary["recyclable_rate"], 80.0)
        self.assertEqual(summary["high_viability_count"], 6)
        self.assertEqual(summary["avg_recyclability_score"], 78.5)
        self.assertEqual(summary["avg_confidence_score"], 0.9123)
        self.assertEqual(summary["total_reuse_suggestions"], 25)
        self.assertEqual(summary["avg_suggestions_per_analysis"], 2.5)
        self.assertEqual(summary["total_matched_opportunities"], 18)
        self.assertEqual(summary["avg_match_score"], 84.7)
        self.assertEqual(cursor.execute.call_count, 3)

    def test_get_impact_summary_empty_database(self):
        conn, _ = _mock_db_connection(
            fetchone_results=[
                (0, 0, 0, 0, None, None),
                (0,),
                (0, None),
            ]
        )
        with patch.object(repository, "get_connection", return_value=conn):
            summary = repository.get_impact_summary()

        self.assertEqual(summary["total_analyses"], 0)
        self.assertEqual(summary["recyclable_rate"], 0.0)
        self.assertEqual(summary["avg_recyclability_score"], 0.0)
        self.assertEqual(summary["avg_confidence_score"], 0.0)
        self.assertEqual(summary["avg_suggestions_per_analysis"], 0.0)
        self.assertEqual(summary["total_matched_opportunities"], 0)
        self.assertEqual(summary["avg_match_score"], 0.0)

    def test_get_category_distribution(self):
        conn, _ = _mock_db_connection(
            fetchall_results=[
                [
                    ("Plastics", 5, 86.4, 0.94123),
                    ("Glass", 3, 95.0, 0.96),
                ]
            ]
        )
        with patch.object(repository, "get_connection", return_value=conn):
            result = repository.get_category_distribution()

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["primary_category"], "Plastics")
        self.assertEqual(result[0]["count"], 5)
        self.assertEqual(result[0]["avg_recyclability_score"], 86.4)
        self.assertEqual(result[0]["avg_confidence_score"], 0.9412)

    def test_get_analyses_over_time_all_and_windowed(self):
        conn, _ = _mock_db_connection(
            fetchall_results=[
                [(date(2026, 11, 16), 2), (date(2026, 11, 17), 4)]
            ]
        )
        with patch.object(repository, "get_connection", return_value=conn):
            rows = repository.get_analyses_over_time()

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], {"date": date(2026, 11, 16), "count": 2})
        self.assertEqual(rows[1], {"date": date(2026, 11, 17), "count": 4})

        conn_w, cursor_w = _mock_db_connection(fetchall_results=[[]])
        with patch.object(repository, "get_connection", return_value=conn_w):
            windowed = repository.get_analyses_over_time(days=30)

        self.assertEqual(windowed, [])
        args = cursor_w.execute.call_args[0]
        self.assertEqual(args[1], (30,))

    def test_get_condition_and_cleanliness_breakdown(self):
        conn, _ = _mock_db_connection(
            fetchall_results=[
                [("Intact", 6), ("Slightly Damaged", 2)],
                [("Clean", 5), ("Lightly Soiled", 3)],
            ]
        )
        with patch.object(repository, "get_connection", return_value=conn):
            breakdown = repository.get_condition_and_cleanliness_breakdown()

        self.assertEqual(
            breakdown["conditions"],
            [
                {"physical_condition": "Intact", "count": 6},
                {"physical_condition": "Slightly Damaged", "count": 2},
            ],
        )
        self.assertEqual(
            breakdown["cleanliness"],
            [
                {"cleanliness_level": "Clean", "count": 5},
                {"cleanliness_level": "Lightly Soiled", "count": 3},
            ],
        )

    def test_get_reuse_and_opportunity_stats(self):
        conn, _ = _mock_db_connection(
            fetchall_results=[
                [("High", 10), ("Medium", 7)],
                [("Easy", 11), ("Moderate", 6)],
                [("Urban Agriculture", 5, 88.25), ("Recycling", 4, None)],
            ]
        )
        with patch.object(repository, "get_connection", return_value=conn):
            stats = repository.get_reuse_and_opportunity_stats(top_n=5)

        self.assertEqual(stats["carbon_offset_ratings"][0], {"rating": "High", "count": 10})
        self.assertEqual(stats["difficulty_levels"][0], {"difficulty": "Easy", "count": 11})
        self.assertEqual(
            stats["opportunity_categories"],
            [
                {"opportunity_category": "Urban Agriculture", "count": 5, "avg_match_score": 88.2},
                {"opportunity_category": "Recycling", "count": 4, "avg_match_score": 0.0},
            ],
        )

    def test_get_top_materials(self):
        conn, _ = _mock_db_connection(
            fetchall_results=[
                [("PET Plastic", "Plastics", 4, 89.5, 0.955)]
            ]
        )
        with patch.object(repository, "get_connection", return_value=conn):
            top = repository.get_top_materials(limit=5)

        self.assertEqual(
            top,
            [
                {
                    "material_type": "PET Plastic",
                    "primary_category": "Plastics",
                    "count": 4,
                    "avg_recyclability_score": 89.5,
                    "avg_confidence_score": 0.955,
                }
            ],
        )


class TestImpactDashboardUI(unittest.TestCase):
    """Verify Impact Dashboard rendering across populated, single-day, empty, and error states."""

    @contextmanager
    def _mock_dashboard_dependencies(
        self,
        *,
        summary=None,
        summary_side_effect=None,
        categories=None,
        daily=None,
        qual=None,
        reuse_opp=None,
        top_materials=None,
    ):
        """Patch all repository functions imported by app.py and block real DB connections."""
        with ExitStack() as stack:
            guard_conn = stack.enter_context(
                patch.object(
                    db_connection,
                    "get_connection",
                    side_effect=AssertionError("UI test attempted a real DB connection"),
                )
            )
            guard_repo_conn = stack.enter_context(
                patch.object(
                    repository,
                    "get_connection",
                    side_effect=AssertionError("UI test attempted a real DB connection"),
                )
            )

            summary_kwargs = (
                {"side_effect": summary_side_effect}
                if summary_side_effect is not None
                else {"return_value": summary}
            )
            mocks = {
                "guard_conn": guard_conn,
                "guard_repo_conn": guard_repo_conn,
                "get_impact_summary": stack.enter_context(
                    patch.object(repository, "get_impact_summary", **summary_kwargs)
                ),
                "get_category_distribution": stack.enter_context(
                    patch.object(
                        repository,
                        "get_category_distribution",
                        return_value=categories if categories is not None else [],
                    )
                ),
                "get_analyses_over_time": stack.enter_context(
                    patch.object(
                        repository,
                        "get_analyses_over_time",
                        return_value=daily if daily is not None else [],
                    )
                ),
                "get_condition_and_cleanliness_breakdown": stack.enter_context(
                    patch.object(
                        repository,
                        "get_condition_and_cleanliness_breakdown",
                        return_value=qual if qual is not None else {"conditions": [], "cleanliness": []},
                    )
                ),
                "get_reuse_and_opportunity_stats": stack.enter_context(
                    patch.object(
                        repository,
                        "get_reuse_and_opportunity_stats",
                        return_value=reuse_opp
                        if reuse_opp is not None
                        else {
                            "carbon_offset_ratings": [],
                            "difficulty_levels": [],
                            "opportunity_categories": [],
                        },
                    )
                ),
                "get_top_materials": stack.enter_context(
                    patch.object(
                        repository,
                        "get_top_materials",
                        return_value=top_materials if top_materials is not None else [],
                    )
                ),
                "get_all_analyses": stack.enter_context(
                    patch.object(repository, "get_all_analyses", return_value=[])
                ),
                "get_analysis_by_id": stack.enter_context(
                    patch.object(repository, "get_analysis_by_id", return_value=None)
                ),
            }
            yield mocks

    def _open_impact_dashboard(self):
        """Instantiate AppTest using an absolute path and navigate to Impact Dashboard."""
        self.assertTrue(Path(APP_PATH).is_file(), f"app.py not found at {APP_PATH}")
        at = AppTest.from_file(APP_PATH, default_timeout=APP_TIMEOUT)
        at.run(timeout=APP_TIMEOUT)
        self.assertFalse(at.exception, f"Initial Home render failed: {at.exception}")
        at.sidebar.radio[0].set_value("Impact Dashboard").run(timeout=APP_TIMEOUT)
        return at

    def test_populated_dashboard_rendering_and_analyze_navigation(self):
        data = _sample_populated_payload()
        with self._mock_dashboard_dependencies(
            summary=data["summary"],
            categories=data["categories"],
            daily=data["daily"],
            qual=data["qual"],
            reuse_opp=data["reuse_opp"],
            top_materials=data["top_materials"],
        ) as mocks:
            at = self._open_impact_dashboard()
            self.assertFalse(at.exception)
            self.assertEqual(at.session_state["selected_page"], "Impact Dashboard")

            # Confirm all 6 aggregation helpers ran and no real DB connection was attempted
            mocks["get_impact_summary"].assert_called_once()
            mocks["get_category_distribution"].assert_called_once()
            mocks["get_analyses_over_time"].assert_called_once()
            mocks["get_condition_and_cleanliness_breakdown"].assert_called_once()
            mocks["get_reuse_and_opportunity_stats"].assert_called_once()
            mocks["get_top_materials"].assert_called_once()
            mocks["guard_conn"].assert_not_called()
            mocks["guard_repo_conn"].assert_not_called()

            all_markdown = " ".join(m.value for m in at.markdown)
            self.assertIn("Total Analyses", all_markdown)
            self.assertIn("83.3%", all_markdown)
            self.assertIn("Data Integrity Note", all_markdown)
            self.assertEqual(len(at.dataframe), 1)

            # Verify primary button navigates to Analyze Waste
            self.assertGreaterEqual(len(at.button), 2)
            self.assertIn("Return to Waste Analysis", at.button[0].label)
            at.button[0].click().run(timeout=APP_TIMEOUT)
            self.assertFalse(at.exception)
            self.assertEqual(at.session_state["selected_page"], "Analyze Waste")

    def test_populated_dashboard_history_navigation(self):
        data = _sample_populated_payload()
        with self._mock_dashboard_dependencies(
            summary=data["summary"],
            categories=data["categories"],
            daily=data["daily"],
            qual=data["qual"],
            reuse_opp=data["reuse_opp"],
            top_materials=data["top_materials"],
        ) as mocks:
            at = self._open_impact_dashboard()
            self.assertFalse(at.exception)
            self.assertIn("View Analysis History", at.button[1].label)

            at.button[1].click().run(timeout=APP_TIMEOUT)
            self.assertFalse(at.exception)
            self.assertEqual(at.session_state["selected_page"], "Analysis History")
            mocks["get_all_analyses"].assert_called_once()
            mocks["guard_conn"].assert_not_called()
            mocks["guard_repo_conn"].assert_not_called()

    def test_single_day_activity_rendering(self):
        mock_summary = {
            "total_analyses": 1,
            "unique_categories": 1,
            "recyclable_count": 1,
            "recyclable_rate": 100.0,
            "high_viability_count": 1,
            "avg_recyclability_score": 90.0,
            "avg_confidence_score": 0.95,
            "total_reuse_suggestions": 2,
            "avg_suggestions_per_analysis": 2.0,
            "total_matched_opportunities": 1,
            "avg_match_score": 91.0,
        }
        with self._mock_dashboard_dependencies(
            summary=mock_summary,
            categories=[
                {
                    "primary_category": "Plastics",
                    "count": 1,
                    "avg_recyclability_score": 90.0,
                    "avg_confidence_score": 0.95,
                }
            ],
            daily=[{"date": date(2026, 11, 18), "count": 1}],
            qual={
                "conditions": [{"physical_condition": "Intact", "count": 1}],
                "cleanliness": [{"cleanliness_level": "Clean", "count": 1}],
            },
            reuse_opp={
                "carbon_offset_ratings": [{"rating": "High", "count": 2}],
                "difficulty_levels": [{"difficulty": "Easy", "count": 2}],
                "opportunity_categories": [
                    {"opportunity_category": "Recycling", "count": 1, "avg_match_score": 91.0}
                ],
            },
            top_materials=[
                {
                    "material_type": "PET",
                    "primary_category": "Plastics",
                    "count": 1,
                    "avg_recyclability_score": 90.0,
                    "avg_confidence_score": 0.95,
                }
            ],
        ) as mocks:
            at = self._open_impact_dashboard()
            self.assertFalse(at.exception)
            self.assertEqual(len(at.dataframe), 1)
            mocks["guard_conn"].assert_not_called()
            mocks["guard_repo_conn"].assert_not_called()

    def test_empty_database_state(self):
        empty_summary = {
            "total_analyses": 0,
            "unique_categories": 0,
            "recyclable_count": 0,
            "recyclable_rate": 0.0,
            "high_viability_count": 0,
            "avg_recyclability_score": 0.0,
            "avg_confidence_score": 0.0,
            "total_reuse_suggestions": 0,
            "avg_suggestions_per_analysis": 0.0,
            "total_matched_opportunities": 0,
            "avg_match_score": 0.0,
        }
        with self._mock_dashboard_dependencies(summary=empty_summary) as mocks:
            at = self._open_impact_dashboard()
            self.assertFalse(at.exception)
            self.assertEqual(len(at.info), 1)
            self.assertIn("No saved waste analyses found yet", at.info[0].value)

            # Downstream queries should not run when total_analyses == 0
            mocks["get_category_distribution"].assert_not_called()
            mocks["get_analyses_over_time"].assert_not_called()
            mocks["get_condition_and_cleanliness_breakdown"].assert_not_called()
            mocks["get_reuse_and_opportunity_stats"].assert_not_called()
            mocks["get_top_materials"].assert_not_called()
            mocks["guard_conn"].assert_not_called()
            mocks["guard_repo_conn"].assert_not_called()

            at.button[0].click().run(timeout=APP_TIMEOUT)
            self.assertFalse(at.exception)
            self.assertEqual(at.session_state["selected_page"], "Analyze Waste")

    def test_database_error_state(self):
        with self._mock_dashboard_dependencies(
            summary_side_effect=RuntimeError("Simulated PostgreSQL outage"),
        ) as mocks:
            at = self._open_impact_dashboard()
            self.assertFalse(at.exception)
            self.assertEqual(len(at.error), 1)
            self.assertIn("Simulated PostgreSQL outage", at.error[0].value)

            mocks["get_category_distribution"].assert_not_called()
            mocks["guard_conn"].assert_not_called()
            mocks["guard_repo_conn"].assert_not_called()

            at.button[0].click().run(timeout=APP_TIMEOUT)
            self.assertFalse(at.exception)
            self.assertEqual(at.session_state["selected_page"], "Analyze Waste")


if __name__ == "__main__":
    unittest.main()
