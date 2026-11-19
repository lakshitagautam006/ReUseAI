"""Material Detection and Classification Module.
Responsible for material categorization, recyclability scoring, and hazard verification.
"""

from typing import Dict, Any, List, Optional, Tuple
from src.models.schemas import MaterialAnalysis

# Baseline recyclability ratings by standard material classification
STANDARD_RECYCLABILITY_INDEX = {
    "Plastics": {
        "PET": 90,
        "HDPE": 85,
        "PVC": 20,
        "LDPE": 60,
        "PP": 75,
        "PS": 15,
        "Other": 30,
    },
    "Cardboard & Paper": {
        "Corrugated Cardboard": 95,
        "Office Paper": 90,
        "Newsprint": 85,
        "Waxed / Laminated Paper": 25,
    },
    "Metals": {
        "Aluminum": 98,
        "Steel / Tin": 92,
        "Copper / Brass": 95,
    },
    "Glass": {
        "Clear Glass": 95,
        "Colored Glass": 85,
        "Ceramic / Pyrex": 10,
    },
    "Textiles": {
        "Pure Cotton": 70,
        "Polyester Blend": 45,
        "Synthetic / Multi-layer": 25,
    },
    "Electronics": {
        "Printed Circuit Boards": 80,
        "Wiring & Cables": 85,
        "Lithium Batteries": 60,
    },
    "Wood & Timber": {
        "Untreated Lumber": 90,
        "Plywood / MDF": 40,
        "Treated / Painted Wood": 30,
    },
    "Organics": {
        "Clean Biomass": 95,
        "Food Waste": 90,
    }
}


