
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


def get_impact_summary():
    """Return top-level aggregate statistics across saved analyses and related records."""

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    COUNT(*) AS total_analyses,
                    COUNT(DISTINCT NULLIF(TRIM(primary_category), '')) AS unique_categories,
                    COALESCE(SUM(CASE WHEN recyclability_score >= 50 THEN 1 ELSE 0 END), 0) AS recyclable_count,
                    COALESCE(SUM(CASE WHEN recyclability_score >= 70 THEN 1 ELSE 0 END), 0) AS high_viability_count,
                    AVG(recyclability_score) AS avg_recyclability_score,
                    AVG(confidence_score) AS avg_confidence_score
                FROM analyses;
                """
            )
            analysis_row = cur.fetchone()

            cur.execute(
                """
                SELECT COUNT(*)
                FROM reuse_suggestions;
                """
            )
            suggestions_row = cur.fetchone()

            cur.execute(
                """
                SELECT
                    COUNT(*) AS total_matched_opportunities,
                    AVG(
                        CASE
                            WHEN (opportunity_data::jsonb->>'match_score') ~ '^[0-9]+(\\.[0-9]+)?$'
                            THEN (opportunity_data::jsonb->>'match_score')::double precision
                            ELSE NULL
                        END
                    ) AS avg_match_score
                FROM matched_opportunities;
                """
            )
            opportunities_row = cur.fetchone()

    total_analyses = int(analysis_row[0] or 0) if analysis_row else 0
    unique_categories = int(analysis_row[1] or 0) if analysis_row else 0
    recyclable_count = int(analysis_row[2] or 0) if analysis_row else 0
    high_viability_count = int(analysis_row[3] or 0) if analysis_row else 0
    avg_recyclability = analysis_row[4] if analysis_row else None
    avg_confidence = analysis_row[5] if analysis_row else None

    total_suggestions = int(suggestions_row[0] or 0) if suggestions_row else 0
    total_opportunities = int(opportunities_row[0] or 0) if opportunities_row else 0
    avg_match_score = opportunities_row[1] if opportunities_row else None

    return {
        "total_analyses": total_analyses,
        "unique_categories": unique_categories,
        "recyclable_count": recyclable_count,
        "recyclable_rate": round((recyclable_count / total_analyses) * 100.0, 1)
        if total_analyses > 0
        else 0.0,
        "high_viability_count": high_viability_count,
        "avg_recyclability_score": round(float(avg_recyclability), 1)
        if avg_recyclability is not None
        else 0.0,
        "avg_confidence_score": round(float(avg_confidence), 4)
        if avg_confidence is not None
        else 0.0,
        "total_reuse_suggestions": total_suggestions,
        "avg_suggestions_per_analysis": round(total_suggestions / total_analyses, 1)
        if total_analyses > 0
        else 0.0,
        "total_matched_opportunities": total_opportunities,
        "avg_match_score": round(float(avg_match_score), 1)
        if avg_match_score is not None
        else 0.0,
    }


def get_category_distribution():
    """Return analysis counts and average recyclability grouped by primary category."""

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    COALESCE(NULLIF(TRIM(primary_category), ''), 'Unknown') AS primary_category,
                    COUNT(*) AS analysis_count,
                    AVG(recyclability_score) AS avg_recyclability_score,
                    AVG(confidence_score) AS avg_confidence_score
                FROM analyses
                GROUP BY COALESCE(NULLIF(TRIM(primary_category), ''), 'Unknown')
                ORDER BY analysis_count DESC, primary_category ASC;
                """
            )
            rows = cur.fetchall()

    return [
        {
            "primary_category": row[0],
            "count": int(row[1]),
            "avg_recyclability_score": round(float(row[2]), 1)
            if row[2] is not None
            else 0.0,
            "avg_confidence_score": round(float(row[3]), 4)
            if row[3] is not None
            else 0.0,
        }
        for row in rows
    ]


def get_analyses_over_time(days=None):
    """Return daily analysis counts ordered chronologically."""

    with get_connection() as conn:
        with conn.cursor() as cur:
            if days is not None and int(days) > 0:
                cur.execute(
                    """
                    SELECT
                        DATE(created_at) AS analysis_date,
                        COUNT(*) AS analysis_count
                    FROM analyses
                    WHERE created_at IS NOT NULL
                      AND created_at >= CURRENT_DATE - (%s * INTERVAL '1 day')
                    GROUP BY DATE(created_at)
                    ORDER BY analysis_date ASC;
                    """,
                    (int(days),),
                )
            else:
                cur.execute(
                    """
                    SELECT
                        DATE(created_at) AS analysis_date,
                        COUNT(*) AS analysis_count
                    FROM analyses
                    WHERE created_at IS NOT NULL
                    GROUP BY DATE(created_at)
                    ORDER BY analysis_date ASC;
                    """
                )
            rows = cur.fetchall()

    return [
        {
            "date": row[0],
            "count": int(row[1]),
        }
        for row in rows
    ]


