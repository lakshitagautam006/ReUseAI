"""Data schemas for waste analysis, material properties, reuse recommendations,
and resource matching opportunities (Phase 4).
These models represent the structured hand-off payload for the matching engine
and provide full support for the standardized Groq Vision schema:
(material, waste_type, condition, recyclable, confidence, reuse_ideas).
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import json


@dataclass
class MaterialAnalysis:
    """Represents the detected material properties and physical state."""
    material_type: str                   # e.g., "Polyethylene Terephthalate (PET)"
    primary_category: str                # e.g., "Plastics", "Cardboard & Paper", "Metals"
    sub_category: str                    # e.g., "Rigid Container (Code #1)"
    confidence_score: float              # 0.0 to 1.0
    cleanliness_level: str               # "Clean", "Moderately Dirty", "Dirty", "Unknown"
    physical_condition: str              # "Intact", "Slightly Damaged", "Fragmented"
    recyclability_score: int             # 0 to 100 index
    detected_features: List[str] = field(default_factory=list)
    hazardous_elements: List[str] = field(default_factory=list)
    cleanliness_explanation: Optional[str] = None

    @property
    def material(self) -> str:
        """Standardized schema alias for material_type."""
        return self.material_type

    @property
    def waste_type(self) -> str:
        """Standardized schema alias for primary_category."""
        return self.primary_category

    @property
    def condition(self) -> str:
        """Standardized schema alias for physical_condition."""
        return self.physical_condition

    @property
    def recyclable(self) -> bool:
        """Standardized schema alias for recyclability (True if score >= 50)."""
        return self.recyclability_score >= 50

    @property
    def confidence(self) -> float:
        """Standardized schema alias for confidence_score."""
        return self.confidence_score


@dataclass
class ReuseSuggestion:
    """Represents a structured reuse or upcycling recommendation."""
    title: str                           # e.g., "Self-Watering Herb Planter"
    category: str                        # "DIY / Household", "Secondary Manufacturing", "Community Donation"
    difficulty: str                      # "Easy", "Medium", "Advanced"
    estimated_time: str                  # e.g., "15-20 minutes"
    tools_required: List[str] = field(default_factory=list)
    step_by_step_guide: List[str] = field(default_factory=list)
    environmental_benefit: str = ""      # e.g., "Diverts 45g of plastic from landfill"
    carbon_offset_rating: str = "Medium" # "Low", "Medium", "High"


@dataclass
class MatchedOpportunity:
    """Represents a matched reuse opportunity for analyzed waste material (Phase 4)."""
    opportunity_name: str                # Name of opportunity / organization / project
    opportunity_category: str            # Domain category
    match_score: float                   # Score from 0.0 to 100.0
    reason: str                          # Specific justification for matching
    suggested_application: str           # Practical application advice
    target_user: str = ""                # Potential user / beneficiary

    def to_dict(self) -> Dict[str, Any]:
        """Convert matched opportunity to dictionary."""
        return asdict(self)


@dataclass
class WasteAnalysisResult:
    """Comprehensive analysis result output by the Vision subsystem and Resource Matcher.
    Serves as the direct interface contract for Subsystem 2 (Matching Engine)
    and strictly preserves the 6-field standardized JSON schema.
    """
    material: MaterialAnalysis
    reuse_suggestions: List[ReuseSuggestion] = field(default_factory=list)
    matched_opportunities: List[MatchedOpportunity] = field(default_factory=list)
    potential_industry_matches: List[str] = field(default_factory=list)
    handling_instructions: List[str] = field(default_factory=list)
    summary: str = ""
    is_demo_mode: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def waste_type(self) -> str:
        return self.material.primary_category

    @property
    def condition(self) -> str:
        return self.material.physical_condition

    @property
    def recyclable(self) -> bool:
        return self.material.recyclable

    @property
    def confidence(self) -> float:
        return self.material.confidence_score

    @property
    def reuse_ideas(self) -> List[str]:
        ideas: List[str] = []
        for s in self.reuse_suggestions:
            if s.step_by_step_guide:
                guide_str = " ".join(s.step_by_step_guide)
                ideas.append(f"{s.title}: {guide_str}" if not guide_str.startswith(s.title) else guide_str)
            else:
                ideas.append(s.title)
        return ideas

    def to_schema_dict(self) -> Dict[str, Any]:
        """Return the exact 6-field JSON schema:
        material, waste_type, condition, recyclable, confidence, reuse_ideas.
        """
        return {
            "material": self.material.material_type,
            "waste_type": self.material.primary_category,
            "condition": self.material.physical_condition,
            "recyclable": self.material.recyclable,
            "confidence": round(self.material.confidence_score, 2),
            "reuse_ideas": self.reuse_ideas,
        }

    def to_schema_json(self, indent: int = 2) -> str:
        """Serialize the exact 6-field schema to a formatted JSON string."""
        return json.dumps(self.to_schema_dict(), indent=indent)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the analysis result to a Python dictionary.
        Preserves existing object structure while ensuring top-level standard schema keys.
        """
        data = asdict(self)
        data["waste_type"] = self.waste_type
        data["condition"] = self.condition
        data["recyclable"] = self.recyclable
        data["confidence"] = self.confidence
        data["reuse_ideas"] = self.reuse_ideas
        data["cleanliness_level"] = self.material.cleanliness_level
        data["cleanliness_explanation"] = self.material.cleanliness_explanation
        return data

    def to_json(self, indent: int = 2) -> str:
        """Serialize the full analysis result to a JSON formatted string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WasteAnalysisResult":
        """Reconstruct a WasteAnalysisResult object from either the flat 6-field schema
        or the full detailed dictionary.
        """
        raw_mat = data.get("material", {})
        if isinstance(raw_mat, str):
            # Flat standardized schema
            material_type = raw_mat
            primary_category = str(data.get("waste_type", "Plastics")).strip()
            physical_condition = str(data.get("condition", "Intact")).strip()
            confidence_score = float(data.get("confidence", 0.9))
            rec_val = data.get("recyclable", True)
            rec_score = 85 if rec_val is True else (25 if rec_val is False else int(rec_val))
            cleanliness_val = data.get("cleanliness_level")
            cleanliness_str = str(cleanliness_val).strip() if cleanliness_val and str(cleanliness_val).strip() else "Unknown"
            material = MaterialAnalysis(
                material_type=material_type,
                primary_category=primary_category,
                sub_category=str(data.get("sub_category", "Standard grade")).strip(),
                confidence_score=confidence_score,
                cleanliness_level=cleanliness_str,
                physical_condition=physical_condition,
                recyclability_score=rec_score,
                detected_features=data.get("detected_features", []),
                hazardous_elements=data.get("hazardous_elements", []),
                cleanliness_explanation=data.get("cleanliness_explanation"),
            )
        else:
            # Nested dictionary
            cleanliness_val = raw_mat.get("cleanliness_level") or data.get("cleanliness_level")
            cleanliness_str = str(cleanliness_val).strip() if cleanliness_val and str(cleanliness_val).strip() else "Unknown"
            material = MaterialAnalysis(
                material_type=raw_mat.get("material_type", "Unknown"),
                primary_category=raw_mat.get("primary_category", "Unknown"),
                sub_category=raw_mat.get("sub_category", "Unknown"),
                confidence_score=float(raw_mat.get("confidence_score", 0.0)),
                cleanliness_level=cleanliness_str,
                physical_condition=raw_mat.get("physical_condition", "Unknown"),
                recyclability_score=int(raw_mat.get("recyclability_score", 0)),
                detected_features=raw_mat.get("detected_features", []),
                hazardous_elements=raw_mat.get("hazardous_elements", []),
                cleanliness_explanation=raw_mat.get("cleanliness_explanation", data.get("cleanliness_explanation")),
            )

        # Parse suggestions from either reuse_suggestions or reuse_ideas
        raw_suggs = data.get("reuse_suggestions", [])
        if not raw_suggs and "reuse_ideas" in data:
            raw_ideas = data.get("reuse_ideas", [])
            suggestions = [
                ReuseSuggestion(
                    title=idea.split(":")[0].strip() if ":" in idea else idea[:40].strip(),
                    category="DIY / Upcycling",
                    difficulty="Easy",
                    estimated_time="15-30 mins",
                    tools_required=["Basic household tools"],
                    step_by_step_guide=[idea],
                    environmental_benefit="Diverts waste from landfills into functional repurposing.",
                    carbon_offset_rating="Medium",
                )
                for idea in raw_ideas if isinstance(idea, str) and idea.strip()
            ]
        else:
            suggestions = [
                ReuseSuggestion(
                    title=s.get("title", ""),
                    category=s.get("category", "DIY / Household"),
                    difficulty=s.get("difficulty", "Easy"),
                    estimated_time=s.get("estimated_time", "N/A"),
                    tools_required=s.get("tools_required", []),
                    step_by_step_guide=s.get("step_by_step_guide", []),
                    environmental_benefit=s.get("environmental_benefit", ""),
                    carbon_offset_rating=s.get("carbon_offset_rating", "Medium"),
                )
                for s in raw_suggs
            ]

        # Parse matched opportunities (Phase 4)
        matched_opps = [
            MatchedOpportunity(
                opportunity_name=m.get("opportunity_name", ""),
                opportunity_category=m.get("opportunity_category", ""),
                match_score=float(m.get("match_score", 0.0)),
                reason=m.get("reason", ""),
                suggested_application=m.get("suggested_application", ""),
                target_user=m.get("target_user", ""),
            )
            for m in data.get("matched_opportunities", [])
        ]

        return cls(
            material=material,
            reuse_suggestions=suggestions,
            matched_opportunities=matched_opps,
            potential_industry_matches=data.get("potential_industry_matches", []),
            handling_instructions=data.get("handling_instructions", []),
            summary=data.get("summary", ""),
            is_demo_mode=data.get("is_demo_mode", False),
            metadata=data.get("metadata", {}),
        )
