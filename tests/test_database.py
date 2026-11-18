
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


def test_save_and_retrieve_analysis():

    # Create sample material analysis
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

    # Create sample reuse suggestion
    suggestion = ReuseSuggestion(
        title="DIY Plant Pot",
        category="DIY / Household",
        difficulty="Easy",
        estimated_time="15 minutes",
        tools_required=["Scissors"],
        step_by_step_guide=["Cut the bottle", "Add soil"],
        environmental_benefit="Reduces plastic waste",
        carbon_offset_rating="Medium",
    )

    # Create sample matched opportunity
    opportunity = MatchedOpportunity(
        opportunity_name="Plastic Recycling Unit",
        opportunity_category="Recycling",
        match_score=92.0,
        reason="PET plastic is recyclable",
        suggested_application="Send material for recycling",
        target_user="Recycling Industry",
    )

    # Create complete result
    result = WasteAnalysisResult(
        material=material,
        reuse_suggestions=[suggestion],
        matched_opportunities=[opportunity],
        summary="Sample PET plastic analysis",
    )

    # Save to PostgreSQL
    analysis_id = save_analysis(result)
    print("\nSaved Analysis ID:", analysis_id)

    # Retrieve saved analysis
    saved_result = get_analysis_by_id(analysis_id)
    print("\nRetrieved Material:", saved_result["material"]["material_type"])

    # Check database records
    analyses = get_all_analyses()
    print("\nTotal Saved Analyses:", len(analyses))

    assert saved_result is not None
    assert saved_result["material"]["material_type"] == "Polyethylene Terephthalate (PET)"

    print("\nSave and retrieval test passed!")


if __name__ == "__main__":
    test_save_and_retrieve_analysis()
