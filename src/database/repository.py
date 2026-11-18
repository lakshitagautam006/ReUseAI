
import json

from src.database.connection import get_connection


def save_analysis(result):
    """Save a complete waste analysis and its related suggestions."""

    data = result.to_dict()
    material = data["material"]

    with get_connection() as conn:
        with conn.cursor() as cur:

            # Save main analysis
            cur.execute(
                """
                INSERT INTO analyses (
                    material_type,
                    primary_category,
                    sub_category,
                    confidence_score,
                    cleanliness_level,
                    physical_condition,
                    recyclability_score,
                    full_result
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
                """,
                (
                    material["material_type"],
                    material["primary_category"],
                    material["sub_category"],
                    material["confidence_score"],
                    material["cleanliness_level"],
                    material["physical_condition"],
                    material["recyclability_score"],
                    json.dumps(data),
                ),
            )

            analysis_id = cur.fetchone()[0]

            # Save reuse suggestions
            for suggestion in data.get("reuse_suggestions", []):
                cur.execute(
                    """
                    INSERT INTO reuse_suggestions
                    (analysis_id, suggestion_data)
                    VALUES (%s, %s);
                    """,
                    (analysis_id, json.dumps(suggestion)),
                )

            # Save matched opportunities
            for opportunity in data.get("matched_opportunities", []):
                cur.execute(
                    """
                    INSERT INTO matched_opportunities
                    (analysis_id, opportunity_data)
                    VALUES (%s, %s);
                    """,
                    (analysis_id, json.dumps(opportunity)),
                )

    return analysis_id


def get_all_analyses(limit=50):
    """Retrieve the latest saved analyses."""

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, material_type, primary_category,
                       physical_condition, confidence_score, created_at
                FROM analyses
                ORDER BY created_at DESC
                LIMIT %s;
                """,
                (limit,),
            )

            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "material_type": row[1],
            "primary_category": row[2],
            "physical_condition": row[3],
            "confidence_score": row[4],
            "created_at": row[5],
        }
        for row in rows
    ]


def get_analysis_by_id(analysis_id):
    """Retrieve one complete analysis using its ID."""

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT full_result
                FROM analyses
                WHERE id = %s;
                """,
                (analysis_id,),
            )

            row = cur.fetchone()

    if row is None:
        return None

    return row[0]
