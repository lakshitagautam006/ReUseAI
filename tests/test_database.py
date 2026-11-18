"""Database unit and integration tests for ReUseAI PostgreSQL persistence.

Verifies:
- Main analysis persistence in `analyses`.
- Reuse suggestions persistence in `reuse_suggestions`.
- Matched opportunities persistence in `matched_opportunities`.
- Complete result retrieval via `get_analysis_by_id`.
- Nonexistent and invalid analysis ID handling.
- Transaction rollback and connection configuration error handling.
"""

import json
import os
import unittest
from unittest.mock import MagicMock, patch
import psycopg

from src.database import connection as db_connection
from src.database import repository
from src.database.repository import (
    save_analysis,
    get_all_analyses,
    get_analysis_by_id,
)
from src.models.schemas import (
    MaterialAnalysis,
    ReuseSuggestion,
    MatchedOpportunity,
    WasteAnalysisResult,
)


def _build_sample_result() -> WasteAnalysisResult:
    """Create a complete WasteAnalysisResult with multiple suggestions and opportunities."""
    material = MaterialAnalysis(
        material_type="Polyethylene Terephthalate (PET)",
        primary_category="Plastics",
        sub_category="Plastic Bottle",
        confidence_score=0.95,
        cleanliness_level="Clean",
        physical_condition="Intact",
        recyclability_score=90,
        detected_features=["Transparent", "Lightweight"],
        hazardous_elements=[],
    )

    suggestions = [
        ReuseSuggestion(
            title="Self-Watering Herb Planter",
            category="Urban Agriculture & Gardening",
            difficulty="Easy",
            estimated_time="15 minutes",
            tools_required=["Scissors", "Cotton wick"],
            step_by_step_guide=[
                "Clean bottle thoroughly with warm water.",
                "Cut the bottle horizontally into upper and lower halves.",
                "Invert the top funnel into the base reservoir.",
                "Add soil and herb seedling with a cotton wick.",
            ],
            environmental_benefit="Reduces plastic waste",
            carbon_offset_rating="Medium",
        ),
        ReuseSuggestion(
            title="Modular Desk Organizer Caddy",
            category="Home Organization & Storage",
            difficulty="Easy",
            estimated_time="10 minutes",
            tools_required=["Utility knife", "Sandpaper"],
            step_by_step_guide=[
                "Wash and dry the bottle completely.",
                "Mark an even height around the lower base.",
                "Trim cleanly along the marked line.",
                "Smooth cut edges with fine sandpaper.",
            ],
            environmental_benefit="Replaces virgin plastic desk organizers",
            carbon_offset_rating="Low",
        ),
    ]

    opportunities = [
        MatchedOpportunity(
            opportunity_name="Plastic Recycling Unit",
            opportunity_category="Recycling",
            match_score=92.0,
            reason="PET plastic is recyclable and clean.",
            suggested_application="Send material for mechanical rPET pelletizing.",
            target_user="Recycling Industry",
        ),
        MatchedOpportunity(
            opportunity_name="Community Garden Planter Drive",
            opportunity_category="Urban Agriculture",
            match_score=87.5,
            reason="Intact clean PET container is suitable for passive planters.",
            suggested_application="Fabricate self-watering seedling planters.",
            target_user="Community Gardens",
        ),
    ]

    return WasteAnalysisResult(
        material=material,
        reuse_suggestions=suggestions,
        matched_opportunities=opportunities,
        handling_instructions=["Rinse and air dry before reuse."],
        summary="Sample PET plastic analysis",
    )


def _mock_db_connection(fetchone_results=None, fetchall_results=None, execute_side_effect=None):
    """Create a context-manager-compatible mock connection and cursor."""
    cursor = MagicMock()
    if fetchone_results is not None:
        cursor.fetchone.side_effect = list(fetchone_results)
    if fetchall_results is not None:
        cursor.fetchall.side_effect = list(fetchall_results)
    if execute_side_effect is not None:
        cursor.execute.side_effect = execute_side_effect

    conn = MagicMock()
    conn.__enter__.return_value = conn
    conn.__exit__.return_value = False
    conn.cursor.return_value.__enter__.return_value = cursor
    conn.cursor.return_value.__exit__.return_value = False
    return conn, cursor


