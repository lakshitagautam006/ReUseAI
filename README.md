# ♻️ ReUseAI – Intelligent Waste-to-Resource Matcher

ReUseAI is a circular economy web application built with **Python**, **Streamlit**, **Groq Vision AI**, and **PostgreSQL**. It analyzes uploaded waste material photographs to classify materials, evaluate physical condition and recyclability, generate step-by-step reuse and upcycling guides, match circular secondary-use opportunities, persist analyses in PostgreSQL, and visualize live database telemetry on an Impact Dashboard.

---

## Key Capabilities

- **Image Validation & Preprocessing (`src/utils/image_processor.py`)**: Validates JPG, JPEG, PNG, and WEBP uploads (up to 10 MB), corrects EXIF orientation, composites transparent channels onto RGB, and downscales oversized images to ≤ 1024 px while preserving aspect ratio.
- **Vision AI Material Analysis (`src/services/ai_client.py`, `src/services/material_detector.py`)**: Uses the official Groq Python SDK (`qwen/qwen3.8-27b` by default) to analyze images in a single request and apply domain recyclability rules.
- **Reuse & Upcycling Engine (`src/services/reuse_engine.py`)**: Produces descriptive, unique reuse and upcycling recommendations with 4–6 sequential fabrication steps, tool lists, and qualitative eco-benefits.
- **Resource Matching Engine (`src/services/matching_engine.py`)**: Scores circular opportunities across material compatibility, waste category, physical condition/integrity, and application synergy with four-point match rationales.
- **PostgreSQL Persistence & Analysis History (`src/database/connection.py`, `src/database/repository.py`)**: Saves complete analyses, linked reuse suggestions, and matched opportunities transactionally, with searchable/filterable history retrieval.
- **Live Impact Dashboard (`app.py`)**: Displays real-time KPIs, category distribution, daily activity, condition/cleanliness breakdowns, reuse & opportunity insights, and top materials directly from PostgreSQL—without fabricating weight (kg) or CO₂ savings estimates.

---

## Standardized 6-Field JSON Schema

ReUseAI enforces a backward-compatible six-field JSON contract (`WasteAnalysisResult.to_schema_dict()` / `to_schema_json()`):

```json
{
  "material": "Polyethylene Terephthalate / PET",
  "waste_type": "Plastics",
  "condition": "Intact, Clean",
  "recyclable": true,
  "confidence": 0.96,
  "reuse_ideas": [
    "Sub-Irrigated Self-Watering Planter: ..."
  ]
}
```

| Field | Type | Description |
| :--- | :--- | :--- |
| `material` | `string` | Specific identified material name |
| `waste_type` | `string` | Primary waste category (e.g., `Plastics`, `Glass`, `Metals`, `Cardboard & Paper`) |
| `condition` | `string` | Physical state and condition assessment |
| `recyclable` | `boolean` | Recyclability classification (`true` when `recyclability_score >= 50`) |
| `confidence` | `float` | Vision model confidence score (`0.0` to `1.0`) |
| `reuse_ideas` | `list[string]` | Actionable reuse and upcycling suggestions |

---

## Project Structure

```text
ReUseAI/
├── app.py                          # Streamlit frontend (Home, Analyze Waste, Results, History, Impact Dashboard, About)
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variable template
├── src/
│   ├── config.py                   # Environment & application settings
│   ├── database/
│   │   ├── connection.py           # PostgreSQL connection management (psycopg v3)
│   │   └── repository.py           # Transactional persistence, retrieval, and Impact Dashboard queries
│   ├── models/
│   │   └── schemas.py              # Dataclasses and 6-field JSON schema serialization/deserialization
│   ├── services/
│   │   ├── ai_client.py            # Groq Vision API wrapper & JSON normalization
│   │   ├── analyzer.py             # End-to-end analysis pipeline orchestrator
│   │   ├── material_detector.py    # Material evaluation & recyclability scoring
│   │   ├── reuse_engine.py         # Step-by-step reuse/upcycling generator
│   │   └── matching_engine.py      # Multi-factor circular opportunity matcher
│   └── utils/
│       ├── image_processor.py      # Validation, EXIF transpose, RGB normalization, resizing
│       └── sample_generator.py     # Synthetic sample discard images for quick testing
└── tests/
    ├── test_database.py            # Database persistence, rollback, and retrieval tests
    ├── test_end_to_end_workflow.py # Full mocked pipeline → DB persistence integration tests
    ├── test_frontend_redesign.py   # Streamlit AppTest UI rendering tests
    ├── test_groq_vision.py         # Groq Vision client, 6-field schema, and error handling tests
    ├── test_image_processor.py     # Image validation & preprocessing tests
    ├── test_impact_dashboard.py    # Impact Dashboard aggregation & UI state tests
    ├── test_matching_engine.py     # Resource matching & reuse engine tests
    ├── test_modules.py             # Core subsystem unit tests
    └── test_navigation.py          # Streamlit page navigation tests
```

---

## Setup & Installation

### 1. Create and Activate a Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your real values (never commit `.env`):

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=qwen/qwen3.8-27b
DATABASE_URL=postgresql://username:password@localhost:5432/reuseai
DB_CONNECT_TIMEOUT=5
APP_ENV=development
```

### 3. PostgreSQL Schema Reference

ReUseAI expects three relational tables in your PostgreSQL database:

- **`analyses`**: `id` (PK), `material_type`, `primary_category`, `sub_category`, `confidence_score`, `cleanliness_level`, `physical_condition`, `recyclability_score`, `full_result` (`JSONB`), `created_at` (`TIMESTAMP`)
- **`reuse_suggestions`**: `id` (PK), `analysis_id` (FK → `analyses.id`), `suggestion_data` (`JSONB`)
- **`matched_opportunities`**: `id` (PK), `analysis_id` (FK → `analyses.id`), `opportunity_data` (`JSONB`)

---

## Running the Application

```powershell
streamlit run app.py
```

---

## Running Tests

Run the full automated test suite:

```powershell
pytest -v
```

By default, both live external integration test flags are **disabled**. Ordinary `pytest` runs use mocked unit and integration tests without making live PostgreSQL writes or live Groq Vision API calls.

### Optional Live Integration Tests (Windows PowerShell)

- **`RUN_LIVE_DB_TESTS=1`** — enables live PostgreSQL integration tests in `tests/test_database.py` (requires a reachable PostgreSQL database configured in `DATABASE_URL`):

```powershell
$env:RUN_LIVE_DB_TESTS="1"
pytest tests/test_database.py -v
Remove-Item Env:RUN_LIVE_DB_TESTS
```

- **`RUN_LIVE_GROQ_TESTS=1`** — enables the live Groq Vision API integration test in `tests/test_groq_vision.py` (requires a valid `GROQ_API_KEY` and network access):

```powershell
$env:RUN_LIVE_GROQ_TESTS="1"
pytest tests/test_groq_vision.py -v
Remove-Item Env:RUN_LIVE_GROQ_TESTS
```