def get_condition_and_cleanliness_breakdown():
    """Return counts grouped by physical condition and cleanliness level."""

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    COALESCE(NULLIF(TRIM(physical_condition), ''), 'Unknown') AS physical_condition,
                    COUNT(*) AS count
                FROM analyses
                GROUP BY COALESCE(NULLIF(TRIM(physical_condition), ''), 'Unknown')
                ORDER BY count DESC, physical_condition ASC;
                """
            )
            condition_rows = cur.fetchall()

            cur.execute(
                """
                SELECT
                    COALESCE(NULLIF(TRIM(cleanliness_level), ''), 'Unknown') AS cleanliness_level,
                    COUNT(*) AS count
                FROM analyses
                GROUP BY COALESCE(NULLIF(TRIM(cleanliness_level), ''), 'Unknown')
                ORDER BY count DESC, cleanliness_level ASC;
                """
            )
            cleanliness_rows = cur.fetchall()

    return {
        "conditions": [
            {"physical_condition": row[0], "count": int(row[1])}
            for row in condition_rows
        ],
        "cleanliness": [
            {"cleanliness_level": row[0], "count": int(row[1])}
            for row in cleanliness_rows
        ],
    }


def get_reuse_and_opportunity_stats(top_n=8):
    """Return aggregate insights from reuse_suggestions and matched_opportunities."""

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    COALESCE(
                        NULLIF(TRIM(suggestion_data::jsonb->>'carbon_offset_rating'), ''),
                        'Unspecified'
                    ) AS rating,
                    COUNT(*) AS count
                FROM reuse_suggestions
                GROUP BY COALESCE(
                    NULLIF(TRIM(suggestion_data::jsonb->>'carbon_offset_rating'), ''),
                    'Unspecified'
                )
                ORDER BY count DESC, rating ASC;
                """
            )
            rating_rows = cur.fetchall()

            cur.execute(
                """
                SELECT
                    COALESCE(
                        NULLIF(TRIM(suggestion_data::jsonb->>'difficulty'), ''),
                        'Unspecified'
                    ) AS difficulty,
                    COUNT(*) AS count
                FROM reuse_suggestions
                GROUP BY COALESCE(
                    NULLIF(TRIM(suggestion_data::jsonb->>'difficulty'), ''),
                    'Unspecified'
                )
                ORDER BY count DESC, difficulty ASC;
                """
            )
            difficulty_rows = cur.fetchall()

            cur.execute(
                """
                SELECT
                    COALESCE(
                        NULLIF(TRIM(opportunity_data::jsonb->>'opportunity_category'), ''),
                        'Uncategorized'
                    ) AS opportunity_category,
                    COUNT(*) AS count,
                    AVG(
                        CASE
                            WHEN (opportunity_data::jsonb->>'match_score') ~ '^[0-9]+(\\.[0-9]+)?$'
                            THEN (opportunity_data::jsonb->>'match_score')::double precision
                            ELSE NULL
                        END
                    ) AS avg_match_score
                FROM matched_opportunities
                GROUP BY COALESCE(
                    NULLIF(TRIM(opportunity_data::jsonb->>'opportunity_category'), ''),
                    'Uncategorized'
                )
                ORDER BY count DESC, opportunity_category ASC
                LIMIT %s;
                """,
                (int(top_n),),
            )
            opportunity_rows = cur.fetchall()

    return {
        "carbon_offset_ratings": [
            {"rating": row[0], "count": int(row[1])}
            for row in rating_rows
        ],
        "difficulty_levels": [
            {"difficulty": row[0], "count": int(row[1])}
            for row in difficulty_rows
        ],
        "opportunity_categories": [
            {
                "opportunity_category": row[0],
                "count": int(row[1]),
                "avg_match_score": round(float(row[2]), 1)
                if row[2] is not None
                else 0.0,
            }
            for row in opportunity_rows
        ],
    }


def get_top_materials(limit=10):
    """Return the most frequently analyzed materials with average scores."""

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    COALESCE(NULLIF(TRIM(material_type), ''), 'Unknown') AS material_type,
                    COALESCE(NULLIF(TRIM(primary_category), ''), 'Unknown') AS primary_category,
                    COUNT(*) AS analysis_count,
                    AVG(recyclability_score) AS avg_recyclability_score,
                    AVG(confidence_score) AS avg_confidence_score
                FROM analyses
                GROUP BY
                    COALESCE(NULLIF(TRIM(material_type), ''), 'Unknown'),
                    COALESCE(NULLIF(TRIM(primary_category), ''), 'Unknown')
                ORDER BY analysis_count DESC, avg_recyclability_score DESC NULLS LAST, material_type ASC
                LIMIT %s;
                """,
                (int(limit),),
            )
            rows = cur.fetchall()

    return [
        {
            "material_type": row[0],
            "primary_category": row[1],
            "count": int(row[2]),
            "avg_recyclability_score": round(float(row[3]), 1)
            if row[3] is not None
            else 0.0,
            "avg_confidence_score": round(float(row[4]), 4)
            if row[4] is not None
            else 0.0,
        }
        for row in rows
    ]