class TestDatabaseRepositoryUnit(unittest.TestCase):
    """Deterministic unit tests for DB persistence, retrieval, and error handling."""

    def test_save_analysis_persists_main_suggestions_and_opportunities(self):
        result = _build_sample_result()
        conn, cursor = _mock_db_connection(fetchone_results=[(42,)])

        with patch.object(repository, "get_connection", return_value=conn):
            saved_id = save_analysis(result)

        self.assertEqual(saved_id, 42)
        # 1 main INSERT + 2 reuse_suggestions INSERTs + 2 matched_opportunities INSERTs
        self.assertEqual(cursor.execute.call_count, 5)

        calls = cursor.execute.call_args_list
        # Verify main analysis insert
        main_sql, main_params = calls[0][0]
        self.assertIn("INSERT INTO analyses", main_sql)
        self.assertEqual(main_params[0], "Polyethylene Terephthalate (PET)")
        self.assertEqual(main_params[1], "Plastics")
        self.assertEqual(main_params[6], 90)
        persisted_json = json.loads(main_params[7])
        self.assertEqual(persisted_json["waste_type"], "Plastics")
        self.assertEqual(len(persisted_json["reuse_suggestions"]), 2)
        self.assertEqual(len(persisted_json["matched_opportunities"]), 2)

        # Verify reuse suggestions inserts linked to analysis_id=42
        for idx in (1, 2):
            sugg_sql, sugg_params = calls[idx][0]
            self.assertIn("INSERT INTO reuse_suggestions", sugg_sql)
            self.assertEqual(sugg_params[0], 42)
            sugg_payload = json.loads(sugg_params[1])
            self.assertIn("title", sugg_payload)

        # Verify matched opportunities inserts linked to analysis_id=42
        for idx in (3, 4):
            opp_sql, opp_params = calls[idx][0]
            self.assertIn("INSERT INTO matched_opportunities", opp_sql)
            self.assertEqual(opp_params[0], 42)
            opp_payload = json.loads(opp_params[1])
            self.assertIn("opportunity_name", opp_payload)
            self.assertIn("match_score", opp_payload)

        conn.rollback.assert_not_called()

    def test_save_analysis_rolls_back_on_partial_failure(self):
        result = _build_sample_result()
        call_counter = {"count": 0}

        def fail_on_second_insert(*args, **kwargs):
            call_counter["count"] += 1
            if call_counter["count"] == 2:
                raise RuntimeError("Simulated child insert failure")

        conn, _ = _mock_db_connection(
            fetchone_results=[(99,)],
            execute_side_effect=fail_on_second_insert,
        )

        with patch.object(repository, "get_connection", return_value=conn):
            with self.assertRaises(RuntimeError):
                save_analysis(result)

        conn.rollback.assert_called_once()

    def test_save_analysis_rejects_invalid_payload(self):
        with patch.object(repository, "get_connection") as mock_conn:
            with self.assertRaises(ValueError):
                save_analysis(None)
            with self.assertRaises(ValueError):
                save_analysis({"not": "a result object"})
            mock_conn.assert_not_called()

    def test_get_analysis_by_id_handles_dict_json_string_and_nonexistent(self):
        sample_dict = _build_sample_result().to_dict()

        # Case 1: JSONB dict returned directly
        conn1, _ = _mock_db_connection(fetchone_results=[(sample_dict,)])
        with patch.object(repository, "get_connection", return_value=conn1):
            fetched = get_analysis_by_id(10)
        self.assertEqual(fetched["material"]["material_type"], "Polyethylene Terephthalate (PET)")

        # Case 2: JSON string returned
        conn2, _ = _mock_db_connection(fetchone_results=[(json.dumps(sample_dict),)])
        with patch.object(repository, "get_connection", return_value=conn2):
            fetched_str = get_analysis_by_id(10)
        self.assertEqual(fetched_str["waste_type"], "Plastics")

        # Case 3: Nonexistent ID returns None
        conn3, _ = _mock_db_connection(fetchone_results=[None])
        with patch.object(repository, "get_connection", return_value=conn3):
            missing = get_analysis_by_id(999999)
        self.assertIsNone(missing)

        # Case 4: Invalid/non-positive IDs return None without querying DB
        with patch.object(repository, "get_connection") as mock_conn:
            self.assertIsNone(get_analysis_by_id(None))
            self.assertIsNone(get_analysis_by_id("not-an-int"))
            self.assertIsNone(get_analysis_by_id(0))
            self.assertIsNone(get_analysis_by_id(-7))
            mock_conn.assert_not_called()

    def test_get_connection_rejects_missing_or_placeholder_url(self):
        with patch.dict(os.environ, {"DATABASE_URL": ""}, clear=False):
            with self.assertRaises(ValueError):
                db_connection.get_connection()

        with patch.dict(
            os.environ,
            {"DATABASE_URL": "postgresql://username:password@localhost:5432/reuseai"},
            clear=False,
        ):
            with self.assertRaises(ValueError):
                db_connection.get_connection()

    def test_require_live_db_gating_and_error_distinction(self):
        live_case = TestDatabaseLiveIntegration()

        # 1. Skips when RUN_LIVE_DB_TESTS is not enabled
        with patch.dict(os.environ, {"RUN_LIVE_DB_TESTS": ""}, clear=False):
            with self.assertRaises(unittest.SkipTest):
                live_case._require_live_db()

        # 2. Skips when server is genuinely unreachable (connection failure without SQLSTATE)
        unreachable_err = psycopg.OperationalError(
            "connection failed: connection to server at '127.0.0.1', port 5432 failed: Connection refused"
        )
        with (
            patch.dict(os.environ, {"RUN_LIVE_DB_TESTS": "1"}, clear=False),
            patch.object(db_connection, "get_connection", side_effect=unreachable_err),
        ):
            with self.assertRaises(unittest.SkipTest):
                live_case._require_live_db()

        # 3. Fails (does NOT skip) on PostgreSQL auth errors (InvalidPassword / SQLSTATE 28P01)
        auth_err = psycopg.errors.InvalidPassword("password authentication failed")
        with (
            patch.dict(os.environ, {"RUN_LIVE_DB_TESTS": "1"}, clear=False),
            patch.object(db_connection, "get_connection", side_effect=auth_err),
        ):
            with self.assertRaises(psycopg.errors.InvalidPassword):
                live_case._require_live_db()

        # 4. Fails (does NOT skip) on libpq connect-time missing database / auth FATAL errors
        missing_db_err = psycopg.OperationalError('FATAL: database "missing_db" does not exist')
        with (
            patch.dict(os.environ, {"RUN_LIVE_DB_TESTS": "1"}, clear=False),
            patch.object(db_connection, "get_connection", side_effect=missing_db_err),
        ):
            with self.assertRaises(psycopg.OperationalError):
                live_case._require_live_db()

        # 5. Fails (does NOT skip) on SQL/schema/permission errors after connection opens
        conn, _ = _mock_db_connection(
            execute_side_effect=psycopg.errors.InsufficientPrivilege("permission denied for table analyses")
        )
        with (
            patch.dict(os.environ, {"RUN_LIVE_DB_TESTS": "1"}, clear=False),
            patch.object(db_connection, "get_connection", return_value=conn),
        ):
            with self.assertRaises(psycopg.errors.InsufficientPrivilege):
                live_case._require_live_db()


