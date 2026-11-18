"""AI Client module for ReUseAI.
Uses the official Groq Python SDK with the high-speed vision model: qwen/qwen3.8-27b.
Preprocessed images are encoded as base64 and sent in a single API request,
strictly adhering to the standardized schema:
(material, waste_type, condition, recyclable, confidence, reuse_ideas).
"""

import base64
import json
import re
import time
from typing import Dict, Any, Optional
from PIL import Image

from groq import (
    Groq,
    GroqError,
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
)

from src.config import (
    GROQ_API_KEY,
    DEFAULT_MODEL,
    API_REQUEST_TIMEOUT_MS,
    MAX_API_RETRIES,
)
from src.utils.image_processor import image_to_bytes

# Strict system prompt enforcing the exact standardized 6-field JSON schema
VISION_SYSTEM_PROMPT = """You are ReUseAI, an expert circular economy and material classification vision AI.
Analyze the provided waste material image. You MUST return ONLY a valid JSON object with this exact schema:
{
  "material": "Specific material name (e.g. Polyethylene Terephthalate / PET Plastic)",
  "waste_type": "Primary waste category (e.g. Plastics, Cardboard & Paper, Metals, Glass, Textiles, Electronics, Wood & Timber, Organics, Other)",
  "condition": "Physical condition and state (e.g. Intact, Clean / Crushed / Lightly Soiled / Fragmented)",
  "recyclable": true,
  "confidence": 0.95,
  "reuse_ideas": [
    "Unique Descriptive Project 1: 1. Preparation step... 2. Measuring/cutting step... 3. Assembly step... 4. Finishing step... 5. Practical deployment step",
    "Unique Descriptive Project 2: 1. Preparation step... 2. Measuring/cutting step... 3. Assembly step... 4. Finishing step... 5. Practical deployment step"
  ]
}
Requirements for reuse_ideas:
- Provide 2 to 3 distinct, practical reuse or upcycling applications.
- Never use generic titles like 'DIY Upcycling Project'. Give a specific descriptive project title.
- Each idea must outline sequential, actionable steps explaining the physical fabrication process.
Output pure valid JSON only. Do not include markdown formatting or commentary outside the JSON."""


