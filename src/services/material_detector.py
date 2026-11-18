"""Material Detection and Classification Module.
Responsible for material categorization, recyclability scoring, and hazard verification.
"""

from typing import Dict, Any, List, Optional
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

        cleanliness = str(raw_data.get("cleanliness_level", "Clean")).strip()
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

        # Recyclability calculation with domain penalty adjustments
        rec_val = raw_data.get("recyclable")
        if isinstance(rec_val, bool):
            base_score = 85 if rec_val else 25
        elif isinstance(rec_val, (int, float)):
            base_score = int(rec_val)
        else:
            base_score = int(raw_data.get("recyclability_score", 75))

        adjusted_score = self._compute_adjusted_recyclability(
            base_score=base_score,
            cleanliness=cleanliness,
            condition=condition,
            hazards=hazards
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
        )

    def _compute_adjusted_recyclability(
        self,
        base_score: int,
        cleanliness: str,
        condition: str,
        hazards: List[str]
    ) -> int:
        """Apply real-world contamination and material degradation penalties."""
        score = base_score

        # Cleanliness penalty
        clean_lower = cleanliness.lower()
        if "heavy" in clean_lower or "contaminated" in clean_lower:
            score -= 30
        elif "light" in clean_lower or "soiled" in clean_lower:
            score -= 10

        # Physical condition penalty
        cond_lower = condition.lower()
        if "crush" in cond_lower or "fragment" in cond_lower:
            score -= 15
        elif "damage" in cond_lower:
            score -= 5

        # Hazardous substance presence penalty
        for hazard in hazards:
            h_lower = hazard.lower()
            if any(term in h_lower for term in ["battery", "chemical", "sharp", "lead", "mercury"]):
                score -= 20
                break

        return max(0, min(100, score))
