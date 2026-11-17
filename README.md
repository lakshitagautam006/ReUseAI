# ReUseAI – Intelligent Waste-to-Resource Matcher
> **Subsystem 1: Computer Vision & Material Analysis Engine**  
> *Built with Python, Streamlit, Groq Vision API (qwen/qwen3.8-27b), Pillow, and Python-dotenv.*

---

## 📌 Project Overview

**ReUseAI** is an AI-powered circular economy platform designed to divert industrial, commercial, and household waste from landfills into productive secondary lifecycles.

This repository contains **Subsystem 1 (Member 1's deliverable)**:
- **Computer Vision Recognition:** Ingests images of waste items via upload and analyzes them using Groq Vision (`qwen/qwen3.8-27b`).
- **Material Classification:** Identifies polymer/material types (PET, HDPE, Cardboard, Aluminum, Glass, etc.) and visual features.
- **State & Recyclability Diagnostics:** Evaluates cleanliness, contamination, structural condition, and calculates a 0–100 Recyclability Index.
- **Upcycling Synthesis:** Generates step-by-step DIY upcycling guides, required tools, and estimated carbon offsets in a single API request.
- **Interface for Subsystem 2:** Prepares standardized industrial feedstock match targets and JSON payloads strictly adhering to the exact 6-field contract (`material`, `waste_type`, `condition`, `recyclable`, `confidence`, `reuse_ideas`) for **Team Member 2's Matching Engine and Database**.

---

## 🗂️ Clean & Modular Project Structure

```text
ReUseAI/
│
├── .env.example                 # Template for Groq API credentials and configuration
├── .gitignore                   # Git ignore rules for Python, virtual environments, .env
├── requirements.txt             # Lightweight dependencies (Groq SDK, Streamlit, Pillow)
├── README.md                    # Project documentation and execution instructions
├── app.py                       # Main Streamlit web application entry point
│
├── src/                         # Core modular source package
│   ├── __init__.py
│   ├── config.py                # Environment variable loader and global settings
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py           # Dataclasses and standardized 6-field schema serializers
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_client.py         # Official Groq Vision client (qwen/qwen3.8-27b)
│   │   ├── analyzer.py          # Unified WasteAnalyzer orchestrator pipeline
│   │   ├── matching_engine.py   # Phase 4: Resource Matching Engine & Opportunity Catalog
│   │   ├── material_detector.py # Material classification and recyclability penalty engine
│   │   └── reuse_engine.py      # Upcycling project generator and industry match hook
│   │
│   └── utils/
│       ├── __init__.py
│       ├── image_processor.py   # Pillow image validation, normalisation, and resizing
│       └── sample_generator.py  # Built-in synthetic waste graphics for instant UI testing
│
└── tests/
    ├── __init__.py
    ├── test_matching_engine.py  # Phase 4 unit tests for resource matching & scoring
    ├── test_groq_vision.py      # Unit & live integration tests for Groq Vision API
    ├── test_modules.py          # Unit and integration tests for all core modules
    ├── test_image_processor.py  # Phase 3 unit tests for image validation and preprocessing
    └── test_navigation.py       # Streamlit navigation flow tests
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- **Python 3.10+** (Tested on Python 3.12 on Windows)
- **VS Code** (or any modern IDE / terminal)

### 2. Environment Setup (Recommended)
Open PowerShell or Command Prompt in the project folder:

```powershell
# Navigate to the project root
cd c:\Users\Dell\Documents\ReUseAI

# (Optional but recommended) Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Windows Command Prompt (cmd):
.\venv\Scripts\activate.bat
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure API Credentials
Copy `.env.example` to `.env`:
```powershell
copy .env.example .env
```
Open `.env` in VS Code and set your Groq API key:
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=qwen/qwen3.8-27b
```

### 5. Run the Streamlit Application
```powershell
streamlit run app.py
```
Streamlit will automatically open your browser at `http://localhost:8501`.

### 6. Run Unit & Integration Tests
To verify all modules and Groq Vision integration:
```powershell
python -m unittest discover tests
```

---

## 🔌 Integration Interface for Subsystem 2 (Team Member 2)

All analyses produce a standardized payload that can be exported directly from the web interface or serialized via Python:

### Standardized 6-Field JSON Schema Contract:
```json
{
  "material": "Polyethylene Terephthalate / PET",
  "waste_type": "Plastics",
  "condition": "Intact, Clean",
  "recyclable": true,
  "confidence": 0.98,
  "reuse_ideas": [
    "Create a self-watering planter by cutting the bottle in half, inverting the top section into the base, and adding a cotton wick.",
    "Make a DIY hanging bird feeder with feeding ports and a dowel perch."
  ]
}
```

Member 2 can directly import `WasteAnalyzer` into their FastAPI/Flask or backend worker:
```python
from src.services.analyzer import WasteAnalyzer

analyzer = WasteAnalyzer()
result = analyzer.analyze("path/to/waste_image.jpg")

# Export exact 6-field schema:
payload = result.to_schema_dict()
# {
#   "material": "...",
#   "waste_type": "...",
#   "condition": "...",
#   "recyclable": True,
#   "confidence": 0.98,
#   "reuse_ideas": [...]
# }
```