class TestDatabaseLiveIntegration(unittest.TestCase):
    """Opt-in non-destructive integration tests against PostgreSQL (set RUN_LIVE_DB_TESTS=1)."""

    @staticmethod
    def _is_unreachable_db_error(exc: psycopg.OperationalError) -> bool:
        """Return True only when an OperationalError indicates an unreachable/offline server."""
        if getattr(exc, "sqlstate", None) is not None:
            return False
        if isinstance(exc, psycopg.errors.ConnectionTimeout):
            return True

        msg = str(exc).lower()
        fatal_config_markers = (
            "authentication failed",
            "does not exist",
            "permission denied for",
            "no pg_hba.conf entry",
            "invalid authorization",
        )
        if any(marker in msg for marker in fatal_config_markers):
            return False

        unreachable_markers = (
            "connection failed",
            "could not connect",
            "connection refused",
            "timeout",
            "timed out",
            "could not translate host",
            "name or service not known",
            "network is unreachable",
            "server closed the connection unexpectedly",
        )
        return any(marker in msg for marker in unreachable_markers)

    def _require_live_db(self):
        if os.getenv("RUN_LIVE_DB_TESTS", "").strip() != "1":
            self.skipTest(
                "Live PostgreSQL tests skipped by default; set RUN_LIVE_DB_TESTS=1 to run."
            )

        try:
            conn = db_connection.get_connection()
        except ValueError as exc:
            self.skipTest(f"Live PostgreSQL tests skipped: {exc}")
        except psycopg.OperationalError as exc:
            if self._is_unreachable_db_error(exc):
                self.skipTest(f"PostgreSQL server is unreachable: {exc}")
            raise

        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")

    def test_live_save_and_retrieve_complete_analysis_and_children(self):
        self._require_live_db()
        result = _build_sample_result()

        analysis_id = save_analysis(result)
        self.assertIsInstance(analysis_id, int)
        self.assertGreater(analysis_id, 0)

        # Verify main analysis and child tables directly (read-only checks)
        with db_connection.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT material_type, primary_category, recyclability_score
                    FROM analyses
                    WHERE id = %s;
                    """,
                    (analysis_id,),
                )
                main_row = cur.fetchone()
                self.assertIsNotNone(main_row)
                self.assertEqual(main_row[0], "Polyethylene Terephthalate (PET)")
                self.assertEqual(main_row[1], "Plastics")
                self.assertEqual(main_row[2], 90)

                cur.execute(
                    """
                    SELECT suggestion_data
                    FROM reuse_suggestions
                    WHERE analysis_id = %s;
                    """,
                    (analysis_id,),
                )
                suggestion_rows = cur.fetchall()
                self.assertEqual(len(suggestion_rows), len(result.reuse_suggestions))

                cur.execute(
                    """
                    SELECT opportunity_data
                    FROM matched_opportunities
                    WHERE analysis_id = %s;
                    """,
                    (analysis_id,),
                )
                opportunity_rows = cur.fetchall()
                self.assertEqual(len(opportunity_rows), len(result.matched_opportunities))

        # Verify complete result retrieval
        saved_result = get_analysis_by_id(analysis_id)
        self.assertIsNotNone(saved_result)
        self.assertEqual(saved_result["material"]["material_type"], "Polyethylene Terephthalate (PET)")
        self.assertEqual(len(saved_result["reuse_suggestions"]), len(result.reuse_suggestions))
        self.assertEqual(len(saved_result["matched_opportunities"]), len(result.matched_opportunities))
        self.assertEqual(saved_result["waste_type"], "Plastics")
        self.assertTrue(saved_result["recyclable"])

        # Verify listing includes saved analysis
        analyses = get_all_analyses(limit=50)
        self.assertTrue(any(item["id"] == analysis_id for item in analyses))

    def test_live_nonexistent_analysis_id_returns_none(self):
        self._require_live_db()
        self.assertIsNone(get_analysis_by_id(999999999))
        self.assertIsNone(get_analysis_by_id(-1))


if __name__ == "__main__":
    unittest.main()