class MaterialDetector:
    """Specialized engine for material identification, property extraction, and scoring."""

    def __init__(self):
        pass

    VALID_CLEANLINESS_LEVELS = ("Clean", "Moderately Dirty", "Dirty", "Unknown")

    @classmethod
    def classify_cleanliness(cls, raw_data: Dict[str, Any]) -> Tuple[str, str]:
        """Classify waste cleanliness into one of 4 strict visual categories:
        - 'Clean': No significant visible dirt or stains.
        - 'Moderately Dirty': Minor visible dirt, stains or residue.
        - 'Dirty': Extensive visible mud, dirt, grease, stains or surface contamination.
        - 'Unknown': Image quality or view is insufficient to determine cleanliness.

        NEVER defaults to 'Clean'. If visual evidence is insufficient or absent, returns 'Unknown'.
        Returns a tuple of (cleanliness_level, cleanliness_explanation).
        """
        raw_level = raw_data.get("cleanliness_level")
        raw_explanation = raw_data.get("cleanliness_explanation")

        condition = str(raw_data.get("condition") or raw_data.get("physical_condition") or "").strip()
        features = raw_data.get("detected_features", [])
        if isinstance(features, list):
            features_text = " ".join(str(f) for f in features)
        else:
            features_text = str(features)
        summary = str(raw_data.get("summary") or "").strip()
        material = str(raw_data.get("material") or raw_data.get("material_type") or "").strip()

        evidence_text = f"{condition} {features_text} {summary} {material} {raw_explanation or ''}".lower()

        def is_negated(term: str, text: str) -> bool:
            neg_prefixes = [f"no {term}", f"not {term}", f"no visible {term}", f"free of {term}", f"without {term}", f"zero {term}"]
            return any(neg in text for neg in neg_prefixes)

        # 1. Dirty Check (Extensive mud, dirt patches, grease, soil, surface contamination)
        dirty_terms = [
            "mud", "muddy", "dirt patches", "dirt patch", "heavy dirt", "heavily soiled",
            "heavily contaminated", "heavy soil", "grease", "greasy", "oil residue", "oily",
            "grime", "grimy", "sludge", "muck", "severely stained", "filthy", "caked with dirt",
            "heavily stained"
        ]
        has_dirty_evidence = False
        for dt in dirty_terms:
            if dt in evidence_text and not is_negated(dt, evidence_text):
                has_dirty_evidence = True
                break

        raw_level_str = str(raw_level).strip().lower() if raw_level else ""
        if raw_level_str in ("dirty", "heavily contaminated", "heavily soiled"):
            has_dirty_evidence = True
        elif "dirty" in raw_level_str and "moderately" not in raw_level_str:
            has_dirty_evidence = True

        if has_dirty_evidence:
            explanation = (
                str(raw_explanation).strip()
                if raw_explanation and any(w in str(raw_explanation).lower() for w in ["mud", "dirt", "soil", "stain", "contamin", "greas", "grime"])
                else "Extensive visible mud, dirt patches, or surface contamination observed on material exterior."
            )
            return "Dirty", explanation

        # 2. Moderately Dirty Check (Minor visible dirt, dust, stains or residue)
        mod_terms = [
            "moderately dirty", "moderately soiled", "lightly soiled", "light soil",
            "slightly dirty", "dusty", "dust", "slight dust", "minor dirt", "minor stains",
            "minor residue", "light residue", "water spots", "fingerprints"
        ]
        has_mod_evidence = False
        for mt in mod_terms:
            if mt in evidence_text and not is_negated(mt, evidence_text):
                has_mod_evidence = True
                break

        if raw_level_str in ("moderately dirty", "lightly soiled", "slightly dirty", "moderate"):
            has_mod_evidence = True

        if has_mod_evidence:
            explanation = (
                str(raw_explanation).strip()
                if raw_explanation and any(w in str(raw_explanation).lower() for w in ["dust", "minor", "light", "stain", "residue", "soiled"])
                else "Minor visible dust, light residue, or minor surface stains observed on the material."
            )
            return "Moderately Dirty", explanation

        # 3. Clean Check (Surface appears clear and free of significant visible dirt or stains)
        clean_terms = [
            "clean", "spotless", "pristine", "unsoiled", "washed", "no visible dirt",
            "free of dirt", "clear and clean", "uncontaminated"
        ]
        has_clean_evidence = False
        for ct in clean_terms:
            if ct in evidence_text:
                has_clean_evidence = True
                break

        if raw_level_str == "clean":
            has_clean_evidence = True

        if has_clean_evidence:
            explanation = (
                str(raw_explanation).strip()
                if raw_explanation and "clean" in str(raw_explanation).lower()
                else "Surface appears clear and free of significant visible dirt, residue, or stains."
            )
            return "Clean", explanation

        # 4. Fallback / Default: Unknown (NEVER default to Clean)
        explanation = (
            str(raw_explanation).strip()
            if raw_explanation
            else "Visual evidence is insufficient to determine surface cleanliness from the image."
        )
        return "Unknown", explanation

    def evaluate(self, raw_data: Dict[str, Any]) -> MaterialAnalysis:
        """Process raw model inferences into a validated MaterialAnalysis instance.

        Applies domain rules for recyclability scoring penalties (e.g. contamination,
        structural fragmentation) and hazard recognition.
        """
        material_type = str(
            raw_data.get("material") or raw_data.get("material_type", "Unknown Material")
        ).strip()
        primary_category = str(
            raw_data.get("waste_type") or raw_data.get("primary_category", "Plastics")
        ).strip()
        sub_category = str(raw_data.get("sub_category", "Standard grade")).strip()

        confidence_val = raw_data.get("confidence")
        if confidence_val is None:
            confidence_val = raw_data.get("confidence_score", 0.85)
        try:
            confidence = float(confidence_val)
        except (ValueError, TypeError):
            confidence = 0.85

        cleanliness, cleanliness_explanation = self.classify_cleanliness(raw_data)
        condition = str(
            raw_data.get("condition") or raw_data.get("physical_condition", "Intact")
        ).strip()

        # Features & hazards
        features = raw_data.get("detected_features", [])
        if not isinstance(features, list):
            features = [str(features)]

        hazards = raw_data.get("hazardous_elements", [])
        if not isinstance(hazards, list):
            hazards = [str(hazards)]

        # Recyclability calculation: derive material-specific baseline
        rec_val = raw_data.get("recyclable")
        explicit_score = raw_data.get("recyclability_score")

        if explicit_score is not None and rec_val is None:
            # Preserves explicit manual override or legacy test inputs
            base_score = int(explicit_score)
        else:
            is_rec_bool = rec_val if isinstance(rec_val, bool) else (explicit_score is not None and explicit_score >= 50)
            base_score = self._determine_material_base_score(
                material_type=material_type,
                category=primary_category,
                is_recyclable=is_rec_bool,
            )

        adjusted_score = self._compute_adjusted_recyclability(
            base_score=base_score,
            cleanliness=cleanliness,
            condition=condition,
            hazards=hazards,
            material_type=material_type,
            category=primary_category,
        )

        return MaterialAnalysis(
            material_type=material_type,
            primary_category=primary_category,
            sub_category=sub_category,
            confidence_score=max(0.0, min(1.0, confidence)),
            cleanliness_level=cleanliness,
            physical_condition=condition,
            recyclability_score=adjusted_score,
            detected_features=features,
            hazardous_elements=hazards,
            cleanliness_explanation=cleanliness_explanation,
        )

    def _determine_material_base_score(
        self,
        material_type: str,
        category: str,
        is_recyclable: Optional[bool] = None,
    ) -> int:
        """Derive indicative baseline recyclability score (0-100) based on material science principles."""
        mat_lower = material_type.lower()
        cat_lower = category.lower()

        # 1. Metals
        if any(m in mat_lower for m in ["aluminum", "aluminium", "soda can", "beverage can", "foil"]):
            base = 98
        elif any(m in mat_lower for m in ["copper", "brass", "bronze"]):
            base = 95
        elif any(m in mat_lower for m in ["steel", "tin", "iron", "ferrous"]):
            base = 92
        elif "metal" in cat_lower:
            base = 94

        # 2. Glass
        elif any(g in mat_lower for g in ["clear glass", "flint glass", "glass bottle", "glass jar"]):
            base = 95
        elif any(g in mat_lower for g in ["colored glass", "amber glass", "green glass"]):
            base = 88
        elif any(g in mat_lower for g in ["ceramic", "pyrex", "plate glass", "window glass", "mirror", "porcelain"]):
            base = 20
        elif "glass" in cat_lower:
            base = 92

        # 3. Cardboard & Paper
        elif any(p in mat_lower for p in ["corrugated", "cardboard box", "shipping box", "kraft"]):
            base = 95
        elif any(p in mat_lower for p in ["office paper", "printer paper", "white paper", "document"]):
            base = 90
        elif any(p in mat_lower for p in ["newsprint", "newspaper", "magazine"]):
            base = 82
        elif any(p in mat_lower for p in ["waxed", "laminated", "tetra pak", "milk carton", "coffee cup"]):
            base = 35
        elif any(p in cat_lower for p in ["paper", "cardboard"]):
            base = 88

        # 4. Plastics & Polymers (Resin Codes 1-7)
        elif any(p in mat_lower for p in ["pet", "pete", "polyethylene terephthalate", "water bottle", "soda bottle"]):
            base = 90
        elif any(p in mat_lower for p in ["hdpe", "high-density", "milk jug", "detergent"]):
            base = 86
        elif any(p in mat_lower for p in ["pp", "polypropylene", "yogurt tub", "container lid"]):
            base = 74
        elif any(p in mat_lower for p in ["ldpe", "low-density", "plastic bag", "shrink wrap", "film"]):
            base = 58
        elif any(p in mat_lower for p in ["pvc", "polyvinyl", "vinyl pipe", "blister pack"]):
            base = 22
        elif any(p in mat_lower for p in ["ps", "polystyrene", "styrofoam", "foam cup", "cutlery"]):
            base = 15
        elif any(p in mat_lower for p in ["abs", "nylon", "polycarbonate", "multi-layer", "composite plastic", "#7"]):
            base = 30
        elif "plastic" in cat_lower:
            base = 72

        # 5. Organics & Biomass
        elif any(o in mat_lower for o in ["food", "compost", "biomass", "organic", "peel", "scrap", "leaves"]):
            base = 88
        elif "organic" in cat_lower:
            base = 88

        # 6. Wood & Timber
        elif any(w in mat_lower for w in ["untreated wood", "pallet", "lumber", "solid wood"]):
            base = 85
        elif any(w in mat_lower for w in ["plywood", "mdf", "particle board", "treated wood", "painted wood"]):
            base = 35
        elif "wood" in cat_lower:
            base = 65

        # 7. Textiles
        elif any(t in mat_lower for t in ["cotton", "wool", "linen", "natural fiber"]):
            base = 68
        elif any(t in mat_lower for t in ["polyester", "synthetic", "nylon fabric", "blend"]):
            base = 40
        elif "textile" in cat_lower or "fabric" in cat_lower:
            base = 52

        # 8. Electronics & E-Waste
        elif any(e in mat_lower for e in ["circuit board", "pcb", "wiring", "cable", "copper wire"]):
            base = 80
        elif any(e in mat_lower for e in ["battery", "lithium", "cell"]):
            base = 55
        elif "electronic" in cat_lower or "e-waste" in cat_lower:
            base = 70

        else:
            base = 75 if is_recyclable is not False else 30

        # If explicitly deemed non-recyclable by vision inference, cap baseline
        if is_recyclable is False:
            base = min(base, 35)

        return base

    def _compute_adjusted_recyclability(
        self,
        base_score: int,
        cleanliness: str,
        condition: str,
        hazards: List[str],
        material_type: str = "",
        category: str = "",
    ) -> int:
        """Apply real-world contamination and material degradation penalties."""
        score = base_score

        # Cleanliness penalty
        clean_lower = cleanliness.lower()
        if clean_lower == "dirty" or "heavy" in clean_lower or "contaminated" in clean_lower:
            score -= 30
        elif clean_lower == "moderately dirty" or "light" in clean_lower or "soiled" in clean_lower or "dust" in clean_lower:
            score -= 10
        elif clean_lower == "unknown":
            score -= 5

        # Physical condition penalty
        cond_lower = condition.lower()
        mat_lower = material_type.lower()
        cat_lower = category.lower()

        if "crush" in cond_lower or "fragment" in cond_lower:
            if "metal" in cat_lower or "aluminum" in mat_lower or "steel" in mat_lower:
                # Crushed metals are readily baled and processed
                score -= 5
            elif "glass" in cat_lower or "glass" in mat_lower:
                # Shattered/fragmented glass creates high contamination in sorting
                score -= 25
            else:
                score -= 15
        elif "damage" in cond_lower or "torn" in cond_lower:
            score -= 5

        # Hazardous substance presence penalty
        for hazard in hazards:
            h_lower = hazard.lower()
            if any(term in h_lower for term in ["battery", "chemical", "sharp", "lead", "mercury", "toxic"]):
                score -= 20
                break

        return max(0, min(100, score))

    @staticmethod
    def get_recyclability_tier(score: int) -> Dict[str, str]:
        """Return indicative classification, styling, and rationale for recyclability score."""
        if score >= 75:
            return {
                "tier": "High",
                "label": "High Recyclability",
                "badge_bg": "#DCFCE7",
                "badge_color": "#15803D",
                "border": "#86EFAC",
                "summary": "Primary circular viability with robust curbside or industrial processing infrastructure.",
            }
        elif score >= 45:
            return {
                "tier": "Moderate",
                "label": "Moderate Recyclability",
                "badge_bg": "#FEF3C7",
                "badge_color": "#B45309",
                "border": "#FCD34D",
                "summary": "Acceptable through specialized mechanical sorting or conditioned pre-processing streams.",
            }
        else:
            return {
                "tier": "Low",
                "label": "Low Recyclability",
                "badge_bg": "#FEE2E2",
                "badge_color": "#B91C1C",
                "border": "#FCA5A5",
                "summary": "Difficult to process through standard streams; prioritize direct reuse or specialized diversion.",
            }
