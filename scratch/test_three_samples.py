"""Verification script for ReUseAI Phase 4 Improvements across Three Target Samples:
Sample 1: Plastic Bottle
Sample 2: Cardboard Box
Sample 3: Glass Jar (Clean & Intact vs Crushed/Fragmented)

Demonstrates:
- Unique descriptive titles (no 'DIY Upcycling Project')
- 4-6 sequential, actionable steps per recommendation
- Dynamic, non-identical match scores
- Complete four-point match rationales (Material match, physical properties, condition suitability, practical usage)
"""

import sys
import os

# Ensure workspace root is in path
sys.path.insert(0, os.path.abspath("."))

from src.services.matching_engine import ResourceMatchingEngine
from src.services.reuse_engine import ReuseEngine
from src.models.schemas import MaterialAnalysis, WasteAnalysisResult
from src.utils.sample_generator import (
    create_sample_plastic_bottle,
    create_sample_cardboard_box,
    create_sample_glass_jar,
)


def print_separator(title: str):
    print("\n" + "=" * 80)
    print(f" {title.upper()} ")
    print("=" * 80)


def evaluate_sample(
    sample_name: str,
    material_type: str,
    primary_category: str,
    sub_category: str,
    condition: str,
    recyclable: bool,
    confidence: float,
    raw_ideas: list,
):
    print_separator(f"Evaluating {sample_name}")

    mat = MaterialAnalysis(
        material_type=material_type,
        primary_category=primary_category,
        sub_category=sub_category,
        confidence_score=confidence,
        cleanliness_level="Clean" if "Clean" in condition else "Soiled",
        physical_condition=condition,
        recyclability_score=90 if recyclable else 35,
    )

    # 1. Reuse Recommendations
    reuse_engine = ReuseEngine()
    suggestions = reuse_engine.generate_suggestions(raw_ideas, mat)

    print(f"\n[1] Material Classification:")
    print(f"    - Material: {mat.material_type}")
    print(f"    - Category: {mat.primary_category}")
    print(f"    - Condition: {mat.physical_condition}")
    print(f"    - Recyclability Index: {mat.recyclability_score}/100")
    print(f"    - Confidence: {mat.confidence_score * 100:.1f}%")

    print(f"\n[2] Upcycling Recommendations ({len(suggestions)} distinct projects):")
    for i, s in enumerate(suggestions, start=1):
        print(f"\n    Project {i}: {s.title}")
        print(f"    Category: {s.category} | Difficulty: {s.difficulty} | Time: {s.estimated_time}")
        print(f"    Required Tools: {', '.join(s.tools_required)}")
        print(f"    Sequential Steps ({len(s.step_by_step_guide)} steps):")
        for step_idx, step in enumerate(s.step_by_step_guide, start=1):
            print(f"      Step {step_idx}: {step}")
        print(f"    Eco-Benefit: {s.environmental_benefit}")

    # 2. Resource Matching Engine
    matcher = ResourceMatchingEngine()
    matches = matcher.match(
        material=mat.material_type,
        waste_type=mat.primary_category,
        condition=mat.physical_condition,
        recyclable=recyclable,
        reuse_ideas=[s.title for s in suggestions],
        confidence=mat.confidence_score,
        top_k=3,
    )

    print(f"\n[3] Matched Reuse Opportunities ({len(matches)} matched):")
    scores = [m.match_score for m in matches]
    print(f"    Computed Match Scores: {scores} (Dynamic & Non-Identical: {len(scores) == len(set(scores))})")

    for i, m in enumerate(matches, start=1):
        print(f"\n    Match {i}: {m.opportunity_name} [{m.match_score:.1f}% Match]")
        print(f"    Category: {m.opportunity_category}")
        print(f"    Potential User: {m.target_user}")
        print(f"    Suggested Application: {m.suggested_application}")
        print(f"    Four-Point Match Rationale:")
        print(f"      {m.reason}")


def main():
    # Verify sample generator functions
    img_bottle = create_sample_plastic_bottle()
    img_box = create_sample_cardboard_box()
    img_jar = create_sample_glass_jar()
    print(f"Sample Graphics Generated Successfully: Bottle {img_bottle.size}, Box {img_box.size}, Jar {img_jar.size}")

    # Sample 1: Plastic Bottle
    evaluate_sample(
        sample_name="Sample 1: Plastic Bottle (PET)",
        material_type="Polyethylene Terephthalate / PET Plastic",
        primary_category="Plastics",
        sub_category="Code #1 Resin Beverage Bottle",
        condition="Intact, Clean",
        recyclable=True,
        confidence=0.96,
        raw_ideas=[
            "Sub-Irrigated Self-Watering Planter with capillary wick",
            "Makerspace 1.75mm 3D printer filament extrusion"
        ]
    )

    # Sample 2: Cardboard Box
    evaluate_sample(
        sample_name="Sample 2: Cardboard Box (Corrugated)",
        material_type="Corrugated Cardboard",
        primary_category="Cardboard & Paper",
        sub_category="Single-Wall Kraft Shipping Box",
        condition="Slightly Damaged, Clean",
        recyclable=True,
        confidence=0.94,
        raw_ideas=[
            "Permaculture sheet mulch and soil weed suppressor",
            "Interlocking slotted drawer divider grid"
        ]
    )

    # Sample 3A: Glass Jar (Intact, Clean)
    evaluate_sample(
        sample_name="Sample 3A: Glass Jar (Clean & Intact)",
        material_type="Silica Glass Jar with Lid",
        primary_category="Glass",
        sub_category="Container Glass",
        condition="Intact, Clean",
        recyclable=True,
        confidence=0.97,
        raw_ideas=[
            "Airtight Zero-Waste Bulk Pantry Storage Jar",
            "Artisan botanical soy candle vessel"
        ]
    )

    # Sample 3B: Glass Jar (Crushed / Fragmented) - Demonstrating Condition Awareness
    evaluate_sample(
        sample_name="Sample 3B: Glass Jar (Crushed / Broken Cullet)",
        material_type="Silica Glass Jar",
        primary_category="Glass",
        sub_category="Container Glass",
        condition="Crushed, Fragmented",
        recyclable=True,
        confidence=0.95,
        raw_ideas=[
            "Tumble into smooth drainage pebbles for terrariums",
            "Crush into terrazzo floor tile aggregate"
        ]
    )


if __name__ == "__main__":
    main()
