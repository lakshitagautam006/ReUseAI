"""Reuse Suggestions and Resource Match Preparation Engine.
Transforms identified material attributes into actionable upcycling projects
and pre-formats potential industrial matches for Member 2's matching engine.
Guarantees unique, descriptive project titles and 4-6 sequential, actionable steps
tailored to material types, conditions, and practical applications.
"""

import re
from typing import List, Dict, Any, Optional, Set
from src.models.schemas import ReuseSuggestion, MaterialAnalysis


# Industry classification database mapping for handoff to matching engine
INDUSTRY_FEEDSTOCK_PROFILES = {
    "Plastics": [
        "Mechanical rPET / rHDPE Pelletizers",
        "Textile Fiber & Staple Yarn Manufacturers",
        "Local Makerspace Extrusion & 3D Print Collectives",
        "Blow-molding Packaging Re-processors"
    ],
    "Cardboard & Paper": [
        "Kraft Pulp & Corrugated Box Board Mills",
        "Molded Pulp Packaging & Egg Carton Converters",
        "Cellulose Fiber Thermal Insulation Manufacturers"
    ],
    "Metals": [
        "Secondary Aluminum Smelters & Ingot Casting",
        "Scrap Metal Shredders & Magnetic Sorters",
        "Ferrous Foundry Re-melt Plants"
    ],
    "Glass": [
        "Cullet Beneficiation & Optical Sorting Plants",
        "Fiberglass Insulation Blenders",
        "Foamed Glass & Construction Aggregate Mixers",
        "Zero-Waste Container Sanitization & Refill Hubs"
    ],
    "Textiles": [
        "Shoddy & Mungo Mechanical Fiber Tearing Plants",
        "Automotive Acoustic Underlay & Soundproofing Recyclers",
        "Industrial Cleaning Rag Converters"
    ],
    "Electronics": [
        "WEEE Certified E-Scrap & Precious Metal Refiners",
        "Battery Hydrometallurgical Extraction Facilities",
        "Component Refurbishers & Secondary Hardware Labs"
    ],
    "Wood & Timber": [
        "Engineered Particleboard & Biomass Pellet Producers",
        "Architectural Salvage & Upcycled Furniture Workshops",
        "Landscaping Mulch & Woodchip Processors"
    ],
    "Organics": [
        "Commercial Aerobic In-Vessel Composting Facilities",
        "Anaerobic Digestion & Biomethane Generators"
    ]
}


