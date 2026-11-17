"""Unit and integration test suite for Phase 4: Resource Matching Engine & Reuse Engine Improvements.
Verifies:
1. Dynamic, non-identical match scores (eliminates identical ~99.7% bug).
2. Four-point detailed match rationale (material match, physical properties, condition suitability, practical use).
3. 4-6 meaningful, sequential, actionable steps for all upcycling recommendations.
4. Unique, descriptive project titles (no generic repeated 'DIY Upcycling Project').
5. Sample 1: Plastic Bottle (distinct plastic opportunities, 4-6 steps).
6. Sample 2: Cardboard Box (packaging, storage, mulch applications, 4-6 steps).
7. Sample 3: Glass Jar (cleanliness/physical condition awareness, 4-6 steps).
8. Physical integrity & contamination constraints.
"""

import unittest
from src.services.matching_engine import ResourceMatchingEngine, SAMPLE_OPPORTUNITY_CATALOG
from src.services.reuse_engine import ReuseEngine
from src.models.schemas import WasteAnalysisResult, MaterialAnalysis, ReuseSuggestion, MatchedOpportunity


class TestResourceMatchingEngine(unittest.TestCase):
    """Test suite for Phase 4 Resource Matching Engine and Upcycling Suggestions."""

    def setUp(self):
        self.matcher = ResourceMatchingEngine()
        self.reuse_engine = ReuseEngine()

    # -------------------------------------------------------------------------
    # Sample 1: Plastic Bottle Verification
    # -------------------------------------------------------------------------
    def test_sample_1_plastic_bottle(self):
        """Sample 1: PET Plastic Bottle.
        - Matches distinct plastic opportunities (Planter, 3D printing filament, textile fiber).
        - Generates dynamic, non-identical scores.
        - Generates 4-6 sequential actionable steps per recommendation with unique titles.
        """
        mat = MaterialAnalysis(
            material_type="Polyethylene Terephthalate / PET Plastic",
            primary_category="Plastics",
            sub_category="Code #1 Resin Bottle",
            confidence_score=0.96,
            cleanliness_level="Clean",
            physical_condition="Intact, Clean",
            recyclability_score=92,
        )

        # 1. Matching Engine Test
        matches = self.matcher.match(
            material=mat.material_type,
            waste_type=mat.primary_category,
            condition=mat.physical_condition,
            recyclable=True,
            reuse_ideas=[
                "Sub-Irrigated Self-Watering Planter with cotton capillary wick",
                "Extrude into 1.75mm recycled 3D printer filament"
            ],
            confidence=mat.confidence_score,
            top_k=3,
        )

        self.assertEqual(len(matches), 3, "Expected top 3 plastic matches.")

        # Verify distinct match scores (Fix for identical 99.7% bug)
        scores = [m.match_score for m in matches]
        self.assertEqual(len(scores), len(set(scores)), f"Match scores must be non-identical: {scores}")
        self.assertEqual(scores, sorted(scores, reverse=True), "Scores must be descending.")

        # Verify all opportunities are plastic-appropriate
        names = [m.opportunity_name for m in matches]
        self.assertTrue(
            any("Planter" in n or "3D Printing" in n or "Textile" in n for n in names),
            f"Expected plastic opportunities in {names}"
        )

        # Verify four-point rationale for each match
        for m in matches:
            self._verify_four_point_rationale(m)

        # 2. Reuse Engine Test (4-6 actionable steps, unique descriptive titles)
        suggestions = self.reuse_engine.generate_suggestions(
            raw_suggestions=[
                "Sub-Irrigated Self-Watering Planter: Invert top half and add potting soil.",
                "Precision 1.75mm 3D Printer Filament: Cut bottle ribbon and extrude through heated nozzle."
            ],
            material=mat
        )

        self.assertGreaterEqual(len(suggestions), 2)
        titles = [s.title for s in suggestions]
        self.assertEqual(len(titles), len(set(titles)), "All suggestion titles must be unique.")

        for s in suggestions:
            # No generic placeholder titles
            self.assertNotIn("DIY Upcycling Project", s.title)
            self.assertNotIn("Creative Repurposing Project", s.title)
            # Enforce 4-6 meaningful, sequential, actionable steps
            self.assertGreaterEqual(
                len(s.step_by_step_guide), 4,
                f"Suggestion '{s.title}' must have at least 4 steps, found {len(s.step_by_step_guide)}"
            )
            self.assertLessEqual(
                len(s.step_by_step_guide), 6,
                f"Suggestion '{s.title}' must have at most 6 steps, found {len(s.step_by_step_guide)}"
            )
            # Steps must be substantive
            for step in s.step_by_step_guide:
                self.assertGreaterEqual(len(step), 20, "Steps must explain the actual physical process.")

    # -------------------------------------------------------------------------
    # Sample 2: Cardboard Box Verification
    # -------------------------------------------------------------------------
    def test_sample_2_cardboard_box(self):
        """Sample 2: Corrugated Cardboard Box.
        - Matches packaging, storage, or sheet mulch applications.
        - Generates dynamic, non-identical scores.
        - Generates 4-6 sequential actionable steps per recommendation with unique titles.
        """
        mat = MaterialAnalysis(
            material_type="Corrugated Cardboard",
            primary_category="Cardboard & Paper",
            sub_category="Single-Wall Shipping Box",
            confidence_score=0.94,
            cleanliness_level="Clean",
            physical_condition="Slightly Damaged, Clean",
            recyclability_score=88,
        )

        # 1. Matching Engine Test
        matches = self.matcher.match(
            material=mat.material_type,
            waste_type=mat.primary_category,
            condition=mat.physical_condition,
            recyclable=True,
            reuse_ideas=[
                "Biodegradable permaculture sheet mulch and garden weed barrier",
                "Laser-cut interlocking drawer dividers for desk supplies"
            ],
            confidence=mat.confidence_score,
            top_k=3,
        )

        self.assertEqual(len(matches), 3)

        # Verify distinct non-identical scores
        scores = [m.match_score for m in matches]
        self.assertEqual(len(scores), len(set(scores)), f"Scores must be non-identical: {scores}")

        # Verify cardboard-specific opportunities
        names = [m.opportunity_name for m in matches]
        self.assertTrue(
            any("Mulch" in n or "Molded Pulp" in n or "Partition" in n for n in names),
            f"Expected cardboard opportunities in {names}"
        )

        # Verify four-point rationale for each match
        for m in matches:
            self._verify_four_point_rationale(m)

        # 2. Reuse Engine Test
        suggestions = self.reuse_engine.generate_suggestions(
            raw_suggestions=[
                "Biodegradable Permaculture Sheet Mulch: Remove tape and lay flat over weeds.",
                "Laser-Cut Interlocking Modular Drawer Grid: Measure drawer and cut slotted strips."
            ],
            material=mat
        )

        self.assertGreaterEqual(len(suggestions), 2)
        for s in suggestions:
            self.assertNotIn("DIY Upcycling Project", s.title)
            self.assertGreaterEqual(len(s.step_by_step_guide), 4)
            self.assertLessEqual(len(s.step_by_step_guide), 6)

    # -------------------------------------------------------------------------
    # Sample 3: Glass Jar Verification
    # -------------------------------------------------------------------------
    def test_sample_3_glass_jar_clean_and_intact(self):
        """Sample 3 (Part A): Clean, Intact Glass Jar.
        - Recognizes cleanliness and intact physical integrity.
        - Matches food-safe pantry bulk storage, artisan candle vessel, or terrarium.
        - Generates dynamic, non-identical scores.
        - Generates 4-6 sequential actionable steps per recommendation with unique titles.
        """
        mat = MaterialAnalysis(
            material_type="Silica Glass Jar with Lid",
            primary_category="Glass",
            sub_category="Container Glass",
            confidence_score=0.97,
            cleanliness_level="Clean",
            physical_condition="Intact, Clean",
            recyclability_score=95,
        )

        # 1. Matching Engine Test
        matches = self.matcher.match(
            material=mat.material_type,
            waste_type=mat.primary_category,
            condition=mat.physical_condition,
            recyclable=True,
            reuse_ideas=[
                "Airtight Zero-Waste Bulk Pantry Storage Jar for grains and legumes",
                "Hand-poured soy wax aromatherapy candle vessel"
            ],
            confidence=mat.confidence_score,
            top_k=3,
        )

        self.assertEqual(len(matches), 3)

        # Verify distinct non-identical scores
        scores = [m.match_score for m in matches]
        self.assertEqual(len(scores), len(set(scores)), f"Scores must be non-identical: {scores}")

        # Top matches should favor intact glass container opportunities
        names = [m.opportunity_name for m in matches]
        self.assertTrue(
            any("Pantry" in n or "Candle" in n or "Terrarium" in n for n in names),
            f"Expected intact container opportunities in {names}"
        )

        # Verify four-point rationale for each match
        for m in matches:
            self._verify_four_point_rationale(m)

        # 2. Reuse Engine Test
        suggestions = self.reuse_engine.generate_suggestions(
            raw_suggestions=[
                "Airtight Zero-Waste Bulk Pantry Storage Jar: Clean jar, sterilize in boiling water, label with tare weight.",
                "Artisan Hand-Poured Botanical Soy Candle Vessel: Affix wick, pour melted soy wax, and cure for 24 hours."
            ],
            material=mat
        )

        self.assertGreaterEqual(len(suggestions), 2)
        for s in suggestions:
            self.assertNotIn("DIY Upcycling Project", s.title)
            self.assertGreaterEqual(len(s.step_by_step_guide), 4)
            self.assertLessEqual(len(s.step_by_step_guide), 6)

    def test_sample_3_glass_jar_crushed_or_fragmented_condition_awareness(self):
        """Sample 3 (Part B): Crushed / Broken Glass Jar.
        - Condition Awareness: Crushed glass CANNOT match intact container opportunities (pantry refill or candle vessel).
        - It MUST match Terrazzo Tile aggregate or Horticultural drainage instead!
        """
        matches_broken = self.matcher.match(
            material="Silica Glass Jar",
            waste_type="Glass",
            condition="Crushed, Fragmented",
            recyclable=True,
            reuse_ideas=["Tumble into decorative landscape pebbles"],
            confidence=0.95,
            top_k=3,
        )

        self.assertGreaterEqual(len(matches_broken), 1)
        broken_names = [m.opportunity_name for m in matches_broken]

        # Must match Terrazzo or Horticultural Drainage, NOT intact storage
        self.assertTrue(
            any("Terrazzo" in n or "Drainage" in n for n in broken_names),
            f"Broken glass must match aggregate/terrazzo, got {broken_names}"
        )
        self.assertNotIn(
            "Zero-Waste Pantry Bulk Refill & Storage Station", broken_names,
            "Broken glass must not match intact pantry food storage!"
        )
        self.assertNotIn(
            "Artisan Hand-Poured Soy Candle & Luminary Studio", broken_names,
            "Broken glass must not match intact candle vessels!"
        )

    # -------------------------------------------------------------------------
    # Helper: Four-Point Rationale Verification
    # -------------------------------------------------------------------------
    def _verify_four_point_rationale(self, opp: MatchedOpportunity):
        """Verify that the match rationale explicitly covers all 4 required points:
        1. Why this resource matches the material.
        2. Which physical properties make it suitable.
        3. Whether the material condition supports the proposed application.
        4. What the resource can practically be used for.
        """
        r = opp.reason
        self.assertTrue(len(r) > 50, f"Rationale too short: {r}")

        # Point 1: Material Match
        self.assertTrue(
            "supplies compatible" in r or "feedstock" in r or "matches" in r.lower(),
            f"Rationale missing material match explanation: {r}"
        )

        # Point 2: Specific Physical Properties
        self.assertIn("Key properties:", r, f"Rationale missing physical properties: {r}")

        # Point 3: Condition Suitability
        self.assertIn("Condition suitability:", r, f"Rationale missing condition suitability: {r}")

        # Point 4: Practical Usage
        self.assertIn("Practical application:", r, f"Rationale missing practical application: {r}")

    # -------------------------------------------------------------------------
    # Edge Cases & Constraints
    # -------------------------------------------------------------------------
    def test_hazardous_contamination_returns_empty_matches(self):
        """Verify that heavily contaminated or hazardous waste finds 0 matches."""
        matches = self.matcher.match(
            material="Toxic Chemical Sludge",
            waste_type="Hazardous Chemicals",
            condition="Heavily Contaminated, Toxic",
            recyclable=False,
            confidence=0.9,
            top_k=3,
        )
        self.assertEqual(matches, [], "Hazardous waste must return empty matches list.")

    def test_non_recyclable_penalty(self):
        """Verify that opportunities requiring recyclable feedstock penalize non-recyclable items."""
        matches_rec = self.matcher.match(
            material="PET Plastic",
            waste_type="Plastics",
            condition="Intact, Clean",
            recyclable=True,
            confidence=0.95,
        )
        matches_non_rec = self.matcher.match(
            material="PET Plastic",
            waste_type="Plastics",
            condition="Intact, Clean",
            recyclable=False,
            confidence=0.95,
        )

        score_rec = next((m.match_score for m in matches_rec if "3D Printing" in m.opportunity_name), 0)
        score_non_rec = next((m.match_score for m in matches_non_rec if "3D Printing" in m.opportunity_name), 0)

        self.assertGreater(score_rec, score_non_rec, "Recyclable item should score higher for industrial recycling.")
        self.assertLessEqual(score_non_rec, 40.0, "Non-recyclable item should be penalized <= 40.0")

    def test_match_from_result_integration(self):
        """Test matching directly from a WasteAnalysisResult schema."""
        result = WasteAnalysisResult(
            material=MaterialAnalysis(
                material_type="Aluminum Beverage Can",
                primary_category="Metals",
                sub_category="Drawn Aluminum Can",
                confidence_score=0.95,
                cleanliness_level="Clean",
                physical_condition="Intact, Clean",
                recyclability_score=95,
            ),
            reuse_suggestions=[
                ReuseSuggestion(
                    title="Filigree Punched Luminary & Lantern Vessel",
                    category="Decor",
                    difficulty="Easy",
                    estimated_time="20 mins",
                    tools_required=["Hammer", "Nails"],
                    step_by_step_guide=[
                        "Step 1: Clean can",
                        "Step 2: Freeze with water",
                        "Step 3: Punch holes",
                        "Step 4: Melt ice",
                        "Step 5: Insert candle"
                    ],
                )
            ]
        )

        matches = self.matcher.match_from_result(result, top_k=3)
        self.assertEqual(len(matches), 3)
        scores = [m.match_score for m in matches]
        self.assertEqual(len(scores), len(set(scores)), "Scores must be dynamic and non-identical.")


if __name__ == "__main__":
    unittest.main()
