"""Waste Analyzer Orchestrator Module.
Connects image preprocessing, vision AI, material detection, and reuse engines
into an optimized, single-pass execution pipeline with stage-by-stage timing.
"""

from typing import Union, Dict, Any, Callable, Optional
from PIL import Image
from io import BytesIO
import time

from src.models.schemas import WasteAnalysisResult
from src.utils.image_processor import (
    validate_image,
    preprocess_image,
    get_image_metadata,
    open_image,
)
from src.services.ai_client import GroqVisionClient, GeminiVisionClient
from src.services.material_detector import MaterialDetector
from src.services.reuse_engine import ReuseEngine
from src.services.matching_engine import ResourceMatchingEngine


class WasteAnalyzer:
    """High-level orchestrator for the ReUseAI image recognition subsystem.
    Callable by Streamlit, CLI scripts, and future REST/FastAPI endpoints.
    """

    def __init__(self, api_key: str = None, model_name: str = None):
        self.ai_client = GroqVisionClient(api_key=api_key, model_name=model_name)
        self.detector = MaterialDetector()
        self.reuse_engine = ReuseEngine()
        self.matching_engine = ResourceMatchingEngine()

    @property
    def is_api_ready(self) -> bool:
        """Returns True if the vision client is configured with a valid API key."""
        return self.ai_client.is_ready()

    def analyze(
        self,
        image_input: Union[Image.Image, bytes, BytesIO],
        progress_callback: Optional[Callable[[str, str], None]] = None,
    ) -> WasteAnalysisResult:
        """Run the end-to-end material analysis and recommendation pipeline.
        Measures individual stage execution times for performance monitoring.

        Args:
            image_input: PIL Image, raw bytes, or BytesIO buffer.
            progress_callback: Optional callable(stage_code, status_message) for UI feedback.

        Returns:
            WasteAnalysisResult schema containing material specs, reuse suggestions, and timings.
        """
        pipeline_start = time.perf_counter()

        # Step 1: Input Validation
        is_valid, error_msg = validate_image(image_input)
        if not is_valid:
            raise ValueError(f"Image validation failed: {error_msg}")

        # Step 2: Image Opening & Preprocessing
        if progress_callback:
            progress_callback("preprocessing", "Preprocessing image & optimizing resolution...")

        t_prep_start = time.perf_counter()
        pil_image = open_image(image_input)

        metadata = get_image_metadata(pil_image)
        optimized_image = preprocess_image(pil_image)
        t_prep_end = time.perf_counter()
        prep_duration = t_prep_end - t_prep_start

        # Step 3: Single Groq Vision Request
        if progress_callback:
            progress_callback("vision_ai", "Analyzing material with Groq Vision (qwen/qwen3.8-27b)...")

        raw_ai_output = self.ai_client.analyze_image(optimized_image)

        ai_meta = raw_ai_output.get("metadata", {})
        ai_timings = ai_meta.get("timings", {})
        api_duration = ai_timings.get("api_request_seconds", ai_meta.get("latency_seconds", 0.0))
        parse_duration = ai_timings.get("parsing_seconds", 0.0)

        # Step 4: Material Detection & Scoring Diagnostics
        if progress_callback:
            progress_callback("diagnostics", "Evaluating condition & computing recyclability index...")

        t_reuse_start = time.perf_counter()
        material = self.detector.evaluate(raw_ai_output)

        # Step 5: Reuse & Upcycling Recommendation Engine
        if progress_callback:
            progress_callback("reuse_engine", "Generating upcycling guides & industrial matches...")

        raw_suggestions = raw_ai_output.get("reuse_ideas") or raw_ai_output.get("reuse_suggestions", [])
        reuse_suggestions = self.reuse_engine.generate_suggestions(raw_suggestions, material)

        # Step 6: Resource Matching Engine (Phase 4)
        if progress_callback:
            progress_callback("matching", "Matching waste with reuse opportunities & potential users...")

        matched_opportunities = self.matching_engine.match(
            material=material.material_type,
            waste_type=material.primary_category,
            condition=material.physical_condition,
            recyclable=material.recyclable,
            reuse_ideas=raw_ai_output.get("reuse_ideas", []),
            confidence=material.confidence_score,
            top_k=3,
        )

        # Step 7: Industrial Match Candidate Preparation (Interface for Member 2)
        raw_matches = raw_ai_output.get("potential_industry_matches", [])
        industry_matches = self.reuse_engine.get_industry_matches(material, raw_matches)
        t_reuse_end = time.perf_counter()
        reuse_duration = t_reuse_end - t_reuse_start

        total_duration = time.perf_counter() - pipeline_start

        if progress_callback:
            progress_callback("complete", "Analysis complete!")

        # Consolidate all stage timings into metadata
        timings = {
            "preprocessing_seconds": round(prep_duration, 4),
            "api_request_seconds": round(api_duration, 3),
            "parsing_seconds": round(parse_duration, 4),
            "reuse_generation_seconds": round(reuse_duration, 4),
            "total_seconds": round(total_duration, 3),
        }

        merged_metadata = {
            **metadata,
            **ai_meta,
            "timings": timings,
        }

        return WasteAnalysisResult(
            material=material,
            reuse_suggestions=reuse_suggestions,
            matched_opportunities=matched_opportunities,
            potential_industry_matches=industry_matches,
            handling_instructions=raw_ai_output.get("handling_instructions", [
                "Clean and dry the item thoroughly before storage or transfer.",
                "Ensure local municipal or industrial recycling acceptance."
            ]),
            summary=raw_ai_output.get("summary", "Material identified and analyzed successfully."),
            is_demo_mode=raw_ai_output.get("is_demo_mode", False),
            metadata=merged_metadata,
        )