# Curated project catalogs with 4-6 actionable, sequential fabrication steps
CURATED_PROJECT_CATALOG: Dict[str, List[Dict[str, Any]]] = {
    "Plastics": [
        {
            "title": "Sub-Irrigated Self-Watering Herb Planter",
            "category": "Urban Agriculture & Gardening",
            "difficulty": "Easy",
            "estimated_time": "20-25 mins",
            "tools_required": ["Utility knife or heavy scissors", "Cotton wick / thick yarn", "Potting soil", "Water"],
            "step_by_step_guide": [
                "Thoroughly clean the plastic container with warm soapy water and remove any adhesive labels.",
                "Using a utility knife, carefully cut the bottle horizontally approximately 4 inches below the bottle neck.",
                "Invert the top funnel section upside-down into the bottom reservoir base.",
                "Feed an 8-inch braided cotton wick through the mouth opening so 3 inches dangle into the lower reservoir.",
                "Fill the inverted upper cup with potting soil, insert your herb seedling, and pour water into the base reservoir."
            ],
            "environmental_benefit": "Diverts rigid PET/HDPE polymers from landfills while establishing zero-electricity food growing.",
            "carbon_offset_rating": "Medium"
        },
        {
            "title": "Modular Interlocking Workshop Storage Organizer",
            "category": "Home Organization & Workshop",
            "difficulty": "Easy",
            "estimated_time": "15-20 mins",
            "tools_required": ["Box cutter", "Sandpaper (fine grit)", "Permanent marker", "Paper clips or binder clips"],
            "step_by_step_guide": [
                "Wash and dry the plastic containers completely to eliminate any chemical or food residues.",
                "Mark a level cutting line 3 inches from the container bottom using a ruler and marker.",
                "Trim along the marked line with a sharp blade to create uniform open-top storage caddies.",
                "Smooth any sharp cut plastic edges using 220-grit sandpaper to prevent finger scrapes.",
                "Arrange the bins in a grid inside drawers or workshops and clip them together for screws, nails, or stationery."
            ],
            "environmental_benefit": "Replaces purchased virgin injection-molded plastic organizers with repurposed durable vessels.",
            "carbon_offset_rating": "Low"
        },
        {
            "title": "Precision 1.75mm 3D Printer Filament Feedstock",
            "category": "Makerspace & Additive Manufacturing",
            "difficulty": "Moderate",
            "estimated_time": "45-60 mins",
            "tools_required": ["Rotary bottle cutter blade", "Heat gun or PID heater block", "Shredder / spooling rig"],
            "step_by_step_guide": [
                "Inspect the bottle to ensure clean, label-free thermoplastic resin (PET or HDPE).",
                "Cut away the uneven bottle base and mount the cylinder onto a specialized strip-pulling blade jig.",
                "Pull a continuous 9mm-wide plastic ribbon from the rotating bottle wall under steady tension.",
                "Feed the plastic ribbon through an 8mm heated brass extrusion nozzle calibrated to 210°C.",
                "Collect the extruded, cooled 1.75mm round filament onto a standard 3D printer spool for prototyping."
            ],
            "environmental_benefit": "Provides circular local manufacturing feedstock, displacing petrochemical virgin filament production.",
            "carbon_offset_rating": "High"
        },
        {
            "title": "Microclimate Seedling Germination Cloche",
            "category": "Horticulture & Permaculture",
            "difficulty": "Easy",
            "estimated_time": "10-15 mins",
            "tools_required": ["Utility shears", "Bamboo garden stake", "Organic potting mix"],
            "step_by_step_guide": [
                "Rinse the transparent bottle with water and ensure optimal light transmission through the clear plastic.",
                "Cut off the bottom 2 inches of the bottle with shears to create an open dome cover.",
                "Remove the bottle cap to allow natural convective airflow and moisture regulation.",
                "Place the transparent dome directly over sensitive outdoor seedling sprouts in garden beds.",
                "Anchor the dome against wind gusts using a bamboo stake through the top spout for frost protection."
            ],
            "environmental_benefit": "Extends seasonal growing cycles naturally without disposable petroleum agricultural fleece.",
            "carbon_offset_rating": "Medium"
        }
    ],
    "Cardboard & Paper": [
        {
            "title": "Biodegradable Permaculture Sheet Mulch & Weed Suppressor",
            "category": "Soil Regeneration & Gardening",
            "difficulty": "Easy",
            "estimated_time": "20-30 mins",
            "tools_required": ["Utility knife", "Water hose / watering can", "Organic mulch or wood chips"],
            "step_by_step_guide": [
                "Flatten the cardboard boxes completely and peel away all plastic packaging tape, shipping labels, and staples.",
                "Moisten the bare soil bed thoroughly where weed suppression or soil conditioning is desired.",
                "Lay the corrugated cardboard flat on the soil, overlapping all edges by at least 6 inches to block light.",
                "Saturate the cardboard layer with water until the cellulose fibers are completely damp and pliable.",
                "Cover the wet cardboard with a 3-4 inch layer of organic compost or woodchips to foster fungal earthworm activity."
            ],
            "environmental_benefit": "Diverts bulky corrugated fiber from municipal waste, building rich topsoil while eliminating chemical herbicides.",
            "carbon_offset_rating": "High"
        },
        {
            "title": "Laser-Cut Interlocking Modular Drawer Grid",
            "category": "Makerspace & Office Organization",
            "difficulty": "Moderate",
            "estimated_time": "30-40 mins",
            "tools_required": ["Steel ruler", "X-Acto or utility knife", "Pencil", "Cutting mat"],
            "step_by_step_guide": [
                "Measure the exact interior width, depth, and height of your target desk or tool drawer.",
                "Cut long rectangular corrugated cardboard strips matching the drawer depth and height dimensions.",
                "Mark vertical slot notches halfway through each strip at regular 3-inch intervals with a pencil.",
                "Carefully cut 1/8-inch wide slots along the marked lines so perpendicular strips will interlock flush.",
                "Assemble the interlocking grid pattern, slide it into the drawer, and organize office supplies or hardware."
            ],
            "environmental_benefit": "Eliminates the purchase of virgin plastic drawer organizers by transforming rigid shipping discards.",
            "carbon_offset_rating": "Low"
        },
        {
            "title": "Shock-Absorbing Molded Pulp Packing Cushions",
            "category": "Eco-Packaging & Shipping",
            "difficulty": "Moderate",
            "estimated_time": "40-50 mins",
            "tools_required": ["Bucket or basin", "Water", "Kitchen blender or paint stirrer", "Wire mesh mold screen"],
            "step_by_step_guide": [
                "Tear clean cardboard into 1-inch squares and soak them in a bucket of warm water for 2 hours.",
                "Blend the softened cardboard slurry into a smooth, fibrous cellulose pulp using a mechanical mixer.",
                "Press the wet pulp firmly into wire mesh corner molds to squeeze out excess liquid.",
                "Allow the compressed fiber forms to sun-dry or oven-dry at 80°C until fully rigid and moisture-free.",
                "Use the lightweight molded corners to protect fragile ceramics, electronics, or glassware during transit."
            ],
            "environmental_benefit": "Replaces non-biodegradable expanded polystyrene (Styrofoam) packaging with compostable cellulose cushions.",
            "carbon_offset_rating": "High"
        }
    ],
    "Metals": [
        {
            "title": "Filigree Punched Luminary & Lantern Vessel",
            "category": "Artisanal Decor & Lighting",
            "difficulty": "Moderate",
            "estimated_time": "30-40 mins",
            "tools_required": ["Hammer", "Assorted nails or center punch", "Pencil", "Freezer / water", "Tea-light candle"],
            "step_by_step_guide": [
                "Clean the metal can thoroughly and strip off any exterior paper labels and glue residue.",
                "Fill the can completely with water and freeze solid overnight to provide internal hydraulic backing.",
                "Sketch a geometric or celestial pattern of dots directly onto the metal surface with a marker.",
                "Using a hammer and sharp nail, punch holes along the design lines through the ice-supported metal wall.",
                "Melt out the ice, dry the interior completely, and insert a candle or solar LED to project ambient light patterns."
            ],
            "environmental_benefit": "Upcycles rigid consumer food/beverage tins into durable home lighting, bypassing energy-intensive scrap remelting.",
            "carbon_offset_rating": "Medium"
        },
        {
            "title": "Modular Robotics Prototyping Chassis Brackets",
            "category": "STEM Education & Hardware Prototyping",
            "difficulty": "Moderate",
            "estimated_time": "35-45 mins",
            "tools_required": ["Tin snips / metal shears", "Drill with 3mm metal bit", "Steel ruler", "Deburring file"],
            "step_by_step_guide": [
                "Cut the top and bottom rims off the aluminum cylinder using heavy-duty shears to flatten a clean sheet.",
                "Measure and mark 20mm x 40mm rectangular bracket blanks on the flattened aluminum sheet.",
                "Cut out the blanks with tin snips and file all sheared edges smooth to remove dangerous sharp metal burrs.",
                "Drill precision 3mm mounting holes matching standard servo and microcontroller fastener spacing.",
                "Bend the brackets cleanly over a 90-degree workbench edge to create rigid structural robotics mounts."
            ],
            "environmental_benefit": "Provides zero-cost structural hardware for STEM robotics education while recycling non-ferrous sheet metal.",
            "carbon_offset_rating": "Medium"
        },
        {
            "title": "Corrosion-Resistant Hanging Succulent Wall Caddy",
            "category": "Urban Agriculture & Decor",
            "difficulty": "Easy",
            "estimated_time": "20-25 mins",
            "tools_required": ["Can opener", "Nail and hammer", "Jute twine", "Potting soil & gravel", "Succulents"],
            "step_by_step_guide": [
                "Smooth any remaining inner rim burrs using pliers or an abrasive stone until completely safe to touch.",
                "Punch three 4mm drainage holes into the bottom base of the can using a hammer and nail.",
                "Punch two opposing hanging holes near the top rim and thread sturdy jute twine for vertical suspension.",
                "Add a 1-inch layer of coarse gravel for aeration, followed by well-draining cactus and succulent potting mix.",
                "Plant your succulent cuttings, hang the caddy in direct sunlight, and water sparingly."
            ],
            "environmental_benefit": "Keeps rust-resistant aluminum and tin cans in active botanical service instead of single-use disposal.",
            "carbon_offset_rating": "Low"
        }
    ],
    "Glass": [
        {
            "title": "Airtight Zero-Waste Pantry Bulk Storage Vessel",
            "category": "Kitchen & Zero-Waste Living",
            "difficulty": "Easy",
            "estimated_time": "15-20 mins",
            "tools_required": ["Warm water & baking soda", "Scrub brush", "Chalkboard label", "Chalk marker"],
            "step_by_step_guide": [
                "Submerge the glass jar in warm water and baking soda for 15 minutes to dissolve label adhesive cleanly.",
                "Scrub away any remaining glue residue with a sponge and inspect the glass rim for any hairline chips or cracks.",
                "Sterilize the jar and lid in boiling water for 5 minutes, then dry thoroughly with a lint-free cloth.",
                "Apply a reusable chalkboard or vinyl label to the front facet and record the tare weight and food contents.",
                "Fill with bulk dry legumes, rice, spices, or seeds for clean, pest-proof, zero-waste pantry storage."
            ],
            "environmental_benefit": "Eliminates single-use plastic packaging at bulk refill stores and leverages non-porous infinitely recyclable silica glass.",
            "carbon_offset_rating": "Medium"
        },
        {
            "title": "Self-Contained Miniature Biosphere Terrarium",
            "category": "Horticulture & Botanical Craft",
            "difficulty": "Moderate",
            "estimated_time": "30-40 mins",
            "tools_required": ["Clean glass jar with lid", "Pea gravel or tumbled glass", "Activated charcoal", "Sphagnum moss", "Miniature ferns"],
            "step_by_step_guide": [
                "Thoroughly clean and dry the glass jar to ensure pristine optical clarity and eliminate any mold spores.",
                "Pour a 1-inch foundation layer of clean pea gravel or tumbled glass cullet at the bottom for drainage.",
                "Add a thin layer of crushed horticultural activated charcoal to filter water and prevent stagnant odors.",
                "Layer damp sphagnum moss followed by organic terrarium soil, then plant small moisture-loving mosses and ferns.",
                "Mist lightly with distilled water, seal the airtight lid, and place in bright, indirect sunlight to establish a closed water cycle."
            ],
            "environmental_benefit": "Repurposes intact glass vessels into self-sustaining educational ecosystems that clean indoor air.",
            "carbon_offset_rating": "Low"
        },
        {
            "title": "Artisan Hand-Poured Botanical Soy Candle Vessel",
            "category": "Artisanal Decor & Craft",
            "difficulty": "Moderate",
            "estimated_time": "35-45 mins",
            "tools_required": ["Heat-safe glass jar", "Natural soy wax flakes", "Cotton candle wick", "Wick centering clip", "Essential oils"],
            "step_by_step_guide": [
                "Verify the glass jar is heat-resistant, undamaged, and completely free of chips, grease, or moisture.",
                "Secure a pre-tabbed lead-free cotton wick to the center bottom of the jar using a heat-resistant adhesive dot.",
                "Melt natural soy wax flakes in a double-boiler until clear and liquid at approximately 75°C-80°C.",
                "Blend in plant-based essential oils, then slowly pour the liquid wax into the prepared glass container.",
                "Lock the wick upright with a centering clip, allow the candle to cure undisturbed for 24 hours, and trim wick to 1/4 inch."
            ],
            "environmental_benefit": "Replaces commercially manufactured paraffin candles in disposable containers with reusable artisan glass.",
            "carbon_offset_rating": "Medium"
        }
    ]
}