class GroqVisionClient:
    """Official Groq Vision client wrapper for waste material analysis."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = (api_key if api_key is not None else GROQ_API_KEY).strip()
        self.model_name = (model_name if model_name is not None else DEFAULT_MODEL).strip()
        self.client: Optional[Groq] = None
        self._init_client()

    def _init_client(self):
        """Initialize the official Groq client with configured timeout."""
        if not self.api_key or self.api_key.startswith("your_"):
            self.client = None
            return

        try:
            timeout_sec = float(API_REQUEST_TIMEOUT_MS) / 1000.0
            self.client = Groq(
                api_key=self.api_key,
                timeout=timeout_sec,
                max_retries=max(0, MAX_API_RETRIES - 1),
            )
        except Exception:
            self.client = None

    def is_ready(self) -> bool:
        """Check whether live Groq Vision calls can be executed."""
        return bool(self.client is not None and self.api_key and not self.api_key.startswith("your_"))

    def analyze_image(self, image: Image.Image) -> Dict[str, Any]:
        """Perform vision analysis on the given PIL Image using the live Groq Vision API.
        Measures API request latency and JSON parsing latency with high precision.

        Returns a dictionary adhering strictly to the required schema:
        material, waste_type, condition, recyclable, confidence, reuse_ideas,
        along with stage execution timings and provider metadata.
        """
        if not self.is_ready():
            raise ValueError(
                "Groq Vision API key is not configured. Please provide a valid GROQ_API_KEY "
                "in your .env file or sidebar settings to run live AI analysis."
            )

        if not isinstance(image, Image.Image):
            raise TypeError("Expected a valid PIL Image instance for vision analysis.")

        # Measure single API call
        t_api_start = time.perf_counter()
        raw_text = self._call_groq_api(image)
        t_api_end = time.perf_counter()

        # Measure JSON parsing
        t_parse_start = time.perf_counter()
        parsed = self._extract_json(raw_text)
        t_parse_end = time.perf_counter()

        # Ensure exact schema keys are present and clean
        normalized = self._normalize_schema(parsed)

        api_seconds = round(t_api_end - t_api_start, 3)
        parse_seconds = round(t_parse_end - t_parse_start, 4)

        normalized["is_demo_mode"] = False
        normalized["metadata"] = {
            "api_latency_seconds": api_seconds,
            "parse_latency_seconds": parse_seconds,
            "timings": {
                "api_request_seconds": api_seconds,
                "parsing_seconds": parse_seconds,
            },
            "model_used": self.model_name,
            "provider": "groq",
        }
        return normalized

    def _call_groq_api(self, image: Image.Image) -> str:
        """Encode the preprocessed image to base64 and make a single Groq Vision call."""
        # Convert preprocessed image to JPEG bytes then base64
        try:
            img_bytes = image_to_bytes(image, format_name="JPEG", quality=90)
            b64_str = base64.b64encode(img_bytes).decode("utf-8")
            data_url = f"data:image/jpeg;base64,{b64_str}"
        except Exception as exc:
            raise ValueError(f"Failed to encode image to base64: {str(exc)}") from exc

        prompt = (
            f"{VISION_SYSTEM_PROMPT}\n\n"
            "Analyze the waste material in this image now. Return only JSON adhering to the exact schema."
        )

        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": data_url}
                            }
                        ]
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
                max_tokens=1500,
            )
            if not completion or not completion.choices or not completion.choices[0].message:
                raise ValueError("Groq Vision API returned an empty response.")
            return completion.choices[0].message.content or ""
        except AuthenticationError as exc:
            raise PermissionError(
                "Invalid or unauthorized Groq API key. Please check your GROQ_API_KEY in .env or the sidebar."
            ) from exc
        except RateLimitError as exc:
            raise RuntimeError(
                "Groq Vision API rate limit or quota exceeded. Please wait a moment before trying again."
            ) from exc
        except APITimeoutError as exc:
            raise TimeoutError(
                f"Groq Vision API request timed out after {API_REQUEST_TIMEOUT_MS // 1000}s. Please check your network and try again."
            ) from exc
        except APIConnectionError as exc:
            raise ConnectionError(
                "Failed to connect to Groq API. Please check your internet connection."
            ) from exc
        except APIStatusError as exc:
            raise RuntimeError(
                f"Groq API error (status {exc.status_code}): {exc.message}"
            ) from exc
        except GroqError as exc:
            raise RuntimeError(f"Groq Vision error: {str(exc)}") from exc

    def _extract_json(self, response_text: str) -> Dict[str, Any]:
        """Extract and parse JSON from model response text with robust fallback logic."""
        if not response_text or not str(response_text).strip():
            raise ValueError("Vision model returned an empty response.")
        text = str(response_text).strip()

        # If already clean JSON
        if text.startswith("{") and text.endswith("}"):
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass

        # Strip markdown fences if present
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            text = match.group(1).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            json_start = text.find("{")
            json_end = text.rfind("}")
            if json_start != -1 and json_end != -1:
                try:
                    return json.loads(text[json_start : json_end + 1])
                except json.JSONDecodeError:
                    pass
            raise ValueError(f"Model returned malformed JSON: {text[:200]}")

    def _normalize_schema(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Enforce the exact 6-field standardized schema:
        material, waste_type, condition, recyclable, confidence, reuse_ideas.
        """
        material = str(raw.get("material") or raw.get("material_type", "Unknown Material")).strip()
        waste_type = str(raw.get("waste_type") or raw.get("primary_category", "Other")).strip()
        condition = str(raw.get("condition") or raw.get("physical_condition", "Intact")).strip()

        rec_val = raw.get("recyclable")
        if rec_val is None:
            rec_val = raw.get("recyclability_score")
        if isinstance(rec_val, bool):
            recyclable = rec_val
        elif isinstance(rec_val, (int, float)):
            recyclable = rec_val >= 50
        elif isinstance(rec_val, str):
            recyclable = rec_val.lower() in ("true", "yes", "1", "recyclable")
        else:
            recyclable = True

        conf_val = raw.get("confidence")
        if conf_val is None:
            conf_val = raw.get("confidence_score", 0.90)
        try:
            confidence = round(max(0.0, min(1.0, float(conf_val))), 2)
        except (ValueError, TypeError):
            confidence = 0.90

        raw_ideas = raw.get("reuse_ideas") or raw.get("reuse_suggestions", [])
        if not isinstance(raw_ideas, list):
            raw_ideas = [str(raw_ideas)]

        reuse_ideas = []
        for idea in raw_ideas:
            if isinstance(idea, str) and idea.strip():
                reuse_ideas.append(idea.strip())
            elif isinstance(idea, dict):
                title = idea.get("title", "")
                guide = idea.get("step_by_step_guide", [])
                if guide and isinstance(guide, list):
                    reuse_ideas.append(f"{title}: {' '.join(guide)}")
                elif title:
                    reuse_ideas.append(title)

        if not reuse_ideas:
            reuse_ideas = [
                "Clean and repurpose as an eco-friendly storage container or household organizer.",
                "Donate to a local community upcycling or secondary craft collective."
            ]

        # Construct normalized dictionary strictly with the 6 schema keys
        normalized = {
            "material": material,
            "waste_type": waste_type,
            "condition": condition,
            "recyclable": recyclable,
            "confidence": confidence,
            "reuse_ideas": reuse_ideas,
        }

        # Preserve any additional domain fields if available
        for key in ("handling_instructions", "detected_features", "hazardous_elements", "summary"):
            if key in raw:
                normalized[key] = raw[key]

        return normalized


# Backward-compatible alias for any legacy modules or tests
GeminiVisionClient = GroqVisionClient