class ReuseEngine:
    """Generates upcycling suggestions and prepares industrial feedstock matches.
    Enforces unique titles, distinct practical applications, and 4-6 sequential actionable steps.
    """

    def __init__(self):
        pass

    def generate_suggestions(
        self,
        raw_suggestions: List[Any],
        material: MaterialAnalysis
    ) -> List[ReuseSuggestion]:
        """Convert raw AI suggestions (strings or dicts) into structured ReuseSuggestion objects.
        Ensures:
        - Unique, descriptive project titles (never generic "DIY Upcycling Project").
        - Each suggestion represents a distinct practical application.
        - Exactly 4-6 meaningful, sequential, actionable steps per project.
        - Dynamic enrichment from the curated domain catalog when AI input is sparse.
        """
        suggestions: List[ReuseSuggestion] = []
        used_titles: Set[str] = set()

        items = raw_suggestions if isinstance(raw_suggestions, list) else [raw_suggestions]

        for item in items:
            sugg = self._parse_and_enrich_item(item, material, used_titles)
            if sugg is not None:
                suggestions.append(sugg)
                used_titles.add(sugg.title.lower())

        # If model returned fewer than 2 distinct suggestions, enrich from curated catalog
        if len(suggestions) < 2:
            category = material.primary_category if material else "Plastics"
            catalog_pool = CURATED_PROJECT_CATALOG.get(category, CURATED_PROJECT_CATALOG.get("Plastics", []))

            for candidate in catalog_pool:
                if len(suggestions) >= 2:
                    break
                cand_title = candidate["title"]
                if cand_title.lower() not in used_titles:
                    suggestions.append(
                        ReuseSuggestion(
                            title=cand_title,
                            category=candidate["category"],
                            difficulty=candidate["difficulty"],
                            estimated_time=candidate["estimated_time"],
                            tools_required=list(candidate["tools_required"]),
                            step_by_step_guide=list(candidate["step_by_step_guide"]),
                            environmental_benefit=candidate["environmental_benefit"],
                            carbon_offset_rating=candidate["carbon_offset_rating"],
                        )
                    )
                    used_titles.add(cand_title.lower())

        # Guaranteed fallback if still empty
        if not suggestions:
            suggestions.append(self._generate_fallback_suggestion(material))

        return suggestions[:4]

    def _parse_and_enrich_item(
        self,
        item: Any,
        material: MaterialAnalysis,
        used_titles: Set[str]
    ) -> Optional[ReuseSuggestion]:
        """Parse an individual suggestion item (string or dict) into a verified ReuseSuggestion."""
        if not item:
            return None

        mat_name = material.material_type if material else "Material"
        category = material.primary_category if material else "General"

        if isinstance(item, str):
            text = item.strip()
            if not text:
                return None

            # Extract title and possible embedded steps
            title, remaining_text = self._extract_title_and_body(text, mat_name)
            steps = self._extract_or_generate_steps(title, remaining_text, material)

            # Deduplicate titles
            title = self._ensure_unique_title(title, used_titles, mat_name)

            return ReuseSuggestion(
                title=title,
                category=self._infer_category(title, category),
                difficulty="Easy" if len(steps) <= 4 else "Moderate",
                estimated_time="20-30 mins",
                tools_required=self._infer_tools(title, category),
                step_by_step_guide=steps,
                environmental_benefit=f"Diverts post-consumer {mat_name} from landfill and extends material functional utility.",
                carbon_offset_rating="Medium",
            )

        elif isinstance(item, dict):
            raw_title = str(item.get("title", "")).strip()
            if not raw_title or self._is_generic_title(raw_title):
                raw_title = self._synthesize_title_from_text(
                    item.get("description", "") or item.get("step_by_step_guide", ""),
                    mat_name
                )

            title = self._ensure_unique_title(raw_title, used_titles, mat_name)

            raw_steps = item.get("step_by_step_guide") or item.get("steps") or item.get("instructions")
            steps = self._extract_or_generate_steps(title, raw_steps, material)

            tools = item.get("tools_required", [])
            if isinstance(tools, str):
                tools = [t.strip() for t in tools.split(",") if t.strip()]
            if not tools:
                tools = self._infer_tools(title, category)

            return ReuseSuggestion(
                title=title,
                category=str(item.get("category", self._infer_category(title, category))).strip(),
                difficulty=str(item.get("difficulty", "Easy" if len(steps) <= 4 else "Moderate")).strip(),
                estimated_time=str(item.get("estimated_time", "20-30 mins")).strip(),
                tools_required=tools,
                step_by_step_guide=steps,
                environmental_benefit=str(
                    item.get("environmental_benefit", f"Diverts {mat_name} from disposal streams and lowers carbon footprint.")
                ).strip(),
                carbon_offset_rating=str(item.get("carbon_offset_rating", "Medium")).strip(),
            )

        return None

    def _extract_title_and_body(self, text: str, mat_name: str) -> tuple[str, str]:
        """Extract a crisp, descriptive project title from raw text."""
        # Try delimiter splitting: "Title: Body" or "Title - Body"
        delims = [": ", " - ", " — ", " | "]
        for delim in delims:
            if delim in text:
                parts = text.split(delim, 1)
                candidate = parts[0].strip()
                # Clean numbered prefixes e.g. "1. ", "Idea 1: "
                candidate = re.sub(r"^(?:\d+[\.\)]\s*|idea\s*\d*[:\s]*|project\s*\d*[:\s]*)", "", candidate, flags=re.IGNORECASE).strip()
                if 4 <= len(candidate) <= 50 and not self._is_generic_title(candidate):
                    return candidate, parts[1].strip()

        # If entire text is already a crisp descriptive project title phrase (<= 55 chars)
        clean_full = re.sub(r"^(?:\d+[\.\)]\s*|idea\s*\d*[:\s]*|project\s*\d*[:\s]*)", "", text, flags=re.IGNORECASE).strip()
        if 4 <= len(clean_full) <= 55 and not self._is_generic_title(clean_full):
            return clean_full, ""

        # Check if first sentence is a valid title using sentence boundary (dot followed by whitespace)
        sentence_parts = re.split(r"\.(?:\s+|$)", text, maxsplit=1)
        if sentence_parts:
            first_sentence = sentence_parts[0].strip()
            first_sentence = re.sub(r"^(?:\d+[\.\)]\s*|idea\s*\d*[:\s]*|project\s*\d*[:\s]*)", "", first_sentence, flags=re.IGNORECASE).strip()
            if 4 <= len(first_sentence) <= 50 and not self._is_generic_title(first_sentence):
                remaining = sentence_parts[1].strip() if len(sentence_parts) > 1 else ""
                return first_sentence, remaining

        # Synthesize a descriptive project title
        return self._synthesize_title_from_text(text, mat_name), text

    def _synthesize_title_from_text(self, text: str, mat_name: str) -> str:
        """Create a descriptive action title by matching keywords in text."""
        t_low = str(text).lower()
        if "planter" in t_low or "seed" in t_low or "garden" in t_low or "herb" in t_low:
            return f"Self-Watering Botanical Planter from {mat_name}"
        elif "organizer" in t_low or "divider" in t_low or "caddy" in t_low or "drawer" in t_low:
            return f"Interlocking Desk & Drawer Organizer from {mat_name}"
        elif "mulch" in t_low or "weed" in t_low or "compost" in t_low:
            return f"Biodegradable Permaculture Sheet Mulch from {mat_name}"
        elif "jar" in t_low or "pantry" in t_low or "storage" in t_low or "bulk" in t_low:
            return f"Airtight Zero-Waste Bulk Pantry Jar from {mat_name}"
        elif "candle" in t_low or "lantern" in t_low or "light" in t_low or "luminary" in t_low:
            return f"Artisan Ambient Candle Lantern from {mat_name}"
        elif "filament" in t_low or "3d" in t_low or "print" in t_low:
            return f"Extruded 3D Printing Filament from {mat_name}"
        elif "terrarium" in t_low or "drainage" in t_low or "moss" in t_low:
            return f"Self-Contained Glass Terrarium from {mat_name}"
        elif "bracket" in t_low or "robot" in t_low or "hardware" in t_low:
            return f"Precision Prototyping Hardware Brackets from {mat_name}"
        else:
            return f"Custom Architectural Storage Vessel from {mat_name}"

    def _is_generic_title(self, title: str) -> bool:
        """Identify generic repetitive placeholder titles that must be replaced."""
        t = title.strip().lower()
        generic_patterns = [
            "diy upcycling project",
            "diy project",
            "upcycling project",
            "creative repurposing project",
            "creative project",
            "repurpose project",
            "waste reuse",
            "recycling idea",
            "idea 1",
            "idea 2",
            "idea 3",
            "project 1",
            "project 2",
            "project",
            "general reuse",
        ]
        return any(g in t for g in generic_patterns) or len(title.strip()) < 4

    def _ensure_unique_title(self, title: str, used_titles: Set[str], mat_name: str) -> str:
        """Guarantee title uniqueness among suggestions."""
        clean = title.strip()
        if clean.lower() not in used_titles:
            return clean

        # Generate unique variant
        variants = [
            f"{clean} (Primary Fabrication)",
            f"{clean} (Secondary Form)",
            f"Alternative {clean}",
            f"Custom Modified {clean}",
        ]
        for v in variants:
            if v.lower() not in used_titles:
                return v

        return f"{clean} - Variant {len(used_titles) + 1}"

    def _extract_or_generate_steps(
        self,
        title: str,
        raw_steps_or_text: Any,
        material: MaterialAnalysis
    ) -> List[str]:
        """Strictly enforce that every recommendation contains between 4 and 6 meaningful,
        sequential, actionable steps explaining the actual physical fabrication process.
        """
        parsed_steps: List[str] = []

        # Case 1: Provided as list of strings
        if isinstance(raw_steps_or_text, list):
            for s in raw_steps_or_text:
                s_str = str(s).strip()
                if len(s_str) > 10:
                    # Strip leading numbering like "Step 1: " or "1. "
                    cleaned = re.sub(r"^(?:step\s*\d*[:\s]*|\d+[\.\)]\s*)", "", s_str, flags=re.IGNORECASE).strip()
                    parsed_steps.append(cleaned)

        # Case 2: Provided as paragraph or string
        elif isinstance(raw_steps_or_text, str) and raw_steps_or_text.strip():
            text = raw_steps_or_text.strip()
            # Check for embedded numbered steps e.g. "1. ... 2. ... 3. ..."
            num_matches = re.split(r"(?:^|\s+)(?:\d+[\.\)]|step\s*\d+[:\s])\s+", text, flags=re.IGNORECASE)
            cleaned_num = [m.strip() for m in num_matches if len(m.strip()) > 15]
            if len(cleaned_num) >= 3:
                parsed_steps = cleaned_num
            else:
                # Split by sentence periods
                sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 15]
                if len(sentences) >= 4:
                    parsed_steps = sentences[:6]

        # Check if parsed steps satisfy the 4 to 6 actionable step criteria
        if 4 <= len(parsed_steps) <= 6:
            return parsed_steps

        # If too many (> 6), condense down to 5 sequential steps
        if len(parsed_steps) > 6:
            return self._condense_steps(parsed_steps, max_steps=5)

        # If too few (< 4) or empty, generate complete 5-step actionable workflow
        return self._generate_archetype_steps(title, parsed_steps, material)

    def _condense_steps(self, steps: List[str], max_steps: int = 5) -> List[str]:
        """Condense a lengthy step list into max_steps logical sequential steps."""
        if len(steps) <= max_steps:
            return steps
        first_step = steps[0]
        last_step = steps[-1]
        middle = steps[1:-1]
        chunk_size = len(middle) // (max_steps - 2)
        condensed = [first_step]
        for i in range(max_steps - 2):
            sub = middle[i * chunk_size : (i + 1) * chunk_size] if i < (max_steps - 3) else middle[i * chunk_size :]
            condensed.append("; ".join(sub))
        condensed.append(last_step)
        return condensed[:max_steps]

    def _generate_archetype_steps(
        self,
        title: str,
        existing_hints: List[str],
        material: MaterialAnalysis
    ) -> List[str]:
        """Generate 5 sequential, actionable steps specific to the project archetype."""
        t_low = title.lower()
        mat_name = material.material_type if material else "material"
        category = material.primary_category if material else "Plastics"

        # Archetype: Glass Pantry Jar / Bulk Food Refill
        if any(w in t_low for w in ["pantry", "jar", "bulk", "dry goods", "airtight"]) or ("food" in t_low and "jar" in mat_name.lower()):
            return [
                f"Submerge the {mat_name} in warm water with 2 tablespoons of baking soda for 15 minutes to loosen labels.",
                "Peel off the paper label and scrub any stubborn adhesive using an abrasive sponge or plant-based oil.",
                "Inspect the rim and threads under strong light to confirm there are zero chips, cracks, or structural defects.",
                "Sterilize the jar and lid in boiling water for 5 minutes, then invert onto a clean drying rack until completely dry.",
                "Apply a reusable chalkboard or vinyl label, record the vessel tare weight, and fill with bulk spices, grains, or beans."
            ]

        # Archetype: Candle Luminary / Ambient Lantern
        elif any(w in t_low for w in ["candle", "lantern", "luminary", "light", "lamp"]):
            if "glass" in mat_name.lower() or "glass" in category.lower():
                return [
                    f"Inspect the {mat_name} to confirm zero hairline cracks or rim chips, then wash with warm soapy water and wipe dry.",
                    "Affix a lead-free pre-tabbed cotton wick to the center bottom of the jar using a heat-resistant adhesive dot.",
                    "Melt natural soy wax flakes in a double-boiler until completely liquefied at approximately 75°C to 80°C.",
                    "Stir in botanical essential oils, then slowly pour the warm wax into the glass container, avoiding air pocket formation.",
                    "Center the wick using a stabilization clip, allow to cure undisturbed for 24 hours, and trim the wick to 1/4 inch."
                ]
            else:
                return [
                    f"Clean the {mat_name} thoroughly and strip away all exterior paper labels and adhesive residues.",
                    "Fill the metal container completely with water and freeze solid overnight to provide internal hydraulic backing.",
                    "Sketch a decorative filigree or geometric pattern of light-emission dots directly on the metal surface.",
                    "Punch through the design points using a hammer and sharp center punch against the supported ice core.",
                    "Melt out the ice, dry the interior completely, and insert a candle or solar LED to project ambient patterns."
                ]

        # Archetype: Planter / Botanical Wicking Container
        elif any(w in t_low for w in ["planter", "herb", "wick", "pot", "seedling", "garden"]):
            return [
                f"Thoroughly clean the {mat_name} with warm water and eco-friendly soap, removing all paper labels and adhesive.",
                "Mark a level cutting line around the upper third of the vessel using a ruler and permanent marker.",
                "Carefully slice along the line using heavy shears or a utility knife, separating the top funnel from the base reservoir.",
                "Punch three 5mm drainage holes in the inverted top section and thread an 8-inch cotton wicking cord through the spout.",
                "Fill the upper section with lightweight organic potting mix, embed seeds or seedlings, and add 2 inches of water to the base."
            ]

        # Archetype: Desk Organizer / Drawer Divider / Caddy
        elif any(w in t_low for w in ["organizer", "divider", "drawer", "caddy", "bin", "partition"]) or ("storage" in t_low and not any(k in t_low for k in ["jar", "pantry", "bottle"])):
            return [
                f"Inspect the {mat_name} discard and remove any dust, stickers, or contaminated foreign materials.",
                "Measure the interior dimensions of your storage drawer and mark reference guidelines with a straightedge.",
                "Cut the material cleanly into modular compartments or interlocking slotted partition strips.",
                "Smooth all cut edges with fine-grit sandpaper or protective edge tape to eliminate sharp corners or burrs.",
                "Assemble the dividers in a rigid grid configuration and load with office supplies, craft items, or hardware."
            ]

        # Archetype: Mulch / Weed Barrier / Soil Regeneration
        elif any(w in t_low for w in ["mulch", "weed", "soil", "barrier", "compost", "bed"]):
            return [
                f"Strip all non-biodegradable packing tape, plastic film, shipping barcodes, and metal staples from the {mat_name}.",
                "Clear unwanted weeds from the target soil area and water the bare ground thoroughly.",
                "Lay the unprinted material flat over the soil bed, overlapping adjacent edges by at least 6 inches to seal light gaps.",
                "Drench the laid cellulose layer completely with water until fully pliable and molded to the ground contours.",
                "Spread a 3 to 4-inch layer of organic woodchips or finished compost on top to retain moisture and foster soil microbes."
            ]

        # Archetype: 3D Printing Filament / Polymer Extrusion
        elif any(w in t_low for w in ["filament", "3d print", "extrud", "spool"]):
            return [
                f"Thoroughly wash and dry the thermoplastic {mat_name} to eliminate sugars, dust, and beverage residues.",
                "Slice the bottom off the container and mount onto an adjustable bottle-slitting blade jig.",
                "Pull a continuous 9mm-wide ribbon strip through the razor guide under uniform manual tension.",
                "Feed the plastic ribbon into a PID-controlled heated extrusion nozzle set to 215°C for melt-compression.",
                "Spool the resulting 1.75mm round filament onto a standard printing reel, checking diameter with digital calipers."
            ]

        # Archetype: Terrarium / Drainage Substrate
        elif any(w in t_low for w in ["terrarium", "drainage", "gravel", "pebble", "biosphere"]):
            return [
                f"Wash the glass vessel with warm water to achieve pristine optical transparency, avoiding chemical cleaners.",
                "Add a 1-inch bottom drainage layer of tumbled pebbles or clean glass cullet to prevent root rot.",
                "Spread a thin layer of horticultural activated charcoal over the stones to filter water and absorb odors.",
                "Add damp sphagnum moss and organic potting soil, then gently plant small shade-tolerant ferns and mosses.",
                "Mist the foliage with distilled water, seal the airtight lid, and position in bright indirect ambient light."
            ]

        # Archetype: Hardware / Robotics Brackets
        elif any(w in t_low for w in ["bracket", "robot", "hardware", "proto", "mount"]):
            return [
                f"Cut away the rims of the metal container using shears and flatten the body into an unbent sheet.",
                "Scribe precise bracket dimensions (e.g. 25mm x 50mm) onto the metal surface using a steel ruler and scribe.",
                "Cut out the bracket blanks with tin snips, then file all edges to remove hazardous burrs.",
                "Center-punch and drill 3mm mounting holes matching standard robotic hardware or fastener dimensions.",
                "Clamp the piece along the marked fold line in a vise and bend cleanly to a rigid 90-degree structural angle."
            ]

        # Universal Default 5-Step Structural Upcycling Workflow
        return [
            f"Thoroughly clean and sanitize the {mat_name} using warm water and mild eco-friendly detergent.",
            "Carefully inspect the physical structure for any sharp burrs, cracks, or contamination, removing unwanted labels.",
            f"Measure and mark reference cutting or folding lines tailored for your specific household or workshop application.",
            "Execute clean precision cuts or shaping adjustments using appropriate hand tools while observing workshop safety.",
            "Finalize the repurposed object by smoothing edges, fitting fasteners or liners, and putting it into immediate functional use."
        ]

    def _infer_category(self, title: str, default_category: str) -> str:
        """Assign appropriate project category from title keywords."""
        t = title.lower()
        if any(w in t for w in ["planter", "herb", "garden", "mulch", "soil", "seedling", "compost", "terrarium"]):
            return "Urban Agriculture & Gardening"
        elif any(w in t for w in ["organizer", "drawer", "caddy", "divider", "storage", "pantry", "jar"]):
            return "Home Organization & Storage"
        elif any(w in t for w in ["filament", "3d", "robot", "bracket", "maker", "hardware"]):
            return "Makerspace & Engineering"
        elif any(w in t for w in ["candle", "lantern", "luminary", "decor", "craft", "artisan"]):
            return "Artisanal Decor & Lighting"
        elif any(w in t for w in ["insulation", "brick", "wall", "cushion", "pulp"]):
            return "Sustainable Materials & Packaging"
        return "DIY / Circular Upcycling"

    def _infer_tools(self, title: str, category: str) -> List[str]:
        """Infer realistic tools required based on the project title and category."""
        t = title.lower()
        if "planter" in t:
            return ["Utility knife / heavy shears", "Cotton wick", "Potting soil", "Water"]
        elif "organizer" in t or "divider" in t:
            return ["Steel ruler", "Utility knife", "Sandpaper (fine grit)", "Pencil"]
        elif "mulch" in t:
            return ["Utility blade", "Water hose / watering can", "Woodchips or finished compost"]
        elif "pantry" in t or "jar" in t:
            return ["Baking soda & warm water", "Abrasive sponge", "Chalkboard label & marker"]
        elif "candle" in t:
            return ["Heat-resistant vessel", "Soy wax flakes", "Cotton candle wick", "Double boiler"]
        elif "lantern" in t:
            return ["Hammer", "Center punch or assorted nails", "Marker", "Freezer water backing"]
        elif "filament" in t:
            return ["Rotary slitting blade", "PID heated extrusion nozzle (210°C)", "Collection spool"]
        elif "bracket" in t or "robot" in t:
            return ["Tin snips / metal shears", "Drill with 3mm metal bit", "Flat file", "Bench vise"]
        elif "terrarium" in t:
            return ["Clean glass jar", "Drainage pebbles / cullet", "Activated charcoal", "Sphagnum moss"]
        else:
            return ["Scissors / Utility knife", "Cleaning sponge", "Ruler", "Marker"]

    def get_industry_matches(
        self,
        material: MaterialAnalysis,
        raw_matches: Optional[List[str]] = None
    ) -> List[str]:
        """Produce prioritized industry partner profiles for Member 2's matching engine.
        Combines model inferences with pre-mapped circular industrial demand streams.
        """
        matches: List[str] = []
        if raw_matches and isinstance(raw_matches, list):
            matches.extend([m.strip() for m in raw_matches if m.strip()])

        category = material.primary_category if material else "Plastics"
        fallback_streams = INDUSTRY_FEEDSTOCK_PROFILES.get(category, [
            "Regional Municipal Secondary Sorters",
            "Specialized Circular Material Aggregators"
        ])

        for stream in fallback_streams:
            if stream not in matches:
                matches.append(stream)

        return matches[:6]

    def _generate_fallback_suggestion(self, material: MaterialAnalysis) -> ReuseSuggestion:
        """Create a solid, rigorous fallback suggestion with 5 actionable sequential steps."""
        mat_name = material.material_type if material else "Discarded Material"
        return ReuseSuggestion(
            title=f"Multi-Compartment Utility Organizer from {mat_name}",
            category="Home Organization & Workshop",
            difficulty="Easy",
            estimated_time="20 mins",
            tools_required=["Utility knife / shears", "Cleaning sponge", "Fine sandpaper", "Label marker"],
            step_by_step_guide=[
                f"Thoroughly clean the {mat_name} with warm water and eco-friendly soap, removing all paper labels and residual adhesives.",
                "Inspect the surface and mark level cutting guidelines using a ruler and marker tailored to your target drawer or shelf height.",
                "Carefully trim along the marked lines with sharp utility shears to form uniform open modular storage compartments.",
                "Smooth all cut plastic or paperboard edges using fine sandpaper or adhesive edge-trim to prevent sharp points.",
                "Insert the finished organizer into your workshop, kitchen, or desk drawer to sort fasteners, cords, or stationery."
            ],
            environmental_benefit=f"Keeps {mat_name} in active secondary service and diverts high-value resource from landfilling.",
            carbon_offset_rating="Medium"
        )
